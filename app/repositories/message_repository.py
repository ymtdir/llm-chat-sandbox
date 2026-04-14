"""Message repository for database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message, SenderType


async def create(
    db: AsyncSession,
    conversation_id: int,
    content: str,
    sender_type: SenderType,
    sender_id: int,
) -> Message:
    """Create a new message."""
    message = Message(
        conversation_id=conversation_id,
        content=content,
        sender_type=sender_type,
        sender_id=sender_id,
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)
    return message


async def get_recent(
    db: AsyncSession, conversation_id: int, limit: int = 50
) -> list[Message]:
    """Get recent messages for a conversation."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.sent_at.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    return list(reversed(messages))  # Return in chronological order


async def get_unanswered_user_messages(
    db: AsyncSession, conversation_id: int
) -> list[Message]:
    """Get user messages that haven't been answered by character."""
    result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.sender_type == SenderType.USER,
        )
        .order_by(Message.sent_at.asc())
    )
    return list(result.scalars().all())
