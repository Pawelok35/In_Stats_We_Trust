from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Tuple

import yaml


def load_guardrails(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _pp(value: Optional[float]) -> Optional[float]:
    if value is None or math.isnan(value):
        return None
    return value * 100.0

# === Guardrails v1 (obecna wersja) ==========================================


def apply_guardrails(
    *,
    matchup: dict,
    bucket: str,
    rating: float,
    guardrails: Mapping[str, object],
) -> Tuple[float, str, List[str]]:
    """
    matchup: {
      "fav": "TEAM",
      "dog": "TEAM",
      "last3": { "<field>_<TEAM>": val, ... },
      "last5": {...}  # optional
    }
    bucket: current bucket string (Calm/Breeze/Gale/Cyclone/Supercell/Ultimate...)
    rating: current numeric rating
    """
    notes: List[str] = []
    penalty = 0.0
    supercell_allowed = True

    # Helpers to pull metrics
    last3 = matchup.get("last3") or {}
    last5 = matchup.get("last5") or {}
    fav = matchup.get("fav")
    dog = matchup.get("dog")

    def gap(field: str) -> Optional[float]:
        fa = last3.get(f"{field}_{fav}")
        da = last3.get(f"{field}_{dog}")
        if fa is None or da is None:
            return None
        try:
            return float(fa) - float(da)
        except (TypeError, ValueError):
            return None

    # 1) PPD diff last3
    ppd_diff = gap("points_per_drive_off_avg")
    ppd_cfg: Mapping[str, float] = guardrails.get("ppd_last3", {})  # type: ignore
    if ppd_diff is not None:
        if bucket == "Supercell" and ppd_diff < ppd_cfg.get("min_for_supercell", -math.inf):
            supercell_allowed = False
            notes.append(f"PPD diff last3 too low ({ppd_diff:.2f})")
        elif bucket == "Cyclone" and ppd_diff < ppd_cfg.get("min_for_cyclone", -math.inf):
            notes.append(f"PPD diff last3 below cyclone guard ({ppd_diff:.2f})")

    # 2) 3rd down gap last3 (pp)
    td_gap = gap("third_down_conv_off_avg")
    td_cfg: Mapping[str, float] = guardrails.get("third_down_gap_last3", {})  # type: ignore
    if td_gap is not None:
        td_gap_pp = td_gap * 100.0
        if bucket == "Supercell" and td_gap_pp < td_cfg.get("min_for_supercell", -math.inf):
            supercell_allowed = False
            notes.append(f"3rd down gap last3 too low ({td_gap_pp:.1f} pp)")
        elif bucket == "Cyclone" and td_gap_pp < td_cfg.get("min_for_cyclone", -math.inf):
            notes.append(f"3rd down gap below cyclone guard ({td_gap_pp:.1f} pp)")

    # 3) Explosive gap last3 (pp)
    expl_gap = gap("explosive_play_rate_off_avg")
    expl_cfg: Mapping[str, float] = guardrails.get("explosive_gap_last3", {})  # type: ignore
    if expl_gap is not None:
        expl_gap_pp = expl_gap * 100.0
        if bucket == "Supercell" and expl_gap_pp < expl_cfg.get("min_for_supercell", -math.inf):
            supercell_allowed = False
            notes.append(f"Explosive gap last3 too low ({expl_gap_pp:.1f} pp)")
        elif bucket == "Cyclone" and expl_gap_pp < expl_cfg.get("min_for_cyclone", -math.inf):
            notes.append(f"Explosive gap below cyclone guard ({expl_gap_pp:.1f} pp)")

    # 4) Pass pro vs pressure mismatch (dog pass pro - fav pressure)
    pm_cfg: Mapping[str, float] = guardrails.get("pressure_mismatch", {})  # type: ignore
    try:
        fav_pressure = float(last3.get(f"pressure_rate_def_avg_{fav}", math.nan))
        dog_passpro = float(last3.get(f"pressure_rate_allowed_avg_{dog}", math.nan))
    except (TypeError, ValueError):
        fav_pressure = math.nan
        dog_passpro = math.nan
    if not math.isnan(fav_pressure) and not math.isnan(dog_passpro):
        mismatch_pp = (dog_passpro - fav_pressure) * 100.0
        if mismatch_pp > pm_cfg.get("warning_threshold", math.inf):
            penalty -= pm_cfg.get("rating_penalty", 0.0)
            notes.append(f"Pass-pro mismatch warning (dog pass pro - fav pressure = {mismatch_pp:.1f} pp)")

    # 5) Red zone cap
    try:
        rz_off = float(last3.get(f"redzone_td_rate_off_avg_{fav}", math.nan))
    except (TypeError, ValueError):
        rz_off = math.nan
    rz_cfg: Mapping[str, object] = guardrails.get("redzone_cap", {})  # type: ignore
    if not math.isnan(rz_off) and rz_cfg.get("downgrade_if_below", False):
        rz_pp = rz_off * 100.0
        rz_sup = float(rz_cfg.get("min_redzone_td_supercell", -math.inf))
        rz_cyc = float(rz_cfg.get("min_redzone_td_cyclone", -math.inf))
        if bucket == "Supercell" and rz_pp < rz_sup:
            supercell_allowed = False
            notes.append(f"Red zone TD last3 too low for Supercell ({rz_pp:.1f}%)")
        elif bucket == "Cyclone" and rz_pp < rz_cyc:
            notes.append(f"Red zone TD last3 below cyclone guard ({rz_pp:.1f}%)")

    # 6) Defensive trend guard (last3 vs last5 EPA def; wyższe = gorsze)
    if guardrails.get("defensive_trend_guard", {}).get("downgrade_if_def_epa_declining", False):
        try:
            last3_def = float(last3.get(f"epa_def_mean_avg_{fav}", math.nan))
            last5_def = float(last5.get(f"epa_def_mean_avg_{fav}", math.nan))
        except (TypeError, ValueError):
            last3_def = math.nan
            last5_def = math.nan
        if not math.isnan(last3_def) and not math.isnan(last5_def):
            if last3_def > last5_def:  # def EPA rośnie (gorsza)
                notes.append("Def EPA trending worse (last3 > last5)")
                penalty -= 0.2

    # Final adjustments
    rating_adj = rating + penalty
    bucket_final = bucket
    if bucket == "Supercell" and not supercell_allowed:
        bucket_final = "Cyclone"
        notes.append("Supercell guardrail triggered -> downgrading to Cyclone")

    return rating_adj, bucket_final, notes


# === Guardrails v2 (supercell->vortex->cyclone downgrade) ====================

def apply_guardrails_v2(
    *,
    matchup: dict,
    bucket: str,
    rating: float,
    guardrails: Mapping[str, object],
) -> tuple[float, str, list[str], int]:
    """
    Zwraca: (rating_adj, bucket_final, notes, guardrail_level)
    guardrail_level:
      0 = brak
      1 = soft_warning (tylko penalty/notes)
      2 = downgraded_supercell
      3 = downgraded_vortex
    """
    notes: list[str] = []
    penalty = 0.0
    level = 0

    last3 = matchup.get("last3") or {}
    last5 = matchup.get("last5") or {}
    fav = matchup.get("fav")
    dog = matchup.get("dog")

    def gap(field: str) -> Optional[float]:
        fa = last3.get(f"{field}_{fav}")
        da = last3.get(f"{field}_{dog}")
        if fa is None or da is None:
            return None
        try:
            return float(fa) - float(da)
        except (TypeError, ValueError):
            return None

    # Defaults / config
    min_rating_cfg: Mapping[str, float] = guardrails.get("min_rating", {})  # type: ignore
    ppd_cfg: Mapping[str, float] = guardrails.get("ppd_last3", {})  # type: ignore
    td_cfg: Mapping[str, float] = guardrails.get("third_down_gap_last3", {})  # type: ignore
    expl_cfg: Mapping[str, float] = guardrails.get("explosive_gap_last3", {})  # type: ignore
    rz_cfg: Mapping[str, float] = guardrails.get("redzone_td_last3", {})  # type: ignore
    pm_cfg: Mapping[str, float] = guardrails.get("pressure_mismatch", {})  # type: ignore
    def_trend_cfg: Mapping[str, float] = guardrails.get("def_epa_trend", {})  # type: ignore

    supercell_allowed = True
    vortex_allowed = True

    # Min rating gates
    if bucket == "Supercell" and rating < min_rating_cfg.get("supercell", -math.inf):
        supercell_allowed = False
        notes.append(f"Rating {rating:.2f} below Supercell min {min_rating_cfg.get('supercell')}")
        level = max(level, 2)
    if bucket == "Vortex" and rating < min_rating_cfg.get("vortex", -math.inf):
        vortex_allowed = False
        notes.append(f"Rating {rating:.2f} below Vortex min {min_rating_cfg.get('vortex')}")
        level = max(level, 3)

    # PPD diff
    ppd_diff = gap("points_per_drive_off_avg")
    if ppd_diff is not None:
        if bucket == "Supercell" and ppd_diff < ppd_cfg.get("supercell_min", -math.inf):
            supercell_allowed = False
            notes.append(f"PPD diff last3 too low ({ppd_diff:.2f})")
            level = max(level, 2)
        elif bucket == "Vortex" and ppd_diff < ppd_cfg.get("vortex_min", -math.inf):
            vortex_allowed = False
            notes.append(f"PPD diff last3 too low for Vortex ({ppd_diff:.2f})")
            level = max(level, 3)
        elif ppd_diff < ppd_cfg.get("cyclone_min", -math.inf):
            notes.append(f"PPD diff last3 below cyclone guard ({ppd_diff:.2f})")

    # 3rd down gap (pp)
    td_gap = gap("third_down_conv_off_avg")
    if td_gap is not None:
        td_gap_pp = td_gap * 100.0
        if bucket == "Supercell" and td_gap_pp < td_cfg.get("supercell_min", -math.inf):
            supercell_allowed = False
            notes.append(f"3rd down gap last3 too low ({td_gap_pp:.1f} pp)")
            level = max(level, 2)
        elif bucket == "Vortex" and td_gap_pp < td_cfg.get("vortex_min", -math.inf):
            vortex_allowed = False
            notes.append(f"3rd down gap last3 too low for Vortex ({td_gap_pp:.1f} pp)")
            level = max(level, 3)
        elif td_gap_pp < td_cfg.get("cyclone_min", -math.inf):
            notes.append(f"3rd down gap last3 below cyclone guard ({td_gap_pp:.1f} pp)")

    # Explosive gap (pp)
    expl_gap = gap("explosive_play_rate_off_avg")
    if expl_gap is not None:
        expl_gap_pp = expl_gap * 100.0
        if bucket == "Supercell" and expl_gap_pp < expl_cfg.get("supercell_min", -math.inf):
            supercell_allowed = False
            notes.append(f"Explosive gap last3 too low ({expl_gap_pp:.1f} pp)")
            level = max(level, 2)
        elif bucket == "Vortex" and expl_gap_pp < expl_cfg.get("vortex_min", -math.inf):
            vortex_allowed = False
            notes.append(f"Explosive gap last3 too low for Vortex ({expl_gap_pp:.1f} pp)")
            level = max(level, 3)
        elif expl_gap_pp < expl_cfg.get("cyclone_min", -math.inf):
            notes.append(f"Explosive gap last3 below cyclone guard ({expl_gap_pp:.1f} pp)")

    # Red zone absolute (pp)
    try:
        rz_off = float(last3.get(f"redzone_td_rate_off_avg_{fav}", math.nan))
    except (TypeError, ValueError):
        rz_off = math.nan
    if not math.isnan(rz_off):
        rz_pp = rz_off * 100.0
        if bucket == "Supercell" and rz_pp < rz_cfg.get("supercell_min", -math.inf):
            supercell_allowed = False
            notes.append(f"Red zone TD last3 too low for Supercell ({rz_pp:.1f}%)")
            level = max(level, 2)
        elif bucket == "Vortex" and rz_pp < rz_cfg.get("vortex_min", -math.inf):
            vortex_allowed = False
            notes.append(f"Red zone TD last3 too low for Vortex ({rz_pp:.1f}%)")
            level = max(level, 3)
        elif rz_pp < rz_cfg.get("cyclone_min", -math.inf):
            notes.append(f"Red zone TD last3 below cyclone guard ({rz_pp:.1f}%)")

    # Pressure mismatch
    try:
        fav_pressure = float(last3.get(f"pressure_rate_def_avg_{fav}", math.nan))
        dog_passpro = float(last3.get(f"pressure_rate_allowed_avg_{dog}", math.nan))
    except (TypeError, ValueError):
        fav_pressure = math.nan
        dog_passpro = math.nan
    if not math.isnan(fav_pressure) and not math.isnan(dog_passpro):
        mismatch_pp = (dog_passpro - fav_pressure) * 100.0
        if mismatch_pp > pm_cfg.get("hard_block_supercell", math.inf):
            supercell_allowed = False
            notes.append(f"Pass-pro mismatch blocks Supercell ({mismatch_pp:.1f} pp)")
            level = max(level, 2)
        if mismatch_pp > pm_cfg.get("warning_threshold", math.inf):
            penalty -= pm_cfg.get("rating_penalty", 0.0)
            notes.append(f"Pass-pro mismatch warning ({mismatch_pp:.1f} pp)")
            if level == 0:
                level = 1

    # Defensive trend
    try:
        last3_def = float(last3.get(f"epa_def_mean_avg_{fav}", math.nan))
        last5_def = float(last5.get(f"epa_def_mean_avg_{fav}", math.nan))
    except (TypeError, ValueError):
        last3_def = math.nan
        last5_def = math.nan
    if not math.isnan(last3_def) and not math.isnan(last5_def):
        worsening = last3_def - last5_def
        if bucket == "Supercell" and worsening > def_trend_cfg.get("max_worsening_supercell", math.inf):
            supercell_allowed = False
            notes.append(f"Def EPA trending worse (+{worsening:.3f}) blocks Supercell")
            level = max(level, 2)
            penalty -= def_trend_cfg.get("rating_penalty", 0.0)
        elif bucket == "Vortex" and worsening > def_trend_cfg.get("max_worsening_vortex", math.inf):
            vortex_allowed = False
            notes.append(f"Def EPA trending worse (+{worsening:.3f}) blocks Vortex")
            level = max(level, 3)
            penalty -= def_trend_cfg.get("rating_penalty", 0.0)

    # Final rating
    rating_adj = rating + penalty

    bucket_final = bucket
    if bucket == "Supercell":
        if not supercell_allowed and vortex_allowed:
            bucket_final = "Vortex"
            level = max(level, 2)
        elif not supercell_allowed and not vortex_allowed:
            bucket_final = "Cyclone"
            level = max(level, 3)
    elif bucket == "Vortex":
        if not vortex_allowed:
            bucket_final = "Cyclone"
            level = max(level, 3)

    if level == 0 and (notes or penalty != 0):
        level = 1

    return rating_adj, bucket_final, notes, level


def apply_guardrails_v2_1(
    *,
    matchup: dict,
    bucket: str,
    rating: float,
    guardrails: Mapping[str, object],
) -> tuple[float, str, list[str], int]:
    """
    Wariant v2.1:
    - bazuje na v2 (Supercell -> Vortex -> Cyclone, Vortex -> Cyclone)
    - dodatkowe twarde progi dla Supercell (min rating/gaps/RZ)
    - Supercell wymaga braku wcześniejszych notatek (guardrail_notes musi być puste)
    - guardrail_level jak w v2 (0/1/2/3)
    """
    # Najpierw użyj v2
    rating_adj, bucket_after_v2, notes, level = apply_guardrails_v2(
        matchup=matchup,
        bucket=bucket,
        rating=rating,
        guardrails=guardrails,
    )

    fav = matchup.get("fav")
    dog = matchup.get("dog")
    last3 = matchup.get("last3") or {}

    def gap(field: str) -> Optional[float]:
        fa = last3.get(f"{field}_{fav}")
        da = last3.get(f"{field}_{dog}")
        if fa is None or da is None:
            return None
        try:
            return float(fa) - float(da)
        except (TypeError, ValueError):
            return None

    # Twarde progi dla Supercell (jeśli wciąż Supercell)
    if bucket_after_v2 == "Supercell":
        MIN_RATING = 7.5
        MIN_PPD = 1.3
        MIN_3RD = 12.0  # pp
        MIN_EXPL = 5.0  # pp
        MIN_RZ = 22.0   # %

        reasons = []
        if notes:
            reasons.append("Guardrails notes present -> Supercell not clean")
        if rating_adj < MIN_RATING:
            reasons.append(f"Rating {rating_adj:.2f} < {MIN_RATING}")
        ppd = gap("points_per_drive_off_avg")
        if ppd is not None and ppd < MIN_PPD:
            reasons.append(f"PPD diff {ppd:.2f} < {MIN_PPD}")
        td_gap = gap("third_down_conv_off_avg")
        if td_gap is not None and td_gap * 100.0 < MIN_3RD:
            reasons.append(f"3rd down gap {td_gap*100:.1f} pp < {MIN_3RD} pp")
        expl_gap = gap("explosive_play_rate_off_avg")
        if expl_gap is not None and expl_gap * 100.0 < MIN_EXPL:
            reasons.append(f"Explosive gap {expl_gap*100:.1f} pp < {MIN_EXPL} pp")
        try:
            rz_off = float(last3.get(f"redzone_td_rate_off_avg_{fav}", math.nan)) * 100.0
        except (TypeError, ValueError):
            rz_off = math.nan
        if not math.isnan(rz_off) and rz_off < MIN_RZ:
            reasons.append(f"Red zone {rz_off:.1f}% < {MIN_RZ}%")

        if reasons:
            # degrade to Vortex
            bucket_after_v2 = "Vortex"
            notes.extend(reasons)
            level = max(level, 2)

    # Jeżeli po degradacji jest Vortex, ale wcześniejsze poziomy blokują Vortex w v2 (level 3), zostaje Cyclone
    if bucket_after_v2 == "Vortex" and level >= 3:
        bucket_after_v2 = "Cyclone"

    return rating_adj, bucket_after_v2, notes, level


# === Rail Guard value buffer (model vs spread) =================================

VALUE_BUFFER_BUCKET_ORDER = [
    "Calm",
    "Breeze",
    "Gale",
    "Cyclone",
    "Vortex",
    "Supercell",
    "Ultimate Supercell",
]


def apply_value_buffer_guard(
    *,
    predicted_margin: Optional[float],
    spread: Optional[float],
    original_bucket: str,
    guardrail_level: int = 0,
) -> tuple[str, Optional[float], str, str, str]:
    """
    Zwraca: (guard_bucket, value_buffer, rail_guard_status, rail_guard_action, notes)

    v2.2 zasady:
      - |buffer| < 3 -> neutral
      - BOOST wyłącznie Calm/Breeze, sufit = Gale (nigdy nie awansuje do Cyclone/Vortex/Supercell/Ultimate)
        * +5..+9 -> +1 (do max Gale)
        * >= +10 -> +2 (do max Gale)
      - Ujemne progi:
        * <= -10: -2 tier dla Cyclone/Vortex/Supercell/Ultimate, inaczej -1
        * -5..-9: -1 tier
        * -3..-4: -1 tylko jeśli start = Vortex/Supercell/Ultimate (wysoki bucket)
      - Guardrail level >=2 i buffer <0 -> wymuś co najmniej -1 (nie sumuj podwójnie)
    """
    if predicted_margin is None or spread is None:
        return original_bucket, None, "SKIP", "NO_CHANGE", "Brak danych margin/spread"
    notes_parts: list[str] = []
    try:
        value_buffer = float(predicted_margin) - float(spread)
    except (TypeError, ValueError):
        return original_bucket, None, "SKIP", "NO_CHANGE", "Nieprawidłowe margin/spread"

    try:
        idx = VALUE_BUFFER_BUCKET_ORDER.index(original_bucket)
    except ValueError:
        # Jeśli bucket nieznany, nie zmieniamy
        return original_bucket, value_buffer, "PASS", "NO_CHANGE", "; ".join(notes_parts)

    delta = 0
    gale_idx = VALUE_BUFFER_BUCKET_ORDER.index("Gale")

    # Strefa neutralna
    if abs(value_buffer) < 3.0:
        delta = 0
        notes_parts.append("v2.2: |buffer|<3 neutral")
    else:
        if value_buffer >= 10.0:
            if original_bucket in ("Calm", "Breeze"):
                delta = min(2, gale_idx - idx)
                notes_parts.append("v2.2: buffer>=10, boost cap=Gale")
            else:
                delta = 0
                notes_parts.append("v2.2: buffer>=10 but boost blocked (>=Gale)")
        elif value_buffer >= 5.0:
            if original_bucket in ("Calm", "Breeze"):
                delta = min(1, gale_idx - idx)
                notes_parts.append("v2.2: buffer 5-9, +1 cap=Gale")
            else:
                delta = 0
                notes_parts.append("v2.2: buffer 5-9 but boost blocked (>=Gale)")
        elif value_buffer <= -10.0:
            if original_bucket in ("Cyclone", "Vortex", "Supercell", "Ultimate Supercell"):
                delta = -2
                notes_parts.append("v2.2: buffer<=-10, -2 for high bucket")
            else:
                delta = -1
                notes_parts.append("v2.2: buffer<=-10, -1 for low bucket")
        elif value_buffer <= -5.0:
            delta = -1
            notes_parts.append("v2.2: buffer -5..-9, -1")
        elif value_buffer <= -3.0:
            if original_bucket in ("Vortex", "Supercell", "Ultimate Supercell"):
                delta = -1
                notes_parts.append("v2.2: buffer -3..-4, -1 for high bucket")
            else:
                delta = 0
                notes_parts.append("v2.2: buffer -3..-4, neutral for low bucket")

    # Guardrail level bezpiecznik (nie sumujemy podwójnie)
    if guardrail_level >= 2 and value_buffer < 0:
        if delta == 0:
            delta = -1
            notes_parts.append("v2.2: guardrail_level>=2, force -1")
        else:
            delta = min(delta, -1)  # zostawia -2, nie dodaje kolejnego -1
            notes_parts.append("v2.2: guardrail_level>=2, min -1 applied")

    new_idx = max(0, min(len(VALUE_BUFFER_BUCKET_ORDER) - 1, idx + delta))
    # Blok awansu powyżej Gale
    if new_idx > gale_idx and new_idx > idx:
        new_idx = idx  # nie awansujemy ponad Gale
        delta = 0
        notes_parts.append("v2.2: cap=Gale, boost blocked")

    guard_bucket = VALUE_BUFFER_BUCKET_ORDER[new_idx]

    if guard_bucket != original_bucket:
        if new_idx > idx:
            status = "BOOST"
            action = f"PROMOTE TO {guard_bucket.upper()}"
        else:
            status = "DOWNGRADE"
            action = f"DOWNGRADE TO {guard_bucket.upper()}"
    else:
        status = "PASS"
        action = "NO_CHANGE"

    notes = "; ".join(notes_parts)
    return guard_bucket, value_buffer, status, action, notes
