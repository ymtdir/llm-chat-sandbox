"""Diary schemas for API requests and responses."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class DiaryResponse(BaseModel):
    """Schema for diary response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    diary_date: date
    content: str
    diary_metadata: dict | None = Field(serialization_alias="metadata")
    created_at: datetime


class DiaryListResponse(BaseModel):
    """Schema for diary list response."""

    diaries: list[DiaryResponse]
