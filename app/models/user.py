from sqlalchemy import Boolean, Column, String
from app.models.base import BaseModel
from app.core.database import Base

class User(BaseModel):
    __tablename__ = "users"

    id = Column(String, unique=True, index=True, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean)

