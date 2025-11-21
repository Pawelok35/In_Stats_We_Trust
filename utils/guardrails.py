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
