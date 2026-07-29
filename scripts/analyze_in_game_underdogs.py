from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

import nfl_data_py as nfl
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


PBP_COLUMNS = [
    "game_id",
    "play_id",
    "qtr",
    "quarter_seconds_remaining",
    "game_seconds_remaining",
    "home_team",
    "away_team",
    "total_home_score",
    "total_away_score",
    "home_score",
    "away_score",
    "spread_line",
    "home_wp",
    "away_wp",
    "vegas_home_wp",
]


def american_odds_from_probability(probability: float | None) -> float | None:
    if probability is None or math.isnan(probability) or probability <= 0 or probability >= 1:
        return None
    if probability >= 0.5:
        return -100 * probability / (1 - probability)
    return 100 * (1 - probability) / probability


def load_regular_game_ids(season: int, data_root: Path) -> set[str]:
    schedule_path = data_root / "schedules" / f"{season}.parquet"
    if not schedule_path.exists():
        return set()
    schedule = pd.read_parquet(schedule_path)
    if "game_type" in schedule.columns:
        schedule = schedule[schedule["game_type"] == "REG"]
    return set(schedule["game_id"].dropna().astype(str))


def underdog_side(spread_line: float) -> str | None:
    # nflverse spread_line is from the away team's perspective.
    if spread_line > 0:
        return "away"
    if spread_line < 0:
        return "home"
    return None


def snapshot_rows(pbp: pd.DataFrame, quarter: int) -> pd.DataFrame:
    q = pbp[pbp["qtr"] == quarter].copy()
    q = q.sort_values(["game_id", "play_id"])
    return q.groupby("game_id", as_index=False).tail(1)


def build_snapshots(pbp: pd.DataFrame) -> pd.DataFrame:
    q1 = snapshot_rows(pbp, 1).assign(snapshot="Q1")
    h1 = snapshot_rows(pbp, 2).assign(snapshot="H1")
    q3 = snapshot_rows(pbp, 3).assign(snapshot="Q3")
    return pd.concat([q1, h1, q3], ignore_index=True)


def enrich_snapshot(row: pd.Series) -> dict[str, Any]:
    spread = float(row["spread_line"])
    side = underdog_side(spread)
    if side is None:
        return {}

    home_score_now = float(row["total_home_score"])
    away_score_now = float(row["total_away_score"])
    home_final = int(row["home_score"])
    away_final = int(row["away_score"])
    underdog_team = row["away_team"] if side == "away" else row["home_team"]
    favorite_team = row["home_team"] if side == "away" else row["away_team"]
    underdog_score_now = away_score_now if side == "away" else home_score_now
    favorite_score_now = home_score_now if side == "away" else away_score_now
    underdog_final = away_final if side == "away" else home_final
    favorite_final = home_final if side == "away" else away_final
    underdog_wp = float(row["away_wp"] if side == "away" else row["home_wp"])
    vegas_home_wp = row.get("vegas_home_wp")
    if pd.isna(vegas_home_wp):
        underdog_vegas_wp = None
    else:
        underdog_vegas_wp = float(1 - vegas_home_wp if side == "away" else vegas_home_wp)

    if side == "away":
        ats_margin = away_final + spread - home_final
    else:
        ats_margin = home_final - spread - away_final

    return {
        "game_id": row["game_id"],
        "snapshot": row["snapshot"],
        "underdog_side": side,
        "underdog_team": underdog_team,
        "favorite_team": favorite_team,
        "spread_line_away_perspective": spread,
        "underdog_score_now": underdog_score_now,
        "favorite_score_now": favorite_score_now,
        "underdog_margin_now": underdog_score_now - favorite_score_now,
        "underdog_wp": underdog_wp,
        "underdog_fair_ml": american_odds_from_probability(underdog_wp),
        "underdog_vegas_wp": underdog_vegas_wp,
        "underdog_vegas_fair_ml": american_odds_from_probability(underdog_vegas_wp),
        "underdog_final": underdog_final,
        "favorite_final": favorite_final,
        "underdog_final_margin": underdog_final - favorite_final,
        "underdog_won_su": underdog_final > favorite_final,
        "underdog_covered": ats_margin > 0,
        "ats_margin": ats_margin,
        "pregame_spread_abs": abs(spread),
    }


def analyze_seasons(seasons: list[int], data_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    details = []
    for season in seasons:
        detail, _ = analyze(season, data_root)
        detail["season"] = season
        details.append(detail)
    all_detail = pd.concat(details, ignore_index=True) if details else pd.DataFrame()
    if all_detail.empty:
        return all_detail, pd.DataFrame(), pd.DataFrame()
    summary = summarize(all_detail)
    buckets = summarize_buckets(all_detail)
    return all_detail, summary, buckets


def analyze(season: int, data_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    pbp = nfl.import_pbp_data(
        [season],
        columns=PBP_COLUMNS,
        include_participation=False,
        downcast=True,
        cache=False,
    )
    game_ids = load_regular_game_ids(season, data_root)
    if game_ids:
        pbp = pbp[pbp["game_id"].isin(game_ids)].copy()
    pbp = pbp.dropna(subset=["spread_line", "home_score", "away_score"])
    snapshots = build_snapshots(pbp)
    rows = [enrich_snapshot(row) for _, row in snapshots.iterrows()]
    detail = pd.DataFrame([row for row in rows if row])
    detail = detail[detail["underdog_margin_now"] > 0].copy()
    summary = summarize(detail)
    return detail, summary


def summarize(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame()
    grouped = []
    for snapshot, group in detail.groupby("snapshot", sort=False):
        grouped.append(
            {
                "snapshot": snapshot,
                "cases_underdog_led": len(group),
                "avg_lead": group["underdog_margin_now"].mean(),
                "median_lead": group["underdog_margin_now"].median(),
                "su_wins": int(group["underdog_won_su"].sum()),
                "su_win_rate": group["underdog_won_su"].mean(),
                "covers": int(group["underdog_covered"].sum()),
                "cover_rate": group["underdog_covered"].mean(),
                "median_wp": group["underdog_wp"].median(),
                "median_fair_ml": group["underdog_fair_ml"].median(),
                "median_vegas_wp": group["underdog_vegas_wp"].median(),
                "median_vegas_fair_ml": group["underdog_vegas_fair_ml"].median(),
            }
        )
    order = {"Q1": 1, "H1": 2, "Q3": 3}
    return pd.DataFrame(grouped).sort_values("snapshot", key=lambda s: s.map(order))


def summarize_buckets(detail: pd.DataFrame) -> pd.DataFrame:
    if detail.empty:
        return pd.DataFrame()
    q3 = detail[detail["snapshot"] == "Q3"].copy()
    if q3.empty:
        return pd.DataFrame()
    q3["spread_bucket"] = q3["pregame_spread_abs"].apply(_spread_bucket)
    q3["lead_bucket"] = q3["underdog_margin_now"].apply(_lead_bucket)
    q3["location"] = q3["underdog_side"].map({"home": "home dog", "away": "away dog"})
    q3["fair_ml_bucket"] = q3["underdog_wp"].apply(
        lambda p: "plus-money fair" if p < 0.5 else "favorite fair"
    )
    rows = []
    group_cols = ["spread_bucket", "lead_bucket", "location", "fair_ml_bucket"]
    for keys, group in q3.groupby(group_cols, dropna=False):
        cases = len(group)
        su_wins = int(group["underdog_won_su"].sum())
        covers = int(group["underdog_covered"].sum())
        su_rate = su_wins / cases if cases else 0.0
        rows.append(
            {
                "spread_bucket": keys[0],
                "lead_bucket": keys[1],
                "location": keys[2],
                "fair_ml_bucket": keys[3],
                "cases": cases,
                "su_wins": su_wins,
                "su_win_rate": su_rate,
                "break_even_live_ml": american_odds_from_probability(su_rate),
                "covers": covers,
                "cover_rate_pregame_spread": covers / cases if cases else 0.0,
                "median_wp": group["underdog_wp"].median(),
                "median_fair_ml": group["underdog_fair_ml"].median(),
                "avg_lead": group["underdog_margin_now"].mean(),
            }
        )
    order_spread = {"<=3": 1, "3.5-7": 2, "7.5+": 3}
    order_lead = {"1-3": 1, "4-7": 2, "8+": 3}
    bucket_df = pd.DataFrame(rows)
    bucket_df["_spread_order"] = bucket_df["spread_bucket"].map(order_spread)
    bucket_df["_lead_order"] = bucket_df["lead_bucket"].map(order_lead)
    bucket_df["live_decision_note"] = bucket_df.apply(_live_decision_note, axis=1)
    return (
        bucket_df.sort_values(
            ["_spread_order", "_lead_order", "cases"],
            ascending=[True, True, False],
        )
        .drop(columns=["_spread_order", "_lead_order"])
        .reset_index(drop=True)
    )


def _live_decision_note(row: pd.Series) -> str:
    cases = int(row["cases"])
    su_rate = float(row["su_win_rate"])
    if cases < 30:
        return "NO BET - sample <30"
    if su_rate >= 0.70:
        return f"ML WATCH - only better than {_fmt_ml(row['break_even_live_ml'])}"
    if su_rate >= 0.55:
        return f"PRICE SENSITIVE ML - only better than {_fmt_ml(row['break_even_live_ml'])}"
    return "NO ML - historical win rate too low"


def _spread_bucket(value: float) -> str:
    if value <= 3:
        return "<=3"
    if value <= 7:
        return "3.5-7"
    return "7.5+"


def _lead_bucket(value: float) -> str:
    if value <= 3:
        return "1-3"
    if value <= 7:
        return "4-7"
    return "8+"


def write_report(
    season_label: str,
    detail: pd.DataFrame,
    summary: pd.DataFrame,
    output: Path,
    bucket_summary: pd.DataFrame | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# In-Game Pregame Underdog Study - {season_label}",
        "",
        "Scope: regular season games only when local schedule data is available.",
        "",
        "Important limitation: nfl_data_py does not provide historical executable live moneyline odds. "
        "The `fair ML` columns below are converted from nflfastR win probability / vegas win probability proxies.",
        "",
        "## Summary",
        "",
        "| Snapshot | Cases Led | Avg Lead | SU W-L | SU Win% | ATS W-L | ATS Cover% | Median WP | Median Fair ML | Median Vegas WP | Median Vegas Fair ML |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dicts() if hasattr(summary, "to_dicts") else summary.to_dict("records"):
        cases = int(row["cases_underdog_led"])
        su_wins = int(row["su_wins"])
        covers = int(row["covers"])
        lines.append(
            "| {snapshot} | {cases} | {avg_lead:.1f} | {su_wins}-{su_losses} | "
            "{su_win_rate:.1%} | {covers}-{cover_losses} | {cover_rate:.1%} | "
            "{median_wp:.1%} | {median_fair_ml} | {median_vegas_wp:.1%} | {median_vegas_fair_ml} |".format(
                snapshot=row["snapshot"],
                cases=cases,
                avg_lead=row["avg_lead"],
                su_wins=su_wins,
                su_losses=cases - su_wins,
                su_win_rate=row["su_win_rate"],
                covers=covers,
                cover_losses=cases - covers,
                cover_rate=row["cover_rate"],
                median_wp=row["median_wp"],
                median_fair_ml=_fmt_ml(row["median_fair_ml"]),
                median_vegas_wp=row["median_vegas_wp"],
                median_vegas_fair_ml=_fmt_ml(row["median_vegas_fair_ml"]),
            )
        )
    lines.extend(
        [
            "",
            "## Q3 Live Trigger Map",
            "",
            "This table is the closest we can get without true historical live odds. "
            "`Break-even live ML` is the worst live moneyline price you could accept based on historical SU win rate for that state. "
            "Example: if break-even is `-150`, you need better than -150. If it is `+120`, you need +120 or better.",
            "",
            "| Spread Bucket | Lead Bucket | Location | Fair ML Bucket | Cases | SU W-L | SU Win% | Break-even Live ML | Pregame ATS Cover% | Median WP | Median Fair ML | Live Decision Note |",
            "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    if bucket_summary is not None and not bucket_summary.empty:
        for row in bucket_summary.to_dict("records"):
            cases = int(row["cases"])
            su_wins = int(row["su_wins"])
            lines.append(
                "| {spread_bucket} | {lead_bucket} | {location} | {fair_ml_bucket} | {cases} | "
                "{su_wins}-{su_losses} | {su_win_rate:.1%} | {be_ml} | {cover_rate:.1%} | "
                "{median_wp:.1%} | {median_fair_ml} | {decision} |".format(
                    spread_bucket=row["spread_bucket"],
                    lead_bucket=row["lead_bucket"],
                    location=row["location"],
                    fair_ml_bucket=row["fair_ml_bucket"],
                    cases=cases,
                    su_wins=su_wins,
                    su_losses=cases - su_wins,
                    su_win_rate=row["su_win_rate"],
                    be_ml=_fmt_ml(row["break_even_live_ml"]),
                    cover_rate=row["cover_rate_pregame_spread"],
                    median_wp=row["median_wp"],
                    median_fair_ml=_fmt_ml(row["median_fair_ml"]),
                    decision=row["live_decision_note"],
                )
            )
    else:
        lines.append("| - | - | - | - | 0 | 0-0 | 0.0% | n/a | 0.0% | 0.0% | n/a | n/a |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `Q1`, `H1`, and `Q3` mean the underdog was leading at the end of that game segment.",
            "- `SU Win%` shows how often the pregame underdog finished the upset after leading.",
            "- `ATS Cover%` shows how often the pregame underdog covered the original pregame spread.",
            "- `Median Fair ML` is not a historical live book line. It is the no-vig fair moneyline implied by the model win probability.",
            "- `Break-even live ML` is based on realized historical SU win rate in that bucket, not on available book prices.",
            "- `Live Decision Note` is intentionally conservative: it only marks a moneyline watch state when the bucket has at least 30 historical cases.",
            "- This does not choose a live spread because archived live spread lines are not present in nfl_data_py.",
            "- This report can identify live states worth monitoring; it cannot prove live betting profit without archived live odds.",
            "",
            "## Detail Export",
            "",
            f"CSV detail: `{output.with_suffix('.csv')}`",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    detail.to_csv(output.with_suffix(".csv"), index=False)


def _fmt_ml(value: Any) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):+.0f}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze pregame underdogs leading in-game.")
    parser.add_argument("--season", type=int)
    parser.add_argument("--seasons", nargs="+", type=int)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    seasons = args.seasons or ([args.season] if args.season else None)
    if not seasons:
        raise SystemExit("Provide --season or --seasons.")
    detail, summary, bucket_summary = analyze_seasons(seasons, args.data_root)
    season_label = str(seasons[0]) if len(seasons) == 1 else f"{seasons[0]}_{seasons[-1]}"
    output = args.output or Path("research") / f"in_game_underdog_study_{season_label}.md"
    write_report(season_label, detail, summary, output, bucket_summary)
    print(f"report={output}")
    print(f"detail={output.with_suffix('.csv')}")
    print(summary.to_string(index=False))
    if not bucket_summary.empty:
        print(bucket_summary.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
