from email import contentmanager
from pydantic import BaseModel, field_validator
from datetime import datetime, date
from typing import List, Dict
import uuid
class NoteFolder(BaseModel):
    id: int
    user_id: uuid.UUID
    name: str
    parent_id: int | None
    is_root: bool

    class Config:
        from_attributes = True 

class Note(BaseModel):
    id: int
    user_id: str
    name: str
    content: Dict | None = None
    folder_id: int

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
    parent_id: int | None = None

class NoteFolderEdit(BaseModel):
    id: int
    user_id: str
    name: str
    parent_id: int

class NoteFolderDelete(BaseModel):
    id: int
    user_id: str

class NoteCreate(BaseModel):
    title: str
    format: str
    content: str | None = None
    folder_id: int
    
class NoteEdit(BaseModel):
    id: int
    user_id: str
    name: str
    content: Dict 
    folder_id: int 

class NoteDelete(BaseModel):
    id: int
    user_id: str