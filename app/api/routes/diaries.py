"""Diary API endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.repositories import diary_repository
from app.schemas.diary import DiaryListResponse, DiaryResponse

router = APIRouter(prefix="/api/diaries", tags=["diaries"])


@router.get("", response_model=DiaryListResponse)
async def list_diaries(
    limit: int = Query(30, ge=1, le=100, description="Maximum number of diaries to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiaryListResponse:
    """Get recent diary entries for the current user."""
    diaries = await diary_repository.list_by_user(db, current_user.id, limit)
    return DiaryListResponse(diaries=diaries)


@router.get("/{diary_date}", response_model=DiaryResponse)
async def get_diary_by_date(
    diary_date: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiaryResponse:
    """Get diary entry for a specific date."""
    diary = await diary_repository.get_by_user_and_date(db, current_user.id, diary_date)
    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diary for date {diary_date} not found",
        )

    return DiaryResponse.model_validate(diary)
