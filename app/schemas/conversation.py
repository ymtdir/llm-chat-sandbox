"""Conversation schemas for API requests and responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""

    character_id: int = Field(..., gt=0, description="ID of the character to converse with")


class MessageCreate(BaseModel):
    """Schema for creating a message."""

    content: str = Field(..., min_length=1, max_length=1000, description="Message content")


class MessageResponse(BaseModel):
    """Schema for message response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    content: str
    sender_type: str
    sender_id: int
    sent_at: datetime


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    character_id: int
    created_at: datetime
    updated_at: datetime | None


class ConversationWithMessagesResponse(BaseModel):
    """Schema for conversation with recent messages."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    character_id: int
    created_at: datetime
    updated_at: datetime | None
    messages: list[MessageResponse] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    """Schema for conversation list response."""

    conversations: list[ConversationResponse]


class MessageListResponse(BaseModel):
    """Schema for message list response."""

    messages: list[MessageResponse]
