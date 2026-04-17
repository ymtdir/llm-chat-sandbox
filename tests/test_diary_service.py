"""Tests for diary service.

NOTE: Message timestamps are explicitly set in tests to avoid timezone issues.
Messages use server_default=func.now() which returns UTC time, but tests use
date.today() for local date. Explicitly setting sent_at ensures messages fall
within the expected date range for filtering.
"""

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

    # Store IDs before commit to avoid MissingGreenlet
    user_id = sample_user.id
    conversation_id = sample_conversation.id
    character_id = sample_conversation.character_id

    # Create messages for today
    for i in range(10):
        msg = await message_repository.create(
            db=db,
            conversation_id=conversation_id,
            content=f"Test message {i}",
            sender_type=SenderType.USER if i % 2 == 0 else SenderType.CHARACTER,
            sender_id=user_id if i % 2 == 0 else character_id,
        )
        # Set sent_at to today to avoid timezone issues
        msg.sent_at = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=10 + i)
    await db.commit()

    # Mock DiaryGenerator
    with patch("app.services.diary_service.DiaryGenerator") as mock_generator_class:
        mock_generator = MagicMock()
        mock_generator.generate_from_conversation.return_value = "今日の日記"
        mock_generator_class.return_value = mock_generator

        diary = await diary_service.generate_daily_diary(db, user_id, target_date)

    assert diary is not None
    assert diary.user_id == user_id
    assert diary.diary_date == target_date
    assert diary.content == "今日の日記"
    assert diary.diary_metadata["message_count"] == 10
    assert diary.diary_metadata["conversation_count"] == 1


async def test_generate_daily_diary_insufficient_messages(
    db: AsyncSession, sample_conversation, sample_user
):
    """Test that diary is not generated when messages < 5."""
    target_date = date.today()

    # Store IDs before operations
    user_id = sample_user.id
    conversation_id = sample_conversation.id

    # Create only 3 messages
    for i in range(3):
        await message_repository.create(
            db=db,
            conversation_id=conversation_id,
            content=f"Test message {i}",
            sender_type=SenderType.USER,
            sender_id=user_id,
        )
    await db.commit()

    diary = await diary_service.generate_daily_diary(db, user_id, target_date)

    assert diary is None


async def test_generate_daily_diary_boundary_4_messages(
    db: AsyncSession, sample_conversation, sample_user
):
    """Test that diary is not generated with exactly 4 messages (below threshold)."""
    target_date = date.today()

    # Store IDs before operations
    user_id = sample_user.id
    conversation_id = sample_conversation.id

    # Create exactly 4 messages (below MIN_MESSAGES_FOR_DIARY)
    for i in range(4):
        await message_repository.create(
            db=db,
            conversation_id=conversation_id,
            content=f"Test message {i}",
            sender_type=SenderType.USER,
            sender_id=user_id,
        )
    await db.commit()

    diary = await diary_service.generate_daily_diary(db, user_id, target_date)

    assert diary is None


async def test_generate_daily_diary_boundary_6_messages(
    db: AsyncSession, sample_conversation, sample_user
):
    """Test that diary is generated with exactly 6 messages (above threshold)."""
    target_date = date.today()

    # Store IDs before operations
    user_id = sample_user.id
    conversation_id = sample_conversation.id
    character_id = sample_conversation.character_id

    # Create exactly 6 messages (above MIN_MESSAGES_FOR_DIARY)
    for i in range(6):
        msg = await message_repository.create(
            db=db,
            conversation_id=conversation_id,
            content=f"Test message {i}",
            sender_type=SenderType.USER if i % 2 == 0 else SenderType.CHARACTER,
            sender_id=user_id if i % 2 == 0 else character_id,
        )
        # Set sent_at to today to avoid timezone issues
        msg.sent_at = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=10 + i)
    await db.commit()

    # Mock DiaryGenerator
    with patch("app.services.diary_service.DiaryGenerator") as mock_generator_class:
        mock_generator = MagicMock()
        mock_generator.generate_from_conversation.return_value = "6件のメッセージから生成"
        mock_generator_class.return_value = mock_generator

        diary = await diary_service.generate_daily_diary(db, user_id, target_date)

    assert diary is not None
    assert diary.diary_metadata["message_count"] == 6


async def test_generate_daily_diary_duplicate_error(
    db: AsyncSession, sample_conversation, sample_user
):
    """Test error when diary already exists for the date."""
    target_date = date.today()

    # Store IDs before operations
    user_id = sample_user.id
    conversation_id = sample_conversation.id

    # Create messages
    for i in range(10):
        msg = await message_repository.create(
            db=db,
            conversation_id=conversation_id,
            content=f"Test message {i}",
            sender_type=SenderType.USER,
            sender_id=user_id,
        )
        # Set sent_at to today to avoid timezone issues
        msg.sent_at = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=10 + i)
    await db.commit()

    # Create first diary
    with patch("app.services.diary_service.DiaryGenerator") as mock_generator_class:
        mock_generator = MagicMock()
        mock_generator.generate_from_conversation.return_value = "日記1"
        mock_generator_class.return_value = mock_generator

        await diary_service.generate_daily_diary(db, user_id, target_date)
        await db.commit()

    # Try to create duplicate
    with pytest.raises(ValueError, match="Diary already exists"):
        await diary_service.generate_daily_diary(db, user_id, target_date)


async def test_generate_daily_diary_no_conversations(db: AsyncSession, sample_user):
    """Test when user has no conversations."""
    target_date = date.today()

    diary = await diary_service.generate_daily_diary(db, sample_user.id, target_date)

    assert diary is None


async def test_get_diary_success(db: AsyncSession, sample_user):
    """Test getting existing diary."""
    from app.repositories import diary_repository

    target_date = date.today()
    user_id = sample_user.id

    # Create a diary
    created_diary = await diary_repository.create(
        db=db,
        user_id=user_id,
        diary_date=target_date,
        content="Test diary content",
    )
    # Store ID before commit
    created_diary_id = created_diary.id
    await db.commit()

    # Get the diary
    diary = await diary_service.get_diary(db, user_id, target_date)

    assert diary is not None
    assert diary.id == created_diary_id
    assert diary.content == "Test diary content"


async def test_get_diary_not_found(db: AsyncSession, sample_user):
    """Test getting non-existent diary."""
    target_date = date.today()

    diary = await diary_service.get_diary(db, sample_user.id, target_date)

    assert diary is None


async def test_list_diaries(db: AsyncSession, sample_user):
    """Test listing diaries for a user."""
    from app.repositories import diary_repository

    user_id = sample_user.id

    # Create multiple diaries
    for i in range(5):
        target_date = date.today() - timedelta(days=i)
        await diary_repository.create(
            db=db,
            user_id=user_id,
            diary_date=target_date,
            content=f"Diary {i}",
        )
    await db.commit()

    diaries = await diary_service.list_diaries(db, user_id, limit=10)

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

    user_id = sample_user.id
    conversation_id = sample_conversation.id

    # Create messages for today
    msg = await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content="Test message",
        sender_type=SenderType.USER,
        sender_id=user_id,
    )
    # Set sent_at to today to avoid timezone issues
    msg.sent_at = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=10)
    await db.commit()

    user_ids = await diary_service.get_users_with_messages_on_date(db, target_date)

    assert len(user_ids) == 1
    assert user_id in user_ids


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

    user_id = sample_user.id
    conversation_id = sample_conversation.id

    # Create messages for yesterday (should be ignored)
    for i in range(10):
        msg = await message_repository.create(
            db=db,
            conversation_id=conversation_id,
            content=f"Yesterday message {i}",
            sender_type=SenderType.USER,
            sender_id=user_id,
        )
        # Manually set sent_at to yesterday
        msg.sent_at = datetime.combine(yesterday, datetime.min.time()) + timedelta(hours=i)

    # Create only 3 messages for today (insufficient)
    for i in range(3):
        await message_repository.create(
            db=db,
            conversation_id=conversation_id,
            content=f"Today message {i}",
            sender_type=SenderType.USER,
            sender_id=user_id,
        )

    await db.commit()

    # Should return None because only 3 messages on target date
    diary = await diary_service.generate_daily_diary(db, user_id, target_date)

    assert diary is None
