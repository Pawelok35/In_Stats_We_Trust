from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts import matchup_analyzer


def _report_text(*, epa_offense: str = "+0.120", include_optional: bool = False) -> str:
    optional = ""
    if include_optional:
        optional = """
## Third Down Conversion Form (up to Week 9)

| Team | Season-to-date | Last 5 | Last 3 |
| --- | --- | --- | --- |
| BAL | 0.0% | 0.0% | 0.0% |
| MIA | 40.0% | 40.0% | 40.0% |
"""
    return f"""
**Model (4 metrics):** BAL edge: +0.100 (BAL +0.100 vs MIA +0.000)

## PowerScore Breakdown (Model)

| Component | BAL | MIA |
| --- | --- | --- |
| EPA Offense | {epa_offense} | +0.080 |
| EPA Defense | +0.020 | +0.030 |
| Success Rate Offense | 52.0% | 48.0% |

## Success Rate Offense Form (up to Week 9)

| Team | Season-to-date | Last 5 | Last 3 |
| --- | --- | --- | --- |
| BAL | 52.0% | 51.0% | 50.0% |
| MIA | 48.0% | 47.0% | 46.0% |

## PowerScore Breakdown (7 Metrics)

| Component | BAL | MIA |
| --- | --- | --- |
| Turnover Margin | 0.0 | -1.0 |
| Pressure Rate (Def) | 31.0% | 26.0% |
{optional}
"""


def _args():
    return SimpleNamespace(
        window="season",
        spread=-3.5,
        total=44.5,
        neutral_site=False,
        prime_time=False,
    )


def test_matchup_analyzer_blocks_missing_required_metric(tmp_path):
    report = tmp_path / "report.md"
    report.write_text(_report_text(epa_offense="N/A"), encoding="utf-8")

    with pytest.raises(ValueError):
        matchup_analyzer.run(report, "BAL", "MIA", _args())


def test_matchup_analyzer_optional_table_warning_without_fake_zero(tmp_path):
    report = tmp_path / "report.md"
    report.write_text(_report_text(include_optional=False), encoding="utf-8")

    result = matchup_analyzer.run(report, "BAL", "MIA", _args())

    assert "DATA QUALITY WARNINGS" in result.text
    assert "optional table omitted: Third Down Conversion" in result.text
    assert "Third Down Conversion" in result.text
    assert "0.0% vs 0.0%" not in result.text
    assert "N/A" in result.text
