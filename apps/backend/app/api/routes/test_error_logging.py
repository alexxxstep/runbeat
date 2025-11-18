"""
Test endpoint for error logging verification.
This file is for testing purposes only and should be removed in production.
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from app.services.error_logging_service import error_logging_service
from uuid import uuid4

router = APIRouter(prefix="/test-error-logging", tags=["test"])


@router.get("/trigger-error")
async def trigger_test_error():
    """
    Trigger a test error to verify error logging works.
    This will:
    1. Log an error via logger.error() (should be caught by DatabaseLogHandler)
    2. Return error details
    """
    try:
        # Simulate an error
        test_data = {"test": "data", "user_id": str(uuid4())}

        # This should be caught by DatabaseLogHandler
        logger.error(
            "TEST ERROR: This is a test error to verify logging system",
            extra={
                "user_id": str(uuid4()),
                "request_path": "/test-error-logging/trigger-error",
                "request_method": "GET",
                "error_details": test_data,
            }
        )

        return {
            "status": "error_logged",
            "message": "Test error has been logged. Check Supabase error_logs table.",
            "note": "This error was logged via logger.error() and should appear in the database.",
        }
    except Exception as e:
        logger.error(f"Failed to trigger test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trigger-critical")
async def trigger_test_critical():
    """
    Trigger a test CRITICAL error.
    """
    try:
        logger.critical(
            "TEST CRITICAL: This is a test critical error",
            extra={
                "user_id": str(uuid4()),
                "request_path": "/test-error-logging/trigger-critical",
                "request_method": "GET",
                "error_details": {"severity": "critical", "test": True},
            }
        )

        return {
            "status": "critical_logged",
            "message": "Test critical error has been logged.",
        }
    except Exception as e:
        logger.error(f"Failed to trigger test critical: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trigger-warning")
async def trigger_test_warning():
    """
    Trigger a test WARNING.
    """
    try:
        logger.warning(
            "TEST WARNING: This is a test warning",
            extra={
                "user_id": str(uuid4()),
                "request_path": "/test-error-logging/trigger-warning",
                "request_method": "GET",
                "error_details": {"severity": "warning", "test": True},
            }
        )

        return {
            "status": "warning_logged",
            "message": "Test warning has been logged.",
        }
    except Exception as e:
        logger.error(f"Failed to trigger test warning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trigger-exception")
async def trigger_test_exception():
    """
    Trigger a test exception to verify exception logging.
    """
    try:
        # Raise an exception
        raise ValueError("TEST EXCEPTION: This is a test exception for logging verification")
    except ValueError as e:
        logger.error(
            f"Caught test exception: {e}",
            extra={
                "user_id": str(uuid4()),
                "request_path": "/test-error-logging/trigger-exception",
                "request_method": "GET",
                "error_details": {"exception_type": type(e).__name__},
            }
        )

        return {
            "status": "exception_logged",
            "message": "Test exception has been logged.",
            "exception_type": type(e).__name__,
        }


@router.post("/direct-log")
async def direct_log_test(
    message: str = "Test direct log",
    level: str = "ERROR",
):
    """
    Directly log an error using error_logging_service (sync version).
    This bypasses DatabaseLogHandler and calls the service directly.
    """
    try:
        error_id = error_logging_service.log_error(
            level=level,
            message=message,
            exception=None,
            user_id=uuid4(),
            request_path="/test-error-logging/direct-log",
            request_method="POST",
            error_details={"test": True, "direct_call": True, "method": "sync"},
        )

        return {
            "status": "logged",
            "error_id": error_id,
            "message": f"Error logged directly (sync) with ID: {error_id}",
        }
    except Exception as e:
        logger.error(f"Failed to log directly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/direct-log-async")
async def direct_log_async_test(
    message: str = "Test direct async log",
    level: str = "ERROR",
):
    """
    Directly log an error using error_logging_service (async version).
    This tests the new async logging method.
    """
    try:
        error_id = await error_logging_service.log_error_async(
            level=level,
            message=message,
            exception=None,
            user_id=uuid4(),
            request_path="/test-error-logging/direct-log-async",
            request_method="POST",
            error_details={"test": True, "direct_call": True, "method": "async"},
        )

        return {
            "status": "logged",
            "error_id": error_id,
            "message": f"Error logged directly (async) with ID: {error_id}",
        }
    except Exception as e:
        logger.error(f"Failed to log directly (async): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-recent-logs")
async def check_recent_logs(limit: int = 5):
    """
    Check recent error logs from database.
    """
    try:
        logs = error_logging_service.get_error_logs(limit=limit)

        return {
            "status": "success",
            "count": len(logs),
            "logs": logs,
        }
    except Exception as e:
        logger.error(f"Failed to fetch recent logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

