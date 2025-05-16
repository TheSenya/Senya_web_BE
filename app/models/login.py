from sqlalchemy import Column, Integer, String, DateTime, UUID, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class LoginAttempts(Base):
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)  
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    success = Column(Boolean, nullable=False)
    ip_address = Column(String, nullable=False)

    # Relationships
    user = relationship('User', back_populates='login_attempts')