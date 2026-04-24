"""
User profile and settings endpoints.
"""

import uuid
from datetime import datetime

import pytz
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.database import get_db
from app.db.models import InstagramConnection, UserProfile
from app.services.scheduler import get_scheduler

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    id: str
    full_name: str
    company_name: str | None
    whatsapp_number: str | None
    post_time_hour: int
    post_time_minute: int
    timezone: str
    scheduler_active: bool
    instagram_connected: bool
    instagram_username: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=100)
    company_name: str | None = Field(None, max_length=100)
    whatsapp_number: str | None = Field(None, pattern=r"^\+[1-9]\d{7,14}$")
    post_time_hour: int | None = Field(None, ge=0, le=23)
    post_time_minute: int | None = Field(None, ge=0, le=59)
    timezone: str | None = None


class SchedulerToggleRequest(BaseModel):
    active: bool


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _instagram_for_user(db: AsyncSession, user_id: uuid.UUID) -> InstagramConnection | None:
    result = await db.execute(
        select(InstagramConnection).where(
            InstagramConnection.user_id == user_id,
            InstagramConnection.is_active == True,
        )
    )
    return result.scalar_one_or_none()


def _profile_response(user: UserProfile, ig: InstagramConnection | None) -> ProfileResponse:
    return ProfileResponse(
        id=str(user.id),
        full_name=user.full_name,
        company_name=user.company_name,
        whatsapp_number=user.whatsapp_number,
        post_time_hour=user.post_time_hour,
        post_time_minute=user.post_time_minute,
        timezone=user.timezone,
        scheduler_active=user.scheduler_active,
        instagram_connected=ig is not None,
        instagram_username=ig.username if ig else None,
        created_at=user.created_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ig = await _instagram_for_user(db, user.id)
    return _profile_response(user, ig)


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    body: UpdateProfileRequest,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.timezone:
        try:
            pytz.timezone(body.timezone)
        except pytz.UnknownTimeZoneError:
            raise HTTPException(status_code=400, detail=f"Unknown timezone: {body.timezone}")

    updates = body.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(user, key, value)

    schedule_changed = any(k in updates for k in ("post_time_hour", "post_time_minute", "timezone"))
    if schedule_changed and user.scheduler_active:
        get_scheduler().register_user_job(
            user_id=str(user.id),
            hour=user.post_time_hour,
            minute=user.post_time_minute,
            timezone=user.timezone,
        )

    ig = await _instagram_for_user(db, user.id)
    return _profile_response(user, ig)


@router.post("/me/scheduler")
async def toggle_scheduler(
    body: SchedulerToggleRequest,
    user: UserProfile = Depends(get_current_user),
):
    if body.active and not user.whatsapp_number:
        raise HTTPException(
            status_code=400,
            detail="Add your WhatsApp number before activating the scheduler.",
        )

    user.scheduler_active = body.active

    if body.active:
        get_scheduler().register_user_job(
            user_id=str(user.id),
            hour=user.post_time_hour,
            minute=user.post_time_minute,
            timezone=user.timezone,
        )
    else:
        get_scheduler().remove_user_job(str(user.id))

    return {"scheduler_active": body.active}
