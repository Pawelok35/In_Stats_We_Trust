"""Markdown report generation utilities for weekly build outputs."""
from __future__ import annotations

from utils.paths import rolling_core12_through_path
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Optional
from metrics.form_windows import compute_form_windows
from metrics.opponent_similarity import compute_team_analogs
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import polars as pl
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from utils.config import load_settings
from utils.dataframes import preview_dataframe, read_parquet_or_raise
from utils.logging import get_logger
from utils.manifest import write_manifest
from metrics.power_score import _weight_mapping
from utils.paths import (
    comparison_report_assets_dir,
    comparison_report_path,
    comparison_reports_manifest_path,
    l2_audit_path,
    manifest_path,
    path_for,
    report_assets_dir,
    report_manifest_path,
    report_path,
    team_report_assets_dir,
    team_report_path,
    team_reports_manifest_path,
    weekly_summary_path,
)
def _load_core12_for_teams(season: int, week: int, team_a: str, team_b: str):
    """
    Wczytaj Core12 z L4 dla dwóch drużyn.
    Zwraca (df_a, df_b) jako małe DataFrame'y po jednym wierszu.
    """
    core12_path = path_for("l4_core12", season, week)
    df_core12 = pl.read_parquet(core12_path)

    df_a = df_core12.filter(pl.col("TEAM") == team_a)
    df_b = df_core12.filter(pl.col("TEAM") == team_b)

    if df_a.is_empty():
        raise ValueError(f"Brak Core12 dla {team_a} w {core12_path}")
    if df_b.is_empty():
        raise ValueError(f"Brak Core12 dla {team_b} w {core12_path}")

    return df_a, df_b

# === Metric Comparison helpers ==============================================

METRIC_COMPARISON_FIELDS: list[tuple[str, str, str]] = [
    ('Core EPA Offense', 'core_epa_offense', 'decimal'),
    ('Core EPA Defense', 'core_epa_defense', 'decimal'),
    ('Success Rate Offense', 'success_rate_offense', 'percent'),
    ('Success Rate Defense', 'success_rate_defense', 'percent'),
    ('Explosive Play Rate (Off)', 'explosive_play_rate_offense', 'percent'),
    ('Third Down Conversion', 'third_down_conversion_offense', 'percent'),
    ('Points per Drive Differential', 'points_per_drive_diff', 'decimal'),
    ('Yards per Play Differential', 'yards_per_play_diff', 'decimal'),
    ('Turnover Margin', 'turnover_margin', 'decimal'),
    ('Red Zone TD Rate (Off)', 'redzone_td_rate_offense', 'percent'),
    ('Pressure Rate (Def)', 'pressure_rate_defense', 'percent'),
    ('Tempo', 'tempo', 'decimal'),
    ('PowerScore', 'power_score', 'decimal'),
]


def load_team_snapshot(season: int, week: int, team_a: str, team_b: str) -> pl.DataFrame:
    core12_path = path_for('l4_core12', season, week)
    df_core12 = pl.read_parquet(core12_path)
    df_core12 = df_core12.with_columns(pl.col('TEAM').cast(pl.Utf8).str.to_uppercase())

    team_a = team_a.upper()
    team_b = team_b.upper()

    ps_path = path_for('l4_powerscore', season, week)
    try:
        df_ps = pl.read_parquet(ps_path)
    except FileNotFoundError:
        df_ps = df_core12.select(['season', 'week', 'TEAM']).with_columns(
            pl.lit(None).alias('power_score')
        )
    else:
        if 'team' in df_ps.columns and 'TEAM' not in df_ps.columns:
            df_ps = df_ps.rename({'team': 'TEAM'})
        if 'TEAM' in df_ps.columns:
            df_ps = df_ps.with_columns(pl.col('TEAM').cast(pl.Utf8).str.to_uppercase())
        else:
            df_ps = df_ps.with_columns(pl.lit(None).alias('TEAM'))

        for cand in ['power_score', 'powerscore', 'PowerScore', 'powerScore']:
            if cand in df_ps.columns:
                df_ps = df_ps.rename({cand: 'power_score'})
                break
        if 'power_score' not in df_ps.columns:
            df_ps = df_ps.with_columns(pl.lit(None).alias('power_score'))

    if 'season' not in df_ps.columns:
        df_ps = df_ps.with_columns(pl.lit(season).alias('season'))
    if 'week' not in df_ps.columns:
        df_ps = df_ps.with_columns(pl.lit(week).alias('week'))

    merged = df_core12.join(
        df_ps.select(['season', 'week', 'TEAM', 'power_score']),
        on=['season', 'week', 'TEAM'],
        how='left',
    )
    merged = merged.filter(pl.col('TEAM').is_in([team_a, team_b]))

    required = {field for _, field, _ in METRIC_COMPARISON_FIELDS} | {'TEAM'}
    missing = [col for col in required if col not in merged.columns]
    if missing:
        raise KeyError(f'Missing required columns in L4 snapshot: {missing}')

    if 'power_score' not in merged.columns:
        merged = merged.with_columns(pl.lit(None).alias('power_score'))

    return merged


def _get_team_row(df: pl.DataFrame, team: str) -> Mapping[str, Any]:
    team_code = team.upper()
    subset = df.filter(pl.col("TEAM") == team_code)
    if subset.is_empty():
        raise ValueError(f"No Core12 snapshot row for team {team_code}.")

    row = subset.to_dicts()[0]

    power_score_value = None
    if "power_score" in row:
        power_score_value = row["power_score"]
    elif "powerscore" in row:
        power_score_value = row["powerscore"]

    return {
        "TEAM": team_code,
        "core_epa_offense": row.get("core_epa_offense"),
        "core_epa_defense": row.get("core_epa_defense"),
        "success_rate_offense": row.get("success_rate_offense"),
        "success_rate_defense": row.get("success_rate_defense"),
        "explosive_play_rate_offense": row.get("explosive_play_rate_offense"),
        "third_down_conversion_offense": row.get("third_down_conversion_offense"),
        "points_per_drive_diff": row.get("points_per_drive_diff"),
        "yards_per_play_diff": row.get("yards_per_play_diff"),
        "turnover_margin": row.get("turnover_margin"),
        "redzone_td_rate_offense": row.get("redzone_td_rate_offense"),
        "pressure_rate_defense": row.get("pressure_rate_defense"),
        "tempo": row.get("tempo"),
        "power_score": power_score_value,
    }


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def _to_float(value: Any) -> float | None:
    if _is_missing(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_decimal(value: float | None) -> str:
    if value is None:
        return 'n/a'
    return f'{value:.3f}'


def _format_percentage(value: float | None) -> str:
    if value is None:
        return 'n/a'
    return f'{value * 100:.1f}%'


def _format_delta(delta: float | None) -> str:
    if delta is None:
        return 'n/a'
    if abs(delta) < 1e-12:
        return '\u00b1 0.000'
    arrow = '\u2191' if delta > 0 else '\u2193'
    return f'{arrow} {delta:+.3f}'


def _format_delta_percentage(delta: float | None) -> str:
    if delta is None:
        return 'n/a'
    if abs(delta) < 1e-12:
        return '\u00b1 0.0 pp'
    arrow = '\u2191' if delta > 0 else '\u2193'
    return f'{arrow} {delta * 100:+.1f} pp'


def _render_metric_comparison_table(
    row_a: Mapping[str, Any],
    row_b: Mapping[str, Any],
    team_a: str,
    team_b: str,
) -> str:
    lines: list[str] = [f'| Metric | {team_a} | {team_b} | Delta |', '|---|---:|---:|---:|']

    for label, field, fmt in METRIC_COMPARISON_FIELDS:
        val_a = _to_float(row_a.get(field))
        val_b = _to_float(row_b.get(field))

        if val_a is None or val_b is None:
            lines.append(f'| {label} | n/a | n/a | n/a |')
            continue

        if fmt == 'percent':
            formatted_a = _format_percentage(val_a)
            formatted_b = _format_percentage(val_b)
            delta_display = _format_delta_percentage(val_a - val_b)
        else:
            formatted_a = _format_decimal(val_a)
            formatted_b = _format_decimal(val_b)
            delta_display = _format_delta(val_a - val_b)

        lines.append(f'| {label} | {formatted_a} | {formatted_b} | {delta_display} |')

    return '\n'.join(lines)

# === END Metric Comparison helpers ==========================================


# === chart helpers (minimalne, bez seaborn) ===
def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)

def _df_to_markdown(df: pl.DataFrame) -> str:
    """
    Convert a polars.DataFrame to a GitHub-style markdown table.
    Floats -> 3 decimal places. Everything else as string.
    """
    cols = df.columns

    # header row
    header = "| " + " | ".join(cols) + " |"

    # separator row
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"

    # data rows
    body_rows: list[str] = []
    for row in df.to_dicts():
        cells: list[str] = []
        for c in cols:
            val = row[c]
            if isinstance(val, float):
                cells.append(f"{val:.3f}")
            else:
                cells.append(str(val))
        body_rows.append("| " + " | ".join(cells) + " |")

    return "\n".join([header, sep, *body_rows])

def _pretty_form_table(df: pl.DataFrame, team_a: str, team_b: str) -> str:
    """
    We take the wide form_df from compute_form_windows (which has columns like
    'epa_off_mean_avg_BAL', 'success_rate_off_avg_BAL', etc.)
    and reshape it into a clean markdown table like:

    | Window | BAL Off EPA | BAL Off SR | BAL Def EPA | BAL Def SR | BAL Tempo | MIA Off EPA | ... |

    Off EPA  = epa_off_mean_avg_XXX
    Off SR   = success_rate_off_avg_XXX
    Def EPA  = epa_def_mean_avg_XXX
    Def SR   = success_rate_def_avg_XXX
    Tempo    = tempo_avg_XXX
    """

    # safety: we expect these cols from compute_form_windows
    required_cols = [
        f"epa_off_mean_avg_{team_a}",
        f"success_rate_off_avg_{team_a}",
        f"epa_def_mean_avg_{team_a}",
        f"success_rate_def_avg_{team_a}",
        f"tempo_avg_{team_a}",
        f"epa_off_mean_avg_{team_b}",
        f"success_rate_off_avg_{team_b}",
        f"epa_def_mean_avg_{team_b}",
        f"success_rate_def_avg_{team_b}",
        f"tempo_avg_{team_b}",
        "window",
    ]
    for col in required_cols:
        if col not in df.columns:
            raise RuntimeError(f"Missing expected col '{col}' in form dataframe")

    # build display rows
    display_rows: list[dict[str, object]] = []
    for row in df.to_dicts():
        display_rows.append(
            {
                "Window": row["window"],
                f"{team_a} Off EPA": row[f"epa_off_mean_avg_{team_a}"],
                f"{team_a} Off SR": row[f"success_rate_off_avg_{team_a}"],
                f"{team_a} Def EPA": row[f"epa_def_mean_avg_{team_a}"],
                f"{team_a} Def SR": row[f"success_rate_def_avg_{team_a}"],
                f"{team_a} Tempo": row[f"tempo_avg_{team_a}"],
                f"{team_b} Off EPA": row[f"epa_off_mean_avg_{team_b}"],
                f"{team_b} Off SR": row[f"success_rate_off_avg_{team_b}"],
                f"{team_b} Def EPA": row[f"epa_def_mean_avg_{team_b}"],
                f"{team_b} Def SR": row[f"success_rate_def_avg_{team_b}"],
                f"{team_b} Tempo": row[f"tempo_avg_{team_b}"],
            }
        )

    # now turn display_rows into markdown manually (like _df_to_markdown but custom order)
    ordered_cols = list(display_rows[0].keys()) if display_rows else []

    header = "| " + " | ".join(ordered_cols) + " |"
    sep = "| " + " | ".join(["---"] * len(ordered_cols)) + " |"

    body_lines: list[str] = []
    for r in display_rows:
        cells: list[str] = []
        for col in ordered_cols:
            val = r[col]
            if isinstance(val, float):
                # SR is a rate (0.x). For now zostawiamy xxx.xxx bez %
                cells.append(f"{val:.3f}")
            else:
                cells.append(str(val))
        body_lines.append("| " + " | ".join(cells) + " |")

    return "\n".join([header, sep, *body_lines])


def _save_dummy_chart(path: Path, title: str = "Comparison Chart") -> Path:
    # prościutki wykres pod testy (PNG), tryb headless
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _ensure_parent(path)
    plt.figure()
    plt.title(title)
    plt.plot([0, 1], [0, 1])
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


# === formatowanie strzałki w Edge Summary ===
def _fmt_delta_arrow(delta: float) -> str:
    if delta > 0:
        return f"↑ {delta:+.3f}"
    if delta < 0:
        return f"↓ {delta:+.3f}"
    return "± 0.000"






# === pomocnicze czytanie pliku manifestu (do weekly summary) ===
def _read_manifest_files(manifest_path: Path) -> list[str]:
    if not manifest_path.exists():
        return []
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    # oczekujemy struktury {"files": [{"path": "..."} , ...]}
    return [entry["path"] for entry in data.get("files", [])]


logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
REPORT_TEMPLATE = "report_week.md.j2"
TEAM_REPORT_TEMPLATE = "report_team.md.j2"
COMPARE_REPORT_TEMPLATE = "report_compare.md.j2"
# Percentage formatting for selected rate metrics in comparison tables


FORMAT_RATE_METRICS_AS_PERCENT = os.environ.get("CORE12_RATE_PERCENT", "0").strip().lower() in {
    "1",
    "true",
    "yes",
}

# Metryki wyświetlane jako procenty (z "pp" dla delty)
_RATE_PERCENT_KEYS = {
    "core_pressure_rate_def",
    "core_explosive_play_rate_off",
    "core_redzone_td_rate",
}

_RATE_PERCENT_LABELS = {
    "Pressure Rate (Def)",
    "Explosive Play Rate (Off)",
    "Red Zone TD Rate (Off)",
}






@dataclass
class ChartInfo:
    title: str
    path: Path
    relative_path: str

    def __getitem__(self, key: str):
        return getattr(self, key)


@dataclass
class LayerSnapshot:
    name: str
    layer: str
    artifact_path: str
    artifact_full_path: Path
    artifact_exists: bool
    manifest_path: str
    manifest_exists: bool
    rows: Optional[int]
    cols: Optional[int]
    sha256: Optional[str]


_JINJA_ENV: Optional[Environment] = None


def _jinja_env() -> Environment:
    """Return a cached Jinja environment for report templates."""

    global _JINJA_ENV
    if _JINJA_ENV is None:
        _JINJA_ENV = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
    return _JINJA_ENV


def _safe_relative_path(path: Path, base: Path) -> str:
    try:
        return Path(os.path.relpath(path, base)).as_posix()
    except ValueError:
        return path.as_posix()


def _relative_display(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _load_json(path: Path) -> MutableMapping[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse JSON from %s: %s", path, exc)
        return None


def render_markdown(template_name: str, context: Mapping[str, Any]) -> str:
    """Render a Jinja template to markdown and ensure the result is non-empty."""

    try:
        template = _jinja_env().get_template(template_name)
    except TemplateNotFound as exc:  # pragma: no cover - defensive
        raise FileNotFoundError(f"Template {template_name} not found.") from exc
    rendered = template.render(**context)
    if not rendered.strip():
        raise ValueError(f"Template {template_name} produced empty output.")
    return rendered


def save_report(target: Path, content: str, *, assets: Iterable[Path] | None = None) -> Path:
    """Persist markdown content to disk, ensuring parent directories exist."""

    if not content.strip():
        raise ValueError("Cannot save empty report content.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    if assets:
        for asset in assets:
            asset.parent.mkdir(parents=True, exist_ok=True)
    return target


def _layer_snapshot(name: str, layer: str, season: int, week: int) -> LayerSnapshot:
    artifact = path_for(layer, season, week)
    manifest_file = manifest_path(layer, season, week)
    payload = _load_json(manifest_file)
    rows = payload.get("rows") if payload else None
    cols = payload.get("cols") if payload else None
    sha256 = payload.get("sha256") if payload else None
    return LayerSnapshot(
        name=name,
        layer=layer,
        artifact_path=_relative_display(artifact),
        artifact_full_path=artifact,
        artifact_exists=artifact.exists(),
        manifest_path=_relative_display(manifest_file),
        manifest_exists=manifest_file.exists(),
        rows=rows,
        cols=cols,
        sha256=sha256,
    )


def _audit_snapshot(season: int, week: int, *, tail_lines: int = 5) -> dict[str, Any]:
    audit_file = l2_audit_path(season, week)
    if not audit_file.exists():
        return {"path": _relative_display(audit_file), "exists": False, "lines": []}
    lines = audit_file.read_text(encoding="utf-8").splitlines()
    return {
        "path": _relative_display(audit_file),
        "exists": True,
        "lines": lines[-tail_lines:],
    }


def _optional_layer_df(layer: str, season: int, week: int) -> Optional[pl.DataFrame]:
    artifact = path_for(layer, season, week)
    if not artifact.exists():
        return None
    return read_parquet_or_raise(artifact)


def _normalize_power_score_df(df: Optional[pl.DataFrame]) -> Optional[pl.DataFrame]:
    if df is None:
        return None
    rename_map: dict[str, str] = {}
    if "PowerScore" in df.columns and "power_score" not in df.columns:
        rename_map["PowerScore"] = "power_score"
    if "TEAM" in df.columns and "team" not in df.columns:
        rename_map["TEAM"] = "team"
    if rename_map:
        df = df.rename(rename_map)
    if "team" in df.columns:
        df = df.with_columns(pl.col("team").cast(pl.Utf8).str.to_uppercase())
    if "power_score" in df.columns:
        df = df.with_columns(pl.col("power_score").cast(pl.Float64))
    return df


def _metrics_snapshots(season: int, week: int) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []

    core12_snapshot = _layer_snapshot("L4 Core12 Preview", "l4_core12", season, week)
    if core12_snapshot.artifact_exists:
        columns = ["TEAM", "core_epa_off", "core_sr_off", "core_sr_def"]
        try:
            df = read_parquet_or_raise(core12_snapshot.artifact_full_path)
            preview = preview_dataframe(
                df,
                columns,
                limit=5,
                sort_by=["core_epa_off"],
                descending=True,
            )
        except FileNotFoundError:
            preview = []
        snapshots.append(
            {
                **core12_snapshot.__dict__,
                "preview_columns": columns,
                "preview": preview,
            }
        )

    powerscore_snapshot = _layer_snapshot("PowerScore Rankings", "l4_powerscore", season, week)
    if powerscore_snapshot.artifact_exists:
        columns = ["team", "power_score"]
        try:
            df = read_parquet_or_raise(powerscore_snapshot.artifact_full_path)

            _tmp = _normalize_power_score_df(df)
            if _tmp is not None:
                df = _tmp

            preview = preview_dataframe(
                df,
                columns,
                limit=10,
                sort_by=["power_score"],
                descending=True,
            )

        except FileNotFoundError:
            preview = []
        snapshots.append(
            {
                **powerscore_snapshot.__dict__,
                "preview_columns": columns,
                "preview": preview,
            }
        )

    return snapshots


def make_charts(context: Mapping[str, Any]) -> list[ChartInfo]:
    season = context.get("season")
    week = context.get("week")
    if season is None or week is None:
        logger.debug("Season/week missing in chart context; skipping charts.")
        return []

    markdown_path: Optional[Path] = context.get("markdown_path")
    assets_dir: Optional[Path] = context.get("assets_dir")
    if markdown_path is None:
        markdown_path = report_path(int(season), int(week))
    if assets_dir is None:
        assets_dir = report_assets_dir(int(season), int(week))
    assets_dir.mkdir(parents=True, exist_ok=True)
    markdown_base = markdown_path.parent

    charts: list[dict[str, Any]] = []

    def _register_chart(title: str, chart_path: Path) -> None:
        chart_info = {
            "title": title,
            "path": chart_path,
            "relative_path": _safe_relative_path(chart_path, markdown_base),
        }
        charts.append(chart_info)
        logger.info("Generated chart '%s' at %s", title, chart_path)

    metrics = context.get("metrics") or []
    for metric in metrics:
        if metric.get("layer") != "l4_powerscore":
            continue
        artifact = metric.get("artifact_full_path")
        if not artifact:
            continue
        try:
            df = read_parquet_or_raise(Path(artifact))
        except FileNotFoundError:
            logger.debug("PowerScore artifact missing at %s", artifact)
            continue
        df = _normalize_power_score_df(df)
        if df is None or {"team", "power_score"} - set(df.columns):
            logger.debug("PowerScore dataset missing required columns.")
            continue
        cleaned = (
            df.select(["team", "power_score"])
            .drop_nulls()
            .filter(pl.col("power_score").is_finite())
        )
        if cleaned.is_empty():
            logger.debug("PowerScore dataset empty after filtering.")
            continue
        top = cleaned.sort("power_score", descending=True).head(10)
        teams = top["team"].to_list()
        scores = top["power_score"].to_list()
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.barh(list(reversed(teams)), list(reversed(scores)), color="#2B6CB0")
        ax.set_xlabel("PowerScore")
        ax.set_ylabel("Team")
        ax.set_title("PowerScore Top 10")
        ax.grid(axis="x", linestyle="--", alpha=0.3)
        fig.tight_layout()
        chart_path = assets_dir / "powerscore_top10.png"
        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        _register_chart("PowerScore Top 10", chart_path)

        if not charts and season is not None and week is not None:
            try:
                l3_df = _optional_layer_df("l3_team_week", int(season), int(week))
                if (
                    l3_df is not None
                    and not l3_df.is_empty()
                    and {"TEAM", "tempo"}.issubset(l3_df.columns)
                ):
                    top = (
                        l3_df.select(["TEAM", "tempo"])
                        .drop_nulls()
                        .filter(pl.col("tempo").is_finite())
                        .sort("tempo", descending=True)
                        .head(10)
                    )
                    if not top.is_empty():
                        teams = top["TEAM"].to_list()
                        values = top["tempo"].to_list()
                        fig, ax = plt.subplots(figsize=(8, 4.5))
                        ax.barh(list(reversed(teams)), list(reversed(values)), color="#2B6CB0")
                        ax.set_xlabel("Tempo")
                        ax.set_ylabel("Team")
                        ax.set_title("L3 Tempo Leaders")
                        ax.grid(axis="x", linestyle="--", alpha=0.3)
                        fig.tight_layout()
                        chart_path = assets_dir / "l3_tempo_top10.png"
                        fig.savefig(chart_path, dpi=150, bbox_inches="tight")
                        plt.close(fig)
                        charts.append(
                            {
                                "title": "L3 Tempo Leaders",
                                "path": chart_path,
                                "relative_path": _safe_relative_path(chart_path, markdown_base),
                            }
                        )
            except Exception:
                logger.debug("Failed to build L3 Tempo chart fallback.", exc_info=True)
    return charts


def generate_report(season: int, week: int, *, l3_result: Optional[Path] = None) -> Path:
    season = int(season)
    week = int(week)
    settings = load_settings()

    layers = [
        _layer_snapshot("L1 Ingest", "l1", season, week).__dict__,
        _layer_snapshot("L2 Clean", "l2", season, week).__dict__,
        _layer_snapshot("L3 Team Week", "l3_team_week", season, week).__dict__,
    ]

    metrics = _metrics_snapshots(season, week)
    audit = _audit_snapshot(season, week)

    markdown_target = report_path(season, week)
    charts = make_charts(
        {
            "season": season,
            "week": week,
            "markdown_path": markdown_target,
            "metrics": metrics,
        }
    )
    if not charts:
        assets_dir = report_assets_dir(season, week)
        fallback_png = assets_dir / "l3_tempo_top10.png"  # opcjonalnie zamiast summary.png
        _save_dummy_chart(fallback_png, title="L3 Tempo Leaders")
        charts = [
            {
                "title": "L3 Tempo Leaders",
                "path": fallback_png,
                "relative_path": _safe_relative_path(fallback_png, markdown_target.parent),
            }
        ]

    context = {
        "season": season,
        "week": week,
        "generated_at": datetime.now(timezone.utc),
        "data_root": _relative_display(settings.data_root),
        "layers": layers,
        "metrics": metrics,
        "audit": audit,
        "charts": charts,
    }

    rendered = render_markdown(REPORT_TEMPLATE, context)
    save_report(markdown_target, rendered, assets=[chart["path"] for chart in charts])

    manifest_out = report_manifest_path(season, week)

    manifest_files = [markdown_target] + [chart["path"] for chart in charts]
    write_manifest(
        path=markdown_target,  # artefakt: istniejący plik .md
        manifest_path=manifest_out,  # oczekiwane przez testy: reports/2025_wX/manifest.json
        layer="reports",
        season=season,
        week=week,
        rows=None,
        cols=None,
        files=manifest_files,
    )

    logger.info("Generated weekly report at %s", markdown_target)
    return markdown_target

def _fmt_delta_arrow(delta: float) -> str:
    if delta > 0:
        return f"↑ {delta:+.3f}"
    if delta < 0:
        return f"↓ {delta:+.3f}"
    return "± 0.000"



def _slugify(value: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in value.upper()).strip("_")
    return safe or "team"


def _load_metric_frames(season: int, week: int) -> dict[str, Optional[pl.DataFrame]]:
    return {
        "l3": _optional_layer_df("l3_team_week", season, week),
        "core12": _optional_layer_df("l4_core12", season, week),
        "powerscore": _normalize_power_score_df(_optional_layer_df("l4_powerscore", season, week)),
    }


def available_teams(
    season: int,
    week: int,
    *,
    frames: Optional[dict[str, Optional[pl.DataFrame]]] = None,
) -> list[str]:
    frames = frames or _load_metric_frames(season, week)
    candidates = [frames.get("l3"), frames.get("powerscore"), frames.get("core12")]
    for df in candidates:
        if df is None or df.is_empty():
            continue
        team_col = "team" if "team" in df.columns else "TEAM" if "TEAM" in df.columns else None
        if team_col is None:
            continue
        series = df.select(team_col).drop_nulls().unique()
        if series.is_empty():
            continue
        teams = sorted({str(value).upper() for value in series.to_series().to_list() if value})
        if teams:
            return teams
    return []


def _team_row(df: Optional[pl.DataFrame], team: str) -> Optional[dict[str, Any]]:
    if df is None:
        return None
    team_col = "team" if "team" in df.columns else "TEAM"
    if team_col not in df.columns:
        return None
    result = df.filter(pl.col(team_col) == team)
    if result.is_empty():
        return None
    row = result.to_dicts()[0]
    if "team" not in row:
        row["team"] = row.get(team_col)
    return row


logger = get_logger(__name__)

def _core12_metrics_for(season: int, week: int, team: str) -> dict[str, float]:
    """
    Wczytaj metryki Core12 dla danej drużyny.
    Robimy rolling snapshot (preferowane), fallback do l4_core12/{season}/{week}.parquet.
    Dodatkowo mapujemy nazwy kolumn z pliku na nasze klucze używane w raporcie.
    """

    rolling_path_str = rolling_core12_through_path(season, week - 1)
    rolling_path = Path(rolling_path_str)

    df = None

    if rolling_path.exists():
        df_try = pl.read_parquet(rolling_path)
        if not df_try.is_empty():
            df = df_try
        else:
            logger.warning(
                "Rolling Core12 snapshot %s is empty; will try fallback L4 for season=%s week=%s",
                rolling_path, season, week
            )
    else:
        logger.warning(
            "Rolling Core12 snapshot %s not found; will try fallback L4 for season=%s week=%s",
            rolling_path, season, week
        )

    if df is None:
        fallback_path = Path(f"data/l4_core12/{season}/{week}.parquet")
        if fallback_path.exists():
            df = pl.read_parquet(fallback_path)
        else:
            logger.error(
                "No Core12 data available for season=%s week=%s (no rolling, no fallback).",
                season, week
            )
            return {}

    # 2. znajdź wiersz tej drużyny
    if "week" in df.columns:
        row_df = df.filter(
            (pl.col("TEAM") == team)
            & (pl.col("season") == season)
            & (pl.col("week") == week)
        )
        if row_df.is_empty():
            # rolling case: może nie mieć week == current
            row_df = df.filter(
                (pl.col("TEAM") == team)
                & (pl.col("season") == season)
            )
    else:
        row_df = df.filter(
            (pl.col("TEAM") == team)
            & (pl.col("season") == season)
        )

    if row_df.is_empty():
        logger.warning(
            "Team %s not found in Core12 data for season=%s week=%s.",
            team, season, week
        )
        return {}

    raw_row = row_df.head(1).to_dicts()[0]

    # 3. mapowanie nazw kolumn z parquet -> nasze klucze raportowe
    # lewa strona: klucze używane później w raporcie
    # prawa strona: nazwy kolumn w df_core12
    rename_map = {
        "core_epa_off": ["core_epa_offense", "core_epa_off"],
        "core_epa_def": ["core_epa_defense", "core_epa_def"],
        "core_sr_off": ["success_rate_offense", "core_sr_off"],
        "core_sr_def": ["success_rate_defense", "core_sr_def"],
        "core_explosive_play_rate_off": ["explosive_play_rate_offense", "core_explosive_play_rate_off"],
        "core_third_down_conv": ["third_down_conversion_offense", "core_third_down_conv"],
        "core_points_per_drive_diff": ["points_per_drive_diff", "core_points_per_drive_diff"],
        "core_ypp_diff": ["yards_per_play_diff", "core_ypp_diff"],
        "core_turnover_margin": ["turnover_margin", "core_turnover_margin"],
        "core_redzone_td_rate": ["redzone_td_rate_offense", "core_redzone_td_rate"],
        "core_pressure_rate_def": ["pressure_rate_defense", "core_pressure_rate_def"],
        # tempo NIE jest częścią core_metrics_dict tutaj, tempo łapiemy osobno w _team_summary,
        # ale nie szkodzi mieć go dostępnego:
        "tempo": ["tempo"],
    }

    out: dict[str, float] = {}
    for std_key, candidates in rename_map.items():
        for source_col in candidates:
            if source_col in raw_row:
                v = raw_row[source_col]
                if isinstance(v, (int, float)):
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if math.isfinite(fv):
                        out[std_key] = fv
                        break

    return out

def _team_summary(
    season: int,
    week: int,
    team: str,
    *,
    frames: Optional[dict[str, Optional[pl.DataFrame]]] = None,
) -> tuple[SimpleNamespace, dict[str, Optional[pl.DataFrame]]]:
    """
    Zwraca podsumowanie drużyny używane w raportach.

    - rolling_df: snapshot formy do poprzedniego tygodnia (through_<week-1>.parquet)
    - l3_row_now: tempo z aktualnego tygodnia (albo fallback z poprzedniego)
    - ps_row_now: PowerScore z aktualnego tygodnia (albo fallback)
    - core_metrics: lista metryk do tabeli porównawczej (Core12 + tempo + PowerScore)
    """

    frames = frames or _load_metric_frames(season, week)

    # 1. Rolling snapshot Core12 (stan przed tym tygodniem)
    rolling_df = _load_team_state_before_week(season, week)
    rolling_row = _team_row(rolling_df, team)
    # rolling_row to słownik np. {
    #   'TEAM': 'BAL', 'core_epa_off': ..., 'core_epa_def': ..., 'tempo': ..., 'through_week': 8, ...
    # }

    # 2. Pobierz rekordy z aktualnego tygodnia
    l3_row_now = _team_row(frames.get("l3"), team)
    ps_row_now = _team_row(frames.get("powerscore"), team)

    # 3. FALLBACK tempo / powerscore do poprzedniego tygodnia jeśli brak
    if (l3_row_now is None or "tempo" not in l3_row_now or l3_row_now["tempo"] is None) and week > 1:
        prev_frames = _load_metric_frames(season, week - 1)
        l3_row_prev = _team_row(prev_frames.get("l3"), team)
        if l3_row_prev is not None and "tempo" in l3_row_prev and l3_row_prev["tempo"] is not None:
            l3_row_now = l3_row_prev

    if (ps_row_now is None or (ps_row_now.get("power_score") is None and ps_row_now.get("PowerScore") is None)) and week > 1:
        prev_frames = _load_metric_frames(season, week - 1)
        ps_row_prev = _team_row(prev_frames.get("powerscore"), team)
        if ps_row_prev is not None:
            ps_row_now = ps_row_prev

    # 4. Wyciągnij wartości liczbowe tempo / powerscore (po fallbackach)
    power_score = None
    if ps_row_now is not None:
        candidate = ps_row_now.get("power_score") or ps_row_now.get("PowerScore")
        if candidate is not None:
            try:
                power_score = float(candidate)
            except (TypeError, ValueError):
                power_score = None

    tempo = None
    if l3_row_now is not None and "tempo" in l3_row_now and l3_row_now["tempo"] is not None:
        try:
            tempo = float(l3_row_now["tempo"])
        except (TypeError, ValueError):
            tempo = None
    if tempo is None and rolling_row is not None and "tempo" in rolling_row and rolling_row["tempo"] is not None:
        try:
            tempo = float(rolling_row["tempo"])
        except (TypeError, ValueError):
            tempo = None

    # 5. core_metrics_dict = pełne Core12 dla tej drużyny (rolling -> fallback aktualny tydzień)
    core_metrics_dict = _core12_metrics_for(season, week, team)

    # 6. Zbuduj listę core_metrics (to jest to, co później trafia do tabeli Metric Comparison)
    core_metrics: list[dict[str, Any]] = []
    for key, label in [
        ("core_epa_off", "Core EPA Offense"),
        ("core_epa_def", "Core EPA Defense"),
        ("core_sr_off", "Success Rate Offense"),
        ("core_sr_def", "Success Rate Defense"),
        ("core_explosive_play_rate_off", "Explosive Play Rate (Off)"),
        ("core_third_down_conv", "Third Down Conversion"),
        ("core_points_per_drive_diff", "Points per Drive Differential"),
        ("core_ypp_diff", "Yards per Play Differential"),
        ("core_turnover_margin", "Turnover Margin"),
        ("core_redzone_td_rate", "Red Zone TD Rate (Off)"),
        ("core_pressure_rate_def", "Pressure Rate (Def)"),
    ]:
        val = core_metrics_dict.get(key, None)
        core_metrics.append(
            {
                "key": key,
                "label": label,
                "value": val,
            }
        )

    # Dopnij Tempo i PowerScore jako zwykłe metryki, żeby trafiły do comparison_rows
    core_metrics.append(
        {
            "key": "tempo",
            "label": "Tempo",
            "value": tempo if tempo is not None else None,
        }
    )
    core_metrics.append(
        {
            "key": "powerscore",
            "label": "PowerScore",
            "value": power_score if power_score is not None else None,
        }
    )

    summary = SimpleNamespace(
        team=team,
        powerscore=power_score,
        tempo=tempo,
        core12=core_metrics_dict,  # <- UWAGA: teraz wkładamy dict z Core12, nie rolling_row
        core_metrics=core_metrics,
    )

    return summary, frames



def _team_chart(
    team: str, summary: SimpleNamespace, assets_dir: Path, markdown_base: Path
) -> dict[str, Any]:
    metrics = [metric for metric in summary.core_metrics if metric["value"] is not None]
    if not metrics:
        metrics = [{"label": "Tempo", "value": summary.tempo or 0.0}]
    labels = [metric["label"] for metric in metrics]
    values = [metric["value"] for metric in metrics]
    fig, ax = plt.subplots(figsize=(8, 4.0))
    ax.barh(list(reversed(labels)), list(reversed(values)), color="#3182CE")
    ax.set_xlabel("Value")
    ax.set_title(f"{team} Metrics")
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    fig.tight_layout()
    assets_dir.mkdir(parents=True, exist_ok=True)
    chart_path = assets_dir / f"{_slugify(team).lower()}_metrics.png"
    fig.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {
        "title": f"{team} Metrics",
        "path": chart_path,
        "relative_path": _safe_relative_path(chart_path, markdown_base),
    }


def generate_team_report(
    season: int,
    week: int,
    team: str,
    *,
    frames: Optional[dict[str, Optional[pl.DataFrame]]] = None,
) -> Path:
    season = int(season)
    week = int(week)
    normalized_team = team.upper()
    summary, frames = _team_summary(season, week, normalized_team, frames=frames)
    if all(value is None for value in (summary.core12, summary.powerscore, summary.tempo)):
        raise ValueError(f"No metrics available for team {team}.")

    markdown_target = team_report_path(season, week, normalized_team)
    assets_dir = team_report_assets_dir(season, week, normalized_team)
    markdown_base = markdown_target.parent
    chart = _team_chart(normalized_team, summary, assets_dir, markdown_base)

    context = {
        "season": season,
        "week": week,
        "team": normalized_team,
        "generated_at": datetime.now(timezone.utc),
        "summary": summary,
        "charts": [chart],
    }

    rendered = render_markdown(TEAM_REPORT_TEMPLATE, context)
    save_report(markdown_target, rendered, assets=[chart["path"]])

    manifest_files = [markdown_target, chart["path"]]
    write_manifest(
        path=markdown_target,
        layer="team_report",
        season=season,
        week=week,
        rows=None,
        cols=None,
        files=manifest_files,
    )
    logger.info("Generated team report for %s at %s", normalized_team, markdown_target)
    return markdown_target


def build_weekly_team_reports(season: int, week: int) -> list[Path]:
    frames = _load_metric_frames(season, week)
    teams = available_teams(season, week, frames=frames)
    if not teams:
        logger.warning(
            "No teams available for season=%s week=%s; skipping team reports.", season, week
        )
        return []
    generated: list[Path] = []
    for team in teams:
        try:
            generated.append(generate_team_report(season, week, team, frames=frames))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to generate team report for %s: %s", team, exc)
    if generated:
        manifest_files: list[Path] = []
        for path in generated:
            manifest_files.append(path)
            assets_root = path.parent / "assets"
            if assets_root.exists():
                manifest_files.extend(assets_root.rglob("*.png"))

        manifest_out = team_reports_manifest_path(season, week)

        artifact_file = generated[0]
        write_manifest(
            path=artifact_file,
            manifest_path=manifest_out,
            layer="team_reports",
            season=season,
            week=week,
            rows=len(generated),
            cols=None,
            files=manifest_files,
        )

    return generated


def _merge_numeric(source: Mapping[str, Any], key: str) -> Optional[float]:
    value = source.get(key)
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


_POWERSCORE_COMPONENTS = [
    {
        "label": "EPA Offense",
        "column": "core_epa_off",
        "weight_key": "offense_epa",
        "is_percent": False,
    },
    {
        "label": "EPA Defense",
        "column": "core_epa_def",
        "weight_key": "defense_epa",
        "is_percent": False,
    },
    {
        "label": "Success Rate Offense",
        "column": "core_sr_off",
        "weight_key": "offense_success_rate",
        "is_percent": True,
    },
    {
        "label": "Tempo",
        "column": "core_ed_sr_off",
        "weight_key": "tempo",
        "is_percent": False,
    },
]

_EXTENDED_POWERSCORE_COMPONENTS = [
    {
        "label": "EPA Offense",
        "column": "core_epa_off",
        "weight": 0.25,
        "is_percent": False,
    },
    {
        "label": "EPA Defense",
        "column": "core_epa_def",
        "weight": 0.20,
        "is_percent": False,
    },
    {
        "label": "Success Rate Offense",
        "column": "core_sr_off",
        "weight": 0.15,
        "is_percent": True,
    },
    {
        "label": "Turnover Margin",
        "column": "core_turnover_margin",
        "weight": 0.10,
        "is_percent": False,
    },
    {
        "label": "Tempo",
        "column": "core_ed_sr_off",
        "weight": 0.10,
        "is_percent": False,
    },
    {
        "label": "Red Zone TD Rate (Off)",
        "column": "core_redzone_td_rate",
        "weight": 0.10,
        "is_percent": True,
    },
    {
        "label": "Pressure Rate (Def)",
        "column": "core_pressure_rate_def",
        "weight": 0.10,
        "is_percent": True,
    },
]

_TREND_METRICS = [
    {
        "label": "Off EPA",
        "column": "epa_off_mean",
        "is_percent": False,
        "better": "higher",
    },
    {
        "label": "Def EPA",
        "column": "epa_def_mean",
        "is_percent": False,
        "better": "lower",
    },
    {
        "label": "Off SR",
        "column": "success_rate_off",
        "is_percent": True,
        "better": "higher",
    },
    {
        "label": "Def SR",
        "column": "success_rate_def",
        "is_percent": True,
        "better": "lower",
    },
    {
        "label": "Tempo",
        "column": "tempo",
        "is_percent": False,
        "better": "higher",
    },
]

_SOS_WINDOWS = [
    ("season", None, "Season-to-date"),
    ("last5", 5, "Last 5 games"),
    ("last3", 3, "Last 3 games"),
]

_MATCHUP_EDGE_CONFIG = [
    {
        "label": "Rush Success Edge (off - opp run def)",
        "off_col": "rush_success_rate_off",
        "def_col": "rush_success_rate_def",
        "is_percent": True,
        "mode": "off_minus_def",
    },
    {
        "label": "Pass Success Edge (off - opp pass def)",
        "off_col": "pass_success_rate_off",
        "def_col": "pass_success_rate_def",
        "is_percent": True,
        "mode": "off_minus_def",
    },
    {
        "label": "Explosive Rate Edge (off - opp def)",
        "off_col": "explosive_play_rate_off",
        "def_col": "explosive_play_rate_def",
        "is_percent": True,
        "mode": "off_minus_def",
    },
    {
        "label": "Pass Protection Edge",
        "off_col": "pressure_rate_allowed",
        "def_col": "pressure_rate_def",
        "is_percent": True,
        "mode": "protection",
    },
]

_DRIVE_CONTEXT_CONFIG = [
    ("Avg Start (own yardline)", "avg_start_yd100_off", "yardline"),
    ("Opponent Avg Start (own yardline)", "avg_start_yd100_def", "yardline"),
    ("Field Position Edge (own - opp)", "start_field_position_edge", "edge"),
    ("Points per Drive (offense)", "points_per_drive_off", "points"),
    ("Points per Drive Allowed", "points_per_drive_def", "points"),
    ("Points per Drive Differential", "points_per_drive_diff", "points"),
]

_POWERSCORE_SPREAD_COEFFICIENT = 18.5
_SPREAD_TO_PROB_SCALE = 6.0
_PROE_LEAN_THRESHOLD = 0.03
_PROE_NEUTRAL_BAND = 0.01


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def _latest_l3_row_with_fallback(
    season: int,
    current_week: int,
    team: str,
    *,
    frames: Optional[dict[str, Optional[pl.DataFrame]]] = None,
) -> tuple[Optional[dict[str, Any]], Optional[int]]:
    search_week = current_week
    frames = frames or {}
    while search_week >= 1:
        if search_week == current_week and frames.get("l3") is not None:
            frame = frames.get("l3")
        else:
            cache_key = f"_fallback_l3_week_{search_week}"
            if cache_key in frames:
                frame = frames[cache_key]
            else:
                frame = _optional_layer_df("l3_team_week", season, search_week)
                frames[cache_key] = frame
        row = _team_row(frame, team)
        if row:
            return row, search_week
        search_week -= 1
    return None, None


def _build_matchup_edges_snapshot(
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    *,
    frames: Optional[dict[str, Optional[pl.DataFrame]]] = None,
) -> Optional[str]:
    row_a, week_a = _latest_l3_row_with_fallback(
        season,
        current_week,
        team_a,
        frames=frames,
    )
    row_b, week_b = _latest_l3_row_with_fallback(
        season,
        current_week,
        team_b,
        frames=frames,
    )
    if row_a is None or row_b is None:
        return None

    reference_week = max(filter(None, [week_a, week_b]), default=None)

    def _edge_value(
        offense_row: dict[str, Any],
        defense_row: dict[str, Any],
        config: Mapping[str, Any],
    ) -> Optional[float]:
        off_val = _coerce_float(offense_row.get(config["off_col"]))
        def_val = _coerce_float(defense_row.get(config["def_col"]))
        if off_val is None or def_val is None:
            return None
        mode = config.get("mode", "off_minus_def")
        if mode == "protection":
            return (1.0 - off_val) - def_val
        return off_val - def_val

    def _fmt_edge(value: Optional[float], *, is_percent: bool) -> str:
        if value is None:
            return "n/a"
        if is_percent:
            return f"{value * 100:+.1f} pp"
        return f"{value:+.3f}"

    lines = [
        f"| Edge | {team_a} | {team_b} | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]

    any_row_added = False
    for config in _MATCHUP_EDGE_CONFIG:
        edge_a = _edge_value(row_a, row_b, config)
        edge_b = _edge_value(row_b, row_a, config)
        if edge_a is None and edge_b is None:
            continue
        delta = None
        if edge_a is not None and edge_b is not None:
            delta = edge_a - edge_b
        lines.append(
            "| {label} | {a} | {b} | {d} |".format(
                label=config["label"],
                a=_fmt_edge(edge_a, is_percent=config["is_percent"]),
                b=_fmt_edge(edge_b, is_percent=config["is_percent"]),
                d=_fmt_edge(delta, is_percent=config["is_percent"]),
            )
        )
        any_row_added = True

    if not any_row_added:
        return None

    if reference_week is not None and reference_week < current_week:
        lines.append(f"*Values use latest available L3 data (Week {reference_week}).*")
    return "\n".join(lines)


def _build_drive_context_table(
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    *,
    frames: Optional[dict[str, Optional[pl.DataFrame]]] = None,
) -> Optional[str]:
    row_a, week_a = _latest_l3_row_with_fallback(
        season,
        current_week,
        team_a,
        frames=frames,
    )
    row_b, week_b = _latest_l3_row_with_fallback(
        season,
        current_week,
        team_b,
        frames=frames,
    )
    if row_a is None or row_b is None:
        return None

    reference_week = max(filter(None, [week_a, week_b]), default=None)

    def _own_yardline(raw_value: Optional[float]) -> Optional[float]:
        if raw_value is None:
            return None
        return 100.0 - raw_value

    def _value_for(row: dict[str, Any], key: str) -> Optional[float]:
        return _coerce_float(row.get(key))

    def _fmt(value: Optional[float], kind: str) -> str:
        if value is None:
            return "n/a"
        if kind == "yardline":
            return f"{value:.1f}"
        if kind == "edge":
            return f"{value:+.1f}"
        if kind == "points":
            return f"{value:.2f}"
        return f"{value:.3f}"

    rows: list[tuple[str, Optional[float], Optional[float], str]] = []
    for label, key, kind in _DRIVE_CONTEXT_CONFIG:
        val_a = _value_for(row_a, key)
        val_b = _value_for(row_b, key)
        if kind == "yardline":
            val_a = None if val_a is None else _own_yardline(val_a)
            val_b = None if val_b is None else _own_yardline(val_b)
        rows.append((label, val_a, val_b, kind))

    if not any(val_a is not None or val_b is not None for _, val_a, val_b, _ in rows):
        return None

    lines = [
        f"| Metric | {team_a} | {team_b} |",
        "| --- | ---: | ---: |",
    ]
    for label, val_a, val_b, kind in rows:
        lines.append(
            "| {label} | {a} | {b} |".format(
                label=label,
                a=_fmt(val_a, kind),
                b=_fmt(val_b, kind),
            )
        )

    if reference_week is not None and reference_week < current_week:
        lines.append(f"*Values use latest available L3 data (Week {reference_week}).*")
    return "\n".join(lines)


def _build_game_script_snapshot(
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    *,
    frames: Optional[dict[str, Optional[pl.DataFrame]]] = None,
) -> Optional[str]:
    row_a, week_a = _latest_l3_row_with_fallback(
        season,
        current_week,
        team_a,
        frames=frames,
    )
    row_b, week_b = _latest_l3_row_with_fallback(
        season,
        current_week,
        team_b,
        frames=frames,
    )
    if row_a is None or row_b is None:
        return None

    reference_week = max(filter(None, [week_a, week_b]), default=None)

    def _team_projection(row: dict[str, Any], team: str) -> dict[str, Optional[float]]:
        tempo = _coerce_float(row.get("tempo"))
        pass_rate = _coerce_float(row.get("pass_rate_off"))
        rush_rate = _coerce_float(row.get("rush_rate_off"))
        passes_per_drive = None
        runs_per_drive = None
        if tempo is not None and pass_rate is not None:
            passes_per_drive = tempo * pass_rate
        if tempo is not None and rush_rate is not None:
            runs_per_drive = tempo * rush_rate
        return {
            "team": team,
            "tempo": tempo,
            "pass_rate": pass_rate,
            "rush_rate": rush_rate,
            "passes_per_drive": passes_per_drive,
            "runs_per_drive": runs_per_drive,
        }

    projections = [
        _team_projection(row_a, team_a),
        _team_projection(row_b, team_b),
    ]

    if all(
        all(entry.get(field) is None for field in ("tempo", "pass_rate", "rush_rate"))
        for entry in projections
    ):
        return None

    def _fmt_percent(value: Optional[float]) -> str:
        if value is None:
            return "n/a"
        return f"{value * 100:.1f}%"

    def _fmt_decimal(value: Optional[float], *, digits: int = 2, signed: bool = False) -> str:
        if value is None:
            return "n/a"
        fmt = f"{{:{'+' if signed else ''}.{digits}f}}"
        return fmt.format(value)

    lines = [
        "| Team | Tempo | Pass Rate | Rush Rate | Passes/Drive | Runs/Drive |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for entry in projections:
        lines.append(
            "| {team} | {tempo} | {pass_rate} | {rush_rate} | {ppd} | {rpd} |".format(
                team=entry["team"],
                tempo=_fmt_decimal(entry.get("tempo"), digits=2),
                pass_rate=_fmt_percent(entry.get("pass_rate")),
                rush_rate=_fmt_percent(entry.get("rush_rate")),
                ppd=_fmt_decimal(entry.get("passes_per_drive"), digits=2),
                rpd=_fmt_decimal(entry.get("runs_per_drive"), digits=2),
            )
        )
    if reference_week is not None and reference_week < current_week:
        lines.append(f"*Values use latest available L3 data (Week {reference_week}).*")
    return "\n".join(lines)


def _build_comparison_metrics(
    summary_a: SimpleNamespace,
    summary_b: SimpleNamespace,
) -> list[dict[str, Any]]:
    """
    Build comparison table entries between two teams.
    Only include metrics that actually exist in L3/L4 datasets.
    """
    metrics: list[dict[str, Any]] = []

    # --- Core metrics (rolling Core12)
    for metric_a, metric_b in zip(summary_a.core_metrics, summary_b.core_metrics):
        value_a = _merge_numeric(metric_a, "value")
        value_b = _merge_numeric(metric_b, "value")
        # pomijamy metryki bez wartości lub równe dokładnie 0.0 (placeholder)
        if value_a is None or value_b is None or (abs(value_a) < 1e-9 and abs(value_b) < 1e-9):
            continue
        metrics.append(
            {
                "key": metric_a.get("key"),
                "label": metric_a["label"],
                "team_a": value_a,
                "team_b": value_b,
            }
        )

    # --- PowerScore i Tempo (z L3/L4)
    if summary_a.powerscore is not None and summary_b.powerscore is not None:
        metrics.append(
            {
                "key": "power_score",
                "label": "PowerScore",
                "team_a": summary_a.powerscore,
                "team_b": summary_b.powerscore,
            }
        )

    if summary_a.tempo is not None and summary_b.tempo is not None:
        metrics.append(
            {
                "key": "tempo",
                "label": "Tempo",
                "team_a": summary_a.tempo,
                "team_b": summary_b.tempo,
            }
        )

    # --- Safety fallback (jeśli niektóre core metryki nie trafiły do rolling_df)
    extra_labels = {
        "core_ypp_diff": "Yards per Play Differential",
        "core_turnover_margin": "Turnover Margin",
        "core_points_per_drive_diff": "Points per Drive Differential",
        "core_redzone_td_rate": "Red Zone TD Rate (Off)",
        "core_pressure_rate_def": "Pressure Rate (Def)",
        "core_explosive_play_rate_off": "Explosive Play Rate (Off)",
    }

    for key, label in extra_labels.items():
        already = any(m.get("key") == key for m in metrics)
        if already:
            continue
        val_a = _merge_numeric(getattr(summary_a, "core12", {}) or {}, key)
        val_b = _merge_numeric(getattr(summary_b, "core12", {}) or {}, key)
        if val_a is None or val_b is None or (abs(val_a) < 1e-9 and abs(val_b) < 1e-9):
            continue
        metrics.append(
            {
                "key": key,
                "label": label,
                "team_a": val_a,
                "team_b": val_b,
            }
        )

    return metrics


def _build_powerscore_breakdown(
    season: int,
    week: int,
    team_a: str,
    team_b: str,
    *,
    frames: Optional[dict[str, Optional[pl.DataFrame]]] = None,
    components: Optional[list[dict[str, Any]]] = None,
    weights_override: Optional[Mapping[str, float]] = None,
) -> Optional[tuple[str, dict[str, Any]]]:
    frames = frames or _load_metric_frames(season, week)
    core12 = frames.get("core12")
    if core12 is None or core12.is_empty():
        return None

    teams_df = core12.filter(pl.col("TEAM").is_in([team_a, team_b]))
    if teams_df.is_empty() or teams_df.height < 2:
        return None

    components = components or _POWERSCORE_COMPONENTS
    if weights_override is None:
        if any("weight_key" in component for component in components):
            weights = _weight_mapping()
        else:
            weights = {}
    else:
        weights = dict(weights_override)

    def _get_value(df: pl.DataFrame, team: str, column: str) -> Optional[float]:
        if column not in df.columns:
            return None
        subset = df.filter(pl.col("TEAM") == team).select(column).to_series()
        if subset.is_empty():
            return None
        value = subset.item(0)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _format_value(value: Optional[float], *, is_percent: bool) -> str:
        if value is None or not math.isfinite(value):
            return "n/a"
        if is_percent:
            return f"{value * 100:.1f}%"
        return f"{value:.3f}"

    def _format_delta(delta: Optional[float], *, is_percent: bool) -> str:
        if delta is None or not math.isfinite(delta):
            return "n/a"
        if is_percent:
            return f"{delta * 100:+.1f} pp"
        return f"{delta:+.3f}"

    rows: list[str] = []
    rows.append(f"| Component | Weight | {team_a} | {team_b} | Delta |")
    rows.append("| --- | ---: | ---: | ---: | ---: |")

    has_any = False
    score_a = 0.0
    score_b = 0.0
    entries: list[dict[str, Any]] = []

    for component in components:
        weight = component.get("weight")
        if weight is None:
            weight_key = component.get("weight_key")
            weight = float(weights.get(weight_key, 0.0)) if weight_key else 0.0
        if weight == 0.0:
            continue

        a_val = _get_value(teams_df, team_a, component["column"])
        b_val = _get_value(teams_df, team_b, component["column"])
        delta = None
        if a_val is not None and b_val is not None and math.isfinite(a_val) and math.isfinite(b_val):
            delta = a_val - b_val

        if a_val is not None and math.isfinite(a_val):
            score_a += a_val * weight
        if b_val is not None and math.isfinite(b_val):
            score_b += b_val * weight

        if a_val is None and b_val is None:
            continue

        has_any = True
        entries.append(
            {
                "label": component["label"],
                "weight": weight,
                "delta": delta,
                "is_percent": component["is_percent"],
            }
        )
        rows.append(
            "| {label} | {weight:.0%} | {a} | {b} | {d} |".format(
                label=component["label"],
                weight=weight,
                a=_format_value(a_val, is_percent=component["is_percent"]),
                b=_format_value(b_val, is_percent=component["is_percent"]),
                d=_format_delta(delta, is_percent=component["is_percent"]),
            )
        )

    if not has_any:
        return None

    summary = {
        "score_a": score_a,
        "score_b": score_b,
        "delta": score_a - score_b,
        "entries": entries,
    }

    return "\n".join(rows), summary


def _build_trend_summary(
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
) -> Optional[tuple[str, int]]:
    if current_week <= 1:
        return None

    week_values: list[int] = []
    metric_data: dict[str, dict[str, dict[int, Optional[float]]]] = {
        team: {metric["column"]: {} for metric in _TREND_METRICS}
        for team in (team_a, team_b)
    }

    for week in range(current_week - 1, 0, -1):
        df = _optional_layer_df("l3_team_week", season, week)
        if df is None or df.is_empty():
            continue
        team_frames = {
            team_a: df.filter(pl.col("TEAM") == team_a),
            team_b: df.filter(pl.col("TEAM") == team_b),
        }
        if any(frame.is_empty() for frame in team_frames.values()):
            continue
        week_values.append(week)
        for team, team_df in team_frames.items():
            for metric in _TREND_METRICS:
                column = metric["column"]
                if column not in team_df.columns:
                    continue
                series = team_df.select(column).to_series()
                if series.is_empty():
                    continue
                value = series.item(0)
                try:
                    metric_data[team][column][week] = float(value) if value is not None else None
                except (TypeError, ValueError):
                    metric_data[team][column][week] = None
        if len(week_values) >= 3:
            break

    week_values = sorted(set(week_values))
    if len(week_values) < 2:
        return None
    week_values = week_values[-3:]

    header_cells = ["Metric"] + [f"W{week}" for week in week_values] + ["Trend"]
    lines = [
        "| " + " | ".join(header_cells) + " |",
        "|" + " --- |" * len(header_cells),
    ]

    def _format_value(value: Optional[float], *, is_percent: bool) -> str:
        if value is None or not math.isfinite(value):
            return "n/a"
        if is_percent:
            return f"{value * 100:.1f}%"
        return f"{value:.3f}"

    def _trend_label(values: list[Optional[float]], metric: dict[str, Any]) -> str:
        valid = [v for v in values if v is not None and math.isfinite(v)]
        if len(valid) < 2:
            return "n/a"
        delta = valid[-1] - valid[0]
        threshold = 0.01 if not metric["is_percent"] else 0.01
        adjusted = delta if metric["better"] == "higher" else -delta
        if adjusted > threshold:
            return "+ improving"
        if adjusted < -threshold:
            return "- declining"
        return "= stable"

    for metric in _TREND_METRICS:
        column = metric["column"]
        for team in (team_a, team_b):
            raw_values = [
                metric_data[team][column].get(week) for week in week_values
            ]
            formatted_values = [
                _format_value(val, is_percent=metric["is_percent"]) for val in raw_values
            ]
            trend = _trend_label(raw_values, metric)
            lines.append(
                "| {metric_label} {team} | {values} {trend} |".format(
                    metric_label=metric["label"],
                    team=team,
                    values=" | ".join(formatted_values) + " |",
                    trend=trend,
                )
            )

    return "\n".join(lines), len(week_values)


def _build_matchup_analogs_section(
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    *,
    top_n: int = 3,
) -> Optional[str]:
    analogs_a = compute_team_analogs(
        season=season,
        current_week=current_week,
        team=team_a,
        target_opponent=team_b,
        top_n=top_n,
    )
    analogs_b = compute_team_analogs(
        season=season,
        current_week=current_week,
        team=team_b,
        target_opponent=team_a,
        top_n=top_n,
    )

    if not analogs_a and not analogs_b:
        return None

    def _fmt_decimal(value: Optional[float]) -> str:
        if value is None or not math.isfinite(value):
            return "n/a"
        return f"{value:.3f}"

    def _section(team: str, opponent: str, entries: Iterable):
        lines: list[str] = []
        if not entries:
            lines.append(f"**{team}** has not faced an opponent matching {opponent}'s profile yet.")
            lines.append("")
            return lines

        lines.append(f"**{team} analogs vs {opponent} profile**")
        lines.append("")
        lines.append("| Week | Opponent | Score | Winner | Similarity | EPA Off | Success Rate | PPD Diff |")
        lines.append("| ---: | --- | --- | --- | ---: | ---: | ---: | ---: |")

        def _fmt_score(entry) -> str:
            if entry.points_for is None or entry.points_against is None:
                return "n/a"
            pf = int(round(entry.points_for))
            pa = int(round(entry.points_against))
            return f"{pf}-{pa}"

        def _fmt_winner(entry, self_team: str, opponent_team: str) -> str:
            if entry.winner is None:
                return "n/a"
            if entry.winner == "TIE":
                return "TIE"
            if entry.winner == self_team:
                return self_team
            if entry.winner == opponent_team:
                return opponent_team
            return entry.winner

        for entry in entries:
            if entry.location == "home":
                marker = "H"
            elif entry.location == "away":
                marker = "A"
            else:
                marker = "-"
            opponent_label = f"{entry.opponent} ({marker})"
            lines.append(
                "| {week} | {opponent} | {score} | {winner} | {similarity:.3f} | {epa} | {sr} | {ppd} |".format(
                    week=entry.week,
                    opponent=opponent_label,
                    score=_fmt_score(entry),
                    winner=_fmt_winner(entry, team, opponent),
                    similarity=entry.similarity,
                    epa=_fmt_decimal(entry.epa_off),
                    sr=_fmt_percent(entry.success_rate),
                    ppd=_fmt_decimal(entry.points_per_drive_diff),
                )
            )
        lines.append("")
        return lines

    lines: list[str] = []
    lines.extend(_section(team_a, team_b, analogs_a))
    lines.extend(_section(team_b, team_a, analogs_b))

    markdown = "\n".join(lines).rstrip()
    return markdown or None


def _compute_strength_of_schedule(
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
) -> Optional[tuple[dict[str, Optional[float]], dict[str, Optional[float]], int]]:
    eval_week = current_week - 1
    if eval_week < 1:
        return None

    ps_frames: list[pl.DataFrame] = []
    for wk in range(1, eval_week + 1):
        ps_path = path_for("l4_powerscore", season, wk)
        if not ps_path.exists():
            continue
        df = pl.read_parquet(ps_path)
        if df.is_empty():
            continue
        rename_map: dict[str, str] = {}
        if "team" in df.columns and "TEAM" not in df.columns:
            rename_map["team"] = "TEAM"
        if "PowerScore" in df.columns and "power_score" not in df.columns:
            rename_map["PowerScore"] = "power_score"
        if rename_map:
            df = df.rename(rename_map)
        if "TEAM" not in df.columns or "power_score" not in df.columns:
            continue
        ps_frames.append(
            df.select(
                [
                    pl.col("TEAM").cast(pl.Utf8).str.to_uppercase(),
                    pl.lit(wk).cast(pl.Int64).alias("week"),
                    pl.col("power_score").cast(pl.Float64),
                ]
            )
        )

    if not ps_frames:
        return None

    ps_df = pl.concat(ps_frames, how="vertical")
    opponents_frames: list[pl.DataFrame] = []
    for wk in range(1, eval_week + 1):
        l2_path = path_for("l2", season, wk)
        if not l2_path.exists():
            continue
        df = pl.read_parquet(l2_path)
        if df.is_empty() or not {"TEAM", "OPP"}.issubset(df.columns):
            continue
        opponents_frames.append(
            df.select(
                [
                    pl.lit(wk).cast(pl.Int64).alias("week"),
                    pl.col("TEAM").cast(pl.Utf8).str.to_uppercase(),
                    pl.col("OPP").cast(pl.Utf8).str.to_uppercase(),
                ]
            ).unique()
        )

    if not opponents_frames:
        return None

    opponents_df = pl.concat(opponents_frames, how="vertical")

    def _team_sos(team: str) -> dict[str, Optional[float]]:
        games = opponents_df.filter(pl.col("TEAM") == team)
        if games.is_empty():
            return {}

        joined = games.join(
            ps_df,
            left_on=["OPP", "week"],
            right_on=["TEAM", "week"],
            how="inner",
        )
        if joined.is_empty():
            return {}

        joined = joined.sort("week")
        results: dict[str, Optional[float]] = {}
        series = joined["power_score"]
        for key, window, _ in _SOS_WINDOWS:
            if window is None:
                subset = series
            else:
                subset = series.tail(window)
            results[key] = float(subset.mean()) if subset.len() > 0 else None
        return results

    sos_a = _team_sos(team_a)
    sos_b = _team_sos(team_b)
    if not sos_a and not sos_b:
        return None
    return sos_a, sos_b, eval_week


def _build_strength_of_schedule(
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
) -> Optional[tuple[str, int]]:
    result = _compute_strength_of_schedule(season, current_week, team_a, team_b)
    if result is None:
        return None
    sos_a, sos_b, eval_week = result

    def _fmt(value: Optional[float]) -> str:
        if value is None or not math.isfinite(value):
            return "n/a"
        return f"{value:.3f}"

    lines = [
        f"| Window | {team_a} | {team_b} |",
        "| --- | ---: | ---: |",
    ]
    for key, _, label in _SOS_WINDOWS:
        lines.append(
            f"| {label} | {_fmt(sos_a.get(key))} | {_fmt(sos_b.get(key))} |"
        )

    return "\n".join(lines), eval_week


def _league_pass_rate(season: int, week: int, frames: dict[str, Any]) -> Optional[float]:
    if week is None or week < 1:
        return None
    cache_key = f"_league_pass_rate_week_{week}"
    if cache_key in frames:
        return frames[cache_key]
    df = frames.get("l3")
    if df is None or df.is_empty() or (len(df.columns) > 0 and "week" in df.columns and df["week"].max() != week):
        df = frames.get(f"_fallback_l3_week_{week}")
    if df is None:
        df = _optional_layer_df("l3_team_week", season, week)
        if df is None:
            frames[cache_key] = None
            return None
        frames[f"_fallback_l3_week_{week}"] = df
    if "pass_rate_off" not in df.columns:
        frames[cache_key] = None
        return None
    series = df["pass_rate_off"].cast(pl.Float64).drop_nulls()
    value = float(series.mean()) if series.len() > 0 else None
    frames[cache_key] = value
    return value


def _build_projected_spread_section(
    summary_a: SimpleNamespace,
    summary_b: SimpleNamespace,
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    frames: dict[str, Any],
) -> Optional[str]:
    if summary_a.powerscore is None or summary_b.powerscore is None:
        return None
    delta_ps = summary_a.powerscore - summary_b.powerscore
    model_spread = delta_ps * _POWERSCORE_SPREAD_COEFFICIENT
    win_prob_a = 1.0 / (1.0 + math.exp(-model_spread / _SPREAD_TO_PROB_SCALE))
    win_prob_b = 1.0 - win_prob_a
    spread_text = f"{model_spread:+.1f} pts (favours {team_a if model_spread >= 0 else team_b})"
    sos_data = _compute_strength_of_schedule(season, current_week, team_a, team_b)
    sos_diff_text = "n/a"
    if sos_data is not None:
        sos_a, sos_b, eval_week = sos_data
        base_a = sos_a.get("season")
        base_b = sos_b.get("season")
        if base_a is not None and base_b is not None:
            sos_diff_text = f"{base_a - base_b:+.3f}"
        else:
            sos_diff_text = "n/a"
        note = f"Based on schedule through Week {eval_week}."
    else:
        note = "Schedule differential unavailable."

    lines = [
        "| Metric | Value |",
        "| --- | --- |",
        f"| Model Spread ({team_a} - {team_b}) | {spread_text} |",
        f"| Model Win% {team_a} | {win_prob_a * 100:.1f}% |",
        f"| Model Win% {team_b} | {win_prob_b * 100:.1f}% |",
        f"| SOS Differential ({team_a}-{team_b}) | {sos_diff_text} |",
    ]
    lines.append(f"*Neutral-field assumption. {note}*")
    return "\n".join(lines)


def _proe_lean_label(proe: Optional[float]) -> str:
    if proe is None or not math.isfinite(proe):
        return "n/a"
    if proe > _PROE_LEAN_THRESHOLD:
        return "Pass heavy"
    if proe < -_PROE_LEAN_THRESHOLD:
        return "Run heavy"
    if abs(proe) <= _PROE_NEUTRAL_BAND:
        return "Balanced"
    return "Slight pass lean" if proe > 0 else "Slight run lean"


def _fmt_percent(value: Optional[float]) -> str:
    if value is None or not math.isfinite(value):
        return "n/a"
    return f"{value * 100:.1f}%"


def _build_proe_section(
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    frames: dict[str, Any],
) -> Optional[str]:
    row_a, week_a = _latest_l3_row_with_fallback(season, current_week, team_a, frames=frames)
    row_b, week_b = _latest_l3_row_with_fallback(season, current_week, team_b, frames=frames)
    if row_a is None or row_b is None:
        return None
    pass_rate_a = _coerce_float(row_a.get("pass_rate_off"))
    pass_rate_b = _coerce_float(row_b.get("pass_rate_off"))
    if pass_rate_a is None and pass_rate_b is None:
        return None
    baseline_a = _league_pass_rate(season, week_a, frames)
    baseline_b = _league_pass_rate(season, week_b, frames)
    proe_a = pass_rate_a - baseline_a if pass_rate_a is not None and baseline_a is not None else None
    proe_b = pass_rate_b - baseline_b if pass_rate_b is not None and baseline_b is not None else None

    def _row(team: str, pass_rate: Optional[float], baseline: Optional[float], proe: Optional[float], opponent_row: dict[str, Any]) -> list[str]:
        opp_pass_def = _coerce_float(opponent_row.get("pass_success_rate_def"))
        opp_rush_def = _coerce_float(opponent_row.get("rush_success_rate_def"))
        return [
            team,
            _fmt_percent(pass_rate),
            _fmt_percent(baseline),
            _fmt_percent(proe),
            _fmt_percent(opp_pass_def),
            _fmt_percent(opp_rush_def),
            _proe_lean_label(proe),
        ]

    table = [
        "| Team | Pass Rate | Expected | PROE | Opp Pass SR Allowed | Opp Rush SR Allowed | Lean |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for values in [
        _row(team_a, pass_rate_a, baseline_a, proe_a, row_b),
        _row(team_b, pass_rate_b, baseline_b, proe_b, row_a),
    ]:
        table.append(
            "| {team} | {pass_rate} | {baseline} | {proe} | {opp_pass} | {opp_rush} | {lean} |".format(
                team=values[0],
                pass_rate=values[1],
                baseline=values[2],
                proe=values[3],
                opp_pass=values[4],
                opp_rush=values[5],
                lean=values[6],
            )
        )
    reference_week = max(filter(None, [week_a, week_b]), default=None)
    if reference_week is not None and reference_week < current_week:
        table.append(f"*Pass rates use latest available L3 data (Week {reference_week}).*")
    return "\n".join(table)


_WINDOW_ORDER = ["Season-to-date", "Last 5", "Last 3"]


def _normalize_window_label(window: str) -> Optional[str]:
    if window is None:
        return None
    window = window.strip().lower()
    if window.startswith("weeks"):
        return "Season-to-date"
    if window == "last 5 games":
        return "Last 5"
    if window == "last 3 games":
        return "Last 3"
    return None


def _form_window_values(
    form_df: pl.DataFrame,
    metric_base: str,
    team: str,
) -> dict[str, Optional[float]]:
    col_name = f"{metric_base}_{team}"
    if col_name not in form_df.columns:
        return {}
    subset = form_df.select(["window", col_name])
    values: dict[str, Optional[float]] = {}
    for row in subset.to_dicts():
        label = _normalize_window_label(row["window"])
        if label:
            values[label] = row[col_name]
    return values


def _format_general_value(
    value: Optional[float],
    *,
    as_percent: bool,
    digits: int = 2,
) -> str:
    if value is None or not math.isfinite(value):
        return "n/a"
    if as_percent:
        return f"{value * 100:.1f}%"
    return f"{value:.{digits}f}"


def _format_edge_value(value: Optional[float], *, as_percent: bool) -> str:
    if value is None or not math.isfinite(value):
        return "n/a"
    if as_percent:
        return f"{value * 100:+.1f} pp"
    return f"{value:+.3f}"


def _build_window_table_for_metric(
    form_df: pl.DataFrame,
    metric_base: str,
    team_a: str,
    team_b: str,
    *,
    as_percent: bool,
    digits: int = 2,
    transform: Optional[Callable[[Optional[float]], Optional[float]]] = None,
) -> Optional[str]:
    values_a = _form_window_values(form_df, metric_base, team_a)
    values_b = _form_window_values(form_df, metric_base, team_b)
    if not values_a and not values_b:
        return None

    def _value_for(team_values: dict[str, Optional[float]], label: str) -> Optional[float]:
        raw = team_values.get(label)
        if transform is not None:
            return transform(raw)
        return raw

    lines = ["| Team | Season-to-date | Last 5 | Last 3 |", "| --- | ---: | ---: | ---: |"]
    for team, series in ((team_a, values_a), (team_b, values_b)):
        row = [
            _format_general_value(_value_for(series, label), as_percent=as_percent, digits=digits)
            for label in _WINDOW_ORDER
        ]
        if all(cell == "n/a" for cell in row):
            # skip team rows with no data whatsoever
            continue
        lines.append("| {team} | {season} | {last5} | {last3} |".format(
            team=team,
            season=row[0],
            last5=row[1],
            last3=row[2],
        ))

    if len(lines) <= 2:
        return None
    return "\n".join(lines)


def _build_window_table_from_series(
    team_a: str,
    team_b: str,
    series_a: dict[str, Optional[float]],
    series_b: dict[str, Optional[float]],
    *,
    as_percent: bool,
    digits: int = 2,
) -> Optional[str]:
    lines = ["| Team | Season-to-date | Last 5 | Last 3 |", "| --- | ---: | ---: | ---: |"]
    has_data = False
    for team, series in ((team_a, series_a), (team_b, series_b)):
        row = [
            _format_general_value(series.get(label), as_percent=as_percent, digits=digits)
            for label in _WINDOW_ORDER
        ]
        if all(cell == "n/a" for cell in row):
            continue
        has_data = True
        lines.append(
            "| {team} | {season} | {last5} | {last3} |".format(
                team=team,
                season=row[0],
                last5=row[1],
                last3=row[2],
            )
        )
    if not has_data:
        return None
    return "\n".join(lines)


def _build_edge_window_table(
    form_df: pl.DataFrame,
    team_a: str,
    team_b: str,
    *,
    metric_off: str,
    metric_def: str,
    as_percent: bool,
    invert: bool = False,
) -> Optional[str]:
    off_a = _form_window_values(form_df, metric_off, team_a)
    off_b = _form_window_values(form_df, metric_off, team_b)
    def_a = _form_window_values(form_df, metric_def, team_a)
    def_b = _form_window_values(form_df, metric_def, team_b)
    if not off_a and not off_b:
        return None

    def _edge_series(off_series: dict[str, Optional[float]], opp_def_series: dict[str, Optional[float]]) -> dict[str, Optional[float]]:
        result: dict[str, Optional[float]] = {}
        for label in _WINDOW_ORDER:
            off_val = off_series.get(label)
            def_val = opp_def_series.get(label)
            if off_val is None or def_val is None or not math.isfinite(off_val) or not math.isfinite(def_val):
                result[label] = None
            else:
                result[label] = (def_val - off_val) if invert else (off_val - def_val)
        return result

    edges_a = _edge_series(off_a, def_b)
    edges_b = _edge_series(off_b, def_a)

    lines = ["| Team | Season-to-date | Last 5 | Last 3 |", "| --- | ---: | ---: | ---: |"]
    has_data = False
    for team, series in ((team_a, edges_a), (team_b, edges_b)):
        row = [_format_edge_value(series.get(label), as_percent=as_percent) for label in _WINDOW_ORDER]
        if all(cell == "n/a" for cell in row):
            continue
        has_data = True
        lines.append(
            "| {team} | {season} | {last5} | {last3} |".format(
                team=team,
                season=row[0],
                last5=row[1],
                last3=row[2],
            )
        )

    if not has_data:
        return None
    return "\n".join(lines)


def _build_matchup_edges_table(
    form_df: pl.DataFrame,
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    *,
    frames: dict[str, Any],
) -> Optional[str]:
    sections: list[str] = []
    matchups = [
        ("Rush Success Edge", "rush_success_rate_off_avg", "rush_success_rate_def_avg", True, False),
        ("Pass Success Edge", "pass_success_rate_off_avg", "pass_success_rate_def_avg", True, False),
        ("Explosive Rate Edge", "explosive_play_rate_off_avg", "explosive_play_rate_def_avg", True, False),
        ("Pass Protection vs Pressure", "pressure_rate_allowed_avg", "pressure_rate_def_avg", True, True),
    ]
    for label, off_metric, def_metric, as_percent, invert in matchups:
        table = _build_edge_window_table(
            form_df,
            team_a,
            team_b,
            metric_off=off_metric,
            metric_def=def_metric,
            as_percent=as_percent,
            invert=invert,
        )
        if table:
            sections.append(f"### {label}\n\n{table}\n")
    if sections:
        sections.append("_Positive values favour the listed offense; pass protection uses defense minus pressure allowed._\n")
        return "\n".join(sections).strip()
    return _build_matchup_edges_snapshot(
        season=season,
        current_week=current_week,
        team_a=team_a,
        team_b=team_b,
        frames=frames,
    )


def _build_situational_edges_section(
    form_df: pl.DataFrame,
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    *,
    frames: dict[str, Any],
) -> Optional[str]:
    sections: list[str] = []
    situational_metrics = [
        ("3rd Down Conversion", "third_down_conv_off_avg", "third_down_conv_def_avg", True, False),
        ("Red Zone TD Rate", "redzone_td_rate_off_avg", "redzone_td_rate_def_avg", True, False),
        ("Pass Protection vs Pressure", "pressure_rate_allowed_avg", "pressure_rate_def_avg", True, True),
        ("Explosive Plays", "explosive_play_rate_off_avg", "explosive_play_rate_def_avg", True, False),
    ]
    for label, off_metric, def_metric, as_percent, invert in situational_metrics:
        table = _build_edge_window_table(
            form_df,
            team_a,
            team_b,
            metric_off=off_metric,
            metric_def=def_metric,
            as_percent=as_percent,
            invert=invert,
        )
        if table:
            sections.append(f"### {label}\n\n{table}\n")
    if sections:
        sections.append("_Positive values indicate the offense exceeding the opponent's defensive rate (pass protection uses defense minus pressure allowed)._")
        return "\n".join(sections).strip()
    return _build_situational_edges_snapshot(
        season=season,
        current_week=current_week,
        team_a=team_a,
        team_b=team_b,
        frames=frames,
    )


def _build_drive_context_table(
    form_df: pl.DataFrame,
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    *,
    frames: dict[str, Any],
) -> Optional[str]:
    sections: list[str] = []
    yardline_transform = lambda v: None if v is None else 100.0 - v
    drive_metrics = [
        ("Avg Start (own yardline)", "avg_start_yd100_off_avg", False, 1, yardline_transform),
        ("Opponent Avg Start (own yardline)", "avg_start_yd100_def_avg", False, 1, yardline_transform),
        ("Field Position Edge (own - opp)", "start_field_position_edge_avg", False, 1, None),
        ("Points per Drive (offense)", "points_per_drive_off_avg", False, 2, None),
        ("Points per Drive Allowed", "points_per_drive_def_avg", False, 2, None),
        ("Points per Drive Differential", "points_per_drive_diff_avg", False, 2, None),
    ]
    for label, metric, as_percent, digits, transform in drive_metrics:
        table = _build_window_table_for_metric(
            form_df,
            metric,
            team_a,
            team_b,
            as_percent=as_percent,
            digits=digits,
            transform=transform,
        )
        if table:
            sections.append(f"### {label}\n\n{table}\n")
    if sections:
        sections.append("_Starting field position expressed as own-yard line (higher = shorter field)._")
        return "\n".join(sections).strip()
    return _build_drive_context_snapshot(
        season=season,
        current_week=current_week,
        team_a=team_a,
        team_b=team_b,
        frames=frames,
    )


def _build_game_script_projection(
    form_df: pl.DataFrame,
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    *,
    frames: dict[str, Any],
) -> Optional[str]:
    tempo_a = _form_window_values(form_df, "tempo_avg", team_a)
    tempo_b = _form_window_values(form_df, "tempo_avg", team_b)
    pass_a = _form_window_values(form_df, "pass_rate_off_avg", team_a)
    pass_b = _form_window_values(form_df, "pass_rate_off_avg", team_b)
    if not tempo_a and not pass_a:
        return _build_game_script_snapshot(
            season=season,
            current_week=current_week,
            team_a=team_a,
            team_b=team_b,
            frames=frames,
        )

    def _derive(primary: dict[str, Optional[float]], secondary: Optional[dict[str, Optional[float]]], fn: Callable[[float, Optional[float]], Optional[float]]) -> dict[str, Optional[float]]:
        result: dict[str, Optional[float]] = {}
        for label in _WINDOW_ORDER:
            p_val = primary.get(label)
            s_val = secondary.get(label) if secondary is not None else None
            if p_val is None or (secondary is not None and s_val is None):
                result[label] = None
            else:
                try:
                    result[label] = fn(p_val, s_val)
                except Exception:
                    result[label] = None
        return result

    run_a = {label: (1.0 - value) if value is not None else None for label, value in pass_a.items()}
    run_b = {label: (1.0 - value) if value is not None else None for label, value in pass_b.items()}
    passes_per_drive_a = _derive(tempo_a, pass_a, lambda tempo, pr: tempo * pr if pr is not None else None)
    passes_per_drive_b = _derive(tempo_b, pass_b, lambda tempo, pr: tempo * pr if pr is not None else None)
    runs_per_drive_a = _derive(tempo_a, run_a, lambda tempo, rr: tempo * rr if rr is not None else None)
    runs_per_drive_b = _derive(tempo_b, run_b, lambda tempo, rr: tempo * rr if rr is not None else None)

    sections: list[str] = []
    tempo_table = _build_window_table_from_series(team_a, team_b, tempo_a, tempo_b, as_percent=False, digits=2)
    if tempo_table:
        sections.append("### Tempo\n\n" + tempo_table + "\n")
    pass_table = _build_window_table_from_series(team_a, team_b, pass_a, pass_b, as_percent=True, digits=1)
    if pass_table:
        sections.append("### Pass Rate\n\n" + pass_table + "\n")
    run_table = _build_window_table_from_series(team_a, team_b, run_a, run_b, as_percent=True, digits=1)
    if run_table:
        sections.append("### Run Rate\n\n" + run_table + "\n")
    passes_drive_table = _build_window_table_from_series(team_a, team_b, passes_per_drive_a, passes_per_drive_b, as_percent=False, digits=2)
    if passes_drive_table:
        sections.append("### Passes per Drive\n\n" + passes_drive_table + "\n")
    runs_drive_table = _build_window_table_from_series(team_a, team_b, runs_per_drive_a, runs_per_drive_b, as_percent=False, digits=2)
    if runs_drive_table:
        sections.append("### Runs per Drive\n\n" + runs_drive_table + "\n")

    if sections:
        sections.append("_Derived using aggregated tempo and pass rate (Run Rate = 1 - Pass Rate)._")
        return "\n".join(sections).strip()
    return _build_game_script_snapshot(
        season=season,
        current_week=current_week,
        team_a=team_a,
        team_b=team_b,
        frames=frames,
    )


def _situational_edge_text(
    offense_value: Optional[float],
    defense_value: Optional[float],
    offense_team: str,
    defense_team: str,
    *,
    higher_is_better: bool,
    invert_offense: bool = False,
    threshold: float = 0.02,
) -> str:
    if offense_value is None or defense_value is None:
        return "n/a"
    off_val = offense_value
    def_val = defense_value
    if invert_offense:
        # lower offensive value is better (e.g., pressure allowed)
        margin = def_val - off_val
        offense_better = margin < -threshold
        defense_better = margin > threshold
    else:
        margin = off_val - def_val
        offense_better = margin > threshold if higher_is_better else margin < -threshold
        defense_better = margin < -threshold if higher_is_better else margin > threshold
    advantage = "balanced"
    if offense_better:
        advantage = f"{offense_team} edge"
    elif defense_better:
        advantage = f"{defense_team} edge"
    return (
        f"{_fmt_percent(off_val)} vs {_fmt_percent(def_val)} allowed -> {advantage}"
    )


def _build_situational_edges_snapshot(
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    frames: dict[str, Any],
) -> Optional[str]:
    row_a, week_a = _latest_l3_row_with_fallback(season, current_week, team_a, frames=frames)
    row_b, week_b = _latest_l3_row_with_fallback(season, current_week, team_b, frames=frames)
    if row_a is None or row_b is None:
        return None

    categories = [
        (
            "3rd Down Conversion",
            ("third_down_conv_off", "third_down_conv_def", True, False),
        ),
        (
            "Red Zone TD Rate",
            ("redzone_td_rate_off", "redzone_td_rate_def", True, False),
        ),
        (
            "Pass Protection vs Pressure",
            ("pressure_rate_allowed", "pressure_rate_def", False, True),
        ),
        (
            "Explosive Plays",
            ("explosive_play_rate_off", "explosive_play_rate_def", True, False),
        ),
    ]

    lines = [
        "| Edge | {a} Off vs {b} Def | {b} Off vs {a} Def |".format(a=team_a, b=team_b),
        "| --- | --- | --- |",
    ]
    for label, (off_key, def_key, higher_is_better, invert_offense) in categories:
        cell_a = _situational_edge_text(
            _coerce_float(row_a.get(off_key)),
            _coerce_float(row_b.get(def_key)),
            team_a,
            team_b,
            higher_is_better=higher_is_better,
            invert_offense=invert_offense,
        )
        cell_b = _situational_edge_text(
            _coerce_float(row_b.get(off_key)),
            _coerce_float(row_a.get(def_key)),
            team_b,
            team_a,
            higher_is_better=higher_is_better,
            invert_offense=invert_offense,
        )
        lines.append(f"| {label} | {cell_a} | {cell_b} |")

    reference_week = max(filter(None, [week_a, week_b]), default=None)
    if reference_week is not None and reference_week < current_week:
        lines.append(f"*Metrics use latest available L3 data (Week {reference_week}).*")
    return "\n".join(lines)


def _build_drive_context_snapshot(
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    frames: dict[str, Any],
) -> Optional[str]:
    row_a, week_a = _latest_l3_row_with_fallback(season, current_week, team_a, frames=frames)
    row_b, week_b = _latest_l3_row_with_fallback(season, current_week, team_b, frames=frames)
    if row_a is None or row_b is None:
        return None

    reference_week = max(filter(None, [week_a, week_b]), default=None)

    def _own_yardline(value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        return 100.0 - value

    def _value(row: dict[str, Any], key: str) -> Optional[float]:
        return _coerce_float(row.get(key))

    def _fmt(value: Optional[float], kind: str) -> str:
        if value is None or not math.isfinite(value):
            return "n/a"
        if kind == "yardline":
            return f"{value:.1f}"
        if kind == "edge":
            return f"{value:+.1f}"
        if kind == "points":
            return f"{value:.2f}"
        return f"{value:.3f}"

    rows = [
        ("Avg Start (own yardline)", "avg_start_yd100_off", "yardline"),
        ("Opponent Avg Start (own yardline)", "avg_start_yd100_def", "yardline"),
        ("Field Position Edge (own - opp)", "start_field_position_edge", "edge"),
        ("Points per Drive (offense)", "points_per_drive_off", "points"),
        ("Points per Drive Allowed", "points_per_drive_def", "points"),
        ("Points per Drive Differential", "points_per_drive_diff", "points"),
    ]

    lines = [
        f"| Metric | {team_a} | {team_b} |",
        "| --- | ---: | ---: |",
    ]
    for label, key, kind in rows:
        val_a = _value(row_a, key)
        val_b = _value(row_b, key)
        if kind == "yardline":
            val_a = _own_yardline(val_a)
            val_b = _own_yardline(val_b)
        lines.append(
            "| {label} | {a} | {b} |".format(
                label=label,
                a=_fmt(val_a, kind),
                b=_fmt(val_b, kind),
            )
        )

    if reference_week is not None and reference_week < current_week:
        lines.append(f"*Values use latest available L3 data (Week {reference_week}).*")
    return "\n".join(lines)


def _comparison_edges(
    season: int,
    week: int,
    team_a: str,
    team_b: str,
) -> list[dict[str, Any]]:
    edges_path = path_for("edge_team_vs_team", season, week)
    if not edges_path.exists():
        return []
    df = read_parquet_or_raise(edges_path)
    required_cols = {"team_a", "team_b", "metric", "team_a_value", "team_b_value"}
    if not required_cols.issubset(df.columns):
        return []
    subset = df.filter((pl.col("team_a") == team_a) & (pl.col("team_b") == team_b))
    if subset.is_empty():
        return []
    edges: list[dict[str, Any]] = []
    for row in subset.to_dicts():
        team_a_value = row.get("team_a_value")
        team_b_value = row.get("team_b_value")
        if team_a_value is None or team_b_value is None:
            continue
        team_a_value = float(team_a_value)
        team_b_value = float(team_b_value)
        delta = team_a_value - team_b_value
        edges.append(
            {
                "metric": row.get("metric", "Edge"),
                "team_a_value": team_a_value,
                "team_b_value": team_b_value,
                "delta": delta,  # surowa delta; formatowanie w _fmt_delta_arrow
                "delta_display": f"Delta {delta:+.3f}",  # zostawiamy dla zgodności
            }
        )
    return edges


def build_metric_comparison_table(
    season: int,
    week: int,
    team_a: str,
    team_b: str,
    *,
    comparison_rows: Optional[list[dict[str, Any]]] = None,
) -> str:
    # Jeżeli mamy już obliczone comparison_rows (np. z fallbacku), użyj ich bez ponownego wczytywania snapshotu.
    if comparison_rows:
        lines = ["| Metric | {} | {} | Delta |".format(team_a, team_b), "|---|---:|---:|---:|"]
        for row in comparison_rows:
            a_val = row.get("team_a")
            b_val = row.get("team_b")
            delta = None
            if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)):
                delta = a_val - b_val
            fmt = lambda v: f"{v:.3f}" if isinstance(v, (int, float)) else "n/a"
            lines.append(f"| {row.get('label')} | {fmt(a_val)} | {fmt(b_val)} | {fmt(delta)} |")
        return "\n".join(lines)

    snapshot = load_team_snapshot(season, week, team_a, team_b)
    try:
        row_a = _get_team_row(snapshot, team_a)
    except ValueError:
        row_a = {}
    try:
        row_b = _get_team_row(snapshot, team_b)
    except ValueError:
        row_b = {}

    return _render_metric_comparison_table(row_a, row_b, team_a, team_b)


def _load_schedule_pairs(
    season: int,
    week: int,
    *,
    frames: dict[str, Optional[pl.DataFrame]],
    require_complete_schedule: bool,
) -> Optional[tuple[pl.DataFrame, Path]]:
    settings = load_settings()
    candidates = [
        settings.data_root / "schedules" / f"{season}.parquet",
        settings.data_root / "schedule" / f"{season}.parquet",
    ]
    schedule_path = next((path for path in candidates if path.exists()), None)
    if schedule_path is None:
        message = f"Schedule dataset not found for season {season}."
        if require_complete_schedule:
            raise FileNotFoundError(message)
        logger.info(message)
        return None

    schedule_df = pl.read_parquet(schedule_path)
    if schedule_df.is_empty():
        message = f"Schedule dataset at {schedule_path} is empty."
        if require_complete_schedule:
            raise ValueError(message)
        logger.info(message)
        return None

    if "week" in schedule_df.columns:
        schedule_df = schedule_df.filter(pl.col("week") == week)
    if schedule_df.is_empty():
        message = f"No schedule entries for season {season} week {week}."
        if require_complete_schedule:
            raise ValueError(message)
        logger.info(message)
        return None

    if {"home_team", "away_team"}.issubset(schedule_df.columns):
        pairs = schedule_df.select(
            [
                pl.col("home_team").alias("team_a"),
                pl.col("away_team").alias("team_b"),
            ]
        )
    elif {"team_a", "team_b"}.issubset(schedule_df.columns):
        pairs = schedule_df.select(["team_a", "team_b"])
    elif {"TEAM", "OPP"}.issubset(schedule_df.columns):
        pairs = schedule_df.select(["TEAM", "OPP"]).rename({"TEAM": "team_a", "OPP": "team_b"})
    else:
        message = (
            f"Schedule dataset {schedule_path} must include columns "
            "home_team/away_team or team_a/team_b."
        )
        if require_complete_schedule:
            raise ValueError(message)
        logger.info(message)
        return None

    pairs = (
        pairs.drop_nulls()
        .with_columns(
            [
                pl.col("team_a").cast(pl.Utf8).str.to_uppercase().str.strip_chars(),
                pl.col("team_b").cast(pl.Utf8).str.to_uppercase().str.strip_chars(),
            ]
        )
        .filter(pl.col("team_a") != pl.col("team_b"))
        .unique()
    )
    if pairs.is_empty():
        message = f"No matchup pairs remain for season {season} week {week}."
        if require_complete_schedule:
            raise ValueError(message)
        logger.info(message)
        return None

    available = set(available_teams(season, week, frames=frames))
    if not available:
        message = (
            f"No computed teams available for season {season} week {week}; "
            "cannot validate schedule completeness."
        )
        if require_complete_schedule:
            raise ValueError(message)
        logger.warning(message)
        return None

    teams_in_pairs = set(pairs.get_column("team_a").to_list()) | set(
        pairs.get_column("team_b").to_list()
    )
    missing = sorted(team for team in teams_in_pairs if team not in available)
    if missing:
        missing_str = ", ".join(missing)
        available_str = ", ".join(sorted(available)) or "none"
        message = (
            f"Schedule {schedule_path} references teams without computed metrics for "
            f"season {season} week {week}: {missing_str}. "
            f"Available teams: {available_str}."
        )
        if require_complete_schedule:
            raise ValueError(message)
        logger.warning(message)
        pairs = pairs.filter(
            pl.col("team_a").is_in(sorted(available)) & pl.col("team_b").is_in(sorted(available))
        )

    if pairs.is_empty():
        message = (
            "After filtering unavailable teams, no matchup pairs remain for "
            f"season {season} week {week}."
        )
        if require_complete_schedule:
            raise ValueError(message)
        logger.info(message)
        return None

    logger.info(
        "Loaded %s matchup pairs for season %s week %s from %s.",
        pairs.height,
        season,
        week,
        schedule_path,
    )
    return pairs, schedule_path


def validate_schedule_for_week(
    season: int,
    week: int,
    *,
    require_complete_schedule: bool = True,
) -> None:
    frames = _load_metric_frames(season, week)
    result = _load_schedule_pairs(
        season,
        week,
        frames=frames,
        require_complete_schedule=require_complete_schedule,
    )
    if result is not None:
        pairs, source_path = result
        logger.info(
            "Validated schedule completeness for season %s week %s using %s pairs (source=%s).",
            season,
            week,
            pairs.height,
            source_path,
        )

# mapujemy "logiczna_nazwa" -> lista możliwych nazw w plikach L4
_METRIC_ALIASES = {
    # EPA
    "core_epa_off":        ["core_epa_off", "core_epa_offense"],
    "core_epa_def":        ["core_epa_def", "core_epa_defense"],

    # Success Rate
    "core_sr_off":         ["core_sr_off", "success_rate_offense"],
    "core_sr_def":         ["core_sr_def", "success_rate_defense"],

    # Explosive Play Rate (Off)
    "core_explosive_play_rate_off": [
        "core_explosive_play_rate_off",
        "explosive_play_rate_offense",
        "core_ed_sr_off",  # widzieliśmy to w starym schemacie: core_ed_sr_off
    ],

    # Third Down Conversion
    "core_third_down_conv": [
        "core_third_down_conv",
        "third_down_conversion_offense",
    ],

    # Points per Drive Differential
    "core_points_per_drive_diff": [
        "core_points_per_drive_diff",
        "points_per_drive_diff",
    ],

    # Yards per Play Differential
    "core_ypp_diff": [
        "core_ypp_diff",
        "yards_per_play_diff",
    ],

    # Turnover Margin
    "core_turnover_margin": [
        "core_turnover_margin",
        "turnover_margin",
    ],

    # Red Zone TD Rate Offense
    "core_redzone_td_rate": [
        "core_redzone_td_rate",
        "redzone_td_rate_offense",
    ],

    # Pressure Rate Defense
    "core_pressure_rate_def": [
        "core_pressure_rate_def",
        "pressure_rate_defense",
    ],

    # Tempo (tylko w nowych tygodniach)
    "tempo": [
        "tempo",
    ],
    # Pass rate (L3)
    "pass_rate_off": [
        "pass_rate_off",
    ],
}

_METRIC_LAYER_OVERRIDES: dict[str, str] = {
    "pass_rate_off": "l3_team_week",
}

_WEIGHTED_METRIC_CONFIG: dict[str, dict[str, str]] = {
    # Offensive success rate should be weighted by offensive plays when averaging across weeks.
    "core_sr_off": {
        "type": "l3_column",
        "column": "plays",
    },
    "core_explosive_play_rate_off": {
        "type": "l3_column",
        "column": "plays",
    },
    "core_third_down_conv": {
        "type": "l3_column",
        "column": "plays",
    },
    "pass_rate_off": {
        "type": "l3_column",
        "column": "plays",
    },
    "core_points_per_drive_diff": {
        "type": "l3_column",
        "column": "drives",
    },
    # Defensive success rate weighted by opponent offensive plays (counts from L2 where OPP==team).
    "core_sr_def": {
        "type": "l2_defense_count",
    },
}



def _metric_form_table(
    season: int,
    current_week: int,
    team_a: str,
    team_b: str,
    *,
    column_name: str,   # <- to jest nasza "logiczna nazwa", np. "core_epa_off"
    as_percent: bool,
) -> str:
    """
    Buduje tabelę:
    | Team | Season-to-date | Last 5 | Last 3 |

    Łączy dane z różnych tygodni, nawet jeśli różni się nazwa kolumny
    między starszym i nowszym L4.

    column_name to jedna z logicznych nazw z METRIC_FORM_CONFIG.
    """

    import polars as pl
    from pathlib import Path
    import math
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        "Building metric form table for %s (as_percent=%s) through week %s",
        column_name,
        as_percent,
        current_week - 1,
    )

    # znajdź możliwe rzeczywiste nazwy kolumn dla tej metryki
    candidates = _METRIC_ALIASES.get(column_name, [column_name])

    dfs: list[pl.DataFrame] = []

    layer = _METRIC_LAYER_OVERRIDES.get(column_name, "l4_core12")
    layer_dir = "l4_core12" if layer is None else layer
    if layer not in {"l4_core12", "l3_team_week"}:
        layer_dir = "l4_core12"

    # scope: form tables should exclude the current matchup week so that
    # "up to Week N" reflects completed games only (week-1 for current week)
    for w in range(1, current_week):
        p = Path(f"data/{layer_dir}/{season}/{w}.parquet")
        if not p.exists():
            continue

        df_w_full = pl.read_parquet(p)

        # spróbuj znaleźć którąś z aliasowanych nazw
        physical_col = None
        for cand in candidates:
            if cand in df_w_full.columns:
                physical_col = cand
                break

        if physical_col is None:
            logger.info(
                "Week %s skipped for %s: none of %s present in %s",
                w, column_name, candidates, df_w_full.columns
            )
            continue

        # zachowaj tylko TEAM, week i tę jedną kolumnę pod logiczną nazwą
        df_w = df_w_full.select(
            [
                pl.col("TEAM"),
                pl.col("week"),
                pl.col(physical_col).alias(column_name),
            ]
        )
        dfs.append(df_w)

    # fallback: if we still have no rows, walk backwards for the most recent available week
    if not dfs and current_week > 1:
        for fallback_week in range(current_week - 1, 0, -1):
            p = Path(f"data/{layer_dir}/{season}/{fallback_week}.parquet")
            if not p.exists():
                continue

            df_w_full = pl.read_parquet(p)

            physical_col = None
            for cand in candidates:
                if cand in df_w_full.columns:
                    physical_col = cand
                    break

            if physical_col is None:
                continue

            df_w = df_w_full.select(
                [
                    pl.col("TEAM"),
                    pl.lit(fallback_week).alias("week"),
                    pl.col(physical_col).alias(column_name),
                ]
            )
            dfs.append(df_w)
            break

    # dalej pusto? uczciwie komunikujemy brak danych.
    if not dfs:
        logger.warning(
            "No usable data for %s up to week %s. Returning no-data message.",
            column_name, current_week
        )
        return "_No data available yet._"

    hist = pl.concat(dfs).with_columns(
        pl.col("TEAM").cast(pl.Utf8).str.to_uppercase()
    )

    teams = [team_a.upper(), team_b.upper()]
    hist = (
        hist
        .filter(pl.col("TEAM").is_in(teams))
        .sort(["TEAM", "week"])
    )

    weight_col: str | None = None
    weight_cfg = _WEIGHTED_METRIC_CONFIG.get(column_name)
    if weight_cfg is not None:
        weight_type = weight_cfg.get("type")
        weight_frames: list[pl.DataFrame] = []

        for w in range(1, current_week):
            weight_path: Path | None = None
            if weight_type == "l3_column":
                weight_path = Path(f"data/l3_team_week/{season}/{w}.parquet")
            elif weight_type == "l2_defense_count":
                weight_path = Path(f"data/l2/{season}/{w}.parquet")

            if weight_path is None or not weight_path.exists():
                continue

            df_weight = pl.read_parquet(weight_path)

            if weight_type == "l3_column":
                weight_field = weight_cfg.get("column")
                if not weight_field or weight_field not in df_weight.columns:
                    continue
                weight_frames.append(
                    df_weight.select(
                        [
                            pl.col("TEAM").cast(pl.Utf8).str.to_uppercase().alias("TEAM"),
                            pl.lit(w).alias("week"),
                            pl.col(weight_field).cast(pl.Float64).alias("_weight"),
                        ]
                    )
                )
            elif weight_type == "l2_defense_count":
                if "OPP" not in df_weight.columns:
                    continue
                weight_frames.append(
                    df_weight.group_by("OPP")
                    .agg(pl.len().alias("_weight"))
                    .select(
                        [
                            pl.col("OPP").cast(pl.Utf8).str.to_uppercase().alias("TEAM"),
                            pl.lit(w).alias("week"),
                            pl.col("_weight").cast(pl.Float64),
                        ]
                    )
                )

        if weight_frames:
            weights_df = pl.concat(weight_frames, how="vertical")
            hist = hist.join(weights_df, on=["TEAM", "week"], how="left")
            hist = hist.with_columns(pl.col("_weight").fill_null(0.0))
            weight_col = "_weight"

    if weight_col is not None:
        unique_teams = sorted(set(teams))
        season_records: list[dict[str, str | float | None]] = []
        last5_records: list[dict[str, str | float | None]] = []
        last3_records: list[dict[str, str | float | None]] = []

        for team in unique_teams:
            team_df = hist.filter(pl.col("TEAM") == team).sort("week")
            if team_df.is_empty():
                season_records.append({"TEAM": team, "season_to_date": None})
                last5_records.append({"TEAM": team, "last5": None})
                last3_records.append({"TEAM": team, "last3": None})
                continue

            values = team_df[column_name].to_list()
            weights = team_df[weight_col].to_list()

            def _weighted_mean_for(count: int | None) -> float | None:
                if not values:
                    return None
                if count is not None:
                    subset_vals = values[-count:]
                    subset_weights = weights[-count:]
                else:
                    subset_vals = values
                    subset_weights = weights
                total_weight = sum(subset_weights)
                if total_weight <= 0:
                    return None
                weighted_sum = sum(v * w for v, w in zip(subset_vals, subset_weights))
                return float(weighted_sum / total_weight)

            season_records.append({"TEAM": team, "season_to_date": _weighted_mean_for(None)})
            last5_records.append({"TEAM": team, "last5": _weighted_mean_for(5)})
            last3_records.append({"TEAM": team, "last3": _weighted_mean_for(3)})

        season_avg = pl.DataFrame(season_records)
        last5 = pl.DataFrame(last5_records)
        last3 = pl.DataFrame(last3_records)
    else:
        season_avg = (
            hist
            .group_by("TEAM")
            .agg(pl.col(column_name).mean().alias("season_to_date"))
        )
        last5 = (
            hist
            .group_by("TEAM")
            .agg(pl.col(column_name).tail(5).mean().alias("last5"))
        )
        last3 = (
            hist
            .group_by("TEAM")
            .agg(pl.col(column_name).tail(3).mean().alias("last3"))
        )

    out = (
        season_avg
        .join(last5, on="TEAM")
        .join(last3, on="TEAM")
        .sort("TEAM")
    )

    def _fmt_value(v):
        if v is None or (isinstance(v, float) and not math.isfinite(v)):
            return "n/a"
        try:
            fv = float(v)
        except (TypeError, ValueError):
            return "n/a"
        if as_percent:
            return f"{fv * 100:.1f}%"
        return f"{fv:.3f}"

    lines = [
        "| Team | Season-to-date | Last 5 | Last 3 |",
        "|------|---------------:|-------:|-------:|",
    ]

    for row in out.to_dicts():
        st = _fmt_value(row["season_to_date"])
        l5 = _fmt_value(row["last5"])
        l3 = _fmt_value(row["last3"])
        lines.append(f"| {row['TEAM']} | {st} | {l5} | {l3} |")

    return "\n".join(lines)



METRIC_FORM_CONFIG = [
    ("Core EPA Offense", "core_epa_off", False),
    ("Core EPA Defense", "core_epa_def", False),

    ("Success Rate Offense", "core_sr_off", True),
    ("Success Rate Defense", "core_sr_def", True),

    ("Explosive Play Rate (Off)", "core_explosive_play_rate_off", True),
    ("Third Down Conversion", "core_third_down_conv", True),

    ("Points per Drive Differential", "core_points_per_drive_diff", False),

    ("Yards per Play Differential", "core_ypp_diff", False),
    ("Turnover Margin", "core_turnover_margin", False),

    ("Red Zone TD Rate (Off)", "core_redzone_td_rate", True),
    ("Pressure Rate (Def)", "core_pressure_rate_def", True),

    ("Tempo", "tempo", False),
    ("Pass Rate Offense", "pass_rate_off", True),
]






def generate_comparison_report(
    season: int,
    week: int,
    team_a: str,
    team_b: str,
    *,
    frames: Optional[dict[str, Optional[pl.DataFrame]]] = None,
) -> list[Path]:
    """
    Generuje pojedynczy raport porównawczy (matchup) między dwiema drużynami.
    Zwraca listę ścieżek: [plik_markdown.md, wykres_team_a.png, wykres_team_b.png]
    """

    season = int(season)
    week = int(week)
    team_a = team_a.upper().strip()
    team_b = team_b.upper().strip()

    # 1. Zbierz metryki drużyn (tempo, PowerScore, Core12 itd.)
    summary_a, frames = _team_summary(season, week, team_a, frames=frames)
    summary_b, _      = _team_summary(season, week, team_b, frames=frames)

    # 2. Porównanie metryk (Core12 + tempo + PowerScore) - dalej tego używamy np. do Quick Edge
    comparison_rows = _build_comparison_metrics(summary_a, summary_b)

    # 3. Recent form (season-to-date / last5 / last3) szeroka tabela (Off EPA, SR, Def EPA itd.)
    form_df = compute_form_windows(
        season=season,
        teams=[team_a, team_b],
        current_week=week,
    )
    # 4. Quick Edge / skrót przewag (używa comparison_rows + rolling form_df)
    # tempo last3
    tempo_a_recent = None
    tempo_b_recent = None
    try:
        tempo_a_recent = (
            form_df
            .filter(pl.col("window") == "last 3 games")[f"tempo_avg_{team_a}"]
            .to_list()[0]
        )
        tempo_b_recent = (
            form_df
            .filter(pl.col("window") == "last 3 games")[f"tempo_avg_{team_b}"]
            .to_list()[0]
        )
    except Exception:
        pass

    # Points per Drive Diff z comparison_rows (jeśli tam jest)
    ppd_a = None
    ppd_b = None
    for row in comparison_rows:
        if row.get("label") == "Points per Drive Differential":
            ppd_a = row.get("team_a")
            ppd_b = row.get("team_b")

    def _fmt_edge_val(val: Optional[float]) -> str:
        if val is None:
            return "n/a"
        try:
            return f"{float(val):.3f}"
        except (TypeError, ValueError):
            return "n/a"

    quick_edge_lines: list[str] = []
    quick_edge_lines.append(
        f"- PowerScore advantage: {_fmt_edge_val(summary_a.powerscore)} vs {_fmt_edge_val(summary_b.powerscore)}"
    )
    quick_edge_lines.append(
        f"- Tempo (last 3): {_fmt_edge_val(tempo_a_recent)} vs {_fmt_edge_val(tempo_b_recent)}"
    )
    quick_edge_lines.append(
        f"- Points per Drive Diff: {_fmt_edge_val(ppd_a)} vs {_fmt_edge_val(ppd_b)}"
    )

    # 5. Budujemy markdown raportu
    md_lines: list[str] = []

    # Header
    md_lines.append(f"# Matchup Report - {team_a} vs {team_b}")
    md_lines.append("")
    # Jeśli korzystamy z fallbacku (metryki z wcześniejszego tygodnia), nadal pokazujemy tabelę,
    # jeżeli udało się zbudować wartości porównawcze.
    has_metric_values = bool(comparison_rows)

    breakdown_result = _build_powerscore_breakdown(
        season=season,
        week=week,
        team_a=team_a,
        team_b=team_b,
        frames=frames,
    )
    if breakdown_result:
        breakdown_md, breakdown_summary = breakdown_result
    else:
        breakdown_md = None
        breakdown_summary = None

    extended_result = _build_powerscore_breakdown(
        season=season,
        week=week,
        team_a=team_a,
        team_b=team_b,
        frames=frames,
        components=_EXTENDED_POWERSCORE_COMPONENTS,
        weights_override={},
    )
    if extended_result:
        extended_breakdown_md, extended_summary = extended_result
    else:
        extended_breakdown_md = None
        extended_summary = None

    if has_metric_values:
        md_lines.append("## Metric Comparison")
        md_lines.append("")
        md_lines.append(
            build_metric_comparison_table(
                season=season,
                week=week,
                team_a=team_a,
                team_b=team_b,
                comparison_rows=comparison_rows,
            )
        )
        md_lines.append("")

    if breakdown_md:
        md_lines.append("## PowerScore Breakdown (Model)")
        md_lines.append("")
        md_lines.append(breakdown_md)
        md_lines.append("")
    if extended_breakdown_md:
        md_lines.append("## PowerScore Breakdown (7 Metrics)")
        md_lines.append("")
        md_lines.append(extended_breakdown_md)
        md_lines.append("")

    summary_lines: list[str] = []
    if breakdown_summary:
        delta_base = breakdown_summary["delta"]
        leader_base = team_a if delta_base > 0 else team_b if delta_base < 0 else "None"
        summary_lines.append(
            f"**Model (4 metrics):**\n"
            f"{leader_base} edge: {abs(delta_base):+.3f} "
            f"({team_a} {breakdown_summary['score_a']:+.3f} vs {team_b} {breakdown_summary['score_b']:+.3f})"
        )
    if extended_summary:
        delta_ext = extended_summary["delta"]
        leader_ext = team_a if delta_ext > 0 else team_b if delta_ext < 0 else "None"
        summary_lines.append(
            f"**7 metrics version:**\n"
            f"{leader_ext} edge: {abs(delta_ext):+.3f} "
            f"({team_a} {extended_summary['score_a']:+.3f} vs {team_b} {extended_summary['score_b']:+.3f})"
        )
        entries = extended_summary.get("entries") or []
        if entries and abs(delta_ext) > 1e-6:
            leader = team_a if delta_ext > 0 else team_b
            relevant = [
                entry for entry in entries
                if entry.get("delta") is not None and math.isfinite(entry.get("delta", math.nan))
            ]
            if delta_ext > 0:
                positive = [entry for entry in relevant if entry["delta"] > 0]
                if positive:
                    relevant = positive
            else:
                negative = [entry for entry in relevant if entry["delta"] < 0]
                if negative:
                    relevant = negative
            if relevant:
                top_entry = max(
                    relevant,
                    key=lambda entry: abs(entry.get("delta", 0.0) * entry.get("weight", 0.0))
                )
                delta_text = f"{abs(delta_ext):.3f}"
                summary_lines.append(
                    f"**Verdict:** {leader} holds the edge in the extended breakdown "
                    f"(lead {delta_text}), driven by {top_entry['label']} "
                    f"({top_entry['weight'] * 100:.0f}% weight)."
                )

    if summary_lines:
        md_lines.append("## PowerScore Summary")
        md_lines.append("")
        md_lines.extend(summary_lines)
        risk_flags: list[str] = []
        # Heurystyka: jeżeli przewaga opiera się głównie na niestabilnych metrykach
        # (Turnover Margin / Red Zone TD Rate), pokaż ostrzeżenie.
        def _risk_flags_from_entries(entries: list[dict[str, Any]]) -> list[str]:
            if not entries:
                return []
            vols = [
                e for e in entries
                if isinstance(e.get("label"), str)
                and any(tok in e["label"].lower() for tok in ("turnover", "red zone"))
            ]
            share = sum(e.get("weight", 0.0) for e in vols)
            if share >= 0.20:  # ≥20% wagi z niestabilnych statystyk
                return [
                    f"Score relies ~{share * 100:.0f}% on volatile stats (TO/Red Zone) – treat edge with caution."
                ]
            return []

        if extended_summary:
            risk_flags.extend(_risk_flags_from_entries(extended_summary.get("entries") or []))

        if risk_flags:
            md_lines.append("### Risk flags")
            md_lines.append("")
            for flag in risk_flags:
                md_lines.append(f"- {flag}")
            md_lines.append("")
        md_lines.append("")

    projected_md = _build_projected_spread_section(
        summary_a,
        summary_b,
        season,
        week,
        team_a,
        team_b,
        frames,
    )
    if projected_md:
        md_lines.append("## Model Outlook")
        md_lines.append("")
        md_lines.append(projected_md)
        md_lines.append("")

    proe_md = _build_proe_section(
        season,
        week,
        team_a,
        team_b,
        frames,
    )
    if proe_md:
        md_lines.append("## PROE Tendencies")
        md_lines.append("")
        md_lines.append(proe_md)
        md_lines.append("")

    situational_md = _build_situational_edges_section(
        form_df,
        season,
        week,
        team_a,
        team_b,
        frames=frames,
    )
    if situational_md:
        md_lines.append("## Situational Edges")
        md_lines.append("")
        md_lines.append(situational_md)
        md_lines.append("")

    matchup_edges_md = _build_matchup_edges_table(
        form_df,
        season,
        week,
        team_a,
        team_b,
        frames=frames,
    )
    if matchup_edges_md:
        md_lines.append("## Matchup Edges")
        md_lines.append("")
        md_lines.append(matchup_edges_md)
        md_lines.append("")

    drive_context_md = _build_drive_context_table(
        form_df,
        season,
        week,
        team_a,
        team_b,
        frames=frames,
    )
    if drive_context_md:
        md_lines.append("## Drive Context")
        md_lines.append("")
        md_lines.append(drive_context_md)
        md_lines.append("")

    game_script_md = _build_game_script_projection(
        form_df,
        season,
        week,
        team_a,
        team_b,
        frames=frames,
    )
    if game_script_md:
        md_lines.append("## Game Script Projection")
        md_lines.append("")
        md_lines.append(game_script_md)
        md_lines.append("")

    sos_result = _build_strength_of_schedule(
        season=season,
        current_week=week,
        team_a=team_a,
        team_b=team_b,
    )
    if sos_result:
        sos_md, sos_week = sos_result
        md_lines.append(f"## Strength of Schedule (through Week {sos_week})")
        md_lines.append("")
        md_lines.append(sos_md)
        md_lines.append("")

    trend_result = _build_trend_summary(
        season=season,
        current_week=week,
        team_a=team_a,
        team_b=team_b,
    )
    if trend_result:
        trend_md, trend_span = trend_result
        md_lines.append(f"## Trend Summary (last {trend_span} weeks)")
        md_lines.append("")
        md_lines.append(trend_md)
        md_lines.append("")

    analogs_md = _build_matchup_analogs_section(
        season=season,
        current_week=week,
        team_a=team_a,
        team_b=team_b,
    )
    if analogs_md:
        md_lines.append("## Matchup Analogs")
        md_lines.append("")
        md_lines.append(analogs_md)
        md_lines.append("")

    # Optional Edge Summary if comparison edges dataset provides entries
    edges = _comparison_edges(season, week, team_a, team_b)
    if edges:
        md_lines.append("## Edge Summary")
        md_lines.append("")
        md_lines.append(f"| Edge | {team_a} | {team_b} | Delta |")
        md_lines.append("| --- | ---: | ---: | ---: |")
        for edge in edges:
            delta_fmt = _fmt_delta_arrow(float(edge.get("delta", 0.0)))
            md_lines.append(
                "| {label} | {a:.3f} | {b:.3f} | {delta} |".format(
                    label=edge.get("metric", "Edge"),
                    a=float(edge.get("team_a_value", 0.0)),
                    b=float(edge.get("team_b_value", 0.0)),
                    delta=delta_fmt,
                )
            )
        md_lines.append("")

    for (metric_label, column_name, is_percent) in METRIC_FORM_CONFIG:
        md_lines.append(f"## {metric_label} Form (up to Week {week - 1})")
        md_lines.append("")
        md_lines.append(
            _metric_form_table(
                season=season,
                current_week=week,
                team_a=team_a,
                team_b=team_b,
                column_name=column_name,
                as_percent=is_percent,
            )
        )
        md_lines.append("")



    # 6. Ścieżki zapisu (gdzie .md i gdzie PNG)
    markdown_target = comparison_report_path(season, week, team_a, team_b)
    assets_dir = comparison_report_assets_dir(season, week, team_a, team_b)
    markdown_base = markdown_target.parent
    assets_dir.mkdir(parents=True, exist_ok=True)

    # 7. Zapisz markdown na dysk
    save_report(markdown_target, "\n".join(md_lines))

    # 8. Dwa mini-wykresy dla drużyn (barh z metrykami)
    chart_a = _team_chart(team_a, summary_a, assets_dir, markdown_base)
    chart_b = _team_chart(team_b, summary_b, assets_dir, markdown_base)

    # 9. Manifest dla tej pary
    manifest_out = comparison_reports_manifest_path(season, week)
    write_manifest(
        path=str(markdown_target),
        manifest_path=manifest_out,
        layer="comparison_reports",
        season=season,
        week=week,
        rows=None,
        cols=None,
        files=[
            str(markdown_target),
            str(chart_a["path"]),
            str(chart_b["path"]),
        ],
    )

    logger.info(
        "Generated comparison report %s vs %s at %s",
        team_a,
        team_b,
        markdown_target,
    )

    return [Path(markdown_target), chart_a["path"], chart_b["path"]]



def generate_comparison_reports_from_schedule(
    season: int,
    week: int,
    *,
    require_complete_schedule: bool = True,
) -> list[Path]:
    frames = _load_metric_frames(season, week)
    result = _load_schedule_pairs(
        season,
        week,
        frames=frames,
        require_complete_schedule=require_complete_schedule,
    )
    if result is None:
        return []
    pairs, source_path = result

    generated: list[Path] = []
    first_md: Optional[Path] = None

    for row in pairs.to_dicts():
        team_a = row.get("team_a")
        team_b = row.get("team_b")
        if not team_a or not team_b:
            continue
        try:
            # single-call zwraca [md, png, ...] — wpinamy wszystko do jednej listy
            paths = generate_comparison_report(
                season,
                week,
                team_a,
                team_b,
                frames=frames,
            )
            if paths:
                if first_md is None:
                    first_md = paths[0]
                generated.extend(paths)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Skipping matchup %s vs %s: %s", team_a, team_b, exc)

    if generated:
        manifest_out = comparison_reports_manifest_path(season, week)
        write_manifest(
            path=str(first_md or generated[0]),
            manifest_path=manifest_out,
            layer="comparison_reports",
            season=season,
            week=week,
            rows=len(generated),
            cols=None,
            files=[str(p) for p in generated],
        )

    logger.info(
        "Generated %s comparison reports for season %s week %s (source=%s).",
        len(generated),
        season,
        week,
        source_path,
    )
    return generated
def _load_team_state_before_week(season: int, week: int) -> pl.DataFrame:
    """
    Zwraca snapshot stanu drużyn PRZED danym tygodniem.

    Przykład:
    - dla week=9 -> weź through_8.parquet
    - dla week=1 -> nie ma week-1, więc próbujemy through_1.parquet jako fallback

    Zwraca DataFrame z kolumnami Core12 rolling:
    ['season','TEAM', core_epa_off,..., core_pressure_rate_def, ... 'through_week']
    """
    # safety: żeby nie mieć week 0
    through_week = max(1, week - 1)

    path = rolling_core12_through_path(season, through_week)
    p = Path(path)
    if not p.exists():
        # fallback: jeżeli np. jesteśmy bardzo wcześnie w sezonie i nie ma through_(week-1),
        # to użyj aktualnego through_week
        if Path(rolling_core12_through_path(season, week)).exists():
            through_week = week
            p = Path(rolling_core12_through_path(season, week))
        else:
            raise FileNotFoundError(
                f"Rolling Core12 snapshot not found for season={season} week<={week} "
                f"(tried {path})"
            )

    df = pl.read_parquet(p)

    # sanity: normalizujemy nazwę kolumny drużyny na 'TEAM' i zostawiamy info,
    # który snapshot został użyty
    df = df.with_columns(
        pl.lit(through_week).alias("rolling_through_week")
    )

    return df


def generate_weekly_summary(
    season: int,
    week: int,
    *,
    team_reports: Optional[list[Path]] = None,
    comparison_reports: Optional[list[Path]] = None,
) -> Path:
    season = int(season)
    week = int(week)
    summary_path = weekly_summary_path(season, week)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    # Preferujemy odczyt z manifestów; jeżeli listy zostały podane, też je pokażemy.
    team_manifest = team_reports_manifest_path(season, week)
    cmp_manifest = comparison_reports_manifest_path(season, week)

    team_files = _read_manifest_files(team_manifest)
    cmp_files = _read_manifest_files(cmp_manifest)

    # Dodaj z wejścia (jeśli zostały przekazane w wywołaniu)
    if team_reports:
        team_files.extend(str(p) for p in team_reports)
    if comparison_reports:
        cmp_files.extend(str(p) for p in comparison_reports)

    # Unikalne i posortowane
    team_files = sorted({p for p in team_files if p.endswith(".md")})
    cmp_files = sorted({p for p in cmp_files if p.endswith(".md")})

    lines: list[str] = [f"# Weekly Summary — Week {week}, {season}", ""]
    lines.append("## PowerScore Movers")
    lines.append("")

    if team_files:
        lines.append("### Team Reports")
        for p in team_files:
            # test oczekuje ścieżek w code-span (`...`)
            lines.append(f"- `{Path(p).as_posix()}`")
        lines.append("")
    else:
        lines.append("No team reports generated.")
        lines.append("")

    if cmp_files:
        lines.append("### Matchup Reports")
        for p in cmp_files:
            lines.append(f"- `{Path(p).as_posix()}`")
        lines.append("")
    else:
        lines.append("No matchup reports generated.")
        lines.append("")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Weekly summary written to %s", summary_path)
    return summary_path


__all__ = [
    "available_teams",
    "build_weekly_team_reports",
    "generate_comparison_report",
    "generate_comparison_reports_from_schedule",
    "generate_report",
    "generate_team_report",
    "generate_weekly_summary",
    "make_charts",
    "render_markdown",
    "save_report",
    "validate_schedule_for_week",
]
from metrics.power_score import _weight_mapping
_POWERSCORE_COMPONENTS = [
    {
        "label": "EPA Offense",
        "column": "core_epa_off",
        "weight_key": "offense_epa",
        "is_percent": False,
    },
    {
        "label": "EPA Defense",
        "column": "core_epa_def",
        "weight_key": "defense_epa",
        "is_percent": False,
    },
    {
        "label": "Success Rate Offense",
        "column": "core_sr_off",
        "weight_key": "offense_success_rate",
        "is_percent": True,
    },
    {
        "label": "Tempo",
        "column": "core_ed_sr_off",
        "weight_key": "tempo",
        "is_percent": False,
    },
]
