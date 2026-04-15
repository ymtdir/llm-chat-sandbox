"""Conversation service for business logic."""

import html
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.response_timing import ResponseTimingCalculator
from app.models.character import Character
from app.models.conversation import Conversation
from app.models.message import Message, SenderType
from app.models.scheduled_response import ResponseStatus, ScheduledResponse
from app.repositories import conversation_repository, message_repository


async def create_conversation(
    db: AsyncSession, user_id: int, character_id: int
) -> Conversation:
    """Create a new conversation between user and character."""
    conversation = await conversation_repository.create(db, user_id, character_id)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def get_user_conversations(
    db: AsyncSession, user_id: int
) -> list[Conversation]:
    """Get all conversations for a user."""
    return await conversation_repository.get_user_conversations(db, user_id)


async def send_message(
    db: AsyncSession,
    conversation_id: int,
    user_id: int,
    content: str,
    character: Character,
) -> Message:
    """Send a message and schedule AI response.

    Args:
        db: Database session
        conversation_id: ID of the conversation
        user_id: ID of the user sending the message
        content: Message content (will be HTML-escaped for XSS protection)
        character: Character that will respond

    Returns:
        The created message

    """
    # HTML escape for XSS protection
    safe_content = html.escape(content)

    # Create user message
    message = await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content=safe_content,
        sender_type=SenderType.USER,
        sender_id=user_id,
    )

    # Calculate response delay using ResponseTimingCalculator
    current_time = datetime.now(UTC)
    delay = ResponseTimingCalculator.calculate_response_delay(
        character.config, current_time
    )
    scheduled_at = current_time + delay

    # Create scheduled response
    scheduled_response = ScheduledResponse(
        character_id=character.id,
        conversation_id=conversation_id,
        trigger_message_id=message.id,
        scheduled_at=scheduled_at,
        status=ResponseStatus.PENDING,
        response_config=character.config,
    )
    db.add(scheduled_response)

    await db.commit()
    await db.refresh(message)

    return message


async def get_messages(
    db: AsyncSession, conversation_id: int, limit: int = 50
) -> list[Message]:
    """Get recent messages for a conversation.

    Args:
        db: Database session
        conversation_id: ID of the conversation
        limit: Maximum number of messages to retrieve (default: 50)

    Returns:
        List of messages in chronological order

    """
    return await message_repository.get_recent(db, conversation_id, limit)
