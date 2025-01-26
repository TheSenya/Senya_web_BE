from pydantic import BaseModel
from app.schemas.user import User

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    username: str
    email: str

class Token(BaseModel):
    access_token: str
    token_type: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str

class RegisterResponse(BaseModel):
    user: User
    token: Token
