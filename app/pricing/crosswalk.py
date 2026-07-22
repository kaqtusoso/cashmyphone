"""
Crosswalk — mappar CashMyPhones formulärsvar till varje återförsäljares condition-nyckel.

CashMyPhone använder Swappies formulärflöde. De individuella yt-svaren
(skärm, sidor, baksida) och funktionsflaggorna mappas till varje återförsäljares
egna skick-system.

─── Indata (FormAnswers) ──────────────────────────────────────────────────────
  screen_surface   – skärmens visuella slitage: LIKE_NEW | ALMOST_NEW | GOOD | MODERATE
  sides_surface    – sidornas visuella slitage: samma skala
  back_surface     – baksidans visuella skick: MODERATE = sprucken/trasig i äldre klienter
  is_broken        – underkänd funktionskoll     (Swappie: inget bud)
  is_screen_broken – skärm fungerar ej           (Swappie: BS)
  is_glass_broken  – äldre samlingsflagga för sprucket/flisigt skärmglas
  is_frame_broken  – sprucken/skadad sida/baksida (Swappie: BF)
  is_back_camera_broken – bakre kamera trasig    (Swappie: BBC)
  is_battery_low   – batteri under tröskeln      (Swappie: BAT, tröskel 86%)
  is_water_damaged – böjd, vatten, Face/Touch ID (Swappie: → MODERATE visuellt)

─── Condition-nyckelformat per återförsäljare ────────────────────────────────
  Swappie:     None om funktionskollen underkänns, annars "LIKE_NEW" / "GOOD:B,BAT,BBC,BF,BS"
  FixMyPhone:  "like_new"  /  "good:no_battery:no_display"
  HappyPhone:  identisk med FixMyPhone
  Telestore:   "nyskick"   /  "bra:bat:sidor"  /  "water_damaged"
               None = Telestore lägger inget bud (enheten fungerar ej)
  reNewed:     "very_good" / "used" / "worn" / "broken"
  Fixiphone:   "d0" / "d10" / ... summerat procentavdrag enligt deras formulär
  FixPhonePro: "s=n|b=n|d=no|f=y|bt=ok"
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
    is_broken:        bool = False  # minst ett fel i den samlade funktionskollen
    is_power_broken:  bool = False
    is_network_broken: bool = False
    is_face_id_broken: bool = False
    is_selfie_camera_broken: bool = False
    is_speaker_broken: bool = False
    is_charging_or_buttons_broken: bool = False
    is_other_broken: bool = False
    is_screen_broken: bool = False  # skärmfunktion trasig (fläckar/linjer)
    is_glass_broken:  bool = False  # äldre flagga: skärmglas sprucket/flisigt
    is_glass_chipped: bool = False  # faktisk spricka/flisa
    is_glass_scratched: bool = False  # djupa repor, men inte spricka
    is_frame_broken:  bool = False  # skadade/spruckna sidor eller baksida
    is_sides_cracked: bool = False
    is_back_cracked: bool = False
    is_back_camera_broken: bool = False  # bakre kamera fungerar inte
    is_battery_low:   bool = False  # batteri under tröskeln
    battery_health_percent: Optional[int] = None
    is_water_damaged: bool = False  # böjd, vatten eller Face/Touch ID trasigt


def _glass_cracked(a: FormAnswers) -> bool:
    """Ny klient skiljer flisa/spricka från repa; legacyfältet betyder spricka."""
    return a.is_glass_chipped or a.is_glass_broken


def _glass_scratched(a: FormAnswers) -> bool:
    return a.is_glass_scratched


def _sides_cracked(a: FormAnswers) -> bool:
    return a.is_sides_cracked or (
        a.is_frame_broken and a.sides_surface == "MODERATE"
    )


def _back_cracked(a: FormAnswers) -> bool:
    return a.is_back_cracked or (
        a.is_frame_broken and a.back_surface == "MODERATE"
    )


def _granular_function_flags(a: FormAnswers) -> List[str]:
    names = (
        "is_power_broken", "is_network_broken", "is_face_id_broken",
        "is_selfie_camera_broken", "is_back_camera_broken",
        "is_speaker_broken", "is_charging_or_buttons_broken",
        "is_other_broken",
    )
    return [name for name in names if getattr(a, name)]


def _has_non_camera_function_issue(a: FormAnswers) -> bool:
    # is_broken finns kvar för äldre klienter och omfattar inte bakkameran.
    return a.is_broken or any(
        getattr(a, name)
        for name in (
            "is_power_broken", "is_network_broken", "is_face_id_broken",
            "is_selfie_camera_broken", "is_speaker_broken",
            "is_charging_or_buttons_broken", "is_other_broken",
        )
    )


def _has_any_function_issue(a: FormAnswers) -> bool:
    return _has_non_camera_function_issue(a) or a.is_back_camera_broken


# ─── Swappie ──────────────────────────────────────────────────────────────────

_SWAPPIE_FUNC: Dict[str, str] = {
    "is_battery_low":   "BAT",
    "is_glass_broken":  "B",
    "is_screen_broken": "BS",
    "is_frame_broken":  "BF",
    "is_back_camera_broken": "BBC",
}


def _battery_low_for_swappie(a: FormAnswers) -> bool:
    """Swappies liveflöde använder 86 % som gräns (85 % ger BAT)."""
    if a.battery_health_percent is not None:
        return a.battery_health_percent < 86
    return a.is_battery_low

def swappie_condition(a: FormAnswers) -> Optional[str]:
    # Swappies svenska säljflöde visar "Ej kvalificerad" när någon del av
    # funktionskollen underkänns. Televeras is_broken samlar alla sådana fel.
    if _has_non_camera_function_issue(a):
        return None

    # Swappies "Skadad" för sida/baksida är BROKEN_FRAME, inte en visuell
    # MODERATE-nivå. Äldre klienter skickar samtidigt MODERATE för den skadade
    # ytan, så cappa just dessa ytor när den explicita flaggan finns.
    sides_visual = (
        "LIKE_NEW"
        if _sides_cracked(a) and a.sides_surface == "MODERATE"
        else a.sides_surface
    )
    back_visual = (
        "LIKE_NEW"
        if _back_cracked(a) and a.back_surface == "MODERATE"
        else a.back_surface
    )
    visual = _worst(a.screen_surface, sides_visual, back_visual)
    if a.is_water_damaged:
        visual = "MODERATE"

    functional = []
    if _battery_low_for_swappie(a):
        functional.append(_SWAPPIE_FUNC["is_battery_low"])
    enabled = {
        "is_glass_broken": _glass_cracked(a) or _glass_scratched(a),
        "is_screen_broken": a.is_screen_broken,
        "is_frame_broken": _sides_cracked(a) or _back_cracked(a),
        "is_back_camera_broken": a.is_back_camera_broken,
    }
    functional.extend(
        abbrev for flag, abbrev in _SWAPPIE_FUNC.items()
        if flag != "is_battery_low" and enabled.get(flag, False)
    )
    functional.sort()
    return f"{visual}:{','.join(functional)}" if functional else visual


# ─── FixMyPhone / HappyPhone ──────────────────────────────────────────────────

_FMP_VISUAL: Dict[str, str] = {
    "LIKE_NEW":   "like_new",
    "ALMOST_NEW": "very_good",
    "GOOD":       "good",
    "MODERATE":   "acceptable",
}

def fixmyphone_condition(a: FormAnswers) -> str:
    # FixMyPhone grupperar Face/Touch ID med böjd/fuktskadad och ger fast pris.
    if a.is_water_damaged or a.is_face_id_broken:
        return "water_damaged"

    # Spricka/flisa besvaras separat i deras formulär och ska därför inte
    # samtidigt sänka den rena visuella nivån.
    screen_visual = "LIKE_NEW" if _glass_cracked(a) else a.screen_surface
    back_visual = "LIKE_NEW" if _back_cracked(a) else a.back_surface
    visual = _FMP_VISUAL[_worst(screen_visual, a.sides_surface, back_visual)]

    # Suffix i alfabetisk ordning (no_back, no_battery, no_display, no_working)
    suffixes: List[str] = []
    if _back_cracked(a):
        suffixes.append("no_back")
    if a.is_battery_low:
        suffixes.append("no_battery")
    if _glass_cracked(a) or _glass_scratched(a) or a.is_screen_broken:
        suffixes.append("no_display")
    if _has_any_function_issue(a):
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

    Telestore använder sin officiella 60-kronorsrad för enheter med
    funktionsfel eller vattenskada.
    Böjda/vattenskadade telefoner ger alltid 60 kr (water_damaged).
    """
    if _has_any_function_issue(a) or a.is_water_damaged:
        # Officiella AJAX-API:t ger 60 kr för både ej fungerande och
        # böjd/vattenskadad telefon. Samma lagrade 60-kronorsrad återanvänds.
        return "water_damaged"

    # Skickfrågan avser hela telefonen. Sprickor hanteras separat av :sidor.
    screen_for_skick = "LIKE_NEW" if _glass_cracked(a) else a.screen_surface
    sides_for_skick = "LIKE_NEW" if _sides_cracked(a) else a.sides_surface
    back_for_skick = "LIKE_NEW" if _back_cracked(a) else a.back_surface
    base_visual = _worst(screen_for_skick, sides_for_skick, back_for_skick)

    # Glassprickor eller skärmproblem → sprickor_fram (overridar övrig skick)
    if _glass_cracked(a) or a.is_screen_broken:
        skick = "sprickor_fram"
    else:
        skick = _TELESTORE_SKICK[base_visual]

    suffixes: List[str] = []
    if a.is_battery_low:
        suffixes.append("bat")
    if _back_cracked(a) or _sides_cracked(a):
        suffixes.append("sidor")

    return f"{skick}:{':'.join(suffixes)}" if suffixes else skick


# ─── PhoneHero ────────────────────────────────────────────────────────────────

_PHONEHERO_VISUAL: Dict[str, str] = {
    "LIKE_NEW":   "n",
    "ALMOST_NEW": "ns",
    "GOOD":       "ns",
    "MODERATE":   "ms",
}

def _phonehero_new_device_family(model: Optional[str]) -> bool:
    if not model:
        return False
    normalized = " ".join(model.split()).lower()
    if normalized == "iphone air":
        return True
    parts = normalized.split()
    if len(parts) < 2:
        return False
    try:
        return int(parts[1]) >= 16
    except ValueError:
        return False


def _phonehero_defect(
    a: FormAnswers,
    *,
    new_device_family: bool,
    touch_id_model: bool,
) -> str:
    # Äldre klienter skickar bara is_broken; behåll det konservativa startfelet.
    granular = _granular_function_flags(a)
    if a.is_broken and not granular:
        return "off"
    if a.is_power_broken:
        return "off"
    if a.is_face_id_broken:
        return "fp" if touch_id_model else "fid"
    if a.is_speaker_broken:
        return "snd"
    if a.is_back_camera_broken or a.is_selfie_camera_broken:
        # Kamera är ett eget svar i äldre formulär. Nyare modeller har i stället
        # "Annat fel" och saknar kameraalternativet.
        return "oth" if new_device_family else "cam"
    if a.is_network_broken or a.is_charging_or_buttons_broken or a.is_other_broken:
        return "oth"
    return "no"


def phonehero_conditions(
    a: FormAnswers,
    *,
    model: Optional[str] = None,
    ignore_battery: bool = False,
) -> List[str]:
    """
    Returnerar möjliga PhoneHero-nycklar.

    PhoneHero använder två olika formulärfamiljer:
      äldre modeller: s=...|b=...|d=...|c=...|bt=...
      nyare modeller: dev=...|d=...|c=...

    Eftersom formulärfamiljen beror på modell returnerar vi båda. DB-frågan
    matchar sedan bara den nyckel som faktiskt finns för vald modell.
    """
    new_device_family = _phonehero_new_device_family(model)
    screen = _PHONEHERO_VISUAL[a.screen_surface]
    if a.is_screen_broken:
        screen = "lcd"
    elif _glass_cracked(a):
        screen = "sg"
    elif _glass_scratched(a):
        screen = "ms"

    body_surface = _worst(a.sides_surface, a.back_surface)
    body = "sp" if (_back_cracked(a) or _sides_cracked(a)) else _PHONEHERO_VISUAL[body_surface]

    if _glass_cracked(a) and _back_cracked(a):
        device = "sfb"
    elif _glass_cracked(a) or a.is_screen_broken:
        device = "sf"
    elif _back_cracked(a):
        device = "sb"
    elif _glass_scratched(a):
        device = "ms"
    else:
        device = _PHONEHERO_VISUAL[_worst(a.screen_surface, a.sides_surface, a.back_surface)]

    normalized_model = f" {' '.join((model or '').lower().split())} "
    defect = _phonehero_defect(
        a,
        new_device_family=new_device_family,
        touch_id_model=" iphone se " in normalized_model,
    )
    critical = "no"
    if a.is_water_damaged:
        critical = "ybad" if _has_any_function_issue(a) else "yok"

    battery = "low" if a.is_battery_low else "ok"

    batteryless = f"dev={device}|d={defect}|c={critical}"
    if ignore_battery:
        return [batteryless]

    return [
        f"s={screen}|b={body}|d={defect}|c={critical}|bt={battery}",
        f"dev={device}|d={defect}|c={critical}|bt={battery}",
        batteryless,
    ]


# ─── reNewed ──────────────────────────────────────────────────────────────────

_RENEWED_VISUAL: Dict[str, str] = {
    "LIKE_NEW":   "very_good",
    "ALMOST_NEW": "very_good",
    "GOOD":       "used",
    "MODERATE":   "worn",
}

def renewed_condition(a: FormAnswers) -> Optional[str]:
    """
    Returnerar reNeweds Reusely-condition.

    reNewed har fyra publika skicknivåer. "Trasigt skick" kräver enligt deras
    villkor att telefonen kan startas och inte är fukt-/böjskadad, så sådana
    kombinationer filtreras bort.
    """
    if (
        a.is_power_broken
        or a.is_water_damaged
        or (a.is_broken and not _granular_function_flags(a))
    ):
        return None

    if (
        _has_any_function_issue(a)
        or _glass_cracked(a)
        or a.is_screen_broken
        or _back_cracked(a)
        or _sides_cracked(a)
    ):
        return "broken"

    if _glass_scratched(a):
        return "worn"

    visual = _RENEWED_VISUAL[_worst(a.screen_surface, a.sides_surface, a.back_surface)]

    # Deras bästa skick kräver minst 85 % batterihälsa; övriga visuella skick
    # kräver minst 80 %. CashMyPhones batteriflagga betyder under topptröskeln.
    if a.battery_health_percent is not None and a.battery_health_percent < 80:
        return "broken"
    if a.is_battery_low and visual == "very_good":
        return "used"

    return visual


# ─── Fixiphone ────────────────────────────────────────────────────────────────

def fixiphone_se_condition(a: FormAnswers) -> str:
    """
    Returnerar Fixiphones summerade avdragsnyckel.

    Fixiphone fragar:
      - fungerar telefonen normalt? nej = 45
      - ar skarmens farg jamn? nej = 45
      - finns repor/bucklor i ram eller skarm? omarkbar = 10, markbar = 20
      - ar nagon glasdel trasig? ja = 45
      - ar den bojd/vattenskadad/Face ID trasig? ja = 90
    """
    deduction = 0
    granular_working_issue = any((
        a.is_power_broken,
        a.is_network_broken,
        a.is_selfie_camera_broken,
        a.is_back_camera_broken,
        a.is_speaker_broken,
        a.is_charging_or_buttons_broken,
        a.is_other_broken,
    ))
    if granular_working_issue or (a.is_broken and not _granular_function_flags(a)):
        deduction += 45
    if a.is_screen_broken:
        deduction += 45

    visual_wear = _worst(a.screen_surface, a.sides_surface)
    # Fixiphone skiljer bara på "Nej", "Omärkbar" och "Märkbar" för
    # repor/bucklor. Lätta repor i Televeras flöde motsvarar omärkbara spår.
    if visual_wear in {"ALMOST_NEW", "GOOD"}:
        deduction += 10
    elif visual_wear == "MODERATE":
        deduction += 20

    if _glass_cracked(a) or _back_cracked(a):
        deduction += 45
    if a.is_water_damaged or a.is_face_id_broken:
        deduction += 90

    return f"d{deduction}"


# ─── FixPhonePro ──────────────────────────────────────────────────────────────

_FIXPHONEPRO_VISUAL: Dict[str, str] = {
    "LIKE_NEW":   "n",
    "ALMOST_NEW": "ns",
    "GOOD":       "ms",
    "MODERATE":   "sp",
}

def fixphonepro_condition(a: FormAnswers) -> str:
    """
    Returnerar FixPhonePros formel-nyckel.

    FixPhonePro fragar separat efter skarm, baksida/ram, fel, om allt fungerar
    och batterihalsa. Alla feltyper har samma prisfaktor i deras publika JS.
    """
    if _glass_cracked(a) or a.is_screen_broken:
        screen = "sp"
    elif _glass_scratched(a):
        screen = "ms"
    else:
        screen = _FIXPHONEPRO_VISUAL[a.screen_surface]

    body_surface = _worst(a.sides_surface, a.back_surface)
    body = "sp" if (_back_cracked(a) or _sides_cracked(a)) else _FIXPHONEPRO_VISUAL[body_surface]

    has_defect = _has_any_function_issue(a) or a.is_screen_broken or a.is_water_damaged
    functional = "n" if has_defect else "y"
    defect = "yes" if has_defect else "no"
    battery = "low" if a.is_battery_low else "ok"

    return f"s={screen}|b={body}|d={defect}|f={functional}|bt={battery}"


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
        "renewed":    renewed_condition(a),
        "fixiphone":  fixiphone_se_condition(a),
        "fixphonepro": fixphonepro_condition(a),
    }
