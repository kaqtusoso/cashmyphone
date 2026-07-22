"""Verifiera tre representativa Televera-scenarier mot lagrade produktionspriser.

Skriptet använder den lokala crosswalk-koden för condition-nycklar och läser
endast offentliga /api/prices-rader. Ingen order eller prisdata ändras.
"""
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.pricing.crosswalk import FormAnswers, all_conditions, phonehero_conditions
from app.routers.prices import _phonehero_ignores_battery


API_BASE = os.environ.get(
    "TELEVERA_API_URL",
    "https://cashmyphone-production.up.railway.app",
).rstrip("/")
RETAILERS = (
    "swappie", "fixmyphone", "happyphone", "telestore",
    "phonehero", "renewed", "fixiphone", "fixphonepro",
)


@dataclass(frozen=True)
class Scenario:
    name: str
    model: str
    storage_gb: int
    description: str
    answers: FormAnswers


SCENARIOS = (
    Scenario(
        name="A",
        model="iPhone 16 Pro",
        storage_gb=256,
        description="Nyskick, 100 % batteri och alla funktioner fungerar",
        answers=FormAnswers(
            "LIKE_NEW", "LIKE_NEW", "LIKE_NEW",
            battery_health_percent=100,
        ),
    ),
    Scenario(
        name="B",
        model="iPhone 13",
        storage_gb=128,
        description=(
            "Djupa skärmrepor, synligt slitage på baksidan, lätt slitage på "
            "sidorna, 82 % batteri, fullt fungerande"
        ),
        answers=FormAnswers(
            "GOOD", "ALMOST_NEW", "GOOD",
            is_glass_scratched=True,
            is_battery_low=True,
            battery_health_percent=82,
        ),
    ),
    Scenario(
        name="C",
        model="iPhone 12",
        storage_gb=128,
        description=(
            "Spruckna sidor och sprucken baksida, trasig bakkamera, "
            "79 % batteri, men telefonen startar"
        ),
        answers=FormAnswers(
            "ALMOST_NEW", "MODERATE", "MODERATE",
            is_back_camera_broken=True,
            is_frame_broken=True,
            is_sides_cracked=True,
            is_back_cracked=True,
            is_battery_low=True,
            battery_health_percent=79,
        ),
    ),
)


def scenario_conditions(scenario: Scenario) -> Dict[str, Optional[Union[str, List[str]]]]:
    conditions = all_conditions(scenario.answers)
    conditions["phonehero"] = phonehero_conditions(
        scenario.answers,
        model=scenario.model,
        ignore_battery=_phonehero_ignores_battery(scenario.model),
    )
    return conditions


async def _fetch_one(
    client: httpx.AsyncClient,
    scenario: Scenario,
    retailer: str,
    condition: str,
) -> List[dict]:
    response = await client.get(
        f"{API_BASE}/api/prices",
        params={
            "model": scenario.model,
            "storage_gb": scenario.storage_gb,
            "retailer": retailer,
            "condition": condition,
            "limit": 100,
        },
    )
    response.raise_for_status()
    return [
        row for row in response.json()
        if row.get("model", "").lower() == scenario.model.lower()
        and row.get("storage_gb") == scenario.storage_gb
        and row.get("retailer", "").lower() == retailer
        and row.get("condition", "").lower() == condition.lower()
    ]


async def verify() -> List[dict]:
    output = []
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for scenario in SCENARIOS:
            condition_map = scenario_conditions(scenario)
            quotes = {}
            for retailer in RETAILERS:
                value = condition_map[retailer]
                if value is None:
                    quotes[retailer] = {"condition": None, "price_sek": None}
                    continue
                keys = value if isinstance(value, list) else [value]
                results = await asyncio.gather(
                    *(_fetch_one(client, scenario, retailer, key) for key in keys)
                )
                rows = [row for group in results for row in group]
                rows = [row for row in rows if row.get("price_sek", 0) > 0]
                best = max(rows, key=lambda row: row["price_sek"], default=None)
                quotes[retailer] = {
                    "condition": best["condition"] if best else keys,
                    "price_sek": best["price_sek"] if best else None,
                }
            output.append({
                "scenario": scenario.name,
                "model": scenario.model,
                "storage_gb": scenario.storage_gb,
                "description": scenario.description,
                "quotes": quotes,
            })
    return output


if __name__ == "__main__":
    print(json.dumps(asyncio.run(verify()), ensure_ascii=False, indent=2))
