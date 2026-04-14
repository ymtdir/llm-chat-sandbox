"""Tests for character endpoints."""


def create_test_character_data(name: str = "Test Character") -> dict:
    """Create valid character data for testing."""
    return {
        "name": name,
        "config": {
            "personality": "diligent",
            "occupation": "office_worker",
            "working_hours": {"start": 9, "end": 18},
            "response_patterns": {
                "base_delay_minutes": {"min": 3, "max": 10},
                "time_of_day_modifiers": [
                    {"hours": [12, 13], "multiplier": 0.5},
                ],
                "randomness_factor": 0.2,
                "reply_probability": 0.95,
            },
            "system_prompt": "You are a helpful assistant.",
        },
    }


def get_auth_token(client) -> str:
    """Register a user and return auth token."""
    client.post(
        "/api/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "password123",
        },
    )

    return response.json()["access_token"]


def test_list_characters_empty(client):
    """Test listing characters when none exist."""
    response = client.get("/api/characters")

    assert response.status_code == 200
    data = response.json()
    assert "characters" in data
    assert data["characters"] == []


def test_list_characters_with_data(client):
    """Test listing characters when some exist."""
    # Create characters
    token = get_auth_token(client)
    client.post(
        "/api/characters",
        json=create_test_character_data("Character 1"),
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/api/characters",
        json=create_test_character_data("Character 2"),
        headers={"Authorization": f"Bearer {token}"},
    )

    # List characters
    response = client.get("/api/characters")

    assert response.status_code == 200
    data = response.json()
    assert "characters" in data
    assert len(data["characters"]) == 2
    assert data["characters"][0]["name"] == "Character 1"
    assert data["characters"][1]["name"] == "Character 2"

    # Verify schema
    for character in data["characters"]:
        assert "id" in character
        assert "name" in character
        assert "config" in character
        assert "created_at" in character


def test_get_character_success(client):
    """Test getting a specific character."""
    # Create a character
    token = get_auth_token(client)
    create_response = client.post(
        "/api/characters",
        json=create_test_character_data("Test Character"),
        headers={"Authorization": f"Bearer {token}"},
    )
    character_id = create_response.json()["id"]

    # Get the character
    response = client.get(f"/api/characters/{character_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == character_id
    assert data["name"] == "Test Character"
    assert data["config"]["personality"] == "diligent"
    assert data["config"]["occupation"] == "office_worker"
    assert "created_at" in data


def test_get_character_not_found(client):
    """Test getting a non-existent character."""
    response = client.get("/api/characters/999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_character_success(client):
    """Test creating a character with valid data."""
    token = get_auth_token(client)
    character_data = create_test_character_data("New Character")

    response = client.post(
        "/api/characters",
        json=character_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == "New Character"
    assert data["config"]["personality"] == "diligent"
    assert data["config"]["occupation"] == "office_worker"
    assert data["config"]["working_hours"]["start"] == 9
    assert data["config"]["working_hours"]["end"] == 18
    assert data["config"]["response_patterns"]["randomness_factor"] == 0.2
    assert data["config"]["response_patterns"]["reply_probability"] == 0.95
    assert data["config"]["system_prompt"] == "You are a helpful assistant."
    assert "created_at" in data


def test_create_character_unauthorized(client):
    """Test creating a character without authentication."""
    character_data = create_test_character_data()

    response = client.post("/api/characters", json=character_data)

    assert response.status_code == 401


def test_create_character_invalid_personality(client):
    """Test creating a character with invalid personality."""
    token = get_auth_token(client)
    character_data = create_test_character_data()
    character_data["config"]["personality"] = "invalid_personality"

    response = client.post(
        "/api/characters",
        json=character_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_create_character_invalid_occupation(client):
    """Test creating a character with invalid occupation."""
    token = get_auth_token(client)
    character_data = create_test_character_data()
    character_data["config"]["occupation"] = "invalid_occupation"

    response = client.post(
        "/api/characters",
        json=character_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_create_character_missing_required_fields(client):
    """Test creating a character with missing required fields."""
    token = get_auth_token(client)

    # Missing system_prompt
    character_data = create_test_character_data()
    del character_data["config"]["system_prompt"]

    response = client.post(
        "/api/characters",
        json=character_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_create_character_invalid_reply_probability(client):
    """Test creating a character with invalid reply_probability."""
    token = get_auth_token(client)
    character_data = create_test_character_data()
    character_data["config"]["response_patterns"]["reply_probability"] = 1.5  # > 1.0

    response = client.post(
        "/api/characters",
        json=character_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_create_character_empty_name(client):
    """Test creating a character with empty name."""
    token = get_auth_token(client)
    character_data = create_test_character_data("")

    response = client.post(
        "/api/characters",
        json=character_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
