"""Service for diary generation and management."""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.diary_generator import DiaryGenerator
from app.models.conversation import Conversation
from app.models.diary import Diary
from app.models.message import Message
from app.repositories import conversation_repository, diary_repository, message_repository
from app.services.llm_service import LLMService

# Minimum number of messages required to generate a diary
MIN_MESSAGES_FOR_DIARY = 5


async def generate_daily_diary(
    db: AsyncSession, user_id: int, target_date: date
) -> Diary | None:
    """Generate diary for a specific user and date.

    Args:
        db: Database session
        user_id: ID of the user
        target_date: Date to generate diary for

    Returns:
        Generated diary entry, or None if insufficient messages

    Raises:
        ValueError: If diary already exists for this date

    """
    # Check if diary already exists
    existing_diary = await diary_repository.get_by_user_and_date(
        db, user_id, target_date
    )
    if existing_diary:
        raise ValueError(
            f"Diary already exists for user {user_id} on {target_date}"
        )

    # Get all conversations for the user
    conversations = await conversation_repository.get_user_conversations(db, user_id)
    if not conversations:
        return None

    # Collect all messages from target date
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())

    # Fetch all messages for user's conversations in a single query (avoid N+1)
    conversation_ids = [conv.id for conv in conversations]
    all_messages_unfiltered = await message_repository.get_messages_by_conversation_ids(
        db, conversation_ids, limit=10000
    )

    # Filter messages by date
    all_messages = [
        msg
        for msg in all_messages_unfiltered
        if start_datetime <= msg.sent_at <= end_datetime
    ]

    # Skip if insufficient messages
    if len(all_messages) < MIN_MESSAGES_FOR_DIARY:
        return None

    # Sort messages chronologically
    all_messages.sort(key=lambda m: m.sent_at)

    # Generate diary content
    llm_service = LLMService()
    generator = DiaryGenerator(llm_service)
    content = generator.generate_from_conversation(all_messages)

    # Create diary entry with metadata
    metadata = {
        "message_count": len(all_messages),
        "conversation_count": len(conversations),
        "generated_at": datetime.now().isoformat(),
    }

    diary = await diary_repository.create(
        db=db,
        user_id=user_id,
        diary_date=target_date,
        content=content,
        metadata=metadata,
    )

    return diary


async def get_diary(
    db: AsyncSession, user_id: int, diary_date: date
) -> Diary | None:
    """Get diary entry for a specific date.

    Args:
        db: Database session
        user_id: ID of the user
        diary_date: Date of the diary entry

    Returns:
        Diary entry if found, None otherwise

    """
    return await diary_repository.get_by_user_and_date(db, user_id, diary_date)


async def list_diaries(
    db: AsyncSession, user_id: int, limit: int = 30
) -> list[Diary]:
    """Get recent diary entries for a user.

    Args:
        db: Database session
        user_id: ID of the user
        limit: Maximum number of entries to return

    Returns:
        List of diary entries

    """
    return await diary_repository.list_by_user(db, user_id, limit)


async def get_users_with_messages_on_date(
    db: AsyncSession, target_date: date
) -> list[int]:
    """Get list of user IDs who have messages on the target date.

    Args:
        db: Database session
        target_date: Date to check for messages

    Returns:
        List of user IDs with messages on the target date

    """
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())

    # Query to get distinct user IDs from conversations with messages on target date
    result = await db.execute(
        select(Conversation.user_id)
        .join(Message, Message.conversation_id == Conversation.id)
        .where(Message.sent_at >= start_datetime, Message.sent_at <= end_datetime)
        .distinct()
    )

    return list(result.scalars().all())
