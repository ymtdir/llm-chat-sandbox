"""Scheduler jobs for processing AI responses."""

import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import engine
from app.models.message import SenderType
from app.repositories import character_repository
from app.repositories import conversation_repository
from app.repositories import message_repository
from app.repositories import scheduled_response_repository
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def process_pending_responses() -> None:
    """Process pending scheduled responses.

    This job:
    1. Finds all pending responses that are ready to be sent
    2. For each response, generates AI reply using conversation history
    3. Handles batch reading: multiple user messages → single AI response
    4. Saves the AI response as a message
    5. Marks the scheduled response as sent or failed
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get pending responses
            current_time = datetime.now()
            pending_responses = await scheduled_response_repository.get_pending(db, current_time)

            if not pending_responses:
                logger.debug("No pending responses to process")
                return

            logger.info(f"Processing {len(pending_responses)} pending responses")

            # Group responses by conversation to handle batch reading
            conversation_groups: dict[int, list] = {}
            for response in pending_responses:
                conv_id = response.conversation_id
                if conv_id not in conversation_groups:
                    conversation_groups[conv_id] = []
                conversation_groups[conv_id].append(response)

            # Process each conversation group
            for conv_id, responses in conversation_groups.items():
                try:
                    await _process_conversation_responses(db, conv_id, responses)
                except Exception as e:
                    logger.error(f"Error processing conversation {conv_id}: {e}", exc_info=True)
                    # Mark all responses in this group as failed
                    for response in responses:
                        await scheduled_response_repository.mark_as_failed(
                            db, response.id, str(e)
                        )
                    await db.commit()

        except Exception as e:
            logger.error(f"Error in process_pending_responses: {e}", exc_info=True)
            await db.rollback()


async def _process_conversation_responses(
    db: AsyncSession, conversation_id: int, responses: list
) -> None:
    """Process all pending responses for a single conversation.

    Implements batch reading: If there are multiple unanswered user messages,
    respond to all of them in a single AI message.

    Args:
        db: Database session
        conversation_id: ID of the conversation
        responses: List of pending scheduled responses for this conversation
    """
    # Get conversation and character
    conversation = await conversation_repository.get_by_id(db, conversation_id)
    if not conversation:
        raise ValueError(f"Conversation {conversation_id} not found")

    character = await character_repository.get_by_id(db, conversation.character_id)
    if not character:
        raise ValueError(f"Character {conversation.character_id} not found")

    # Get conversation history
    messages = await message_repository.get_recent(db, conversation_id, limit=50)

    # Build conversation history for LLM
    conversation_history = []
    for msg in messages:
        role = "user" if msg.sender_type == SenderType.USER else "assistant"
        conversation_history.append({"role": role, "content": msg.content})

    # Get system prompt from character config
    system_prompt = character.config.get("system_prompt", "You are a helpful assistant.")

    # Generate AI response
    llm_service = LLMService()
    try:
        ai_response = llm_service.generate_response(
            system_prompt=system_prompt,
            conversation_history=conversation_history,
        )
    except Exception as e:
        logger.error(f"LLM generation failed for conversation {conversation_id}: {e}")
        raise

    # Save AI response as a message
    ai_message = await message_repository.create(
        db=db,
        conversation_id=conversation_id,
        content=ai_response,
        sender_type=SenderType.CHARACTER,
        sender_id=character.id,
    )
    await db.flush()

    # Mark all responses in this batch as sent (batch reading)
    for response in responses:
        await scheduled_response_repository.mark_as_sent(db, response.id, ai_message.id)

    await db.commit()
    logger.info(
        f"Processed {len(responses)} responses for conversation {conversation_id}, "
        f"created message {ai_message.id}"
    )


def run_process_pending_responses() -> None:
    """Synchronous wrapper for APScheduler compatibility.

    APScheduler requires a synchronous function, so this wrapper
    runs the async process_pending_responses using asyncio.run().
    """
    asyncio.run(process_pending_responses())
