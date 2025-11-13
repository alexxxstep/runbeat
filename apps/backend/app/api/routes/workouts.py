"""
Workout CRUD endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from typing import List, Optional
from datetime import datetime

from app.services.supabase_service import SupabaseService
from app.schemas.workout import (
    WorkoutCreateRequest,
    WorkoutResponse,
    WorkoutListResponse,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])


def get_supabase_service() -> SupabaseService:
    """Dependency to get SupabaseService instance."""
    return SupabaseService()


@router.post("", response_model=WorkoutResponse, status_code=201)
async def create_workout(
    request: WorkoutCreateRequest,
    supabase: SupabaseService = Depends(get_supabase_service),
) -> WorkoutResponse:
    """
    Create a new workout.

    Args:
        request: Workout creation request
        supabase: SupabaseService dependency

    Returns:
        Created workout

    Raises:
        HTTPException: If creation fails
    """
    try:
        logger.info(f"Creating workout for user {request.user_id}")

        # Insert workout into database
        workout_data = {
            "user_id": request.user_id,
            "type": request.workout.type,
            "duration_minutes": request.workout.duration_minutes,
            "intensity": request.workout.intensity,
            "hr_zones": request.workout.hr_zones,
        }

        # Add optional fields if provided in request
        if request.genres:
            workout_data["genres"] = request.genres
        if request.interval_stages:
            workout_data["interval_stages"] = request.interval_stages
        if request.prompt:
            workout_data["prompt"] = request.prompt

        result = (
            supabase.get_client()
            .table("workouts")
            .insert(workout_data)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500, detail="Failed to create workout")

        workout = result.data[0]

        return WorkoutResponse(
            id=workout["id"],
            user_id=workout["user_id"],
            type=workout["type"],
            duration_minutes=workout["duration_minutes"],
            intensity=workout["intensity"],
            hr_zones=workout["hr_zones"],
            completed_at=(
                datetime.fromisoformat(
                    workout["completed_at"].replace("Z", "+00:00"))
                if workout.get("completed_at")
                else None
            ),
            created_at=datetime.fromisoformat(
                workout["created_at"].replace("Z", "+00:00")
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create workout: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create workout: {str(e)}",
        )


@router.get("", response_model=WorkoutListResponse)
async def get_workouts(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(
        10, ge=1, le=100, description="Number of workouts to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    supabase: SupabaseService = Depends(get_supabase_service),
) -> WorkoutListResponse:
    """
    Get list of workouts for a user.

    Args:
        user_id: User ID
        limit: Maximum number of workouts to return
        offset: Pagination offset
        supabase: SupabaseService dependency

    Returns:
        List of workouts

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"Fetching workouts for user {user_id}")

        # Get workouts from database
        result = (
            supabase.get_client()
            .table("workouts")
            .select("*", count="exact")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )

        workouts = [
            WorkoutResponse(
                id=w["id"],
                user_id=w["user_id"],
                type=w["type"],
                duration_minutes=w["duration_minutes"],
                intensity=w["intensity"],
                hr_zones=w["hr_zones"],
                genres=w.get("genres", []),
                interval_stages=w.get("interval_stages"),
                prompt=w.get("prompt"),
                completed_at=(
                    datetime.fromisoformat(
                        w["completed_at"].replace("Z", "+00:00"))
                    if w.get("completed_at")
                    else None
                ),
                created_at=datetime.fromisoformat(
                    w["created_at"].replace("Z", "+00:00")
                ),
            )
            for w in result.data
        ]

        return WorkoutListResponse(
            workouts=workouts,
            total=result.count if result.count is not None else len(workouts),
        )

    except Exception as e:
        logger.error(f"Failed to get workouts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workouts: {str(e)}",
        )


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: str,
    user_id: str = Query(..., description="User ID"),
    supabase: SupabaseService = Depends(get_supabase_service),
) -> WorkoutResponse:
    """
    Get a specific workout by ID.

    Args:
        workout_id: Workout ID
        user_id: User ID (for authorization)
        supabase: SupabaseService dependency

    Returns:
        Workout details

    Raises:
        HTTPException: If workout not found or access denied
    """
    try:
        logger.info(f"Fetching workout {workout_id} for user {user_id}")

        # Get workout from database
        result = (
            supabase.get_client()
            .table("workouts")
            .select("*")
            .eq("id", workout_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Workout not found")

        workout = result.data[0]

        return WorkoutResponse(
            id=workout["id"],
            user_id=workout["user_id"],
            type=workout["type"],
            duration_minutes=workout["duration_minutes"],
            intensity=workout["intensity"],
            hr_zones=workout["hr_zones"],
            genres=workout.get("genres", []),
            interval_stages=workout.get("interval_stages"),
            prompt=workout.get("prompt"),
            completed_at=(
                datetime.fromisoformat(
                    workout["completed_at"].replace("Z", "+00:00"))
                if workout.get("completed_at")
                else None
            ),
            created_at=datetime.fromisoformat(
                workout["created_at"].replace("Z", "+00:00")
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workout: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workout: {str(e)}",
        )


@router.delete("/{workout_id}", status_code=204)
async def delete_workout(
    workout_id: str,
    user_id: str = Query(..., description="User ID"),
    supabase: SupabaseService = Depends(get_supabase_service),
):
    """
    Delete a workout.

    Args:
        workout_id: Workout ID
        user_id: User ID (for authorization)
        supabase: SupabaseService dependency

    Raises:
        HTTPException: If workout not found or deletion fails
    """
    try:
        logger.info(f"Deleting workout {workout_id} for user {user_id}")

        # Delete workout from database
        result = (
            supabase.get_client()
            .table("workouts")
            .delete()
            .eq("id", workout_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Workout not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workout: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete workout: {str(e)}",
        )


@router.patch("/{workout_id}/complete", response_model=WorkoutResponse)
async def complete_workout(
    workout_id: str,
    user_id: str = Query(..., description="User ID"),
    supabase: SupabaseService = Depends(get_supabase_service),
) -> WorkoutResponse:
    """
    Mark a workout as completed.

    Args:
        workout_id: Workout ID
        user_id: User ID (for authorization)
        supabase: SupabaseService dependency

    Returns:
        Updated workout

    Raises:
        HTTPException: If workout not found or update fails
    """
    try:
        logger.info(
            f"Marking workout {workout_id} as completed for user {user_id}")

        # Update workout
        result = (
            supabase.get_client()
            .table("workouts")
            .update({"completed_at": datetime.now().isoformat()})
            .eq("id", workout_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Workout not found")

        workout = result.data[0]

        return WorkoutResponse(
            id=workout["id"],
            user_id=workout["user_id"],
            type=workout["type"],
            duration_minutes=workout["duration_minutes"],
            intensity=workout["intensity"],
            hr_zones=workout["hr_zones"],
            genres=workout.get("genres", []),
            interval_stages=workout.get("interval_stages"),
            prompt=workout.get("prompt"),
            completed_at=(
                datetime.fromisoformat(
                    workout["completed_at"].replace("Z", "+00:00"))
                if workout.get("completed_at")
                else None
            ),
            created_at=datetime.fromisoformat(
                workout["created_at"].replace("Z", "+00:00")
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete workout: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete workout: {str(e)}",
        )
