from fastapi import WebSocket
from typing import Dict, Set, Optional
from datetime import datetime
from app.config.logger import logger
from starlette.websockets import WebSocketDisconnect
from typing import Dict, Set, Optional


class WebSocketManager:
    """A simple WebSocket manager for handling connections and room-based messaging."""

    def __init__(self):
        # Track pending connections {client_id: set(websocket)}
        self.pending_connections: Dict[str, WebSocket] = {}
        # Track active connections {client_id: set(websocket)}
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:

        # check if current user already has a connection open
        if client_id in self.active_connections:
            try:
                old_connection = self.active_connections[client_id]
                await old_connection.close(code=1000)
                logger.info(f"Closed existing connection for client {client_id}")
            except Exception as e:
                logger.error(f"Error closing existing connection: {e}")
        
        # Accept the new connection
        await websocket.accept()
        
        # Store the connection
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected successfully")


    async def disconnect(self, client_id: str, websocket: WebSocket) -> None:
        # Remove from active connections
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        logger.info(f"Client {client_id} disconnected successfully")

        try:
            await websocket.close()
        except Exception as e:
            logger.error(f"Error closing websocket: {e}  might already be closed")


# Create a global instance
websocket_manager = WebSocketManager() 