from email import contentmanager
from pydantic import BaseModel, field_validator
from datetime import datetime, date
from typing import List, Dict
import uuid
class NoteFolder(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    is_root: bool

    class Config:
        from_attributes = True 

class Note(BaseModel):
    id: uuid.UUID
    user_id: str
    name: str
    content: Dict | None = None
    folder_id: uuid.UUID

    class Config:
        from_attributes = True 

    @field_validator('user_id', mode='before')
    def convert_uuid_to_str(cls, v):
        import uuid
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

class NoteFolderCreate(BaseModel):
    name: str
    user_id: str
    parent_id: uuid.UUID | None = None

class NoteFolderEdit(BaseModel):
    id: uuid.UUID
    user_id: str
    name: str
    parent_id: uuid.UUID

class NoteFolderDelete(BaseModel):
    id: uuid.UUID
    user_id: str

class NoteCreate(BaseModel):
    title: str
    format: str
    content: str | None = None
    folder_id: uuid.UUID
    
class NoteEdit(BaseModel):
    id: uuid.UUID
    user_id: str
    name: str
    content: Dict 
    folder_id: uuid.UUID 

class NoteDelete(BaseModel):
    id: uuid.UUID
    user_id: str