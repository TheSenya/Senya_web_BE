from app.models.base import BaseModel
from sqlalchemy import (
    Column, String, Integer, ForeignKey, Text, DateTime, func, Boolean
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID, JSONB

class NoteFolder(BaseModel):
    __tablename__ = "note_folder"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)
    is_root = Column(Boolean, default=False, nullable=False)
    parent_id = Column(Integer, ForeignKey("note_folder.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="note_folders")
    parent = relationship("NoteFolder", remote_side=[id], backref=backref("children", cascade="all, delete-orphan")) # backref is a shortcut to add a relationship to the parent NoteFolder
    notes = relationship('Note', back_populates='folders', cascade="all, delete-orphan")

class Note(BaseModel):
    __tablename__ = "note"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(150), nullable=False)
    folder_id = Column(Integer, ForeignKey("note_folder.id"), nullable=False)
    content = Column(JSONB, nullable=True)
    format = Column(String(20), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notes")
    folder = relationship("NoteFolder", back_populates="notes")
