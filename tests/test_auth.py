from app.core.config import settings
from app.config.logger import logger
import sys
sys.dont_write_bytecode = True
# from app.core.logger import logger

# Define the API prefix from configuration
API_V1_PREFIX = settings.API_V1_STR
# logger.info(f"API_V1_PREFIX: {API_V1_PREFIX}")

def test_register_user(client):
    # Test data for successful registration
    TEST_USER = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword"
    }

    # (PASS) Test successful registration
    response = client.post(f"{API_V1_PREFIX}/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword"
    })
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
    assert response.json()["detail"] == "Email or username already registered"

    # (FAIL) Test username already registered 
    TEST_USER_DUPLICATE_USERNAME = {
        "email": "test2@example.com",
        "username": "testuser",
        "password": "testpassword3"
    }
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=TEST_USER_DUPLICATE_USERNAME)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email or username already registered"

    # (FAIL) Test duplicate registration
    response = client.post(f"{API_V1_PREFIX}/auth/register", json=TEST_USER)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email or username already registered"

    # Test token validation flow
    # First register and get initial tokens
    TEST_USER_TOKENS = {
        "email": "tokens@example.com",
        "username": "tokenuser",
        "password": "testpassword"
    }
    
    register_response = client.post(f"{API_V1_PREFIX}/auth/register", json=TEST_USER_TOKENS)
    assert register_response.status_code == 200
    access_token = register_response.json()["token"]["access_token"]
    refresh_token = register_response.cookies.get("refresh_token")
    
    logger.debug(f"access_token: {access_token}")
    logger.debug(f"refresh_token: {refresh_token}")

    # Test valid access token
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = client.get(f"{API_V1_PREFIX}/auth/me", headers=headers, cookies={"refresh_token": refresh_token})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == TEST_USER_TOKENS["email"]
    
    # Test invalid access token but valid refresh token
    invalid_token = "invalid.token.here"
    headers = {"Authorization": f"Bearer {invalid_token}"}
    me_response = client.get(f"{API_V1_PREFIX}/auth/me", headers=headers, cookies={"refresh_token": refresh_token})
    assert me_response.status_code == 401
    
    # Test missing tokens
    me_response = client.get(f"{API_V1_PREFIX}/auth/me")
    assert me_response.status_code == 401
    

