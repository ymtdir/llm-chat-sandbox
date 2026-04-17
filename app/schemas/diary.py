"""Diary schemas for API requests and responses."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DiaryResponse(BaseModel):
    """Schema for diary response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    diary_date: date
    content: str
    metadata: dict | None
    created_at: datetime


class DiaryListResponse(BaseModel):
    """Schema for diary list response."""

    diaries: list[DiaryResponse]
