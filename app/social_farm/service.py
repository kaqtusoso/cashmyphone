from __future__ import annotations

import json
import logging
import re
import uuid
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import httpx
from sqlalchemy import desc, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import BuybackPrice
from .models import SocialFarmGenerationRun, SocialFarmPost, SocialFarmSlide
from .providers import ProviderUnavailable, generate_background, generate_copy
from .renderer import decode_body, render_slide, validate_copy
from .topics import TOPICS, SlideBlueprint, TopicBlueprint

logger = logging.getLogger(__name__)


def storage_root() -> Path:
    path = Path(settings.social_farm_storage_dir)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _slugify(value: str) -> str:
    normalized = value.lower()
    replacements = {"å": "a", "ä": "a", "ö": "o"}
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized[:90] or "televera-post"


async def build_fact_pack(db: AsyncSession) -> dict[str, Any]:
    result = await db.execute(
        select(
            func.count(distinct(BuybackPrice.retailer)),
            func.max(BuybackPrice.scraped_at),
        ).where(BuybackPrice.is_active == True)
    )
    retailer_count, latest_price_at = result.one()
    return {
        "brand": "Televera",
        "role": "Svensk jämförelsetjänst för bud på begagnade iPhones",
        "retailer_count_available": int(retailer_count or 0),
        "latest_price_at": latest_price_at.isoformat() if latest_price_at else None,
        "claim_rules": [
            "Säg jämför bud, inte garanterat högsta pris",
            "Televera är en jämförelsetjänst och köper inte mobilen",
            "Slutpriset fastställs efter uppköparens kontroll",
            "Använd inga konkreta prisbelopp utan daterad data för exakt skick",
        ],
    }


async def _select_topic(db: AsyncSession, requested_key: Optional[str]) -> TopicBlueprint:
    if requested_key:
        for topic in TOPICS:
            if topic.key == requested_key:
                return topic
        raise ValueError(f"Okänt ämne: {requested_key}")

    cutoff = datetime.utcnow() - timedelta(days=settings.social_farm_topic_cooldown_days)
    recent_result = await db.execute(
        select(SocialFarmPost.topic_key)
        .where(SocialFarmPost.created_at >= cutoff)
        .order_by(desc(SocialFarmPost.created_at))
    )
    recent = {row[0] for row in recent_result.all()}
    for topic in TOPICS:
        if topic.key not in recent:
            return topic

    least_recent_result = await db.execute(
        select(
            SocialFarmPost.topic_key,
            func.max(SocialFarmPost.created_at).label("last_used"),
        )
        .group_by(SocialFarmPost.topic_key)
        .order_by("last_used")
        .limit(1)
    )
    least_recent = least_recent_result.first()
    if least_recent:
        for topic in TOPICS:
            if topic.key == least_recent[0]:
                return topic
    return TOPICS[0]


def _copy_prompt(topic: TopicBlueprint, fact_pack: dict[str, Any]) -> str:
    example_slides = [
        {
            "heading": slide.heading,
            "body": list(slide.body),
            "scene": slide.scene,
            "visual_type": slide.visual_type,
        }
        for slide in topic.slides
    ]
    return f"""
Du är Televeras svenska short-form-redaktör.

Skapa ett TikTok-bildspel med exakt sex slides: en cover och fem innehållsslides.
Utgå från ämnet och dramaturgin nedan men skriv en ny, naturlig svensk version.

Hårda regler:
- Televera är en jämförelsetjänst, inte köparen.
- Skriv "jämför bud", aldrig "garanterat högsta pris".
- Hitta inte på kundhistorier, prisbelopp, resultat eller tidsvinster.
- Skriv som en riktig svensk person som berättar för en kompis: kort, konkret och vardagligt.
- Undvik abstrakta AI-formuleringar som "gav mig överblick", "fick ett sammanhang",
  "det jag egentligen sparade", "helheten", "i lugn och ro" och "utan stress".
- Exakt en av de fem innehållsslidesen ska nämna Televera naturligt och förklara
  nyttan: att flera uppköpares bud kan jämföras på samma ställe.
- Övriga fyra innehållsslides får inte nämna Televera.
- CTA:n ska innehålla televera.se och vara konkret och lågmäld. Gör tydligt att
  läsaren kan jämföra utan att lova att sälja.
- Cover: högst 72 tecken.
- Varje innehållsrubrik: högst 58 tecken.
- Varje innehållsslide har exakt två textblock, högst 105 tecken vardera.
- Högst två slides får ha visual_type "person_far".
- Använd aldrig visual_type "person_interaction".
- Svara med endast giltig JSON, inga kodstaket.

JSON-format:
{{
  "title": "...",
  "caption": "...",
  "cta": "...",
  "slides": [
    {{
      "heading": "...",
      "body": ["...", "..."],
      "scene": "...",
      "visual_type": "object|room|person_far|interface"
    }}
  ]
}}

Ämne: {topic.title}
Kategori: {topic.category}
Fact pack: {json.dumps(fact_pack, ensure_ascii=False)}
Referensdramaturgi: {json.dumps(example_slides, ensure_ascii=False)}
""".strip()


def _validate_generated_copy(payload: dict[str, Any], topic: TopicBlueprint) -> dict[str, Any]:
    slides = payload.get("slides")
    if not isinstance(slides, list) or len(slides) != 5:
        raise ValueError("Copy-svaret måste innehålla exakt fem innehållsslides")
    title = str(payload.get("title") or topic.title).strip()
    if validate_copy("cover", title, []):
        raise ValueError("Cover-texten klarar inte längdkraven")
    normalized_slides: list[dict[str, Any]] = []
    person_count = 0
    allowed_visuals = {"object", "room", "person_far", "interface"}
    televera_slide_count = 0
    banned_phrases = (
        "gav mig överblick",
        "fick ett sammanhang",
        "det jag egentligen sparade",
        "helhetsbedömningen",
        "i lugn och ro",
        "utan stress",
    )
    for index, slide in enumerate(slides):
        heading = str(slide.get("heading", "")).strip()
        body = slide.get("body")
        scene = str(slide.get("scene", "")).strip()
        visual_type = str(slide.get("visual_type", "object")).strip()
        if not heading or not scene or not isinstance(body, list) or len(body) != 2:
            raise ValueError(f"Ogiltig struktur på slide {index + 1}")
        normalized_body = [str(value).strip() for value in body]
        if validate_copy("body", heading, normalized_body):
            raise ValueError(f"Slide {index + 1} klarar inte längdkraven")
        if visual_type not in allowed_visuals:
            visual_type = "object"
        if visual_type == "person_far":
            person_count += 1
            if person_count > 2:
                visual_type = "room"
        slide_text = " ".join([heading, *normalized_body]).lower()
        if any(phrase in slide_text for phrase in banned_phrases):
            raise ValueError(f"Slide {index + 1} innehåller AI-klingande standardspråk")
        if "televera" in slide_text:
            televera_slide_count += 1
        normalized_slides.append(
            {
                "heading": heading,
                "body": normalized_body,
                "scene": scene,
                "visual_type": visual_type,
            }
        )
    if televera_slide_count != 1:
        raise ValueError("Exakt en innehållsslide måste nämna Televera")
    cta = str(payload.get("cta") or topic.cta).strip()
    if "televera.se" not in cta.lower():
        raise ValueError("CTA:n måste innehålla televera.se")
    return {
        "title": title,
        "caption": str(payload.get("caption") or topic.caption).strip(),
        "cta": cta,
        "slides": normalized_slides,
    }


async def _content_for_topic(
    topic: TopicBlueprint,
    fact_pack: dict[str, Any],
) -> tuple[dict[str, Any], str, list[str]]:
    warnings: list[str] = []
    if settings.social_farm_copy_provider == "openai":
        try:
            payload = await generate_copy(_copy_prompt(topic, fact_pack))
            return _validate_generated_copy(payload, topic), "openai", warnings
        except (ProviderUnavailable, httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError) as exc:
            logger.warning("Copy-provider misslyckades; använder kuraterad fallback: %s", exc)
            warnings.append(f"Copy-fallback användes: {exc}")

    content = {
        "title": topic.title,
        "caption": topic.caption,
        "cta": topic.cta,
        "slides": [
            {
                "heading": slide.heading,
                "body": list(slide.body),
                "scene": slide.scene,
                "visual_type": slide.visual_type,
            }
            for slide in topic.slides
        ],
    }
    return content, "curated", warnings

def _image_prompt(scene: str, visual_type: str) -> str:
    person_rule = (
        "One adult may appear from behind or at a distance. Keep the face obscured "
        "and hands hidden or relaxed, never gripping or intersecting an object."
        if visual_type == "person_far"
        else "No people and no hands in the frame."
    )
    return f"""
Create a text-free, photorealistic vertical lifestyle photograph for a Swedish
TikTok photo slideshow. Scene: {scene}.

It should feel like a believable personal camera-roll photo: candid, slightly
imperfect framing, real fabric/wood/glass texture, subtle analog grain and
natural available light. Use an attainable Scandinavian apartment, café,
garden or coastal setting — visually rich and lived-in, never a studio set.
Books, flowers, bedding, breakfast, drinks and an older phone may appear as
ordinary details rather than hero products.

Use full-bleed 9:16 composition. Keep the scene visually interesting throughout,
with main objects mostly in the lower half and a somewhat calmer upper-middle
area where white typography can later sit; do not make that area blank or turn
it into a gradient. {person_rule}

The image must contain no text, readable writing, logo, watermark or readable
interface. Avoid isolated product renders, glossy advertising, luxury villas,
influencer posing, sterile minimalism, CGI sheen, malformed phones, extra
fingers, fused objects and complicated hand-object interactions.
""".strip()


async def _maybe_generate_background(
    *,
    prompt: str,
    output_path: Path,
    should_generate: bool,
) -> tuple[Optional[str], str, list[str]]:
    warnings: list[str] = []
    if not should_generate or settings.social_farm_image_provider != "openai":
        return None, "local", warnings
    try:
        await generate_background(prompt, output_path)
        return str(output_path), "openai", warnings
    except (ProviderUnavailable, httpx.HTTPError, KeyError, ValueError) as exc:
        logger.warning("Bildprovider misslyckades; använder lokal fallback: %s", exc)
        warnings.append(f"Lokal bildfallback användes: {exc}")
        return None, "local", warnings


async def generate_post(
    db: AsyncSession,
    *,
    trigger: str = "manual",
    topic_key: Optional[str] = None,
    slot_key: Optional[str] = None,
    force_local_images: bool = False,
) -> SocialFarmPost:
    slot = slot_key or f"manual-{uuid.uuid4().hex}"
    existing_run = await db.scalar(
        select(SocialFarmGenerationRun).where(SocialFarmGenerationRun.slot_key == slot)
    )
    if existing_run and existing_run.post_id:
        existing_post = await db.get(SocialFarmPost, existing_run.post_id)
        if existing_post:
            return existing_post
    if existing_run:
        raise RuntimeError(f"Generation pågår eller har redan misslyckats för {slot}")

    run = SocialFarmGenerationRun(slot_key=slot, trigger=trigger, status="running")
    db.add(run)
    await db.commit()
    await db.refresh(run)

    try:
        topic = await _select_topic(db, topic_key)
        fact_pack = await build_fact_pack(db)
        content, copy_provider, post_warnings = await _content_for_topic(topic, fact_pack)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        slug = f"{timestamp}-{_slugify(content['title'])}"
        post = SocialFarmPost(
            slug=slug,
            topic_key=topic.key,
            category=topic.category,
            title=content["title"],
            caption=content["caption"],
            cta=content["cta"],
            status="needs_review",
            copy_provider=copy_provider,
            fact_pack_json=json.dumps(fact_pack, ensure_ascii=False),
            quality_warnings_json="[]",
        )
        db.add(post)
        await db.flush()

        slide_payloads = [
            {
                "kind": "cover",
                "heading": content["title"],
                "body": [],
                "scene": "svensk vardagsmiljö med en äldre smartphone och gott om negativt utrymme",
                "visual_type": "object",
            },
            *[
                {
                    "kind": "body",
                    **slide,
                }
                for slide in content["slides"]
            ],
        ]

        post_dir = storage_root() / "posts" / slug
        image_budget = (
            0
            if force_local_images
            else max(0, min(6, settings.social_farm_generated_images_per_post))
        )
        for position, payload in enumerate(slide_payloads):
            raw_background = post_dir / f"background-{position + 1:02d}.jpg"
            background_path, image_provider, image_warnings = await _maybe_generate_background(
                prompt=_image_prompt(payload["scene"], payload["visual_type"]),
                output_path=raw_background,
                should_generate=position < image_budget,
            )
            output_path = post_dir / f"slide-{position + 1:02d}.png"
            copy_warnings = validate_copy(
                payload["kind"],
                payload["heading"],
                payload["body"],
            )
            render_warnings = render_slide(
                output_path=output_path,
                position=position,
                kind=payload["kind"],
                heading=payload["heading"],
                body=payload["body"],
                visual_type=payload["visual_type"],
                background_path=background_path,
            )
            warnings = copy_warnings + image_warnings + render_warnings
            post_warnings.extend(warnings)
            db.add(
                SocialFarmSlide(
                    post_id=post.id,
                    position=position,
                    kind=payload["kind"],
                    heading=payload["heading"],
                    body_json=json.dumps(payload["body"], ensure_ascii=False),
                    scene_prompt=payload["scene"],
                    visual_type=payload["visual_type"],
                    background_path=background_path,
                    render_path=str(output_path),
                    image_provider=image_provider,
                    quality_warnings_json=json.dumps(warnings, ensure_ascii=False),
                )
            )

        post.quality_warnings_json = json.dumps(
            list(dict.fromkeys(post_warnings)),
            ensure_ascii=False,
        )
        run.status = "success"
        run.post_id = post.id
        run.finished_at = datetime.utcnow()
        await db.commit()
        await db.refresh(post)
        return post
    except Exception as exc:
        await db.rollback()
        failed_run = await db.get(SocialFarmGenerationRun, run.id)
        if failed_run:
            failed_run.status = "failed"
            failed_run.error_message = str(exc)[:2000]
            failed_run.finished_at = datetime.utcnow()
            await db.commit()
        raise


async def scheduled_generation(db: AsyncSession) -> Optional[SocialFarmPost]:
    """Skapa högst ett nytt utkast per konfigurerat 48-timmarsfönster."""
    latest = await db.scalar(
        select(SocialFarmPost).order_by(desc(SocialFarmPost.created_at)).limit(1)
    )
    now = datetime.utcnow()
    if latest and now - latest.created_at < timedelta(hours=settings.social_farm_interval_hours):
        return None
    slot_key = f"scheduled-{now.strftime('%Y-%m-%d')}"
    return await generate_post(
        db,
        trigger="scheduled",
        slot_key=slot_key,
    )


async def list_posts(db: AsyncSession, limit: int = 30) -> list[SocialFarmPost]:
    result = await db.execute(
        select(SocialFarmPost).order_by(desc(SocialFarmPost.created_at)).limit(limit)
    )
    return list(result.scalars().all())


async def get_post(db: AsyncSession, post_id: int) -> Optional[SocialFarmPost]:
    return await db.get(SocialFarmPost, post_id)


async def get_slides(db: AsyncSession, post_id: int) -> list[SocialFarmSlide]:
    result = await db.execute(
        select(SocialFarmSlide)
        .where(SocialFarmSlide.post_id == post_id)
        .order_by(SocialFarmSlide.position)
    )
    return list(result.scalars().all())


async def update_slide(
    db: AsyncSession,
    *,
    post: SocialFarmPost,
    slide: SocialFarmSlide,
    heading: str,
    body: list[str],
) -> SocialFarmSlide:
    slide.heading = heading.strip()
    slide.body_json = json.dumps([value.strip() for value in body[:2]], ensure_ascii=False)
    warnings = validate_copy(slide.kind, slide.heading, decode_body(slide.body_json))
    if not slide.render_path:
        raise RuntimeError("Sliden saknar renderingsfil")
    warnings += render_slide(
        output_path=Path(slide.render_path),
        position=slide.position,
        kind=slide.kind,
        heading=slide.heading,
        body=decode_body(slide.body_json),
        visual_type=slide.visual_type,
        background_path=slide.background_path,
    )
    slide.quality_warnings_json = json.dumps(warnings, ensure_ascii=False)
    post.updated_at = datetime.utcnow()
    post.status = "needs_review"
    await db.commit()
    await db.refresh(slide)
    return slide


async def refresh_post_copy(
    db: AsyncSession,
    *,
    post: SocialFarmPost,
) -> SocialFarmPost:
    """Apply the current curated copy to an existing draft and re-render it."""
    topic = next((candidate for candidate in TOPICS if candidate.key == post.topic_key), None)
    if not topic:
        raise ValueError(f"Okänt ämne: {post.topic_key}")

    slides = await get_slides(db, post.id)
    if len(slides) != 6:
        raise ValueError("Utkastet måste innehålla exakt sex slides")

    payloads = [
        {
            "heading": topic.title,
            "body": [],
            "scene": slides[0].scene_prompt,
            "visual_type": slides[0].visual_type,
        },
        *[
            {
                "heading": blueprint.heading,
                "body": list(blueprint.body),
                "scene": blueprint.scene,
                "visual_type": blueprint.visual_type,
            }
            for blueprint in topic.slides
        ],
    ]

    post.title = topic.title
    post.caption = topic.caption
    post.cta = topic.cta
    post.copy_provider = "curated"
    post.status = "needs_review"
    post.approved_at = None
    post.updated_at = datetime.utcnow()

    post_warnings: list[str] = []
    for slide, payload in zip(slides, payloads):
        slide.heading = payload["heading"]
        slide.body_json = json.dumps(payload["body"], ensure_ascii=False)
        slide.scene_prompt = payload["scene"]
        slide.visual_type = payload["visual_type"]
        warnings = validate_copy(slide.kind, slide.heading, payload["body"])
        if not slide.render_path:
            raise RuntimeError("Sliden saknar renderingsfil")
        warnings += render_slide(
            output_path=Path(slide.render_path),
            position=slide.position,
            kind=slide.kind,
            heading=slide.heading,
            body=payload["body"],
            visual_type=slide.visual_type,
            background_path=slide.background_path,
        )
        slide.quality_warnings_json = json.dumps(warnings, ensure_ascii=False)
        post_warnings.extend(warnings)

    post.quality_warnings_json = json.dumps(
        list(dict.fromkeys(post_warnings)),
        ensure_ascii=False,
    )
    await db.commit()
    await db.refresh(post)
    return post


async def regenerate_slide_background(
    db: AsyncSession,
    *,
    post: SocialFarmPost,
    slide: SocialFarmSlide,
    force_local: bool = False,
) -> SocialFarmSlide:
    if not slide.render_path:
        raise RuntimeError("Sliden saknar renderingsfil")
    post_dir = Path(slide.render_path).parent
    background_path, image_provider, warnings = await _maybe_generate_background(
        prompt=_image_prompt(slide.scene_prompt, slide.visual_type),
        output_path=post_dir / f"background-{slide.position + 1:02d}-{uuid.uuid4().hex[:8]}.jpg",
        should_generate=not force_local,
    )
    slide.background_path = background_path
    slide.image_provider = image_provider
    warnings += validate_copy(slide.kind, slide.heading, decode_body(slide.body_json))
    warnings += render_slide(
        output_path=Path(slide.render_path),
        position=slide.position,
        kind=slide.kind,
        heading=slide.heading,
        body=decode_body(slide.body_json),
        visual_type=slide.visual_type,
        background_path=background_path,
    )
    slide.quality_warnings_json = json.dumps(warnings, ensure_ascii=False)
    post.status = "needs_review"
    post.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(slide)
    return slide


def file_url(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    try:
        relative = Path(path).resolve().relative_to(storage_root().resolve())
    except ValueError:
        return None
    return f"/social-farm-files/{relative.as_posix()}"


def serialize_slide(slide: SocialFarmSlide) -> dict[str, Any]:
    return {
        "id": slide.id,
        "position": slide.position,
        "kind": slide.kind,
        "heading": slide.heading,
        "body": decode_body(slide.body_json),
        "scene_prompt": slide.scene_prompt,
        "visual_type": slide.visual_type,
        "image_provider": slide.image_provider,
        "render_url": file_url(slide.render_path),
        "quality_warnings": json.loads(slide.quality_warnings_json or "[]"),
    }


async def serialize_post(db: AsyncSession, post: SocialFarmPost) -> dict[str, Any]:
    slides = await get_slides(db, post.id)
    return {
        "id": post.id,
        "slug": post.slug,
        "topic_key": post.topic_key,
        "category": post.category,
        "title": post.title,
        "caption": post.caption,
        "cta": post.cta,
        "status": post.status,
        "copy_provider": post.copy_provider,
        "quality_warnings": json.loads(post.quality_warnings_json or "[]"),
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
        "approved_at": post.approved_at.isoformat() if post.approved_at else None,
        "slides": [serialize_slide(slide) for slide in slides],
    }


async def create_post_export(db: AsyncSession, post: SocialFarmPost) -> Path:
    slides = await get_slides(db, post.id)
    export_path = storage_root() / "exports" / f"{post.slug}.zip"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = await serialize_post(db, post)
    with zipfile.ZipFile(export_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for slide in slides:
            if slide.render_path and Path(slide.render_path).exists():
                archive.write(
                    slide.render_path,
                    arcname=f"slide-{slide.position + 1:02d}.png",
                )
        archive.writestr(
            "caption.txt",
            f"{post.caption}\n\nCTA: {post.cta}\n",
        )
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2),
        )
    return export_path
