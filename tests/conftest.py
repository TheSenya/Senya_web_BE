import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, get_db, Base, engine

from app.models.user import User
from app.models.login import LoginAttempts

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Create all tables in the test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Create a new database session for every test.
    The session is rolled back and closed after each test ensuring isolation.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """
    Override the get_db dependency to ensure our FastAPI routes use
    the test database session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
