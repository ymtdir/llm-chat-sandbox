"""LLM service for AI response generation using Groq API."""

import os
from typing import Any

from groq import Groq


class LLMService:
    """Service for generating AI responses using Groq API."""

    def __init__(self) -> None:
        """Initialize Groq client."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is required. "
                "Get your API key from: https://console.groq.com/"
            )
        self.client = Groq(api_key=api_key)
        self.timeout = 30  # seconds
        self.max_retries = 3

    def generate_response(
        self,
        system_prompt: str,
        conversation_history: list[dict[str, str]],
        model: str = "llama-3.3-70b-versatile",
    ) -> str:
        """Generate AI response based on conversation history.

        Args:
            system_prompt: System prompt defining character personality
            conversation_history: List of messages with 'role' and 'content'
            model: Groq model to use (default: llama-3.3-70b-versatile)

        Returns:
            Generated response text

        Raises:
            Exception: If API call fails after retries

        """
        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,  # type: ignore[arg-type]
                    timeout=self.timeout,
                    max_tokens=1000,
                    temperature=0.8,
                )

                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("Response content is None")

                return content

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Will retry
                    continue
                # Last attempt failed

        # All retries failed
        raise Exception(
            f"Failed to generate response after {self.max_retries} attempts: {last_error}"
        )
