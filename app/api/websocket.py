"""WebSocket connection manager for real-time notifications."""

import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections.

    Handles connection lifecycle (connect, disconnect) and message broadcasting
    to specific users or all connected clients.
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        # Map user_id to WebSocket connection
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection.

        Args:
            user_id: ID of the user connecting
            websocket: WebSocket connection instance
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected via WebSocket")

    def disconnect(self, user_id: int) -> None:
        """Remove a WebSocket connection.

        Args:
            user_id: ID of the user disconnecting
        """
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket")

    async def send_message(self, user_id: int, message: dict[str, Any]) -> None:
        """Send a message to a specific user.

        Args:
            user_id: ID of the target user
            message: Message data to send (will be JSON-encoded)
        """
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(message)
                logger.debug(f"Sent message to user {user_id}: {message.get('type')}")
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                # Remove stale connection
                self.disconnect(user_id)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected users.

        Args:
            message: Message data to send (will be JSON-encoded)
        """
        disconnected_users = []

        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to user {user_id}: {e}")
                disconnected_users.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)


# Global connection manager instance
manager = ConnectionManager()
