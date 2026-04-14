"""Character API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.user import User
from app.schemas.character import (
    CharacterCreate,
    CharacterListResponse,
    CharacterResponse,
)

router = APIRouter(prefix="/api/characters", tags=["characters"])


@router.get("", response_model=CharacterListResponse)
async def list_characters(
    db: AsyncSession = Depends(get_db),
) -> CharacterListResponse:
    """Get all available characters."""
    result = await db.execute(select(Character))
    characters = result.scalars().all()
    return CharacterListResponse(characters=list(characters))


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
) -> Character:
    """Get a specific character by ID."""
    result = await db.execute(select(Character).where(Character.id == character_id))
    character = result.scalar_one_or_none()

    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character with id {character_id} not found",
        )

    return character


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(
    character_data: CharacterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Character:
    """Create a new character (admin only).

    Note: In a production environment, this should check for admin role.
    For now, any authenticated user can create characters.
    """
    # Create new character
    new_character = Character(
        name=character_data.name,
        config=character_data.config.model_dump(),
    )

    db.add(new_character)
    await db.commit()
    await db.refresh(new_character)

    return new_character
