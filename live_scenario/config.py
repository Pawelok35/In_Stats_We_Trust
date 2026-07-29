"""Configuration constants for Live Scenario core helpers."""

RESULTS = ("WIN", "LOSS", "TIE")
STATE_RESULTS = ("LEAD", "TRAIL", "TIE")
QUARTERS = ("q1", "q2", "q3", "q4")
SCHEMA_VERSION = "live_scenario.v2"
METHODOLOGY_VERSION = "live_scenario_methodology.v1"
SAMPLE_UNIT = "team-game observations"

LEGACY_SAMPLE_QUALITY_THRESHOLDS = {
    "NO_DATA": (None, 0),
    "VERY_LOW": (1, 19),
    "LOW": (20, 49),
    "MODERATE": (50, 99),
    "STRONG": (100, None),
}

V2_SAMPLE_QUALITY_THRESHOLDS = {
    "NO_DATA": (None, 0),
    "VERY_LOW": (1, 9),
    "LOW": (10, 29),
    "MODERATE": (30, 74),
    "STRONG": (75, None),
}

V2_MARGIN_BUCKETS = (
    "TRAILING_15_PLUS",
    "TRAILING_8_TO_14",
    "TRAILING_1_TO_7",
    "TIED",
    "LEADING_1_TO_7",
    "LEADING_8_TO_14",
    "LEADING_15_PLUS",
)

TIE_POLICIES = ("TIE_AS_PUSH", "TIE_AS_LOSS", "THREE_WAY_DISTRIBUTION")
V2_SEASON_PHASES = ("EARLY", "MID", "LATE", "PLAYOFFS")
SHRINKAGE_PRIOR_WEIGHT = 20
HISTORICAL_WINDOWS = {
    "PRIMARY_WINDOW": (2015, 2025),
    "RECENT_WINDOW": (2021, 2025),
    "EXTENDED_WINDOW": (2012, 2025),
}
DEFAULT_STABILITY_THRESHOLD_PP = 15.0
