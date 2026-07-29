"""V2 report service for Live Scenario.

This module is not wired into the legacy CLI or GUI yet. It builds the first
structured V2 report contract from a current game state and historical
team-game observations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from live_scenario.config import (
    DEFAULT_STABILITY_THRESHOLD_PP,
    HISTORICAL_WINDOWS,
    METHODOLOGY_VERSION,
    SAMPLE_UNIT,
    SCHEMA_VERSION,
    SHRINKAGE_PRIOR_WEIGHT,
    TIE_POLICIES,
)
from live_scenario.spread import PregameSpreadContext, build_pregame_spread_context
from live_scenario.state import (
    LiveCurrentState,
    margin_bucket_v2,
    parse_cumulative_state_path,
    parse_path,
)
from live_scenario.stats import sample_quality_v2

DEFAULT_WARNINGS = (
    "Historical context only. No automatic betting recommendation.",
    "Historical live profitability cannot be validated without archived live market prices.",
)


@dataclass(frozen=True)
class ScenarioLayerResult:
    name: str
    filters_applied: tuple[str, ...]
    filters_relaxed: tuple[str, ...]
    wins: int
    losses: int
    ties: int
    raw_probability: float | None
    league_reference_probability: float | None
    raw_delta_vs_league_pp: float | None
    adjusted_probability: float | None
    adjusted_delta_vs_league_pp: float | None
    adjustment_method: str | None
    prior_strength_k: int | None
    raw_probability_interval: tuple[float | None, float | None]
    adjusted_probability_interval: tuple[float | None, float | None]
    sample_size: int
    sample_quality: str
    opponent_league_reference_probability: float | None = None
    raw_delta_vs_opponent_league_pp: float | None = None
    adjusted_delta_vs_opponent_league_pp: float | None = None
    mirrored_filters_applied: tuple[str, ...] = ()
    # Backward-compatible alias. New consumers should use raw_delta_vs_league_pp.
    delta_vs_league_pp: float | None = None


@dataclass(frozen=True)
class MarketComparison:
    market_available: bool
    primary_probability_source: str
    tie_policy: str
    adjusted_historical_probability: float | None
    historical_win_probability: float | None
    historical_loss_probability: float | None
    historical_tie_probability: float | None
    team_a_live_decimal: float | None = None
    opponent_live_decimal: float | None = None
    team_a_implied_probability: float | None = None
    opponent_implied_probability: float | None = None
    team_a_no_vig_probability: float | None = None
    opponent_no_vig_probability: float | None = None
    historical_break_even_price: float | None = None
    edge_vs_market_pp: float | None = None
    estimated_ev: float | None = None


@dataclass(frozen=True)
class SampleReliability:
    exact_filtered_match: dict[str, Any]
    expanded_team_match: dict[str, Any]
    contextual_league_match: dict[str, Any]
    broad_league_baseline: dict[str, Any]
    spread_filter_levels: dict[str, Any]


@dataclass(frozen=True)
class LiveScenarioReport:
    schema_version: str
    methodology_version: str
    generated_at_utc: str
    data_cutoff_utc: str
    seasons_included: tuple[int, ...]
    games_included: int
    sample_unit: str
    excluded_games_count: int
    data_quality_warnings: tuple[str, ...]
    current_state: dict[str, Any]
    pregame_spread_context: dict[str, Any]
    broad_league_game_state_baseline: dict[str, Any]
    spread_conditioned_game_state_baseline: dict[str, Any]
    quarter_path_context: dict[str, Any]
    exact_combined_match: dict[str, Any]
    play_level_events: dict[str, Any]
    broad_baseline_without_spread: dict[str, Any]
    spread_conditioned_baseline: dict[str, Any]
    historical_windows: dict[str, Any]
    historical_window_stability: dict[str, Any]
    forum_content_summary: dict[str, Any]
    league_baseline: ScenarioLayerResult
    opponent_league_reference: ScenarioLayerResult
    team_a_history: ScenarioLayerResult
    opponent_recovery_history: ScenarioLayerResult
    market_comparison: MarketComparison
    sample_and_reliability: SampleReliability
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _state_to_dict(current_state: LiveCurrentState) -> dict[str, Any]:
    return {
        "team_a": current_state.team_a,
        "opponent": current_state.opponent,
        "completed_quarters": current_state.completed_quarters,
        "team_a_quarter_result_path": current_state.team_a_quarter_result_path,
        "opponent_quarter_result_path": current_state.opponent_quarter_result_path,
        "team_a_cumulative_state_path": current_state.team_a_cumulative_state_path,
        "opponent_cumulative_state_path": current_state.opponent_cumulative_state_path,
        "team_a_path": current_state.team_a_path,
        "opponent_path": current_state.opponent_path,
        "team_a_score": current_state.team_a_score,
        "opponent_score": current_state.opponent_score,
        "margin": current_state.margin,
        "margin_bucket": current_state.margin_bucket,
    }


def _filter_by_cumulative_path_and_margin(
    rows: pd.DataFrame,
    *,
    path: str,
    completed_quarters: int,
    margin_bucket: str,
) -> pd.DataFrame:
    data = rows.copy()
    for idx, result in enumerate(parse_cumulative_state_path(path), start=1):
        col = f"after_q{idx}_state_v2"
        if col not in data.columns:
            raise ValueError(f"Historical rows are missing required column: {col}")
        data = data[data[col] == result]
    margin_col = f"after_q{completed_quarters}_margin_bucket_v2"
    if margin_col not in data.columns:
        raise ValueError(f"Historical rows are missing required column: {margin_col}")
    return data[data[margin_col] == margin_bucket]


def _filter_by_cumulative_path(rows: pd.DataFrame, *, path: str) -> pd.DataFrame:
    data = rows.copy()
    for idx, result in enumerate(parse_cumulative_state_path(path), start=1):
        col = f"after_q{idx}_state_v2"
        if col not in data.columns:
            raise ValueError(f"Historical rows are missing required column: {col}")
        data = data[data[col] == result]
    return data


def _filter_by_quarter_path(
    rows: pd.DataFrame,
    *,
    path: str,
) -> pd.DataFrame:
    data = rows.copy()
    for idx, result in enumerate(parse_path(path), start=1):
        col = f"q{idx}_result"
        if col not in data.columns:
            raise ValueError(f"Historical rows are missing required column: {col}")
        data = data[data[col] == result]
    return data


def _round_probability(value: float | None) -> float | None:
    return round(value, 6) if value is not None else None


def _round_pp(value: float | None) -> float | None:
    return round(value, 4) if value is not None else None


def _wilson_interval(
    wins: int,
    sample: int,
    *,
    z: float = 1.96,
) -> tuple[float | None, float | None]:
    if sample <= 0:
        return (None, None)
    p = wins / sample
    denom = 1 + z**2 / sample
    center = (p + z**2 / (2 * sample)) / denom
    margin = z * ((p * (1 - p) / sample + z**2 / (4 * sample**2)) ** 0.5) / denom
    return (round(max(0.0, center - margin), 6), round(min(1.0, center + margin), 6))


def _beta_normal_interval(
    alpha: float,
    beta: float,
    *,
    z: float = 1.96,
) -> tuple[float | None, float | None]:
    total = alpha + beta
    if total <= 0:
        return (None, None)
    mean = alpha / total
    variance = (alpha * beta) / (total**2 * (total + 1))
    margin = z * (variance**0.5)
    return (round(max(0.0, mean - margin), 6), round(min(1.0, mean + margin), 6))


def _layer_result(
    *,
    name: str,
    data: pd.DataFrame,
    filters_applied: tuple[str, ...],
    filters_relaxed: tuple[str, ...] = (),
    league_probability: float | None = None,
    opponent_league_probability: float | None = None,
    mirrored_filters_applied: tuple[str, ...] = (),
) -> ScenarioLayerResult:
    counts = data["final_state"].value_counts().to_dict() if not data.empty else {}
    wins = int(counts.get("WIN", 0))
    losses = int(counts.get("LOSS", 0))
    ties = int(counts.get("TIE", 0))
    sample = int(len(data))
    raw_probability = wins / sample if sample else None
    raw_delta = None
    if raw_probability is not None and league_probability is not None:
        raw_delta = (raw_probability - league_probability) * 100
    raw_delta_vs_opponent = None
    if raw_probability is not None and opponent_league_probability is not None:
        raw_delta_vs_opponent = (raw_probability - opponent_league_probability) * 100

    adjusted_probability = None
    adjusted_delta = None
    adjusted_delta_vs_opponent = None
    adjustment_method = None
    prior_strength = None
    adjusted_interval = (None, None)
    prior_probability = (
        opponent_league_probability
        if opponent_league_probability is not None
        else league_probability
    )
    if (
        prior_probability is not None
        and raw_probability is not None
        and name != "league_baseline"
        and not name.endswith("_league_reference")
    ):
        prior_strength = SHRINKAGE_PRIOR_WEIGHT
        alpha_prior = prior_probability * prior_strength
        beta_prior = (1 - prior_probability) * prior_strength
        alpha_posterior = wins + alpha_prior
        beta_posterior = losses + ties + beta_prior
        adjusted_probability = alpha_posterior / (sample + prior_strength)
        if league_probability is not None:
            adjusted_delta = (adjusted_probability - league_probability) * 100
        if opponent_league_probability is not None:
            adjusted_delta_vs_opponent = (
                adjusted_probability - opponent_league_probability
            ) * 100
        adjustment_method = (
            "beta_binomial_shrinkage_to_opponent_league_reference"
            if opponent_league_probability is not None
            else "beta_binomial_shrinkage_to_league_baseline"
        )
        adjusted_interval = _beta_normal_interval(alpha_posterior, beta_posterior)

    return ScenarioLayerResult(
        name=name,
        filters_applied=filters_applied,
        filters_relaxed=filters_relaxed,
        wins=wins,
        losses=losses,
        ties=ties,
        raw_probability=_round_probability(raw_probability),
        league_reference_probability=_round_probability(league_probability),
        raw_delta_vs_league_pp=_round_pp(raw_delta),
        adjusted_probability=_round_probability(adjusted_probability),
        adjusted_delta_vs_league_pp=_round_pp(adjusted_delta),
        adjustment_method=adjustment_method,
        prior_strength_k=prior_strength,
        raw_probability_interval=_wilson_interval(wins, sample),
        adjusted_probability_interval=adjusted_interval,
        sample_size=sample,
        sample_quality=sample_quality_v2(sample),
        opponent_league_reference_probability=_round_probability(opponent_league_probability),
        raw_delta_vs_opponent_league_pp=_round_pp(raw_delta_vs_opponent),
        adjusted_delta_vs_opponent_league_pp=_round_pp(adjusted_delta_vs_opponent),
        mirrored_filters_applied=mirrored_filters_applied,
        delta_vs_league_pp=_round_pp(raw_delta),
    )


def _market_comparison(
    *,
    win_probability: float | None,
    loss_probability: float | None,
    tie_probability: float | None,
    tie_policy: str,
    team_a_live_decimal: float | None,
    opponent_live_decimal: float | None,
) -> MarketComparison:
    if tie_policy not in TIE_POLICIES:
        raise ValueError(f"Unsupported tie_policy: {tie_policy}")
    if team_a_live_decimal is not None and team_a_live_decimal <= 1:
        raise ValueError("team_a_live_decimal must be > 1.")
    if opponent_live_decimal is not None and opponent_live_decimal <= 1:
        raise ValueError("opponent_live_decimal must be > 1.")

    adjusted_probability = win_probability
    break_even = None
    if tie_policy == "TIE_AS_PUSH" and win_probability and loss_probability is not None:
        break_even = 1 + loss_probability / win_probability
    elif tie_policy == "TIE_AS_LOSS" and win_probability:
        break_even = 1 / win_probability

    if team_a_live_decimal is None and opponent_live_decimal is None:
        return MarketComparison(
            market_available=False,
            primary_probability_source="league_baseline",
            tie_policy=tie_policy,
            adjusted_historical_probability=adjusted_probability,
            historical_win_probability=win_probability,
            historical_loss_probability=loss_probability,
            historical_tie_probability=tie_probability,
            historical_break_even_price=break_even,
        )

    team_a_implied = 1 / team_a_live_decimal if team_a_live_decimal else None
    opponent_implied = 1 / opponent_live_decimal if opponent_live_decimal else None
    team_a_no_vig = None
    opponent_no_vig = None
    if team_a_implied is not None and opponent_implied is not None:
        total = team_a_implied + opponent_implied
        team_a_no_vig = team_a_implied / total if total else None
        opponent_no_vig = opponent_implied / total if total else None

    market_reference = team_a_no_vig if team_a_no_vig is not None else team_a_implied
    edge = None
    if adjusted_probability is not None and market_reference is not None:
        edge = round((adjusted_probability - market_reference) * 100, 4)

    ev = None
    if adjusted_probability is not None and team_a_live_decimal is not None:
        if tie_policy == "TIE_AS_PUSH" and loss_probability is not None:
            ev = round(adjusted_probability * (team_a_live_decimal - 1) - loss_probability, 6)
        elif tie_policy == "TIE_AS_LOSS":
            ev = round(adjusted_probability * team_a_live_decimal - 1, 6)

    return MarketComparison(
        market_available=True,
        primary_probability_source="league_baseline",
        tie_policy=tie_policy,
        adjusted_historical_probability=adjusted_probability,
        historical_win_probability=win_probability,
        historical_loss_probability=loss_probability,
        historical_tie_probability=tie_probability,
        team_a_live_decimal=team_a_live_decimal,
        opponent_live_decimal=opponent_live_decimal,
        team_a_implied_probability=team_a_implied,
        opponent_implied_probability=opponent_implied,
        team_a_no_vig_probability=team_a_no_vig,
        opponent_no_vig_probability=opponent_no_vig,
        historical_break_even_price=break_even,
        edge_vs_market_pp=edge,
        estimated_ev=ev,
    )


def _reliability_block(
    *,
    name: str,
    data: pd.DataFrame,
    filters_applied: list[str],
    filters_relaxed: list[str],
) -> dict[str, Any]:
    layer = _layer_result(
        name=name,
        data=data,
        filters_applied=tuple(filters_applied),
        filters_relaxed=tuple(filters_relaxed),
    )
    return {
        "name": layer.name,
        "filters_applied": list(layer.filters_applied),
        "filters_relaxed": list(layer.filters_relaxed),
        "sample_size": layer.sample_size,
        "wins": layer.wins,
        "losses": layer.losses,
        "ties": layer.ties,
        "raw_probability": layer.raw_probability,
        "sample_quality": layer.sample_quality,
    }


def _public_layer_block(
    *,
    name: str,
    data: pd.DataFrame,
    filters_applied: list[str],
    filters_relaxed: list[str],
    league_probability: float | None = None,
) -> dict[str, Any]:
    layer = _layer_result(
        name=name,
        data=data,
        filters_applied=tuple(filters_applied),
        filters_relaxed=tuple(filters_relaxed),
        league_probability=league_probability,
    )
    return asdict(layer)


def _empty_reliability_block(
    *,
    name: str,
    filters_applied: list[str],
    filters_relaxed: list[str],
    missing_columns: list[str] | None = None,
) -> dict[str, Any]:
    payload = _reliability_block(
        name=name,
        data=pd.DataFrame(columns=["final_state"]),
        filters_applied=filters_applied,
        filters_relaxed=filters_relaxed,
    )
    if missing_columns:
        payload["missing_columns"] = missing_columns
    return payload


def _spread_bucket_without_role(bucket: str | None) -> str | None:
    if not bucket or bucket == "UNKNOWN":
        return None
    for prefix in ("FAV_", "DOG_", "PK_"):
        if bucket.startswith(prefix):
            return bucket.removeprefix(prefix)
    return bucket


def _filter_exact_spread(
    data: pd.DataFrame,
    context: PregameSpreadContext,
) -> tuple[pd.DataFrame, list[str]]:
    if context.team_a_closing_spread is None:
        return data.iloc[0:0].copy(), ["team_a_closing_spread"]
    if "team_a_closing_spread" not in data.columns:
        return data.iloc[0:0].copy(), ["team_a_closing_spread"]
    spread = pd.to_numeric(data["team_a_closing_spread"], errors="coerce")
    return data[spread.round(3) == round(context.team_a_closing_spread, 3)], []


def _filter_spread_bucket(
    data: pd.DataFrame,
    context: PregameSpreadContext,
) -> tuple[pd.DataFrame, list[str]]:
    if context.spread_bucket == "UNKNOWN":
        return data.iloc[0:0].copy(), ["spread_bucket"]
    role_col = (
        "team_a_role"
        if "team_a_role" in data.columns
        else "role"
        if "role" in data.columns
        else None
    )
    bucket_col = (
        "team_a_spread_bucket"
        if "team_a_spread_bucket" in data.columns
        else "spread_bucket_v2"
        if "spread_bucket_v2" in data.columns
        else "spread_bucket"
        if "spread_bucket" in data.columns
        else None
    )
    missing = []
    if role_col is None:
        missing.append("team_a_role")
    if bucket_col is None:
        missing.append("spread_bucket")
    if missing:
        return data.iloc[0:0].copy(), missing

    unprefixed_bucket = _spread_bucket_without_role(context.spread_bucket)
    role_mask = data[role_col].astype(str).str.upper() == context.team_a_role
    bucket_series = data[bucket_col].astype(str).str.upper()
    bucket_mask = (bucket_series == context.spread_bucket) | (
        bucket_series == str(unprefixed_bucket).upper()
    )
    return data[role_mask & bucket_mask], []


def _filter_role_only(
    data: pd.DataFrame,
    context: PregameSpreadContext,
) -> tuple[pd.DataFrame, list[str]]:
    if context.team_a_role == "UNKNOWN":
        return data.iloc[0:0].copy(), ["team_a_role"]
    role_col = (
        "team_a_role"
        if "team_a_role" in data.columns
        else "role"
        if "role" in data.columns
        else None
    )
    if role_col is None:
        return data.iloc[0:0].copy(), ["team_a_role"]
    return data[data[role_col].astype(str).str.upper() == context.team_a_role], []


def _spread_conditioned_levels(
    *,
    base_rows: pd.DataFrame,
    pregame_context: PregameSpreadContext,
) -> dict[str, Any]:
    exact_rows, exact_missing = _filter_exact_spread(base_rows, pregame_context)
    bucket_rows, bucket_missing = _filter_spread_bucket(base_rows, pregame_context)
    role_rows, role_missing = _filter_role_only(base_rows, pregame_context)

    return {
        "exact_spread_match": (
            _empty_reliability_block(
                name="exact_spread_match",
                filters_applied=["cumulative_state_path", "margin_bucket", "exact_spread"],
                filters_relaxed=[],
                missing_columns=exact_missing,
            )
            if exact_missing
            else _reliability_block(
                name="exact_spread_match",
                data=exact_rows,
                filters_applied=["cumulative_state_path", "margin_bucket", "exact_spread"],
                filters_relaxed=[],
            )
        ),
        "spread_bucket_match": (
            _empty_reliability_block(
                name="spread_bucket_match",
                filters_applied=["cumulative_state_path", "margin_bucket", "spread_bucket"],
                filters_relaxed=["exact_spread"],
                missing_columns=bucket_missing,
            )
            if bucket_missing
            else _reliability_block(
                name="spread_bucket_match",
                data=bucket_rows,
                filters_applied=["cumulative_state_path", "margin_bucket", "spread_bucket"],
                filters_relaxed=["exact_spread"],
            )
        ),
        "role_only_match": (
            _empty_reliability_block(
                name="role_only_match",
                filters_applied=["cumulative_state_path", "margin_bucket", "team_a_role"],
                filters_relaxed=["exact_spread", "spread_bucket"],
                missing_columns=role_missing,
            )
            if role_missing
            else _reliability_block(
                name="role_only_match",
                data=role_rows,
                filters_applied=["cumulative_state_path", "margin_bucket", "team_a_role"],
                filters_relaxed=["exact_spread", "spread_bucket"],
            )
        ),
        "no_spread_baseline": _reliability_block(
            name="no_spread_baseline",
            data=base_rows,
            filters_applied=["cumulative_state_path", "margin_bucket"],
            filters_relaxed=["exact_spread", "spread_bucket", "team_a_role"],
        ),
    }


def _select_spread_conditioned_baseline(levels: dict[str, Any]) -> dict[str, Any]:
    for key in ("exact_spread_match", "spread_bucket_match", "role_only_match"):
        level = levels[key]
        if level.get("sample_size", 0) > 0:
            selected = dict(level)
            selected["selected_level"] = key
            return selected
    selected = dict(levels["no_spread_baseline"])
    selected["selected_level"] = "no_spread_baseline"
    return selected


def _spread_bucket_only_layer(
    *,
    base_rows: pd.DataFrame,
    pregame_context: PregameSpreadContext,
    league_probability: float | None,
) -> dict[str, Any]:
    rows, missing = _filter_spread_bucket(base_rows, pregame_context)
    if missing:
        payload = _empty_reliability_block(
            name="spread_conditioned_game_state_baseline",
            filters_applied=["cumulative_state_path", "margin_bucket", "spread_bucket"],
            filters_relaxed=[],
            missing_columns=missing,
        )
        payload["league_reference_probability"] = league_probability
        payload["raw_delta_vs_league_pp"] = None
        payload["adjusted_probability"] = None
        payload["adjusted_delta_vs_league_pp"] = None
        payload["adjustment_method"] = None
        payload["prior_strength_k"] = None
        payload["raw_probability_interval"] = (None, None)
        payload["adjusted_probability_interval"] = (None, None)
        return payload
    return _public_layer_block(
        name="spread_conditioned_game_state_baseline",
        data=rows,
        filters_applied=["cumulative_state_path", "margin_bucket", "spread_bucket"],
        filters_relaxed=[],
        league_probability=league_probability,
    )


def _play_level_events_summary(data: pd.DataFrame) -> dict[str, Any]:
    if "play_level_events_eligible" not in data.columns:
        return {
            "filters_applied": ["play_level_events_eligible == true"],
            "eligible_sample": 0,
            "excluded_sample": len(data),
            "eligible_unique_games": 0,
            "excluded_unique_games": int(data["game_id"].nunique()) if "game_id" in data else 0,
            "reason_for_exclusions": {
                "missing_play_level_events_eligible_column": len(data),
            },
        }
    eligible = data[data["play_level_events_eligible"] == True]  # noqa: E712
    excluded = data[data["play_level_events_eligible"] != True]  # noqa: E712
    reasons: dict[str, int] = {}
    if "score_reconciliation_status" in excluded.columns and not excluded.empty:
        reasons = {
            str(status): int(count)
            for status, count in excluded["score_reconciliation_status"].value_counts().items()
        }
    return {
        "filters_applied": ["play_level_events_eligible == true"],
        "eligible_sample": int(len(eligible)),
        "excluded_sample": int(len(excluded)),
        "eligible_unique_games": int(eligible["game_id"].nunique()) if "game_id" in eligible else 0,
        "excluded_unique_games": int(excluded["game_id"].nunique()) if "game_id" in excluded else 0,
        "reason_for_exclusions": reasons,
    }


def _filter_window(data: pd.DataFrame, *, start: int, end: int) -> pd.DataFrame:
    if "season" not in data.columns:
        return data.iloc[0:0].copy()
    seasons = pd.to_numeric(data["season"], errors="coerce")
    return data[(seasons >= start) & (seasons <= end)]


def _historical_window_results(base_rows: pd.DataFrame) -> dict[str, Any]:
    windows = {}
    for name, (start, end) in HISTORICAL_WINDOWS.items():
        window_rows = _filter_window(base_rows, start=start, end=end)
        block = _reliability_block(
            name=name.lower(),
            data=window_rows,
            filters_applied=["cumulative_state_path", "margin_bucket", "historical_window"],
            filters_relaxed=[],
        )
        block["historical_window"] = {"start": start, "end": end}
        windows[name] = block
    return windows


def _historical_window_stability(
    windows: dict[str, Any],
    *,
    threshold_pp: float,
) -> dict[str, Any]:
    probabilities = {
        name: block["raw_probability"]
        for name, block in windows.items()
        if block.get("raw_probability") is not None
    }
    if len(probabilities) < 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "threshold_pp": threshold_pp,
            "max_difference_pp": None,
            "probabilities": probabilities,
        }

    values = list(probabilities.values())
    max_difference_pp = round((max(values) - min(values)) * 100, 4)
    return {
        "status": "STABLE" if max_difference_pp <= threshold_pp else "UNSTABLE",
        "threshold_pp": threshold_pp,
        "max_difference_pp": max_difference_pp,
        "probabilities": probabilities,
    }


def _quarter_scores_for_summary(current_state: LiveCurrentState) -> list[dict[str, int]]:
    rows = []
    for idx, score in enumerate(current_state.quarter_scores, start=1):
        rows.append(
            {
                "quarter": idx,
                "team_a_points": score.team_a,
                "opponent_points": score.opponent,
            }
        )
    return rows


def _quarter_scores_q1_q2_q3(current_state: LiveCurrentState) -> dict[str, dict[str, int] | None]:
    payload: dict[str, dict[str, int] | None] = {}
    for idx in (1, 2, 3):
        key = f"q{idx}"
        if idx <= len(current_state.quarter_scores):
            score = current_state.quarter_scores[idx - 1]
            payload[key] = {"team_a_points": score.team_a, "opponent_points": score.opponent}
        else:
            payload[key] = None
    return payload


def _record(layer: ScenarioLayerResult) -> str:
    return f"{layer.wins}-{layer.losses}-{layer.ties}"


def _probability_delta_pp(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round((left - right) * 100, 4)


def _build_forum_content_summary(
    *,
    current_state: LiveCurrentState,
    pregame_context: PregameSpreadContext,
    broad_baseline: dict[str, Any],
    spread_conditioned: dict[str, Any],
    team_a: ScenarioLayerResult,
    opponent: ScenarioLayerResult,
    warnings: tuple[str, ...],
) -> dict[str, Any]:
    team_note = None
    if team_a.sample_size > 0 and team_a.raw_probability is not None:
        team_note = {
            "sample_size": team_a.sample_size,
            "raw_final_win_probability": team_a.raw_probability,
            "raw_delta_vs_league_pp": team_a.raw_delta_vs_league_pp,
            "adjusted_final_win_probability": team_a.adjusted_probability,
            "adjusted_delta_vs_league_pp": team_a.adjusted_delta_vs_league_pp,
        }
    opponent_note = None
    if opponent.sample_size > 0 and opponent.raw_probability is not None:
        opponent_note = {
            "opponent_specific_record": _record(opponent),
            "opponent_adjusted_probability": opponent.adjusted_probability,
            "opponent_specific_sample_quality": opponent.sample_quality,
        }

    warning = None
    if broad_baseline.get("sample_quality") in {"NO_DATA", "VERY_LOW"}:
        warning = "Small sample. Historical context only."
    elif warnings:
        warning = "Historical context only."

    return {
        "matchup": f"{current_state.team_a} vs {current_state.opponent}",
        "current_score": {
            "team_a": current_state.team_a_score,
            "opponent": current_state.opponent_score,
        },
        "quarter_scores": _quarter_scores_for_summary(current_state),
        "quarter_scores_q1_q2_q3": _quarter_scores_q1_q2_q3(current_state),
        "quarter_result_path": current_state.team_a_quarter_result_path,
        "opponent_quarter_result_path": current_state.opponent_quarter_result_path,
        "cumulative_state_path": current_state.team_a_cumulative_state_path,
        "opponent_cumulative_state_path": current_state.opponent_cumulative_state_path,
        "margin": current_state.margin,
        "margin_bucket": current_state.margin_bucket,
        "pregame_spread": pregame_context.team_a_closing_spread,
        "spread_bucket": pregame_context.spread_bucket,
        "broad_final_win_probability": broad_baseline.get("raw_probability"),
        "broad_sample_size": broad_baseline.get("sample_size"),
        "spread_conditioned_final_win_probability": spread_conditioned.get("raw_probability"),
        "spread_conditioned_sample_size": spread_conditioned.get("sample_size"),
        "spread_conditioned_level": spread_conditioned.get("selected_level"),
        "difference_vs_broad_pp": _probability_delta_pp(
            spread_conditioned.get("raw_probability"),
            broad_baseline.get("raw_probability"),
        ),
        "team_specific_note": team_note,
        "team_specific_record": _record(team_a) if team_a.sample_size else None,
        "team_specific_sample_quality": team_a.sample_quality,
        "opponent_specific_note": opponent_note,
        "opponent_specific_record": _record(opponent) if opponent.sample_size else None,
        "opponent_adjusted_probability": opponent.adjusted_probability,
        "warning": warning,
    }


def build_basic_after_q_report(
    *,
    current_state: LiveCurrentState,
    historical_rows: pd.DataFrame,
    data_cutoff_utc: str,
    generated_at_utc: str | None = None,
    team_a_live_decimal: float | None = None,
    opponent_live_decimal: float | None = None,
    tie_policy: str = "TIE_AS_LOSS",
    pregame_spread_context: PregameSpreadContext | None = None,
    stability_threshold_pp: float = DEFAULT_STABILITY_THRESHOLD_PP,
    excluded_games_count: int = 0,
    data_quality_warnings: tuple[str, ...] = (),
) -> LiveScenarioReport:
    completed = current_state.completed_quarters
    pregame_context = pregame_spread_context or build_pregame_spread_context()
    league_rows = _filter_by_cumulative_path_and_margin(
        historical_rows,
        path=current_state.team_a_cumulative_state_path,
        completed_quarters=completed,
        margin_bucket=current_state.margin_bucket,
    )
    league = _layer_result(
        name="league_baseline",
        data=league_rows,
        filters_applied=("cumulative_state_path", "margin_bucket"),
    )
    broad_game_state = _public_layer_block(
        name="broad_league_game_state_baseline",
        data=league_rows,
        filters_applied=["cumulative_state_path", "margin_bucket"],
        filters_relaxed=["quarter_result_path", "spread_bucket"],
    )

    team_rows = league_rows[league_rows["team"] == current_state.team_a]
    team_a = _layer_result(
        name="team_a_history",
        data=team_rows,
        filters_applied=("team", "cumulative_state_path", "margin_bucket"),
        league_probability=league.raw_probability,
    )

    opponent_bucket = margin_bucket_v2(-current_state.margin)
    opponent_league_rows = _filter_by_cumulative_path_and_margin(
        historical_rows,
        path=current_state.opponent_cumulative_state_path,
        completed_quarters=completed,
        margin_bucket=opponent_bucket,
    )
    opponent_league = _layer_result(
        name="opponent_league_reference",
        data=opponent_league_rows,
        filters_applied=("cumulative_state_path", "margin_bucket"),
        filters_relaxed=("team", "quarter_result_path", "spread_bucket"),
        mirrored_filters_applied=(
            "opponent_cumulative_state_path",
            "opponent_margin_bucket",
        ),
    )
    opponent_rows = opponent_league_rows
    opponent_rows = opponent_rows[opponent_rows["team"] == current_state.opponent]
    opponent = _layer_result(
        name="opponent_recovery_history",
        data=opponent_rows,
        filters_applied=("team", "opponent_cumulative_state_path", "opponent_margin_bucket"),
        opponent_league_probability=opponent_league.raw_probability,
        mirrored_filters_applied=(
            "opponent_cumulative_state_path",
            "opponent_margin_bucket",
        ),
    )
    quarter_path_rows = _filter_by_quarter_path(
        historical_rows,
        path=current_state.team_a_quarter_result_path,
    )
    quarter_path_context = _public_layer_block(
        name="quarter_path_context",
        data=quarter_path_rows,
        filters_applied=["quarter_result_path"],
        filters_relaxed=["cumulative_state_path", "margin_bucket", "spread_bucket"],
        league_probability=league.raw_probability,
    )
    exact_combined_rows = _filter_by_quarter_path(
        league_rows,
        path=current_state.team_a_quarter_result_path,
    )
    exact_combined = _public_layer_block(
        name="exact_combined_match",
        data=exact_combined_rows,
        filters_applied=["quarter_result_path", "cumulative_state_path", "margin_bucket"],
        filters_relaxed=["spread_bucket"],
        league_probability=league.raw_probability,
    )

    seasons = ()
    if "season" in historical_rows.columns:
        seasons = tuple(
            int(season)
            for season in sorted(historical_rows["season"].dropna().unique())
        )
    if "game_id" in historical_rows.columns:
        games_included = int(historical_rows["game_id"].nunique())
    else:
        games_included = int(len(historical_rows))

    team_path_rows = _filter_by_cumulative_path(
        historical_rows[historical_rows["team"] == current_state.team_a],
        path=current_state.team_a_cumulative_state_path,
    )
    broad_path_rows = _filter_by_cumulative_path(
        historical_rows,
        path=current_state.team_a_cumulative_state_path,
    )
    reliability = SampleReliability(
        exact_filtered_match=_reliability_block(
            name="exact_filtered_match",
            data=team_rows,
            filters_applied=["team", "cumulative_state_path", "margin_bucket"],
            filters_relaxed=[],
        ),
        expanded_team_match=_reliability_block(
            name="expanded_team_match",
            data=team_path_rows,
            filters_applied=["team", "cumulative_state_path"],
            filters_relaxed=["margin_bucket"],
        ),
        contextual_league_match=_reliability_block(
            name="contextual_league_match",
            data=league_rows,
            filters_applied=["cumulative_state_path", "margin_bucket"],
            filters_relaxed=["team"],
        ),
        broad_league_baseline=_reliability_block(
            name="broad_league_baseline",
            data=broad_path_rows,
            filters_applied=["cumulative_state_path"],
            filters_relaxed=["team", "margin_bucket"],
        ),
        spread_filter_levels=_spread_conditioned_levels(
            base_rows=league_rows,
            pregame_context=pregame_context,
        ),
    )
    broad_without_spread = reliability.spread_filter_levels["no_spread_baseline"]
    spread_conditioned = _select_spread_conditioned_baseline(reliability.spread_filter_levels)
    spread_bucket_layer = _spread_bucket_only_layer(
        base_rows=league_rows,
        pregame_context=pregame_context,
        league_probability=league.raw_probability,
    )
    play_level_events = _play_level_events_summary(league_rows)
    historical_windows = _historical_window_results(league_rows)
    window_stability = _historical_window_stability(
        historical_windows,
        threshold_pp=stability_threshold_pp,
    )
    forum_summary = _build_forum_content_summary(
        current_state=current_state,
        pregame_context=pregame_context,
        broad_baseline=broad_without_spread,
        spread_conditioned=spread_bucket_layer,
        team_a=team_a,
        opponent=opponent,
        warnings=DEFAULT_WARNINGS,
    )

    return LiveScenarioReport(
        schema_version=SCHEMA_VERSION,
        methodology_version=METHODOLOGY_VERSION,
        generated_at_utc=generated_at_utc or _utc_now(),
        data_cutoff_utc=data_cutoff_utc,
        seasons_included=seasons,
        games_included=games_included,
        sample_unit=SAMPLE_UNIT,
        excluded_games_count=excluded_games_count,
        data_quality_warnings=data_quality_warnings,
        current_state=_state_to_dict(current_state),
        pregame_spread_context=pregame_context.to_dict(),
        broad_league_game_state_baseline=broad_game_state,
        spread_conditioned_game_state_baseline=spread_bucket_layer,
        quarter_path_context=quarter_path_context,
        exact_combined_match=exact_combined,
        play_level_events=play_level_events,
        broad_baseline_without_spread=broad_without_spread,
        spread_conditioned_baseline=spread_conditioned,
        historical_windows=historical_windows,
        historical_window_stability=window_stability,
        forum_content_summary=forum_summary,
        league_baseline=league,
        opponent_league_reference=opponent_league,
        team_a_history=team_a,
        opponent_recovery_history=opponent,
        market_comparison=_market_comparison(
            win_probability=league.raw_probability,
            loss_probability=(
                round(league.losses / league.sample_size, 6) if league.sample_size else None
            ),
            tie_probability=(
                round(league.ties / league.sample_size, 6) if league.sample_size else None
            ),
            tie_policy=tie_policy,
            team_a_live_decimal=team_a_live_decimal,
            opponent_live_decimal=opponent_live_decimal,
        ),
        sample_and_reliability=reliability,
        warnings=DEFAULT_WARNINGS,
    )
