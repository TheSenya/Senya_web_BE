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

from app.core.auth import get_current_user

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


@router.get("/folder")
@token_auth()
async def get_user_folders(request: Request, db: Session = Depends(get_db)):

    user = get_current_user(request, db)

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    user_id = user.id
    
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


# Note Folder endpoints
@router.post("/folder")
@token_auth()
async def create_note_folder(request: Request, folder: NoteFolderCreate, db: Session = Depends(get_db)):

    # get user id from request state
    logger.debug(f'request.state.user: {request.state.user}')
    user_id = request.state.user.get('id')

    logger.debug(f'user_id: {user_id}')

    #check if authenticated user id matches user id of the folder to be created
    if user_id != folder.user_id:
        raise HTTPException(status_code=401, detail="User does not have access to this folder")

    # check if user id is valid
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # check if user_id matches the user_id of the parent folder
    if folder.parent_id is not None:
        query = """
            SELECT * FROM note_folder WHERE id = :parent_id AND user_id = :user_id
        """
        res = db.execute(text(query), {"parent_id": folder.parent_id, "user_id": user_id}).one()
        
        if res is None:
            raise HTTPException(status_code=404, detail="Parent folder not found")

    # create new folder
    query = """
        INSERT INTO note_folder (user_id, name, parent_id, is_root) 
        VALUES (:user_id, :name, :parent_id, :is_root)
        RETURNING id, user_id, name, parent_id, is_root;
    """
    
    res = db.execute(text(query), {"user_id": user_id, "name": folder.name, "parent_id": folder.parent_id, "is_root": False}).one()

    logger.debug(f"create new folder res DICT: {row2dict(res)}")

    new_folder = row2dict(res)

    return NoteFolder(id=new_folder["id"], user_id=new_folder["user_id"], name=new_folder["name"], parent_id=new_folder["parent_id"], is_root=new_folder["is_root"])
    
@router.put("/folder/{folder_id}", response_model=NoteFolderEdit)
@token_auth()
async def update_note_folder(request: Request, folder: NoteFolderEdit, db: Session = Depends(get_db)):

    # get user id from request state
    user_id = request.state.user.get('id')
    logger.debug(f'user_id: {user_id}')

    # check if user id is valid
    if user_id is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # check if user_id matches the user_id for the folder to be updated
    if user_id != folder.user_id:
        raise HTTPException(status_code=401, detail="User does not have access to this folder")
    
    # check if user_id matches the user_id of the folder owner and if the folder exists
    if folder.id is not None:
        query = """
            SELECT * FROM note_folder WHERE id = :id  AND user_id = :user_id
        """
        res = db.execute(text(query), {"id": folder.id, "user_id": uuid.UUID(user_id)}).one()
        
        if res is None:
            raise HTTPException(status_code=404, detail="Folder not found")
        
    # check if parent_id is valid
    if folder.parent_id is not None:
        query = """
            SELECT * FROM note_folder WHERE id = :parent_id AND user_id = :user_id
        """
        res = db.execute(text(query), {"parent_id": folder.parent_id, "user_id": uuid.UUID(user_id)}).one()
        
        if res is None:
            raise HTTPException(status_code=404, detail="Parent folder not found")  

    # update folder
    query = """
        UPDATE note_folder SET name = :name, parent_id = :parent_id WHERE id = :id AND user_id = :user_id
    """
    res = db.execute(text(query), {"id": folder.id, "user_id": uuid.UUID(user_id), "name": folder.name, "parent_id": folder.parent_id})

    return
 

@router.delete("/folder/{folder_id}/{user_id}")
@token_auth()
async def delete_note_folder(request: Request, folder_id: int, user_id: str, db: Session = Depends(get_db)):

    # check if user_id of folder matches the current user's user_id
    if user_id != request.state.user.get('id'):   
        raise HTTPException(status_code=401, detail="User does not have access to this folder")
    
    # check if folder exists
    if folder_id is not None:   
        query = """
            SELECT * FROM note_folder WHERE id = :id AND user_id = :user_id
        """
        res = db.execute(text(query), {"id": folder_id, "user_id": uuid.UUID(user_id)}).one()   
        
        if res is None:
            raise HTTPException(status_code=404, detail="Folder not found")
        
    # delete folder
    query = """
        DELETE FROM note_folder WHERE id = :id AND user_id = :user_id
    """
    db.execute(text(query), {"id": folder_id, "user_id": uuid.UUID(user_id)})

    return {"message": "Folder deleted successfully"}


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
