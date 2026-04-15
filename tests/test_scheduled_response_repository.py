"""Tests for scheduled response repository."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_response import ResponseStatus
from app.repositories import scheduled_response_repository


@pytest.fixture
async def sample_scheduled_response(db: AsyncSession, sample_conversation):
    """Create a sample scheduled response for testing."""
    scheduled_at = datetime.now() + timedelta(minutes=5)
    response = await scheduled_response_repository.create(
        db=db,
        character_id=sample_conversation.character_id,
        conversation_id=sample_conversation.id,
        trigger_message_id=1,
        scheduled_at=scheduled_at,
        response_config={"test": "config"},
    )
    await db.flush()
    return response


async def test_create_scheduled_response(db: AsyncSession, sample_conversation):
    """Test creating a scheduled response."""
    scheduled_at = datetime.now() + timedelta(minutes=10)

    response = await scheduled_response_repository.create(
        db=db,
        character_id=sample_conversation.character_id,
        conversation_id=sample_conversation.id,
        trigger_message_id=1,
        scheduled_at=scheduled_at,
        response_config={"key": "value"},
    )

    assert response.id is not None
    assert response.character_id == sample_conversation.character_id
    assert response.conversation_id == sample_conversation.id
    assert response.trigger_message_id == 1
    assert response.status == ResponseStatus.PENDING
    assert response.response_config == {"key": "value"}
    assert response.sent_message_id is None
    assert response.sent_at is None


async def test_get_pending_no_responses(db: AsyncSession):
    """Test getting pending responses when none exist."""
    responses = await scheduled_response_repository.get_pending(db)
    assert responses == []


async def test_get_pending_with_future_responses(db: AsyncSession, sample_conversation):
    """Test that future responses are not returned."""
    # Create response scheduled for the future
    future_time = datetime.now() + timedelta(hours=1)
    await scheduled_response_repository.create(
        db=db,
        character_id=sample_conversation.character_id,
        conversation_id=sample_conversation.id,
        trigger_message_id=1,
        scheduled_at=future_time,
        response_config={},
    )
    await db.commit()

    responses = await scheduled_response_repository.get_pending(db)
    assert responses == []


async def test_get_pending_with_past_responses(db: AsyncSession, sample_conversation):
    """Test getting responses scheduled in the past."""
    # Create response scheduled for the past
    past_time = datetime.now() - timedelta(minutes=5)
    await scheduled_response_repository.create(
        db=db,
        character_id=sample_conversation.character_id,
        conversation_id=sample_conversation.id,
        trigger_message_id=1,
        scheduled_at=past_time,
        response_config={},
    )
    await db.commit()

    responses = await scheduled_response_repository.get_pending(db)
    assert len(responses) == 1
    assert responses[0].status == ResponseStatus.PENDING


async def test_get_pending_excludes_sent(db: AsyncSession, sample_conversation):
    """Test that sent responses are not returned."""
    past_time = datetime.now() - timedelta(minutes=5)

    # Create pending response
    response = await scheduled_response_repository.create(
        db=db,
        character_id=sample_conversation.character_id,
        conversation_id=sample_conversation.id,
        trigger_message_id=1,
        scheduled_at=past_time,
        response_config={},
    )
    await db.commit()

    # Mark as sent
    await scheduled_response_repository.mark_as_sent(db, response.id, 999)
    await db.commit()

    # Should not be returned
    responses = await scheduled_response_repository.get_pending(db)
    assert responses == []


async def test_get_pending_excludes_failed(db: AsyncSession, sample_conversation):
    """Test that failed responses are not returned."""
    past_time = datetime.now() - timedelta(minutes=5)

    # Create pending response
    response = await scheduled_response_repository.create(
        db=db,
        character_id=sample_conversation.character_id,
        conversation_id=sample_conversation.id,
        trigger_message_id=1,
        scheduled_at=past_time,
        response_config={},
    )
    await db.commit()

    # Mark as failed
    await scheduled_response_repository.mark_as_failed(db, response.id, "Test error")
    await db.commit()

    # Should not be returned
    responses = await scheduled_response_repository.get_pending(db)
    assert responses == []


async def test_get_pending_ordered_by_scheduled_at(db: AsyncSession, sample_conversation):
    """Test that pending responses are ordered by scheduled_at."""
    base_time = datetime.now() - timedelta(hours=1)

    # Create responses in random order
    await scheduled_response_repository.create(
        db=db,
        character_id=sample_conversation.character_id,
        conversation_id=sample_conversation.id,
        trigger_message_id=2,
        scheduled_at=base_time + timedelta(minutes=20),
        response_config={},
    )
    await scheduled_response_repository.create(
        db=db,
        character_id=sample_conversation.character_id,
        conversation_id=sample_conversation.id,
        trigger_message_id=1,
        scheduled_at=base_time + timedelta(minutes=10),
        response_config={},
    )
    await scheduled_response_repository.create(
        db=db,
        character_id=sample_conversation.character_id,
        conversation_id=sample_conversation.id,
        trigger_message_id=3,
        scheduled_at=base_time + timedelta(minutes=30),
        response_config={},
    )
    await db.commit()

    responses = await scheduled_response_repository.get_pending(db)
    assert len(responses) == 3
    # Should be ordered by scheduled_at ascending
    assert responses[0].trigger_message_id == 1
    assert responses[1].trigger_message_id == 2
    assert responses[2].trigger_message_id == 3


async def test_get_by_id_success(db: AsyncSession, sample_scheduled_response):
    """Test getting a scheduled response by ID."""
    response = await scheduled_response_repository.get_by_id(db, sample_scheduled_response.id)
    assert response is not None
    assert response.id == sample_scheduled_response.id


async def test_get_by_id_not_found(db: AsyncSession):
    """Test getting a non-existent scheduled response."""
    response = await scheduled_response_repository.get_by_id(db, 99999)
    assert response is None


async def test_mark_as_sent_success(db: AsyncSession, sample_scheduled_response):
    """Test marking a response as sent."""
    result = await scheduled_response_repository.mark_as_sent(
        db, sample_scheduled_response.id, sent_message_id=123
    )
    await db.commit()

    assert result is not None
    assert result.status == ResponseStatus.SENT
    assert result.sent_message_id == 123
    assert result.sent_at is not None


async def test_mark_as_sent_not_found(db: AsyncSession):
    """Test marking a non-existent response as sent."""
    result = await scheduled_response_repository.mark_as_sent(db, 99999, sent_message_id=123)
    assert result is None


async def test_mark_as_failed_success(db: AsyncSession, sample_scheduled_response):
    """Test marking a response as failed."""
    error_msg = "Test error message"
    result = await scheduled_response_repository.mark_as_failed(
        db, sample_scheduled_response.id, error_message=error_msg
    )
    await db.commit()

    assert result is not None
    assert result.status == ResponseStatus.FAILED
    assert result.response_config["error"] == error_msg


async def test_mark_as_failed_without_error_message(db: AsyncSession, sample_scheduled_response):
    """Test marking a response as failed without error message."""
    result = await scheduled_response_repository.mark_as_failed(db, sample_scheduled_response.id)
    await db.commit()

    assert result is not None
    assert result.status == ResponseStatus.FAILED


async def test_mark_as_failed_not_found(db: AsyncSession):
    """Test marking a non-existent response as failed."""
    result = await scheduled_response_repository.mark_as_failed(db, 99999, "Error")
    assert result is None
