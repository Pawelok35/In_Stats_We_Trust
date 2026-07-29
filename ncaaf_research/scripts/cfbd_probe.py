"""Probe CollegeFootballData API availability for NCAAF research."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import httpx

API_ROOT = "https://api.collegefootballdata.com"
OUTPUT_DIR = Path("ncaaf_research/data/probe")


def _request(endpoint: str, *, api_key: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    headers = {"Authorization": f"Bearer {api_key}"}
    response = httpx.get(
        f"{API_ROOT}{endpoint}",
        headers=headers,
        params=params,
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected response type for {endpoint}: {type(payload).__name__}")
    return payload


def _write_sample(name: str, rows: list[dict[str, Any]], limit: int = 5) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.json"
    path.write_text(
        json.dumps(rows[:limit], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def probe(year: int, week: int) -> list[str]:
    api_key = os.getenv("CFBD_API_KEY")
    if not api_key:
        return [
            "[BLOCKED] CFBD_API_KEY is not set.",
            "Set it first, e.g. $env:CFBD_API_KEY = 'your_api_key'",
        ]

    checks = [
        (
            "games",
            "/games",
            {"year": year, "week": week, "seasonType": "regular"},
        ),
        (
            "lines",
            "/lines",
            {"year": year, "week": week, "seasonType": "regular"},
        ),
        (
            "plays",
            "/plays",
            {"year": year, "week": week, "seasonType": "regular"},
        ),
    ]

    messages: list[str] = []
    for name, endpoint, params in checks:
        rows = _request(endpoint, api_key=api_key, params=params)
        path = _write_sample(f"{year}_week{week}_{name}", rows)
        messages.append(f"[OK] {name}: rows={len(rows)} sample={path}")
    return messages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe CFBD API endpoints for NCAAF research.")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--week", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for message in probe(args.year, args.week):
        print(message)


if __name__ == "__main__":
    main()
