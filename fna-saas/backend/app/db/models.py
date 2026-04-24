"""
SQLAlchemy ORM models.
These mirror the Supabase schema defined in the migrations.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

# ── Enums ─────────────────────────────────────────────────────────────────────

import enum


class DraftStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    posting = "posting"
    posted = "posted"
    image_failed = "image_failed"
    post_failed = "post_failed"


class PostType(str, enum.Enum):
    single_image = "single_image"
    carousel = "carousel"


class AudienceType(str, enum.Enum):
    client = "client"
    advisor = "advisor"


class AnalyticsStage(str, enum.Enum):
    h24 = "24h"
    h72 = "72h"
    d7 = "7d"


class JobStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    failed = "failed"


# ── Models ────────────────────────────────────────────────────────────────────

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    company_name: Mapped[str | None] = mapped_column(Text)
    whatsapp_number: Mapped[str | None] = mapped_column(Text)
    whatsapp_phone_number_id: Mapped[str | None] = mapped_column(Text)    # encrypted
    whatsapp_access_token: Mapped[str | None] = mapped_column(Text)       # encrypted
    post_time_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=9)
    post_time_minute: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    timezone: Mapped[str] = mapped_column(Text, nullable=False, default="America/Chicago")
    scheduler_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    drafts: Mapped[list["Draft"]] = relationship("Draft", back_populates="user_profile", lazy="noload")
    instagram_connection: Mapped["InstagramConnection | None"] = relationship(
        "InstagramConnection", back_populates="user_profile", uselist=False, lazy="noload"
    )


class InstagramConnection(Base):
    __tablename__ = "instagram_connections"
    __table_args__ = (UniqueConstraint("user_id", name="uq_instagram_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    instagram_account_id: Mapped[str] = mapped_column(Text, nullable=False)    # encrypted
    instagram_access_token: Mapped[str] = mapped_column(Text, nullable=False)  # encrypted
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    username: Mapped[str | None] = mapped_column(Text)
    profile_picture_url: Mapped[str | None] = mapped_column(Text)
    page_id: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user_profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="instagram_connection")


class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    theme: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[AudienceType] = mapped_column(Enum(AudienceType, name="audience_type"), nullable=False)
    hook: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[str] = mapped_column(Text, nullable=False)
    image_concept: Mapped[str | None] = mapped_column(Text)
    post_type: Mapped[PostType] = mapped_column(Enum(PostType, name="post_type"), nullable=False, default=PostType.single_image)
    carousel_slides: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[DraftStatus] = mapped_column(Enum(DraftStatus, name="draft_status"), nullable=False, default=DraftStatus.pending)
    whatsapp_message_id: Mapped[str | None] = mapped_column(Text)
    status_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user_profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="drafts")
    post_result: Mapped["PostResult | None"] = relationship("PostResult", back_populates="draft", uselist=False, lazy="noload")


class PostResult(Base):
    __tablename__ = "post_results"
    __table_args__ = (UniqueConstraint("draft_id", name="uq_post_result_draft"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    draft_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    instagram_post_id: Mapped[str] = mapped_column(Text, nullable=False)
    instagram_url: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    image_urls: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    draft: Mapped["Draft"] = relationship("Draft", back_populates="post_result")
    analytics: Mapped[list["PostAnalytics"]] = relationship("PostAnalytics", back_populates="post_result", lazy="noload")
    analytics_jobs: Mapped[list["AnalyticsJob"]] = relationship("AnalyticsJob", back_populates="post_result", lazy="noload")


class PostAnalytics(Base):
    __tablename__ = "post_analytics"
    __table_args__ = (UniqueConstraint("post_result_id", "fetch_stage", name="uq_analytics_stage"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("post_results.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    draft_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("drafts.id", ondelete="CASCADE"), nullable=False)
    instagram_post_id: Mapped[str] = mapped_column(Text, nullable=False)
    fetch_stage: Mapped[AnalyticsStage] = mapped_column(Enum(AnalyticsStage, name="analytics_stage"), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reach: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shares: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    saves: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # engagement_rate is a generated column in Postgres; read-only in ORM
    engagement_rate: Mapped[float | None] = mapped_column(Numeric(6, 3))

    post_result: Mapped["PostResult"] = relationship("PostResult", back_populates="analytics")


class AnalyticsJob(Base):
    __tablename__ = "analytics_jobs"
    __table_args__ = (UniqueConstraint("post_result_id", "fetch_stage", name="uq_analytics_job"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("post_results.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="CASCADE"), nullable=False)
    fetch_stage: Mapped[AnalyticsStage] = mapped_column(Enum(AnalyticsStage, name="analytics_stage"), nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status"), nullable=False, default=JobStatus.scheduled)
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)

    post_result: Mapped["PostResult"] = relationship("PostResult", back_populates="analytics_jobs")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    signature_valid: Mapped[bool] = mapped_column(Boolean, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error: Mapped[str | None] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
