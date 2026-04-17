"""Tests for diary generator domain service."""

from unittest.mock import MagicMock

import pytest

from app.domain.diary_generator import DiaryGenerator
from app.models.message import SenderType


@pytest.fixture
def mock_messages():
    """Create mock messages for testing."""
    from datetime import datetime

    messages = []
    for i in range(10):
        msg = MagicMock()
        msg.content = f"Test message {i}"
        msg.sender_type = SenderType.USER if i % 2 == 0 else SenderType.CHARACTER
        msg.sent_at = datetime(2024, 1, 1, 10 + i, 0)
        messages.append(msg)
    return messages


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = MagicMock()
    service.generate_response.return_value = "今日は楽しい会話ができた。"
    return service


def test_generate_from_conversation_success(mock_messages, mock_llm_service):
    """Test successful diary generation from messages."""
    generator = DiaryGenerator(mock_llm_service)

    result = generator.generate_from_conversation(mock_messages)

    assert result == "今日は楽しい会話ができた。"
    mock_llm_service.generate_response.assert_called_once()

    # Verify system prompt contains key instructions
    call_args = mock_llm_service.generate_response.call_args
    assert "日記の自動生成アシスタント" in call_args.kwargs["system_prompt"]


def test_generate_from_conversation_empty_list(mock_llm_service):
    """Test error when message list is empty."""
    generator = DiaryGenerator(mock_llm_service)

    with pytest.raises(ValueError, match="Cannot generate diary from empty message list"):
        generator.generate_from_conversation([])


def test_generate_with_llm_error(mock_messages, mock_llm_service):
    """Test handling of LLM errors."""
    mock_llm_service.generate_response.side_effect = Exception("API Error")
    generator = DiaryGenerator(mock_llm_service)

    with pytest.raises(Exception, match="API Error"):
        generator.generate_from_conversation(mock_messages)


def test_generate_strips_whitespace(mock_messages, mock_llm_service):
    """Test that generated text is stripped of whitespace."""
    mock_llm_service.generate_response.return_value = "  日記のテキスト  \n"
    generator = DiaryGenerator(mock_llm_service)

    result = generator.generate_from_conversation(mock_messages)

    assert result == "日記のテキスト"
