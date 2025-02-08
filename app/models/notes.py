from app.models.base import BaseModel
from sqlalchemy import (
    Column, String, Integer, ForeignKey, Text, DateTime, func, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

class NoteFolder(BaseModel):
    __tablename__ = "note_folder"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    name = Column(String(50), nullable=False)
    is_root = Column(Boolean, default=False, nullable=False)
    parent_id = Column(Integer, ForeignKey("note_folder.id"), nullable=True)  # Changed to nullable=True

    users = relationship("User", back_populates="note_folders")  # Fixed relationship name
    parent = relationship("NoteFolder", remote_side=[id], backref="children")
    notes = relationship('Note', back_populates='folders', cascade="all, delete-orphan")  # Fixed relationship name

class Note(BaseModel):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    name = Column(String(150), nullable=False)
    folder_id = Column(Integer, ForeignKey("note_folder.id"), nullable=False)
    content = Column(JSONB, nullable=True)
    format = Column(String(20), nullable=False)

    users = relationship("User", back_populates="notes")  # Fixed relationship
    folder = relationship("NoteFolder", back_populates="notes")  # Fixed relationship name
