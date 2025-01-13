from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
from app.core.database import Base

class User(BaseModel):
    __tablename__ = "users"

    # Change from String to Integer and enable auto-increment
    id = Column(UUID(as_uuid=True), unique=True, index=True, primary_key=True, autoincrement=False)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean)
