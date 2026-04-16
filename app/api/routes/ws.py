"""WebSocket endpoints for real-time notifications."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError

from app.api.websocket import manager
from app.core.security import get_current_user_from_token

router = APIRouter(tags=["websocket"])

logger = logging.getLogger(__name__)


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int) -> None:
    """WebSocket endpoint for real-time notifications.

    Args:
        websocket: WebSocket connection
        user_id: ID of the user connecting

    Authentication:
        Expects a 'token' query parameter with a valid JWT token.
        Example: ws://localhost:8000/ws/1?token=eyJhbGci...
    """
    # Authenticate user via token query parameter
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(f"WebSocket connection rejected: No token provided for user {user_id}")
        return

    try:
        # Verify token and get authenticated user
        authenticated_user = await get_current_user_from_token(token)

        # Verify user_id matches token
        if authenticated_user.id != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            logger.warning(
                f"WebSocket connection rejected: User ID mismatch "
                f"(token: {authenticated_user.id}, path: {user_id})"
            )
            return

    except (JWTError, Exception) as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(f"WebSocket authentication failed for user {user_id}: {e}")
        return

    # Accept connection
    await manager.connect(user_id, websocket)

    try:
        # Keep connection alive and handle client messages
        while True:
            # Receive messages from client (e.g., ping/pong for keep-alive)
            data = await websocket.receive_text()
            logger.debug(f"Received from user {user_id}: {data}")

            # Echo back for now (can be extended for client->server messages)
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
        manager.disconnect(user_id)
