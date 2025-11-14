"""
Error logging service for storing errors in database.
"""
import traceback
import sys
from typing import Optional, Dict, Any
from loguru import logger
from app.services.supabase_service import supabase_service
from app.models.error_log import ErrorLog
from app.core.config import settings
from uuid import UUID


class ErrorLoggingService:
    """Service for logging errors to database."""

    def __init__(self):
        """Initialize error logging service."""
        self.supabase = supabase_service.get_client()
        self.environment = settings.ENVIRONMENT if hasattr(settings, "ENVIRONMENT") else "production"
        logger.info(f"ErrorLoggingService initialized (environment: {self.environment})")

    def log_error(
        self,
        level: str,
        message: str,
        exception: Optional[Exception] = None,
        user_id: Optional[UUID] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        request_body: Optional[Dict[str, Any]] = None,
        response_status: Optional[int] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Log error to database.

        Args:
            level: Log level (ERROR, CRITICAL, WARNING)
            message: Error message
            exception: Exception object (optional)
            user_id: User ID if error is user-related
            request_path: API request path
            request_method: HTTP method
            request_body: Request body
            response_status: HTTP response status
            error_details: Additional error details

        Returns:
            Error log ID if successful, None otherwise
        """
        try:
            # Extract error information from exception
            error_type = None
            stack_trace = None
            if exception:
                error_type = type(exception).__name__
                stack_trace = "".join(
                    traceback.format_exception(
                        type(exception), exception, exception.__traceback__
                    )
                )

            # Prepare error log data
            error_log_data = {
                "level": level,
                "message": message,
                "error_type": error_type,
                "error_details": error_details,
                "stack_trace": stack_trace,
                "user_id": str(user_id) if user_id else None,
                "request_path": request_path,
                "request_method": request_method,
                "request_body": request_body,
                "response_status": response_status,
                "environment": self.environment,
                "service_name": "runbeat-backend",
            }

            # Insert into database
            response = (
                self.supabase.table("error_logs")
                .insert(error_log_data)
                .execute()
            )

            if response.data and len(response.data) > 0:
                error_log_id = response.data[0].get("id")
                logger.debug(f"Error logged to database: {error_log_id}")
                return error_log_id
            else:
                logger.warning("Failed to log error to database: empty response")
                return None

        except Exception as e:
            # Don't fail if error logging fails - just log to console
            logger.error(f"Failed to log error to database: {e}")
            # Also log to stderr to ensure it's not lost
            print(f"CRITICAL: Failed to log error to database: {e}", file=sys.stderr)
            return None

    def get_error_logs(
        self,
        level: Optional[str] = None,
        user_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list:
        """
        Get error logs from database.

        Args:
            level: Filter by log level
            user_id: Filter by user ID
            limit: Maximum number of logs to return
            offset: Offset for pagination
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            List of error logs
        """
        try:
            query = self.supabase.table("error_logs").select("*")

            if level:
                query = query.eq("level", level)
            if user_id:
                query = query.eq("user_id", str(user_id))
            if start_date:
                query = query.gte("created_at", start_date)
            if end_date:
                query = query.lte("created_at", end_date)

            query = query.order("created_at", desc=True).limit(limit).offset(offset)

            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Failed to get error logs from database: {e}")
            return []

    def get_error_statistics(
        self,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get error statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with error statistics
        """
        try:
            # Get total errors
            total_response = (
                self.supabase.table("error_logs")
                .select("id", count="exact")
                .gte("created_at", f"NOW() - INTERVAL '{days} days'")
                .execute()
            )
            total_errors = total_response.count if hasattr(total_response, "count") else 0

            # Get errors by level
            levels = ["ERROR", "CRITICAL", "WARNING"]
            errors_by_level = {}
            for level in levels:
                level_response = (
                    self.supabase.table("error_logs")
                    .select("id", count="exact")
                    .eq("level", level)
                    .gte("created_at", f"NOW() - INTERVAL '{days} days'")
                    .execute()
                )
                errors_by_level[level] = (
                    level_response.count if hasattr(level_response, "count") else 0
                )

            # Get top error types
            top_errors_response = (
                self.supabase.table("error_logs")
                .select("error_type", count="exact")
                .gte("created_at", f"NOW() - INTERVAL '{days} days'")
                .not_.is_("error_type", "null")
                .execute()
            )
            # Note: Supabase doesn't support GROUP BY directly in Python client
            # This would need to be done via raw SQL or RPC function

            return {
                "total_errors": total_errors,
                "errors_by_level": errors_by_level,
                "period_days": days,
            }

        except Exception as e:
            logger.error(f"Failed to get error statistics: {e}")
            return {
                "total_errors": 0,
                "errors_by_level": {},
                "period_days": days,
            }


# Singleton instance
error_logging_service = ErrorLoggingService()

