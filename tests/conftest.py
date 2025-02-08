# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from fastapi.testclient import TestClient

# Import your FastAPI app and the database items.
# Adjust these import paths according to your project structure.
from app.main import app           # your FastAPI application
from app.core.database import Base, get_db  # SQLAlchemy Base and dependency that yields a DB session


# <-- Ensure all models are imported here so they get registered with Base.metadata.
from app.models.user import User
from app.models.login import LoginAttempts
from app.models.workout import Workouts
from app.models.notes import Note, NoteFolder

from app.core.config import settings



# ------------------------------------------------------------------------------
# Fixture: Start PostgreSQL Container for Tests
# ------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def postgres_container():
    """
    Start a temporary PostgreSQL container using Testcontainers.
    The container will run for the duration of the test session.
    
    Testcontainers automatically pulls the image (here we use postgres:15),
    starts the container, and provides a connection URL.
    
    See: :contentReference[oaicite:0]{index=0} for Testcontainers Python documentation.
    """
    # Using a context manager ensures that the container is stopped when tests finish.
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres  # yield the container instance for use in later fixtures


# ------------------------------------------------------------------------------
# Fixture: Create SQLAlchemy Engine and Set Up Schema
# ------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def test_engine(postgres_container):
    """
    Create a SQLAlchemy engine using the connection URL from the test Postgres container.
    Then, create all tables as defined in your SQLAlchemy models.
    
    This engine is shared across all tests in the session.
    """
    # Get the connection URL from the running container
    engine = create_engine(postgres_container.get_connection_url())
    # Create the database tables using your metadata (make sure all your models have been imported)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


# ------------------------------------------------------------------------------
# Fixture: Create a New Database Session for Each Test
# ------------------------------------------------------------------------------
@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Create a new SQLAlchemy session for each test function.
    At the end of each test, rollback any changes so that the database
    remains clean for the next test.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # Roll back any changes (ensures isolation between tests)
        session.rollback()
        session.close()


# ------------------------------------------------------------------------------
# Fixture: Create a TestClient That Uses the Test Database Session
# ------------------------------------------------------------------------------
@pytest.fixture(scope="function")
def client(db_session):
    """
    Override the FastAPI dependency (get_db) so that when endpoints ask for
    a database session they receive our test session.
    
    Then, create a TestClient instance that we can use in our endpoint tests.
    """
    def override_get_db():
        # This override returns our test session
        try:
            yield db_session
        finally:
            # (The db_session fixture handles rollback and closing)
            pass

    # Override the dependency in our FastAPI app
    app.dependency_overrides[get_db] = override_get_db

    # Create a TestClient for the app – this allows you to make HTTP requests to your endpoints.
    with TestClient(app) as test_client:
        yield test_client

    # Clean up the dependency override after the test runs
    app.dependency_overrides.clear()
