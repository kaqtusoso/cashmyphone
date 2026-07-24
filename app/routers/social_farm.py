from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..social_farm.models import SocialFarmSlide
from ..social_farm.service import (
    generate_post,
    create_post_export,
    get_post,
    list_posts,
    refresh_post_copy,
    regenerate_slide_background,
    scheduled_generation,
    serialize_post,
    update_slide,
)
from ..social_farm.topics import TOPICS

router = APIRouter(prefix="/api/social-farm", tags=["social-farm"])


def require_admin_key(x_api_key: Optional[str] = Header(None)) -> None:
    if not x_api_key or x_api_key != settings.scrape_api_key:
        raise HTTPException(status_code=401, detail="Ogiltig API-nyckel")


class GenerateRequest(BaseModel):
    topic_key: Optional[str] = None
    force_local_images: bool = False


class SlideUpdateRequest(BaseModel):
    heading: str = Field(min_length=1, max_length=160)
    body: list[str] = Field(default_factory=list, max_length=2)


class RegenerateRequest(BaseModel):
    force_local: bool = False


@router.get("/topics", dependencies=[Depends(require_admin_key)])
async def topics():
    return [
        {
            "key": topic.key,
            "category": topic.category,
            "title": topic.title,
        }
        for topic in TOPICS
    ]


@router.get("/posts", dependencies=[Depends(require_admin_key)])
async def posts(
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    rows = await list_posts(db, limit=limit)
    return {"posts": [await serialize_post(db, row) for row in rows]}


@router.get("/posts/{post_id}", dependencies=[Depends(require_admin_key)])
async def post_detail(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Utkastet hittades inte")
    return await serialize_post(db, post)


@router.post("/generate", dependencies=[Depends(require_admin_key)])
async def generate(
    request: GenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        post = await generate_post(
            db,
            trigger="manual",
            topic_key=request.topic_key,
            force_local_images=request.force_local_images,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await serialize_post(db, post)


@router.post("/schedule/run", dependencies=[Depends(require_admin_key)])
async def run_schedule(db: AsyncSession = Depends(get_db)):
    post = await scheduled_generation(db)
    if not post:
        return {"created": False, "message": "Nästa 48-timmarsfönster har inte öppnat ännu"}
    return {"created": True, "post": await serialize_post(db, post)}


@router.post("/posts/{post_id}/approve", dependencies=[Depends(require_admin_key)])
async def approve(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Utkastet hittades inte")
    post.status = "approved"
    post.approved_at = datetime.utcnow()
    await db.commit()
    await db.refresh(post)
    return await serialize_post(db, post)


@router.post("/posts/{post_id}/refresh-copy", dependencies=[Depends(require_admin_key)])
async def refresh_copy(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Utkastet hittades inte")
    try:
        await refresh_post_copy(db, post=post)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return await serialize_post(db, post)


@router.get("/posts/{post_id}/export", dependencies=[Depends(require_admin_key)])
async def export_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Utkastet hittades inte")
    export_path = await create_post_export(db, post)
    return FileResponse(
        path=export_path,
        filename=export_path.name,
        media_type="application/zip",
    )


@router.post(
    "/posts/{post_id}/slides/{slide_id}",
    dependencies=[Depends(require_admin_key)],
)
async def edit_slide(
    post_id: int,
    slide_id: int,
    request: SlideUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    post = await get_post(db, post_id)
    slide = await db.get(SocialFarmSlide, slide_id)
    if not post or not slide or slide.post_id != post.id:
        raise HTTPException(status_code=404, detail="Sliden hittades inte")
    if slide.kind == "cover" and request.body:
        raise HTTPException(status_code=400, detail="Cover-sliden ska inte ha brödtext")
    slide = await update_slide(
        db,
        post=post,
        slide=slide,
        heading=request.heading,
        body=request.body,
    )
    return await serialize_post(db, post)


@router.post(
    "/posts/{post_id}/slides/{slide_id}/regenerate",
    dependencies=[Depends(require_admin_key)],
)
async def regenerate_slide(
    post_id: int,
    slide_id: int,
    request: RegenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    post = await get_post(db, post_id)
    slide = await db.get(SocialFarmSlide, slide_id)
    if not post or not slide or slide.post_id != post.id:
        raise HTTPException(status_code=404, detail="Sliden hittades inte")
    await regenerate_slide_background(
        db,
        post=post,
        slide=slide,
        force_local=request.force_local,
    )
    return await serialize_post(db, post)
