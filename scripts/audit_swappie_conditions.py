"""Differentialtesta Televeras Swappie-crosswalk mot Swappies live-API.

Kör från repo-roten:
    python scripts/audit_swappie_conditions.py --model "iPhone 15"

Testet hämtar hela officiella villkorsmatrisen, kräver exakt 160 unika
kombinationer per modell/lagring och provar därefter alla 2 048 kombinationer
som Televeras pris-crosswalk kan generera.
"""
import argparse
import asyncio
import sys
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from curl_cffi.requests import AsyncSession as CurlAsyncSession

from app.pricing.crosswalk import FormAnswers, swappie_condition
from app.scrapers.swappie import (
    KNOWN_FUNCTIONAL_CONDITIONS,
    KNOWN_VISUAL_CONDITIONS,
    _condition_key,
    _fetch_model_curl,
    _parse_results,
    _validate_api_schema,
)


def _generated_crosswalk_keys():
    surfaces = ("LIKE_NEW", "ALMOST_NEW", "GOOD", "MODERATE")
    keys = set()
    checked = 0
    for screen, sides, back in product(surfaces, repeat=3):
        for glass, display, frame, camera, low_battery in product(
            [False, True], repeat=5
        ):
            key = swappie_condition(FormAnswers(
                screen_surface=screen,
                sides_surface=sides,
                back_surface=back,
                is_glass_broken=glass,
                is_screen_broken=display,
                is_frame_broken=frame,
                is_back_camera_broken=camera,
                is_battery_low=low_battery,
            ))
            if key is not None:
                keys.add(key)
            checked += 1
    return checked, keys


async def audit(model: str) -> None:
    async with CurlAsyncSession(impersonate="chrome136") as session:
        rows = await _fetch_model_curl(session, model)
    if not rows:
        raise RuntimeError(f"Swappie returnerade inga API-rader för {model}")

    _validate_api_schema(rows)
    parsed = _parse_results(rows)
    api_keys = {row["condition"] for row in parsed}
    checked, generated_keys = _generated_crosswalk_keys()
    missing = generated_keys - api_keys
    if missing:
        raise RuntimeError(
            f"{len(missing)} Televera-nycklar saknas i Swappies API: {sorted(missing)}"
        )

    device_count = len({row["model_name"] for row in rows})
    print(
        f"OK: {len(rows)} API-rader för {device_count} modell/lagringar; "
        f"{checked} Televera-kombinationer testade; {len(generated_keys)} unika nycklar."
    )

    target = next(
        (
            row for row in rows
            if row.get("model_name") == "iPhone 15 128GB"
            and row.get("visual_condition") == "ALMOST_NEW"
            and row.get("functional_condition") == ["BROKEN_FRAME"]
        ),
        None,
    )
    if target:
        price = target["price"]["price"]
        print(f"Linda-kontroll: ALMOST_NEW:BF = {price:.2f} kr i live-API:t.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="iPhone 15")
    args = parser.parse_args()
    asyncio.run(audit(args.model))


if __name__ == "__main__":
    main()
