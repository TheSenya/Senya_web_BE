from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Senya Web Backend"
    DEBUG: bool
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"  # Adding this for JWT encoding

    # Database settings
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_HOST: str
    DATABASE_PORT: int

    FRONTEND_URL: str 
    CORS_ORIGINS: list 

    COOKIE_SAMESITE: str
    COOKIE_SECURE: bool

    class Config:
        env_file = ".env"

settings = Settings()

# Export these for easier imports elsewhere
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM