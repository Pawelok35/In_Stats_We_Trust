"""
Backfill team metrics for a target week by copying values from earlier weeks when teams had a bye.

Usage example:

    python scripts/backfill_metrics.py --season 2025 --target-week 9 --schedule-week 10

This ensures that all teams scheduled for week 10 have L3/Core12/PowerScore rows for week 9,
copying the latest available data from earlier weeks when necessary.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import polars as pl

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from etl.mappers import _TEAM_ALIAS_MAP  # noqa: E402
from utils.config import load_settings  # noqa: E402
from utils.manifest import write_manifest  # noqa: E402


def _normalize_team(team: str) -> str:
    team = team.strip().upper()
    return _TEAM_ALIAS_MAP.get(team, team)


def _alias_candidates(team: str) -> set[str]:
    canonical = _normalize_team(team)
    aliases = {canonical}
    for alias, mapped in _TEAM_ALIAS_MAP.items():
        if mapped == canonical:
            aliases.add(alias.upper())
    return aliases


def _schedule_teams(data_root: Path, season: int, week: int) -> set[str]:
    schedule_path = data_root / "schedules" / f"{season}.parquet"
    if not schedule_path.exists():
        raise FileNotFoundError(f"Schedule dataset not found: {schedule_path}")
    schedule_df = pl.read_parquet(schedule_path)
    if schedule_df.is_empty():
        raise ValueError(f"Schedule dataset at {schedule_path} is empty.")
    if "week" in schedule_df.columns:
        schedule_df = schedule_df.filter(pl.col("week") == week)
    if schedule_df.is_empty():
        raise ValueError(f"No schedule entries for season {season} week {week}.")
    candidates: list[str] = []
    for column in ("home_team", "away_team", "team_a", "team_b", "TEAM", "OPP"):
        if column in schedule_df.columns:
            candidates.extend(schedule_df[column].drop_nulls().to_list())
    if not candidates:
        raise ValueError("Schedule parquet must contain team columns (home_team/away_team or team_a/team_b).")
    return {_normalize_team(code) for code in candidates}


def _layer_paths(season: int, week: int, data_root: Path) -> dict[str, Path]:
    return {
        "l3_team_week": data_root / "l3_team_week" / str(season) / f"{week}.parquet",
        "l4_core12": data_root / "l4_core12" / str(season) / f"{week}.parquet",
        "l4_powerscore": data_root / "l4_powerscore" / str(season) / f"{week}.parquet",
    }


def _team_column(layer: str) -> str:
    return "team" if layer == "l4_powerscore" else "TEAM"


def _load_frame(path: Path, team_column: str) -> pl.DataFrame:
    if not path.exists():
        return pl.DataFrame({team_column: pl.Series([], dtype=pl.Utf8)})
    df = pl.read_parquet(path)
    if team_column not in df.columns:
        raise ValueError(f"Column {team_column} not found in {path}")
    return df


def _coerce_to_schema(df: pl.DataFrame, schema: dict[str, pl.DataType]) -> pl.DataFrame:
    for column, dtype in schema.items():
        if column in df.columns:
            df = df.with_columns(pl.col(column).cast(dtype, strict=False))
        else:
            df = df.with_columns(pl.lit(None).cast(dtype, strict=False).alias(column))
    return df.select(list(schema.keys()))


def _find_latest_row(layer: str, canonical_team: str, search_weeks: Iterable[int], data_root: Path, season: int) -> pl.DataFrame | None:
    team_column = _team_column(layer)
    aliases = _alias_candidates(canonical_team)
    for wk in search_weeks:
        path = _layer_paths(season, wk, data_root)[layer]
        if not path.exists():
            continue
        df = pl.read_parquet(path)
        if team_column not in df.columns or df.is_empty():
            continue
        row = df.filter(pl.col(team_column).str.to_uppercase().is_in(aliases))
        if not row.is_empty():
            return row
    return None


CANONICAL_ORDER: dict[str, list[str]] = {
    "l3_team_week": [
        "season",
        "week",
        "TEAM",
        "drives",
        "plays",
        "epa_off_mean",
        "success_rate_off",
        "epa_def_mean",
        "success_rate_def",
        "tempo",
        "pressure_rate_def",
        "explosive_play_rate_off",
        "third_down_conv_off",
        "redzone_td_rate_off",
        "turnover_margin",
        "points_per_drive_off",
        "points_per_drive_def",
        "points_per_drive_diff",
        "ypp_off",
        "ypp_def",
        "ypp_diff",
    ],
    "l4_core12": [
        "season",
        "week",
        "TEAM",
        "core_epa_offense",
        "core_epa_defense",
        "success_rate_offense",
        "success_rate_defense",
        "explosive_play_rate_offense",
        "third_down_conversion_offense",
        "points_per_drive_diff",
        "yards_per_play_diff",
        "turnover_margin",
        "redzone_td_rate_offense",
        "pressure_rate_defense",
        "tempo",
        "core_epa_off",
        "core_epa_def",
        "core_sr_off",
        "core_sr_def",
        "core_explosive_play_rate_off",
        "core_third_down_conv",
        "core_ypp_diff",
        "core_turnover_margin",
        "core_points_per_drive_diff",
        "core_redzone_td_rate",
        "core_pressure_rate_def",
        "core_ed_sr_off",
    ],
    "l4_powerscore": [
        "season",
        "week",
        "team",
        "power_score",
    ],
}


def _write_layer(layer: str, df: pl.DataFrame, path: Path, season: int, week: int) -> None:
    team_column = _team_column(layer)
    df = df.with_columns(
        pl.col(team_column)
        .cast(pl.Utf8)
        .str.to_uppercase()
        .map_elements(_normalize_team, return_dtype=pl.Utf8)
        .alias(team_column)
    )
    order = CANONICAL_ORDER.get(layer)
    if order:
        available = [col for col in order if col in df.columns]
        remaining = [col for col in df.columns if col not in available]
        df = df.select(available + remaining)
    df = df.sort(team_column)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
    manifest_path = path.parent / f"{week}_manifest.json"
    write_manifest(
        path=path,
        manifest_path=manifest_path,
        layer=layer,
        season=season,
        week=week,
        rows=df.height,
        cols=df.width,
    )


def backfill_metrics(season: int, target_week: int, schedule_week: int, data_root: Path) -> None:
    teams_needed = _schedule_teams(data_root, season, schedule_week)
    layers = _layer_paths(season, target_week, data_root)
    search_weeks = list(range(target_week - 1, 0, -1))

    canonical_schemas: dict[str, dict[str, pl.DataType]] = {}
    for layer, target_path in layers.items():
        team_column = _team_column(layer)
        current_df = _load_frame(target_path, team_column)
        if current_df.is_empty():
            current_df = pl.DataFrame({team_column: pl.Series([], dtype=pl.Utf8)})
        existing = {_normalize_team(code) for code in current_df[team_column].to_list() if code}

        if layer not in canonical_schemas or not canonical_schemas[layer]:
            schema_candidates = []
            for wk in [w for w in range(target_week - 1, 0, -1)] + [target_week]:
                candidate_path = _layer_paths(season, wk, data_root)[layer]
                if candidate_path.exists():
                    schema_candidates.append(pl.read_parquet(candidate_path, n_rows=0).schema)
                    break
            canonical_schemas[layer] = schema_candidates[0] if schema_candidates else current_df.schema

        missing = sorted(team for team in teams_needed if team not in existing)
        if not missing:
            _write_layer(layer, current_df, target_path, season, target_week)
            continue

        rows: list[pl.DataFrame] = [current_df]
        template_schema = canonical_schemas.get(layer, current_df.schema)

        for team in missing:
            row = _find_latest_row(layer, team, search_weeks, data_root, season)
            if row is None or row.is_empty():
                print(f"[warn] Could not find fallback metrics for {team} ({layer}); skipping.")
                continue
            row = row.with_columns(
                [
                    pl.lit(season).alias("season") if "season" in row.columns else pl.lit(season),
                    pl.lit(target_week).alias("week") if "week" in row.columns else pl.lit(target_week),
                    pl.lit(team).alias(team_column),
                ]
            )
            if not template_schema:
                template_schema = row.schema
            row = _coerce_to_schema(row, template_schema)
            rows.append(row)

        # ensure all frames share identical schema
        if template_schema:
            rows = [_coerce_to_schema(frame, template_schema) for frame in rows]

        combined = pl.concat(rows, how="vertical_relaxed")
        combined = (
            combined
            .group_by(team_column)
            .agg([pl.all().last()])
            .sort(team_column)
        )
        for column in combined.columns:
            if isinstance(combined[column].dtype, pl.List):
                combined = combined.with_columns(pl.col(column).list.get(-1).alias(column))
        _write_layer(layer, combined, target_path, season, target_week)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill team metrics for a target week using earlier data.")
    parser.add_argument("--season", type=int, default=2025, help="Season to modify (default: 2025)")
    parser.add_argument("--target-week", type=int, default=9, help="Week to ensure metrics exist for (default: 9)")
    parser.add_argument(
        "--schedule-week",
        type=int,
        default=10,
        help="Week from the schedule whose teams should be covered (default: 10)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.season <= 0 or args.target_week <= 0 or args.schedule_week <= 0:
        raise SystemExit("[error] season and weeks must be positive integers")
    settings = load_settings()
    data_root = Path(settings.data_root)
    backfill_metrics(args.season, args.target_week, args.schedule_week, data_root)


if __name__ == "__main__":
    main()
