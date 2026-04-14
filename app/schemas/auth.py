"""Authentication related schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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

    fcm_token: str = Field(..., min_length=1, max_length=255)
