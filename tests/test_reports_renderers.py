from types import SimpleNamespace

import polars as pl
import pytest

import app.reports as reports


def test_render_markdown_non_empty(monkeypatch):
    class DummyTemplate:
        def render(self, **_ctx):
            return "content"

    monkeypatch.setattr(
        reports,
        "_jinja_env",
        lambda: SimpleNamespace(get_template=lambda _name: DummyTemplate()),
    )

    result = reports.render_markdown("dummy", {})
    assert result == "content"


def test_render_markdown_raises_on_empty(monkeypatch):
    class EmptyTemplate:
        def render(self, **_ctx):
            return "   "

    monkeypatch.setattr(
        reports,
        "_jinja_env",
        lambda: SimpleNamespace(get_template=lambda _name: EmptyTemplate()),
    )

    with pytest.raises(ValueError):
        reports.render_markdown("dummy", {})


def test_make_charts_creates_powerscore_chart(tmp_path, monkeypatch):
    settings = SimpleNamespace(data_root=tmp_path)
    monkeypatch.setattr("utils.paths.load_settings", lambda: settings)

    artifact = tmp_path / "l4_powerscore" / "2025" / "8.parquet"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(
        {
            "team": ["AAA", "BBB", "CCC"],
            "power_score": [0.7, 0.65, 0.6],
        }
    ).write_parquet(artifact)

    ctx = {
        "season": 2025,
        "week": 8,
        "metrics": [
            {
                "layer": "l4_powerscore",
                "artifact_exists": True,
                "artifact_full_path": artifact,
            }
        ],
    }

    charts = reports.make_charts(ctx)

    assert len(charts) == 1
    chart = charts[0]
    assert chart["path"].exists()
    assert chart["path"].suffix == ".png"
    assert chart["relative_path"] == "2025_w8/assets/powerscore_top10.png"


def test_make_charts_handles_missing_columns(tmp_path, monkeypatch):
    settings = SimpleNamespace(data_root=tmp_path)
    monkeypatch.setattr("utils.paths.load_settings", lambda: settings)

    artifact = tmp_path / "l4_powerscore" / "2025" / "8.parquet"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"team": ["AAA"]}).write_parquet(artifact)

    ctx = {
        "season": 2025,
        "week": 8,
        "metrics": [
            {
                "layer": "l4_powerscore",
                "artifact_exists": True,
                "artifact_full_path": artifact,
            }
        ],
    }

    charts = reports.make_charts(ctx)
    assert charts == []


def test_save_report_persists_file(tmp_path):
    target = tmp_path / "reports" / "summary.md"
    content = "# Heading"

    result = reports.save_report(target, content)

    assert result == target
    assert target.exists()
    assert target.read_text(encoding="utf-8") == content


def test_save_report_rejects_empty(tmp_path):
    target = tmp_path / "reports" / "summary.md"

    with pytest.raises(ValueError):
        reports.save_report(target, "  ")
