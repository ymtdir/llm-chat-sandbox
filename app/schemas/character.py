"""Character schemas for API requests and responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.character import CharacterConfig


class CharacterCreate(BaseModel):
    """Schema for creating a character."""

    name: str = Field(..., min_length=1, max_length=100)
    config: CharacterConfig


class CharacterResponse(BaseModel):
    """Schema for character response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    config: CharacterConfig
    created_at: datetime


class CharacterListResponse(BaseModel):
    """Schema for character list response."""

    characters: list[CharacterResponse]
