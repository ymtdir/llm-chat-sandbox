"""Authentication related schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload."""

    user_id: int | None = None


class FcmTokenUpdate(BaseModel):
    """Schema for FCM token update."""

    fcm_token: str = Field(
        ...,
        min_length=100,
        max_length=255,
        description="Firebase Cloud Messaging registration token",
    )

    @field_validator("fcm_token")
    @classmethod
    def validate_fcm_token(cls, v: str) -> str:
        """Validate FCM token format."""
        # FCM tokens typically contain alphanumeric, colons, underscores, and hyphens
        import re

        if not re.match(r"^[a-zA-Z0-9:_-]+$", v):
            raise ValueError(
                "Invalid FCM token format. Token should only contain "
                "alphanumeric characters, colons, underscores, and hyphens."
            )
        return v
