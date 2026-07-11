from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConditionMapping:
    condition_class: str
    condition_label: str
    condition_rank: int
    source_note: str
    confidence: str = "high"


CONDITION_CLASSES: dict[str, dict[str, Any]] = {
    "new_in_box": {"label": "Ny i kartong", "rank": 4},
    "class_a": {"label": "Klass A", "rank": 3},
    "class_b": {"label": "Klass B", "rank": 2},
    "class_c": {"label": "Klass C", "rank": 1},
    "unknown": {"label": "Ej klassat", "rank": 0},
}


def _normalize(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip().lower()
    text = text.replace("–", "-").replace("—", "-")
    return text


def _mapping(condition_class: str, source_note: str, confidence: str = "high") -> ConditionMapping:
    config = CONDITION_CLASSES[condition_class]
    return ConditionMapping(
        condition_class=condition_class,
        condition_label=config["label"],
        condition_rank=config["rank"],
        source_note=source_note,
        confidence=confidence,
    )


def map_used_phone_condition(retailer: Any, raw_condition: Any) -> ConditionMapping:
    retailer_key = _normalize(retailer)
    raw_key = _normalize(raw_condition)

    if retailer_key == "phonehero":
        if raw_key == "ny i kartong":
            return _mapping("new_in_box", "PhoneHero Ny i kartong")
        if raw_key == "klass a":
            return _mapping("class_a", "PhoneHero Klass A")
        if raw_key == "klass b":
            return _mapping("class_b", "PhoneHero Klass B")
        if raw_key == "klass c":
            return _mapping("class_c", "PhoneHero Klass C")

    if retailer_key == "swappie":
        if raw_key == "a":
            return _mapping("class_a", "Swappie grade A")
        if raw_key == "b":
            return _mapping("class_b", "Swappie grade B")
        if raw_key in {"c", "d"}:
            return _mapping("class_c", f"Swappie grade {raw_key.upper()}", "medium" if raw_key == "d" else "high")

    if retailer_key == "telestore":
        if raw_key == "helt ny":
            return _mapping("new_in_box", "Telestore Helt ny")
        if raw_key in {"premium", "klass a"}:
            return _mapping("class_a", f"Telestore {raw_condition}")
        if raw_key == "klass b":
            return _mapping("class_b", "Telestore Klass B")
        if raw_key == "klass c":
            return _mapping("class_c", "Telestore Klass C")

    if retailer_key == "fixmyphone":
        if raw_key in {"like new", "like-new"}:
            return _mapping("class_a", "FixMyPhone Like new")
        if raw_key in {"very good", "very-good"}:
            return _mapping("class_b", "FixMyPhone Very good")
        if raw_key in {"good", "acceptable"}:
            return _mapping("class_c", f"FixMyPhone {raw_condition}", "medium" if raw_key == "acceptable" else "high")

    if retailer_key == "happyphone":
        if raw_key in {"som ny", "premium", "klass a"}:
            return _mapping("class_a", f"HappyPhone {raw_condition}")
        if raw_key == "klass b":
            return _mapping("class_b", "HappyPhone Klass B")
        if raw_key == "klass c":
            return _mapping("class_c", "HappyPhone Klass C")

    if retailer_key == "renewed":
        cleaned = re.sub(r"\s*\(kampanj\)\s*", "", raw_key).strip()
        if cleaned in {"nyskick", "premium"}:
            return _mapping("class_a", f"ReNewed {raw_condition}")
        if cleaned == "utmärkt skick":
            return _mapping("class_b", f"ReNewed {raw_condition}")
        if cleaned in {"bra skick", "okej skick"}:
            return _mapping("class_c", f"ReNewed {raw_condition}", "medium" if cleaned == "okej skick" else "high")

    if retailer_key == "fixtech":
        if raw_key == "nyhet":
            return _mapping("new_in_box", "FixTech NYHET", "medium")
        if raw_key == "som ny":
            return _mapping("class_a", "FixTech som ny")

    if retailer_key == "fixiphone":
        if raw_key in {"grade a", "klass a"}:
            return _mapping("class_a", f"Fixiphone {raw_condition}", "medium")
        if raw_key in {"grade b", "klass b"}:
            return _mapping("class_b", f"Fixiphone {raw_condition}", "medium")
        if raw_key in {"grade c", "klass c"}:
            return _mapping("class_c", f"Fixiphone {raw_condition}", "medium")

    return _mapping("unknown", f"Unmapped condition: {retailer or '<missing>'} / {raw_condition or '<missing>'}", "low")

