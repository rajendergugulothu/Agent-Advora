"""
Scheduler service.

Manages per-user APScheduler jobs for:
1. Daily content generation + WhatsApp draft delivery
2. Analytics metric fetching at 24h, 72h, and 7d after posting
3. Instagram token refresh (runs weekly, refreshes tokens expiring within 15 days)

Each user gets their own isolated job that fires at their configured time and timezone.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AsyncClient, acreate_client

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import decrypt_token, encrypt_token
from app.db.database import AsyncSessionFactory
from app.db.models import (
    AnalyticsJob,
    AnalyticsStage,
    Draft,
    DraftStatus,
    InstagramConnection,
    JobStatus,
    PostAnalytics,
    PostResult,
    UserProfile,
)
from app.services import content, image, whatsapp
from app.services.instagram import (
    fetch_post_insights,
    refresh_long_lived_token,
    token_expires_at,
)

log = get_logger(__name__)
settings = get_settings()

_ANALYTICS_DELAYS: dict[AnalyticsStage, timedelta] = {
    AnalyticsStage.h24: timedelta(hours=24),
    AnalyticsStage.h72: timedelta(hours=72),
    AnalyticsStage.d7: timedelta(days=7),
}


class SchedulerService:
    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()
        self._supabase: AsyncClient | None = None

    async def start(self) -> None:
        self._supabase = await acreate_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
        self._scheduler.start()
        await self._register_all_user_jobs()
        self._scheduler.add_job(
            self._run_due_analytics_jobs,
            "interval",
            minutes=15,
            id="analytics_runner",
            replace_existing=True,
        )
        self._scheduler.add_job(
            self._refresh_expiring_tokens,
            CronTrigger(hour=3, minute=0),        # runs at 3 AM UTC daily
            id="token_refresh",
            replace_existing=True,
        )
        log.info("scheduler_started")

    async def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    # ── User job registration ─────────────────────────────────────────────────

    async def _register_all_user_jobs(self) -> None:
        """Load all active users and register their daily jobs."""
        async with AsyncSessionFactory() as db:
            result = await db.execute(
                select(UserProfile).where(
                    UserProfile.is_active == True,
                    UserProfile.scheduler_active == True,
                )
            )
            users = result.scalars().all()

        for user in users:
            self.register_user_job(
                user_id=str(user.id),
                hour=user.post_time_hour,
                minute=user.post_time_minute,
                timezone=user.timezone,
            )
        log.info("user_jobs_registered", count=len(users))

    def register_user_job(
        self,
        user_id: str,
        hour: int,
        minute: int,
        timezone: str,
    ) -> None:
        """Register or replace a user's daily content generation job."""
        job_id = f"daily_post_{user_id}"
        self._scheduler.add_job(
            self._daily_generate_and_send,
            CronTrigger(hour=hour, minute=minute, timezone=timezone),
            id=job_id,
            args=[user_id],
            replace_existing=True,
            misfire_grace_time=3600,    # allow up to 1h late firing on missed jobs
        )
        log.info("user_job_registered", user_id=user_id, hour=hour, minute=minute, timezone=timezone)

    def remove_user_job(self, user_id: str) -> None:
        job_id = f"daily_post_{user_id}"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
            log.info("user_job_removed", user_id=user_id)

    # ── Daily content job ─────────────────────────────────────────────────────

    async def _daily_generate_and_send(self, user_id: str) -> None:
        """Generate a draft and send it to the user's WhatsApp."""
        log.info("daily_job_start", user_id=user_id)
        supabase = self._supabase

        async with AsyncSessionFactory() as db:
            user = await db.get(UserProfile, uuid.UUID(user_id))
            if not user or not user.is_active:
                log.warning("daily_job_skipped_inactive", user_id=user_id)
                return

            if not user.whatsapp_number or not user.whatsapp_access_token:
                log.warning("daily_job_skipped_no_whatsapp", user_id=user_id)
                return

            recipient = user.whatsapp_number

        try:
            post = await content.generate_post(supabase=supabase, user_id=user_id)
        except Exception as exc:
            log.error("content_generation_failed", user_id=user_id, error=str(exc))
            await whatsapp.send_text_message(
                f"Content generation failed: {exc}", recipient
            )
            return

        async with AsyncSessionFactory() as db:
            draft = Draft(
                user_id=uuid.UUID(user_id),
                theme=post["theme"],
                audience=post["audience"],
                hook=post["hook"],
                caption=post["caption"],
                hashtags=post["hashtags"],
                image_concept=post.get("image_concept"),
                post_type=post["post_type"],
                carousel_slides=post.get("carousel_slides", []),
                status=DraftStatus.pending,
            )
            db.add(draft)
            await db.flush()
            draft_id = str(draft.id)

        message_id = await whatsapp.send_draft_for_approval(
            post=post,
            draft_id=draft_id,
            recipient_number=recipient,
        )

        if message_id:
            async with AsyncSessionFactory() as db:
                await db.execute(
                    update(Draft)
                    .where(Draft.id == uuid.UUID(draft_id))
                    .values(whatsapp_message_id=message_id)
                )
            log.info("daily_job_done", user_id=user_id, draft_id=draft_id)
        else:
            log.error("whatsapp_delivery_failed", user_id=user_id, draft_id=draft_id)

    # ── Approval handling ─────────────────────────────────────────────────────

    async def handle_approve(self, draft_id: str, user_id: str) -> None:
        """Called by the webhook handler when a user taps Approve."""
        async with AsyncSessionFactory() as db:
            draft = await db.get(Draft, uuid.UUID(draft_id))
            if not draft or draft.status != DraftStatus.pending:
                log.warning("approve_skipped_not_pending", draft_id=draft_id)
                return

            user = await db.get(UserProfile, uuid.UUID(user_id))
            ig_result = await db.execute(
                select(InstagramConnection).where(
                    InstagramConnection.user_id == uuid.UUID(user_id),
                    InstagramConnection.is_active == True,
                )
            )
            ig = ig_result.scalar_one_or_none()

            if not ig or not ig.is_active:
                await whatsapp.send_text_message(
                    "Instagram is not connected. Please connect your account in the dashboard.",
                    user.whatsapp_number,
                )
                return

            await db.execute(
                update(Draft)
                .where(Draft.id == uuid.UUID(draft_id))
                .values(status=DraftStatus.approved)
            )

        await whatsapp.send_text_message(
            f"Draft approved. Generating image assets now...\n(~15-30 seconds)",
            user.whatsapp_number,
        )

        post = {
            "theme": draft.theme,
            "caption": draft.caption,
            "hashtags": draft.hashtags,
            "image_concept": draft.image_concept,
            "post_type": draft.post_type,
            "carousel_slides": draft.carousel_slides,
        }

        account_id = decrypt_token(ig.instagram_account_id)
        access_token = decrypt_token(ig.instagram_access_token)

        result = await self._build_and_publish(
            draft_id=draft_id,
            post=post,
            account_id=account_id,
            access_token=access_token,
        )

        if result["success"]:
            async with AsyncSessionFactory() as db:
                post_result = PostResult(
                    draft_id=uuid.UUID(draft_id),
                    user_id=uuid.UUID(user_id),
                    instagram_post_id=result["post_id"],
                    instagram_url=result.get("instagram_url"),
                    image_url=result.get("image_url"),
                    image_urls=result.get("image_urls", []),
                )
                db.add(post_result)
                await db.flush()
                post_result_id = str(post_result.id)

                await db.execute(
                    update(Draft)
                    .where(Draft.id == uuid.UUID(draft_id))
                    .values(status=DraftStatus.posted)
                )

            await self._schedule_analytics_jobs(
                post_result_id=post_result_id,
                user_id=user_id,
                draft_id=draft_id,
                instagram_post_id=result["post_id"],
            )

            msg = "Posted to Instagram successfully!"
            if result.get("instagram_url"):
                msg += f"\n{result['instagram_url']}"
            await whatsapp.send_text_message(msg, user.whatsapp_number)
            log.info("post_approved_and_published", draft_id=draft_id, post_id=result["post_id"])

        else:
            async with AsyncSessionFactory() as db:
                await db.execute(
                    update(Draft)
                    .where(Draft.id == uuid.UUID(draft_id))
                    .values(
                        status=DraftStatus.post_failed,
                        status_reason=result.get("error"),
                    )
                )
            await whatsapp.send_text_message(
                f"Posting failed: {result.get('error', 'Unknown error')}",
                user.whatsapp_number,
            )

    async def handle_regenerate(self, draft_id: str, user_id: str) -> None:
        """Called by the webhook handler when a user taps Regenerate."""
        async with AsyncSessionFactory() as db:
            await db.execute(
                update(Draft)
                .where(Draft.id == uuid.UUID(draft_id))
                .values(status=DraftStatus.rejected)
            )
            user = await db.get(UserProfile, uuid.UUID(user_id))

        await whatsapp.send_text_message(
            "Regenerating a new draft for you...", user.whatsapp_number
        )
        await self._daily_generate_and_send(user_id)

    # ── Image generation + posting ────────────────────────────────────────────

    async def _build_and_publish(
        self,
        draft_id: str,
        post: dict,
        account_id: str,
        access_token: str,
    ) -> dict:
        from app.services.instagram import post_single_image, post_carousel

        if post["post_type"] == "carousel":
            slides = post.get("carousel_slides") or []
            image_urls = await image.generate_carousel_images(
                slides=slides, theme=post["theme"], draft_id=draft_id
            )
            if not image_urls:
                return {"success": False, "error": "Carousel image generation failed."}

            result = await post_carousel(
                image_urls=image_urls,
                caption=post["caption"],
                hashtags=post["hashtags"],
                account_id=account_id,
                access_token=access_token,
            )
            result["image_urls"] = image_urls
            return result

        image_url = await image.generate_single_image(
            image_concept=post["image_concept"],
            theme=post["theme"],
            draft_id=draft_id,
        )
        if not image_url:
            return {"success": False, "error": "Image generation failed."}

        result = await post_single_image(
            image_url=image_url,
            caption=post["caption"],
            hashtags=post["hashtags"],
            account_id=account_id,
            access_token=access_token,
        )
        result["image_url"] = image_url
        return result

    # ── Analytics job scheduling ──────────────────────────────────────────────

    async def _schedule_analytics_jobs(
        self,
        post_result_id: str,
        user_id: str,
        draft_id: str,
        instagram_post_id: str,
    ) -> None:
        """Create DB records and APScheduler one-shot jobs for 24h/72h/7d fetches."""
        now = datetime.now(timezone.utc)

        async with AsyncSessionFactory() as db:
            for stage, delay in _ANALYTICS_DELAYS.items():
                fire_at = now + delay
                job = AnalyticsJob(
                    post_result_id=uuid.UUID(post_result_id),
                    user_id=uuid.UUID(user_id),
                    fetch_stage=stage,
                    scheduled_for=fire_at,
                )
                db.add(job)

        log.info("analytics_jobs_scheduled", post_result_id=post_result_id)

    async def _run_due_analytics_jobs(self) -> None:
        """Poll for due analytics jobs and fetch Instagram Insights."""
        async with AsyncSessionFactory() as db:
            result = await db.execute(
                select(AnalyticsJob).where(
                    AnalyticsJob.status == JobStatus.scheduled,
                    AnalyticsJob.scheduled_for <= datetime.now(timezone.utc),
                )
            )
            jobs = result.scalars().all()

        for job in jobs:
            await self._execute_analytics_job(job.id)

    async def _execute_analytics_job(self, job_id: uuid.UUID) -> None:
        async with AsyncSessionFactory() as db:
            job = await db.get(AnalyticsJob, job_id)
            if not job or job.status != JobStatus.scheduled:
                return

            post_result = await db.get(PostResult, job.post_result_id)
            ig_conn = await db.execute(
                select(InstagramConnection).where(
                    InstagramConnection.user_id == job.user_id,
                    InstagramConnection.is_active == True,
                )
            )
            ig = ig_conn.scalar_one_or_none()

            if not ig:
                await db.execute(
                    update(AnalyticsJob)
                    .where(AnalyticsJob.id == job_id)
                    .values(status=JobStatus.failed, error="No active Instagram connection")
                )
                return

            access_token = decrypt_token(ig.instagram_access_token)

        metrics = await fetch_post_insights(
            post_id=post_result.instagram_post_id,
            access_token=access_token,
        )

        async with AsyncSessionFactory() as db:
            if metrics:
                analytics = PostAnalytics(
                    post_result_id=job.post_result_id,
                    user_id=job.user_id,
                    draft_id=post_result.draft_id,
                    instagram_post_id=post_result.instagram_post_id,
                    fetch_stage=job.fetch_stage,
                    **metrics,
                )
                db.add(analytics)
                await db.execute(
                    update(AnalyticsJob)
                    .where(AnalyticsJob.id == job_id)
                    .values(
                        status=JobStatus.completed,
                        attempted_at=datetime.now(timezone.utc),
                    )
                )
                log.info(
                    "analytics_fetched",
                    post_result_id=str(job.post_result_id),
                    stage=job.fetch_stage,
                    engagement_rate=metrics,
                )
            else:
                await db.execute(
                    update(AnalyticsJob)
                    .where(AnalyticsJob.id == job_id)
                    .values(
                        status=JobStatus.failed,
                        attempted_at=datetime.now(timezone.utc),
                        error="Insights API returned no data",
                    )
                )

    # ── Token refresh ─────────────────────────────────────────────────────────

    async def _refresh_expiring_tokens(self) -> None:
        """Refresh Instagram tokens expiring within 15 days."""
        threshold = datetime.now(timezone.utc) + timedelta(days=15)

        async with AsyncSessionFactory() as db:
            result = await db.execute(
                select(InstagramConnection).where(
                    InstagramConnection.is_active == True,
                    InstagramConnection.token_expires_at <= threshold,
                )
            )
            connections = result.scalars().all()

        for conn in connections:
            try:
                current_token = decrypt_token(conn.instagram_access_token)
                refreshed = await refresh_long_lived_token(current_token)
                new_token = refreshed["access_token"]
                new_expiry = token_expires_at(refreshed.get("expires_in", 5184000))

                async with AsyncSessionFactory() as db:
                    await db.execute(
                        update(InstagramConnection)
                        .where(InstagramConnection.id == conn.id)
                        .values(
                            instagram_access_token=encrypt_token(new_token),
                            token_expires_at=new_expiry,
                            last_refreshed_at=datetime.now(timezone.utc),
                        )
                    )
                log.info("token_refreshed", connection_id=str(conn.id), new_expiry=new_expiry)

            except Exception as exc:
                log.error("token_refresh_failed", connection_id=str(conn.id), error=str(exc))


# ── Singleton ─────────────────────────────────────────────────────────────────
# Route handlers and main.py import get_scheduler() instead of importing
# from app.main — this eliminates circular imports entirely.

_instance: SchedulerService | None = None


def get_scheduler() -> SchedulerService:
    global _instance
    if _instance is None:
        _instance = SchedulerService()
    return _instance
