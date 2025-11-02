import polars as pl
from pathlib import Path
import argparse
import re
from textwrap import dedent

def load_l4_form(season: int, cutoff_week: int) -> pl.DataFrame:
    """
    Wczytaj tygodnie 1..cutoff_week z L4 do jednego DF.
    Zwróć df z kolumnami: season, week, TEAM, core_epa_off, ...
    """
    frames = []
    for wk in range(1, cutoff_week + 1):
        path = Path(f"data/l4_core12/{season}/{wk}.parquet")
        if not path.exists():
            # pomijamy tydzień jeśli nie ma pliku (bye week / brak jeszcze danych)
            continue

        df_wk = pl.read_parquet(path).with_columns([
            pl.lit(wk).alias("week"),
            pl.lit(season).alias("season"),
        ])
        frames.append(df_wk)

    if not frames:
        raise RuntimeError("Brak danych L4 dla podanego sezonu/tygodnia.")

    return pl.concat(frames, how="vertical")


def summarize_metric_for_team(df_team: pl.DataFrame, value_col: str) -> dict:
    """
    Na podstawie wierszy jednej drużyny (TEAM=X), posortowanych po week,
    policz:
    - Season-to-date: średnia ze wszystkich tygodni
    - Last 5: średnia z tail(5)
    - Last 3: średnia z tail(3)

    Zwróć floaty (mogą być None jeśli team nie ma wystarczająco wierszy).
    """
    if df_team.is_empty():
        return {"season_to_date": None, "last5": None, "last3": None}

    df_team = df_team.sort("week")

    col = df_team[value_col]

    def _safe_mean(series: pl.Series) -> float:
        return float(series.mean()) if series.len() > 0 else None

    season_to_date = _safe_mean(col)
    last5 = _safe_mean(col.tail(5))
    last3 = _safe_mean(col.tail(3))

    return {
        "season_to_date": season_to_date,
        "last5": last5,
        "last3": last3,
    }


def build_form_table(df_l4: pl.DataFrame, value_col: str, teams: list[str]) -> pl.DataFrame:
    """
    Zbuduj tabelę formy (TEAM, Season-to-date, Last 5, Last 3)
    dla wybranych drużyn i danej metryki (np. core_epa_off).
    """
    rows = []
    for team in teams:
        stats = summarize_metric_for_team(
            df_l4.filter(pl.col("TEAM") == team),
            value_col=value_col,
        )
        rows.append({
            "TEAM": team,
            "Season-to-date": stats["season_to_date"],
            "Last 5": stats["last5"],
            "Last 3": stats["last3"],
        })

    return pl.DataFrame(rows)


def format_float(x: float, decimals: int = 3) -> str:
    if x is None:
        return "n/a"
    return f"{x:.{decimals}f}"


def render_table_markdown(df_form: pl.DataFrame, title: str, cutoff_week: int) -> str:
    """
    Renderuje tabelkę w tym samym stylu co raport:
    ## {title} (up to Week {cutoff_week})

    | Team | Season-to-date | Last 5 | Last 3 |
    |------|---------------:|-------:|-------:|
    | DET  | 0.088 | 0.073 | 0.054 |
    | MIN  | -0.081 | -0.027 | -0.078 |
    """
    lines = []
    lines.append(f"## {title} (up to Week {cutoff_week})\n")
    lines.append("| Team | Season-to-date | Last 5 | Last 3 |")
    lines.append("|------|---------------:|-------:|-------:|")

    for row in df_form.iter_rows(named=True):
        lines.append(
            f"| {row['TEAM']} | "
            f"{format_float(row['Season-to-date'])} | "
            f"{format_float(row['Last 5'])} | "
            f"{format_float(row['Last 3'])} |"
        )

    return "\n".join(lines)


def parse_core_epa_off_from_report(md_text: str) -> pl.DataFrame:
    """
    Wyciąga sekcję '## Core EPA Offense Form ...' z pliku .md raportu
    i buduje DataFrame z kolumnami TEAM, Season-to-date, Last 5, Last 3.
    Zakładamy dokładnie taki układ jak generuje raport.
    """
    # Znajdź blok zaczynający się od '## Core EPA Offense Form'
    pattern_header = r"## Core EPA Offense Form.*?(?:\r?\n)(?:\r?\n)?(\|.*?)(?:\r?\n\r?\n|$)"
    m = re.search(pattern_header, md_text, flags=re.DOTALL)
    if not m:
        raise RuntimeError("Nie znalazłem sekcji 'Core EPA Offense Form' w raporcie.")

    table_block = m.group(1).strip()

    # Rozbij na linie i pomiń dwie pierwsze (nagłówki kolumn + separator ----)
    lines = table_block.splitlines()
    data_lines = [ln for ln in lines if ln.strip().startswith("|")][2:]

    teams = []
    s2d_vals = []
    last5_vals = []
    last3_vals = []

    for ln in data_lines:
        # przykład linii:
        # | DET | 0.088 | 0.073 | 0.054 |
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) < 4:
            continue

        team = cells[0]
        s2d = float(cells[1])
        last5 = float(cells[2])
        last3 = float(cells[3])

        teams.append(team)
        s2d_vals.append(s2d)
        last5_vals.append(last5)
        last3_vals.append(last3)

    return pl.DataFrame({
        "TEAM": teams,
        "Season-to-date": s2d_vals,
        "Last 5": last5_vals,
        "Last 3": last3_vals,
    })


def compare_form_tables(df_calc: pl.DataFrame, df_report: pl.DataFrame, tolerance: float = 1e-6) -> pl.DataFrame:
    """
    Łączy (join po TEAM) i sprawdza różnice między wyliczeniem a raportem.
    Zwraca tabelę kontroli z kolumnami diff_*.
    """
    merged = df_calc.join(df_report, on="TEAM", how="inner", suffix="_report")

    # policz różnice
    return merged.with_columns([
        (pl.col("Season-to-date") - pl.col("Season-to-date_report")).alias("diff_s2d"),
        (pl.col("Last 5") - pl.col("Last 5_report")).alias("diff_last5"),
        (pl.col("Last 3") - pl.col("Last 3_report")).alias("diff_last3"),
        ((pl.col("Season-to-date") - pl.col("Season-to-date_report")).abs() <= tolerance).alias("match_s2d"),
        ((pl.col("Last 5") - pl.col("Last 5_report")).abs() <= tolerance).alias("match_last5"),
        ((pl.col("Last 3") - pl.col("Last 3_report")).abs() <= tolerance).alias("match_last3"),
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week", type=int, required=True,
                        help="to jest current_week w raporcie (czyli DET vs MIN przy week 9)")
    parser.add_argument("--team-a", type=str, required=True)
    parser.add_argument("--team-b", type=str, required=True)
    args = parser.parse_args()

    season = args.season
    current_week = args.week
    teams = [args.team_a, args.team_b]

    cutoff_week = current_week - 1  # np. week=9 => cutoff=8

    # 1. wczytaj nasze dane L4
    df_l4 = load_l4_form(season, cutoff_week)

    # 2. policz formę dla Core EPA Offense (= core_epa_off)
    df_form_calc = build_form_table(df_l4, value_col="core_epa_off", teams=teams)

    print("=== [CALC] Nasz wyliczony Core EPA Offense Form z L4 ===")
    print(df_form_calc)

    # 3. wczytaj raport markdown
    report_path = Path(f"data/reports/comparisons/{season}_w{current_week}/{args.team_a}_vs_{args.team_b}.md")
    if not report_path.exists():
        raise RuntimeError(f"Nie znalazłem raportu pod {report_path}")

    md_text = report_path.read_text(encoding="utf-8")

    # 4. wyciągnij tabelę Core EPA Offense Form z raportu
    df_form_report = parse_core_epa_off_from_report(md_text)

    print("\n=== [REPORT] Tabela z raportu ===")
    print(df_form_report)

    # 5. porównanie
    diff = compare_form_tables(df_form_calc, df_form_report)

    print("\n=== [QA DIFF] Porównanie L4 vs Raport ===")
    print(diff)

    # 6. ładny komunikat końcowy
    all_match = (
        diff["match_s2d"].all() and
        diff["match_last5"].all() and
        diff["match_last3"].all()
    )
    if all_match:
        print("\n✅ QA OK: raport zgadza się z danymi L4 dla Core EPA Offense Form.")
    else:
        print("\n❌ QA MISMATCH: raport NIE zgadza się z danymi L4 (patrz diff wyżej).")


if __name__ == "__main__":
    main()
