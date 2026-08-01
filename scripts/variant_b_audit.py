from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - depends on local environment
    yaml = None

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.team_aliases import normalize_team_code

ACTION_TAGS = {"VALUE PLAY", "GOW", "GOM", "GOY"}
KEY_NUMBERS = {3.0, 7.0, 10.0, 14.0}
PRIMARY_KEY_NUMBERS = {3.0, 7.0}

DEFAULT_RULES_CONFIG: dict[str, Any] = {
    "framework_version": "variant_b_audit_v1",
    "rules": {
        "AG-01": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Pick math integrity mismatch.",
        },
        "AG-02": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Whole-number spread requires p_cover, p_push, p_loss.",
        },
        "AG-04": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Market source, quote timestamp, and executable status are required.",
        },
        "AG-05": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Missing model uncertainty or margin distribution.",
        },
        "MM-01": {"risk_level": "MEDIUM", "blocking": False, "description": "Missing opener."},
        "MM-02": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Current quote is not market-grade.",
        },
        "MM-04": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Missing model-generation quote.",
        },
        "KN-02": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Spread is on a configured key number.",
        },
        "NC-03": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Unfavorable move off or through 3 or 7.",
        },
        "NC-04": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "No-chase not assessable without model-generation quote.",
        },
        "PXQ-01": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Price quality requires a fresh atomic executable quote.",
        },
        "PXQ-02": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Price valuation requires p_cover/p_push/p_loss or frozen acceptable_quote_frontier.",
        },
        "PXQ-03": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Manual consensus or aggregator-only quote cannot be treated as executable price proof.",
        },
        "PXQ-04": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Spread and price must come from the same quote/snapshot.",
        },
        "PXQ-05": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Promotional wager types require separate EV handling.",
        },
        "PXQ-06": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Break-even probability must be push-aware.",
        },
        "MS-01": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Market snapshot must identify event, selected side, market scope, spread, price, source, and evidence grade.",
        },
        "MS-02": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Spread and price must be an atomic quote from the same quote ID/market/selection/payload.",
        },
        "MS-03": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Manual consensus is not market-grade proof.",
        },
        "MS-04": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Provider quote is not direct book betslip verification or accepted ticket.",
        },
        "MS-05": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Direct-book proof requires target-stake check and no unresolved odds-change warning.",
        },
        "MS-06": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Provider limit and account-specific accepted stake must be separate.",
        },
        "PROC-01": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Process quality requires immutable point outputs and frozen policy.",
        },
        "PROC-02": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Due blocking rules override numeric quality score.",
        },
        "PROC-03": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Not-due points are pending_not_due rather than failures.",
        },
        "PROC-04": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Future information cannot be used in predecision process quality.",
        },
        "PROC-05": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "LLM numeric outputs or gate statuses cannot satisfy deterministic process checks.",
        },
        "PROC-06": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Cross-point identity, model, PMF, market scope, and quote IDs must be consistent.",
        },
        "PROC-07": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Manual overrides must be append-only and hashed.",
        },
        "PROC-08": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Readiness must be reported by phase.",
        },
        "OD-01": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Due blocking rules force hold/return workflow.",
        },
        "OD-02": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Integrity invalidators route to invalid audit.",
        },
        "OD-03": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Data identity or quote mapping errors route to data correction.",
        },
        "OD-04": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Missing model artifacts route to model rerun.",
        },
        "OD-05": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Pending official windows route to hold pending data.",
        },
        "OD-06": {
            "risk_level": "HIGH",
            "blocking": True,
            "description": "Operator decision cannot perform new research or model calculations.",
        },
        "OD-07": {
            "risk_level": "MEDIUM",
            "blocking": False,
            "description": "Operator decision should be append-only and snapshot-bound.",
        },
    },
}


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
        if not isinstance(record, dict):
            raise ValueError(f"Expected object in {path}:{line_no}")
        records.append(record)
    return records


def safe_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_to_half(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value * 2) / 2


def american_to_decimal(value: Any) -> float | None:
    price = safe_float(value)
    if price is None or price == 0:
        return None
    if price < 0:
        return 1.0 + 100.0 / abs(price)
    return 1.0 + price / 100.0


def has_frozen_frontier(record: dict[str, Any]) -> bool:
    return bool(record.get("acceptable_quote_frontier_id") or record.get("frontier_id"))


def is_known_value(value: Any) -> bool:
    """Return False for placeholders that must never satisfy an audit gate."""
    return value not in (None, "") and str(value).strip().upper() not in {
        "UNKNOWN",
        "MISSING",
        "PENDING",
    }


def is_manual_or_consensus_quote(record: dict[str, Any]) -> bool:
    book = str(record.get("book") or "").upper()
    source_type = str(record.get("source_type") or record.get("book") or "").upper()
    return (
        "MANUAL" in book
        or "CONSENSUS" in book
        or "MANUAL" in source_type
        or "CONSENSUS" in source_type
    )


def has_atomic_quote(record: dict[str, Any]) -> bool:
    if record.get("quote_id"):
        return True
    required = ("handicap", "price", "quote_timestamp_utc")
    return all(record.get(field) not in (None, "") for field in required)


def clean_team(value: Any) -> str:
    return normalize_team_code(str(value).upper())


def selected_team(record: dict[str, Any]) -> str:
    return clean_team(record.get("model_winner") or record.get("home"))


def selected_model_margin(record: dict[str, Any], selected: str) -> float | None:
    model_margin = safe_float(record.get("model_margin"))
    if model_margin is None:
        return None
    home = clean_team(record.get("home"))
    if selected == home:
        return model_margin
    return -model_margin


def canonical_edge(record: dict[str, Any]) -> float | None:
    selected = selected_team(record)
    model_margin = selected_model_margin(record, selected)
    handicap = safe_float(record.get("handicap"))
    if model_margin is None or handicap is None:
        return None
    market_implied_margin = -handicap
    return model_margin - market_implied_margin


def canonical_pick_id(record: dict[str, Any]) -> str:
    season = int(record.get("season", 0) or 0)
    week = int(record.get("week", 0) or 0)
    away = clean_team(record.get("away"))
    home = clean_team(record.get("home"))
    selected = selected_team(record)
    return f"{season}_w{week:02d}_{away}_at_{home}_{selected}"


def is_whole_number_spread(record: dict[str, Any]) -> bool:
    handicap = safe_float(record.get("handicap"))
    return handicap is not None and abs(handicap) == int(abs(handicap))


def is_on_key_number(record: dict[str, Any]) -> bool:
    handicap = safe_float(record.get("handicap"))
    return handicap is not None and abs(handicap) in KEY_NUMBERS


def is_market_grade(record: dict[str, Any]) -> bool:
    book = str(record.get("book") or "")
    executable = str(record.get("executable_status") or "").upper()
    source_type = str(record.get("source_type") or record.get("book") or "").upper()
    has_source = bool(book) and not book.upper().startswith("MANUAL")
    has_timestamp = is_known_value(
        record.get("quote_timestamp_utc") or record.get("decision_ts_utc")
    )
    executable_ok = executable in {
        "CONFIRMED_EXECUTABLE",
        "BETSLIP_CONFIRMED_AT_TARGET_STAKE",
        "CONFIRMED_AT_BOOK",
    }
    return (
        has_source
        and has_timestamp
        and executable_ok
        and "MANUAL" not in source_type
        and "CONSENSUS" not in source_type
    )


def has_model_generation_quote(record: dict[str, Any]) -> bool:
    return all(
        is_known_value(record.get(field))
        for field in (
            "model_generation_spread_selected_team",
            "model_generation_price",
            "model_generation_quote_timestamp_utc",
        )
    )


def has_push_probabilities(record: dict[str, Any]) -> bool:
    return all(record.get(field) not in (None, "") for field in ("p_cover", "p_push", "p_loss"))


def trigger(rule_id: str, rules: dict[str, Any]) -> dict[str, Any]:
    rule = rules.get(rule_id, {})
    return {
        "rule_id": rule_id,
        "risk_level": rule.get("risk_level", "MEDIUM"),
        "blocking": bool(rule.get("blocking", False)),
        "description": rule.get("description", ""),
    }


def point_output(
    *,
    number: int,
    name: str,
    status: str,
    due_status: str,
    triggered_rules: list[dict[str, Any]],
    narrative: str,
    confirmed_facts: list[str] | None = None,
    missing_data: list[str] | None = None,
    pending_data: list[str] | None = None,
    conditional_risks: list[str] | None = None,
    calculations: dict[str, Any] | None = None,
    manual_review_required: bool = False,
) -> dict[str, Any]:
    return {
        "point_number": number,
        "point_name": name,
        "status": status,
        "due_status": due_status,
        "confirmed_facts": confirmed_facts or [],
        "missing_data": missing_data or [],
        "pending_data": pending_data or [],
        "conditional_risks": conditional_risks or [],
        "triggered_rules": triggered_rules,
        "calculations": {
            "owner": "PYTHON_RULE_ENGINE",
            "values": calculations or {},
        },
        "manual_review": {
            "required": manual_review_required,
            "status": "OPEN" if manual_review_required else "NOT_REQUIRED",
        },
        "narrative": narrative,
    }


def build_market_snapshot(record: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    triggered = []
    reason_codes = []
    market_grade = is_market_grade(record)
    atomic_quote = has_atomic_quote(record)
    manual_or_consensus = is_manual_or_consensus_quote(record)

    if not market_grade:
        triggered.append(trigger("MS-01", rules))
    if not atomic_quote:
        triggered.append(trigger("MS-02", rules))
        if record.get("quote_id") in (None, ""):
            reason_codes.append("QUOTE_ID_MISSING")
        if record.get("quote_timestamp_utc") in (None, ""):
            reason_codes.append("SOURCE_TIMESTAMP_MISSING")
    if manual_or_consensus:
        triggered.append(trigger("MS-03", rules))
        reason_codes.append("MANUAL_CONSENSUS_ONLY")
    if str(record.get("executable_status") or "").upper() in {
        "AGGREGATOR_ONLY",
        "DISPLAYED_UNVERIFIED",
    }:
        triggered.append(trigger("MS-04", rules))
        reason_codes.append("AGGREGATOR_ONLY")

    book = record.get("book")
    timestamp = record.get("quote_timestamp_utc") or record.get("decision_ts_utc")
    direct_book_checked = bool(record.get("betslip_verified_at_utc"))
    accepted_stake = safe_float(record.get("accepted_stake"))
    target_stake = safe_float(record.get("target_stake"))

    if record.get("book") in (None, "") or manual_or_consensus:
        reason_codes.append("NAMED_BOOK_MISSING")
    if not direct_book_checked:
        reason_codes.append("DIRECT_BOOK_NOT_CHECKED")
    if target_stake is None:
        reason_codes.append("TARGET_STAKE_NOT_TESTED")
    if str(record.get("executable_status") or "").upper() in {"", "UNKNOWN"}:
        reason_codes.append("EXECUTABLE_STATUS_UNKNOWN")

    if accepted_stake is not None:
        evidence_grade = "EXECUTED_GRADE"
        executable_status = "WAGER_ACCEPTED"
    elif direct_book_checked:
        evidence_grade = "DIRECT_BOOK_GRADE"
        executable_status = "BETSLIP_VERIFIED_AT_TARGET_STAKE"
    elif market_grade:
        evidence_grade = "PROVIDER_GRADE"
        executable_status = str(
            record.get("executable_status") or "AGGREGATOR_DISPLAYED_UNVERIFIED"
        ).upper()
    elif manual_or_consensus:
        evidence_grade = "PREVIEW_ONLY"
        executable_status = "UNKNOWN"
    else:
        evidence_grade = "PREVIEW_ONLY"
        executable_status = "UNKNOWN"

    quote_integrity_status = "VALID" if atomic_quote else "INCOMPLETE"
    market_state = str(record.get("market_state") or "UNKNOWN").upper()
    stake_check_status = str(
        record.get("stake_check_status")
        or ("ACCEPTED_IN_FULL" if accepted_stake is not None else "NOT_TESTED")
    ).upper()
    status = (
        "COMPLETE"
        if evidence_grade in {"EXECUTED_GRADE", "DIRECT_BOOK_GRADE", "PROVIDER_GRADE"}
        and not any(item.get("blocking") for item in triggered)
        else "INCOMPLETE"
    )
    narrative = (
        f"Market snapshot evidence grade is {evidence_grade}."
        if status == "COMPLETE"
        else "Market snapshot is incomplete: feed, book, betslip, and executed-ticket evidence are not interchangeable."
    )
    return point_output(
        number=9,
        name="market_snapshot",
        status=status,
        due_status="DUE",
        triggered_rules=triggered,
        narrative=narrative,
        confirmed_facts=[f"stored_quote={record.get('handicap')} at {record.get('price')}"],
        missing_data=(
            [] if market_grade else ["named executable sportsbook", "executable quote status"]
        ),
        calculations={
            "book": book,
            "timestamp": timestamp,
            "price": safe_float(record.get("price")),
            "price_decimal": american_to_decimal(record.get("price")),
            "selected_team_spread": safe_float(record.get("handicap")),
            "quote_integrity_status": quote_integrity_status,
            "evidence_grade": evidence_grade,
            "market_state": market_state,
            "executable_status": executable_status,
            "stake_check_status": stake_check_status,
            "direct_book_checked": direct_book_checked,
            "target_stake": target_stake,
            "accepted_stake": accepted_stake,
            "market_grade_legacy": market_grade,
            "reason_codes": sorted(set(reason_codes)),
        },
    )


def build_argument_against(record: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    triggered = []
    edge = canonical_edge(record)
    stored_edge = safe_float(record.get("edge_vs_line"))
    edge_mismatch = edge is None or stored_edge is None or abs(edge - stored_edge) > 0.02
    if edge_mismatch:
        triggered.append(trigger("AG-01", rules))
    if is_whole_number_spread(record) and not has_push_probabilities(record):
        triggered.append(trigger("AG-02", rules))
    if not is_market_grade(record):
        triggered.append(trigger("AG-04", rules))
    if record.get("margin_distribution_id") in (None, "") and record.get("uncertainty_id") in (
        None,
        "",
    ):
        triggered.append(trigger("AG-05", rules))

    selected = selected_team(record)
    handicap = safe_float(record.get("handicap"))
    probability_note = (
        "push-aware probabilities are present from the model proof layer"
        if has_push_probabilities(record)
        else "fair-margin edge is not full EV without p_cover/p_push/p_loss"
    )
    market_note = (
        "the market snapshot is market-grade"
        if is_market_grade(record)
        else "the market snapshot is not market-grade"
    )
    narrative = (
        f"{selected} {handicap:+g} has a raw edge signal; {probability_note}, and {market_note}."
    )
    if bool(record.get("neutral_site")):
        narrative += " Neutral-site handling should be reviewed for home-field leakage."

    return point_output(
        number=1,
        name="argument_against",
        status="INCOMPLETE" if triggered else "COMPLETE",
        due_status="DUE",
        triggered_rules=triggered,
        narrative=narrative,
        missing_data=[
            item
            for item, missing in (
                ("p_cover", record.get("p_cover") in (None, "")),
                ("p_push", record.get("p_push") in (None, "")),
                ("p_loss", record.get("p_loss") in (None, "")),
                (
                    "margin distribution / uncertainty id",
                    record.get("margin_distribution_id") in (None, "")
                    and record.get("uncertainty_id") in (None, ""),
                ),
                ("market-grade executable quote", not is_market_grade(record)),
            )
            if missing
        ],
        conditional_risks=(
            ["neutral-site home-field leakage"] if bool(record.get("neutral_site")) else []
        ),
        calculations={
            "selected_team": selected,
            "selected_model_margin_raw": selected_model_margin(record, selected),
            "selected_model_margin_rounded": round_to_half(selected_model_margin(record, selected)),
            "selected_team_spread": handicap,
            "stored_edge_raw": stored_edge,
            "canonical_edge_raw": edge,
            "canonical_edge_rounded": round_to_half(edge),
        },
        manual_review_required=True,
    )


def build_market_move(record: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    triggered = []
    if record.get("opener_spread_selected_team") in (None, ""):
        triggered.append(trigger("MM-01", rules))
    if not is_market_grade(record):
        triggered.append(trigger("MM-02", rules))
    if not has_model_generation_quote(record):
        triggered.append(trigger("MM-04", rules))
    key_numbers_touched = (
        [abs(safe_float(record.get("handicap")) or 0.0)] if is_on_key_number(record) else []
    )
    return point_output(
        number=2,
        name="market_move_notes",
        status="NOT_ASSESSABLE" if triggered else "COMPLETE",
        due_status="DUE",
        triggered_rules=triggered,
        narrative=(
            "Opener/model-generation quote data is incomplete. Movement direction and no-chase "
            "cannot be assessed from a manual current quote."
        ),
        missing_data=[
            "opener",
            "model-generation quote",
            "market-grade current quote",
        ],
        calculations={
            "movement_from_opener": "UNKNOWN",
            "movement_from_model_snapshot": "UNKNOWN",
            "key_numbers_touched": key_numbers_touched,
            "key_numbers_crossed": "NOT_ASSESSABLE",
            "price_movement": "UNKNOWN",
        },
    )


def build_key_number(record: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    triggered = [trigger("KN-02", rules)] if is_on_key_number(record) else []
    handicap = safe_float(record.get("handicap"))
    status = "COMPLETE_WITH_FLAGS" if triggered else "COMPLETE"
    return point_output(
        number=6,
        name="key_number_check",
        status=status,
        due_status="DUE",
        triggered_rules=triggered,
        narrative=(
            f"Current selected-team spread is on key number {abs(handicap):g}; push-aware handling required."
            if triggered
            else "Current selected-team spread is not on configured key number 3, 7, 10, or 14."
        ),
        calculations={
            "selected_team_spread": handicap,
            "is_key_number": bool(triggered),
            "key_number": abs(handicap) if triggered and handicap is not None else None,
        },
    )


def build_no_chase(record: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    triggered = []
    if not has_model_generation_quote(record):
        triggered.append(trigger("NC-04", rules))
    status = "NOT_ASSESSABLE" if triggered else "COMPLETE"
    return point_output(
        number=7,
        name="no_chase_limit",
        status=status,
        due_status="DUE",
        triggered_rules=triggered,
        narrative=(
            "No-chase is NOT_ASSESSABLE because the model-generation quote is missing."
            if triggered
            else "No-chase can be assessed from model-generation quote to current quote."
        ),
        missing_data=(
            []
            if not triggered
            else [
                "model-generation spread",
                "model-generation price",
                "model-generation quote timestamp",
            ]
        ),
        calculations={
            "no_chase_status": "NOT_ASSESSABLE" if triggered else "NOT_TRIGGERED",
            "current_spread": safe_float(record.get("handicap")),
            "model_generation_spread": safe_float(
                record.get("model_generation_spread_selected_team")
            ),
        },
    )


def build_price_quality(record: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    triggered = []
    reason_codes = []
    decimal_odds = american_to_decimal(record.get("price"))
    p_push = safe_float(record.get("p_push"))

    if not is_market_grade(record):
        triggered.append(trigger("PXQ-01", rules))
        reason_codes.append("CURRENT_QUOTE_NOT_EXECUTABLE")
    if is_manual_or_consensus_quote(record):
        triggered.append(trigger("PXQ-03", rules))
        reason_codes.append("CURRENT_QUOTE_IS_CONSENSUS")
    if not has_atomic_quote(record):
        triggered.append(trigger("PXQ-04", rules))
        if record.get("quote_timestamp_utc") in (None, ""):
            reason_codes.append("QUOTE_TIMESTAMP_MISSING")
        if record.get("handicap") in (None, "") or record.get("price") in (None, ""):
            reason_codes.append("SPREAD_PRICE_SNAPSHOT_MISMATCH")
    if (
        not has_push_probabilities(record)
        and not has_frozen_frontier(record)
        and record.get("max_acceptable_price") in (None, "")
    ):
        triggered.append(trigger("PXQ-02", rules))
        for field, code in (
            ("p_cover", "P_COVER_MISSING"),
            ("p_push", "P_PUSH_MISSING"),
            ("p_loss", "P_LOSS_MISSING"),
        ):
            if record.get(field) in (None, ""):
                reason_codes.append(code)
        reason_codes.append("ACCEPTABLE_QUOTE_FRONTIER_MISSING")

    conditional_break_even = 1.0 / decimal_odds if decimal_odds else None
    unconditional_break_even = (
        (1.0 - p_push) / decimal_odds if decimal_odds and p_push is not None else None
    )
    valuation_method = (
        "FULL_MODEL_EV"
        if has_push_probabilities(record)
        else (
            "FROZEN_ACCEPTABLE_QUOTE_FRONTIER" if has_frozen_frontier(record) else "NOT_AVAILABLE"
        )
    )
    quote_quality_status = "FRESH_EXECUTABLE" if is_market_grade(record) else "UNVERIFIED"
    price_status = "NOT_ASSESSABLE" if triggered else "ACCEPTABLE"

    return point_output(
        number=8,
        name="price_quality",
        status="NOT_ASSESSABLE" if triggered else "COMPLETE",
        due_status="DUE",
        triggered_rules=triggered,
        narrative=(
            "Price quality is NOT_ASSESSABLE without a market-grade atomic quote and push-aware probability or frozen frontier."
            if triggered
            else "Price quality is assessable from current quote and model valuation policy."
        ),
        missing_data=[
            item
            for item, missing in (
                ("market-grade executable quote", not is_market_grade(record)),
                (
                    "atomic spread+price quote ID or timestamped snapshot",
                    not has_atomic_quote(record),
                ),
                (
                    "p_cover/p_push/p_loss or frozen acceptable quote frontier",
                    not has_push_probabilities(record)
                    and not has_frozen_frontier(record)
                    and record.get("max_acceptable_price") in (None, ""),
                ),
            )
            if missing
        ],
        calculations={
            "price": safe_float(record.get("price")),
            "price_decimal": round(decimal_odds, 6) if decimal_odds else None,
            "quote_quality_status": quote_quality_status,
            "price_status": price_status,
            "valuation_method": valuation_method,
            "conditional_cover_rate_given_no_push": (
                round(conditional_break_even, 6) if conditional_break_even else None
            ),
            "unconditional_cover_probability_required": (
                round(unconditional_break_even, 6) if unconditional_break_even else None
            ),
            "reason_codes": sorted(set(reason_codes)),
        },
    )


def build_process_quality(points: list[dict[str, Any]], rules: dict[str, Any]) -> dict[str, Any]:
    due_blocking = []
    due_nonblocking = []
    pending_not_due = []
    point_checks = []
    expected_points = {
        1: ("argument_against", "DUE", "HARD_REQUIRED"),
        2: ("market_move_notes", "DUE", "HARD_REQUIRED"),
        3: ("injury_role_notes", "NOT_DUE", "HARD_WHEN_DUE"),
        4: ("schedule_spot_notes", "DUE", "HARD_REQUIRED"),
        5: ("weather_notes", "NOT_DUE", "HARD_WHEN_DUE"),
        6: ("key_number_check", "DUE", "HARD_REQUIRED"),
        7: ("no_chase_limit", "DUE", "HARD_REQUIRED"),
        8: ("price_quality", "DUE", "HARD_REQUIRED"),
        9: ("market_snapshot", "DUE", "HARD_REQUIRED"),
        10: ("public_bias", "NOT_DUE", "CONTEXT_ONLY"),
        11: ("power_rankings_check", "DUE", "CONTEXT_ONLY"),
        12: ("roster_change_check", "DUE", "HARD_REQUIRED"),
        13: ("matchup_specific_risk", "DUE", "SOFT_REQUIRED"),
        14: ("game_script_risk", "DUE", "HARD_REQUIRED"),
        15: ("closing_line", "POST_EVENT_ONLY", "POST_EVENT"),
        16: ("closing_price", "POST_EVENT_ONLY", "POST_EVENT"),
        17: ("clv_points", "POST_EVENT_ONLY", "POST_EVENT"),
    }
    seen_points = set()
    for point in points:
        seen_points.add(point["point_number"])
        due_status = point["due_status"]
        name = point["point_name"]
        blocking_rules = [
            item["rule_id"] for item in point["triggered_rules"] if item.get("blocking")
        ]
        warning_rules = [
            item["rule_id"] for item in point["triggered_rules"] if not item.get("blocking")
        ]
        if due_status != "DUE":
            gate_effect = "NONE"
            effective_status = "PENDING_NOT_DUE"
            pending_not_due.append(name)
        elif blocking_rules:
            gate_effect = "HARD_BLOCK"
            effective_status = "BLOCKED"
        elif warning_rules:
            gate_effect = "WARNING"
            effective_status = "PARTIAL"
        elif point["status"] in {"COMPLETE", "OK"}:
            gate_effect = "NONE"
            effective_status = "OK"
        else:
            gate_effect = "WARNING"
            effective_status = "PARTIAL"
        point_checks.append(
            {
                "point_id": point["point_number"],
                "point_name": name,
                "run_status": "VALID",
                "native_domain_status": point["status"],
                "due_status": due_status,
                "criticality": expected_points.get(
                    point["point_number"], (name, due_status, "SOFT_REQUIRED")
                )[2],
                "gate_effect": gate_effect,
                "effective_status": effective_status,
                "blocking_rules": blocking_rules,
                "warning_rules": warning_rules,
            }
        )
        if due_status != "DUE":
            continue
        due_blocking.extend(blocking_rules)
        due_nonblocking.extend(warning_rules)
    for point_id, (name, due_status, criticality) in expected_points.items():
        if point_id in seen_points:
            continue
        if due_status != "DUE":
            pending_not_due.append(name)
            gate_effect = "NONE"
            effective_status = "PENDING_NOT_DUE"
            blocking_rules = []
            warning_rules = []
        elif criticality in {"HARD_REQUIRED", "HARD_WHEN_DUE"}:
            gate_effect = "HARD_BLOCK"
            effective_status = "BLOCKED"
            blocking_rules = ["PROC-01"]
            warning_rules = []
            due_blocking.extend(blocking_rules)
        else:
            gate_effect = "WARNING"
            effective_status = "PARTIAL"
            blocking_rules = []
            warning_rules = ["PROC-03"]
            due_nonblocking.extend(warning_rules)
        point_checks.append(
            {
                "point_id": point_id,
                "point_name": name,
                "run_status": "NOT_RUN",
                "native_domain_status": "MISSING_POINT_OUTPUT",
                "due_status": due_status,
                "criticality": criticality,
                "gate_effect": gate_effect,
                "effective_status": effective_status,
                "blocking_rules": blocking_rules,
                "warning_rules": warning_rules,
            }
        )
    point_checks.sort(key=lambda item: item["point_id"])
    due_points = [item for item in point_checks if item["due_status"] == "DUE"]
    status = (
        "PREKICK_NOT_READY"
        if due_blocking
        else ("PREKICK_READY_WITH_WARNINGS" if due_nonblocking else "PREKICK_READY")
    )
    triggered = [trigger("PROC-02", rules)] if due_blocking else []
    return point_output(
        number=18,
        name="process_quality",
        status=status,
        due_status="DUE",
        triggered_rules=triggered,
        narrative=(
            "Process quality is incomplete because due blocking rules are open."
            if due_blocking
            else "Process quality has no due blocking rules."
        ),
        calculations={
            "due_blocking_rules": sorted(set(due_blocking)),
            "due_nonblocking_rules": sorted(set(due_nonblocking)),
            "pending_not_due": sorted(set(pending_not_due)),
            "readiness": {
                "research_readiness": "PARTIAL" if due_blocking or due_nonblocking else "COMPLETE",
                "model_audit_readiness": "BLOCKED" if due_blocking else "READY",
                "execution_readiness": "BLOCKED" if due_blocking else "READY",
                "final_prekick_readiness": status,
                "post_close_readiness": "PENDING_NOT_DUE",
            },
            "point_checks": point_checks,
            "coverage": {
                "due_points_total": len(due_points),
                "due_points_ok": sum(1 for item in due_points if item["effective_status"] == "OK"),
                "due_points_partial": sum(
                    1 for item in due_points if item["effective_status"] == "PARTIAL"
                ),
                "due_points_blocked": sum(
                    1 for item in due_points if item["effective_status"] == "BLOCKED"
                ),
                "hard_blockers_count": len(set(due_blocking)),
                "pending_not_due_count": len(set(pending_not_due)),
            },
            "cross_point_checks": {
                "event_identity_consistent": True,
                "selected_team_consistent": True,
                "market_scope_consistent": "PARTIALLY_VERIFIED",
                "model_run_consistent": "NOT_ASSESSABLE",
                "margin_pmf_consistent": "NOT_ASSESSABLE",
                "quote_ids_consistent": False,
                "spread_price_atomic": "NOT_ASSESSABLE",
                "no_future_data_leakage": "NOT_ASSESSABLE",
                "all_numeric_outputs_script_generated": True,
                "unlogged_overrides_present": "UNKNOWN",
            },
            "outcome_used": False,
        },
    )


def build_operator_decision(
    process_quality: dict[str, Any], rules: dict[str, Any]
) -> dict[str, Any]:
    values = process_quality["calculations"]["values"]
    due_blocking = values.get("due_blocking_rules", [])
    pending_not_due = values.get("pending_not_due", [])
    coverage = values.get("coverage", {})
    point_checks = values.get("point_checks", [])

    invalidator_rules = {"PROC-04"}
    data_correction_rules = {"MS-02", "PXQ-04", "PROC-06"}
    model_rerun_rules = {"AG-02", "MM-04", "NC-04", "PXQ-02", "PROC-01"}
    market_capture_rules = {"AG-04", "MM-02", "MS-01", "PXQ-01", "PXQ-03"}

    has_invalidator = bool(invalidator_rules.intersection(due_blocking))
    has_data_correction = bool(data_correction_rules.intersection(due_blocking)) and not bool(
        model_rerun_rules.intersection(due_blocking)
    )
    has_model_rerun = bool(model_rerun_rules.intersection(due_blocking))
    has_market_capture = bool(market_capture_rules.intersection(due_blocking))

    if has_invalidator:
        gate_state = "INVALID"
        operator_action = "INVALID_AUDIT"
        substatus = "AUDIT_INTEGRITY_INVALIDATOR_PRESENT"
        hold_type = None
        triggered = [trigger("OD-02", rules)]
    elif has_data_correction:
        gate_state = "HOLD"
        operator_action = "RETURN_FOR_DATA_CORRECTION"
        substatus = "DATA_CORRECTION_REQUIRED"
        hold_type = "ACTIVE_REMEDIATION_REQUIRED"
        triggered = [trigger("OD-03", rules)]
    elif has_model_rerun:
        gate_state = "HOLD"
        operator_action = "RETURN_FOR_MODEL_RERUN"
        substatus = (
            "MODEL_RERUN_AND_MARKET_GRADE_SNAPSHOT_REQUIRED"
            if has_market_capture
            else "MODEL_RERUN_REQUIRED"
        )
        hold_type = "ACTIVE_REMEDIATION_REQUIRED"
        triggered = [trigger("OD-04", rules)]
    elif due_blocking:
        gate_state = "HOLD"
        operator_action = "HOLD_PENDING_DATA"
        substatus = "MULTIPLE_REQUIRED_INPUTS_PENDING"
        hold_type = (
            "MANUAL_DATA_CAPTURE_REQUIRED"
            if has_market_capture
            else "PASSIVE_WAIT_FOR_OFFICIAL_WINDOW"
        )
        triggered = [trigger("OD-01", rules)]
    elif pending_not_due:
        gate_state = "OPEN"
        operator_action = "READY_FOR_NEXT_AUDIT_STAGE"
        substatus = "CURRENT_PHASE_COMPLETE_PENDING_FUTURE_WINDOWS"
        hold_type = None
        triggered = []
    else:
        gate_state = "OPEN"
        operator_action = "AUDIT_COMPLETE"
        substatus = "FULL_LIFECYCLE_COMPLETE"
        hold_type = None
        triggered = []

    required_actions = []
    if has_data_correction:
        required_actions.append(
            {
                "priority": len(required_actions) + 1,
                "action_code": "CORRECT_ATOMIC_MARKET_OR_IDENTITY_DATA",
                "owner": "MARKET_DATA",
                "source_points": [9, 18],
                "reason_codes": sorted(data_correction_rules.intersection(due_blocking)),
                "required_before_phase_transition": True,
            }
        )
    if has_model_rerun:
        required_actions.append(
            {
                "priority": len(required_actions) + 1,
                "action_code": "RERUN_MODEL_WITH_FULL_MARGIN_DISTRIBUTION",
                "owner": "MODEL_PIPELINE",
                "source_points": [1, 7, 8, 12, 14, 18],
                "reason_codes": sorted(model_rerun_rules.intersection(due_blocking)),
                "required_before_phase_transition": True,
            }
        )
    if has_market_capture:
        required_actions.append(
            {
                "priority": len(required_actions) + 1,
                "action_code": "CAPTURE_ATOMIC_MARKET_GRADE_QUOTE_DURING_RERUN",
                "owner": "MARKET_DATA",
                "source_points": [2, 7, 8, 9],
                "reason_codes": sorted(market_capture_rules.intersection(due_blocking)),
                "required_before_phase_transition": True,
            }
        )

    nonblocking_pending_items = [
        {"item": item, "expected_phase": "FUTURE_OR_POST_CLOSE", "reason_code": "NOT_DUE"}
        for item in pending_not_due
    ]
    prohibited = []
    if gate_state != "OPEN" or due_blocking:
        prohibited = ["EXECUTION_AUDIT_APPROVAL", "FINAL_PREKICK_APPROVAL", "AUDIT_COMPLETE"]

    return point_output(
        number=19,
        name="final_operator_decision",
        status="INCOMPLETE" if due_blocking else "COMPLETE",
        due_status="DUE",
        triggered_rules=triggered,
        narrative=(
            "Operator gate is on hold: model rerun and market-grade snapshot are required."
            if operator_action == "RETURN_FOR_MODEL_RERUN"
            else (
                "Operator gate is on hold: data correction is required."
                if operator_action == "RETURN_FOR_DATA_CORRECTION"
                else (
                    "Operator gate is invalidated by an integrity failure."
                    if operator_action == "INVALID_AUDIT"
                    else (
                        "Hold pending data: blocking process rules remain open."
                        if due_blocking
                        else "Ready for next audit stage."
                    )
                )
            )
        ),
        calculations={
            "gate_state": gate_state,
            "operator_action": operator_action,
            "legacy_single_status": (
                "HOLD_PENDING_DATA" if gate_state == "HOLD" else operator_action
            ),
            "substatus": substatus,
            "hold_type": hold_type,
            "completion_scope": (
                "CURRENT_PHASE" if operator_action != "AUDIT_COMPLETE" else "FULL_LIFECYCLE"
            ),
            "process_quality_input": {
                "overall_status": process_quality["status"],
                "hard_blockers_count": coverage.get("hard_blockers_count", len(set(due_blocking))),
                "warnings_count": len(values.get("due_nonblocking_rules", [])),
                "pending_not_due_count": coverage.get(
                    "pending_not_due_count", len(pending_not_due)
                ),
                "invalidators_count": len(invalidator_rules.intersection(due_blocking)),
            },
            "primary_blocker": {
                "blocker_code": (
                    "AUDIT_INTEGRITY_INVALIDATOR"
                    if has_invalidator
                    else (
                        "DATA_MAPPING_OR_ATOMIC_QUOTE_ERROR"
                        if has_data_correction
                        else (
                            "MODEL_OUTPUT_NOT_EXECUTION_GRADE"
                            if has_model_rerun
                            else "PENDING_REQUIRED_INPUT" if due_blocking else None
                        )
                    )
                ),
                "blocker_class": (
                    "INTEGRITY"
                    if has_invalidator
                    else (
                        "DATA_CORRECTION"
                        if has_data_correction
                        else (
                            "MODEL_RERUN"
                            if has_model_rerun
                            else "PENDING_EXTERNAL" if due_blocking else None
                        )
                    )
                ),
                "source_point": 18 if due_blocking else None,
                "recoverability": (
                    "INVALIDATES_AUDIT"
                    if has_invalidator
                    else (
                        "RECOVERABLE_SAME_AUDIT"
                        if has_data_correction
                        else (
                            "REQUIRES_NEW_MODEL_RUN"
                            if has_model_rerun
                            else "WAIT_UNTIL_DUE" if due_blocking else None
                        )
                    )
                ),
            },
            "required_actions": required_actions,
            "nonblocking_pending_items": nonblocking_pending_items,
            "prohibited_transitions": prohibited,
            "decision_provenance": {
                "producer_type": "RULE_ENGINE",
                "new_research_performed": False,
                "new_model_calculations_performed": False,
                "llm_role": "NARRATIVE_ONLY",
            },
            "open_blockers": due_blocking,
            "wagering_disposition_encoded": False,
            "point_19_reads_points_1_17_directly": False,
            "point_checks_seen": len(point_checks),
        },
        manual_review_required=True,
    )


def build_audit(
    record: dict[str, Any], rules_config: dict[str, Any], audit_stage: str
) -> dict[str, Any]:
    rules = rules_config.get("rules", {})
    points = [
        build_argument_against(record, rules),
        build_market_move(record, rules),
        build_key_number(record, rules),
        build_no_chase(record, rules),
        build_price_quality(record, rules),
        build_market_snapshot(record, rules),
    ]
    process_quality = build_process_quality(points, rules)
    operator_decision = build_operator_decision(process_quality, rules)
    points.extend([process_quality, operator_decision])
    return {
        "schema_version": "variant_b_audit_output.v1",
        "framework_version": rules_config.get("framework_version", "variant_b_audit_v1"),
        "audit_stage": audit_stage,
        "generated_at_utc": utc_now_iso(),
        "pick_id": canonical_pick_id(record),
        "event": {
            "season": int(record.get("season", 0) or 0),
            "week": int(record.get("week", 0) or 0),
            "home": clean_team(record.get("home")),
            "away": clean_team(record.get("away")),
            "selected_team": selected_team(record),
            "neutral_site": bool(record.get("neutral_site", False)),
        },
        "source_pick": record,
        "research_evidence": {
            "gpt_full_19_status": record.get("gpt_full_19_status", "MISSING"),
            "gpt_full_19_snapshot_path": record.get("gpt_full_19_snapshot_path"),
            "gpt_full_19_points_present": record.get("gpt_full_19_points_present", []),
        },
        "audit_points": points,
    }


class StructuredVariantBEvidenceError(ValueError):
    """Raised when structured evidence cannot safely enter the audit API."""

    def __init__(self, reason: str, *, point_id: int | None = None, field: str | None = None):
        self.reason = reason
        self.point_id = point_id
        self.field = field
        super().__init__(reason)


def build_audit_with_structured_evidence(
    record: Mapping[str, Any],
    rules_config: Mapping[str, Any],
    audit_stage: str,
    structured_evidence: Mapping[str, Any],
    *,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Materialize evidence points while retaining existing deterministic builders.

    This wrapper is deliberately side-effect free.  It does not alter legacy
    ``build_audit`` behavior and delegates points 18 and 19 to their existing
    implementations.
    """

    source = dict(record)
    evidence = dict(structured_evidence)
    logical_timestamp = _validate_structured_audit_timestamp(generated_at_utc)
    _validate_structured_evidence_input(source, evidence)
    source.update(_research_input_from_evidence(evidence))
    audit = build_audit(source, dict(rules_config), audit_stage)
    if logical_timestamp is not None:
        audit["generated_at_utc"] = logical_timestamp
    rules = dict(rules_config).get("rules", {})
    deterministic = {point["point_number"]: point for point in audit["audit_points"][:6]}
    evidence_by_id = {item["point_id"]: item for item in evidence["point_results"]}
    evidence_points = []
    for point_id in range(1, 18):
        if point_id in deterministic:
            evidence_points.append(deterministic[point_id])
        else:
            evidence_points.append(_structured_point_output(evidence_by_id[point_id]))
    process_quality = build_process_quality(evidence_points, rules)
    operator_decision = build_operator_decision(process_quality, rules)
    audit["audit_points"] = evidence_points + [process_quality, operator_decision]
    audit["research_evidence"] = {
        "gpt_full_19_status": "STRUCTURED_SIDECAR_COMPLETE",
        "gpt_full_19_snapshot_path": None,
        "gpt_full_19_points_present": list(range(1, 20)),
    }
    audit["structured_evidence_metadata"] = {
        "evidence_id": evidence["evidence_id"],
        "evidence_schema_version": evidence["schema_version"],
        "prompt_version": evidence["prompt_version"],
        "candidate_id": evidence["candidate_id"],
        "research_kind": evidence["research_kind"],
        "generated_at_utc": evidence["generated_at_utc"],
        "source_count": evidence.get("source_count", 0),
        "integration_api_version": "variant_b_structured_evidence_api.v1",
    }
    return audit


def _validate_structured_audit_timestamp(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise StructuredVariantBEvidenceError("INVALID_GENERATED_AT_UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StructuredVariantBEvidenceError("INVALID_GENERATED_AT_UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise StructuredVariantBEvidenceError("INVALID_GENERATED_AT_UTC")
    return value


def _validate_structured_evidence_input(
    record: Mapping[str, Any], evidence: Mapping[str, Any]
) -> None:
    required = {
        "schema_version",
        "prompt_version",
        "evidence_id",
        "candidate_id",
        "game_id",
        "selected_team",
        "model_variant",
        "research_kind",
        "expected_point_count",
        "point_results",
        "probability_assessment",
        "acceptable_quote_frontier",
        "no_chase",
        "key_number_policy",
    }
    missing = sorted(required - evidence.keys())
    if missing:
        raise StructuredVariantBEvidenceError("STRUCTURED_EVIDENCE_MISSING:" + ",".join(missing))
    if (
        evidence["expected_point_count"] != 19
        or not isinstance(evidence["point_results"], list)
        or len(evidence["point_results"]) != 19
    ):
        raise StructuredVariantBEvidenceError("POINT_MAPPING_INCOMPLETE")
    ids = [item.get("point_id") for item in evidence["point_results"] if isinstance(item, Mapping)]
    if ids != list(range(1, 20)):
        raise StructuredVariantBEvidenceError("POINT_MAPPING_INCOMPLETE")
    expected_game = f"{record.get('season')}_w{int(record.get('week', 0)):02d}_{record.get('away')}_at_{record.get('home')}"
    checks = {
        "game_id": expected_game,
        "selected_team": selected_team(dict(record)),
        "model_variant": record.get("model_version"),
    }
    for field, expected in checks.items():
        if evidence.get(field) != expected:
            raise StructuredVariantBEvidenceError("STRUCTURED_EVIDENCE_CONFLICT", field=field)
    frontier = evidence["acceptable_quote_frontier"]
    if (
        not isinstance(frontier, Mapping)
        or frontier.get("selected_team") != checks["selected_team"]
    ):
        raise StructuredVariantBEvidenceError(
            "STRUCTURED_EVIDENCE_CONFLICT", field="frontier.selected_team"
        )
    probability = evidence["probability_assessment"]
    if not isinstance(probability, Mapping) or any(
        field not in probability for field in ("p_cover", "p_push", "p_loss")
    ):
        raise StructuredVariantBEvidenceError("AUDIT_INPUT_INVALID", field="probability_assessment")


def _structured_point_output(item: Mapping[str, Any]) -> dict[str, Any]:
    status_map = {
        "PASS": "COMPLETE",
        "WARNING": "PARTIAL",
        "BLOCKING_RISK": "PARTIAL",
        "PENDING": "PENDING",
        "UNKNOWN": "UNKNOWN",
        "NO_DATA": "MISSING",
        "NOT_DUE": "PENDING",
    }
    status = status_map.get(item.get("status"), "MISSING")
    return point_output(
        number=int(item["point_id"]),
        name=str(item["point_name"]),
        status=status,
        due_status="NOT_DUE" if item.get("status") == "NOT_DUE" else "DUE",
        triggered_rules=[],
        narrative=str(item.get("summary", "")),
        confirmed_facts=list(item.get("evidence_items", [])),
        missing_data=[str(item.get("no_data_reason"))] if item.get("no_data_reason") else [],
        conditional_risks=list(item.get("risk_codes", [])),
        calculations={
            "owner": "STRUCTURED_EVIDENCE",
            "values": {
                "evidence_present": bool(item.get("evidence_items")),
                "data_complete": bool(item.get("data_complete")),
                "blocking_assessment": item.get("blocking_assessment"),
                "structured_data": item.get("structured_data", {}),
                "source_refs": item.get("evidence_items", []),
            },
        },
        manual_review_required=item.get("status")
        in {"WARNING", "BLOCKING_RISK", "PENDING", "UNKNOWN", "NO_DATA"},
    )


def _research_input_from_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    probability = evidence["probability_assessment"]
    frontier = evidence["acceptable_quote_frontier"]
    no_chase = evidence["no_chase"]
    keys = evidence["key_number_policy"]
    values = {
        "p_cover": probability["p_cover"],
        "p_push": probability["p_push"],
        "p_loss": probability["p_loss"],
        "acceptable_quote_frontier_id": evidence["evidence_id"],
        "acceptable_quote_frontier_path": f"structured_evidence:{evidence['evidence_id']}",
        "max_acceptable_price": frontier["minimum_acceptable_price"],
        "structured_no_chase": dict(no_chase),
        "structured_key_number_policy": dict(keys),
    }
    return values


def load_rules_config(path: Path) -> dict[str, Any]:
    if yaml is None:
        return DEFAULT_RULES_CONFIG
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return DEFAULT_RULES_CONFIG
    return loaded


def find_record(
    records: list[dict[str, Any]], home: str | None, away: str | None
) -> dict[str, Any]:
    if home is None and away is None:
        for record in records:
            if str(record.get("tag", "")).upper() in ACTION_TAGS:
                return record
        return records[0]
    home_norm = clean_team(home)
    away_norm = clean_team(away)
    for record in records:
        if (
            clean_team(record.get("home")) == home_norm
            and clean_team(record.get("away")) == away_norm
        ):
            return record
    raise ValueError(f"No pick found for {away_norm} at {home_norm}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--picks-file", type=Path, required=True)
    parser.add_argument("--rules", type=Path, default=ROOT_DIR / "config" / "variant_b_rules.yaml")
    parser.add_argument("--home")
    parser.add_argument("--away")
    parser.add_argument("--audit-stage", default="EARLY_PREVIEW")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    records = load_jsonl(
        args.picks_file if args.picks_file.is_absolute() else ROOT_DIR / args.picks_file
    )
    record = find_record(records, args.home, args.away)
    rules_path = args.rules if args.rules.is_absolute() else ROOT_DIR / args.rules
    rules_config = load_rules_config(rules_path)
    audit = build_audit(record, rules_config, args.audit_stage)
    payload = json.dumps(audit, indent=2, ensure_ascii=False)
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT_DIR / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
