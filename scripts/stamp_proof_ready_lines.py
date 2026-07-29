from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stamp_config(
    *,
    config_path: Path,
    book: str,
    price: float,
    decision_ts_utc: str | None,
    odds_source: str,
    overwrite: bool,
) -> dict[str, Any]:
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if "matchups" not in payload or not isinstance(payload["matchups"], list):
        raise ValueError(f"Config must contain matchups list: {config_path}")

    timestamp = decision_ts_utc or _utc_now()
    changed = 0
    skipped = 0
    for matchup in payload["matchups"]:
        if not isinstance(matchup, dict):
            continue
        for field, value in (
            ("book", book),
            ("price", price),
            ("decision_ts_utc", timestamp),
            ("odds_source", odds_source),
            ("odds_snapshot_type", "decision"),
            ("market", "spread"),
            ("line", matchup.get("spread")),
        ):
            if overwrite or matchup.get(field) in (None, ""):
                matchup[field] = value
                changed += 1
            else:
                skipped += 1

    payload["proof_stamp"] = {
        "book": book,
        "price": price,
        "decision_ts_utc": timestamp,
        "odds_source": odds_source,
        "overwrite": overwrite,
        "stamped_at_utc": _utc_now(),
        "note": "Manual proof metadata stamp. Verify source authenticity before treating as market-grade proof.",
    }
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return {"changed": changed, "skipped": skipped, "timestamp": timestamp}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stamp weekly line YAML with proof-ready metadata.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--book", required=True)
    parser.add_argument("--price", type=float, default=-110)
    parser.add_argument("--decision-ts-utc")
    parser.add_argument("--odds-source", default="manual_snapshot")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = stamp_config(
        config_path=args.config,
        book=args.book,
        price=args.price,
        decision_ts_utc=args.decision_ts_utc,
        odds_source=args.odds_source,
        overwrite=args.overwrite,
    )
    print(f"changed={result['changed']}")
    print(f"skipped={result['skipped']}")
    print(f"decision_ts_utc={result['timestamp']}")


if __name__ == "__main__":
    main()
