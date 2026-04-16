"""WebSocket endpoints for real-time notifications."""

import logging

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from sqlalchemy import select

from app.api.deps import get_connection_manager
from app.api.websocket import ConnectionManager
from app.core.database import AsyncSessionLocal
from app.core.security import ALGORITHM, SECRET_KEY
from app.models.user import User

router = APIRouter(tags=["websocket"])

logger = logging.getLogger(__name__)


async def _get_current_user_from_token(token: str) -> User:
    """Get user from JWT token (WebSocket-specific authentication).

    This function is specific to WebSocket authentication and validates
    JWT tokens passed as query parameters.

    Args:
        token: JWT token string

    Returns:
        Authenticated User object

    Raises:
        JWTError: If token is invalid or expired
        ValueError: If user not found in database
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise JWTError("Token missing 'sub' claim")
        try:
            user_id = int(sub)
        except (TypeError, ValueError) as e:
            raise JWTError(f"Invalid 'sub' claim: {sub}") from e
    except JWTError as e:
        raise JWTError(f"Invalid token: {e}") from e

    # Get user from database
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

    if user is None:
        raise ValueError(f"User {user_id} not found")

    return user


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    manager: ConnectionManager = Depends(get_connection_manager),
) -> None:
    """WebSocket endpoint for real-time notifications.

    Args:
        websocket: WebSocket connection
        user_id: ID of the user connecting
        manager: Connection manager injected via dependency injection

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
        authenticated_user = await _get_current_user_from_token(token)

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
