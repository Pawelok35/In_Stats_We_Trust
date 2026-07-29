from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_scenario.data_provider import (  # noqa: E402
    NflreadpyDataProvider,
    load_raw_schedules,
    raw_pbp_path,
    raw_schedules_path,
)
from live_scenario.dataset import (  # noqa: E402
    dataset_status,
    rebuild_processed_dataset,
    save_raw_pbp,
    save_raw_schedules,
    utc_now,
)

DEFAULT_START_SEASON = 2015
DEFAULT_END_SEASON = 2025


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync durable Live Scenario nflverse data.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--bootstrap", action="store_true")
    mode.add_argument("--refresh-current", action="store_true")
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--rebuild-derived", action="store_true")
    parser.add_argument("--start-season", type=int, default=DEFAULT_START_SEASON)
    parser.add_argument("--end-season", type=int, default=DEFAULT_END_SEASON)
    parser.add_argument("--season", type=int, help="Season for --refresh-current.")
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT / "data")
    parser.add_argument("--data-cutoff-utc")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def _seasons(args: argparse.Namespace) -> list[int]:
    return list(range(args.start_season, args.end_season + 1))


def _provider() -> NflreadpyDataProvider:
    return NflreadpyDataProvider()


def _write_pbp_by_season(
    data_root: Path,
    provider: NflreadpyDataProvider,
    seasons: list[int],
    *,
    force: bool,
) -> dict[int, int]:
    counts = {}
    missing = [
        season for season in seasons if force or not raw_pbp_path(data_root, season).exists()
    ]
    for season in missing:
        season_pbp = provider.load_pbp([season])
        if "season" not in season_pbp.columns:
            raise ValueError("PBP data must include season column.")
        season_pbp = season_pbp[season_pbp["season"].astype(int) == season].copy()
        save_raw_pbp(data_root, season, season_pbp, force=True)
    for season in seasons:
        path = raw_pbp_path(data_root, season)
        counts[season] = int(len(pd.read_parquet(path))) if path.exists() else 0
    return counts


def _write_schedules(
    data_root: Path,
    provider: NflreadpyDataProvider,
    seasons: list[int],
    *,
    force: bool,
) -> Path:
    path = raw_schedules_path(data_root)
    if path.exists() and not force:
        return path
    schedules = provider.load_schedules(seasons)
    save_raw_schedules(data_root, schedules, force=True)
    return path


def _print_manifest_summary(rows: pd.DataFrame, manifest: dict) -> None:
    print("[OK] Live Scenario processed dataset")
    print(f"validation_status: {manifest['validation_status']}")
    print(f"team_game_observations: {manifest['team_game_observations']}")
    print(f"unique_processed_games: {manifest['unique_processed_games']}")
    print("raw_pbp_rows_per_season:")
    for season, count in manifest["raw_pbp_rows_per_season"].items():
        print(f"  {season}: {count}")
    print("team_game_observations_per_season:")
    if not rows.empty:
        for season, count in rows.groupby("season").size().to_dict().items():
            print(f"  {int(season)}: {int(count)}")
    print("errors:", json.dumps(manifest.get("errors", [])))
    print("warnings:", json.dumps(manifest.get("warnings", [])))


def bootstrap(args: argparse.Namespace) -> None:
    seasons = _seasons(args)
    provider = _provider()
    _write_pbp_by_season(args.data_root, provider, seasons, force=args.force)
    _write_schedules(args.data_root, provider, seasons, force=args.force)
    rows, manifest = rebuild_processed_dataset(
        args.data_root,
        seasons=seasons,
        provider_name=provider.source_name,
        provider_version=provider.source_version,
        data_cutoff_utc=args.data_cutoff_utc,
    )
    _print_manifest_summary(rows, manifest)


def refresh_current(args: argparse.Namespace) -> None:
    if args.season is None:
        raise SystemExit("--season is required for --refresh-current.")
    provider = _provider()
    _write_pbp_by_season(args.data_root, provider, [args.season], force=True)
    existing = load_raw_schedules(args.data_root)
    latest = provider.load_schedules([args.season])
    if "season" not in latest.columns:
        raise ValueError("Schedules must include season column.")
    combined = pd.concat(
        [
            (
                existing[existing["season"].astype(int) != args.season]
                if not existing.empty
                else existing
            ),
            latest,
        ],
        ignore_index=True,
    )
    save_raw_schedules(args.data_root, combined, force=True)
    seasons = _seasons(args)
    rows, manifest = rebuild_processed_dataset(
        args.data_root,
        seasons=seasons,
        provider_name=provider.source_name,
        provider_version=provider.source_version,
        data_cutoff_utc=args.data_cutoff_utc,
    )
    _print_manifest_summary(rows, manifest)


def rebuild_derived(args: argparse.Namespace) -> None:
    seasons = _seasons(args)
    rows, manifest = rebuild_processed_dataset(
        args.data_root,
        seasons=seasons,
        provider_name="local_raw",
        provider_version="local_raw",
        data_cutoff_utc=args.data_cutoff_utc,
    )
    _print_manifest_summary(rows, manifest)


def validate_only(args: argparse.Namespace) -> None:
    seasons = _seasons(args)
    status = dataset_status(args.data_root, seasons=seasons)
    print(f"dataset_status: {status.status}")
    print(f"reason: {status.reason}")
    if status.manifest:
        print(json.dumps(status.manifest, indent=2, sort_keys=True))
    if status.status != "READY":
        raise SystemExit(1)


def main() -> None:
    args = parse_args()
    if args.data_cutoff_utc is None:
        args.data_cutoff_utc = utc_now()
    if args.bootstrap:
        bootstrap(args)
    elif args.refresh_current:
        refresh_current(args)
    elif args.rebuild_derived:
        rebuild_derived(args)
    elif args.validate_only:
        validate_only(args)


if __name__ == "__main__":
    main()
