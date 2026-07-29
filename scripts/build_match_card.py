from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd
import polars as pl
import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from metrics.form_windows import compute_form_windows


def _load_week_lines(season: int, week: int) -> dict:
    path = Path(f"config/lines/{season}/week{week}_lines.yaml")
    if not path.exists():
        raise FileNotFoundError(f"Missing lines file: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _find_line_matchup(lines_cfg: dict, home: str, away: str) -> dict:
    for matchup in lines_cfg.get("matchups", []):
        if matchup.get("home") == home and matchup.get("away") == away:
            return matchup
    raise ValueError(f"Matchup {away} @ {home} not found in lines config")


def _load_variant_rows(season: int, week: int, home: str, away: str) -> List[dict]:
    variants = [
        ("B", Path(f"data/picks_variant_b_edge_focus/{season}/week_{week:02d}.jsonl")),
        ("F", Path(f"data/picks_variant_f/{season}/week_{week:02d}.jsonl")),
        ("D", Path(f"data/picks_variant_d_balanced/{season}/week_{week:02d}.jsonl")),
    ]
    rows: List[dict] = []
    for name, path in variants:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("home") == home and row.get("away") == away:
                row["variant"] = name
                rows.append(row)
    if not rows:
        raise ValueError(
            f"No pick variants found for {away} @ {home}, season={season}, week={week}"
        )
    return rows


def _load_weather_row(season: int, week: int, home: str, away: str) -> Optional[dict]:
    path = Path(f"data/results/weather_bucket_games_season{season}.csv")
    if not path.exists():
        return None
    df = pd.read_csv(path)
    mask = (df["week"] == week) & (df["home_team"] == home) & (df["away_team"] == away)
    if not mask.any():
        return None
    return df[mask].iloc[0].to_dict()


def _parse_report_win_probs(
    report_path: str, home: str, away: str
) -> tuple[Optional[float], Optional[float]]:
    path = Path(report_path)
    if not path.exists():
        return None, None
    text = path.read_text(encoding="utf-8")
    home_match = re.search(rf"\|\s*Model Win% {re.escape(home)}\s*\|\s*([0-9.]+)%\s*\|", text)
    away_match = re.search(rf"\|\s*Model Win% {re.escape(away)}\s*\|\s*([0-9.]+)%\s*\|", text)
    home_wp = float(home_match.group(1)) if home_match else None
    away_wp = float(away_match.group(1)) if away_match else None
    return home_wp, away_wp


def _fmt_pct(v: Optional[float]) -> str:
    return "n/a" if v is None else f"{v:.1f}%"


def _fmt_num(v: Optional[float], digits: int = 1) -> str:
    return "n/a" if v is None else f"{v:.{digits}f}"


def _fmt_spread(v: Optional[float]) -> str:
    if v is None:
        return "n/a"
    val = _round_to_half(float(v))
    if float(val).is_integer():
        txt = f"{int(val)}"
    else:
        txt = f"{val:.1f}"
    return txt if txt.startswith("-") else f"+{txt}"


def _to_float(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _diff_or_none(left: Any, right: Any) -> Optional[float]:
    left_value = _to_float(left)
    right_value = _to_float(right)
    if left_value is None or right_value is None:
        return None
    return left_value - right_value


def _round_to_half(v: float) -> float:
    return round(v * 2.0) / 2.0


def _load_team_row(path: Path, team: str) -> dict:
    if not path.exists():
        return {}
    df = pl.read_parquet(path)
    key_col = "TEAM" if "TEAM" in df.columns else "team"
    row = df.filter(pl.col(key_col) == team)
    if row.height == 0:
        return {}
    return row.to_dicts()[0]


def _form_rows(season: int, week: int, home: str, away: str) -> tuple[dict, dict]:
    df = compute_form_windows(season=season, current_week=week, teams=[home, away])
    last3 = df.filter(pl.col("window") == "last 3 games")
    last5 = df.filter(pl.col("window") == "last 5 games")
    return (
        last3.to_dicts()[0] if last3.height else {},
        last5.to_dicts()[0] if last5.height else {},
    )


def _delta(form3: dict, form5: dict, field: str, team: str) -> Optional[float]:
    k = f"{field}_{team}"
    a = _to_float(form3.get(k))
    b = _to_float(form5.get(k))
    if a is None or b is None:
        return None
    return a - b


def _scenario_rows(
    home: str,
    away: str,
    baseline_wp_home: Optional[float],
    baseline_spread_home: float,
    baseline_total: float,
) -> List[dict]:
    wp = baseline_wp_home if baseline_wp_home is not None else 55.0
    return [
        {
            "name": "Baseline",
            "wp_home": wp,
            "spread_home": _round_to_half(baseline_spread_home),
            "total": baseline_total,
            "note": "-",
        },
        {
            "name": "QB Limited",
            "wp_home": max(0.0, wp - 3.0),
            "spread_home": _round_to_half(baseline_spread_home + 1.5),
            "total": baseline_total - 2.0,
            "note": "Moderate drop",
        },
        {
            "name": "QB Out",
            "wp_home": max(0.0, wp - 8.0),
            "spread_home": _round_to_half(baseline_spread_home + 4.0),
            "total": baseline_total - 4.5,
            "note": "Major swing",
        },
        {
            "name": "High Wind",
            "wp_home": max(0.0, wp - 1.0),
            "spread_home": _round_to_half(baseline_spread_home + 0.5),
            "total": baseline_total - 4.0,
            "note": "Total down sharply",
        },
        {
            "name": "Slow Pace",
            "wp_home": max(0.0, wp - 1.5),
            "spread_home": _round_to_half(baseline_spread_home + 0.5),
            "total": baseline_total - 2.0,
            "note": "Lower possession count",
        },
    ]


def _decision_label(
    value_buffer: Optional[float], guardrail_level: Optional[int], fragility_score: int
) -> str:
    vb = value_buffer if value_buffer is not None else -999.0
    gl = guardrail_level if guardrail_level is not None else 3
    if vb >= 5 and gl <= 1 and fragility_score <= 35:
        return "Strong"
    if vb >= 2 and gl <= 2 and fragility_score <= 60:
        return "Tradable"
    if vb >= 0:
        return "Fragile"
    return "Pass"


def _build_markdown(
    *,
    season: int,
    week: int,
    home: str,
    away: str,
    line_row: dict,
    baseline: dict,
    market: dict,
    top_drivers: List[str],
    scenarios: List[dict],
    powerscore: dict,
    weather: dict,
    form: dict,
    injury_rows: List[dict],
    fragility_score: int,
    fragility_label: str,
    decision: str,
    summary: str,
) -> str:
    scenario_lines = "\n".join(
        [
            f"| {r['name']} | {r['wp_home']:.1f}% {home} | {_fmt_spread(r['spread_home'])} | {r['total']:.1f} | {r['note']} |"
            for r in scenarios
        ]
    )
    driver_lines = "\n".join([f"- {d}" for d in top_drivers])
    injury_table = "\n".join(
        [f"| {r['label']} | {r['spread']:+.1f} | {r['total']:+.1f} |" for r in injury_rows]
    )
    return f"""# Match Card: {away} @ {home} (Season {season}, Week {week})

## 1) Match Overview
- Teams: **{away} @ {home}**
- Week: **{week}**
- Kickoff: **n/a in current dataset**
- Venue: **Outdoor (from lines config context)**
- Market lines snapshot (current):
  - Spread: **{_fmt_spread(market['spread_home'])}**
  - Total: **{market['total']:.1f}**

## 2) Baseline Model
- Home Win Probability: **{_fmt_pct(baseline['home_wp'])}**
- Away Win Probability: **{_fmt_pct(baseline['away_wp'])}**
- Fair Spread (home): **{_fmt_spread(baseline['fair_spread_home'])}**
- Fair Total: **{baseline['fair_total']:.1f}**
- Expected score (implied): **{home} {baseline['exp_home']:.1f} - {away} {baseline['exp_away']:.1f}**

## 3) Model vs Market
- Final Market Spread (home): **{_fmt_spread(market['spread_home'])}**
- Spread Edge (model - market): **{_fmt_spread(market['spread_edge'])}**
- Final Market Total: **{market['total']:.1f}**
- Total Edge (model - market): **{market['total_edge']:+.1f}**
- Value Buffer: **{_fmt_num(weather.get('value_buffer'), 1)}**
- Guardrail: **level {weather.get('guardrail_level', 'n/a')}** ({weather.get('bucket', 'n/a')})

## 4) Top Drivers
{driver_lines}

## 5) Scenario Table
| Scenario | Win Prob | Fair Spread (home) | Fair Total | Shift vs Baseline |
|---|---:|---:|---:|---|
{scenario_lines}

## 6) Summary
{summary}

## 7) Form Trend (Last 3 vs Last 5)
| Metric | {home} d(Last3-Last5) | {away} d(Last3-Last5) |
|---|---:|---:|
| EPA Off | {form['home_epa_off_delta']:+.3f} | {form['away_epa_off_delta']:+.3f} |
| Success Rate Off | {form['home_sr_off_delta']:+.3%} | {form['away_sr_off_delta']:+.3%} |
| Tempo | {form['home_tempo_delta']:+.2f} | {form['away_tempo_delta']:+.2f} |

## 8) PowerScore Diff + Components
- Internal PowerScore Diff ({home}-{away}): **{powerscore['diff']:+.3f}**
- Main components:
  - QB efficiency (EPA off delta): **{powerscore['qb_eff']:+.3f}**
  - Pass rush edge (pressure rate def delta): **{powerscore['pass_rush']:+.3%}**
  - Opp-adjusted offense (SR off delta): **{powerscore['sr_off']:+.3%}**

## 9) Stability / Fragility Score
- Score: **{fragility_score}/100**
- Label: **{fragility_label}**
- Inputs: value buffer, scenario spread shift, scenario total shift, guardrail level.

## 10) Injury / Availability Impact
| Scenario | Spread shift | Total shift |
|---|---:|---:|
{injury_table}

## 11) Weather Impact Block
- Bucket: **{weather.get('bucket', 'n/a')}**
- Rating: **{_fmt_num(weather.get('rating'), 2)}**
- Guardrail Notes: **{weather.get('guardrail_notes', 'n/a')}**
- Rail Guard: **{weather.get('rail_guard_status', 'n/a')} / {weather.get('rail_guard_action', 'n/a')}**

## 12) Decision Rules
- Final Label: **{decision}**
- Rule basis: value buffer + guardrail level + fragility score.

## 13) Guardrails Explained
- Guardrail level:
  - **0**: no guardrail (brak ostrzeżeń)
  - **1**: soft warning (lekki sygnał ryzyka)
  - **2**: downgraded supercell (sygnał został obniżony przez guardrails)
  - **3**: downgraded vortex (silne ryzyko, wysoka ostrożność)
- Current level for this game: **{weather.get('guardrail_level', 'n/a')}**
- How to read notes:
  - `PPD diff last3 too low`: przewaga punktów/drive w krótkim oknie jest za słaba.
  - `Explosive gap too low`: przewaga big-play jest za mała lub negatywna.
  - `Red zone TD too low`: skuteczność kończenia drive'ów jest za niska.
  - `Def EPA trending worse`: obrona pogarsza trend vs dłuższe okno.
- Raw notes: **{weather.get('guardrail_notes', 'n/a')}**
"""


def _build_one_card(
    season: int, week: int, home: str, away: str, output: Optional[Path] = None
) -> Path:
    lines_cfg = _load_week_lines(season, week)
    line_row = _find_line_matchup(lines_cfg, home, away)
    variants = _load_variant_rows(season, week, home, away)
    weather_row = _load_weather_row(season, week, home, away) or {}

    base_b = next((r for r in variants if r.get("variant") == "B"), variants[0])
    model_margin = float(base_b.get("model_margin"))
    model_winner = str(base_b.get("model_winner"))
    fair_spread_home = _round_to_half(-model_margin if model_winner == home else model_margin)
    fair_total = float(base_b.get("total"))
    market_spread_home = _round_to_half(float(line_row.get("spread")))
    market_total = float(line_row.get("total"))
    home_wp, away_wp = _parse_report_win_probs(base_b.get("report", ""), home, away)

    exp_home = (
        (fair_total + model_margin) / 2.0
        if model_winner == home
        else (fair_total - model_margin) / 2.0
    )
    exp_away = fair_total - exp_home

    baseline = {
        "home_wp": home_wp,
        "away_wp": away_wp,
        "fair_spread_home": fair_spread_home,
        "fair_total": fair_total,
        "exp_home": exp_home,
        "exp_away": exp_away,
    }

    market = {
        "spread_home": market_spread_home,
        "total": market_total,
        "spread_edge": fair_spread_home - market_spread_home,
        "total_edge": fair_total - market_total,
    }

    through_week = max(1, week - 1)
    rolling_path = Path(f"data/rolling_core12/{season}/through_{through_week}.parquet")
    ps_path = Path(f"data/l4_powerscore/{season}/{through_week}.parquet")
    form3, form5 = _form_rows(season, week, home, away)
    home_roll = _load_team_row(rolling_path, home)
    away_roll = _load_team_row(rolling_path, away)
    home_ps = _load_team_row(ps_path, home)
    away_ps = _load_team_row(ps_path, away)

    driver_candidates = [
        f"Model margin: {model_winner} by {model_margin:.1f} (vs market {_fmt_spread(market_spread_home)})",
        f"Weather bucket: {weather_row.get('bucket', 'n/a')} (rating {_fmt_num(_to_float(weather_row.get('rating')), 2)})",
        f"Value buffer: {_fmt_num(_to_float(weather_row.get('value_buffer')), 1)}",
        f"Third-down edge ({home}-{away}): {_fmt_num(_diff_or_none(home_roll.get('core_third_down_conv'), away_roll.get('core_third_down_conv')), 3)}",
        f"Turnover margin edge ({home}-{away}): {_fmt_num(_diff_or_none(home_roll.get('core_turnover_margin'), away_roll.get('core_turnover_margin')), 3)}",
    ]
    top_drivers = driver_candidates[:5]

    scenarios = _scenario_rows(home, away, home_wp, fair_spread_home, fair_total)
    spread_swing = max(abs(r["spread_home"] - fair_spread_home) for r in scenarios[1:])
    total_swing = max(abs(r["total"] - fair_total) for r in scenarios[1:])
    value_buffer = _to_float(weather_row.get("value_buffer"))
    guardrail_level = (
        int(weather_row.get("guardrail_level"))
        if str(weather_row.get("guardrail_level", "")).isdigit()
        else 3
    )
    vb_penalty = (
        0
        if value_buffer is not None and value_buffer >= 5
        else (20 if value_buffer is not None and value_buffer >= 2 else 35)
    )
    fragility_score = int(
        min(100, 15 * spread_swing + 4 * total_swing + 10 * guardrail_level + vb_penalty)
    )
    fragility_label = (
        "Stable"
        if fragility_score <= 35
        else (
            "Tradable"
            if fragility_score <= 60
            else "Fragile" if fragility_score <= 80 else "Very Fragile"
        )
    )
    decision = _decision_label(value_buffer, guardrail_level, fragility_score)

    injury_rows = [
        {"label": "QB limited", "spread": +1.5, "total": -2.0},
        {"label": "QB out", "spread": +4.0, "total": -4.5},
        {"label": "Weather stress", "spread": +0.5, "total": -4.0},
    ]

    powerscore = {
        "diff": _diff_or_none(home_ps.get("power_score"), away_ps.get("power_score")),
        "qb_eff": _diff_or_none(home_roll.get("core_epa_off"), away_roll.get("core_epa_off")),
        "pass_rush": _diff_or_none(
            home_roll.get("core_pressure_rate_def"),
            away_roll.get("core_pressure_rate_def"),
        ),
        "sr_off": _diff_or_none(home_roll.get("core_sr_off"), away_roll.get("core_sr_off")),
    }

    form = {
        "home_epa_off_delta": _delta(form3, form5, "epa_off_mean_avg", home),
        "away_epa_off_delta": _delta(form3, form5, "epa_off_mean_avg", away),
        "home_sr_off_delta": _delta(form3, form5, "success_rate_off_avg", home),
        "away_sr_off_delta": _delta(form3, form5, "success_rate_off_avg", away),
        "home_tempo_delta": _delta(form3, form5, "tempo_avg", home),
        "away_tempo_delta": _delta(form3, form5, "tempo_avg", away),
    }

    summary = (
        f"Baseline gives {home} an edge ({_fmt_spread(fair_spread_home)} vs market {_fmt_spread(market_spread_home)}), "
        f"with value buffer {_fmt_num(value_buffer, 1)} and bucket {weather_row.get('bucket', 'n/a')}. "
        f"Fragility score is {fragility_score}/100 ({fragility_label}), so decision is **{decision}**."
    )

    markdown = _build_markdown(
        season=season,
        week=week,
        home=home,
        away=away,
        line_row=line_row,
        baseline=baseline,
        market=market,
        top_drivers=top_drivers,
        scenarios=scenarios,
        powerscore=powerscore,
        weather=weather_row,
        form=form,
        injury_rows=injury_rows,
        fragility_score=fragility_score,
        fragility_label=fragility_label,
        decision=decision,
        summary=summary,
    )

    if output is None:
        out = Path(f"data/reports/match_cards/{season}_w{week}_{away}_at_{home}.md")
    else:
        out = output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build automated match cards from existing pipeline artifacts."
    )
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument("--home", type=str, help="Home team code (e.g. CHI)")
    parser.add_argument("--away", type=str, help="Away team code (e.g. CLE)")
    parser.add_argument(
        "--all-week",
        action="store_true",
        help="Generate cards for all matchups from config/lines/{season}/week{week}_lines.yaml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path (.md) for single-game mode.",
    )
    args = parser.parse_args()

    season = args.season
    week = args.week

    if args.all_week:
        lines_cfg = _load_week_lines(season, week)
        matchups = lines_cfg.get("matchups", [])
        if not matchups:
            raise SystemExit("No matchups found in lines config.")
        saved: List[Path] = []
        for m in matchups:
            home = str(m.get("home", "")).upper()
            away = str(m.get("away", "")).upper()
            if not home or not away:
                continue
            out = _build_one_card(season, week, home, away, output=None)
            saved.append(out)
        print(f"Saved {len(saved)} match cards for season={season} week={week}")
        return

    if not args.home or not args.away:
        raise SystemExit("Single-game mode requires --home and --away (or use --all-week).")

    home = args.home.upper()
    away = args.away.upper()
    out = _build_one_card(season, week, home, away, output=args.output)
    print(f"Saved match card: {out}")


if __name__ == "__main__":
    main()
