from app.models.base import BaseModel
from sqlalchemy import (
    Column, String, Integer, ForeignKey, Text, DateTime, func, Boolean
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import text

# we're not using uuid_generate_v4() as it requires the enabling of uuid-ossp extension, but instead  gen_random_uuid() for postgres db 13+

class NoteFolder(BaseModel):
    __tablename__ = "note_folder"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(50), nullable=False)
    is_root = Column(Boolean, default=False, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("note_folder.id", ondelete="CASCADE"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="note_folders")
    parent = relationship("NoteFolder", remote_side=[id], backref=backref("children", cascade="all, delete-orphan"))
    notes = relationship('Note', back_populates='folder', cascade="all, delete-orphan")

class Note(BaseModel):
    __tablename__ = "note"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(150), nullable=False)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("note_folder.id", ondelete="CASCADE"), nullable=False)
    content = Column(JSONB, nullable=True)
    format = Column(String(20), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notes")
    folder = relationship("NoteFolder", back_populates="notes")
