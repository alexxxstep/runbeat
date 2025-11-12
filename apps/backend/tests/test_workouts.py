"""
Tests for workout CRUD endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime

client = TestClient(app)


@pytest.fixture
def mock_workout_data():
    """Mock workout data."""
    return {
        "id": "workout_uuid",
        "user_id": "user_uuid",
        "type": "steady",
        "duration_minutes": 30,
        "intensity": "low",
        "hr_zones": [110, 130],
        "completed_at": None,
        "created_at": "2025-11-12T10:00:00Z",
    }


@patch("app.api.routes.workouts.SupabaseService")
def test_create_workout(mock_supabase_service, mock_workout_data):
    """Test creating a workout."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.insert.return_value.execute.return_value.data = [
        mock_workout_data
    ]
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.post(
        "/workouts",
        json={
            "workout": {
                "type": "steady",
                "duration_minutes": 30,
                "intensity": "low",
                "hr_zones": [110, 130],
                "confidence": 0.95,
                "needs_clarification": False,
            },
            "user_id": "user_uuid",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "workout_uuid"
    assert data["type"] == "steady"
    assert data["duration_minutes"] == 30


@patch("app.api.routes.workouts.SupabaseService")
def test_get_workouts(mock_supabase_service, mock_workout_data):
    """Test getting list of workouts."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_result = MagicMock()
    mock_result.data = [mock_workout_data]
    mock_result.count = 1
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value.execute.return_value = (
        mock_result
    )
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.get("/workouts?user_id=user_uuid&limit=10&offset=0")

    assert response.status_code == 200
    data = response.json()
    assert "workouts" in data
    assert "total" in data
    assert len(data["workouts"]) == 1
    assert data["workouts"][0]["id"] == "workout_uuid"


@patch("app.api.routes.workouts.SupabaseService")
def test_get_workout_by_id(mock_supabase_service, mock_workout_data):
    """Test getting a specific workout."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        mock_workout_data
    ]
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.get(
        "/workouts/workout_uuid?user_id=user_uuid"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "workout_uuid"
    assert data["type"] == "steady"


@patch("app.api.routes.workouts.SupabaseService")
def test_get_workout_not_found(mock_supabase_service):
    """Test getting a non-existent workout."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        []
    )
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.get(
        "/workouts/nonexistent?user_id=user_uuid"
    )

    assert response.status_code == 404


@patch("app.api.routes.workouts.SupabaseService")
def test_delete_workout(mock_supabase_service, mock_workout_data):
    """Test deleting a workout."""
    # Mock Supabase
    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = [
        mock_workout_data
    ]
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.delete(
        "/workouts/workout_uuid?user_id=user_uuid"
    )

    assert response.status_code == 204


@patch("app.api.routes.workouts.SupabaseService")
def test_complete_workout(mock_supabase_service, mock_workout_data):
    """Test marking a workout as completed."""
    # Mock Supabase
    completed_workout = mock_workout_data.copy()
    completed_workout["completed_at"] = "2025-11-12T11:00:00Z"

    mock_supabase = MagicMock()
    mock_supabase.get_client.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [
        completed_workout
    ]
    mock_supabase_service.return_value = mock_supabase

    # Make request
    response = client.patch(
        "/workouts/workout_uuid/complete?user_id=user_uuid"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "workout_uuid"
    assert data["completed_at"] is not None

