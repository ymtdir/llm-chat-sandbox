"""Conversation repository for database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


async def create(
    db: AsyncSession, user_id: int, character_id: int
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(user_id=user_id, character_id=character_id)
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)
    return conversation


async def get_by_id(db: AsyncSession, conversation_id: int) -> Conversation | None:
    """Get conversation by ID."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    return result.scalar_one_or_none()


async def get_user_conversations(
    db: AsyncSession, user_id: int
) -> list[Conversation]:
    """Get all conversations for a user."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())
