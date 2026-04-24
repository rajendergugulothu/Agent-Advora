"""
Draft management endpoints.

- List drafts with pagination
- Get a single draft
- Manually trigger content generation
- View analytics per draft
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AsyncClient

from app.api.v1.deps import get_current_user
from app.db.database import get_db
from app.db.models import Draft, DraftStatus, PostAnalytics, PostResult, UserProfile
from app.services.scheduler import get_scheduler

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class AnalyticsResponse(BaseModel):
    fetch_stage: str
    fetched_at: datetime
    impressions: int
    reach: int
    likes: int
    comments: int
    shares: int
    saves: int
    engagement_rate: float | None


class PostResultResponse(BaseModel):
    instagram_post_id: str
    instagram_url: str | None
    image_url: str | None
    image_urls: list[str]
    posted_at: datetime
    analytics: list[AnalyticsResponse]


class DraftResponse(BaseModel):
    id: str
    theme: str
    audience: str
    hook: str
    caption: str
    hashtags: str
    post_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    post_result: PostResultResponse | None


class DraftListResponse(BaseModel):
    items: list[DraftResponse]
    total: int
    page: int
    page_size: int


class TriggerRequest(BaseModel):
    theme: str | None = None
    audience: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=DraftListResponse)
async def list_drafts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: DraftStatus | None = None,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    query = select(Draft).where(Draft.user_id == user.id)
    if status:
        query = query.where(Draft.status == status)
    query = query.order_by(desc(Draft.created_at)).offset(offset).limit(page_size)

    result = await db.execute(query)
    drafts = result.scalars().all()

    count_query = select(Draft).where(Draft.user_id == user.id)
    if status:
        count_query = count_query.where(Draft.status == status)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    items = []
    for draft in drafts:
        post_result = await _load_post_result(db, draft.id)
        items.append(_draft_to_response(draft, post_result))

    return DraftListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: str,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    draft = await db.get(Draft, uuid.UUID(draft_id))
    if not draft or draft.user_id != user.id:
        raise HTTPException(status_code=404, detail="Draft not found")

    post_result = await _load_post_result(db, draft.id)
    return _draft_to_response(draft, post_result)


@router.post("/trigger", status_code=202)
async def trigger_generation(
    body: TriggerRequest,
    user: UserProfile = Depends(get_current_user),
):
    """
    Manually trigger content generation for this user.
    Returns immediately — generation happens in the background.
    """
    import asyncio
    asyncio.create_task(get_scheduler()._daily_generate_and_send(str(user.id)))
    return {"status": "generation_triggered"}


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _load_post_result(db: AsyncSession, draft_id: uuid.UUID) -> PostResult | None:
    result = await db.execute(
        select(PostResult).where(PostResult.draft_id == draft_id)
    )
    post_result = result.scalar_one_or_none()
    if not post_result:
        return None

    analytics_result = await db.execute(
        select(PostAnalytics).where(PostAnalytics.post_result_id == post_result.id)
    )
    post_result._analytics = analytics_result.scalars().all()
    return post_result


def _draft_to_response(draft: Draft, post_result: PostResult | None) -> DraftResponse:
    pr = None
    if post_result:
        analytics = [
            AnalyticsResponse(
                fetch_stage=a.fetch_stage,
                fetched_at=a.fetched_at,
                impressions=a.impressions,
                reach=a.reach,
                likes=a.likes,
                comments=a.comments,
                shares=a.shares,
                saves=a.saves,
                engagement_rate=float(a.engagement_rate) if a.engagement_rate else None,
            )
            for a in getattr(post_result, "_analytics", [])
        ]
        pr = PostResultResponse(
            instagram_post_id=post_result.instagram_post_id,
            instagram_url=post_result.instagram_url,
            image_url=post_result.image_url,
            image_urls=post_result.image_urls or [],
            posted_at=post_result.posted_at,
            analytics=analytics,
        )

    return DraftResponse(
        id=str(draft.id),
        theme=draft.theme,
        audience=draft.audience,
        hook=draft.hook,
        caption=draft.caption,
        hashtags=draft.hashtags,
        post_type=draft.post_type,
        status=draft.status,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
        post_result=pr,
    )
