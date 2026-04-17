"""Tests for scheduler jobs.

NOTE: Tests have been fixed by storing fixture IDs before async operations
to avoid MissingGreenlet errors when accessing expired SQLAlchemy objects.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import SenderType
from app.models.scheduled_response import ResponseStatus
from app.repositories import message_repository, scheduled_response_repository
from app.scheduler.jobs import _process_conversation_responses, process_pending_responses


async def test_process_pending_responses_no_pending(db: AsyncSession):
    """Test processing when there are no pending responses."""
    # Mock the session to return our test db
    with patch("app.scheduler.jobs.AsyncSessionLocal") as mock_session:
        mock_session.return_value.__aenter__.return_value = db

        # Should not raise an error
        await process_pending_responses()


async def test_process_pending_responses_with_pending(
    db: AsyncSession, sample_conversation, sample_character
):
    """Test processing a pending response."""
    # Store IDs before operations to avoid MissingGreenlet
    conversation_id = sample_conversation.id
    user_id = sample_conversation.user_id
    character_id = sample_character.id
    character_config = sample_character.config

    # Create a user message
    user_message = await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content="Hello, how are you?",
        sender_type=SenderType.USER,
        sender_id=user_id,
    )
    user_message_id = user_message.id

    # Create a pending scheduled response (past due)
    past_time = datetime.now() - timedelta(minutes=5)
    scheduled_response = await scheduled_response_repository.create(
        db=db,
        character_id=character_id,
        conversation_id=conversation_id,
        trigger_message_id=user_message_id,
        scheduled_at=past_time,
        response_config=character_config,
    )
    scheduled_response_id = scheduled_response.id
    await db.commit()

    # Mock LLM service
    with patch("app.scheduler.jobs.LLMService") as mock_llm_service:
        mock_service = MagicMock()
        mock_service.generate_response.return_value = "I'm doing well, thank you!"
        mock_llm_service.return_value = mock_service

        # Mock the session to return our test db
        with patch("app.scheduler.jobs.AsyncSessionLocal") as mock_session:
            mock_session.return_value.__aenter__.return_value = db

            await process_pending_responses()

    # Verify the scheduled response was marked as sent
    updated_response = await scheduled_response_repository.get_by_id(db, scheduled_response_id)
    assert updated_response.status == ResponseStatus.SENT
    assert updated_response.sent_message_id is not None
    assert updated_response.sent_at is not None

    # Verify a message was created
    messages = await message_repository.get_recent(db, conversation_id)
    assert len(messages) == 2  # User message + AI response
    assert messages[1].sender_type == SenderType.CHARACTER
    assert messages[1].content == "I'm doing well, thank you!"


async def test_process_pending_responses_batch_reading(
    db: AsyncSession, sample_conversation, sample_character
):
    """Test batch reading: multiple user messages get one AI response."""
    # Store IDs before operations to avoid MissingGreenlet
    conversation_id = sample_conversation.id
    user_id = sample_conversation.user_id
    character_id = sample_character.id
    character_config = sample_character.config

    # Create multiple user messages
    msg1 = await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content="Hello!",
        sender_type=SenderType.USER,
        sender_id=user_id,
    )
    msg1_id = msg1.id
    msg2 = await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content="How are you?",
        sender_type=SenderType.USER,
        sender_id=user_id,
    )
    msg2_id = msg2.id
    msg3 = await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content="What's up?",
        sender_type=SenderType.USER,
        sender_id=user_id,
    )
    msg3_id = msg3.id

    # Create multiple pending responses for the same conversation
    past_time = datetime.now() - timedelta(minutes=5)
    resp1 = await scheduled_response_repository.create(
        db=db,
        character_id=character_id,
        conversation_id=conversation_id,
        trigger_message_id=msg1_id,
        scheduled_at=past_time,
        response_config=character_config,
    )
    resp1_id = resp1.id
    resp2 = await scheduled_response_repository.create(
        db=db,
        character_id=character_id,
        conversation_id=conversation_id,
        trigger_message_id=msg2_id,
        scheduled_at=past_time,
        response_config=character_config,
    )
    resp2_id = resp2.id
    resp3 = await scheduled_response_repository.create(
        db=db,
        character_id=character_id,
        conversation_id=conversation_id,
        trigger_message_id=msg3_id,
        scheduled_at=past_time,
        response_config=character_config,
    )
    resp3_id = resp3.id
    await db.commit()

    # Mock LLM service
    with patch("app.scheduler.jobs.LLMService") as mock_llm_service:
        mock_service = MagicMock()
        mock_service.generate_response.return_value = "Hey! I'm good, just been busy!"
        mock_llm_service.return_value = mock_service

        with patch("app.scheduler.jobs.AsyncSessionLocal") as mock_session:
            mock_session.return_value.__aenter__.return_value = db

            await process_pending_responses()

    # All three responses should be marked as sent
    for resp_id in [resp1_id, resp2_id, resp3_id]:
        updated_resp = await scheduled_response_repository.get_by_id(db, resp_id)
        assert updated_resp.status == ResponseStatus.SENT

    # But only ONE AI message should be created (batch reading)
    messages = await message_repository.get_recent(db, conversation_id)
    character_messages = [m for m in messages if m.sender_type == SenderType.CHARACTER]
    assert len(character_messages) == 1

    # All responses should reference the same message
    resp1_updated = await scheduled_response_repository.get_by_id(db, resp1_id)
    resp2_updated = await scheduled_response_repository.get_by_id(db, resp2_id)
    resp3_updated = await scheduled_response_repository.get_by_id(db, resp3_id)
    assert resp1_updated.sent_message_id == resp2_updated.sent_message_id
    assert resp2_updated.sent_message_id == resp3_updated.sent_message_id


async def test_process_pending_responses_llm_error(
    db: AsyncSession, sample_conversation, sample_character
):
    """Test handling of LLM errors."""
    # Store IDs before operations to avoid MissingGreenlet
    conversation_id = sample_conversation.id
    user_id = sample_conversation.user_id
    character_id = sample_character.id
    character_config = sample_character.config

    # Create a user message and pending response
    user_message = await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content="Test message",
        sender_type=SenderType.USER,
        sender_id=user_id,
    )
    user_message_id = user_message.id
    past_time = datetime.now() - timedelta(minutes=5)
    scheduled_response = await scheduled_response_repository.create(
        db=db,
        character_id=character_id,
        conversation_id=conversation_id,
        trigger_message_id=user_message_id,
        scheduled_at=past_time,
        response_config=character_config,
    )
    scheduled_response_id = scheduled_response.id
    await db.commit()

    # Mock LLM service to raise an error
    with patch("app.scheduler.jobs.LLMService") as mock_llm_service:
        mock_service = MagicMock()
        mock_service.generate_response.side_effect = Exception("API Error")
        mock_llm_service.return_value = mock_service

        with patch("app.scheduler.jobs.AsyncSessionLocal") as mock_session:
            mock_session.return_value.__aenter__.return_value = db

            # Should not raise, should handle the error gracefully
            await process_pending_responses()

    # Response should be marked as failed
    updated_response = await scheduled_response_repository.get_by_id(db, scheduled_response_id)
    assert updated_response.status == ResponseStatus.FAILED


async def test_process_conversation_responses_success(
    db: AsyncSession, sample_conversation, sample_character
):
    """Test processing responses for a conversation."""
    # Store IDs before operations to avoid MissingGreenlet
    conversation_id = sample_conversation.id
    user_id = sample_conversation.user_id
    character_id = sample_character.id
    character_config = sample_character.config

    # Create a user message
    user_message = await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content="Hello!",
        sender_type=SenderType.USER,
        sender_id=user_id,
    )
    user_message_id = user_message.id
    await db.commit()

    # Create a pending response
    past_time = datetime.now() - timedelta(minutes=5)
    scheduled_response = await scheduled_response_repository.create(
        db=db,
        character_id=character_id,
        conversation_id=conversation_id,
        trigger_message_id=user_message_id,
        scheduled_at=past_time,
        response_config=character_config,
    )
    scheduled_response_id = scheduled_response.id
    await db.commit()

    # Retrieve fresh response object after commit to avoid MissingGreenlet
    fresh_response = await scheduled_response_repository.get_by_id(db, scheduled_response_id)

    # Mock LLM service
    with patch("app.scheduler.jobs.LLMService") as mock_llm_service:
        mock_service = MagicMock()
        mock_service.generate_response.return_value = "Hi there!"
        mock_llm_service.return_value = mock_service

        await _process_conversation_responses(
            db, conversation_id, [fresh_response]
        )

    # Verify LLM was called with correct parameters
    mock_service.generate_response.assert_called_once()
    call_args = mock_service.generate_response.call_args
    assert call_args[1]["system_prompt"] == "You are a test character."
    assert len(call_args[1]["conversation_history"]) == 1
    assert call_args[1]["conversation_history"][0]["role"] == "user"
    assert call_args[1]["conversation_history"][0]["content"] == "Hello!"


async def test_process_conversation_responses_conversation_not_found(db: AsyncSession):
    """Test error handling when conversation doesn't exist."""
    # Should not raise, should handle the error gracefully
    await _process_conversation_responses(db, 99999, [])


async def test_process_conversation_responses_character_not_found(
    db: AsyncSession, sample_conversation, sample_character
):
    """Test error handling when character doesn't exist."""
    # Store IDs before operations to avoid MissingGreenlet
    conversation_id = sample_conversation.id
    user_id = sample_conversation.user_id
    character_id = sample_character.id
    character_config = sample_character.config

    # Create a pending response first
    past_time = datetime.now() - timedelta(minutes=5)
    scheduled_response = await scheduled_response_repository.create(
        db=db,
        character_id=character_id,
        conversation_id=conversation_id,
        trigger_message_id=1,
        scheduled_at=past_time,
        response_config=character_config,
    )
    scheduled_response_id = scheduled_response.id
    await db.commit()

    # Delete the character (this will cause cascade delete issues, so we test with invalid ID instead)
    # Manually update conversation to point to non-existent character
    from app.repositories import conversation_repository
    conv = await conversation_repository.get_by_id(db, conversation_id)
    conv.character_id = 99999
    await db.commit()

    # Retrieve fresh response object after commit to avoid MissingGreenlet
    fresh_response = await scheduled_response_repository.get_by_id(db, scheduled_response_id)

    # Should not raise, should handle the error gracefully
    await _process_conversation_responses(db, conversation_id, [fresh_response])

    # Verify response was marked as failed
    updated_response = await scheduled_response_repository.get_by_id(db, scheduled_response_id)
    assert updated_response.status == ResponseStatus.FAILED


async def test_process_conversation_responses_with_history(
    db: AsyncSession, sample_conversation, sample_character
):
    """Test that conversation history is properly built."""
    # Store IDs before operations to avoid MissingGreenlet
    conversation_id = sample_conversation.id
    user_id = sample_conversation.user_id
    character_id = sample_character.id
    character_config = sample_character.config

    # Create a conversation with history
    await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content="User message 1",
        sender_type=SenderType.USER,
        sender_id=user_id,
    )
    await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content="AI response 1",
        sender_type=SenderType.CHARACTER,
        sender_id=character_id,
    )
    await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content="User message 2",
        sender_type=SenderType.USER,
        sender_id=user_id,
    )
    await db.commit()

    # Create pending response
    past_time = datetime.now() - timedelta(minutes=5)
    scheduled_response = await scheduled_response_repository.create(
        db=db,
        character_id=character_id,
        conversation_id=conversation_id,
        trigger_message_id=1,
        scheduled_at=past_time,
        response_config=character_config,
    )
    scheduled_response_id = scheduled_response.id
    await db.commit()

    # Retrieve fresh response object after commit to avoid MissingGreenlet
    fresh_response = await scheduled_response_repository.get_by_id(db, scheduled_response_id)

    # Mock LLM service
    with patch("app.scheduler.jobs.LLMService") as mock_llm_service:
        mock_service = MagicMock()
        mock_service.generate_response.return_value = "Response"
        mock_llm_service.return_value = mock_service

        await _process_conversation_responses(
            db, conversation_id, [fresh_response]
        )

        # Verify conversation history was built correctly
        call_args = mock_service.generate_response.call_args
        history = call_args[1]["conversation_history"]
        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "User message 1"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "AI response 1"
        assert history[2]["role"] == "user"
        assert history[2]["content"] == "User message 2"
