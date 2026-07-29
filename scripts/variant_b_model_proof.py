from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.variant_b_audit import ACTION_TAGS, clean_team, safe_float, selected_model_margin

DEFAULT_DATA_ROOT = REPO_ROOT / "data"
DEFAULT_MANUAL_RESULTS = DEFAULT_DATA_ROOT / "results" / "manual_results.jsonl"


@dataclass(frozen=True)
class ProbabilityTriplet:
    p_cover: float
    p_push: float
    p_loss: float
    sample_size: int


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}:{line_no}: {exc}") from exc
        records.append(record)
    return records


def load_season_picks(picks_dir: Path, season: int) -> list[dict[str, Any]]:
    season_dir = picks_dir / str(season)
    if not season_dir.exists():
        raise FileNotFoundError(f"Pick directory does not exist: {season_dir}")
    records: list[dict[str, Any]] = []
    for path in sorted(season_dir.glob("week_*.jsonl")):
        records.extend(load_jsonl(path))
    return records


def load_manual_results(path: Path | None, season: int) -> dict[tuple[int, str, str], dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    results: dict[tuple[int, str, str], dict[str, Any]] = {}
    for record in load_jsonl(path):
        if int(record.get("season", 0)) != season:
            continue
        results[
            (
                int(record["week"]),
                clean_team(record["home_team"]),
                clean_team(record["away_team"]),
            )
        ] = {
            "home_score": record.get("home_score"),
            "away_score": record.get("away_score"),
        }
    return results


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def actual_selected_margin(pick: dict[str, Any], result: dict[str, Any]) -> float | None:
    home_score = result.get("home_score")
    away_score = result.get("away_score")
    if home_score is None or away_score is None:
        return None
    if isinstance(home_score, float) and math.isnan(home_score):
        return None
    if isinstance(away_score, float) and math.isnan(away_score):
        return None
    home = clean_team(pick.get("home"))
    away = clean_team(pick.get("away"))
    selected = clean_team(pick.get("model_winner"))
    home_margin = float(home_score) - float(away_score)
    if selected == home:
        return home_margin
    if selected == away:
        return -home_margin
    return None


def historical_residuals(
    *,
    picks_dir: Path,
    data_root: Path,
    seasons: list[int],
    tags: set[str],
    manual_results: Path | None,
) -> list[float]:
    residuals: list[float] = []
    for season in seasons:
        try:
            picks = load_season_picks(picks_dir, season)
        except FileNotFoundError:
            continue
        results = load_manual_results(manual_results, season)
        for pick in picks:
            tag = str(pick.get("tag") or "").upper()
            if tag not in tags:
                continue
            key = (int(pick["week"]), clean_team(pick["home"]), clean_team(pick["away"]))
            result = results.get(key)
            if not result:
                continue
            predicted = selected_model_margin(pick, clean_team(pick.get("model_winner")))
            actual = actual_selected_margin(pick, result)
            if predicted is None or actual is None:
                continue
            residuals.append(actual - predicted)
    return residuals


def probability_triplet(model_margin: float, selected_spread: float, residuals: list[float]) -> ProbabilityTriplet:
    covers = 0
    pushes = 0
    losses = 0
    # ATS margin = actual selected-team margin + selected-team spread.
    # Example: Rams -3 covers if actual margin + (-3) > 0.
    for residual in residuals:
        projected_margin = int(round(model_margin + residual))
        ats_margin = projected_margin + selected_spread
        if ats_margin > 0:
            covers += 1
        elif ats_margin == 0:
            pushes += 1
        else:
            losses += 1
    sample_size = len(residuals)
    if sample_size == 0:
        return ProbabilityTriplet(0.0, 0.0, 0.0, 0)
    return ProbabilityTriplet(
        p_cover=covers / sample_size,
        p_push=pushes / sample_size,
        p_loss=losses / sample_size,
        sample_size=sample_size,
    )


def margin_pmf(model_margin: float, residuals: list[float]) -> dict[str, float]:
    counts: dict[int, int] = {}
    for residual in residuals:
        projected_margin = int(round(model_margin + residual))
        counts[projected_margin] = counts.get(projected_margin, 0) + 1
    sample_size = len(residuals)
    if sample_size == 0:
        return {}
    return {str(margin): count / sample_size for margin, count in sorted(counts.items())}


def decimal_to_american(decimal_odds: float | None) -> int | None:
    if decimal_odds is None or decimal_odds <= 1:
        return None
    if decimal_odds >= 2:
        return int(round((decimal_odds - 1) * 100))
    return int(round(-100 / (decimal_odds - 1)))


def frontier_for_record(model_margin: float, residuals: list[float], min_ev: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for step in range(-30, 31):
        spread = step / 2
        probs = probability_triplet(model_margin, spread, residuals)
        if probs.sample_size == 0 or probs.p_cover <= 0:
            min_decimal = None
        else:
            min_decimal = 1 + (probs.p_loss + min_ev) / probs.p_cover
        rows.append(
            {
                "selected_team_spread": spread,
                "p_cover": round(probs.p_cover, 6),
                "p_push": round(probs.p_push, 6),
                "p_loss": round(probs.p_loss, 6),
                "minimum_decimal_odds": round(min_decimal, 6) if min_decimal else None,
                "minimum_american_odds": decimal_to_american(min_decimal),
            }
        )
    return rows


def enrich_record(
    record: dict[str, Any],
    *,
    residuals: list[float],
    proof_id: str,
    frontier_dir: Path,
    min_ev: float,
) -> dict[str, Any]:
    enriched = dict(record)
    selected = clean_team(record.get("model_winner"))
    model_margin = selected_model_margin(record, selected)
    spread = safe_float(record.get("handicap"))
    if model_margin is None or spread is None or not residuals:
        enriched["model_proof_status"] = "NOT_ASSESSABLE"
        enriched["model_proof_method"] = "EMPIRICAL_RESIDUAL_PMF_MVP"
        return enriched

    probs = probability_triplet(model_margin, spread, residuals)
    pmf = margin_pmf(model_margin, residuals)
    frontier = frontier_for_record(model_margin, residuals, min_ev)
    pick_id = f"{int(record.get('season', 0)):04d}_w{int(record.get('week', 0)):02d}_{clean_team(record.get('away'))}_at_{clean_team(record.get('home'))}_{selected}"
    frontier_path = frontier_dir / f"{pick_id}_acceptable_quote_frontier.json"
    frontier_path.parent.mkdir(parents=True, exist_ok=True)
    frontier_payload = {
        "schema_version": "variant_b_acceptable_quote_frontier.v1",
        "proof_id": proof_id,
        "method": "EMPIRICAL_RESIDUAL_PMF_MVP",
        "pick_id": pick_id,
        "selected_team": selected,
        "model_margin_selected_team": model_margin,
        "min_ev_per_unit": min_ev,
        "frontier": frontier,
    }
    frontier_path.write_text(json.dumps(frontier_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    pmf_path = frontier_dir / f"{pick_id}_margin_pmf.json"
    pmf_payload = {
        "schema_version": "variant_b_margin_pmf.v1",
        "proof_id": proof_id,
        "method": "EMPIRICAL_RESIDUAL_PMF_MVP",
        "pick_id": pick_id,
        "selected_team": selected,
        "model_margin_selected_team": model_margin,
        "sample_size": len(residuals),
        "margin_definition": "selected_team_score_minus_opponent_score",
        "margin_pmf": pmf,
        "probability_sum": round(sum(pmf.values()), 6),
    }
    pmf_path.write_text(json.dumps(pmf_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    enriched.update(
        {
            "p_cover": round(probs.p_cover, 6),
            "p_push": round(probs.p_push, 6),
            "p_loss": round(probs.p_loss, 6),
            "margin_distribution_id": proof_id,
            "margin_pmf_method": "EMPIRICAL_RESIDUAL_PMF_MVP",
            "margin_pmf_path": str(pmf_path.relative_to(REPO_ROOT)),
            "margin_pmf_sample_size": probs.sample_size,
            "margin_pmf_residual_mean": round(mean(residuals), 6),
            "margin_pmf_residual_std": round(pstdev(residuals), 6) if len(residuals) > 1 else 0.0,
            "acceptable_quote_frontier_id": proof_id,
            "acceptable_quote_frontier_path": str(frontier_path.relative_to(REPO_ROOT)),
            "model_proof_status": "EMPIRICAL_MVP",
            "model_proof_warning": (
                "Empirical residual PMF is an automated MVP proof layer, not a final calibrated model distribution."
            ),
        }
    )
    return enriched


def parse_seasons(value: str) -> list[int]:
    seasons: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            seasons.extend(range(int(start), int(end) + 1))
        else:
            seasons.append(int(part))
    return sorted(set(seasons))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Variant B model-proof probabilities from historical residuals.")
    parser.add_argument("--input", type=Path, required=True, help="Future pick JSONL to enrich.")
    parser.add_argument("--output", type=Path, required=True, help="Enriched pick JSONL output.")
    parser.add_argument("--variant", default="variant_m")
    parser.add_argument("--picks-dir", type=Path)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--manual-results", type=Path, default=DEFAULT_MANUAL_RESULTS)
    parser.add_argument("--train-seasons", default="2021-2025")
    parser.add_argument("--tag", action="append", help="Training tag filter. Defaults to action tags.")
    parser.add_argument("--min-ev", type=float, default=0.0)
    parser.add_argument("--frontier-dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input if args.input.is_absolute() else REPO_ROOT / args.input
    output_path = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    picks_dir = args.picks_dir or Path("data") / f"picks_{args.variant}"
    picks_dir = picks_dir if picks_dir.is_absolute() else REPO_ROOT / picks_dir
    data_root = args.data_root if args.data_root.is_absolute() else REPO_ROOT / args.data_root
    manual_results = args.manual_results if args.manual_results and args.manual_results.is_absolute() else (
        REPO_ROOT / args.manual_results if args.manual_results else None
    )
    frontier_dir = args.frontier_dir or output_path.parent / "frontiers"
    frontier_dir = frontier_dir if frontier_dir.is_absolute() else REPO_ROOT / frontier_dir
    tags = {tag.upper() for tag in args.tag} if args.tag else set(ACTION_TAGS)
    seasons = parse_seasons(args.train_seasons)

    residuals = historical_residuals(
        picks_dir=picks_dir,
        data_root=data_root,
        seasons=seasons,
        tags=tags,
        manual_results=manual_results,
    )
    proof_id = f"empirical_residual_pmf_{args.variant}_{min(seasons)}_{max(seasons)}_{utc_now_iso().replace(':', '').replace('-', '')}"
    records = load_jsonl(input_path)
    enriched = [
        enrich_record(record, residuals=residuals, proof_id=proof_id, frontier_dir=frontier_dir, min_ev=args.min_ev)
        for record in records
    ]
    write_jsonl(output_path, enriched)

    manifest = {
        "schema_version": "variant_b_model_proof_manifest.v1",
        "proof_id": proof_id,
        "method": "EMPIRICAL_RESIDUAL_PMF_MVP",
        "input": str(input_path.relative_to(REPO_ROOT)),
        "output": str(output_path.relative_to(REPO_ROOT)),
        "variant": args.variant,
        "train_seasons": seasons,
        "training_tags": sorted(tags),
        "residual_sample_size": len(residuals),
        "residual_mean": round(mean(residuals), 6) if residuals else None,
        "residual_std": round(pstdev(residuals), 6) if len(residuals) > 1 else None,
        "created_at_utc": utc_now_iso(),
    }
    manifest_path = output_path.with_suffix(".model_proof_manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"model_proof_output={output_path}")
    print(f"manifest={manifest_path}")
    print(f"residual_sample_size={len(residuals)}")


if __name__ == "__main__":
    main()
