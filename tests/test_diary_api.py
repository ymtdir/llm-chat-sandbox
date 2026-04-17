"""Tests for diary viewing endpoints."""

from datetime import date, timedelta


def get_auth_token_and_user(client) -> tuple[str, dict]:
    """Register a user and return auth token and user data."""
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "password123",
        },
    )
    user_data = register_response.json()

    login_response = client.post(
        "/api/auth/token",
        json={
            "email": "testuser@example.com",
            "password": "password123",
        },
    )
    token = login_response.json()["access_token"]

    return token, user_data


def test_list_diaries_empty(client):
    """Test listing diaries when user has no diaries."""
    token, _ = get_auth_token_and_user(client)

    response = client.get(
        "/api/diaries",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "diaries" in data
    assert len(data["diaries"]) == 0


def test_list_diaries_with_limit(client):
    """Test listing diaries with limit parameter."""
    token, _ = get_auth_token_and_user(client)

    response = client.get(
        "/api/diaries?limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "diaries" in data


def test_list_diaries_with_invalid_limit(client):
    """Test listing diaries with invalid limit parameter."""
    token, _ = get_auth_token_and_user(client)

    # Test limit = 0 (below minimum)
    response = client.get(
        "/api/diaries?limit=0",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422  # Validation error


def test_list_diaries_unauthorized(client):
    """Test listing diaries without authentication."""
    response = client.get("/api/diaries")

    assert response.status_code == 401


def test_list_diaries_user_isolation(client):
    """Test that users can only see their own diaries."""
    # Create first user
    token1, _ = get_auth_token_and_user(client)

    # Create second user
    client.post(
        "/api/auth/register",
        json={
            "email": "testuser2@example.com",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/api/auth/token",
        json={
            "email": "testuser2@example.com",
            "password": "password123",
        },
    )
    token2 = login_response.json()["access_token"]

    # Both users should see empty lists (no diaries created)
    response1 = client.get(
        "/api/diaries",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert response1.status_code == 200
    diaries1 = response1.json()["diaries"]
    assert len(diaries1) == 0

    response2 = client.get(
        "/api/diaries",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response2.status_code == 200
    diaries2 = response2.json()["diaries"]
    assert len(diaries2) == 0


def test_get_diary_by_date_not_found(client):
    """Test getting a diary for a date that doesn't exist."""
    token, _ = get_auth_token_and_user(client)

    future_date = date.today() + timedelta(days=100)
    response = client.get(
        f"/api/diaries/{future_date}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_diary_by_date_unauthorized(client):
    """Test getting a diary without authentication."""
    today = date.today()
    response = client.get(f"/api/diaries/{today}")

    assert response.status_code == 401


def test_get_diary_by_date_invalid_format(client):
    """Test getting a diary with invalid date format."""
    token, _ = get_auth_token_and_user(client)

    response = client.get(
        "/api/diaries/invalid-date",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422  # Validation error


def test_diary_response_schema_structure(client):
    """Test that diary list response has correct structure."""
    token, _ = get_auth_token_and_user(client)

    response = client.get(
        "/api/diaries",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "diaries" in data
    assert isinstance(data["diaries"], list)


async def test_list_diaries_with_actual_data(client, db, sample_user):
    """Test listing diaries with actual diary data."""
    from app.repositories import diary_repository

    # Create multiple diaries for the sample user (for user isolation test)
    today = date.today()
    user_id = sample_user.id

    await diary_repository.create(
        db=db,
        user_id=user_id,
        diary_date=today,
        content="Today's diary entry",
        metadata={"message_count": 10, "conversation_count": 2},
    )
    await diary_repository.create(
        db=db,
        user_id=user_id,
        diary_date=today - timedelta(days=1),
        content="Yesterday's diary entry",
        metadata={"message_count": 5, "conversation_count": 1},
    )
    await diary_repository.create(
        db=db,
        user_id=user_id,
        diary_date=today - timedelta(days=2),
        content="Two days ago diary entry",
        metadata={"message_count": 8, "conversation_count": 3},
    )
    await db.commit()

    # Get auth token (need to create user via API since sample_user is DB fixture)
    # Use a different email to avoid conflicts
    token, _ = get_auth_token_and_user(client)

    # Since we can't easily authenticate as sample_user, create a new user
    # and create diaries for them instead
    from jose import jwt

    from app.core.database import get_db
    from app.core.security import ALGORITHM, SECRET_KEY
    from app.main import app

    # Decode token to get the actual authenticated user ID
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    auth_user_id = int(payload["sub"])

    # Create diaries for the authenticated user
    async for session in app.dependency_overrides[get_db]():
        await diary_repository.create(
            db=session,
            user_id=auth_user_id,
            diary_date=today,
            content="Today's diary",
            metadata={"message_count": 15},
        )
        await diary_repository.create(
            db=session,
            user_id=auth_user_id,
            diary_date=today - timedelta(days=1),
            content="Yesterday's diary",
            metadata={"message_count": 12},
        )
        await session.commit()
        break

    # Now test the API
    response = client.get(
        "/api/diaries",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["diaries"]) == 2

    # Check that diaries are sorted by date descending
    diaries = data["diaries"]
    assert diaries[0]["diary_date"] == str(today)
    assert diaries[0]["content"] == "Today's diary"
    assert diaries[0]["metadata"]["message_count"] == 15
    assert diaries[1]["diary_date"] == str(today - timedelta(days=1))
    assert diaries[1]["content"] == "Yesterday's diary"


async def test_get_diary_by_date_with_actual_data(client, db):
    """Test getting a specific diary by date with actual data."""
    from app.repositories import diary_repository

    # Create user and get token
    token, _ = get_auth_token_and_user(client)

    from jose import jwt

    from app.core.database import get_db
    from app.core.security import ALGORITHM, SECRET_KEY
    from app.main import app

    # Decode token to get user ID
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    auth_user_id = int(payload["sub"])

    # Create a diary for the authenticated user
    today = date.today()
    async for session in app.dependency_overrides[get_db]():
        await diary_repository.create(
            db=session,
            user_id=auth_user_id,
            diary_date=today,
            content="Test diary content for today",
            metadata={"message_count": 20, "conversation_count": 3},
        )
        await session.commit()
        break

    # Get the diary via API
    response = client.get(
        f"/api/diaries/{today}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["diary_date"] == str(today)
    assert data["content"] == "Test diary content for today"
    assert data["metadata"]["message_count"] == 20
    assert data["metadata"]["conversation_count"] == 3
    assert "id" in data
    assert "created_at" in data


async def test_list_diaries_with_limit_actual_data(client):
    """Test that limit parameter correctly restricts results."""
    from app.repositories import diary_repository

    token, _ = get_auth_token_and_user(client)

    from jose import jwt

    from app.core.database import get_db
    from app.core.security import ALGORITHM, SECRET_KEY
    from app.main import app

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    auth_user_id = int(payload["sub"])

    # Create 5 diaries
    today = date.today()
    async for session in app.dependency_overrides[get_db]():
        for i in range(5):
            await diary_repository.create(
                db=session,
                user_id=auth_user_id,
                diary_date=today - timedelta(days=i),
                content=f"Diary {i}",
                metadata={"day": i},
            )
        await session.commit()
        break

    # Test with limit=2
    response = client.get(
        "/api/diaries?limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["diaries"]) == 2
    # Should get the 2 most recent ones
    assert data["diaries"][0]["content"] == "Diary 0"
    assert data["diaries"][1]["content"] == "Diary 1"
