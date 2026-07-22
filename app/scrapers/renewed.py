"""
reNewed-scraper via Reuselys publika widget-API.

reNewed bäddar in Reusely-widgeten på /pages/salj-din-iphone. Sidkällan
innehåller tenantId, och widgetens JS anropar:

  /v2/widget/catalog/model-device/apple/iphone
  /v2/widget/catalog/model-device/apple/{model}
  /v2/widget/catalog/condition

Condition-nycklarna hålls medvetet korta och stabila:
  very_good, used, worn, broken
"""
import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from .base import BaseScraper
from ..config import settings

logger = logging.getLogger(__name__)

API_BASE = "https://api-eu.reusely.com/api"
TENANT_ID = "2694ab6485960dcbb75b67579d410cabb5f663eada69b6a0b5be503303028338"
SELL_URL = "https://renewed.se/pages/salj-din-iphone"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "sv",
    "x-tenant-id": TENANT_ID,
}

CONDITION_KEYS = {
    "Mycket bra skick": "very_good",
    "Använt skick": "used",
    "Slitet skick": "worn",
    "Trasigt skick": "broken",
}

STORAGE_RE = re.compile(r"(\d+)\s*(GB|TB)", re.I)


def _parse_price(value: Any) -> int:
    if value is None:
        return 0
    text = str(value)
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else 0


def _parse_storage(value: str) -> Optional[int]:
    match = STORAGE_RE.search(value or "")
    if not match:
        return None
    amount = int(match.group(1))
    return amount * 1024 if match.group(2).upper() == "TB" else amount


def _model_name(name: str) -> str:
    return re.sub(r"^Apple\s+", "", name or "").strip()


class RenewedScraper(BaseScraper):
    retailer_id = "renewed"
    retailer_name = "reNewed"
    min_models = 20
    min_rows = 200
    expected_conditions = frozenset(CONDITION_KEYS.values())

    async def fetch_prices(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            base_url=API_BASE,
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            headers=HEADERS,
        ) as client:
            models = await self._get_iphone_models(client)
            if not models:
                logger.warning("reNewed: inga iPhone-modeller hittade")
                return []

            logger.info(f"reNewed: {len(models)} modeller - hämtar priser")

            sem = asyncio.Semaphore(8)

            async def fetch_with_sem(model: Dict[str, Any]) -> List[Dict[str, Any]]:
                async with sem:
                    return await self._fetch_model_prices(client, model)

            results = await asyncio.gather(
                *[fetch_with_sem(model) for model in models],
                return_exceptions=True,
            )

            prices: List[Dict[str, Any]] = []
            for result in results:
                if isinstance(result, list):
                    prices.extend(result)
                else:
                    logger.warning(f"reNewed: modell misslyckades: {result}")

            return prices

    async def _get_iphone_models(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        resp = await client.get(
            "/v2/widget/catalog/model-device/apple/iphone",
            params={"page": 1, "limit": 100, "search": ""},
        )
        resp.raise_for_status()
        data = resp.json().get("result", {})
        return [
            model for model in data.get("data", [])
            if model.get("slug") and not model.get("is_recycle")
        ]

    async def _fetch_model_prices(
        self,
        client: httpx.AsyncClient,
        model: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        slug = model["slug"]
        name = _model_name(model.get("name", slug))

        spec_resp = await client.get(
            f"/v2/widget/catalog/model-device/apple/{slug}",
            params={"is_paginate": 1, "page": 1},
        )
        spec_resp.raise_for_status()
        spec = spec_resp.json().get("result", {})
        sizes = ((spec.get("options") or {}).get("size") or {}).get("choices") or []

        prices: List[Dict[str, Any]] = []
        for size in sizes:
            storage_gb = _parse_storage(size.get("name", ""))
            size_slug = size.get("slug")
            if not storage_gb or not size_slug:
                continue

            conditions = await self._get_conditions(client, slug, size_slug)
            for condition in conditions:
                condition_key = CONDITION_KEYS.get(condition.get("name"))
                price = _parse_price(condition.get("price"))
                if not condition_key or price <= 0:
                    continue

                prices.append({
                    "model": name,
                    "storage_gb": storage_gb,
                    "condition": condition_key,
                    "price_sek": price,
                    "url": SELL_URL,
                })

        logger.info(f"reNewed {name}: {len(prices)} priser")
        return prices

    async def _get_conditions(
        self,
        client: httpx.AsyncClient,
        model_slug: str,
        size_slug: str,
    ) -> List[Dict[str, Any]]:
        resp = await client.get(
            "/v2/widget/catalog/condition",
            params={
                "brand": "apple",
                "spec[device]": "iphone",
                "spec[model]": model_slug,
                "spec[network]": "unlocked",
                "spec[size]": size_slug,
            },
        )
        resp.raise_for_status()
        return resp.json().get("result", {}).get("conditions", [])
