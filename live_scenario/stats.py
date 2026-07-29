"""Probability, odds, EV, and sample-quality helpers for Live Scenario."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ProbabilitySet:
    wins: int
    losses: int
    ties: int
    sample_size: int

    @property
    def win_probability(self) -> float | None:
        return self.wins / self.sample_size if self.sample_size else None

    @property
    def loss_probability(self) -> float | None:
        return self.losses / self.sample_size if self.sample_size else None

    @property
    def tie_probability(self) -> float | None:
        return self.ties / self.sample_size if self.sample_size else None


def sample_quality_legacy(sample_size: int) -> str:
    if sample_size <= 0:
        return "NO_DATA"
    if sample_size < 20:
        return "VERY_LOW"
    if sample_size < 50:
        return "LOW"
    if sample_size < 100:
        return "MODERATE"
    return "STRONG"


def sample_quality_v2(sample_size: int) -> str:
    if sample_size <= 0:
        return "NO_DATA"
    if sample_size <= 9:
        return "VERY_LOW"
    if sample_size <= 29:
        return "LOW"
    if sample_size <= 74:
        return "MODERATE"
    return "STRONG"


def decimal_to_american(decimal_price: float | None) -> float | None:
    if decimal_price is None or math.isnan(decimal_price) or decimal_price <= 1:
        return None
    if decimal_price >= 2:
        return round((decimal_price - 1) * 100, 2)
    return round(-100 / (decimal_price - 1), 2)


def american_to_decimal(price: float | None) -> float | None:
    if price is None or math.isnan(price) or price == 0:
        return None
    if price > 0:
        return 1 + price / 100
    return 1 + 100 / abs(price)


def fair_decimal_no_push(win_probability: float | None) -> float | None:
    if win_probability is None or win_probability <= 0:
        return None
    return 1 / win_probability


def fair_decimal_tie_push(
    win_probability: float | None,
    loss_probability: float | None,
) -> float | None:
    if win_probability is None or loss_probability is None or win_probability <= 0:
        return None
    return 1 + loss_probability / win_probability


def ev_no_push(win_probability: float | None, decimal_odds: float | None) -> float | None:
    if win_probability is None or decimal_odds is None:
        return None
    return win_probability * decimal_odds - 1


def ev_tie_push(
    win_probability: float | None,
    loss_probability: float | None,
    decimal_odds: float | None,
) -> float | None:
    if win_probability is None or loss_probability is None or decimal_odds is None:
        return None
    return win_probability * (decimal_odds - 1) - loss_probability
