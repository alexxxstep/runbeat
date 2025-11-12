"""
Supabase service for database operations.
"""
from supabase import create_client, Client
from loguru import logger
from app.core.config import settings
from typing import Optional


class SupabaseService:
    """Service for Supabase database operations."""

    def __init__(self):
        """Initialize Supabase client."""
        self.client: Optional[Client] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Supabase client with service key."""
        try:
            self.client = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    def get_client(self) -> Client:
        """Get Supabase client instance."""
        if self.client is None:
            self._initialize_client()
        return self.client

    async def health_check(self) -> bool:
        """Check if Supabase connection is healthy."""
        try:
            # Simple query to check connection
            response = self.client.table("users").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False


# Singleton instance
supabase_service = SupabaseService()

