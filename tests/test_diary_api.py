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
