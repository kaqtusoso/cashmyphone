"""
Crosswalk — mappar CashMyPhones formulärsvar till varje återförsäljares condition-nyckel.

CashMyPhone använder Swappies formulärflöde. De individuella yt-svaren
(skärm, sidor, baksida) och funktionsflaggorna mappas till varje återförsäljares
egna skick-system.

─── Indata (FormAnswers) ──────────────────────────────────────────────────────
  screen_surface   – skärmens visuella slitage: LIKE_NEW | ALMOST_NEW | GOOD | MODERATE
  sides_surface    – sidornas visuella slitage: samma skala
  back_surface     – baksidans skick: MODERATE = sprucken/trasig
  is_broken        – enheten startar ej          (Swappie: B)
  is_screen_broken – skärm fungerar ej           (Swappie: BS)
  is_glass_broken  – skärmglas sprucket/repor    (Swappie: BG)
  is_battery_low   – batteri under tröskeln      (Swappie: BAT, tröskel 86%)
  is_water_damaged – böjd, vatten, Face/Touch ID (Swappie: → MODERATE visuellt)

─── Condition-nyckelformat per återförsäljare ────────────────────────────────
  Swappie:     "LIKE_NEW"  /  "GOOD:B,BAT,BG,BS"
  FixMyPhone:  "like_new"  /  "good:no_battery:no_display"
  HappyPhone:  identisk med FixMyPhone
  Telestore:   "nyskick"   /  "bra:bat:sidor"  /  "water_damaged"
               None = Telestore lägger inget bud (enheten fungerar ej)
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Union


# ─── Ytskala ──────────────────────────────────────────────────────────────────

SURFACE_RANK: Dict[str, int] = {
    "LIKE_NEW":   0,
    "ALMOST_NEW": 1,
    "GOOD":       2,
    "MODERATE":   3,
}

def _worst(*surfaces: str) -> str:
    return max(surfaces, key=lambda s: SURFACE_RANK.get(s, 0))


# ─── Indata-struktur ──────────────────────────────────────────────────────────

@dataclass
class FormAnswers:
    """Alla svar från CashMyPhones formulär (Swappie-baserat, 9 steg)."""
    screen_surface:   str          # LIKE_NEW | ALMOST_NEW | GOOD | MODERATE
    sides_surface:    str
    back_surface:     str          # MODERATE = sprucken/trasig
    is_broken:        bool = False  # startar ej
    is_screen_broken: bool = False  # skärmfunktion trasig (fläckar/linjer)
    is_glass_broken:  bool = False  # skärmglas sprucket/allvarliga repor
    is_battery_low:   bool = False  # batteri under tröskeln
    is_water_damaged: bool = False  # böjd, vatten eller Face/Touch ID trasigt


# ─── Swappie ──────────────────────────────────────────────────────────────────

_SWAPPIE_FUNC: Dict[str, str] = {
    "is_broken":        "B",
    "is_battery_low":   "BAT",
    "is_glass_broken":  "BG",
    "is_screen_broken": "BS",
}

def swappie_condition(a: FormAnswers) -> str:
    visual = _worst(a.screen_surface, a.sides_surface, a.back_surface)
    if a.is_water_damaged:
        visual = "MODERATE"

    functional = sorted(
        abbrev for flag, abbrev in _SWAPPIE_FUNC.items()
        if getattr(a, flag)
    )
    return f"{visual}:{','.join(functional)}" if functional else visual


# ─── FixMyPhone / HappyPhone ──────────────────────────────────────────────────

_FMP_VISUAL: Dict[str, str] = {
    "LIKE_NEW":   "like_new",
    "ALMOST_NEW": "very_good",
    "GOOD":       "good",
    "MODERATE":   "acceptable",
}

def fixmyphone_condition(a: FormAnswers) -> str:
    if a.is_water_damaged:
        return "water_damaged"

    visual = _FMP_VISUAL[_worst(a.screen_surface, a.sides_surface, a.back_surface)]

    # Suffix i alfabetisk ordning (no_back, no_battery, no_display, no_working)
    suffixes: List[str] = []
    if a.back_surface == "MODERATE":
        suffixes.append("no_back")
    if a.is_battery_low:
        suffixes.append("no_battery")
    if a.is_glass_broken or a.is_screen_broken:
        suffixes.append("no_display")
    if a.is_broken:
        suffixes.append("no_working")

    return f"{visual}:{':'.join(suffixes)}" if suffixes else visual


# HappyPhone använder identisk prismodell och condition-nyckel som FixMyPhone
happyphone_condition = fixmyphone_condition


# ─── Telestore ────────────────────────────────────────────────────────────────

_TELESTORE_SKICK: Dict[str, str] = {
    "LIKE_NEW":   "nyskick",
    "ALMOST_NEW": "utmarkt",
    "GOOD":       "bra",
    "MODERATE":   "okej",
}

def telestore_condition(a: FormAnswers) -> Optional[str]:
    """
    Returnerar Telestores condition-nyckel, eller None om de inte lägger bud.

    Telestore köper INTE telefoner som inte fungerar (is_broken = True).
    Böjda/vattenskadade telefoner ger alltid 60 kr (water_damaged).
    """
    if a.is_broken:
        return None  # Telestore lägger inget bud

    if a.is_water_damaged:
        return "water_damaged"

    # Skick baseras på skärm + sidor.
    # Spruckna sidor (MODERATE) täcks av :sidor — cappa till GOOD för skick-beräkningen.
    sides_for_skick = "GOOD" if a.sides_surface == "MODERATE" else a.sides_surface
    base_visual = _worst(a.screen_surface, sides_for_skick)

    # Glassprickor eller skärmproblem → sprickor_fram (overridar övrig skick)
    if a.is_glass_broken or a.is_screen_broken:
        skick = "sprickor_fram"
    else:
        skick = _TELESTORE_SKICK[base_visual]

    suffixes: List[str] = []
    if a.is_battery_low:
        suffixes.append("bat")
    if a.back_surface == "MODERATE" or a.sides_surface == "MODERATE":
        suffixes.append("sidor")

    return f"{skick}:{':'.join(suffixes)}" if suffixes else skick


# ─── PhoneHero ────────────────────────────────────────────────────────────────

_PHONEHERO_VISUAL: Dict[str, str] = {
    "LIKE_NEW":   "n",
    "ALMOST_NEW": "ns",
    "GOOD":       "ns",
    "MODERATE":   "ms",
}

def phonehero_conditions(a: FormAnswers) -> List[str]:
    """
    Returnerar möjliga PhoneHero-nycklar.

    PhoneHero använder två olika formulärfamiljer:
      äldre modeller: s=...|b=...|d=...|c=...|bt=...
      nyare modeller: dev=...|d=...|c=...

    Eftersom formulärfamiljen beror på modell returnerar vi båda. DB-frågan
    matchar sedan bara den nyckel som faktiskt finns för vald modell.
    """
    screen = _PHONEHERO_VISUAL[a.screen_surface]
    if a.is_screen_broken:
        screen = "lcd"
    elif a.is_glass_broken:
        screen = "sg"

    body_surface = _worst(a.sides_surface, a.back_surface)
    body = "sp" if a.back_surface == "MODERATE" else _PHONEHERO_VISUAL[body_surface]

    if a.is_glass_broken and a.back_surface == "MODERATE":
        device = "sfb"
    elif a.is_glass_broken or a.is_screen_broken:
        device = "sf"
    elif a.back_surface == "MODERATE":
        device = "sb"
    else:
        device = _PHONEHERO_VISUAL[_worst(a.screen_surface, a.sides_surface, a.back_surface)]

    defect = "off" if a.is_broken else "no"
    critical = "no"
    if a.is_water_damaged:
        critical = "ybad" if a.is_broken else "yok"

    battery = "low" if a.is_battery_low else "ok"

    return [
        f"s={screen}|b={body}|d={defect}|c={critical}|bt={battery}",
        f"dev={device}|d={defect}|c={critical}|bt={battery}",
        f"dev={device}|d={defect}|c={critical}",
    ]


# ─── Samlad lookup ────────────────────────────────────────────────────────────

ConditionLookup = Optional[Union[str, List[str]]]


def all_conditions(a: FormAnswers) -> Dict[str, ConditionLookup]:
    """
    Returnerar condition-nycklarna för alla fyra återförsäljare givet
    ett CashMyPhone-formulärsvar.
    None = återförsäljaren lägger inget bud för denna kombination.
    """
    return {
        "swappie":    swappie_condition(a),
        "fixmyphone": fixmyphone_condition(a),
        "happyphone": happyphone_condition(a),
        "telestore":  telestore_condition(a),
        "phonehero":  phonehero_conditions(a),
    }
