from sqlalchemy import Column, String
from app.models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)