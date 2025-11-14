"""
API routes for error logs management.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from loguru import logger

from app.services.error_logging_service import error_logging_service
from app.models.error_log import ErrorLog

router = APIRouter(prefix="/error-logs", tags=["error-logs"])


@router.get("/", response_model=List[ErrorLog])
def get_error_logs(
    level: Optional[str] = Query(None, description="Filter by log level (ERROR, CRITICAL, WARNING)"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
):
    """
    Get error logs from database.

    Requires authentication and admin privileges in production.
    """
    try:
        # Validate level if provided
        if level and level not in ["ERROR", "CRITICAL", "WARNING"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid level. Must be one of: ERROR, CRITICAL, WARNING",
            )

        logs = error_logging_service.get_error_logs(
            level=level,
            user_id=user_id,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date,
        )

        return logs

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get error logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve error logs")


@router.get("/statistics")
def get_error_statistics(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
):
    """
    Get error statistics.

    Requires authentication and admin privileges in production.
    """
    try:
        stats = error_logging_service.get_error_statistics(days=days)
        return stats

    except Exception as e:
        logger.error(f"Failed to get error statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve error statistics"
        )

