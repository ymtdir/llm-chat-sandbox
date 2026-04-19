"""Tests for conversation endpoints."""


def create_conversation_data(character_id: int = 1) -> dict:
    """Create valid conversation data for testing."""
    return {"character_id": character_id}


def create_message_data(content: str = "Hello!") -> dict:
    """Create valid message data for testing."""
    return {"content": content}


def get_auth_token_and_user(client) -> tuple[str, dict]:
    """Register a user and return auth token and user data."""
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "password123",
        },
    )
    token = register_response.json()["access_token"]

    # Get user data from /me endpoint
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    user_data = me_response.json()

    return token, user_data


def create_test_character(client, token: str) -> dict:
    """Create a test character and return its data."""
    character_response = client.post(
        "/api/characters",
        json={
            "name": "Test Character",
            "config": {
                "personality": "diligent",
                "occupation": "office_worker",
                "working_hours": {"start": 9, "end": 18},
                "response_patterns": {
                    "base_delay_minutes": {"min": 5, "max": 15},
                    "randomness_factor": 0.2,
                    "reply_probability": 0.95,
                },
                "system_prompt": "Test prompt",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return character_response.json()


def test_create_conversation_success(client):
    """Test creating a conversation."""
    token, _ = get_auth_token_and_user(client)
    character = create_test_character(client, token)

    response = client.post(
        "/api/conversations",
        json=create_conversation_data(character["id"]),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["character_id"] == character["id"]
    assert "user_id" in data
    assert "created_at" in data


def test_create_conversation_unauthorized(client):
    """Test creating a conversation without authentication."""
    response = client.post(
        "/api/conversations",
        json=create_conversation_data(),
    )

    assert response.status_code == 401


def test_create_conversation_character_not_found(client):
    """Test creating a conversation with non-existent character."""
    token, _ = get_auth_token_and_user(client)

    response = client.post(
        "/api/conversations",
        json=create_conversation_data(999),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_conversations_empty(client):
    """Test listing conversations when none exist."""
    token, _ = get_auth_token_and_user(client)

    response = client.get(
        "/api/conversations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "conversations" in data
    assert data["conversations"] == []


def test_list_conversations_with_data(client):
    """Test listing conversations when some exist."""
    token, _ = get_auth_token_and_user(client)
    character = create_test_character(client, token)

    # Create conversations
    client.post(
        "/api/conversations",
        json=create_conversation_data(character["id"]),
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/api/conversations",
        json=create_conversation_data(character["id"]),
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/api/conversations",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "conversations" in data
    assert len(data["conversations"]) == 2


def test_send_message_success(client):
    """Test sending a message in a conversation."""
    token, user = get_auth_token_and_user(client)
    character = create_test_character(client, token)

    # Create conversation
    conv_response = client.post(
        "/api/conversations",
        json=create_conversation_data(character["id"]),
        headers={"Authorization": f"Bearer {token}"},
    )
    conversation_id = conv_response.json()["id"]

    # Send message
    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json=create_message_data("Hello!"),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["conversation_id"] == conversation_id
    assert data["content"] == "Hello!"
    assert data["sender_type"] == "user"
    assert "sender_id" in data  # Just check field exists, not specific value
    assert "sent_at" in data


def test_send_message_xss_protection(client):
    """Test that HTML is escaped for XSS protection."""
    token, _ = get_auth_token_and_user(client)
    character = create_test_character(client, token)

    # Create conversation
    conv_response = client.post(
        "/api/conversations",
        json=create_conversation_data(character["id"]),
        headers={"Authorization": f"Bearer {token}"},
    )
    conversation_id = conv_response.json()["id"]

    # Send message with HTML
    malicious_content = "<script>alert('xss')</script>"
    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json=create_message_data(malicious_content),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    # HTML should be escaped
    assert data["content"] == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"


def test_send_message_unauthorized(client):
    """Test sending a message without authentication."""
    response = client.post(
        "/api/conversations/1/messages",
        json=create_message_data(),
    )

    assert response.status_code == 401


def test_send_message_conversation_not_found(client):
    """Test sending a message to non-existent conversation."""
    token, _ = get_auth_token_and_user(client)

    response = client.post(
        "/api/conversations/999/messages",
        json=create_message_data(),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_send_message_forbidden(client):
    """Test sending a message to another user's conversation."""
    # User 1 creates conversation
    token1, _ = get_auth_token_and_user(client)
    character = create_test_character(client, token1)
    conv_response = client.post(
        "/api/conversations",
        json=create_conversation_data(character["id"]),
        headers={"Authorization": f"Bearer {token1}"},
    )
    conversation_id = conv_response.json()["id"]

    # User 2 tries to send message
    client.post(
        "/api/auth/register",
        json={
            "email": "user2@example.com",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/api/auth/token",
        json={
            "email": "user2@example.com",
            "password": "password123",
        },
    )
    token2 = login_response.json()["access_token"]

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json=create_message_data(),
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


def test_send_message_content_validation(client):
    """Test message content validation."""
    token, _ = get_auth_token_and_user(client)
    character = create_test_character(client, token)
    conv_response = client.post(
        "/api/conversations",
        json=create_conversation_data(character["id"]),
        headers={"Authorization": f"Bearer {token}"},
    )
    conversation_id = conv_response.json()["id"]

    # Empty message
    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json=create_message_data(""),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422

    # Message too long (> 1000 characters)
    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json=create_message_data("x" * 1001),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_get_messages_success(client):
    """Test getting messages for a conversation."""
    token, _ = get_auth_token_and_user(client)
    character = create_test_character(client, token)

    # Create conversation
    conv_response = client.post(
        "/api/conversations",
        json=create_conversation_data(character["id"]),
        headers={"Authorization": f"Bearer {token}"},
    )
    conversation_id = conv_response.json()["id"]

    # Send messages
    client.post(
        f"/api/conversations/{conversation_id}/messages",
        json=create_message_data("First message"),
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        f"/api/conversations/{conversation_id}/messages",
        json=create_message_data("Second message"),
        headers={"Authorization": f"Bearer {token}"},
    )

    # Get messages
    response = client.get(
        f"/api/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 2
    # Messages should be in chronological order
    assert data["messages"][0]["content"] == "First message"
    assert data["messages"][1]["content"] == "Second message"


def test_get_messages_unauthorized(client):
    """Test getting messages without authentication."""
    response = client.get("/api/conversations/1/messages")

    assert response.status_code == 401


def test_get_messages_conversation_not_found(client):
    """Test getting messages for non-existent conversation."""
    token, _ = get_auth_token_and_user(client)

    response = client.get(
        "/api/conversations/999/messages",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_get_messages_forbidden(client):
    """Test getting messages for another user's conversation."""
    # User 1 creates conversation
    token1, _ = get_auth_token_and_user(client)
    character = create_test_character(client, token1)
    conv_response = client.post(
        "/api/conversations",
        json=create_conversation_data(character["id"]),
        headers={"Authorization": f"Bearer {token1}"},
    )
    conversation_id = conv_response.json()["id"]

    # User 2 tries to get messages
    client.post(
        "/api/auth/register",
        json={
            "email": "user2@example.com",
            "password": "password123",
        },
    )
    login_response = client.post(
        "/api/auth/token",
        json={
            "email": "user2@example.com",
            "password": "password123",
        },
    )
    token2 = login_response.json()["access_token"]

    response = client.get(
        f"/api/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()
