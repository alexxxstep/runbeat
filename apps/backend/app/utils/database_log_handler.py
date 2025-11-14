"""
Custom loguru handler for logging errors to database.
"""
import sys
import threading
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
            # Get log level
            level = message["level"].name

            # Only log ERROR and CRITICAL to database
            if level not in ["ERROR", "CRITICAL", "WARNING"]:
                return

            # Check if level meets minimum threshold
            if self.level_map.get(level, 0) < self.level_map.get(self.min_level, 0):
                return

            # Extract message text
            message_text = message["message"]

            # Extract exception if present
            exception = message.get("exception")
            if exception:
                exception = exception.value

            # Extract user context if available
            user_id = message.get("extra", {}).get("user_id")
            request_path = message.get("extra", {}).get("request_path")
            request_method = message.get("extra", {}).get("request_method")
            request_body = message.get("extra", {}).get("request_body")
            response_status = message.get("extra", {}).get("response_status")
            error_details = message.get("extra", {}).get("error_details")

            # Log to database asynchronously (fire and forget)
            # Use threading to avoid blocking the main event loop
            def log_to_db():
                """Log error to database in a separate thread."""
                try:
                    # error_logging_service.log_error is synchronous
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
                    # Don't fail if database logging fails
                    print(f"Failed to log to database: {e}", file=sys.stderr)

            # Start logging in a separate thread (fire and forget)
            thread = threading.Thread(target=log_to_db, daemon=True)
            thread.start()

        except Exception as e:
            # Don't fail if handler fails - just log to stderr
            print(f"Database log handler error: {e}", file=sys.stderr)

