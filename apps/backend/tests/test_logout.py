"""
Tests for logout endpoint.
"""
import pytest
from datetime import datetime, timedelta


def test_logout_success(client, test_user):
    """Test successful logout."""
    user_id = test_user["id"]

    # Logout
    response = client.post(f"/auth/logout?user_id={user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user_id"] == user_id
    assert "message" in data


def test_logout_nonexistent_user(client):
    """Test logout with non-existent user."""
    response = client.post("/auth/logout?user_id=nonexistent-user-id")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_logout_clears_tokens(client, test_user, supabase_client):
    """Test that logout clears Spotify tokens."""
    user_id = test_user["id"]

    # Set some tokens first
    expires_at = datetime.now() + timedelta(hours=1)
    supabase_client.table("users").update({
        "spotify_access_token": "test_access_token",
        "spotify_refresh_token": "test_refresh_token",
        "spotify_token_expires_at": expires_at.isoformat(),
    }).eq("id", user_id).execute()

    # Logout
    response = client.post(f"/auth/logout?user_id={user_id}")
    assert response.status_code == 200

    # Verify tokens are cleared
    user = supabase_client.table("users").select("*").eq("id", user_id).execute()
    user_data = user.data[0]

    assert user_data["spotify_access_token"] is None
    assert user_data["spotify_refresh_token"] is None
    assert user_data["spotify_token_expires_at"] is None


def test_logout_missing_user_id(client):
    """Test logout without user_id parameter."""
    response = client.post("/auth/logout")

    assert response.status_code == 422  # Validation error

