"""Domain service for generating diary entries from conversation history."""


from app.models.message import Message, SenderType
from app.services.llm_service import LLMService


class DiaryGenerator:
    """Generate diary entries from conversation history."""

    def __init__(self, llm_service: LLMService) -> None:
        """Initialize diary generator with LLM service.

        Args:
            llm_service: LLM service for generating diary text

        """
        self.llm_service = llm_service

    def generate_from_conversation(self, messages: list[Message]) -> str:
        """Generate diary entry from conversation messages.

        Args:
            messages: List of messages to generate diary from

        Returns:
            Generated diary text (200-300 characters)

        Raises:
            ValueError: If messages list is empty

        """
        if not messages:
            raise ValueError("Cannot generate diary from empty message list")

        # Format conversation history chronologically
        formatted_conversation = self._format_messages(messages)

        # Build prompt for diary generation
        system_prompt = self._build_diary_prompt()

        # Generate diary using LLM
        conversation_history = [{"role": "user", "content": formatted_conversation}]

        diary_text = self.llm_service.generate_response(
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            model="llama-3.3-70b-versatile",
        )

        return diary_text.strip()

    def _format_messages(self, messages: list[Message]) -> str:
        """Format messages into chronological conversation text.

        Args:
            messages: List of messages to format

        Returns:
            Formatted conversation text

        """
        formatted_lines = []

        for message in messages:
            timestamp = message.sent_at.strftime("%H:%M")
            sender = "私" if message.sender_type == SenderType.USER else "相手"
            formatted_lines.append(f"[{timestamp}] {sender}: {message.content}")

        return "\n".join(formatted_lines)

    def _build_diary_prompt(self) -> str:
        """Build system prompt for diary generation.

        Returns:
            System prompt instructing LLM to generate diary

        """
        return """あなたは日記の自動生成アシスタントです。

以下のルールに従って、会話履歴から日記を生成してください：

1. 200〜300文字で簡潔にまとめる
2. 1人称視点（「私」）で記述する
3. その日の主な出来事や会話の要点を抽出する
4. 自然な日本語で読みやすく書く
5. 会話の雰囲気や感情も含める

会話履歴から日記を生成してください。"""
