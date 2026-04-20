"""Tests for authentication endpoints."""

from app.core.security import hash_password, verify_password


def test_password_hashing(client):
    """Test password hashing and verification."""
    password = "test_password123"
    hashed = hash_password(password)

    # Check that hash is different from plain password
    assert hashed != password

    # Check that verification works
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_register_user(client):
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
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_user(client):
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


def test_register_invalid_email(client):
    """Test registration with invalid email."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "not_an_email",
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_register_short_password(client):
    """Test registration with password too short."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test2@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_login_success(client):
    """Test successful login with JSON format."""
    # First register a user
    client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )

    # Then login using /token endpoint (accepts JSON)
    response = client.post(
        "/api/auth/token",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    """Test login with wrong password."""
    # First register a user
    client.post(
        "/api/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "correct_password",
        },
    )

    # Try to login with wrong password using /token endpoint
    response = client.post(
        "/api/auth/token",
        json={
            "email": "wrongpass@example.com",
            "password": "wrong_password",
        },
    )

    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    response = client.post(
        "/api/auth/token",
        json={
            "email": "nonexistent@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 401


def test_fcm_token_update_unauthorized(client):
    """Test FCM token update without authentication."""
    response = client.put(
        "/api/auth/fcm-token",
        json={
            "fcm_token": "a" * 150,
        },
    )

    assert response.status_code == 401


def test_fcm_token_update_authorized(client):
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
        "/api/auth/token",
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
            "fcm_token": "a" * 150,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert "success" in response.json()["message"].lower()


def test_get_current_user_info(client):
    """Test /me endpoint to get current user information."""
    # Register user
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "me@example.com",
            "password": "password123",
        },
    )
    token = register_response.json()["access_token"]

    # Get current user info
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_get_current_user_unauthorized(client):
    """Test /me endpoint without authentication."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
