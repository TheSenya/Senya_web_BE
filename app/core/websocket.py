from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Callable, Any, Optional
import json
import asyncio
from datetime import datetime

class WebSocketManager:
    """
    A reusable WebSocket manager that handles connections, rooms, and message broadcasting.
    
    Design decisions:
    1. Using a class-based approach for better organization and state management
    2. Supporting both room-based and direct messaging
    3. Implementing connection tracking with nested dictionaries for O(1) lookups
    4. Adding support for custom message handlers
    """

    def __init__(self):
        # Store active connections as: {client_id: {room_id: websocket}}
        # Pros: O(1) lookup for specific client/room combinations
        # Cons: More memory usage than a flat structure
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        
        # Store room subscribers as: {room_id: set(client_ids)}
        # Pros: Fast room-based operations, easy to manage subscriptions
        # Cons: Additional memory overhead for tracking relationships
        self.room_subscribers: Dict[str, Set[str]] = {}
        
        # Store custom message handlers as: {message_type: handler_function}
        # Pros: Extensible, allows custom behavior per message type
        # Cons: Requires more setup code
        self.message_handlers: Dict[str, Callable] = {}

    async def connect(
        self, 
        websocket: WebSocket, 
        client_id: str, 
        room_id: str
    ) -> None:
        """
        Establish a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection instance
            client_id: Unique identifier for the client (e.g., user_id)
            room_id: Identifier for the room/feature (e.g., note_id, chat_id)
        """
        try:
            await websocket.accept()
            
            # Initialize nested dictionaries if they don't exist
            if client_id not in self.active_connections:
                self.active_connections[client_id] = {}
            self.active_connections[client_id][room_id] = websocket
            
            # Initialize room if it doesn't exist
            if room_id not in self.room_subscribers:
                self.room_subscribers[room_id] = set()
            self.room_subscribers[room_id].add(client_id)
            
            # Notify room subscribers about new connection
            await self.broadcast_to_room(
                room_id,
                {
                    "type": "connection_status",
                    "status": "connected",
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                exclude_client=client_id
            )
            
        except Exception as e:
            print(f"Error connecting client {client_id}: {str(e)}")
            await self.disconnect(client_id, room_id)

    async def disconnect(self, client_id: str, room_id: str) -> None:
        """
        Handle WebSocket disconnection cleanup.
        
        Design: Gracefully handle all cleanup operations to prevent memory leaks
        """
        # Remove from active connections
        if client_id in self.active_connections:
            self.active_connections[client_id].pop(room_id, None)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        
        # Remove from room subscribers
        if room_id in self.room_subscribers:
            self.room_subscribers[room_id].discard(client_id)
            if not self.room_subscribers[room_id]:
                del self.room_subscribers[room_id]
            else:
                # Notify remaining room subscribers about disconnection
                await self.broadcast_to_room(
                    room_id,
                    {
                        "type": "connection_status",
                        "status": "disconnected",
                        "client_id": client_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

    async def broadcast_to_room(
        self, 
        room_id: str, 
        message: dict, 
        exclude_client: Optional[str] = None
    ) -> None:
        """
        Broadcast a message to all clients in a room.
        
        Design: Using async broadcasting for better performance with many clients
        """
        if room_id in self.room_subscribers:
            # Create tasks for all sends to handle them concurrently
            tasks = []
            for client_id in self.room_subscribers[room_id]:
                if client_id != exclude_client:
                    if websocket := self.get_connection(client_id, room_id):
                        tasks.append(self._safe_send(websocket, message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_send(
        self, 
        websocket: WebSocket, 
        message: dict
    ) -> None:
        """
        Safely send a message through a WebSocket connection.
        
        Design: Wrapper method to handle send errors gracefully
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message: {str(e)}")

    def get_connection(
        self, 
        client_id: str, 
        room_id: str
    ) -> Optional[WebSocket]:
        """
        Get a specific WebSocket connection.
        
        Design: Safe access to nested dictionaries with None fallback
        """
        return self.active_connections.get(client_id, {}).get(room_id)

    def register_handler(
        self, 
        message_type: str, 
        handler: Callable
    ) -> None:
        """
        Register a custom message handler.
        
        Design: Allows extending functionality without modifying core code
        """
        self.message_handlers[message_type] = handler

    async def handle_message(
        self, 
        client_id: str, 
        room_id: str, 
        message: dict
    ) -> None:
        """
        Process incoming messages using registered handlers.
        
        Design: Dynamic message handling based on message type
        """
        message_type = message.get("type")
        if message_type and (handler := self.message_handlers.get(message_type)):
            await handler(client_id, room_id, message)
        else:
            print(f"No handler registered for message type: {message_type}")

# Create a global instance
websocket_manager = WebSocketManager() 