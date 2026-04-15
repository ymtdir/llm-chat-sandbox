"""Tests for LLM service."""

import os
from unittest.mock import MagicMock, patch

import pytest

from app.services.llm_service import LLMService


def test_llm_service_initialization_success():
    """Test successful initialization with API key."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "test-api-key"}):
        with patch("app.services.llm_service.Groq") as mock_groq:
            service = LLMService()
            assert service.timeout == 30
            assert service.max_retries == 3
            mock_groq.assert_called_once_with(api_key="test-api-key")


def test_llm_service_initialization_missing_api_key():
    """Test that initialization fails without API key."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            LLMService()
        assert "GROQ_API_KEY environment variable is required" in str(exc_info.value)


def test_generate_response_success():
    """Test successful response generation."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "test-api-key"}):
        with patch("app.services.llm_service.Groq") as mock_groq:
            # Mock the response
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Hello! How can I help you?"

            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            service = LLMService()
            result = service.generate_response(
                system_prompt="You are a helpful assistant.",
                conversation_history=[{"role": "user", "content": "Hello!"}],
            )

            assert result == "Hello! How can I help you?"

            # Verify API was called correctly
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "llama-3.3-70b-versatile"
            assert call_args[1]["timeout"] == 30
            assert call_args[1]["max_tokens"] == 1000
            assert call_args[1]["temperature"] == 0.8
            assert len(call_args[1]["messages"]) == 2
            assert call_args[1]["messages"][0]["role"] == "system"
            assert call_args[1]["messages"][1]["role"] == "user"


def test_generate_response_with_custom_model():
    """Test response generation with custom model."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "test-api-key"}):
        with patch("app.services.llm_service.Groq") as mock_groq:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Test response"

            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            service = LLMService()
            service.generate_response(
                system_prompt="Test prompt",
                conversation_history=[],
                model="custom-model",
            )

            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "custom-model"


def test_generate_response_none_content():
    """Test handling of None content in response."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "test-api-key"}):
        with patch("app.services.llm_service.Groq") as mock_groq:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = None

            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            service = LLMService()
            with pytest.raises(Exception) as exc_info:
                service.generate_response(
                    system_prompt="Test",
                    conversation_history=[],
                )
            assert "Response content is None" in str(exc_info.value)
            assert "Failed to generate response after 3 attempts" in str(exc_info.value)


def test_generate_response_retry_on_error():
    """Test retry logic on API errors."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "test-api-key"}):
        with patch("app.services.llm_service.Groq") as mock_groq:
            # First two calls fail, third succeeds
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = [
                Exception("API Error 1"),
                Exception("API Error 2"),
                MagicMock(choices=[MagicMock(message=MagicMock(content="Success!"))]),
            ]
            mock_groq.return_value = mock_client

            service = LLMService()
            result = service.generate_response(
                system_prompt="Test",
                conversation_history=[],
            )

            assert result == "Success!"
            assert mock_client.chat.completions.create.call_count == 3


def test_generate_response_all_retries_fail():
    """Test that exception is raised after all retries fail."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "test-api-key"}):
        with patch("app.services.llm_service.Groq") as mock_groq:
            # All calls fail
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("Persistent API Error")
            mock_groq.return_value = mock_client

            service = LLMService()
            with pytest.raises(Exception) as exc_info:
                service.generate_response(
                    system_prompt="Test",
                    conversation_history=[],
                )

            assert "Failed to generate response after 3 attempts" in str(exc_info.value)
            assert "Persistent API Error" in str(exc_info.value)
            assert mock_client.chat.completions.create.call_count == 3


def test_generate_response_conversation_history():
    """Test that conversation history is properly included."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "test-api-key"}):
        with patch("app.services.llm_service.Groq") as mock_groq:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Response"

            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_groq.return_value = mock_client

            service = LLMService()
            service.generate_response(
                system_prompt="System",
                conversation_history=[
                    {"role": "user", "content": "Message 1"},
                    {"role": "assistant", "content": "Response 1"},
                    {"role": "user", "content": "Message 2"},
                ],
            )

            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]["messages"]

            # Should have system + 3 history messages
            assert len(messages) == 4
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "System"
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "Message 1"
            assert messages[2]["role"] == "assistant"
            assert messages[2]["content"] == "Response 1"
            assert messages[3]["role"] == "user"
            assert messages[3]["content"] == "Message 2"
