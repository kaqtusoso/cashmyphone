from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import httpx

from ..config import settings


OPENAI_API_BASE = "https://api.openai.com/v1"


class ProviderUnavailable(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    if not settings.openai_api_key:
        raise ProviderUnavailable("OPENAI_API_KEY saknas")
    return {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }


def _extract_output_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def _parse_json_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned)


async def generate_copy(prompt: str) -> dict[str, Any]:
    """Generera ett strukturerat svenskt manus via Responses API."""
    request = {
        "model": settings.social_farm_text_model,
        "input": prompt,
        "reasoning": {"effort": "low"},
        "text": {"verbosity": "low"},
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{OPENAI_API_BASE}/responses",
            headers=_headers(),
            json=request,
        )
        response.raise_for_status()
    return _parse_json_text(_extract_output_text(response.json()))


async def generate_background(prompt: str, output_path: Path) -> None:
    """Generera ett textfritt 9:16-bakgrundsfoto via Image API."""
    request = {
        "model": settings.social_farm_image_model,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1536",
        "quality": settings.social_farm_image_quality,
        "output_format": "jpeg",
    }
    async with httpx.AsyncClient(timeout=240) as client:
        response = await client.post(
            f"{OPENAI_API_BASE}/images/generations",
            headers=_headers(),
            json=request,
        )
        response.raise_for_status()
    payload = response.json()
    encoded = payload["data"][0]["b64_json"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(encoded))
