"""Tests for notification service."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserFcmToken
from app.services.notification_service import (
    get_user_fcm_tokens,
    initialize_firebase,
    send_push_notification,
)


@pytest.fixture
async def sample_fcm_tokens(db: AsyncSession, sample_user):
    """Create sample FCM tokens for testing."""
    token1 = UserFcmToken(
        user_id=sample_user.id,
        fcm_token="test_token_1",
    )
    token2 = UserFcmToken(
        user_id=sample_user.id,
        fcm_token="test_token_2",
    )
    db.add(token1)
    db.add(token2)
    await db.flush()
    return [token1, token2]


async def test_get_user_fcm_tokens(db: AsyncSession, sample_user, sample_fcm_tokens):
    """Test getting FCM tokens for a user."""
    tokens = await get_user_fcm_tokens(db, sample_user.id)

    assert len(tokens) == 2
    assert "test_token_1" in tokens
    assert "test_token_2" in tokens


async def test_get_user_fcm_tokens_no_tokens(db: AsyncSession, sample_user):
    """Test getting FCM tokens when user has no tokens."""
    tokens = await get_user_fcm_tokens(db, sample_user.id)

    assert len(tokens) == 0


@patch("app.services.notification_service.firebase_admin")
@patch("app.services.notification_service.credentials")
def test_initialize_firebase(mock_credentials, mock_firebase_admin, monkeypatch):
    """Test Firebase initialization."""
    # Set environment variable
    monkeypatch.setenv("FIREBASE_CREDENTIALS_PATH", "./test-credentials.json")

    # Mock credentials and firebase_admin
    mock_cred = MagicMock()
    mock_credentials.Certificate.return_value = mock_cred

    # Reset global state
    import app.services.notification_service as ns

    ns._firebase_app = None

    # Call initialize
    initialize_firebase()

    # Verify Firebase was initialized
    mock_credentials.Certificate.assert_called_once_with("./test-credentials.json")
    mock_firebase_admin.initialize_app.assert_called_once_with(mock_cred)


@patch("app.services.notification_service.credentials")
def test_initialize_firebase_missing_env(mock_credentials, monkeypatch):
    """Test Firebase initialization fails without environment variable."""
    # Ensure env var is not set
    monkeypatch.delenv("FIREBASE_CREDENTIALS_PATH", raising=False)

    # Reset global state
    import app.services.notification_service as ns

    ns._firebase_app = None

    # Should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        initialize_firebase()

    assert "FIREBASE_CREDENTIALS_PATH" in str(exc_info.value)


@patch("app.services.notification_service.messaging")
@patch("app.services.notification_service.initialize_firebase")
async def test_send_push_notification_success(
    mock_initialize, mock_messaging, db: AsyncSession, sample_user, sample_fcm_tokens
):
    """Test sending push notification successfully."""
    # Mock Firebase messaging
    mock_messaging.send.return_value = "message_id_123"

    # Send notification
    sent_count = await send_push_notification(
        db=db,
        user_id=sample_user.id,
        title="Test Title",
        body="Test Body",
        data={"key": "value"},
    )

    # Verify sent to 2 devices
    assert sent_count == 2
    assert mock_messaging.send.call_count == 2


@patch("app.services.notification_service.messaging")
@patch("app.services.notification_service.initialize_firebase")
async def test_send_push_notification_no_tokens(
    mock_initialize, mock_messaging, db: AsyncSession, sample_user
):
    """Test sending push notification when user has no tokens."""
    # Send notification
    sent_count = await send_push_notification(
        db=db,
        user_id=sample_user.id,
        title="Test Title",
        body="Test Body",
    )

    # No tokens, so no messages sent
    assert sent_count == 0
    assert mock_messaging.send.call_count == 0


@patch("app.services.notification_service.messaging")
@patch("app.services.notification_service.initialize_firebase")
async def test_send_push_notification_unregistered_token(
    mock_initialize, mock_messaging, db: AsyncSession, sample_user, sample_fcm_tokens
):
    """Test handling unregistered FCM token."""
    # Mock one token as unregistered
    mock_messaging.send.side_effect = [
        "message_id_123",  # First token succeeds
        mock_messaging.UnregisteredError("Token unregistered"),  # Second fails
    ]

    # Send notification
    sent_count = await send_push_notification(
        db=db,
        user_id=sample_user.id,
        title="Test Title",
        body="Test Body",
    )

    # Only 1 successful send
    assert sent_count == 1

    # Verify unregistered token was deleted
    await db.commit()
    remaining_tokens = await get_user_fcm_tokens(db, sample_user.id)
    assert len(remaining_tokens) == 1
    assert "test_token_1" in remaining_tokens


@patch("app.services.notification_service.messaging")
@patch("app.services.notification_service.initialize_firebase")
async def test_send_push_notification_with_data(
    mock_initialize, mock_messaging, db: AsyncSession, sample_user, sample_fcm_tokens
):
    """Test sending push notification with custom data payload."""
    mock_messaging.send.return_value = "message_id_123"

    # Send with data
    data_payload = {
        "conversation_id": 123,
        "message_id": 456,
        "type": "new_message",
    }

    sent_count = await send_push_notification(
        db=db,
        user_id=sample_user.id,
        title="Character Name",
        body="Message preview...",
        data=data_payload,
    )

    assert sent_count == 2

    # Verify data was converted to strings
    call_args = mock_messaging.Message.call_args_list[0]
    message_data = call_args[1]["data"]
    assert message_data == {
        "conversation_id": "123",
        "message_id": "456",
        "type": "new_message",
    }
