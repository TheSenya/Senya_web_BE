from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.core.database import Base


class User(BaseModel):
    __tablename__ = "users"

    # Change from String to Integer and enable auto-increment
    id = Column(
        UUID(as_uuid=True),
        unique=True,
        index=True,
        primary_key=True,
        autoincrement=False,
    )
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean)

    # Relationships
    note_folders = relationship(
        "NoteFolder", back_populates="user", cascade="all, delete-orphan"
    )
    # One-to-many relationship with the Folder table. Deleting a user also deletes all associated folders.
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    workouts = relationship(
        "Workout", back_populates="user", cascade="all, delete-orphan"
    )
    exercises = relationship(
        "Exercise", back_populates="user", cascade="all, delete-orphan"
    )
    login_attempts = relationship("LoginAttempts", back_populates="user")
