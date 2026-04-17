"""Scheduler jobs for processing AI responses."""

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import get_connection_manager
from app.core.database import engine
from app.models.message import Message, SenderType
from app.repositories import (
    character_repository,
    conversation_repository,
    message_repository,
    scheduled_response_repository,
)
from app.services.llm_service import LLMService
from app.services.notification_service import send_push_notification

logger = logging.getLogger(__name__)

# Maximum length for notification body text
MAX_NOTIFICATION_BODY_LENGTH = 50


def build_message_payload(ai_message: Message, conversation_id: int) -> dict:
    """Build message payload for notifications.

    Args:
        ai_message: The AI-generated message
        conversation_id: ID of the conversation

    Returns:
        Message payload dict compatible with both WebSocket and FCM

    """
    return {
        "type": "new_message",
        "conversation_id": conversation_id,
        "message": {
            "id": ai_message.id,
            "content": ai_message.content,
            "sender_type": ai_message.sender_type.value,
            "sender_id": ai_message.sender_id,
            "sent_at": ai_message.sent_at.isoformat(),
        },
    }

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def process_pending_responses() -> None:
    """Process pending scheduled responses.

    This job:
    1. Finds all pending responses that are ready to be sent
    2. For each response, generates AI reply using conversation history
    3. Handles batch reading: multiple user messages → single AI response
    4. Saves the AI response as a message
    5. Marks the scheduled response as sent or failed
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get pending responses
            current_time = datetime.now()
            pending_responses = await scheduled_response_repository.get_pending(db, current_time)

            if not pending_responses:
                logger.debug("No pending responses to process")
                return

            logger.info(f"Processing {len(pending_responses)} pending responses")

            # Group responses by conversation to handle batch reading
            conversation_groups: dict[int, list] = {}
            for response in pending_responses:
                conv_id = response.conversation_id
                if conv_id not in conversation_groups:
                    conversation_groups[conv_id] = []
                conversation_groups[conv_id].append(response)

            # Process each conversation group
            for conv_id, responses in conversation_groups.items():
                await _process_conversation_responses(db, conv_id, responses)

        except Exception as e:
            logger.error(f"Error in process_pending_responses: {e}", exc_info=True)
            await db.rollback()


async def _process_conversation_responses(
    db: AsyncSession, conversation_id: int, responses: list
) -> None:
    """Process all pending responses for a single conversation.

    Implements batch reading: If there are multiple unanswered user messages,
    respond to all of them in a single AI message.

    Args:
        db: Database session
        conversation_id: ID of the conversation
        responses: List of pending scheduled responses for this conversation
    """
    try:
        # Get conversation and character
        conversation = await conversation_repository.get_by_id(db, conversation_id)
        if not conversation:
            error_msg = f"Conversation {conversation_id} not found"
            logger.error(error_msg)
            for response in responses:
                await scheduled_response_repository.mark_as_failed(db, response.id, error_msg)
            await db.commit()
            return

        character = await character_repository.get_by_id(db, conversation.character_id)
        if not character:
            error_msg = f"Character {conversation.character_id} not found"
            logger.error(error_msg)
            for response in responses:
                await scheduled_response_repository.mark_as_failed(db, response.id, error_msg)
            await db.commit()
            return

        # Get conversation history
        messages = await message_repository.get_recent(db, conversation_id, limit=50)

        # Build conversation history for LLM
        conversation_history = []
        for msg in messages:
            role = "user" if msg.sender_type == SenderType.USER else "assistant"
            conversation_history.append({"role": role, "content": msg.content})

        # Get system prompt from character config
        system_prompt = character.config.get("system_prompt", "You are a helpful assistant.")

        # Generate AI response
        llm_service = LLMService()
        try:
            ai_response = llm_service.generate_response(
                system_prompt=system_prompt,
                conversation_history=conversation_history,
            )
        except Exception as e:
            error_msg = f"LLM generation failed: {str(e)}"
            logger.error(f"{error_msg} for conversation {conversation_id}", exc_info=True)
            # Mark all responses in this batch as failed
            for response in responses:
                await scheduled_response_repository.mark_as_failed(db, response.id, error_msg)
            await db.commit()
            return

        # Save AI response as a message
        ai_message = await message_repository.create(
            db=db,
            conversation_id=conversation_id,
            content=ai_response,
            sender_type=SenderType.CHARACTER,
            sender_id=character.id,
        )
        await db.flush()

        # Mark all responses in this batch as sent (batch reading)
        for response in responses:
            try:
                await scheduled_response_repository.mark_as_sent(db, response.id, ai_message.id)
            except Exception as e:
                # Log but don't fail the whole batch if marking fails
                logger.error(
                    f"Failed to mark response {response.id} as sent: {e}", exc_info=True
                )

        await db.commit()
        logger.info(
            f"Processed {len(responses)} responses for conversation {conversation_id}, "
            f"created message {ai_message.id}"
        )

        # Send notification to the user
        # If WebSocket is connected, use WebSocket; otherwise, use FCM push notification
        try:
            connection_manager = get_connection_manager()
            user_id = conversation.user_id

            # Build message payload (used by both WebSocket and FCM)
            message_payload = build_message_payload(ai_message, conversation_id)

            # Check if user is connected via WebSocket
            if user_id in connection_manager.active_connections:
                # Send via WebSocket
                await connection_manager.send_message(
                    user_id=user_id,
                    message=message_payload,
                )
                logger.debug(f"Sent WebSocket notification to user {user_id}")
            else:
                # User not connected - send push notification via FCM
                try:
                    # Truncate message content for notification body
                    notification_body = (
                        ai_message.content[:MAX_NOTIFICATION_BODY_LENGTH] + "..."
                        if len(ai_message.content) > MAX_NOTIFICATION_BODY_LENGTH
                        else ai_message.content
                    )

                    # Send push notification with message payload as data
                    sent_count = await send_push_notification(
                        db=db,
                        user_id=user_id,
                        title=character.name,
                        body=notification_body,
                        data=message_payload,
                    )

                    if sent_count > 0:
                        logger.info(
                            f"Sent FCM push notification to {sent_count} device(s) "
                            f"for user {user_id}"
                        )
                    else:
                        logger.warning(f"No FCM tokens available for user {user_id}")

                except Exception as fcm_error:
                    # Don't fail the job if push notification fails
                    logger.error(
                        f"Failed to send FCM push notification to user {user_id}: {fcm_error}",
                        exc_info=True,
                    )

        except Exception as e:
            # Don't fail the job if notification fails
            logger.warning(
                f"Failed to send notification to user {conversation.user_id}: {e}"
            )

    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(
            f"Unexpected error processing conversation {conversation_id}: {e}", exc_info=True
        )
        for response in responses:
            try:
                await scheduled_response_repository.mark_as_failed(
                    db, response.id, f"Unexpected error: {str(e)}"
                )
            except Exception as mark_error:
                logger.error(f"Failed to mark response as failed: {mark_error}")
        await db.commit()
