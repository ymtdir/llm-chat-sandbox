"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password, verify_password
from app.main import app
from app.models.user import User

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


@pytest.fixture
async def async_client():
    """Create test client with test database."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield TestClient(app)

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


client = TestClient(app)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password123"
    hashed = hash_password(password)

    # Check that hash is different from plain password
    assert hashed != password

    # Check that verification works
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_register_user():
    """Test user registration endpoint."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_user():
    """Test duplicate user registration."""
    # Register first user
    client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )

    # Try to register same email
    response = client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "different_password",
        },
    )

    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


def test_register_invalid_email():
    """Test registration with invalid email."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "not_an_email",
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_register_short_password():
    """Test registration with password too short."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test2@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_login_success():
    """Test successful login."""
    # First register a user
    client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )

    # Then login
    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    """Test login with wrong password."""
    # First register a user
    client.post(
        "/api/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "correct_password",
        },
    )

    # Try to login with wrong password
    response = client.post(
        "/api/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "wrong_password",
        },
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_user():
    """Test login with non-existent user."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401


def test_fcm_token_update_unauthorized():
    """Test FCM token update without authentication."""
    response = client.put(
        "/api/auth/fcm-token",
        json={
            "fcm_token": "test_fcm_token_123",
        },
    )

    assert response.status_code == 401


def test_fcm_token_update_authorized():
    """Test FCM token update with authentication."""
    # Register and login first
    client.post(
        "/api/auth/register",
        json={
            "email": "fcm@example.com",
            "password": "password123",
        },
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "fcm@example.com",
            "password": "password123",
        },
    )

    token = login_response.json()["access_token"]

    # Update FCM token
    response = client.put(
        "/api/auth/fcm-token",
        json={
            "fcm_token": "test_fcm_token_123",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert "success" in response.json()["message"].lower()