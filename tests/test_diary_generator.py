"""Tests for diary generator domain service."""

from unittest.mock import MagicMock, patch

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


def test_generate_from_conversation_success(mock_messages):
    """Test successful diary generation from messages."""
    generator = DiaryGenerator()

    with patch.object(generator.llm_service, "generate_response") as mock_generate:
        mock_generate.return_value = "今日は楽しい会話ができた。"

        result = generator.generate_from_conversation(mock_messages)

        assert result == "今日は楽しい会話ができた。"
        mock_generate.assert_called_once()

        # Verify system prompt
        call_args = mock_generate.call_args
        assert "日記の自動生成アシスタント" in call_args.kwargs["system_prompt"]


def test_generate_from_conversation_empty_list():
    """Test error when message list is empty."""
    generator = DiaryGenerator()

    with pytest.raises(ValueError, match="Cannot generate diary from empty message list"):
        generator.generate_from_conversation([])


def test_format_messages(mock_messages):
    """Test message formatting."""
    generator = DiaryGenerator()

    result = generator._format_messages(mock_messages)

    # Check format
    assert "[10:00] 私: Test message 0" in result
    assert "[10:01] 相手: Test message 1" in result
    assert "[10:02] 私: Test message 2" in result

    # Count lines
    lines = result.split("\n")
    assert len(lines) == 10


def test_build_diary_prompt():
    """Test diary prompt construction."""
    generator = DiaryGenerator()

    prompt = generator._build_diary_prompt()

    # Verify key instructions
    assert "日記の自動生成アシスタント" in prompt
    assert "200〜300文字" in prompt
    assert "1人称視点" in prompt
    assert "自然な日本語" in prompt


def test_generate_with_llm_error(mock_messages):
    """Test handling of LLM errors."""
    generator = DiaryGenerator()

    with patch.object(generator.llm_service, "generate_response") as mock_generate:
        mock_generate.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            generator.generate_from_conversation(mock_messages)


def test_generate_strips_whitespace(mock_messages):
    """Test that generated text is stripped of whitespace."""
    generator = DiaryGenerator()

    with patch.object(generator.llm_service, "generate_response") as mock_generate:
        mock_generate.return_value = "  日記のテキスト  \n"

        result = generator.generate_from_conversation(mock_messages)

        assert result == "日記のテキスト"
