"""Tests for WebSocket functionality."""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect

from app.core.security import create_access_token
from app.main import app


@pytest.fixture
def ws_client():
    """Create a WebSocket test client."""
    return TestClient(app)


def test_websocket_no_token(ws_client):
    """Test WebSocket connection without token is rejected."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with ws_client.websocket_connect("/ws/1"):
            pass
    assert exc_info.value.code == 1008  # WS_1008_POLICY_VIOLATION


def test_websocket_invalid_token(ws_client):
    """Test WebSocket connection with invalid token is rejected."""
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with ws_client.websocket_connect("/ws/1?token=invalid_token"):
            pass
    assert exc_info.value.code == 1008


async def test_websocket_user_id_mismatch(ws_client, db: AsyncSession, sample_user):
    """Test WebSocket connection with mismatched user_id is rejected."""
    # Create token for sample_user (id=1)
    token = create_access_token(data={"sub": str(sample_user.id)})

    # Try to connect with different user_id (2)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with ws_client.websocket_connect(f"/ws/2?token={token}"):
            pass
    assert exc_info.value.code == 1008


async def test_websocket_successful_connection_unit():
    """Test WebSocket endpoint logic with mocked database."""
    from unittest.mock import AsyncMock, patch

    from app.api.routes.ws import websocket_endpoint
    from app.api.websocket import ConnectionManager
    from app.models.user import User

    # Mock user from authentication
    mock_user = User(id=1, email="test@example.com", password_hash="hashed")

    # Mock websocket
    mock_websocket = MagicMock()
    mock_websocket.query_params = {"token": "valid_token"}
    mock_websocket.accept = AsyncMock()
    mock_websocket.receive_text = AsyncMock(side_effect=["ping", Exception("disconnect")])
    mock_websocket.send_text = AsyncMock()

    # Create mock connection manager
    mock_manager = MagicMock(spec=ConnectionManager)
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = MagicMock()

    # Mock authentication
    with patch("app.api.routes.ws._get_current_user_from_token", return_value=mock_user):
        # Call the endpoint directly with mocked manager
        # (will raise Exception("disconnect") to exit loop)
        try:
            await websocket_endpoint(mock_websocket, user_id=1, manager=mock_manager)
        except Exception:
            pass

        # Verify connection was established
        mock_manager.connect.assert_called_once_with(1, mock_websocket)

        # Verify ping/pong worked
        mock_websocket.send_text.assert_called_once_with("pong")


async def test_connection_manager_send_message(db: AsyncSession, sample_user):
    """Test ConnectionManager.send_message functionality."""
    from unittest.mock import AsyncMock

    from app.api.websocket import ConnectionManager

    # Create isolated manager instance for this test
    manager = ConnectionManager()

    # Mock WebSocket with AsyncMock for async methods
    mock_websocket = MagicMock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_json = AsyncMock()

    # Manually add connection
    await manager.connect(sample_user.id, mock_websocket)

    # Send message
    test_message = {"type": "test", "data": "hello"}
    await manager.send_message(sample_user.id, test_message)

    # Verify send_json was called
    mock_websocket.send_json.assert_called_once_with(test_message)

    # Cleanup
    manager.disconnect(sample_user.id)


async def test_connection_manager_send_message_user_not_connected():
    """Test sending message to non-connected user (should not raise error)."""
    from app.api.websocket import ConnectionManager

    # Create isolated manager instance for this test
    manager = ConnectionManager()

    # Try to send message to user that's not connected
    # Should not raise an error
    await manager.send_message(99999, {"type": "test", "data": "hello"})


async def test_connection_manager_broadcast():
    """Test ConnectionManager.broadcast functionality."""
    from unittest.mock import AsyncMock

    from app.api.websocket import ConnectionManager

    # Create a new manager instance for isolation
    manager = ConnectionManager()

    # Mock WebSockets for multiple users
    mock_ws1 = MagicMock()
    mock_ws1.accept = AsyncMock()
    mock_ws1.send_json = AsyncMock()
    mock_ws2 = MagicMock()
    mock_ws2.accept = AsyncMock()
    mock_ws2.send_json = AsyncMock()

    # Add connections
    await manager.connect(1, mock_ws1)
    await manager.connect(2, mock_ws2)

    # Broadcast message
    test_message = {"type": "broadcast", "data": "announcement"}
    await manager.broadcast(test_message)

    # Verify both received the message
    mock_ws1.send_json.assert_called_once_with(test_message)
    mock_ws2.send_json.assert_called_once_with(test_message)

    # Cleanup
    manager.disconnect(1)
    manager.disconnect(2)


async def test_connection_manager_send_message_error_cleanup():
    """Test that failed message sending removes the connection."""
    from unittest.mock import AsyncMock

    from app.api.websocket import ConnectionManager

    # Create isolated manager instance for this test
    manager = ConnectionManager()

    # Mock WebSocket that raises error on send
    mock_websocket = MagicMock()
    mock_websocket.accept = AsyncMock()
    mock_websocket.send_json = AsyncMock(side_effect=Exception("Connection lost"))

    user_id = 123
    await manager.connect(user_id, mock_websocket)

    # Verify connection exists
    assert user_id in manager.active_connections

    # Try to send message (should fail and cleanup)
    await manager.send_message(user_id, {"type": "test"})

    # Connection should be removed
    assert user_id not in manager.active_connections


async def test_connection_manager_broadcast_error_cleanup():
    """Test that failed broadcast sending removes problematic connections."""
    from unittest.mock import AsyncMock

    from app.api.websocket import ConnectionManager

    # Create isolated manager instance for this test
    manager = ConnectionManager()

    # Mock WebSocket that works
    mock_ws_good = MagicMock()
    mock_ws_good.accept = AsyncMock()
    mock_ws_good.send_json = AsyncMock()

    # Mock WebSocket that raises error
    mock_ws_bad = MagicMock()
    mock_ws_bad.accept = AsyncMock()
    mock_ws_bad.send_json = AsyncMock(side_effect=Exception("Connection lost"))

    user_id_good = 1
    user_id_bad = 2

    await manager.connect(user_id_good, mock_ws_good)
    await manager.connect(user_id_bad, mock_ws_bad)

    # Broadcast (should handle error gracefully)
    await manager.broadcast({"type": "test"})

    # Good connection should still exist
    assert user_id_good in manager.active_connections
    # Bad connection should be removed
    assert user_id_bad not in manager.active_connections

    # Cleanup
    manager.disconnect(user_id_good)


async def test_websocket_token_expiration(ws_client):
    """Test WebSocket connection with expired token is rejected."""
    # Create token with very short expiration
    expired_token = create_access_token(
        data={"sub": "1"}, expires_delta=timedelta(seconds=-1)  # Already expired
    )

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with ws_client.websocket_connect(f"/ws/1?token={expired_token}"):
            pass
    assert exc_info.value.code == 1008
