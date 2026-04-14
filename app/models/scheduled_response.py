"""Scheduled response model."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.character import Character
    from app.models.conversation import Conversation
    from app.models.message import Message


class ResponseStatus(enum.StrEnum):
    """Scheduled response status."""

    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"


class ScheduledResponse(Base):
    """Scheduled AI response."""

    __tablename__ = "scheduled_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    character_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("characters.id"), nullable=False
    )
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    trigger_message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("messages.id"), nullable=False
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[ResponseStatus] = mapped_column(
        Enum(ResponseStatus), default=ResponseStatus.PENDING, nullable=False, index=True
    )
    response_config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    character: Mapped[Character] = relationship("Character", back_populates="scheduled_responses")
    conversation: Mapped[Conversation] = relationship(
        "Conversation", back_populates="scheduled_responses"
    )
    trigger_message: Mapped[Message] = relationship(
        "Message", back_populates="triggered_responses"
    )
