"""Authentication API endpoints."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.user import User, UserFcmToken
from app.schemas.auth import FcmTokenUpdate, Token, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new user."""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Login user and return JWT token."""
    # Authenticate user
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.put("/fcm-token", status_code=status.HTTP_200_OK)
async def update_fcm_token(
    token_data: FcmTokenUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Register or update FCM token for push notifications."""
    # Check if token already exists
    result = await db.execute(
        select(UserFcmToken).where(UserFcmToken.fcm_token == token_data.fcm_token)
    )
    existing_token = result.scalar_one_or_none()

    if existing_token:
        # Update user_id if token belongs to different user
        if existing_token.user_id != current_user.id:
            existing_token.user_id = current_user.id
            await db.commit()
    else:
        # Create new token entry
        new_token = UserFcmToken(
            user_id=current_user.id,
            fcm_token=token_data.fcm_token,
        )
        db.add(new_token)
        await db.commit()

    return {"message": "FCM token updated successfully"}