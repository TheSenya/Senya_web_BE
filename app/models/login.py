from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base

class LoginAttempts(Base):
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    timestamp = Column(DateTime)
    success = Column(Integer)
    ip_address = Column(String)
