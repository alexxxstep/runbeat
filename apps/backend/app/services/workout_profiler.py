# apps/backend/app/services/workout_profiler.py
from dataclasses import dataclass, field
from typing import List, Optional, Literal
import math

from app.schemas.workout import Workout
from app.schemas.playlist import IntervalStage


@dataclass
class WorkoutSegment:
    """Represents a segment of the workout with specific musical targets."""
    name: str
    duration_seconds: float
    min_bpm: int
    max_bpm: int
    target_energy: float
    genres: List[str] = field(default_factory=list)
    type: Literal["warm-up", "main", "cool-down",
                  "high-intensity", "recovery"] = "main"


class WorkoutProfiler:
    """
    Analyzes workout parameters and creates a detailed musical profile,
    broken down into segments with specific track criteria.
    """

    def __init__(self, workout: Workout, user_preferences: dict, interval_stages: Optional[List[IntervalStage]] = None):
        self.workout = workout
        self.user_preferences = user_preferences
        self.interval_stages = interval_stages
        self.genres = user_preferences.get("top_genres", [])

    def create_profile(
        self,
        variant_strategy: Literal["primary", "alternative"] = "primary"
    ) -> List[WorkoutSegment]:
        """
        Generates the full musical profile for the workout based on its type.
        """
        if self.workout.type == "intervals" and self.interval_stages:
            return self._profile_intervals(variant_strategy)
        elif self.workout.type == "steady":
            return self._profile_steady(variant_strategy)
        elif self.workout.type == "progressive":
            return self._profile_progressive(variant_strategy)
        else:
            return self._profile_steady(variant_strategy)  # Fallback

    def _calculate_base_bpm(self, intensity: str) -> int:
        """Calculates a base BPM for a given intensity."""
        intensity_map = {
            "low": 130,
            "moderate": 145,
            "high": 165
        }
        return intensity_map.get(intensity, 145)

    def _profile_steady(self, strategy: str) -> List[WorkoutSegment]:
        """Generates a profile for a steady-state workout (warm-up, main, cool-down)."""
        segments = []
        duration_seconds = self.workout.duration_minutes * 60

        if duration_seconds < 600:  # Short workout
            warmup_duration = 120
            cooldown_duration = 120
        else:
            warmup_duration = 300  # 5 minutes
            cooldown_duration = 300  # 5 minutes

        main_duration = duration_seconds - warmup_duration - cooldown_duration
        target_bpm = self._calculate_base_bpm(self.workout.intensity)

        bpm_flexibility = 10 if strategy == "alternative" else 5

        if warmup_duration > 0:
            segments.append(WorkoutSegment(
                name="Warm-up", duration_seconds=warmup_duration,
                min_bpm=target_bpm - 20, max_bpm=target_bpm - 10,
                target_energy=0.5, type="warm-up", genres=self.genres
            ))
        if main_duration > 0:
            segments.append(WorkoutSegment(
                name="Main Workout", duration_seconds=main_duration,
                min_bpm=target_bpm - bpm_flexibility, max_bpm=target_bpm + bpm_flexibility,
                target_energy=0.7, type="main", genres=self.genres
            ))
        if cooldown_duration > 0:
            segments.append(WorkoutSegment(
                name="Cool-down", duration_seconds=cooldown_duration,
                min_bpm=target_bpm - 30, max_bpm=target_bpm - 20,
                target_energy=0.4, type="cool-down", genres=self.genres
            ))
        return segments

    def _profile_progressive(self, strategy: str) -> List[WorkoutSegment]:
        """Generates a profile for a workout with progressively increasing intensity."""
        segments = []
        duration_seconds = self.workout.duration_minutes * 60
        num_segments = 5  # Fixed number of progressive steps

        warmup_duration = 180 if duration_seconds > 600 else 120
        cooldown_duration = 180 if duration_seconds > 600 else 120

        main_duration = duration_seconds - warmup_duration - cooldown_duration
        segment_duration = main_duration / num_segments

        start_bpm = self._calculate_base_bpm("low")
        end_bpm = self._calculate_base_bpm("high")
        bpm_step = (end_bpm - start_bpm) / (num_segments - 1)

        bpm_flexibility = 8 if strategy == "alternative" else 4

        segments.append(WorkoutSegment(
            name="Warm-up", duration_seconds=warmup_duration,
            min_bpm=start_bpm - 20, max_bpm=start_bpm - 10,
            target_energy=0.5, type="warm-up", genres=self.genres
        ))

        for i in range(num_segments):
            current_bpm = int(start_bpm + (i * bpm_step))
            segments.append(WorkoutSegment(
                name=f"Progression {i+1}/{num_segments}",
                duration_seconds=segment_duration,
                min_bpm=current_bpm - bpm_flexibility,
                max_bpm=current_bpm + bpm_flexibility,
                target_energy=min(0.6 + (i * 0.05), 0.85),
                type="main", genres=self.genres
            ))

        segments.append(WorkoutSegment(
            name="Cool-down", duration_seconds=cooldown_duration,
            min_bpm=start_bpm - 25, max_bpm=start_bpm - 15,
            target_energy=0.4, type="cool-down", genres=self.genres
        ))
        return segments

    def _profile_intervals(self, strategy: str) -> List[WorkoutSegment]:
        """Generates a profile based on custom interval stages."""
        segments = []

        for stage in self.interval_stages:
            duration = stage.duration_minutes * 60
            min_bpm, max_bpm = stage.bpm_range

            # Determine type and energy based on name
            stage_name_lower = stage.name.lower()
            if "recovery" in stage_name_lower or "rest" in stage_name_lower:
                stage_type = "recovery"
                energy = 0.4
            elif "warm" in stage_name_lower:
                stage_type = "warm-up"
                energy = 0.5
            elif "cool" in stage_name_lower:
                stage_type = "cool-down"
                energy = 0.3
            else:
                stage_type = "high-intensity"
                energy = 0.8

            if strategy == "alternative":
                min_bpm -= 5
                max_bpm += 5
                energy = max(0.2, energy - 0.1)

            segments.append(WorkoutSegment(
                name=stage.name,
                duration_seconds=duration,
                min_bpm=min_bpm,
                max_bpm=max_bpm,
                target_energy=energy,
                type=stage_type,
                genres=self.genres
            ))

        return segments
