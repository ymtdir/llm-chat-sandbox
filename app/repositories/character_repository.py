"""Character repository for database operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character


async def get_by_id(db: AsyncSession, character_id: int) -> Character | None:
    """Get a character by ID."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    return result.scalar_one_or_none()


async def get_all(db: AsyncSession) -> list[Character]:
    """Get all characters."""
    result = await db.execute(select(Character))
    return list(result.scalars().all())


async def create(db: AsyncSession, name: str, config: dict) -> Character:
    """Create a new character."""
    character = Character(name=name, config=config)
    db.add(character)
    await db.flush()
    await db.refresh(character)
    return character
