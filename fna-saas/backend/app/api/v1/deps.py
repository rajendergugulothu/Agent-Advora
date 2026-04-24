"""
FastAPI dependencies shared across route handlers.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import create_client

from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import UserProfile

settings = get_settings()
_bearer = HTTPBearer()


def get_supabase():
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """Verify the Supabase Bearer token and return the authenticated user's ID."""
    try:
        supabase = get_supabase()
        response = supabase.auth.get_user(credentials.credentials)
        if not response.user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return str(response.user.id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """Load the current user's profile from the database."""
    user = await db.get(UserProfile, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
