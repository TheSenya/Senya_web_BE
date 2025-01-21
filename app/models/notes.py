from app.models.base import BaseModel
from sqlalchemy import (
    Column, String, Integer, ForeignKey, Text, DateTime, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

class NoteFolder(BaseModel):
    __tablename__ = "note_folder"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    name = Column(String(50), nullable=False)
    parent_id = Column(Integer, ForeignKey("note_folder.id"), nullable=False)

    user = relationship("User", back_populates="note_folder", cascade="all, delete-orphan")
    parent = relationship("NoteFolder", remote_side=[id], backref="children")
    note = relationship('Note', back_populates='note_folder', cascade="all, delete-orphan")

class Note(BaseModel):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    name = Column(String(150), nullable=False)
    folder_id = Column(Integer, ForeignKey("note_folder.id"), nullable=False)
    content = Column(JSONB, nullable=True)

    user = relationship("Note", back_populates="note")
    folder = relationship("NoteFolder", back_populates="note")
