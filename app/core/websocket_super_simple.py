from fastapi import WebSocket
from typing import Dict, Set, Optional
from datetime import datetime
from app.config.logger import logger

class WebSocketManager:
    """A simple WebSocket manager for handling connections and room-based messaging."""

    def __init__(self):
        # Store active connections: {room_id: {client_id: websocket}}
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """Connect a client to a specific room."""
        await websocket.accept()
        
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message: {data}")

    async def disconnect(self, client_id: str, room_id: str) -> None:
        """Remove a client from a room."""
        if room_id in self.rooms:
            self.rooms[room_id].pop(client_id, None)
            
            # Remove room if empty
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            else:
                # Notify others about disconnection
                await self.broadcast_to_room(
                    room_id,
                    {
                        "type": "connection_status",
                        "client_id": client_id,
                        "status": "disconnected",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

    async def broadcast_to_room(self, room_id: str, message: dict, exclude_client: Optional[str] = None) -> None:
        """Send a message to all clients in a room."""
        if room_id in self.rooms:
            for client_id, websocket in self.rooms[room_id].items():
                if client_id != exclude_client:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        print(f"Error sending message to {client_id}: {str(e)}")

# Create a global instance
websocket_manager = WebSocketManager() 