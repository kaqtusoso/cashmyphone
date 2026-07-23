from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SocialFarmPost(Base):
    """Ett komplett sexslides-utkast för TikTok/Instagram."""

    __tablename__ = "social_farm_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    topic_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    caption: Mapped[str] = mapped_column(Text, nullable=False)
    cta: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="needs_review", nullable=False)
    copy_provider: Mapped[str] = mapped_column(String(30), default="curated", nullable=False)
    fact_pack_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    quality_warnings_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_social_farm_posts_status_created", "status", "created_at"),
    )


class SocialFarmSlide(Base):
    """En renderbar slide som tillhör ett socialt inlägg."""

    __tablename__ = "social_farm_slides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("social_farm_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    heading: Mapped[str] = mapped_column(Text, nullable=False)
    body_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    scene_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    visual_type: Mapped[str] = mapped_column(String(30), default="object", nullable=False)
    background_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    render_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_provider: Mapped[str] = mapped_column(String(30), default="local", nullable=False)
    quality_warnings_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("ix_social_farm_slide_post_position", "post_id", "position", unique=True),
    )


class SocialFarmGenerationRun(Base):
    """Idempotens- och fellogg för manuella och schemalagda körningar."""

    __tablename__ = "social_farm_generation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slot_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    trigger: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="running", nullable=False)
    post_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("social_farm_posts.id"),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
