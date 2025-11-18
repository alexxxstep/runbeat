"""
Custom loguru handler for logging errors to database.
"""
import sys
import asyncio
from typing import Dict, Any
from loguru import logger
from app.services.error_logging_service import error_logging_service


class DatabaseLogHandler:
    """Custom handler for loguru that logs errors to database."""

    def __init__(self, min_level: str = "ERROR"):
        """
        Initialize database log handler.

        Args:
            min_level: Minimum log level to save to database (default: ERROR)
        """
        self.min_level = min_level
        self.level_map = {
            "TRACE": 0,
            "DEBUG": 10,
            "INFO": 20,
            "SUCCESS": 25,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
        }
        logger.info(f"DatabaseLogHandler initialized (min_level: {min_level})")

    def __call__(self, message: Dict[str, Any]) -> None:
        """
        Handle log message.

        Args:
            message: Log message dictionary from loguru
        """
        try:
            # Ensure message is a dictionary
            if not isinstance(message, dict):
                return

            # Get log level - handle both object and string formats
            level_obj = message.get("level")
            level = None

            if level_obj is not None:
                if hasattr(level_obj, "name"):
                    level = level_obj.name
                elif isinstance(level_obj, str):
                    level = level_obj
                elif isinstance(level_obj, dict):
                    level = level_obj.get("name", "ERROR")

            # If still no level, try alternative paths
            if not level or not isinstance(level, str):
                record = message.get("record", {})
                if isinstance(record, dict):
                    record_level = record.get("level")
                    if hasattr(record_level, "name"):
                        level = record_level.name
                    elif isinstance(record_level, str):
                        level = record_level
                    elif isinstance(record_level, dict):
                        level = record_level.get("name", "ERROR")

            # Final fallback
            if not level or not isinstance(level, str):
                level = "ERROR"

            # Only log ERROR and CRITICAL to database
            if level not in ["ERROR", "CRITICAL", "WARNING"]:
                return

            # Check if level meets minimum threshold
            if self.level_map.get(level, 0) < self.level_map.get(self.min_level, 0):
                return

            # Extract message text - handle different formats
            message_text = message.get("message", "")
            if not message_text:
                # Try alternative paths
                message_text = message.get("record", {}).get("message", "") if isinstance(message.get("record"), dict) else ""
            if not message_text:
                message_text = str(message)  # Last resort

            # Extract exception if present
            exception = message.get("exception")
            if exception and hasattr(exception, "value"):
                exception = exception.value
            elif exception and isinstance(exception, Exception):
                exception = exception
            else:
                exception = None

            # Extract user context if available - safely handle nested dicts
            extra = message.get("extra", {})
            if not isinstance(extra, dict):
                extra = {}

            user_id = extra.get("user_id") if isinstance(extra, dict) else None
            request_path = extra.get("request_path") if isinstance(extra, dict) else None
            request_method = extra.get("request_method") if isinstance(extra, dict) else None
            request_body = extra.get("request_body") if isinstance(extra, dict) else None
            response_status = extra.get("response_status") if isinstance(extra, dict) else None
            error_details = extra.get("error_details") if isinstance(extra, dict) else None

            # Log to database asynchronously (fire and forget)
            # Use asyncio.create_task to avoid blocking the event loop
            async def log_to_db_async():
                """Log error to database asynchronously."""
                try:
                    await error_logging_service.log_error_async(
                        level=level,
                        message=message_text,
                        exception=exception,
                        user_id=user_id,
                        request_path=request_path,
                        request_method=request_method,
                        request_body=request_body,
                        response_status=response_status,
                        error_details=error_details,
                    )
                except Exception as e:
                    # Don't fail if database logging fails
                    print(f"Failed to log to database (async): {e}", file=sys.stderr)

            # Create task in event loop (fire and forget)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, create task
                    asyncio.create_task(log_to_db_async())
                else:
                    # If loop is not running, run in executor
                    # This shouldn't happen in FastAPI, but handle it gracefully
                    def sync_log():
                        error_logging_service.log_error(
                            level=level,
                            message=message_text,
                            exception=exception,
                            user_id=user_id,
                            request_path=request_path,
                            request_method=request_method,
                            request_body=request_body,
                            response_status=response_status,
                            error_details=error_details,
                        )
                    import threading
                    thread = threading.Thread(target=sync_log, daemon=True)
                    thread.start()
            except RuntimeError:
                # No event loop available, fall back to sync
                error_logging_service.log_error(
                    level=level,
                    message=message_text,
                    exception=exception,
                    user_id=user_id,
                    request_path=request_path,
                    request_method=request_method,
                    request_body=request_body,
                    response_status=response_status,
                    error_details=error_details,
                )

        except Exception as e:
            # Don't fail if handler fails - just log to stderr
            print(f"Database log handler error: {e}", file=sys.stderr)

