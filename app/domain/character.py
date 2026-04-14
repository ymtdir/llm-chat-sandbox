"""Character domain models."""

from typing import Literal

from pydantic import BaseModel, Field


class ResponsePattern(BaseModel):
    """Response timing pattern configuration."""

    base_delay_minutes: dict[str, int] = Field(
        ...,
        description="Base delay range in minutes",
        examples=[{"min": 5, "max": 30}],
    )
    time_of_day_modifiers: list[dict[str, float | list[int]]] = Field(
        default_factory=list,
        description="Time-based delay modifiers",
        examples=[[{"hours": [12, 13], "multiplier": 0.5}]],
    )
    randomness_factor: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Randomness factor for natural variation (0-1)",
    )
    reply_probability: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Probability of replying (0-1)",
    )


class CharacterConfig(BaseModel):
    """Character configuration for AI personality and behavior."""

    personality: Literal["diligent", "normal", "busy"] = Field(
        ...,
        description="Character personality type",
    )
    occupation: Literal["office_worker", "student", "freelancer", "homemaker"] = Field(
        ...,
        description="Character occupation",
    )
    working_hours: dict[str, int] | None = Field(
        default=None,
        description="Working hours (start and end)",
        examples=[{"start": 9, "end": 18}],
    )
    response_patterns: ResponsePattern = Field(
        ...,
        description="Response timing patterns",
    )
    system_prompt: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="System prompt for LLM",
    )