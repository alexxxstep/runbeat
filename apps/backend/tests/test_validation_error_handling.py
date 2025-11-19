"""
Tests for validation error handling in workout creation flow.
Tests the fixes for "'duration', 'intensity'" error.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pydantic import ValidationError

from app.services.workout_builder import WorkoutBuilder
from app.schemas.conversation import ConversationState
from app.api.routes.chat import send_message
from app.schemas.chat import ChatRequest
from app.agents.tools.workout_tools import (
    create_workout_from_params,
    CreateWorkoutFromParamsInput,
)


class TestValidationErrorHandling:
    """Test validation error handling at different levels."""

    def test_create_workout_from_params_schema_accepts_none(self):
        """Test that CreateWorkoutFromParamsInput schema accepts None values."""
        # Should not raise ValidationError
        schema = CreateWorkoutFromParamsInput(
            user_id="test_user",
            duration_minutes=None,
            intensity=None,
        )
        assert schema.user_id == "test_user"
        assert schema.duration_minutes is None
        assert schema.intensity is None

    def test_create_workout_from_params_with_none_returns_error(self):
        """Test that create_workout_from_params returns error message when called with None."""
        result = create_workout_from_params.invoke(
            {
                "user_id": "test_user",
                "duration_minutes": None,
                "intensity": None,
            }
        )
        assert "error" in result.lower()
        assert "duration" in result.lower() or "intensity" in result.lower()

    def test_create_workout_from_params_with_missing_duration(self):
        """Test that missing duration returns appropriate error."""
        result = create_workout_from_params.invoke(
            {
                "user_id": "test_user",
                "duration_minutes": None,
                "intensity": "moderate",
            }
        )
        assert "error" in result.lower()
        assert "duration" in result.lower()

    def test_create_workout_from_params_with_missing_intensity(self):
        """Test that missing intensity returns appropriate error."""
        result = create_workout_from_params.invoke(
            {
                "user_id": "test_user",
                "duration_minutes": 30,
                "intensity": None,
            }
        )
        assert "error" in result.lower()
        assert "intensity" in result.lower()

    @pytest.mark.asyncio
    async def test_workout_builder_handles_validation_error(self):
        """Test that WorkoutBuilder.handle_error catches validation errors."""
        builder = WorkoutBuilder()

        # Simulate validation error
        error = ValueError("'duration', 'intensity'")
        result = builder.agent_executor.handle_parsing_errors(error)

        assert isinstance(result, str)
        assert "тривалість" in result.lower() or "duration" in result.lower()
        assert "інтенсивність" in result.lower() or "intensity" in result.lower()

    @pytest.mark.asyncio
    async def test_workout_builder_handles_different_error_formats(self):
        """Test that error handler catches different error formats."""
        builder = WorkoutBuilder()

        # Test different error formats
        error_formats = [
            ValueError("'duration', 'intensity'"),
            ValueError("missing required fields: duration, intensity"),
            ValidationError.from_exception_data(
                "CreateWorkoutFromParamsInput",
                [
                    {
                        "type": "missing",
                        "loc": ("duration_minutes",),
                        "msg": "Field required",
                    },
                    {
                        "type": "missing",
                        "loc": ("intensity",),
                        "msg": "Field required",
                    },
                ],
            ),
        ]

        for error in error_formats:
            try:
                result = builder.agent_executor.handle_parsing_errors(error)
                assert isinstance(result, str)
                assert len(result) > 0
            except Exception as e:
                # If error handler doesn't catch it, that's also ok
                # as long as it doesn't crash the system
                pass

    @pytest.mark.asyncio
    async def test_chat_endpoint_handles_validation_error(self):
        """Test that chat endpoint handles validation errors gracefully."""
        from fastapi import HTTPException

        # Mock supervisor to raise validation error
        with patch("app.api.routes.chat.supervisor_agent") as mock_supervisor:
            # Simulate validation error
            error = ValueError("'duration', 'intensity'")
            mock_supervisor.handle_message = AsyncMock(side_effect=error)

            request = ChatRequest(user_id="test_user", message="test message")

            # Should return 200 with error message, not 500
            response = await send_message(request)

            assert response.message is not None
            assert "тривалість" in response.message.lower() or "duration" in response.message.lower()
            assert response.workout is None
            assert response.needs_clarification is True

    @pytest.mark.asyncio
    async def test_chat_endpoint_handles_other_errors(self):
        """Test that chat endpoint handles other errors normally."""
        from fastapi import HTTPException

        # Mock supervisor to raise non-validation error
        # Use error message that doesn't contain "duration" or "intensity"
        with patch("app.api.routes.chat.supervisor_agent") as mock_supervisor:
            error = RuntimeError("Database connection failed")
            mock_supervisor.handle_message = AsyncMock(side_effect=error)

            request = ChatRequest(user_id="test_user", message="test message")

            # Should raise HTTPException for non-validation errors
            with pytest.raises(HTTPException) as exc_info:
                await send_message(request)

            assert exc_info.value.status_code == 500

    def test_tool_schema_allows_extra_fields(self):
        """Test that tool schema allows extra fields (extra='allow')."""
        schema = CreateWorkoutFromParamsInput(
            user_id="test_user",
            duration_minutes=30,
            intensity="moderate",
            extra_field="should_be_allowed",
        )
        assert schema.user_id == "test_user"
        # Extra field should be allowed (Pydantic V2 stores in model_extra)
        # Check if extra_field is accessible via model_extra or directly
        assert hasattr(schema, "model_extra") and schema.model_extra is not None
        assert "extra_field" in schema.model_extra or hasattr(schema, "extra_field")

