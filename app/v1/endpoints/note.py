import token
from fastapi import APIRouter, Depends, HTTPException, WebSocket, Cookie, WebSocketDisconnect, Body
from sqlalchemy.orm import Session
from sqlalchemy import event, text
from typing import List, Optional
import json
from app.core.database import get_db
from app.core.helper import row2dict, rows2dict
from app.schemas.notes import (
    NoteCreate,
    NoteEdit,
    NoteDelete,
    Note
)
from app.core.websocket_super_simple import WebSocketManager
from app.core.auth import token_auth, token_auth_ws, token_auth_ws_v2
from app.config.logger import logger
from fastapi import Request
import uuid
from datetime import datetime
from app.core.auth import get_current_user
from app.config.constants import NOTE_FORMAT_MARKDOWN, NOTE_FORMAT_TEXT, NOTE_FORMAT_HTML, NOTE_FORMAT_PDF, NOTE_FORMAT_IMAGE, NOTE_FORMAT_AUDIO

router = APIRouter(prefix="/note", tags=["notes"])

ws_manager = WebSocketManager()

@router.get("/file_formats")
def get_file_formats():
    return [NOTE_FORMAT_MARKDOWN, NOTE_FORMAT_TEXT, NOTE_FORMAT_HTML, NOTE_FORMAT_PDF, NOTE_FORMAT_IMAGE, NOTE_FORMAT_AUDIO]

# ------------------------------------------------------------------------------------------------
# Note websocket
# ------------------------------------------------------------------------------------------------

# @router.websocket("/ws/{note_id}")
# @token_auth_ws_v2()
# async def note_websocket(websocket: WebSocket, note_id: str, user_id: str = '', db: Session = Depends(get_db)):
#     """WebSocket endpoint for note collaboration with authentication"""
#     logger.info(f"--------------------------------------: WEBSOCKET ENDPOINT")
#     logger.info(f"WebSocket connection established for note_id: {note_id}, user_id: {user_id}")

#     try:
#         while True:
#             data = await websocket.receive_text()
#             logger.info(f"Received data from user {user_id}: {data}")
            
#             # Send response as JSON instead of plain text for better client handling
#             await websocket.send_json({
#                 "type": "message",
#                 "content": data,
#                 "note_id": note_id,
#                 "timestamp": datetime.now().isoformat()
#             })
#     except WebSocketDisconnect:
#         logger.info(f"Client {user_id} disconnected")
#         await ws_manager.disconnect(user_id, websocket)
#     except Exception as e:
#         logger.error(f"Error in WebSocket communication: {e}")
#         try:
#             await ws_manager.disconnect(user_id, websocket)
#         except:
#             pass

# ------------------------------------------------------------------------------------------------
# Note endpoints
# ------------------------------------------------------------------------------------------------

# get all notes for a user (not not content)
@router.get("/")
@token_auth()
def get_user_notes(request: Request, db: Session = Depends(get_db)):

    # get current user
    user = get_current_user(request, db)

    # validate is user's match and user exists
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # get all note data with the user's id
    query = """
        SELECT id, user_id, name, folder_id, format FROM note
        WHERE (user_id = :user_id)
    """

    res = db.execute(text(query), {'user_id': uuid.UUID(user.id)}).all()
    
    notes= [Note.model_validate(note) for note in res]
    logger.info(f"notes: {notes}")

    return notes

# get a note by id
@router.get("/{note_id}")
@token_auth()
def get_note(request: Request, note_id: int, db: Session = Depends(get_db)):

    user = get_current_user(request, db)

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
 
    # get note contents
    query = """
        SELECT content FROM note WHERE id = :note_id AND user_id = :user_id
    """

    res = db.execute(text(query), {'note_id': note_id, 'user_id': uuid.UUID(user.id)}).one()

    if res is None:
        raise HTTPException(status_code=404, detail="Note not found")

    # Extract content from JSONB structure
    try:
        content_data = json.loads(res.content) if isinstance(res.content, str) else res.content
        # Return just the content string, not the full JSONB structure
        return content_data.get("content", "")
    except (json.JSONDecodeError, KeyError, TypeError):
        # Fallback for legacy content or malformed JSON
        return res.content

# create a note
@router.post("/")
@token_auth()
async def create_note(request: Request, note: NoteCreate, db: Session = Depends(get_db)):

    user = get_current_user(request, db)

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    user_id = user.id

    # check if folder exists and user can access it
    query = """
        SELECT * FROM note_folder WHERE id = :id AND user_id = :user_id
    """
    res = db.execute(text(query), {"id": note.folder_id, "user_id": uuid.UUID(user_id)}).one()
    
    if res is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # create note
    # Convert text content to structured JSONB
    try:
        structured_content = {
            "content": note.content or "",  # Handle None/empty content
            "metadata": {
                "created_at": str(datetime.now()),
                "format": note.format,
                "version": "1.0",
                "title": note.title
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid content format: {str(e)}")

    query = """
        INSERT INTO note (user_id, name, folder_id, content, format)
        VALUES (:user_id, :name, :folder_id, :content, :format)
        RETURNING *
    """

    res = db.execute(text(query), {
        "user_id": user_id, 
        "name": note.title, 
        "folder_id": note.folder_id, 
        "content": json.dumps(structured_content), 
        "format": note.format
    }).one()

    # insert note into database
    return Note.model_validate(res)

# update a note
@router.patch("/{note_id}")
@token_auth()
def update_note(request: Request, note_id: str, note: NoteEdit, db: Session = Depends(get_db)):

    user = get_current_user(request, db)

    print(f"note: {note}, note_id: {note_id}")

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Structure content as JSONB (similar to create_note)
    try:
        structured_content = {
            "content": note.content,
            "metadata": {
                "updated_at": str(datetime.now()),
                "format": note.format,
                "version": "1.0",
                "title": note.title
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid content format: {str(e)}")
    
    # update note
    query = """
        UPDATE note SET name = :name, content = :content, format = :format 
        WHERE id = :note_id AND user_id = :user_id
        RETURNING *
    """

    res = db.execute(text(query), {
        "name": note.title, 
        "content": json.dumps(structured_content), 
        "format": note.format, 
        "note_id": note_id, 
        "user_id": uuid.UUID(user.id)
    }).one()

    if res is None:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return Note.model_validate(res)

# update a note
@router.put("/{user_id}/{note_id}")
@token_auth()
def update_note(request: Request, user_id: str, note_id: int, note: NoteEdit, db: Session = Depends(get_db)):
    return



@router.put("/", response_model=NoteEdit)
def update_note(note: NoteEdit, db: Session = Depends(get_db)):
    return


@router.delete("/")
def delete_note(note: NoteDelete, db: Session = Depends(get_db)):
    return



