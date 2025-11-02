from app.reports import _render_metric_comparison_table


def test_render_metric_comparison_table_formats_l4_snapshot():
    row_a = {
        "TEAM": "BAL",
        "core_epa_offense": 0.039,
        "core_epa_defense": 0.103,
        "success_rate_offense": 0.491,
        "success_rate_defense": 0.502,
        "explosive_play_rate_offense": 0.123,
        "third_down_conversion_offense": 0.455,
        "points_per_drive_diff": 0.550,
        "yards_per_play_diff": 0.321,
        "turnover_margin": 0.250,
        "redzone_td_rate_offense": 0.700,
        "pressure_rate_defense": 0.315,
        "tempo": 6.455,
        "power_score": 0.243,
    }
    row_b = {
        "TEAM": "MIA",
        "core_epa_offense": 0.012,
        "core_epa_defense": 0.086,
        "success_rate_offense": 0.454,
        "success_rate_defense": 0.477,
        "explosive_play_rate_offense": 0.111,
        "third_down_conversion_offense": 0.389,
        "points_per_drive_diff": 0.400,
        "yards_per_play_diff": 0.300,
        "turnover_margin": -0.100,
        "redzone_td_rate_offense": 0.650,
        "pressure_rate_defense": 0.298,
        "tempo": 7.091,
        "power_score": 0.149,
    }

    markdown = _render_metric_comparison_table(row_a, row_b, "BAL", "MIA")

    lines = markdown.splitlines()
    assert lines[0] == "| Metric | BAL | MIA | Δ |"
    assert any(line.startswith("| Core EPA Offense") for line in lines)
    assert "n/a" not in markdown.lower()
    assert any("| Tempo | 6.455 | 7.091" in line for line in lines)
    assert any(line.startswith("| PowerScore") for line in lines)
