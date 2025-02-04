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
from app.core.helper import row2dict, rows2dict
from fastapi import Request
import uuid

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
    return NoteFolder(id=new_folder["id"], user_id=new_folder["user_id"], name=new_folder["name"], parent_id=new_folder["parent_id"], is_root=new_folder["is_root"])


# Note Folder endpoints
@router.post("/folder")
@token_auth()
async def create_note_folder(request: Request, folder: NoteFolderCreate, db: Session = Depends(get_db)):

    logger.debug(f"create note folder {folder.name} for user: {folder.user_id} with parent_id: {folder.parent_id}")
    # check if parent folder exists
    query = """
        SELECT * FROM note_folder WHERE id = :parent_id
    """
    res = db.execute(text(query), {"parent_id": folder.parent_id}).one()

    logger.debug(f"create note folder res: {res}")

    if res is None:
        raise HTTPException(status_code=404, detail="Parent folder not found")

    # create new folder
    query = """
        INSERT INTO note_folder (user_id, name, parent_id, is_root) 
        VALUES (:user_id, :name, :parent_id, :is_root)
        RETURNING id, user_id, name, parent_id, is_root;
    """
    res = db.execute(text(query), {"user_id": uuid.UUID(folder.user_id), "name": folder.name, "parent_id": folder.parent_id, "is_root": False}).one()

    logger.debug(f"create new folder res: {res}")
    logger.debug(f"create new folder res DICT: {row2dict(res)}")

    new_folder = row2dict(res)

    return NoteFolder(id=new_folder["id"], user_id=new_folder["user_id"], name=new_folder["name"], parent_id=new_folder["parent_id"], is_root=new_folder["is_root"])
    
@router.put("/folder", response_model=NoteFolderEdit)
@token_auth()
async def update_note_folder(request: Request, folder: NoteFolderEdit, db: Session = Depends(get_db)):
    return
 

@router.delete("/folder")
@token_auth()
async def delete_note_folder(request: Request, folder: NoteFolderDelete, db: Session = Depends(get_db)):
    return



@router.get("/folder/{user_id}")
@token_auth()
async def get_user_folders(request: Request, user_id: str, db: Session = Depends(get_db)):
    
    logger.debug(f"get user folders for user: {user_id}")
    query = """
        SELECT * FROM note_folder WHERE user_id = :user_id
    """

    res = db.execute(text(query), {"user_id": user_id}).all()

    logger.debug(f"get user folders res: {res}")

    validated_folders = [NoteFolder.model_validate(folder) for folder in res]
    logger.debug(f"get user folders validated_folders: {validated_folders}")


    logger.debug(f"get user folders res DICT: {rows2dict(res)}")


    return rows2dict(res)


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
