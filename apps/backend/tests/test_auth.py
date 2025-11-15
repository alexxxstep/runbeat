"""
Tests for authentication endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.api.routes.auth.get_spotify_oauth")
def test_spotify_auth_initiate(mock_oauth):
    """Test Spotify OAuth initiation."""
    # Mock OAuth
    mock_oauth_instance = MagicMock()
    mock_oauth_instance.get_authorize_url.return_value = (
        "https://accounts.spotify.com/authorize?client_id=test&response_type=code"
    )
    mock_oauth.return_value = mock_oauth_instance

    # Make request
    response = client.get("/auth/spotify")

    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert "state" in data
    assert "https://accounts.spotify.com/authorize" in data["auth_url"]
    assert len(data["state"]) > 0


def test_spotify_callback_missing_code():
    """Test Spotify callback without code."""
    response = client.get("/auth/spotify/callback")

    # FastAPI returns 422 because required query params are missing
    assert response.status_code == 422


def test_spotify_callback_invalid_state():
    """Test Spotify callback with invalid state."""
    response = client.get(
        "/auth/spotify/callback?code=test_code&state=invalid_state",
        follow_redirects=False,
    )

    # Should redirect to error page
    assert response.status_code in [302, 307]  # Redirect


@patch("app.api.routes.auth.get_spotify_oauth")
@patch("app.api.routes.auth.spotipy.Spotify")
@patch("app.api.routes.auth.SupabaseService")
def test_spotify_callback_success(
    mock_supabase_service, mock_spotify, mock_oauth
):
    """Test successful Spotify callback."""
    # Mock OAuth
    mock_oauth_instance = MagicMock()
    mock_oauth_instance.get_access_token.return_value = {
        "access_token": "test_token",
        "refresh_token": "test_refresh",
        "expires_in": 3600,
    }
    mock_oauth.return_value = mock_oauth_instance

    # Mock Spotify user info
    mock_spotify_instance = MagicMock()
    mock_spotify_instance.current_user.return_value = {
        "id": "spotify_user_123",
        "email": "test@example.com",
    }
    mock_spotify.return_value = mock_spotify_instance

    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )  # No existing user
    mock_supabase.get_client.return_value.table.return_value.insert.return_value.execute.return_value.data = [
        {
            "id": "user_uuid",
            "email": "test@example.com",
            "spotify_user_id": "spotify_user_123",
        }
    ]
    mock_supabase_service.return_value = mock_supabase

    # Create a valid state first
    from app.api.routes.auth import oauth_states
    import secrets
    from datetime import datetime

    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "created_at": datetime.now(),
        "used": False,
    }

    # Make request
    response = client.get(
        f"/auth/spotify/callback?code=test_code&state={state}",
        follow_redirects=False,
    )

    # Should redirect to success page
    assert response.status_code in [302, 307]  # Redirect


@patch("app.api.routes.auth.SupabaseService")
def test_spotify_auth_status_authenticated(mock_supabase_service):
    """Test checking Spotify auth status when authenticated."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {
            "id": "user_uuid",
            "spotify_user_id": "spotify_user_123",
            "spotify_token_expires_at": "2025-12-12T10:00:00Z",
        }
    ]
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.get("/auth/spotify/status?user_id=user_uuid")

    assert response.status_code == 200
    data = response.json()
    assert "authenticated" in data
    assert "spotify_user_id" in data


@patch("app.api.routes.auth.SupabaseService")
def test_spotify_auth_status_user_not_found(mock_supabase_service):
    """Test checking Spotify auth status when user not found."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.get("/auth/spotify/status?user_id=nonexistent")

    assert response.status_code == 404

