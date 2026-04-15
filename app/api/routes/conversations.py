"""Conversation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.character import Character
from app.models.conversation import Conversation
from app.models.user import User
from app.repositories import conversation_repository
from app.schemas.conversation import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
)
from app.services import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Conversation:
    """Create a new conversation."""
    # Verify character exists
    result = await db.execute(
        select(Character).where(Character.id == conversation_data.character_id)
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character with id {conversation_data.character_id} not found",
        )

    return await conversation_service.create_conversation(
        db, current_user.id, conversation_data.character_id
    )


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """Get all conversations for the current user."""
    conversations = await conversation_service.get_user_conversations(db, current_user.id)
    return ConversationListResponse(conversations=conversations)


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Send a message in a conversation."""
    # Get conversation and verify ownership
    conversation = await conversation_repository.get_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with id {conversation_id} not found",
        )

    # Check if user owns this conversation
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this conversation",
        )

    # Get character for response scheduling
    result = await db.execute(
        select(Character).where(Character.id == conversation.character_id)
    )
    character = result.scalar_one_or_none()
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    message = await conversation_service.send_message(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=message_data.content,
        character=character,
    )

    return MessageResponse.model_validate(message)


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageListResponse:
    """Get messages for a conversation."""
    # Get conversation and verify ownership
    conversation = await conversation_repository.get_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with id {conversation_id} not found",
        )

    # Check if user owns this conversation
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this conversation",
        )

    messages = await conversation_service.get_messages(db, conversation_id)
    return MessageListResponse(messages=messages)
