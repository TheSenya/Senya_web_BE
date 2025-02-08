from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
from pydantic import field_validator

class Settings(BaseSettings):
    APP_NAME: str = "Senya Web Backend"
    DEBUG: bool | str = "false"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int | str = "30"
    ALGORITHM: str = "HS256"  # Adding this for JWT encoding

    # Database settings
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_HOST: str
    DATABASE_PORT: int | str

    FRONTEND_URL: str 
    CORS_ORIGINS: str | list[str]

    COOKIE_SAMESITE: str
    COOKIE_SECURE: bool | str

    class Config:
        env_file = ".env"

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        # If a string is provided, split it by comma
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        # Otherwise, assume it’s already a list (e.g. provided as JSON)
        if isinstance(v, list):
            return v
        raise ValueError("Invalid CORS_ORIGINS format")

    @field_validator("DEBUG", "COOKIE_SECURE", mode="before")
    def parse_bool(cls, v):
        if isinstance(v, str):
            return bool(v.lower())
        return v

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES", mode="before")
    def parse_access_token_expire_minutes(cls, v):
        if isinstance(v, str):
            return int(v)
        return v

@lru_cache
def get_settings():
    """
    Caches and returns an instance of Settings.
    This is useful for dependency injection in frameworks like FastAPI.
    """
    return Settings() # type: ignore

settings = get_settings()

# Export these for easier imports elsewhere
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM