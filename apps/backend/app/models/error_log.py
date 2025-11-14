"""
Error log model for database storage.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class ErrorLog(BaseModel):
    """Error log model."""

    id: Optional[UUID] = Field(None, description="Error log ID")
    level: str = Field(..., description="Log level (ERROR, CRITICAL, WARNING)")
    message: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Error type/class name")
    error_details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details as JSON"
    )
    stack_trace: Optional[str] = Field(None, description="Stack trace")
    user_id: Optional[UUID] = Field(None, description="User ID if error is user-related")
    request_path: Optional[str] = Field(None, description="API request path")
    request_method: Optional[str] = Field(None, description="HTTP method")
    request_body: Optional[Dict[str, Any]] = Field(
        None, description="Request body as JSON"
    )
    response_status: Optional[int] = Field(None, description="HTTP response status")
    environment: str = Field("production", description="Environment (production, development)")
    service_name: str = Field("runbeat-backend", description="Service name")
    created_at: Optional[datetime] = Field(None, description="Timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "level": "ERROR",
                "message": "Failed to generate playlist",
                "error_type": "ValueError",
                "error_details": {"workout_id": "123", "reason": "Invalid parameters"},
                "stack_trace": "Traceback...",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "request_path": "/api/v1/playlists/generate",
                "request_method": "POST",
                "response_status": 500,
                "environment": "production",
            }
        }

