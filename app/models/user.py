from sqlalchemy import Boolean, Column, String
from app.models.base import BaseModel
from core.database import Base

class User(BaseModel):
    __tablename__ = "user"

    id = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean)

