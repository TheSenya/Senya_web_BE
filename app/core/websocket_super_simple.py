from fastapi import WebSocket
from typing import Dict, Set, Optional
from datetime import datetime
from app.config.logger import logger
from starlette.websockets import WebSocketDisconnect
from typing import Dict, Set, Optional


class WebSocketManager:
    """A simple WebSocket manager for handling connections and room-based messaging."""

    def __init__(self):
        # Store active connections: {room_id: {client_id: websocket}}
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}
        # Track active connections with a simple counter {client_id: set(websocket)}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str, room_id: str) -> None:


        # if active connection exist for that client and has the same connection
        if client_id in self.active_connections and websocket in self.active_connections[client_id]:
            # TODO raise error user is already connected
            raise WebSocketDisconnect(code=1008) 
        
        await websocket.accept()

        # Get or create a set for this client's connections
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        
        # Add the websocket to the set
        self.active_connections[client_id].add(websocket)

        


    # async def connect(self, websocket: WebSocket) -> None:
    #     """
    #     Connect a client and handle messages until disconnection.
        
    #     This method:
    #     1. Accepts the websocket connection
    #     2. Assigns a unique client ID
    #     3. Handles incoming messages in a loop
    #     4. Catches disconnection events gracefully
    #     """
    #     # Accept the connection
    #     await websocket.accept()
        
    #     # Generate a unique client ID
    #     client_id = f"client_{self.connection_counter}"
    #     self.connection_counter += 1
        
    #     # Store the connection
    #     self.active_connections[client_id] = websocket
    #     logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        


    async def disconnect(self, client_id: str, room_id: str) -> None:
        # """Remove a client from a room."""
        # if room_id in self.rooms:
        #     self.rooms[room_id].pop(client_id, None)
            
        #     # Remove room if empty
        #     if not self.rooms[room_id]:
        #         del self.rooms[room_id]
        #         logger.info(f"Room {room_id} is now empty and has been removed")
        #     else:
        #         # Notify others about disconnection
        #         await self.broadcast_to_room(
        #             room_id,
        #             {
        #                 "type": "connection_status",
        #                 "client_id": client_id,
        #                 "status": "disconnected",
        #                 "timestamp": datetime.utcnow().isoformat()
        #             }
        #         )


        


        """Remove a client from a room."""
        # if room_id in self.rooms:
        #     self.rooms[room_id].pop(client_id, None)
            
        #     # Remove room if empty
        #     if not self.rooms[room_id]:
        #         del self.rooms[room_id]
        #         logger.info(f"Room {room_id} is now empty and has been removed")
        #     else:
        #         # Notify others about disconnection
        #         await self.broadcast_to_room(
        #             room_id,
        #             {
        #                 "type": "connection_status",
        #                 "client_id": client_id,
        #                 "status": "disconnected",
        #                 "timestamp": datetime.utcnow().isoformat()
        #             }
        #         )

    async def broadcast_to_room(self, room_id: str, message: dict, exclude_client: Optional[str] = None) -> None:
        """Send a message to all clients in a room."""
        if room_id in self.rooms:
            for client_id, websocket in self.rooms[room_id].items():
                if client_id != exclude_client:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Error sending message to {client_id}: {str(e)}")
                        # Consider removing the client if we can't send messages

    async def join_room(self, client_id: str, websocket: WebSocket, room_id: str) -> None:
        """Add a client to a specific room."""
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
            
        self.rooms[room_id][client_id] = websocket
        logger.info(f"Client {client_id} joined room {room_id}")
        
        # Notify others in the room
        await self.broadcast_to_room(
            room_id,
            {
                "type": "connection_status",
                "client_id": client_id,
                "status": "connected",
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_client=client_id
        )

# Create a global instance
websocket_manager = WebSocketManager() 