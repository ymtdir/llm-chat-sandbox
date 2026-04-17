"""Notification service for push notifications via Firebase Cloud Messaging."""

import logging
import os
import threading
from typing import Any

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserFcmToken

logger = logging.getLogger(__name__)


class FirebaseManager:
    """Thread-safe singleton manager for Firebase Admin SDK."""

    _instance: "FirebaseManager | None" = None
    _lock = threading.Lock()
    _app: Any = None

    def __new__(cls) -> "FirebaseManager":
        """Create or return existing singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """Initialize Firebase Admin SDK with credentials."""
        if self._app is None:
            try:
                credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
                if not credentials_path:
                    raise ValueError(
                        "FIREBASE_CREDENTIALS_PATH environment variable is required. "
                        "Set it to the path of your Firebase Admin SDK credentials JSON file."
                    )
                cred = credentials.Certificate(credentials_path)
                self._app = firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase Admin SDK: {e}", exc_info=True)
                raise

    @property
    def app(self) -> Any:
        """Get Firebase app instance."""
        if self._app is None:
            self.initialize()
        return self._app


def initialize_firebase() -> None:
    """Initialize Firebase Admin SDK with credentials (compatibility function)."""
    manager = FirebaseManager()
    manager.initialize()


async def get_user_fcm_tokens(db: AsyncSession, user_id: int) -> list[str]:
    """Get all FCM tokens for a user.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        List of FCM tokens for the user

    """
    result = await db.execute(select(UserFcmToken).where(UserFcmToken.user_id == user_id))
    tokens = result.scalars().all()
    return [token.fcm_token for token in tokens]


async def send_push_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> int:
    """Send push notification to a user via FCM.

    Args:
        db: Database session
        user_id: ID of the user to notify
        title: Notification title
        body: Notification body text
        data: Additional data payload (optional)

    Returns:
        Number of successfully sent notifications

    """
    # Ensure Firebase is initialized
    manager = FirebaseManager()
    manager.app  # This will initialize if not already done

    # Get all FCM tokens for the user
    fcm_tokens = await get_user_fcm_tokens(db, user_id)

    if not fcm_tokens:
        logger.warning(f"No FCM tokens found for user {user_id}")
        return 0

    # Build notification payload
    notification = messaging.Notification(title=title, body=body)

    # Build data payload
    data_payload = data or {}

    success_count = 0
    failed_tokens: list[str] = []

    # Send to each token
    for fcm_token in fcm_tokens:
        try:
            message = messaging.Message(
                notification=notification,
                data={k: str(v) for k, v in data_payload.items()},  # FCM requires string values
                token=fcm_token,
            )

            # Send message
            response = messaging.send(message)
            logger.info(f"Successfully sent FCM notification to user {user_id}: {response}")
            success_count += 1

        except messaging.UnregisteredError:
            # Token is no longer valid, mark for deletion
            logger.warning(f"FCM token is unregistered, marking for deletion: {fcm_token}")
            failed_tokens.append(fcm_token)

        except Exception as e:
            logger.error(
                f"Failed to send FCM notification to token {fcm_token[:10]}...: {e}",
                exc_info=True,
            )

    # Clean up invalid tokens
    if failed_tokens:
        await _delete_invalid_tokens(db, failed_tokens)

    return success_count


async def _delete_invalid_tokens(db: AsyncSession, tokens: list[str]) -> None:
    """Delete invalid FCM tokens from database.

    Args:
        db: Database session
        tokens: List of invalid FCM tokens to delete

    """
    try:
        result = await db.execute(
            select(UserFcmToken).where(UserFcmToken.fcm_token.in_(tokens))
        )
        invalid_token_records = result.scalars().all()

        for token_record in invalid_token_records:
            await db.delete(token_record)

        await db.commit()
        logger.info(f"Deleted {len(invalid_token_records)} invalid FCM tokens")

    except Exception as e:
        logger.error(f"Failed to delete invalid FCM tokens: {e}", exc_info=True)
        await db.rollback()
