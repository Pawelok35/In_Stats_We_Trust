"""ATS feature research helpers for champion-pick veto reports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import polars as pl

from utils.team_aliases import normalize_team_code

PAYOUT_WIN = 2.7
PAYOUT_LOSS = -3.0
PAYOUT_RISK = 3.0

CORE_VARIANT_DIR = Path("data/picks_variant_d_balanced")
DEFAULT_OUTPUT = Path("data/results/strategy_search/gom_feature_veto_report.md")
SEASONS = list(range(2017, 2026))
TRAIN_SEASONS = set(range(2017, 2023))
VALIDATION_SEASONS = {2023}
HOLDOUT_SEASONS = {2024, 2025}


@dataclass(frozen=True)
class PickFeatureRow:
    season: int
    week: int
    home: str
    away: str
    pick_team: str
    opponent: str
    outcome: str
    profit: float
    risk: float
    early_down_matchup_edge: float | None
    off_early_down_success_edge: float | None
    def_early_down_epa_allowed_edge: float | None
    fumble_recovery_luck_edge: float | None = None
    third_down_luck_support: float | None = None
    third_down_attempts_combined: float | None = None
    red_zone_luck_support: float | None = None
    red_zone_trips_combined: float | None = None
    pressure_matchup_disadvantage: float | None = None
    sack_conversion_overperformance: float | None = None
    picked_defense_pressure_rate: float | None = None
    league_pressure_rate_median: float | None = None
    off_early_down_success_pick: float | None = None
    off_early_down_success_opp: float | None = None
    def_early_down_epa_allowed_pick: float | None = None
    def_early_down_epa_allowed_opp: float | None = None


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _result_map(seasons: Iterable[int]) -> dict[tuple[int, int, str, str], tuple[Any, Any]]:
    results: dict[tuple[int, int, str, str], tuple[Any, Any]] = {}
    for season in seasons:
        path = Path("data/schedules") / f"{season}.parquet"
        if not path.exists():
            continue
        df = pl.read_parquet(path)
        if "game_type" in df.columns:
            df = df.filter(pl.col("game_type") == "REG")
        for row in df.to_dicts():
            home = normalize_team_code(row.get("home_team"))
            away = normalize_team_code(row.get("away_team"))
            if home and away:
                results[(season, int(row["week"]), home, away)] = (
                    row.get("home_score"),
                    row.get("away_score"),
                )
    return results


def _pick_outcome(pick: dict[str, Any], result: tuple[Any, Any] | None) -> str | None:
    if not result or result[0] is None or result[1] is None:
        return None
    home = normalize_team_code(pick.get("home"))
    away = normalize_team_code(pick.get("away"))
    model_winner = normalize_team_code(pick.get("model_winner"))
    home_score = int(result[0])
    away_score = int(result[1])
    if model_winner == home:
        margin = home_score - away_score
    elif model_winner == away:
        margin = away_score - home_score
    else:
        return None
    ats_margin = margin + float(pick.get("handicap") or 0.0)
    if ats_margin > 0:
        return "win"
    if ats_margin < 0:
        return "loss"
    return "push"


def load_core_gom_picks(
    seasons: Iterable[int] = SEASONS,
    picks_dir: Path = CORE_VARIANT_DIR,
) -> list[dict[str, Any]]:
    """Load the current champion CORE GOM picks and grade them ATS."""

    season_list = list(seasons)
    results = _result_map(season_list)
    rows: list[dict[str, Any]] = []
    for season in season_list:
        season_dir = picks_dir / str(season)
        if not season_dir.exists():
            continue
        for path in sorted(season_dir.glob("week_*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                pick = json.loads(line)
                week = int(pick.get("week") or 0)
                tag = str(pick.get("tag", "")).upper()
                confidence = float(pick.get("confidence") or 0)
                edge = float(pick.get("edge_vs_line") or 0)
                handicap = float(pick.get("handicap") or 0)
                if not (
                    tag == "GOM"
                    and week >= 3
                    and confidence >= 85
                    and edge >= 4
                    and abs(handicap) <= 7
                ):
                    continue
                home = normalize_team_code(pick.get("home"))
                away = normalize_team_code(pick.get("away"))
                outcome = _pick_outcome(pick, results.get((season, week, home, away)))
                if outcome is None:
                    continue
                rows.append(
                    {
                        "season": season,
                        "week": week,
                        "home": home,
                        "away": away,
                        "pick_team": normalize_team_code(pick.get("model_winner")),
                        "opponent": (
                            away if normalize_team_code(pick.get("model_winner")) == home else home
                        ),
                        "outcome": outcome,
                        "profit": (
                            PAYOUT_WIN
                            if outcome == "win"
                            else PAYOUT_LOSS if outcome == "loss" else 0.0
                        ),
                        "risk": PAYOUT_RISK,
                    }
                )
    return rows


def _load_l2_before_week(season: int, week: int) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for prior_week in range(1, week):
        path = Path("data/l2") / str(season) / f"{prior_week}.parquet"
        if path.exists():
            frames.append(pl.read_parquet(path))
    if not frames:
        return pl.DataFrame()
    return pl.concat(frames, how="diagonal_relaxed")


def _shrink_rate(
    successes: pl.Expr,
    attempts: pl.Expr,
    league_rate: float,
    pseudo: float,
) -> pl.Expr:
    return (successes + league_rate * pseudo) / (attempts + pseudo)


def _shrink_mean(total: pl.Expr, attempts: pl.Expr, league_mean: float, pseudo: float) -> pl.Expr:
    return (total + league_mean * pseudo) / (attempts + pseudo)


def _team_prior_features(season: int, week: int, pseudo_plays: float = 100.0) -> dict[str, Any]:
    """Aggregate prior-week early-down features for each team in one season/week cutoff."""

    df = _load_l2_before_week(season, week)
    if df.is_empty():
        return {}
    needed = {"TEAM", "OPP", "down", "epa", "success"}
    if needed - set(df.columns):
        return {}

    base = df.with_columns(
        [
            pl.col("TEAM").map_elements(normalize_team_code, return_dtype=pl.Utf8),
            pl.col("OPP").map_elements(normalize_team_code, return_dtype=pl.Utf8),
            pl.col("down").cast(pl.Int64),
            pl.col("distance").cast(pl.Float64).fill_null(0.0),
            pl.col("epa").cast(pl.Float64).fill_null(0.0),
            pl.col("success").cast(pl.Float64).fill_null(0.0),
            pl.col("is_dropback").cast(pl.Int64).fill_null(0),
            pl.col("is_pressure").cast(pl.Int64).fill_null(0),
            pl.col("is_third_down").cast(pl.Int64).fill_null(0),
            pl.col("third_down_converted").cast(pl.Int64).fill_null(0),
            pl.col("in_redzone").cast(pl.Int64).fill_null(0),
            pl.col("is_offensive_td").cast(pl.Int64).fill_null(0),
            pl.col("is_turnover").cast(pl.Int64).fill_null(0),
            pl.col("play_type").cast(pl.Utf8).fill_null("").str.to_lowercase(),
            pl.col("play_description").cast(pl.Utf8).fill_null("").str.to_uppercase(),
        ]
    ).filter(pl.col("TEAM").is_not_null() & pl.col("OPP").is_not_null())

    early = base.filter(pl.col("down").is_in([1, 2])).filter(
        pl.col("TEAM").is_not_null() & pl.col("OPP").is_not_null()
    )
    if early.is_empty():
        return {}

    base = base.with_columns(
        [
            pl.when(pl.col("distance") <= 3)
            .then(pl.lit("short"))
            .when(pl.col("distance") <= 6)
            .then(pl.lit("medium"))
            .otherwise(pl.lit("long"))
            .alias("_distance_bucket"),
            pl.col("play_description").str.contains("FUMBLES").cast(pl.Int64).alias("_is_fumble"),
            (
                (pl.col("play_type").str.contains("sack"))
                | (pl.col("play_description").str.contains(" SACK"))
            )
            .cast(pl.Int64)
            .alias("_is_sack"),
        ]
    )

    third_downs = base.filter(pl.col("is_third_down") == 1)
    redzone = base.filter(pl.col("in_redzone") == 1)
    dropbacks = base.filter(pl.col("is_dropback") == 1)
    fumbles = base.filter(pl.col("_is_fumble") == 1)

    third_expected: dict[str, float] = {}
    if not third_downs.is_empty():
        third_expected = {
            row["_distance_bucket"]: float(row["_expected_conversion"] or 0.0)
            for row in third_downs.group_by("_distance_bucket")
            .agg(pl.col("third_down_converted").mean().alias("_expected_conversion"))
            .to_dicts()
        }
    if not third_expected:
        third_expected = {"short": 0.55, "medium": 0.4, "long": 0.25}

    redzone_expected = (
        float(redzone.select(pl.col("is_offensive_td").mean()).item())
        if not redzone.is_empty()
        else 0.18
    )
    league_pressure_rate = (
        float(dropbacks.select(pl.col("is_pressure").mean()).item())
        if not dropbacks.is_empty()
        else 0.0
    )
    team_pressure_rates = (
        dropbacks.group_by("OPP")
        .agg(pl.col("is_pressure").mean().alias("_pressure_rate_def"))
        .select("_pressure_rate_def")
        .to_series()
        .to_list()
        if not dropbacks.is_empty()
        else []
    )
    league_pressure_median = (
        _quantile([float(item) for item in team_pressure_rates if item is not None], 0.5)
        if team_pressure_rates
        else league_pressure_rate
    )

    league = early.select(
        [
            pl.col("epa").mean().alias("league_epa"),
            pl.col("success").mean().alias("league_success"),
        ]
    ).to_dicts()[0]
    league_epa = float(league["league_epa"] or 0.0)
    league_success = float(league["league_success"] or 0.0)

    offense = (
        early.group_by("TEAM")
        .agg(
            [
                pl.len().cast(pl.Float64).alias("off_early_down_plays"),
                pl.col("epa").sum().cast(pl.Float64).alias("_off_epa_sum"),
                pl.col("success").sum().cast(pl.Float64).alias("_off_success_sum"),
            ]
        )
        .with_columns(
            [
                _shrink_mean(
                    pl.col("_off_epa_sum"),
                    pl.col("off_early_down_plays"),
                    league_epa,
                    pseudo_plays,
                ).alias("off_early_down_epa"),
                _shrink_rate(
                    pl.col("_off_success_sum"),
                    pl.col("off_early_down_plays"),
                    league_success,
                    pseudo_plays,
                ).alias("off_early_down_success_rate"),
            ]
        )
        .select(["TEAM", "off_early_down_epa", "off_early_down_success_rate"])
    )
    defense = (
        early.group_by("OPP")
        .agg(
            [
                pl.len().cast(pl.Float64).alias("def_early_down_plays"),
                pl.col("epa").sum().cast(pl.Float64).alias("_def_epa_allowed_sum"),
                pl.col("success").sum().cast(pl.Float64).alias("_def_success_allowed_sum"),
            ]
        )
        .rename({"OPP": "TEAM"})
        .with_columns(
            [
                _shrink_mean(
                    pl.col("_def_epa_allowed_sum"),
                    pl.col("def_early_down_plays"),
                    league_epa,
                    pseudo_plays,
                ).alias("def_early_down_epa_allowed"),
                _shrink_rate(
                    pl.col("_def_success_allowed_sum"),
                    pl.col("def_early_down_plays"),
                    league_success,
                    pseudo_plays,
                ).alias("def_early_down_success_allowed"),
            ]
        )
        .select(["TEAM", "def_early_down_epa_allowed", "def_early_down_success_allowed"])
    )
    pressure_off = (
        dropbacks.group_by("TEAM")
        .agg(
            [
                pl.len().cast(pl.Float64).alias("_dropbacks_off"),
                pl.col("is_pressure").sum().cast(pl.Float64).alias("_pressures_allowed"),
            ]
        )
        .with_columns(
            _shrink_rate(
                pl.col("_pressures_allowed"),
                pl.col("_dropbacks_off"),
                league_pressure_rate,
                pseudo_plays,
            ).alias("pressure_allowed_proxy")
        )
        .select(["TEAM", "_dropbacks_off", "pressure_allowed_proxy"])
    )
    pressure_def = (
        dropbacks.group_by("OPP")
        .agg(
            [
                pl.len().cast(pl.Float64).alias("_dropbacks_def"),
                pl.col("is_pressure").sum().cast(pl.Float64).alias("_pressures_created"),
                pl.col("_is_sack").sum().cast(pl.Float64).alias("_sacks_created"),
            ]
        )
        .rename({"OPP": "TEAM"})
        .with_columns(
            [
                _shrink_rate(
                    pl.col("_pressures_created"),
                    pl.col("_dropbacks_def"),
                    league_pressure_rate,
                    pseudo_plays,
                ).alias("pressure_created_proxy"),
                _shrink_rate(
                    pl.col("_sacks_created"),
                    pl.col("_pressures_created"),
                    0.35,
                    20.0,
                ).alias("sack_conversion"),
            ]
        )
        .select(
            [
                "TEAM",
                "pressure_created_proxy",
                "sack_conversion",
                pl.lit(league_pressure_median).alias("league_pressure_rate_median"),
            ]
        )
    )

    if third_downs.is_empty():
        third_off = pl.DataFrame({"TEAM": [], "off_3doe": [], "third_down_att_off": []})
        third_def = pl.DataFrame({"TEAM": [], "def_3doe": [], "third_down_att_def": []})
    else:
        third_with_expected = third_downs.with_columns(
            pl.col("_distance_bucket")
            .replace(third_expected, default=0.35)
            .cast(pl.Float64)
            .alias("_expected_conversion")
        )
        third_off = (
            third_with_expected.group_by("TEAM")
            .agg(
                [
                    pl.len().cast(pl.Float64).alias("third_down_att_off"),
                    (pl.col("third_down_converted") - pl.col("_expected_conversion"))
                    .sum()
                    .cast(pl.Float64)
                    .alias("_off_3doe_sum"),
                ]
            )
            .with_columns(
                _shrink_mean(
                    pl.col("_off_3doe_sum"),
                    pl.col("third_down_att_off"),
                    0.0,
                    25.0,
                ).alias("off_3doe")
            )
            .select(["TEAM", "off_3doe", "third_down_att_off"])
        )
        third_def = (
            third_with_expected.group_by("OPP")
            .agg(
                [
                    pl.len().cast(pl.Float64).alias("third_down_att_def"),
                    (pl.col("_expected_conversion") - pl.col("third_down_converted"))
                    .sum()
                    .cast(pl.Float64)
                    .alias("_def_3doe_sum"),
                ]
            )
            .rename({"OPP": "TEAM"})
            .with_columns(
                _shrink_mean(
                    pl.col("_def_3doe_sum"),
                    pl.col("third_down_att_def"),
                    0.0,
                    25.0,
                ).alias("def_3doe")
            )
            .select(["TEAM", "def_3doe", "third_down_att_def"])
        )

    if redzone.is_empty():
        rz_off = pl.DataFrame({"TEAM": [], "off_rzoe": [], "redzone_trips_off": []})
        rz_def = pl.DataFrame({"TEAM": [], "def_rzoe": [], "redzone_trips_def": []})
    else:
        rz_off = (
            redzone.group_by("TEAM")
            .agg(
                [
                    pl.len().cast(pl.Float64).alias("redzone_trips_off"),
                    (pl.col("is_offensive_td") - redzone_expected)
                    .sum()
                    .cast(pl.Float64)
                    .alias("_off_rzoe_sum"),
                ]
            )
            .with_columns(
                _shrink_mean(
                    pl.col("_off_rzoe_sum"),
                    pl.col("redzone_trips_off"),
                    0.0,
                    20.0,
                ).alias("off_rzoe")
            )
            .select(["TEAM", "off_rzoe", "redzone_trips_off"])
        )
        rz_def = (
            redzone.group_by("OPP")
            .agg(
                [
                    pl.len().cast(pl.Float64).alias("redzone_trips_def"),
                    (redzone_expected - pl.col("is_offensive_td"))
                    .sum()
                    .cast(pl.Float64)
                    .alias("_def_rzoe_sum"),
                ]
            )
            .rename({"OPP": "TEAM"})
            .with_columns(
                _shrink_mean(
                    pl.col("_def_rzoe_sum"),
                    pl.col("redzone_trips_def"),
                    0.0,
                    20.0,
                ).alias("def_rzoe")
            )
            .select(["TEAM", "def_rzoe", "redzone_trips_def"])
        )

    if fumbles.is_empty():
        fumble_features = pl.DataFrame(
            {"TEAM": [], "fumble_recovery_rate": [], "all_fumbles_in_team_games": []}
        )
    else:
        own_fumbles = fumbles.group_by("TEAM").agg(
            [
                pl.len().cast(pl.Float64).alias("_own_fumbles"),
                (pl.lit(1) - pl.col("is_turnover")).sum().cast(pl.Float64).alias("_own_recovered"),
            ]
        )
        opp_fumbles = (
            fumbles.group_by("OPP")
            .agg(
                [
                    pl.len().cast(pl.Float64).alias("_opp_fumbles"),
                    pl.col("is_turnover").sum().cast(pl.Float64).alias("_opp_recovered"),
                ]
            )
            .rename({"OPP": "TEAM"})
        )
        fumble_features = (
            own_fumbles.join(opp_fumbles, on="TEAM", how="outer")
            .with_columns(
                [
                    pl.col("_own_fumbles").fill_null(0.0),
                    pl.col("_opp_fumbles").fill_null(0.0),
                    pl.col("_own_recovered").fill_null(0.0),
                    pl.col("_opp_recovered").fill_null(0.0),
                ]
            )
            .with_columns(
                [
                    (pl.col("_own_fumbles") + pl.col("_opp_fumbles")).alias(
                        "all_fumbles_in_team_games"
                    ),
                    (
                        (pl.col("_own_recovered") + pl.col("_opp_recovered") + 5.0)
                        / (pl.col("_own_fumbles") + pl.col("_opp_fumbles") + 10.0)
                    ).alias("fumble_recovery_rate"),
                ]
            )
            .select(["TEAM", "fumble_recovery_rate", "all_fumbles_in_team_games"])
        )

    feature_frames = [
        offense,
        defense,
        pressure_off,
        pressure_def,
        third_off,
        third_def,
        rz_off,
        rz_def,
        fumble_features,
    ]
    teams: set[str] = set()
    for frame in feature_frames:
        if "TEAM" in frame.columns and not frame.is_empty():
            teams.update(str(team) for team in frame.get_column("TEAM").drop_nulls().to_list())
    combined = pl.DataFrame({"TEAM": sorted(teams)})
    for frame in feature_frames:
        if "TEAM" in frame.columns and not frame.is_empty():
            combined = combined.join(frame, on="TEAM", how="left")
    return {row["TEAM"]: row for row in combined.to_dicts() if row.get("TEAM")}


def build_core_pick_feature_rows(seasons: Iterable[int] = SEASONS) -> list[PickFeatureRow]:
    """Attach no-leakage early-down features to current champion picks."""

    picks = load_core_gom_picks(seasons)
    cache: dict[tuple[int, int], dict[str, Any]] = {}
    output: list[PickFeatureRow] = []
    for pick in picks:
        key = (pick["season"], pick["week"])
        if key not in cache:
            cache[key] = _team_prior_features(*key)
        features = cache[key]
        pick_row = features.get(pick["pick_team"], {})
        opp_row = features.get(pick["opponent"], {})

        off_epa_pick = _safe_float(pick_row.get("off_early_down_epa"))
        off_epa_opp = _safe_float(opp_row.get("off_early_down_epa"))
        def_epa_allowed_pick = _safe_float(pick_row.get("def_early_down_epa_allowed"))
        def_epa_allowed_opp = _safe_float(opp_row.get("def_early_down_epa_allowed"))
        off_sr_pick = _safe_float(pick_row.get("off_early_down_success_rate"))
        off_sr_opp = _safe_float(opp_row.get("off_early_down_success_rate"))
        fumble_pick = _safe_float(pick_row.get("fumble_recovery_rate"))
        fumble_opp = _safe_float(opp_row.get("fumble_recovery_rate"))
        off_3doe_pick = _safe_float(pick_row.get("off_3doe"))
        def_3doe_pick = _safe_float(pick_row.get("def_3doe"))
        third_att_off = _safe_float(pick_row.get("third_down_att_off")) or 0.0
        third_att_def = _safe_float(pick_row.get("third_down_att_def")) or 0.0
        off_rzoe_pick = _safe_float(pick_row.get("off_rzoe"))
        def_rzoe_pick = _safe_float(pick_row.get("def_rzoe"))
        rz_att_off = _safe_float(pick_row.get("redzone_trips_off")) or 0.0
        rz_att_def = _safe_float(pick_row.get("redzone_trips_def")) or 0.0
        pressure_allowed_pick = _safe_float(pick_row.get("pressure_allowed_proxy"))
        pressure_created_pick = _safe_float(pick_row.get("pressure_created_proxy"))
        pressure_allowed_opp = _safe_float(opp_row.get("pressure_allowed_proxy"))
        pressure_created_opp = _safe_float(opp_row.get("pressure_created_proxy"))
        sack_conversion_pick = _safe_float(pick_row.get("sack_conversion"))
        pressure_rate_def_pick = _safe_float(pick_row.get("pressure_created_proxy"))
        league_pressure_median = _safe_float(pick_row.get("league_pressure_rate_median"))

        matchup_edge = None
        if None not in (off_epa_pick, off_epa_opp, def_epa_allowed_pick, def_epa_allowed_opp):
            matchup_edge = (off_epa_pick + def_epa_allowed_opp) - (
                off_epa_opp + def_epa_allowed_pick
            )
        pressure_disadvantage = None
        if None not in (
            pressure_allowed_pick,
            pressure_created_pick,
            pressure_allowed_opp,
            pressure_created_opp,
        ):
            pressure_faced_pick = (pressure_allowed_pick + pressure_created_opp) / 2.0
            pressure_faced_opp = (pressure_allowed_opp + pressure_created_pick) / 2.0
            pressure_disadvantage = pressure_faced_pick - pressure_faced_opp

        output.append(
            PickFeatureRow(
                season=pick["season"],
                week=pick["week"],
                home=pick["home"],
                away=pick["away"],
                pick_team=pick["pick_team"],
                opponent=pick["opponent"],
                outcome=pick["outcome"],
                profit=pick["profit"],
                risk=pick["risk"],
                early_down_matchup_edge=matchup_edge,
                off_early_down_success_edge=(
                    None if None in (off_sr_pick, off_sr_opp) else off_sr_pick - off_sr_opp
                ),
                def_early_down_epa_allowed_edge=(
                    None
                    if None in (def_epa_allowed_pick, def_epa_allowed_opp)
                    else def_epa_allowed_opp - def_epa_allowed_pick
                ),
                fumble_recovery_luck_edge=(
                    None if None in (fumble_pick, fumble_opp) else fumble_pick - fumble_opp
                ),
                third_down_luck_support=(
                    None
                    if None in (off_3doe_pick, def_3doe_pick)
                    else off_3doe_pick + def_3doe_pick
                ),
                third_down_attempts_combined=third_att_off + third_att_def,
                red_zone_luck_support=(
                    None
                    if None in (off_rzoe_pick, def_rzoe_pick)
                    else off_rzoe_pick + def_rzoe_pick
                ),
                red_zone_trips_combined=rz_att_off + rz_att_def,
                pressure_matchup_disadvantage=pressure_disadvantage,
                sack_conversion_overperformance=sack_conversion_pick,
                picked_defense_pressure_rate=pressure_rate_def_pick,
                league_pressure_rate_median=league_pressure_median,
                off_early_down_success_pick=off_sr_pick,
                off_early_down_success_opp=off_sr_opp,
                def_early_down_epa_allowed_pick=def_epa_allowed_pick,
                def_early_down_epa_allowed_opp=def_epa_allowed_opp,
            )
        )
    return output


def _summarize(rows: list[PickFeatureRow]) -> dict[str, Any]:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for row in sorted(rows, key=lambda item: (item.season, item.week, item.home, item.away)):
        equity += row.profit
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    profit = sum(row.profit for row in rows)
    risk = sum(row.risk for row in rows)
    season_profit = {
        season: sum(row.profit for row in rows if row.season == season) for season in SEASONS
    }
    return {
        "bets": len(rows),
        "wins": sum(1 for row in rows if row.outcome == "win"),
        "losses": sum(1 for row in rows if row.outcome == "loss"),
        "pushes": sum(1 for row in rows if row.outcome == "push"),
        "profit": profit,
        "risk": risk,
        "roi": profit / risk if risk else 0.0,
        "worst_season": min(season_profit.values()) if season_profit else 0.0,
        "drawdown": drawdown,
    }


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    pos = (len(sorted_values) - 1) * q
    lower = int(pos)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = pos - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _feature_value(row: PickFeatureRow, feature: str) -> float | None:
    return getattr(row, feature)


def _format_summary(summary: dict[str, Any]) -> str:
    return (
        f"{summary['bets']} | {summary['wins']}-{summary['losses']}-{summary['pushes']} | "
        f"{summary['profit']:+.1f}u | {summary['roi']:.1%} | "
        f"{summary['worst_season']:+.1f}u | {summary['drawdown']:+.1f}u"
    )


def _split_removed_text(rows: list[PickFeatureRow], seasons: set[int]) -> str:
    selected = [row for row in rows if row.season in seasons]
    return f"{sum(row.profit for row in selected):+.1f}u/{len(selected)}"


def _append_natural_veto_tests(lines: list[str], rows: list[PickFeatureRow]) -> None:
    veto_tests = [
        (
            "fumble_recovery_luck_edge >= 0.20",
            lambda row: row.fumble_recovery_luck_edge is not None
            and row.fumble_recovery_luck_edge >= 0.20,
        ),
        (
            "third_down_luck_support >= 0.12 and attempts >= 25",
            lambda row: row.third_down_luck_support is not None
            and row.third_down_luck_support >= 0.12
            and (row.third_down_attempts_combined or 0.0) >= 25,
        ),
        (
            "red_zone_luck_support >= 0.20 and trips >= 12",
            lambda row: row.red_zone_luck_support is not None
            and row.red_zone_luck_support >= 0.20
            and (row.red_zone_trips_combined or 0.0) >= 12,
        ),
        (
            "pressure_matchup_disadvantage >= 0.08",
            lambda row: row.pressure_matchup_disadvantage is not None
            and row.pressure_matchup_disadvantage >= 0.08,
        ),
        (
            "sack_conversion >= 0.50 and pressure <= league median",
            lambda row: row.sack_conversion_overperformance is not None
            and row.picked_defense_pressure_rate is not None
            and row.league_pressure_rate_median is not None
            and row.sack_conversion_overperformance >= 0.50
            and row.picked_defense_pressure_rate <= row.league_pressure_rate_median,
        ),
    ]

    lines.extend(
        [
            "",
            "## Natural Regression Veto Tests",
            "",
            "These tests use fixed natural thresholds, not q33/q66. A veto is useful only "
            "if it removes a small group with a much higher loss rate than the CORE baseline.",
            "",
            "| Veto | Removed | Removed W-L-P | Removed Loss% | Removed Profit | "
            "After Profit | After ROI | Worst Season | Max DD | Train Removed | "
            "Validation Removed | Holdout Removed | Pass? |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for name, predicate in veto_tests:
        removed = [row for row in rows if predicate(row)]
        kept = [row for row in rows if row not in removed]
        removed_summary = _summarize(removed)
        kept_summary = _summarize(kept)
        decisions = removed_summary["wins"] + removed_summary["losses"]
        removed_loss_rate = removed_summary["losses"] / decisions if decisions else 0.0
        passes = (
            2 <= removed_summary["bets"] <= 8
            and removed_summary["losses"] >= 2
            and removed_loss_rate >= 0.40
            and kept_summary["profit"] >= 128.7
            and kept_summary["roi"] >= 0.58
            and kept_summary["drawdown"] >= -6.3
        )
        lines.append(
            "| {name} | {removed_bets} | {removed_wins}-{removed_losses}-{removed_pushes} | "
            "{loss_rate:.1%} | {removed_profit:+.1f}u | {kept_profit:+.1f}u | "
            "{kept_roi:.1%} | {worst:+.1f}u | {dd:+.1f}u | {train} | {val} | "
            "{holdout} | {passes} |".format(
                name=name,
                removed_bets=removed_summary["bets"],
                removed_wins=removed_summary["wins"],
                removed_losses=removed_summary["losses"],
                removed_pushes=removed_summary["pushes"],
                loss_rate=removed_loss_rate,
                removed_profit=removed_summary["profit"],
                kept_profit=kept_summary["profit"],
                kept_roi=kept_summary["roi"],
                worst=kept_summary["worst_season"],
                dd=kept_summary["drawdown"],
                train=_split_removed_text(removed, TRAIN_SEASONS),
                val=_split_removed_text(removed, VALIDATION_SEASONS),
                holdout=_split_removed_text(removed, HOLDOUT_SEASONS),
                passes="yes" if passes else "no",
            )
        )


def write_gom_feature_veto_report(output_path: Path = DEFAULT_OUTPUT) -> Path:
    """Write a feature veto report against current GOM Stable/CORE champion."""

    rows = build_core_pick_feature_rows(SEASONS)
    baseline = _summarize(rows)
    feature_names = [
        "early_down_matchup_edge",
        "off_early_down_success_edge",
        "def_early_down_epa_allowed_edge",
    ]

    lines = [
        "# GOM Stable Feature Veto Report",
        "",
        "Baseline strategy: `variant_d_balanced, GOM, confidence>=85, edge>=4, "
        "week>=3, abs(handicap)<=7`",
        "",
        "Features are computed from prior weeks only. For Week N, the aggregation uses "
        "Weeks 1..N-1 from L2 play-by-play artifacts.",
        "",
        "## Baseline",
        "",
        "| Bets | W-L-P | Profit | ROI | Worst Season | Max DD |",
        "|---:|---:|---:|---:|---:|---:|",
        f"| {_format_summary(baseline)} |",
        "",
        "## Veto Tests",
        "",
        "Thresholds below are the 33rd percentile from train seasons 2017-2022 only. "
        "Each veto removes picks with feature value below that threshold.",
        "",
        "| Feature | Train q33 | Removed | Removed W-L-P | Removed Profit | "
        "After Profit | After ROI | Worst Season | Max DD | Train Removed | "
        "Validation Removed | Holdout Removed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for feature in feature_names:
        train_values = [
            value
            for row in rows
            if row.season in TRAIN_SEASONS
            for value in [_feature_value(row, feature)]
            if value is not None
        ]
        threshold = _quantile(train_values, 0.33)
        removed = [
            row
            for row in rows
            if (value := _feature_value(row, feature)) is not None and value < threshold
        ]
        kept = [row for row in rows if row not in removed]
        removed_summary = _summarize(removed)
        kept_summary = _summarize(kept)
        train_removed = [row for row in removed if row.season in TRAIN_SEASONS]
        val_removed = [row for row in removed if row.season in VALIDATION_SEASONS]
        hold_removed = [row for row in removed if row.season in HOLDOUT_SEASONS]
        lines.append(
            "| {feature} | {threshold:.4f} | {removed_bets} | "
            "{removed_wins}-{removed_losses}-{removed_pushes} | {removed_profit:+.1f}u | "
            "{kept_profit:+.1f}u | {kept_roi:.1%} | {worst:+.1f}u | {dd:+.1f}u | "
            "{train_profit:+.1f}u/{train_bets} | {val_profit:+.1f}u/{val_bets} | "
            "{hold_profit:+.1f}u/{hold_bets} |".format(
                feature=feature,
                threshold=threshold,
                removed_bets=removed_summary["bets"],
                removed_wins=removed_summary["wins"],
                removed_losses=removed_summary["losses"],
                removed_pushes=removed_summary["pushes"],
                removed_profit=removed_summary["profit"],
                kept_profit=kept_summary["profit"],
                kept_roi=kept_summary["roi"],
                worst=kept_summary["worst_season"],
                dd=kept_summary["drawdown"],
                train_profit=sum(row.profit for row in train_removed),
                train_bets=len(train_removed),
                val_profit=sum(row.profit for row in val_removed),
                val_bets=len(val_removed),
                hold_profit=sum(row.profit for row in hold_removed),
                hold_bets=len(hold_removed),
            )
        )

    _append_natural_veto_tests(lines, rows)

    lines.extend(
        [
            "",
            "## Feature Notes",
            "",
            "- `early_down_matchup_edge`: `(pick off early EPA + opponent def EPA allowed) "
            "- (opponent off early EPA + pick def EPA allowed)`.",
            "- `off_early_down_success_edge`: pick-team early-down success rate minus "
            "opponent early-down success rate.",
            "- `def_early_down_epa_allowed_edge`: opponent defense early-down EPA allowed "
            "minus pick-team defense early-down EPA allowed. Positive supports the pick.",
            "- Early-season samples use 100 pseudo-plays shrinkage to the league mean for "
            "the available prior weeks.",
            "- Fumble recovery is a play-description proxy: offensive fumbles not lost plus "
            "opponent fumbles lost are counted as recoveries for the team.",
            "- Third-down expected conversion is estimated from prior-week league conversion "
            "by distance bucket: short, medium, long.",
            "- Red-zone support uses prior red-zone plays as a reproducible proxy rather than "
            "true drive trips.",
            "- Pressure is based on the existing L2 `is_pressure` proxy; sack conversion uses "
            "sack text/play-type matches over pressure plays.",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
