import polars as pl
from pathlib import Path
from typing import Optional, List
from metrics.form_windows import compute_form_windows

def _df_to_markdown(df: pl.DataFrame) -> str:
    """
    Convert a polars.DataFrame to a GitHub-flavored markdown table.
    We include header row, separator row, and then data rows.
    Floats go to 3 decimal places, everything else as-is.
    """
    cols = df.columns

    # header
    header = "| " + " | ".join(cols) + " |"

    # separator
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"

    # rows
    body_rows = []
    for row in df.to_dicts():
        cells = []
        for c in cols:
            val = row[c]
            if isinstance(val, float):
                cells.append(f"{val:.3f}")
            else:
                cells.append(str(val))
        body_rows.append("| " + " | ".join(cells) + " |")

    return "\n".join([header, sep, *body_rows])


def build_comparison_report_with_form(
    season: int,
    week: int,
    team_a: str,
    team_b: str,
    core12_a: pl.DataFrame,
    core12_b: pl.DataFrame,
) -> str:
    """
    This returns the full markdown for the matchup report, including:
    - header
    - metric comparison table (existing logic)
    - recent form windows (last 5 / last 3 / season-to-date)
    NOTE: We assume core12_a/core12_b already filtered to [team_a], [team_b].
    """

    # 1. Core12 comparison block (simplified assumption: you already build a df_comparison somewhere)
    # We'll just assert that exists outside and is passed in OR you splice your existing code here.

    # 2. Form windows
    form_df = compute_form_windows(season, week, [team_a, team_b])

    form_md = _df_to_markdown(form_df)

    # 3. Stitch final markdown.
    # You should merge this with however you're currently building the report body.
    # Below is a skeleton: header + placeholder for the old comparison table + the new form section.
    md_parts: List[str] = []

    md_parts.append(f"# Matchup Report - {team_a} vs {team_b}")
    md_parts.append("")
    md_parts.append("## Metric Comparison")
    md_parts.append("")
    md_parts.append("<!-- TODO: insert your existing metric comparison markdown table here -->")
    md_parts.append("")
    md_parts.append("## Recent Form (Season / Last 5 / Last 3)")
    md_parts.append("")
    md_parts.append(form_md)
    md_parts.append("")

    return "\n".join(md_parts)
