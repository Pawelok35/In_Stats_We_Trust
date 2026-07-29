from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import plotly.graph_objects as go
import polars as pl
import streamlit as st
import yaml

from metrics.form_windows import compute_form_windows

ROOT = Path(__file__).resolve().parents[1]


def _to_float(v: Any) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _round_to_half(v: float) -> float:
    return round(v * 2.0) / 2.0


def _fmt_spread(v: float) -> str:
    val = _round_to_half(float(v))
    txt = f"{int(val)}" if float(val).is_integer() else f"{val:.1f}"
    return txt if txt.startswith("-") else f"+{txt}"


def _weather_path(season: int, profile: str) -> Path:
    if profile == "robust":
        return ROOT / f"data/results/weather_bucket_games_season{season}_robust.csv"
    if profile == "robust_v2":
        return ROOT / f"data/results/weather_bucket_games_season{season}_robust_v2.csv"
    return ROOT / f"data/results/weather_bucket_games_season{season}.csv"


def _load_week_lines(season: int, week: int) -> dict:
    p = ROOT / f"config/lines/{season}/week{week}_lines.yaml"
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _matchups_for_week(season: int, week: int) -> list[tuple[str, str]]:
    cfg = _load_week_lines(season, week)
    out: list[tuple[str, str]] = []
    for m in cfg.get("matchups", []):
        home = str(m.get("home", "")).upper()
        away = str(m.get("away", "")).upper()
        if home and away:
            out.append((away, home))
    return out


def _find_line_row(season: int, week: int, home: str, away: str) -> dict:
    cfg = _load_week_lines(season, week)
    for m in cfg.get("matchups", []):
        if str(m.get("home", "")).upper() == home and str(m.get("away", "")).upper() == away:
            return m
    return {}


def _load_variant_row(season: int, week: int, home: str, away: str, variant: str) -> Optional[dict]:
    path_map = {
        "B": ROOT / f"data/picks_variant_b_edge_focus/{season}/week_{week:02d}.jsonl",
        "F": ROOT / f"data/picks_variant_f/{season}/week_{week:02d}.jsonl",
        "D": ROOT / f"data/picks_variant_d_balanced/{season}/week_{week:02d}.jsonl",
    }
    p = path_map[variant]
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("home") == home and row.get("away") == away:
            row["variant"] = variant
            return row
    return None


def _load_weather_row(season: int, week: int, home: str, away: str, profile: str) -> dict:
    p = _weather_path(season, profile)
    if not p.exists():
        return {}
    df = pd.read_csv(p)
    mask = (df["week"] == week) & (df["home_team"] == home) & (df["away_team"] == away)
    if not mask.any():
        return {}
    return df[mask].iloc[0].to_dict()


def _parse_report_win_probs(
    report_path: str, home: str, away: str
) -> tuple[Optional[float], Optional[float]]:
    p = ROOT / report_path.replace("\\", "/")
    if not p.exists():
        return None, None
    txt = p.read_text(encoding="utf-8", errors="ignore")
    hm = re.search(rf"\|\s*Model Win% {re.escape(home)}\s*\|\s*([0-9.]+)%\s*\|", txt)
    am = re.search(rf"\|\s*Model Win% {re.escape(away)}\s*\|\s*([0-9.]+)%\s*\|", txt)
    return (float(hm.group(1)) if hm else None, float(am.group(1)) if am else None)


def _load_team_row(path: Path, team: str) -> dict:
    if not path.exists():
        return {}
    df = pl.read_parquet(path)
    key = "TEAM" if "TEAM" in df.columns else ("team" if "team" in df.columns else None)
    if key is None:
        return {}
    row = df.filter(pl.col(key) == team)
    return row.to_dicts()[0] if row.height else {}


def _delta(form3: dict, form5: dict, field: str, team: str) -> float:
    a = _to_float(form3.get(f"{field}_{team}"))
    b = _to_float(form5.get(f"{field}_{team}"))
    return (a - b) if (a is not None and b is not None) else 0.0


def _fragility_label(score: int) -> str:
    if score <= 35:
        return "Stable"
    if score <= 60:
        return "Tradable"
    if score <= 80:
        return "Fragile"
    return "Very Fragile"


def _decision(value_buffer: Optional[float], guardrail_level: int, fragility_score: int) -> str:
    vb = value_buffer if value_buffer is not None else -999.0
    if vb >= 5 and guardrail_level <= 1 and fragility_score <= 35:
        return "Strong"
    if vb >= 2 and guardrail_level <= 2 and fragility_score <= 60:
        return "Tradable"
    if vb >= 0:
        return "Fragile"
    return "Pass"


def _scenario_df(base_wp_home: float, base_spread_home: float, base_total: float) -> pd.DataFrame:
    s = _round_to_half(base_spread_home)
    rows = [
        ("Baseline", base_wp_home, s, base_total, "-"),
        (
            "QB Limited",
            max(0.0, base_wp_home - 3.0),
            _round_to_half(s + 1.5),
            base_total - 2.0,
            "Moderate drop",
        ),
        (
            "QB Out",
            max(0.0, base_wp_home - 8.0),
            _round_to_half(s + 4.0),
            base_total - 4.5,
            "Major swing",
        ),
        (
            "High Wind",
            max(0.0, base_wp_home - 1.0),
            _round_to_half(s + 0.5),
            base_total - 4.0,
            "Total down sharply",
        ),
        (
            "Slow Pace",
            max(0.0, base_wp_home - 1.5),
            _round_to_half(s + 0.5),
            base_total - 2.0,
            "Lower possession count",
        ),
    ]
    return pd.DataFrame(
        rows, columns=["Scenario", "Win Prob", "Fair Spread", "Fair Total", "Shift"]
    )


def build_payload(season: int, week: int, away: str, home: str, profile: str) -> dict:
    line = _find_line_row(season, week, home, away)
    v_b = _load_variant_row(season, week, home, away, "B")
    if v_b is None:
        raise ValueError("Missing variant B pick for matchup.")
    weather = _load_weather_row(season, week, home, away, profile)

    model_margin = float(v_b["model_margin"])
    model_winner = str(v_b["model_winner"])
    fair_spread_home = _round_to_half(-model_margin if model_winner == home else model_margin)
    fair_total = float(v_b["total"])
    market_spread_raw = _to_float(line.get("spread"))
    if market_spread_raw is None:
        market_spread_raw = _to_float(v_b.get("spread")) or 0.0
    market_spread = _round_to_half(market_spread_raw)
    market_total = _to_float(line.get("total")) or fair_total

    home_wp, away_wp = _parse_report_win_probs(str(v_b.get("report", "")), home, away)
    if home_wp is None:
        home_wp = 50.0 + (model_margin * 1.25)
    if away_wp is None:
        away_wp = 100.0 - home_wp

    through = max(1, week - 1)
    roll = ROOT / f"data/rolling_core12/{season}/through_{through}.parquet"
    ps = ROOT / f"data/l4_powerscore/{season}/{through}.parquet"
    home_roll = _load_team_row(roll, home)
    away_roll = _load_team_row(roll, away)
    home_ps = _load_team_row(ps, home)
    away_ps = _load_team_row(ps, away)

    form = compute_form_windows(season=season, current_week=week, teams=[home, away])
    last3 = form.filter(pl.col("window") == "last 3 games")
    last5 = form.filter(pl.col("window") == "last 5 games")
    f3 = last3.to_dicts()[0] if last3.height else {}
    f5 = last5.to_dicts()[0] if last5.height else {}

    scenario = _scenario_df(home_wp, fair_spread_home, fair_total)
    spread_swing = float((scenario["Fair Spread"] - fair_spread_home).abs().iloc[1:].max())
    total_swing = float((scenario["Fair Total"] - fair_total).abs().iloc[1:].max())
    vb = _to_float(weather.get("value_buffer"))
    gl_raw = weather.get("guardrail_level", 3)
    gl = int(gl_raw) if str(gl_raw).isdigit() else 3
    vb_penalty = 0 if vb is not None and vb >= 5 else (20 if vb is not None and vb >= 2 else 35)
    fragility_score = int(min(100, 15 * spread_swing + 4 * total_swing + 10 * gl + vb_penalty))

    return {
        "season": season,
        "week": week,
        "away": away,
        "home": home,
        "market_spread": market_spread,
        "market_total": market_total,
        "fair_spread": fair_spread_home,
        "fair_total": fair_total,
        "home_wp": home_wp,
        "away_wp": away_wp,
        "model_margin": model_margin,
        "value_buffer": vb,
        "bucket": weather.get("bucket", "n/a"),
        "guardrail_level": gl,
        "guardrail_notes": str(weather.get("guardrail_notes", "")),
        "scenario": scenario,
        "power_diff": (_to_float(home_ps.get("power_score")) or 0.0)
        - (_to_float(away_ps.get("power_score")) or 0.0),
        "epa_off_delta": (_to_float(home_roll.get("core_epa_off")) or 0.0)
        - (_to_float(away_roll.get("core_epa_off")) or 0.0),
        "sr_off_delta": (_to_float(home_roll.get("core_sr_off")) or 0.0)
        - (_to_float(away_roll.get("core_sr_off")) or 0.0),
        "pressure_delta": (_to_float(home_roll.get("core_pressure_rate_def")) or 0.0)
        - (_to_float(away_roll.get("core_pressure_rate_def")) or 0.0),
        "third_down_delta": (_to_float(home_roll.get("core_third_down_conv")) or 0.0)
        - (_to_float(away_roll.get("core_third_down_conv")) or 0.0),
        "to_delta": (_to_float(home_roll.get("core_turnover_margin")) or 0.0)
        - (_to_float(away_roll.get("core_turnover_margin")) or 0.0),
        "form_epa_home": _delta(f3, f5, "epa_off_mean_avg", home),
        "form_epa_away": _delta(f3, f5, "epa_off_mean_avg", away),
        "form_sr_home": _delta(f3, f5, "success_rate_off_avg", home),
        "form_sr_away": _delta(f3, f5, "success_rate_off_avg", away),
        "form_tempo_home": _delta(f3, f5, "tempo_avg", home),
        "form_tempo_away": _delta(f3, f5, "tempo_avg", away),
        "fragility_score": fragility_score,
        "fragility_label": _fragility_label(fragility_score),
        "decision": _decision(vb, gl, fragility_score),
    }


def _kpi_card(title: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-title">{title}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _panel_title(title: str) -> None:
    st.markdown(f"<div class='panel-title'>{title}</div>", unsafe_allow_html=True)


def _decision_badges(current: str) -> str:
    labels = ["Strong", "Tradable", "Fragile", "Pass"]
    html = []
    for lbl in labels:
        cls = "decision-badge active" if lbl == current else "decision-badge"
        html.append(f"<span class='{cls} {lbl.lower()}'>{lbl}</span>")
    return " ".join(html)


def main() -> None:
    st.set_page_config(page_title="Match Card Dashboard", layout="wide")
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(1200px 600px at 10% 5%, #1f3554 0%, #0d1624 38%, #090f19 100%);
            color: #e8edf5;
            font-family: "Segoe UI", Tahoma, sans-serif;
        }
        .top-strip {
            background: linear-gradient(180deg, rgba(255,255,255,0.09), rgba(255,255,255,0.04));
            border: 1px solid rgba(186, 212, 255, 0.24);
            border-radius: 14px;
            padding: 12px 14px;
            box-shadow: 0 10px 28px rgba(0,0,0,0.35);
            margin-bottom: 12px;
        }
        .top-title {
            font-size: 20px;
            font-weight: 800;
            letter-spacing: 0.3px;
            text-transform: uppercase;
            color: #f3f7ff;
            margin-bottom: 8px;
        }
        .chip-row { display: flex; flex-wrap: wrap; gap: 10px; }
        .chip {
            background: rgba(11, 24, 42, 0.7);
            border: 1px solid rgba(161, 196, 255, 0.24);
            border-radius: 10px;
            padding: 7px 10px;
            min-width: 130px;
        }
        .chip-label { font-size: 11px; color: #b9c9de; text-transform: uppercase; }
        .chip-value { font-size: 19px; font-weight: 800; line-height: 1.1; color: #f6fbff; }
        .panel-title {
            background: linear-gradient(90deg, rgba(198,220,255,0.22), rgba(198,220,255,0.06));
            border: 1px solid rgba(161, 196, 255, 0.24);
            border-radius: 11px;
            padding: 8px 11px;
            margin: 4px 0 8px 0;
            text-transform: uppercase;
            font-size: 21px;
            font-weight: 800;
            letter-spacing: 0.2px;
            color: #eff6ff;
        }
        .kpi-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.04));
            border: 1px solid rgba(186, 212, 255, 0.22);
            border-radius: 12px;
            padding: 12px 14px;
            min-height: 108px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.25);
        }
        .kpi-title { font-size: 11px; opacity: .88; text-transform: uppercase; color: #c7d6ea; }
        .kpi-value { font-size: 33px; font-weight: 800; line-height: 1.05; margin-top: 4px; color: #f9fcff; }
        .kpi-caption { font-size: 12px; opacity: .86; margin-top: 6px; color: #dce8f7; }
        .decision-badge {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 9px;
            margin-right: 6px;
            font-size: 12px;
            border: 1px solid rgba(255,255,255,0.20);
            color: #d7e3f3;
            background: rgba(255,255,255,0.06);
        }
        .decision-badge.active.strong { background: rgba(22, 101, 52, 0.88); color: #f4fff7; }
        .decision-badge.active.tradable { background: rgba(2, 132, 199, 0.82); color: #f1fbff; }
        .decision-badge.active.fragile { background: rgba(180, 83, 9, 0.86); color: #fff8ef; }
        .decision-badge.active.pass { background: rgba(161, 98, 7, 0.88); color: #fff8e7; }
        .summary-box {
            background: linear-gradient(180deg, rgba(255,255,255,0.09), rgba(255,255,255,0.03));
            border: 1px solid rgba(186, 212, 255, 0.2);
            border-radius: 12px;
            padding: 11px 13px;
            margin-top: 6px;
        }
        div[data-testid="stDataFrame"] {
            background: rgba(12,24,39,0.68);
            border: 1px solid rgba(161, 196, 255, 0.16);
            border-radius: 10px;
            padding: 3px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("## Match Card Dashboard")

    seasons = sorted(
        {
            int(
                p.stem.replace("weather_bucket_games_season", "")
                .replace("_robust_v2", "")
                .replace("_robust", "")
            )
            for p in (ROOT / "data/results").glob("weather_bucket_games_season*.csv")
            if any(ch.isdigit() for ch in p.stem)
        }
    )
    if not seasons:
        st.error("No weather bucket files found in data/results.")
        return

    default_season = 2025 if 2025 in seasons else seasons[-1]
    c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
    season = c1.selectbox("Season", seasons, index=seasons.index(default_season))
    week = int(c2.number_input("Week", min_value=1, max_value=21, value=15, step=1))
    matchups = _matchups_for_week(season, week)
    labels = [f"{away} @ {home}" for away, home in matchups] or ["N/A @ N/A"]
    default_idx = labels.index("CLE @ CHI") if "CLE @ CHI" in labels else 0
    pick = c3.selectbox("Matchup", labels, index=default_idx)
    profile = c4.selectbox("Profile", ["baseline", "robust", "robust_v2"], index=0)

    away, home = pick.split(" @ ")[0].strip(), pick.split(" @ ")[1].strip()
    if away == "N/A" or home == "N/A":
        st.warning("No matchups found for selected week.")
        return

    try:
        p = build_payload(season, week, away, home, profile)
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not build card: {e}")
        return

    st.markdown(
        f"""
        <div class="top-strip">
          <div class="top-title">{p['away']} @ {p['home']}</div>
          <div class="chip-row">
            <div class="chip"><div class="chip-label">Season/Week</div><div class="chip-value">{p['season']} / W{p['week']}</div></div>
            <div class="chip"><div class="chip-label">Profile</div><div class="chip-value">{profile}</div></div>
            <div class="chip"><div class="chip-label">Market Spread</div><div class="chip-value">{_fmt_spread(p['market_spread'])}</div></div>
            <div class="chip"><div class="chip-label">Fair Spread</div><div class="chip-value">{_fmt_spread(p['fair_spread'])}</div></div>
            <div class="chip"><div class="chip-label">Market Total</div><div class="chip-value">{p['market_total']:.1f}</div></div>
            <div class="chip"><div class="chip-label">Fair Total</div><div class="chip-value">{p['fair_total']:.1f}</div></div>
            <div class="chip"><div class="chip-label">Bucket</div><div class="chip-value">{p['bucket']}</div></div>
            <div class="chip"><div class="chip-label">Value Buffer</div><div class="chip-value">{p['value_buffer'] if p['value_buffer'] is not None else 'n/a'}</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _panel_title("Baseline Model")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _kpi_card(
            "Win Probability",
            f"{p['home']} {p['home_wp']:.1f}% / {p['away']} {p['away_wp']:.1f}",
            "Baseline model",
        )
    with k2:
        _kpi_card(
            "Fair Spread",
            f"{p['home']} {_fmt_spread(p['fair_spread'])}",
            f"Market {_fmt_spread(p['market_spread'])}",
        )
    with k3:
        _kpi_card("Fair Total", f"{p['fair_total']:.1f}", f"Market {p['market_total']:.1f}")
    with k4:
        _kpi_card("Decision", p["decision"], f"{p['fragility_label']} ({p['fragility_score']}/100)")

    row1_left, row1_mid, row1_right = st.columns([1.2, 1.8, 1.0])
    with row1_left:
        _panel_title("Top Drivers")
        st.markdown(
            "\n".join(
                [
                    f"- Model margin: **{p['model_margin']:.1f}**",
                    f"- Value buffer: **{p['value_buffer'] if p['value_buffer'] is not None else 'n/a'}**",
                    f"- Bucket: **{p['bucket']}** (level {p['guardrail_level']})",
                    f"- Third down edge: **{p['third_down_delta']:+.3f}**",
                    f"- Turnover edge: **{p['to_delta']:+.3f}**",
                ]
            )
        )
    with row1_mid:
        _panel_title("Scenario Table")
        show = p["scenario"].copy()
        show["Win Prob"] = show["Win Prob"].map(lambda x: f"{x:.1f}% {p['home']}")
        show["Fair Spread"] = show["Fair Spread"].map(_fmt_spread)
        show["Fair Total"] = show["Fair Total"].map(lambda x: f"{x:.1f}")
        st.dataframe(show, use_container_width=True, hide_index=True)
    with row1_right:
        _panel_title("PowerScore Diff + Components")
        _kpi_card("PowerScore Diff", f"{p['power_diff']:+.3f}", f"{p['home']} - {p['away']}")
        st.markdown(
            f"- EPA off delta: **{p['epa_off_delta']:+.3f}**\n"
            f"- SR off delta: **{p['sr_off_delta']:+.3%}**\n"
            f"- Pressure delta: **{p['pressure_delta']:+.3%}**"
        )

    row2_left, row2_mid, row2_right = st.columns([1.2, 1.2, 1.6])
    with row2_left:
        _panel_title("Form Trend (Last 3 vs Last 5)")
        form_df = pd.DataFrame(
            [
                ("EPA Off", p["form_epa_home"], p["form_epa_away"]),
                ("Success Rate Off", p["form_sr_home"], p["form_sr_away"]),
                ("Tempo", p["form_tempo_home"], p["form_tempo_away"]),
            ],
            columns=["Metric", p["home"], p["away"]],
        )
        st.dataframe(form_df, use_container_width=True, hide_index=True)

    with row2_mid:
        _panel_title("Stability / Fragility Score")
        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=p["fragility_score"],
                title={"text": p["fragility_label"]},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#d97706"},
                    "steps": [
                        {"range": [0, 35], "color": "#166534"},
                        {"range": [35, 60], "color": "#15803d"},
                        {"range": [60, 80], "color": "#b45309"},
                        {"range": [80, 100], "color": "#991b1b"},
                    ],
                },
            )
        )
        gauge.update_layout(
            height=230, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(gauge, use_container_width=True)
        st.markdown(_decision_badges(p["decision"]), unsafe_allow_html=True)

    with row2_right:
        _panel_title("Model vs Market")
        line = go.Figure()
        x = ["Open", "Midweek", "Final"]
        line.add_trace(
            go.Scatter(
                x=x,
                y=[p["market_spread"], p["market_spread"], p["market_spread"]],
                mode="lines+markers",
                name="Spread",
            )
        )
        line.add_trace(
            go.Scatter(
                x=x,
                y=[p["market_total"], p["market_total"], p["market_total"]],
                mode="lines+markers",
                name="Total",
            )
        )
        line.update_layout(
            height=230,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h"),
        )
        st.plotly_chart(line, use_container_width=True)
        st.markdown(
            f"- Spread edge: **{_fmt_spread(p['fair_spread'] - p['market_spread'])}**\n"
            f"- Total edge: **{(p['fair_total'] - p['market_total']):+.1f}**\n"
            f"- Guardrail notes: **{p['guardrail_notes'] or 'n/a'}**"
        )

    col_weather, col_summary = st.columns([1.1, 1.9])
    with col_weather:
        _panel_title("Weather Impact Block")
        st.markdown(
            f"""
            <div class="summary-box">
            <b>Bucket:</b> {p['bucket']}<br/>
            <b>Guardrail level:</b> {p['guardrail_level']}<br/>
            <b>Value buffer:</b> {p['value_buffer'] if p['value_buffer'] is not None else 'n/a'}<br/>
            <b>Notes:</b> {p['guardrail_notes'] or 'n/a'}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_summary:
        _panel_title("Summary")
        st.markdown(
            f"""
            <div class="summary-box">
            Baseline gives <b>{p['home']}</b> an edge (<b>{_fmt_spread(p['fair_spread'])}</b> vs market <b>{_fmt_spread(p['market_spread'])}</b>),
            with weather bucket <b>{p['bucket']}</b> and value buffer <b>{p['value_buffer'] if p['value_buffer'] is not None else 'n/a'}</b>.<br/>
            Fragility is <b>{p['fragility_score']}/100</b> ({p['fragility_label']}), so current decision is <b>{p['decision']}</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Guardrails Explained", expanded=False):
        st.markdown(
            f"""
**Current guardrail level:** `{p['guardrail_level']}`

**Legend**
- `0` no guardrail: brak ostrzezen
- `1` soft warning: lekki sygnal ryzyka
- `2` downgraded supercell: sygnal zostal obnizony przez guardrails
- `3` downgraded vortex: silne ryzyko, wysoka ostroznosc

**How to read common notes**
- `PPD diff last3 too low`: przewaga points-per-drive w krotkim oknie jest za slaba.
- `Explosive gap too low`: przewaga big-play jest za mala lub ujemna.
- `Red zone TD too low`: skutecznosc konczenia drive'ow jest za niska.
- `Def EPA trending worse`: obrona pogarsza trend wzgledem dluzszego okna.

**Raw notes**
`{p['guardrail_notes'] or 'n/a'}`
"""
        )


if __name__ == "__main__":
    main()
