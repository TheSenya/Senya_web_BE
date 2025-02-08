from conftest import client
from app.core.config import settings

# Define the API prefix from configuration
API_V1_PREFIX = settings.API_V1_STR

def test_register_user(client):

    # Test data
    TEST_USER = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword"
    }

    # (PASS) Test successful registration
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == TEST_USER["email"]
    assert data["user"]["username"] == TEST_USER["username"]
    assert "token" in data
    assert data["token"]["token_type"] == "access"
    assert "access_token" in data["token"]

    # (FAIL) Test email missing
    TEST_USER_MISSING_EMAIL = {
        "username": "testuser",
        "password": "testpassword"
    }
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=TEST_USER_MISSING_EMAIL)
    assert response.status_code == 422

    # (FAIL) Test username missing
    TEST_USER_MISSING_USERNAME = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=TEST_USER_MISSING_USERNAME)
    assert response.status_code == 422

    # (FAIL) Test password missing
    TEST_USER_MISSING_PASSWORD = {
        "email": "test@example.com",
        "username": "testuser"
    }
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=TEST_USER_MISSING_PASSWORD)
    assert response.status_code == 422
    
    # (FAIL) Test email already registered
    TEST_USER_DUPLICATE_EMAIL = {
        "email": "test@example.com",
        "username": "testuser2",
        "password": "testpassword2"
    }
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=TEST_USER_DUPLICATE_EMAIL)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

    # (PASS) Test username already registered 
    TEST_USER_DUPLICATE_USERNAME = {
        "email": "test2@example.com",
        "username": "testuser",
        "password": "testpassword3"
    }
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=TEST_USER_DUPLICATE_USERNAME)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

    # (FAIL) Test duplicate registration
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=TEST_USER)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

