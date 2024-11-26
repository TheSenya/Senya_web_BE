from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

log = logging.getLogger(__name__)

router = APIRouter(
    prefix="/login",
    tags=["authentication"]
)

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    username: str

@router.post("/", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    # This is a mock authentication
    # In a real app, you would verify against a database
    
    log.info(f"Login attempt with username: {login_data.username} and password: {login_data.password}")

    if login_data.username == "senya" and login_data.password == "senya":
        return {
            "access_token": "mock_token_12345",
            "username": login_data.username
        }
    
    raise HTTPException(
        status_code=401,
        detail="Incorrect username or password"
    )