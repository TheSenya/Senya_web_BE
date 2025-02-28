import token
from fastapi import APIRouter, Depends, HTTPException, WebSocket,Cookie,WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import event, text
from typing import List
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
from app.core.auth import token_auth, token_auth_ws
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



@router.websocket("/ws/{note_id}")
# Temporarily uncomment to allow connections without auth
async def note_websocket(websocket: WebSocket, note_id: str,session: str = Cookie(None), db: Session = Depends(get_db)):

    logger.info(f"WebSocket connection attempt for note_id: {note_id}")

    # room_id 
    logger.info(f'session: {session}')
    logger.info(f'webscoket.cookie : {websocket.cookies}')

    room_id = f'noteroom_{note_id}'
    
    # Accept the websocket connection first
    await websocket.accept()
    
    # Generate a unique client ID for this connection
    client_id = f"client_{str(uuid.uuid4())[:8]}"

    auth_msg = await websocket.receive_text()
    auth_msg = json.loads(auth_msg)

    logger.debug('auth message', auth_msg)

    if auth_msg.get('type') == 'authenticate' and auth_msg.get('token'):
        logger.info(f"Authenticated")
        # Now that authentication passed, join the proper room
        await ws_manager.join_room(client_id, websocket, room_id)
    else:
        logger.info(f"Not authenticated")
        await websocket.close(code=1008)  # Policy violation
        return
    
    # receive messages
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received data: {data}")
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from room {room_id}")
        await ws_manager.disconnect(client_id, room_id)
    except Exception as e:
        logger.error(f"Error: {e}")
        await ws_manager.disconnect(client_id, room_id)

# ------------------------------------------------------------------------------------------------
# Note endpoints
# ------------------------------------------------------------------------------------------------

# get all notes for a user
@router.get("/{user_id}")
@token_auth()
def get_user_notes(request: Request, user_id: str, db: Session = Depends(get_db)):

    # get current user
    user = get_current_user(request, db)

    # validate is user's match and user exists
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    if user.id != user_id:
        raise HTTPException(status_code=401, detail="Wrong user")
    
    # get all note data with the user's id
    query = """
        SELECT id, user_id, name, folder_id, format FROM note
        WHERE (user_id = :user_id)
    """

    res = db.execute(text(query), {'user_id': uuid.UUID(user.id)}).all()
    
    notes= [Note.model_validate(note) for note in res]
    logger.info(f"notes: {notes}")

    return notes

# get the contents of a note
@router.get("/{user_id}/{note_id}")
def get_note_contents(user_id: str, note_id: int, db: Session = Depends(get_db)):
    return

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
            "content": note.content,
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

    res = db.execute(text(query), {"user_id": user_id, "name": note.title, "folder_id": note.folder_id, "content": json.dumps(structured_content), "format": note.format}).one()

    # insert note into database
    return row2dict(res)


@router.put("/", response_model=NoteEdit)
def update_note(note: NoteEdit, db: Session = Depends(get_db)):
    return


@router.delete("/")
def delete_note(note: NoteDelete, db: Session = Depends(get_db)):
    return



