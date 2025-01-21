from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.notes import (
    NoteCreate, NoteEdit, NoteDelete,
    NoteFolderCreate, NoteFolderEdit, NoteFolderDelete
)
from app.models.notes import Note, NoteFolder

router = APIRouter(
    prefix="/note",
    tags=["notes"]
)

# Note Folder endpoints
@router.post("/folder", response_model=NoteFolderCreate)
def create_note_folder(
    folder: NoteFolderCreate,
    db: Session = Depends(get_db)
):
    

    return 

@router.put("/folder", response_model=NoteFolderEdit)
def update_note_folder(
    folder: NoteFolderEdit,
    db: Session = Depends(get_db)
):
    return 

@router.delete("/folder")
def delete_note_folder(
    folder: NoteFolderDelete,
    db: Session = Depends(get_db)
):
    return 

@router.get("/folder/{user_id}")
def get_user_folders(
    user_id: str,
    db: Session = Depends(get_db)
):
    return 

# Note endpoints
@router.post("/", response_model=NoteCreate)
def create_note(
    note: NoteCreate,
    db: Session = Depends(get_db)
):
    return 

@router.put("/", response_model=NoteEdit)
def update_note(
    note: NoteEdit,
    db: Session = Depends(get_db)
):
    return 

@router.delete("/")
def delete_note(
    note: NoteDelete,
    db: Session = Depends(get_db)
):
    return 

@router.get("/{user_id}")
def get_user_notes(
    user_id: str,
    folder_id: int = None,
    db: Session = Depends(get_db)
):
    return