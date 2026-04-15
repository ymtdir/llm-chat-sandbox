"""pytest設定とフィクスチャー"""

import asyncio
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_test,
    class_=AsyncSession,
)


async def override_get_db():
    """Override database dependency for testing."""
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


async def _create_tables():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def setup_database():
    """Create and drop tables for each test (sync wrapper)."""
    asyncio.run(_create_tables())
    yield
    asyncio.run(_drop_tables())


@pytest.fixture
def client() -> TestClient:
    """FastAPIテストクライアントのフィクスチャー"""
    return TestClient(app)


@pytest.fixture
async def db() -> AsyncSession:
    """Async database session fixture for direct repository tests."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def sample_user(db: AsyncSession):
    """Create a sample user for testing."""
    from app.repositories import user_repository

    user = await user_repository.create(
        db=db,
        email="test@example.com",
        password_hash="hashed_password",
    )
    await db.flush()
    return user


@pytest.fixture
async def sample_character(db: AsyncSession):
    """Create a sample character for testing."""
    from app.repositories import character_repository

    character = await character_repository.create(
        db=db,
        name="Test Character",
        config={
            "system_prompt": "You are a test character.",
            "response_patterns": {
                "base_delay_minutes": {"min": 5, "max": 15},
                "randomness_factor": 0.2,
                "reply_probability": 0.95,
            },
        },
    )
    await db.flush()
    return character


@pytest.fixture
async def sample_conversation(db: AsyncSession, sample_user, sample_character):
    """Create a sample conversation for testing."""
    from app.repositories import conversation_repository

    conversation = await conversation_repository.create(
        db=db,
        user_id=sample_user.id,
        character_id=sample_character.id,
    )
    await db.flush()
    return conversation
