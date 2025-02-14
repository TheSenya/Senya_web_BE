from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import event, text
from typing import List

from app.core.database import get_db
from app.schemas.notes import (
    NoteCreate,
    NoteEdit,
    NoteDelete,
)
from app.core.auth import token_auth
from app.config.logger import logger
from fastapi import Request
import uuid
from datetime import datetime
from app.core.auth import get_current_user
from app.config.constants import NOTE_FORMAT_MARKDOWN, NOTE_FORMAT_TEXT, NOTE_FORMAT_HTML, NOTE_FORMAT_PDF, NOTE_FORMAT_IMAGE, NOTE_FORMAT_AUDIO
router = APIRouter(prefix="/note", tags=["notes"])

@router.get("/file_formats")
def get_file_formats():
    return [NOTE_FORMAT_MARKDOWN, NOTE_FORMAT_TEXT, NOTE_FORMAT_HTML, NOTE_FORMAT_PDF, NOTE_FORMAT_IMAGE, NOTE_FORMAT_AUDIO]

# Note endpoints
@router.post("/", response_model=NoteCreate)
@token_auth()
async def create_note(request: Request, content: str, title: str, folder_id: int, format: str, db: Session = Depends(get_db)):

    user = get_current_user(request, db)

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    user_id = user.id

    # check if folder exists and user can access it
    query = """
        SELECT * FROM note_folder WHERE id = :id AND user_id = :user_id
    """
    res = db.execute(text(query), {"id": folder_id, "user_id": uuid.UUID(user_id)}).one()
    
    if res is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # create note
        # Convert text content to structured JSONB
    try:
        structured_content = {
            "content": content,
            "metadata": {
                "created_at": datetime.now(),
                "format": format,
                "version": "1.0"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid content format: {str(e)}")

    query = """
        INSTERT INTO note (user_id, name, folder_id, content, format)
        VALUES (:user_id, :name, :folder_id, :content, :format)
        RETURNING *
    """

    db.execute(text(query), {"user_id": user_id, "name": title, "folder_id": folder_id, "content": structured_content, "format": format})

    # insert note into database
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
