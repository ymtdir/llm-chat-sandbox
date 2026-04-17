"""Tests for diary service."""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import SenderType
from app.repositories import message_repository
from app.services import diary_service


async def test_generate_daily_diary_success(db: AsyncSession, sample_conversation, sample_user):
    """Test successful diary generation."""
    target_date = date.today()

    # Create messages for today
    for i in range(10):
        await message_repository.create(
            db=db,
            conversation_id=sample_conversation.id,
            content=f"Test message {i}",
            sender_type=SenderType.USER if i % 2 == 0 else SenderType.CHARACTER,
            sender_id=sample_user.id if i % 2 == 0 else sample_conversation.character_id,
        )
    await db.commit()

    # Mock DiaryGenerator
    with patch("app.services.diary_service.DiaryGenerator") as mock_generator_class:
        mock_generator = MagicMock()
        mock_generator.generate_from_conversation.return_value = "今日の日記"
        mock_generator_class.return_value = mock_generator

        diary = await diary_service.generate_daily_diary(db, sample_user.id, target_date)

    assert diary is not None
    assert diary.user_id == sample_user.id
    assert diary.diary_date == target_date
    assert diary.content == "今日の日記"
    assert diary.diary_metadata["message_count"] == 10
    assert diary.diary_metadata["conversation_count"] == 1


async def test_generate_daily_diary_insufficient_messages(
    db: AsyncSession, sample_conversation, sample_user
):
    """Test that diary is not generated when messages < 5."""
    target_date = date.today()

    # Create only 3 messages
    for i in range(3):
        await message_repository.create(
            db=db,
            conversation_id=sample_conversation.id,
            content=f"Test message {i}",
            sender_type=SenderType.USER,
            sender_id=sample_user.id,
        )
    await db.commit()

    diary = await diary_service.generate_daily_diary(db, sample_user.id, target_date)

    assert diary is None


async def test_generate_daily_diary_duplicate_error(
    db: AsyncSession, sample_conversation, sample_user
):
    """Test error when diary already exists for the date."""
    target_date = date.today()

    # Create messages
    for i in range(10):
        await message_repository.create(
            db=db,
            conversation_id=sample_conversation.id,
            content=f"Test message {i}",
            sender_type=SenderType.USER,
            sender_id=sample_user.id,
        )
    await db.commit()

    # Create first diary
    with patch("app.services.diary_service.DiaryGenerator") as mock_generator_class:
        mock_generator = MagicMock()
        mock_generator.generate_from_conversation.return_value = "日記1"
        mock_generator_class.return_value = mock_generator

        await diary_service.generate_daily_diary(db, sample_user.id, target_date)
        await db.commit()

    # Try to create duplicate
    with pytest.raises(ValueError, match="Diary already exists"):
        await diary_service.generate_daily_diary(db, sample_user.id, target_date)


async def test_generate_daily_diary_no_conversations(db: AsyncSession, sample_user):
    """Test when user has no conversations."""
    target_date = date.today()

    diary = await diary_service.generate_daily_diary(db, sample_user.id, target_date)

    assert diary is None


async def test_get_diary_success(db: AsyncSession, sample_user):
    """Test getting existing diary."""
    from app.repositories import diary_repository

    target_date = date.today()

    # Create a diary
    created_diary = await diary_repository.create(
        db=db,
        user_id=sample_user.id,
        diary_date=target_date,
        content="Test diary content",
    )
    await db.commit()

    # Get the diary
    diary = await diary_service.get_diary(db, sample_user.id, target_date)

    assert diary is not None
    assert diary.id == created_diary.id
    assert diary.content == "Test diary content"


async def test_get_diary_not_found(db: AsyncSession, sample_user):
    """Test getting non-existent diary."""
    target_date = date.today()

    diary = await diary_service.get_diary(db, sample_user.id, target_date)

    assert diary is None


async def test_list_diaries(db: AsyncSession, sample_user):
    """Test listing diaries for a user."""
    from app.repositories import diary_repository

    # Create multiple diaries
    for i in range(5):
        target_date = date.today() - timedelta(days=i)
        await diary_repository.create(
            db=db,
            user_id=sample_user.id,
            diary_date=target_date,
            content=f"Diary {i}",
        )
    await db.commit()

    diaries = await diary_service.list_diaries(db, sample_user.id, limit=10)

    assert len(diaries) == 5
    # Should be ordered by date descending
    assert diaries[0].diary_date == date.today()
    assert diaries[4].diary_date == date.today() - timedelta(days=4)


async def test_list_diaries_empty(db: AsyncSession, sample_user):
    """Test listing diaries when none exist."""
    diaries = await diary_service.list_diaries(db, sample_user.id)

    assert diaries == []


async def test_get_users_with_messages_on_date(db: AsyncSession, sample_conversation, sample_user):
    """Test getting users with messages on a specific date."""
    target_date = date.today()

    # Create messages for today
    await message_repository.create(
        db=db,
        conversation_id=sample_conversation.id,
        content="Test message",
        sender_type=SenderType.USER,
        sender_id=sample_user.id,
    )
    await db.commit()

    user_ids = await diary_service.get_users_with_messages_on_date(db, target_date)

    assert len(user_ids) == 1
    assert sample_user.id in user_ids


async def test_get_users_with_messages_on_date_no_messages(db: AsyncSession):
    """Test when no messages exist on target date."""
    target_date = date.today()

    user_ids = await diary_service.get_users_with_messages_on_date(db, target_date)

    assert user_ids == []


async def test_generate_daily_diary_filters_by_date(
    db: AsyncSession, sample_conversation, sample_user
):
    """Test that only messages from target date are used."""
    target_date = date.today()
    yesterday = target_date - timedelta(days=1)

    # Create messages for yesterday (should be ignored)
    for i in range(10):
        msg = await message_repository.create(
            db=db,
            conversation_id=sample_conversation.id,
            content=f"Yesterday message {i}",
            sender_type=SenderType.USER,
            sender_id=sample_user.id,
        )
        # Manually set sent_at to yesterday
        msg.sent_at = datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=i)

    # Create only 3 messages for today (insufficient)
    for i in range(3):
        await message_repository.create(
            db=db,
            conversation_id=sample_conversation.id,
            content=f"Today message {i}",
            sender_type=SenderType.USER,
            sender_id=sample_user.id,
        )

    await db.commit()

    # Should return None because only 3 messages on target date
    diary = await diary_service.generate_daily_diary(db, sample_user.id, target_date)

    assert diary is None
