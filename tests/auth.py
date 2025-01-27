import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.main import app
from app.core.config import settings

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test database
Base.metadata.create_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

# Test data
TEST_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpassword"
}

def test_register_user(client):
    # Test successful registration
    response = client.post("/auth/register", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == TEST_USER["email"]
    assert data["user"]["username"] == TEST_USER["username"]
    assert "token" in data

    # Test duplicate registration
    response = client.post("/auth/register", json=TEST_USER)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login(client):
    # First register a user
    client.post("/auth/register", json=TEST_USER)
    
    # Test successful login
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in response.cookies

    # Test invalid password
    response = client.post("/auth/login", json={"email": TEST_USER["email"], "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

    # Test invalid email
    response = client.post("/auth/login", json={"email": "wrong@example.com", "password": TEST_USER["password"]})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_me_endpoint(client):
    # Register and login
    client.post("/auth/register", json=TEST_USER)
    login_response = client.post("/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    token = login_response.json()["access_token"]
    
    # Test authorized access
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["username"] == TEST_USER["username"]

    # Test unauthorized access
    response = client.get("/auth/me")
    assert response.status_code == 401

def test_refresh_token(client):
    # Register and login
    client.post("/auth/register", json=TEST_USER)
    login_response = client.post("/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    refresh_token = login_response.cookies["refresh_token"]
    
    # Test token refresh
    response = client.post("/auth/refresh", cookies={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()

    # Test missing refresh token
    response = client.post("/auth/refresh")
    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token missing"

def test_logout(client):
    # Register and login
    client.post("/auth/register", json=TEST_USER)
    login_response = client.post("/auth/login", json={
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    
    # Test logout
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert "refresh_token" not in response.cookies
