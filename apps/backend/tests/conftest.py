"""
Pytest configuration and fixtures.
"""
import os

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Set mock environment variables BEFORE any app imports
os.environ["SUPABASE_URL"] = "http://test.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "test_anon_key"
os.environ["SUPABASE_SERVICE_KEY"] = "test_service_key"
os.environ["SPOTIFY_CLIENT_ID"] = "test_spotify_id"
os.environ["SPOTIFY_CLIENT_SECRET"] = "test_spotify_secret"
os.environ["OPENAI_API_KEY"] = "test_openai_key"
os.environ["SPOTIFY_REDIRECT_URI"] = "http://localhost/callback"


@pytest.fixture(autouse=True)
def reset_supabase_singletons():
    """
    Ensure Supabase singletons are reset between tests for proper mocking.
    """
    from app.api.routes import playlists as playlists_routes
    from app.api.routes import workouts as workouts_routes

    playlists_routes._supabase_service_instance = None
    workouts_routes._supabase_service_instance = None
    yield
    playlists_routes._supabase_service_instance = None
    workouts_routes._supabase_service_instance = None


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)
