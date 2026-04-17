"""Diary repository for database operations."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diary import Diary


async def create(
    db: AsyncSession,
    user_id: int,
    diary_date: date,
    content: str,
    metadata: dict | None = None,
) -> Diary:
    """Create a new diary entry.

    Args:
        db: Database session
        user_id: ID of the user
        diary_date: Date of the diary entry
        content: Generated diary text
        metadata: Optional metadata (e.g., message count, generation info)

    Returns:
        Created diary entry

    """
    diary = Diary(
        user_id=user_id,
        diary_date=diary_date,
        content=content,
        diary_metadata=metadata,
    )
    db.add(diary)
    await db.flush()
    await db.refresh(diary)
    return diary


async def get_by_user_and_date(
    db: AsyncSession, user_id: int, diary_date: date
) -> Diary | None:
    """Get diary entry for a specific user and date.

    Args:
        db: Database session
        user_id: ID of the user
        diary_date: Date of the diary entry

    Returns:
        Diary entry if found, None otherwise

    """
    result = await db.execute(
        select(Diary).where(Diary.user_id == user_id, Diary.diary_date == diary_date)
    )
    return result.scalar_one_or_none()


async def list_by_user(
    db: AsyncSession, user_id: int, limit: int = 30
) -> list[Diary]:
    """Get recent diary entries for a user.

    Args:
        db: Database session
        user_id: ID of the user
        limit: Maximum number of entries to return

    Returns:
        List of diary entries, ordered by date descending

    """
    result = await db.execute(
        select(Diary)
        .where(Diary.user_id == user_id)
        .order_by(Diary.diary_date.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
