from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import event, text
from typing import List

from app.core.database import get_db
from app.schemas.notes import (
    NoteCreate,
    NoteEdit,
    NoteDelete,
    NoteFolderCreate,
    NoteFolderEdit,
    NoteFolderDelete,
)
from app.schemas.notes import Note, NoteFolder
from app.schemas.user import User
from app.core.auth import token_auth
from app.config.logger import logger
from app.core.helper import row2dict

router = APIRouter(prefix="/note", tags=["notes"])


# Create a default Root folder
def create_default_folder(db, username, user_id) -> NoteFolder:
    logger.debug(
        f"create root folder for user: {username} with id: {user_id}"
    )

    query = """
        INSERT INTO note_folder (user_id, name, parent_id, is_root) 
        VALUES (:user_id ,:name, :parent_id, :is_root)
        RETURNING id, user_id, name, parent_id, is_root;
    """
    res = db.execute(
        text(query),
        {
            "user_id": user_id,
            "name": 'ROOT',
            "parent_id": None,
            "is_root": True,
        },
    ).one()
    logger.debug(f"create root folder res: {res}")
    logger.debug(f"create root folder res DICT: {row2dict(res)}")

    new_folder = row2dict(res)

    logger.debug(f"root note create {new_folder}")
    return NoteFolder(id=new_folder["id"], user_id=str(new_folder["user_id"]), name=new_folder["name"], parent_id=new_folder["parent_id"], is_root=new_folder["is_root"])


# Note Folder endpoints
@router.post("/folder", response_model=NoteFolderCreate)
@token_auth()
def create_note_folder(folder: NoteFolderCreate, db: Session = Depends(get_db)):

    return


@router.put("/folder", response_model=NoteFolderEdit)
def update_note_folder(folder: NoteFolderEdit, db: Session = Depends(get_db)):
    return


@router.delete("/folder")
def delete_note_folder(folder: NoteFolderDelete, db: Session = Depends(get_db)):
    return


@router.get("/folder/{user_id}")
@token_auth()
def get_user_folders(user_id: str, db: Session = Depends(get_db)):

    return


# Note endpoints
@router.post("/", response_model=NoteCreate)
@token_auth()
def create_note(note: NoteCreate, db: Session = Depends(get_db)):

    return


@router.put("/", response_model=NoteEdit)
def update_note(note: NoteEdit, db: Session = Depends(get_db)):
    return


@router.delete("/")
def delete_note(note: NoteDelete, db: Session = Depends(get_db)):
    return


@router.get("/{user_id}")
def get_user_notes(user_id: str, folder_id: int | None = None, db: Session = Depends(get_db)):
    return
