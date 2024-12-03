from ipaddress import ip_address
from app.models.base import BaseModel
from core.database import Base
from sqlalchemy import Boolean, Column, Integer, DateTime, String, column

class LoginAttempts(Base):
    __tablename___ = "login_attempt"

    id = Column(String, index=True)
    username = Column(String)
    email = Column(String)
    password_hash = Column(String)
    status = Column(Boolean)
    ip_address = Column(String, index=True)
    other = Column(String)
