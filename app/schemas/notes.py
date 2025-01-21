from email import contentmanager
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Dict

class NoteFolderCreate(BaseModel):
    user_id: str
    name: str
    parent_id: int

class NoteFolderEdit(BaseModel):
    id: int
    user_id: str
    name: str
    parent_id: int

class NoteFolderDelete(BaseModel):
    id: int
    user_id: str

class NoteCreate(BaseModel):
    user_id: str
    name: str
    content: Dict  
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