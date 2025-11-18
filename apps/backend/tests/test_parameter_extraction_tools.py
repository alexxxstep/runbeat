"""
Unit tests for parameter extraction tools.
Tests the extract_workout_parameters tool and helper functions.
"""
import json
import pytest
from app.agents.tools.parameter_extraction_tools import (
    extract_workout_parameters,
    _extract_from_message,
    _merge_parameters,
    _check_all_collected,
)


class TestExtractFromMessage:
    """Test _extract_from_message helper function."""

    def test_extract_duration_ukrainian(self):
        """Test extracting duration in Ukrainian."""
        result = _extract_from_message("45 хвилин")
        assert result["duration_minutes"] == 45

        result = _extract_from_message("30 хв")
        assert result["duration_minutes"] == 30

    def test_extract_duration_english(self):
        """Test extracting duration in English."""
        result = _extract_from_message("45 minutes")
        assert result["duration_minutes"] == 45

        result = _extract_from_message("30 min")
        assert result["duration_minutes"] == 30

    def test_extract_duration_hours(self):
        """Test extracting duration in hours (converted to minutes)."""
        result = _extract_from_message("1 година")
        assert result["duration_minutes"] == 60

        result = _extract_from_message("1.5 hours")
        assert result["duration_minutes"] == 90

    def test_extract_intensity_low(self):
        """Test extracting low intensity."""
        test_cases = ["легка пробіжка", "easy run", "low intensity"]
        for message in test_cases:
            result = _extract_from_message(message)
            assert result.get("intensity") == "low", f"Failed for: {message}"

    def test_extract_intensity_moderate(self):
        """Test extracting moderate intensity."""
        test_cases = ["середня", "moderate", "темпова"]
        for message in test_cases:
            result = _extract_from_message(message)
            assert result.get("intensity") == "moderate", f"Failed for: {message}"

    def test_extract_intensity_high(self):
        """Test extracting high intensity."""
        test_cases = ["висока", "інтенсивна", "high", "hard"]
        for message in test_cases:
            result = _extract_from_message(message)
            assert result.get("intensity") == "high", f"Failed for: {message}"

    def test_extract_workout_type_intervals(self):
        """Test extracting intervals workout type."""
        test_cases = ["інтервальна", "intervals", "інтервали"]
        for message in test_cases:
            result = _extract_from_message(message)
            assert result.get("workout_type") == "intervals", f"Failed for: {message}"

    def test_extract_workout_type_fartlek(self):
        """Test extracting fartlek workout type."""
        test_cases = ["фартлек", "fartlek"]
        for message in test_cases:
            result = _extract_from_message(message)
            assert result.get("workout_type") == "fartlek", f"Failed for: {message}"

    def test_extract_workout_type_steady(self):
        """Test extracting steady workout type."""
        test_cases = ["пробіжка", "біг", "run", "steady"]
        for message in test_cases:
            result = _extract_from_message(message)
            assert result.get("workout_type") == "steady", f"Failed for: {message}"

    def test_extract_genres_ukrainian(self):
        """Test extracting genres in Ukrainian."""
        result = _extract_from_message("електронна музика")
        assert "electronic" in result.get("genres", [])

        result = _extract_from_message("рок")
        assert "rock" in result.get("genres", [])

        result = _extract_from_message("класична")
        assert "classical" in result.get("genres", [])

    def test_extract_genres_english(self):
        """Test extracting genres in English."""
        result = _extract_from_message("electronic music")
        assert "electronic" in result.get("genres", [])

        result = _extract_from_message("rock")
        assert "rock" in result.get("genres", [])

        result = _extract_from_message("jazz")
        assert "jazz" in result.get("genres", [])

    def test_extract_multiple_genres(self):
        """Test extracting multiple genres from one message."""
        result = _extract_from_message("класика джаз")
        genres = result.get("genres", [])
        assert "classical" in genres
        assert "jazz" in genres
        assert len(genres) == 2

    def test_extract_all_parameters(self):
        """Test extracting all parameters from one message."""
        result = _extract_from_message("інтервальна тренування 45 хвилин висока інтенсивність під electronic")

        assert result["duration_minutes"] == 45
        assert result["intensity"] == "high"
        assert result["workout_type"] == "intervals"
        assert "electronic" in result.get("genres", [])

    def test_extract_no_parameters(self):
        """Test message with no recognizable parameters."""
        result = _extract_from_message("так")
        assert "duration_minutes" not in result
        assert "intensity" not in result
        assert "workout_type" not in result
        assert "genres" not in result or result["genres"] == []


class TestMergeParameters:
    """Test _merge_parameters helper function."""

    def test_merge_empty_current(self):
        """Test merging when current is empty."""
        current = {}
        extracted = {"duration_minutes": 45, "intensity": "moderate"}

        result = _merge_parameters(current, extracted)

        assert result["duration_minutes"] == 45
        assert result["intensity"] == "moderate"

    def test_merge_no_overwrite(self):
        """Test that existing parameters are not overwritten."""
        current = {"duration_minutes": 30, "intensity": "low"}
        extracted = {"duration_minutes": 45, "intensity": "high"}

        result = _merge_parameters(current, extracted)

        # Should keep original values
        assert result["duration_minutes"] == 30
        assert result["intensity"] == "low"

    def test_merge_add_new_parameters(self):
        """Test adding new parameters to existing ones."""
        current = {"duration_minutes": 45}
        extracted = {"intensity": "moderate", "workout_type": "intervals"}

        result = _merge_parameters(current, extracted)

        assert result["duration_minutes"] == 45
        assert result["intensity"] == "moderate"
        assert result["workout_type"] == "intervals"

    def test_merge_genres_accumulate(self):
        """Test that genres accumulate (don't replace)."""
        current = {"genres": ["electronic"]}
        extracted = {"genres": ["rock"]}

        result = _merge_parameters(current, extracted)

        assert "electronic" in result["genres"]
        assert "rock" in result["genres"]
        assert len(result["genres"]) == 2

    def test_merge_genres_no_duplicates(self):
        """Test that duplicate genres are removed."""
        current = {"genres": ["electronic", "rock"]}
        extracted = {"genres": ["rock", "jazz"]}

        result = _merge_parameters(current, extracted)

        assert len(result["genres"]) == 3
        assert "electronic" in result["genres"]
        assert "rock" in result["genres"]
        assert "jazz" in result["genres"]

    def test_merge_empty_genres_list(self):
        """Test merging when genres is empty list."""
        current = {"genres": []}
        extracted = {"genres": ["rock"]}

        result = _merge_parameters(current, extracted)

        assert result["genres"] == ["rock"]


class TestCheckAllCollected:
    """Test _check_all_collected helper function."""

    def test_all_collected_true(self):
        """Test when all required parameters are present."""
        params = {
            "duration_minutes": 45,
            "intensity": "moderate",
            "genres": ["electronic"]
        }

        assert _check_all_collected(params) is True

    def test_all_collected_missing_duration(self):
        """Test when duration is missing."""
        params = {
            "intensity": "moderate",
            "genres": ["electronic"]
        }

        assert _check_all_collected(params) is False

    def test_all_collected_missing_intensity(self):
        """Test when intensity is missing."""
        params = {
            "duration_minutes": 45,
            "genres": ["electronic"]
        }

        assert _check_all_collected(params) is False

    def test_all_collected_missing_genres(self):
        """Test when genres are missing."""
        params = {
            "duration_minutes": 45,
            "intensity": "moderate",
            "genres": []
        }

        assert _check_all_collected(params) is False

    def test_all_collected_empty_params(self):
        """Test with empty parameters."""
        params = {}

        assert _check_all_collected(params) is False


class TestExtractWorkoutParametersTool:
    """Test the main extract_workout_parameters tool."""

    def test_tool_basic_extraction(self):
        """Test basic parameter extraction through the tool."""
        result_json = extract_workout_parameters.invoke({
            "user_message": "інтервальна 45 хвилин",
            "conversation_history": "[]",
            "current_params": "{}"
        })

        result = json.loads(result_json)

        assert result["duration_minutes"] == 45
        assert result["workout_type"] == "intervals"
        assert result["all_collected"] is False  # Missing intensity and genres

    def test_tool_accumulate_parameters(self):
        """Test accumulating parameters across multiple messages."""
        # First message: workout type and duration
        result1_json = extract_workout_parameters.invoke({
            "user_message": "інтервальна 44 хвилин",
            "conversation_history": "[]",
            "current_params": "{}"
        })
        result1 = json.loads(result1_json)

        # Second message: genres
        result2_json = extract_workout_parameters.invoke({
            "user_message": "класика джаз",
            "conversation_history": "[]",
            "current_params": result1_json
        })
        result2 = json.loads(result2_json)

        assert result2["duration_minutes"] == 44
        assert result2["workout_type"] == "intervals"
        assert "classical" in result2["genres"]
        assert "jazz" in result2["genres"]
        assert result2["all_collected"] is False  # Still missing intensity

        # Third message: intensity
        result3_json = extract_workout_parameters.invoke({
            "user_message": "середня",
            "conversation_history": "[]",
            "current_params": result2_json
        })
        result3 = json.loads(result3_json)

        assert result3["duration_minutes"] == 44
        assert result3["workout_type"] == "intervals"
        assert result3["intensity"] == "moderate"
        assert "classical" in result3["genres"]
        assert "jazz" in result3["genres"]
        assert result3["all_collected"] is True  # All collected!

    def test_tool_invalid_json_handling(self):
        """Test handling of invalid JSON inputs."""
        # Should not crash, should return valid JSON
        result_json = extract_workout_parameters.invoke({
            "user_message": "45 хвилин",
            "conversation_history": "invalid json",
            "current_params": "also invalid"
        })

        result = json.loads(result_json)  # Should parse successfully
        assert result["duration_minutes"] == 45

    def test_tool_problematic_scenario(self):
        """Test the problematic scenario from user's example."""
        # Message 1: "інтервальна"
        result1_json = extract_workout_parameters.invoke({
            "user_message": "інтервальна",
            "conversation_history": "[]",
            "current_params": "{}"
        })
        result1 = json.loads(result1_json)
        assert result1["workout_type"] == "intervals"

        # Message 2: "44 хвилин"
        result2_json = extract_workout_parameters.invoke({
            "user_message": "44 хвилин",
            "conversation_history": "[]",
            "current_params": result1_json
        })
        result2 = json.loads(result2_json)
        assert result2["workout_type"] == "intervals"
        assert result2["duration_minutes"] == 44

        # Message 3: "класика джаз"
        result3_json = extract_workout_parameters.invoke({
            "user_message": "класика джаз",
            "conversation_history": "[]",
            "current_params": result2_json
        })
        result3 = json.loads(result3_json)
        assert result3["workout_type"] == "intervals"
        assert result3["duration_minutes"] == 44
        assert "classical" in result3["genres"]
        assert "jazz" in result3["genres"]

        # Message 4: "так" (no new params)
        result4_json = extract_workout_parameters.invoke({
            "user_message": "так",
            "conversation_history": "[]",
            "current_params": result3_json
        })
        result4 = json.loads(result4_json)
        assert result4["workout_type"] == "intervals"
        assert result4["duration_minutes"] == 44
        assert "classical" in result4["genres"]
        assert "jazz" in result4["genres"]

        # Message 5: "середня"
        result5_json = extract_workout_parameters.invoke({
            "user_message": "середня",
            "conversation_history": "[]",
            "current_params": result4_json
        })
        result5 = json.loads(result5_json)
        assert result5["workout_type"] == "intervals"
        assert result5["duration_minutes"] == 44
        assert result5["intensity"] == "moderate"
        assert "classical" in result5["genres"]
        assert "jazz" in result5["genres"]
        assert result5["all_collected"] is True
