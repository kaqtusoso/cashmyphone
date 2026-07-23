from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps


CANVAS_SIZE = (1080, 1920)
SIDE_MARGIN = 92
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED_IMAGE = PROJECT_ROOT / "public/social-farm/seed/stockholm-drawer-cover.png"
BACKGROUND_ROOT = PROJECT_ROOT / "public/social-farm/backgrounds"
OBJECT_BACKGROUNDS = (
    BACKGROUND_ROOT / "01-soft-bed.png",
    BACKGROUND_ROOT / "02-sunlit-breakfast.png",
    BACKGROUND_ROOT / "03-summer-picnic.png",
    BACKGROUND_ROOT / "06-evening-drawer.png",
    BACKGROUND_ROOT / "07-city-flash.png",
    BACKGROUND_ROOT / "08-sunlit-reading-corner.png",
)
PERSON_BACKGROUNDS = (
    BACKGROUND_ROOT / "04-plant-cafe.png",
    BACKGROUND_ROOT / "05-coastal-window.png",
    SEED_IMAGE,
)


def _font_path(bold: bool = False) -> str:
    candidates = [
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError("Kunde inte hitta ett sans serif-typsnitt för slide-rendering")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(_font_path(bold=bold), size=size)


def _cover_crop(image: Image.Image) -> Image.Image:
    return ImageOps.fit(
        image.convert("RGB"),
        CANVAS_SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def _local_photo_background(position: int, visual_type: str) -> Image.Image:
    library = PERSON_BACKGROUNDS if visual_type == "person_far" else OBJECT_BACKGROUNDS
    available = tuple(path for path in library if path.exists())
    if not available:
        available = (SEED_IMAGE,)
    return _cover_crop(Image.open(available[position % len(available)]))


def _background(
    *,
    position: int,
    visual_type: str,
    background_path: Optional[str],
) -> Image.Image:
    candidate = Path(background_path) if background_path else None
    if candidate and candidate.exists():
        image = _cover_crop(Image.open(candidate))
    else:
        image = _local_photo_background(position, visual_type)

    image = ImageEnhance.Color(image).enhance(0.88)
    image = ImageEnhance.Contrast(image).enhance(0.96)
    overlay_strength = 70 if position == 0 else 82
    overlay = Image.new("RGBA", CANVAS_SIZE, (18, 18, 16, overlay_strength))
    return Image.alpha_composite(image.convert("RGBA"), overlay)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    words = text.strip().split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _fit_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    max_width: int,
    max_lines: int,
    start_size: int,
    min_size: int,
    bold: bool,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    for size in range(start_size, min_size - 1, -2):
        font = _font(size, bold=bold)
        lines = _wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    font = _font(min_size, bold=bold)
    return font, _wrap_text(draw, text, font, max_width)[:max_lines]


def _draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    lines: Iterable[str],
    *,
    font: ImageFont.FreeTypeFont,
    y: int,
    fill: tuple[int, int, int, int],
    line_gap: int,
    stroke_width: int = 0,
) -> int:
    current_y = y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        x = (CANVAS_SIZE[0] - width) // 2
        draw.text(
            (x, current_y),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=(0, 0, 0, 120),
        )
        current_y += height + line_gap
    return current_y


def render_slide(
    *,
    output_path: Path,
    position: int,
    kind: str,
    heading: str,
    body: list[str],
    visual_type: str,
    background_path: Optional[str] = None,
) -> list[str]:
    """Rendera en redigerbar slide till en deterministisk 1080x1920 PNG."""
    warnings: list[str] = []
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = _background(
        position=position,
        visual_type=visual_type,
        background_path=background_path,
    )
    draw = ImageDraw.Draw(image, "RGBA")
    max_width = CANVAS_SIZE[0] - SIDE_MARGIN * 2

    if kind == "cover":
        font, lines = _fit_lines(
            draw,
            heading,
            max_width=max_width,
            max_lines=4,
            start_size=82,
            min_size=58,
            bold=True,
        )
        if len(lines) >= 4:
            warnings.append("Coverrubriken använder fyra rader")
        total_height = sum(
            draw.textbbox((0, 0), line, font=font)[3] for line in lines
        ) + (len(lines) - 1) * 18
        y = max(250, min(590, (1040 - total_height) // 2 + 140))
        _draw_centered_lines(
            draw,
            lines,
            font=font,
            y=y,
            fill=(255, 255, 255, 255),
            line_gap=18,
        )
    else:
        heading_font, heading_lines = _fit_lines(
            draw,
            heading,
            max_width=max_width - 46,
            max_lines=2,
            start_size=54,
            min_size=40,
            bold=True,
        )
        line_metrics = [
            draw.textbbox((0, 0), line, font=heading_font) for line in heading_lines
        ]
        heading_width = max((bbox[2] - bbox[0] for bbox in line_metrics), default=0)
        heading_height = sum((bbox[3] - bbox[1] for bbox in line_metrics))
        heading_height += max(0, len(heading_lines) - 1) * 7
        pill_left = max(SIDE_MARGIN, (CANVAS_SIZE[0] - heading_width) // 2 - 28)
        pill_right = min(
            CANVAS_SIZE[0] - SIDE_MARGIN,
            (CANVAS_SIZE[0] + heading_width) // 2 + 28,
        )
        pill_top = 220
        pill_bottom = pill_top + heading_height + 36
        draw.rounded_rectangle(
            (pill_left, pill_top, pill_right, pill_bottom),
            radius=22,
            fill=(255, 255, 255, 250),
        )
        _draw_centered_lines(
            draw,
            heading_lines,
            font=heading_font,
            y=pill_top + 12,
            fill=(12, 12, 12, 255),
            line_gap=7,
        )

        body_font = _font(52, bold=True)
        current_y = pill_bottom + 96
        for paragraph_index, paragraph in enumerate(body[:2]):
            lines = _wrap_text(draw, paragraph, body_font, max_width - 50)
            if len(lines) > 3:
                body_font, lines = _fit_lines(
                    draw,
                    paragraph,
                    max_width=max_width - 50,
                    max_lines=3,
                    start_size=50,
                    min_size=40,
                    bold=True,
                )
                warnings.append(
                    f"Textblock {paragraph_index + 1} behövde minskad textstorlek"
                )
            current_y = _draw_centered_lines(
                draw,
                lines,
                font=body_font,
                y=current_y,
                fill=(255, 255, 255, 255),
                line_gap=10,
            )
            current_y += 74
        if current_y > 1030:
            warnings.append("Texten ligger nära den nedre säkra gränsen")

    image.convert("RGB").save(output_path, format="PNG", optimize=True)
    return warnings


def validate_copy(kind: str, heading: str, body: list[str]) -> list[str]:
    warnings: list[str] = []
    if kind == "cover" and len(heading) > 72:
        warnings.append("Coverrubriken är längre än rekommenderat")
    if kind != "cover" and len(heading) > 58:
        warnings.append("Slide-rubriken är längre än rekommenderat")
    if len(body) > 2:
        warnings.append("Fler än två textblock")
    if any(len(paragraph) > 105 for paragraph in body):
        warnings.append("Ett textblock är längre än rekommenderat")
    forbidden = (
        "garanterat högsta",
        "bäst i sverige",
        "alltid högst",
        "televera köper",
    )
    normalized = f"{heading} {' '.join(body)}".lower()
    for phrase in forbidden:
        if phrase in normalized:
            warnings.append(f"Otillåten claim: {phrase}")
    return warnings


def decode_body(body_json: str) -> list[str]:
    try:
        value = json.loads(body_json)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item) for item in value] if isinstance(value, list) else []
