from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pydantic import field_validator
from typing import Union

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"  # This will ignore extra fields
    )   

    # App settings  
    APP_NAME: str = "Senya Web Backend"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: Union[int, str] = "30"
    ALGORITHM: str = "HS256"  # Adding this for JWT encoding
    LOG_LEVEL: str = "INFO"

    # Database settings
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_HOST: str
    DATABASE_PORT: str

    # FRONTEND_URL: str 
    CORS_ORIGINS: Union[str, list[str]]

    COOKIE_SAMESITE: str
    COOKIE_SECURE: Union[bool, str]

    ENVIRONMENT: str

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        # If a string is provided, split it by comma
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        # Otherwise, assume it's already a list (e.g. provided as JSON)
        if isinstance(v, list):
            return v
        raise ValueError("Invalid CORS_ORIGINS format")

    @field_validator("DEBUG", "COOKIE_SECURE", mode="before")
    def parse_bool(cls, v):
        if isinstance(v, str):
            if v.lower() in ('false', '0', 'no', 'off', ''): # Add '' if empty string should be False
                return False
            return True
        return bool(v) # Ensure any other type is converted to bool

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES", mode="before")
    def parse_int(cls, v):
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