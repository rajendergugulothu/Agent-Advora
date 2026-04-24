"""
Instagram OAuth and connection endpoints.

Flow:
1. GET /instagram/connect     → returns the Meta OAuth URL
2. GET /instagram/callback    → Meta redirects here with ?code=...
3. We exchange code → short-lived token → long-lived token
4. We fetch the user's pages → get their Instagram account ID
5. We store encrypted credentials in instagram_connections
"""

import uuid
from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_current_user_id
from app.core.config import get_settings
from app.core.security import encrypt_token
from app.db.database import get_db
from app.db.models import InstagramConnection, UserProfile
from app.services.instagram import (
    exchange_code_for_token,
    exchange_for_long_lived_token,
    get_instagram_account_id,
    get_instagram_profile,
    get_pages,
    token_expires_at,
)

router = APIRouter()
settings = get_settings()

_OAUTH_SCOPES = [
    "instagram_basic",
    "instagram_content_publish",
    "instagram_manage_insights",
    "pages_show_list",
    "pages_read_engagement",
]


# ── Schemas ───────────────────────────────────────────────────────────────────

class ConnectURLResponse(BaseModel):
    url: str


class ConnectionStatusResponse(BaseModel):
    connected: bool
    username: str | None
    profile_picture_url: str | None
    token_expires_at: datetime | None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/connect", response_model=ConnectURLResponse)
async def get_connect_url(user: UserProfile = Depends(get_current_user)):
    """Return the Meta OAuth URL the user should be redirected to."""
    params = urlencode({
        "client_id": settings.meta_app_id,
        "redirect_uri": str(settings.meta_oauth_redirect_uri),
        "scope": ",".join(_OAUTH_SCOPES),
        "response_type": "code",
        "state": str(user.id),       # CSRF protection — verified in callback
    })
    url = f"https://www.facebook.com/v21.0/dialog/oauth?{params}"
    return ConnectURLResponse(url=url)


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Meta redirects here after the user grants permissions.
    Exchanges the code for tokens and stores the connection.
    Then redirects the user back to the dashboard.
    """
    user_id = state      # state == user.id set in /connect

    user = await db.get(UserProfile, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Exchange code for short-lived token
    short_token_data = await exchange_code_for_token(code)
    short_token = short_token_data.get("access_token")
    if not short_token:
        raise HTTPException(status_code=400, detail="Failed to get access token from Meta")

    # Upgrade to long-lived token (60 days)
    long_token_data = await exchange_for_long_lived_token(short_token)
    long_token = long_token_data.get("access_token")
    expires_in = long_token_data.get("expires_in", 5184000)     # default 60 days
    if not long_token:
        raise HTTPException(status_code=400, detail="Failed to get long-lived token")

    # Get pages to find the Instagram account ID
    pages = await get_pages(long_token)
    if not pages:
        raise HTTPException(
            status_code=400,
            detail="No Facebook Pages found. Make sure your Instagram is connected to a Facebook Page.",
        )

    # Use first page with an Instagram business account
    instagram_account_id = None
    page_id = None
    for page in pages:
        ig_id = await get_instagram_account_id(page["id"], long_token)
        if ig_id:
            instagram_account_id = ig_id
            page_id = page["id"]
            break

    if not instagram_account_id:
        raise HTTPException(
            status_code=400,
            detail="No Instagram Business Account found. Make sure your Instagram account is a Business or Creator account linked to your Facebook Page.",
        )

    # Fetch profile info
    profile = await get_instagram_profile(instagram_account_id, long_token)

    expires_at = token_expires_at(expires_in)

    # Upsert the instagram_connection row
    existing_result = await db.execute(
        select(InstagramConnection).where(InstagramConnection.user_id == uuid.UUID(user_id))
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.instagram_account_id = encrypt_token(instagram_account_id)
        existing.instagram_access_token = encrypt_token(long_token)
        existing.token_expires_at = expires_at
        existing.username = profile.get("username")
        existing.profile_picture_url = profile.get("profile_picture_url")
        existing.page_id = page_id
        existing.is_active = True
        existing.last_refreshed_at = datetime.now(timezone.utc)
    else:
        conn = InstagramConnection(
            user_id=uuid.UUID(user_id),
            instagram_account_id=encrypt_token(instagram_account_id),
            instagram_access_token=encrypt_token(long_token),
            token_expires_at=expires_at,
            username=profile.get("username"),
            profile_picture_url=profile.get("profile_picture_url"),
            page_id=page_id,
        )
        db.add(conn)

    # Redirect to frontend dashboard after successful connect
    return RedirectResponse(url=f"{settings.frontend_url}/dashboard/connect?status=success")


@router.get("/status", response_model=ConnectionStatusResponse)
async def get_connection_status(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check whether this user has an active Instagram connection."""
    result = await db.execute(
        select(InstagramConnection).where(
            InstagramConnection.user_id == user.id,
            InstagramConnection.is_active == True,
        )
    )
    ig = result.scalar_one_or_none()
    if not ig:
        return ConnectionStatusResponse(connected=False, username=None, profile_picture_url=None, token_expires_at=None)

    return ConnectionStatusResponse(
        connected=True,
        username=ig.username,
        profile_picture_url=ig.profile_picture_url,
        token_expires_at=ig.token_expires_at,
    )


@router.delete("/disconnect")
async def disconnect_instagram(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate the user's Instagram connection."""
    result = await db.execute(
        select(InstagramConnection).where(
            InstagramConnection.user_id == user.id,
            InstagramConnection.is_active == True,
        )
    )
    ig = result.scalar_one_or_none()
    if ig:
        ig.is_active = False
    return {"disconnected": True}
