"""Scheduled response repository for database operations."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_response import ResponseStatus, ScheduledResponse


async def create(
    db: AsyncSession,
    character_id: int,
    conversation_id: int,
    trigger_message_id: int,
    scheduled_at: datetime,
    response_config: dict,
) -> ScheduledResponse:
    """Create a new scheduled response."""
    scheduled_response = ScheduledResponse(
        character_id=character_id,
        conversation_id=conversation_id,
        trigger_message_id=trigger_message_id,
        scheduled_at=scheduled_at,
        status=ResponseStatus.PENDING,
        response_config=response_config,
    )
    db.add(scheduled_response)
    await db.flush()
    await db.refresh(scheduled_response)
    return scheduled_response


async def get_pending(db: AsyncSession, current_time: datetime | None = None) -> list[ScheduledResponse]:
    """Get pending scheduled responses that are ready to be sent.

    Args:
        db: Database session
        current_time: Current datetime (defaults to now)

    Returns:
        List of pending scheduled responses where scheduled_at <= current_time
    """
    if current_time is None:
        current_time = datetime.now()

    result = await db.execute(
        select(ScheduledResponse)
        .where(
            ScheduledResponse.status == ResponseStatus.PENDING,
            ScheduledResponse.scheduled_at <= current_time,
        )
        .order_by(ScheduledResponse.scheduled_at.asc())
    )
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, scheduled_response_id: int) -> ScheduledResponse | None:
    """Get a scheduled response by ID."""
    result = await db.execute(
        select(ScheduledResponse).where(ScheduledResponse.id == scheduled_response_id)
    )
    return result.scalar_one_or_none()


async def mark_as_sent(
    db: AsyncSession, scheduled_response_id: int, sent_message_id: int
) -> ScheduledResponse | None:
    """Mark a scheduled response as sent.

    Args:
        db: Database session
        scheduled_response_id: ID of the scheduled response
        sent_message_id: ID of the message that was sent

    Returns:
        Updated scheduled response, or None if not found
    """
    scheduled_response = await get_by_id(db, scheduled_response_id)
    if not scheduled_response:
        return None

    scheduled_response.status = ResponseStatus.SENT
    scheduled_response.sent_message_id = sent_message_id
    scheduled_response.sent_at = datetime.now()

    await db.flush()
    await db.refresh(scheduled_response)
    return scheduled_response


async def mark_as_failed(
    db: AsyncSession, scheduled_response_id: int, error_message: str | None = None
) -> ScheduledResponse | None:
    """Mark a scheduled response as failed.

    Args:
        db: Database session
        scheduled_response_id: ID of the scheduled response
        error_message: Optional error message

    Returns:
        Updated scheduled response, or None if not found
    """
    scheduled_response = await get_by_id(db, scheduled_response_id)
    if not scheduled_response:
        return None

    scheduled_response.status = ResponseStatus.FAILED
    if error_message:
        # Store error message in response_config for debugging
        # Create new dict to ensure SQLAlchemy detects the change
        config = dict(scheduled_response.response_config) if scheduled_response.response_config else {}
        config["error"] = error_message
        scheduled_response.response_config = config

    await db.flush()
    await db.refresh(scheduled_response)
    return scheduled_response
