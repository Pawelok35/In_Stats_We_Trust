# INVENTORY.md

## A.1 Executive Summary
- 48 tracked statistics across layers L1–L4 (details in A.2).
- Compute flow: etl/mappers.py:canonicalize_l1, etl/mappers.py:prepare_l2, etl/l3_aggregate.py:_aggregate, metrics/core12.py:compute, metrics/power_score.py:compute orchestrated via pp/cli.py:38-314.
- Reporting & delivery: markdown generation in pp/reports.py:400-1097, charts via pp/reports.py:294-397, and API preview in pp/api.py:19-55.

## A.2 Statystyki – tabela zbiorcza
| stat_key | display_name | layer | file_path | function | lines | inputs | derived_from | written_to | used_by | tests | aliases |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L1.season | Season | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | ingest params | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip |  |
| L1.week | Week | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | ingest params | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip |  |
| L1.game_id | Game ID | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | raw['game_id'] | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip |  |
| L1.play_id | Play ID | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | raw['play_id'] | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip |  |
| L1.posteam | Possessing team | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | raw['posteam'] | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip | TEAM (L2) |
| L1.defteam | Defending team | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | raw['defteam'] | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip | OPP (L2) |
| L1.drive | Drive number | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | raw['drive'] | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip |  |
| L1.play_type | Play type | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | raw['play_type'] | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip |  |
| L1.epa | Expected points added | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | raw['epa'] | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip |  |
| L1.success | Success probability | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | raw['success'] | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip |  |
| L1.yardline_100 | Field position (to EZ) | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | raw['yardline_100'] | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip |  |
| L1.down | Down | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | raw['down'] | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip |  |
| L1.distance | Yards to go | L1 | etl/mappers.py | canonicalize_l1 | 57-98 | raw distance/ydstogo | etl/l1_ingest.py:run (provider parquet) | data/l1/<season>/<week>.parquet | etl/l2_clean.py:run | tests/test_l1_ingest.py::test_l1_ingest_filesystem_roundtrip |  |
| L2.season | Season | L2 | etl/mappers.py | prepare_l2 | 116-212 | L1.season | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts |  |
| L2.week | Week | L2 | etl/mappers.py | prepare_l2 | 116-212 | L1.week | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts |  |
| L2.game_id | Game ID | L2 | etl/mappers.py | prepare_l2 | 116-212 | L1.game_id | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts |  |
| L2.play_id | Play ID | L2 | etl/mappers.py | prepare_l2 | 116-212 | L1.play_id | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts |  |
| L2.TEAM | Possessing team (normalized) | L2 | etl/mappers.py | prepare_l2 | 116-212 | L1.posteam | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts | team (reports, L4) |
| L2.OPP | Opponent team | L2 | etl/mappers.py | prepare_l2 | 116-212 | L1.defteam | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts |  |
| L2.drive | Drive | L2 | etl/mappers.py | prepare_l2 | 116-212 | L1.drive | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts |  |
| L2.play_type | Play type | L2 | etl/mappers.py | prepare_l2 | 116-212 | L1.play_type | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts |  |
| L2.epa | Expected points added | L2 | etl/mappers.py | prepare_l2 | 116-212 | L1.epa | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts |  |
| L2.success | Success probability | L2 | etl/mappers.py | prepare_l2 | 116-212 | L1.success | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts |  |
| L2.yards_gained | Yards gained | L2 | etl/mappers.py | prepare_l2 | 116-212 | raw or null fill | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts |  |
| L2.success_bin | Success flag (>=0.5) | L2 | etl/mappers.py | prepare_l2 | 116-212 | computed from success | L1 canonical dataframe | data/l2/<season>/<week>.parquet | etl/l3_aggregate.py:_aggregate | tests/test_l2_clean.py::test_l2_clean_generates_normalized_artifacts |  |
| L3.season | Season | L3 | etl/l3_aggregate.py | _aggregate | 42-84 | L2.season | L2 cleaned dataframe | data/l3_team_week/<season>/<week>.parquet | metrics/core12.py:compute | tests/test_l3_counts.py::test_l3_aggregation_produces_team_metrics |  |
| L3.week | Week | L3 | etl/l3_aggregate.py | _aggregate | 42-84 | L2.week | L2 cleaned dataframe | data/l3_team_week/<season>/<week>.parquet | metrics/core12.py:compute | tests/test_l3_counts.py::test_l3_aggregation_produces_team_metrics |  |
| L3.TEAM | Team code | L3 | etl/l3_aggregate.py | _aggregate | 42-84 | L2.TEAM | L2 cleaned dataframe | data/l3_team_week/<season>/<week>.parquet | metrics/core12.py:compute | tests/test_l3_counts.py::test_l3_aggregation_produces_team_metrics | team (Core12) |
| L3.drives | Unique drives | L3 | etl/l3_aggregate.py | _aggregate | 42-84 | group by drive | L2 cleaned dataframe | data/l3_team_week/<season>/<week>.parquet | metrics/core12.py:compute | tests/test_l3_counts.py::test_l3_aggregation_produces_team_metrics |  |
| L3.plays | Play count | L3 | etl/l3_aggregate.py | _aggregate | 42-84 | group len | L2 cleaned dataframe | data/l3_team_week/<season>/<week>.parquet | metrics/core12.py:compute | tests/test_l3_counts.py::test_l3_aggregation_produces_team_metrics |  |
| L3.epa_off_mean | Mean offensive EPA | L3 | etl/l3_aggregate.py | _aggregate | 42-84 | mean of epa | L2 cleaned dataframe | data/l3_team_week/<season>/<week>.parquet | metrics/core12.py:compute | tests/test_l3_counts.py::test_l3_aggregation_produces_team_metrics |  |
| L3.success_rate_off | Offensive success rate | L3 | etl/l3_aggregate.py | _aggregate | 42-84 | mean of success | L2 cleaned dataframe | data/l3_team_week/<season>/<week>.parquet | metrics/core12.py:compute | tests/test_l3_counts.py::test_l3_aggregation_produces_team_metrics |  |
| L3.epa_def_mean | Mean defensive EPA allowed | L3 | etl/l3_aggregate.py | _aggregate | 42-84 | mean by OPP | L2 cleaned dataframe | data/l3_team_week/<season>/<week>.parquet | metrics/core12.py:compute | tests/test_l3_counts.py::test_l3_aggregation_produces_team_metrics |  |
| L3.success_rate_def | Defensive success rate | L3 | etl/l3_aggregate.py | _aggregate | 42-84 | mean success by OPP | L2 cleaned dataframe | data/l3_team_week/<season>/<week>.parquet | metrics/core12.py:compute | tests/test_l3_counts.py::test_l3_aggregation_produces_team_metrics |  |
| L3.tempo | Plays per drive | L3 | etl/l3_aggregate.py | _aggregate | 42-84 | plays/drives | L2 cleaned dataframe | data/l3_team_week/<season>/<week>.parquet | metrics/core12.py:compute | tests/test_l3_counts.py::test_l3_aggregation_produces_team_metrics |  |
| L4Core12.season | Season | L4 Core12 | metrics/core12.py | compute | 46-126 | L3.season | L3 team-week aggregates | data/l4_core12/<season>/<week>.parquet | metrics/power_score.py:compute; app/reports.generate_team_report | tests/test_metrics_core12.py::test_core12_compute_generates_expected_columns |  |
| L4Core12.week | Week | L4 Core12 | metrics/core12.py | compute | 46-126 | L3.week | L3 team-week aggregates | data/l4_core12/<season>/<week>.parquet | metrics/power_score.py:compute; app/reports.generate_team_report | tests/test_metrics_core12.py::test_core12_compute_generates_expected_columns |  |
| L4Core12.TEAM | Team code | L4 Core12 | metrics/core12.py | compute | 46-126 | L3.TEAM | L3 team-week aggregates | data/l4_core12/<season>/<week>.parquet | metrics/power_score.py:compute; app/reports.generate_team_report | tests/test_metrics_core12.py::test_core12_compute_generates_expected_columns | team (PowerScore/report previews) |
| L4Core12.core_epa_off | Core EPA offense | L4 Core12 | metrics/core12.py | compute | 46-126 | L3.epa_off_mean | L3 team-week aggregates | data/l4_core12/<season>/<week>.parquet | metrics/power_score.py:compute; app/reports.generate_team_report | tests/test_metrics_core12.py::test_core12_compute_generates_expected_columns |  |
| L4Core12.core_epa_def | Core EPA defense | L4 Core12 | metrics/core12.py | compute | 46-126 | -L3.epa_def_mean | L3 team-week aggregates | data/l4_core12/<season>/<week>.parquet | metrics/power_score.py:compute; app/reports.generate_team_report | tests/test_metrics_core12.py::test_core12_compute_generates_expected_columns |  |
| L4Core12.core_sr_off | Core SR offense | L4 Core12 | metrics/core12.py | compute | 46-126 | L3.success_rate_off | L3 team-week aggregates | data/l4_core12/<season>/<week>.parquet | metrics/power_score.py:compute; app/reports.generate_team_report | tests/test_metrics_core12.py::test_core12_compute_generates_expected_columns |  |
| L4Core12.core_sr_def | Core SR defense | L4 Core12 | metrics/core12.py | compute | 46-126 | 1 - success_rate_def | L3 team-week aggregates | data/l4_core12/<season>/<week>.parquet | metrics/power_score.py:compute; app/reports.generate_team_report | tests/test_metrics_core12.py::test_core12_compute_generates_expected_columns |  |
| L4Core12.core_ed_sr_off | Explosive drive SR | L4 Core12 | metrics/core12.py | compute | 46-126 | success_rate_off * tempo | L3 team-week aggregates | data/l4_core12/<season>/<week>.parquet | metrics/power_score.py:compute; app/reports.generate_team_report | tests/test_metrics_core12.py::test_core12_compute_generates_expected_columns |  |
| L4Core12.core_third_down_conv | 3rd down conversion proxy | L4 Core12 | metrics/core12.py | compute | 46-126 | 0.6*SR + 0.4*EPA | L3 team-week aggregates | data/l4_core12/<season>/<week>.parquet | metrics/power_score.py:compute; app/reports.generate_team_report | tests/test_metrics_core12.py::test_core12_compute_generates_expected_columns |  |
| L4PowerScore.season | Season | L4 PowerScore | metrics/power_score.py | compute | 78-160 | Core12.season | Core12 dataset + config weights | data/l4_powerscore/<season>/<week>.parquet | app/reports.make_charts; app/reports.generate_team_report; app.cli.compare_report | tests/test_powerscore.py::test_powerscore_monotonic |  |
| L4PowerScore.week | Week | L4 PowerScore | metrics/power_score.py | compute | 78-160 | Core12.week | Core12 dataset + config weights | data/l4_powerscore/<season>/<week>.parquet | app/reports.make_charts; app/reports.generate_team_report; app.cli.compare_report | tests/test_powerscore.py::test_powerscore_monotonic |  |
| L4PowerScore.team | Team code | L4 PowerScore | metrics/power_score.py | compute | 78-160 | Core12.TEAM + alias map | Core12 dataset + config weights | data/l4_powerscore/<season>/<week>.parquet | app/reports.make_charts; app/reports.generate_team_report; app.cli.compare_report | tests/test_powerscore.py::test_powerscore_monotonic | TEAM (upstream) |
| L4PowerScore.power_score | Weighted PowerScore | L4 PowerScore | metrics/power_score.py | compute | 78-160 | Core12 metrics * config weights | Core12 dataset + config weights | data/l4_powerscore/<season>/<week>.parquet | app/reports.make_charts; app/reports.generate_team_report; app.cli.compare_report | tests/test_powerscore.py::test_powerscore_monotonic |  |

## A.3 Mapa koncowych produktów
- **Weekly report** – pp/reports.py:400-464 renders eport_week.md.j2, saves markdown at data/reports/<season>_w<week>_summary.md, attaches charts, and records bundle manifest.
- **Team reports** – pp/reports.py:595-637 builds per-team markdown + bar chart assets, manifest at 	eam_reports_manifest_path; consumed by CLI uild-weekly-reports.
- **Matchup reports** – pp/reports.py:765-826 reads schedule pairs, optional edge_team_vs_team parquet, renders comparison markdown and summary chart per matchup.
- **Charts & snapshots** – pp/reports.py:294-397 turns PowerScore/Core12 artifacts into PNGs (PowerScore Top 10, Tempo Leaders) embedded in weekly + team reports.
- **API** – pp/api.py:19-55 exposes /health and /metrics/core12/preview, serving data from data/l4_core12/<season>/<week>.parquet with contract validation.

## A.4 Sciezki artefaktów (SEASON=2025, WEEK=9)
- data/l4_core12/2025/9.parquet – **missing** (last snapshot: data/l4_core12/2025/8.parquet); rerun uild-week after fixing Core12 pipeline.
- data/l4_powerscore/2025/9.parquet – **missing**; compute via metrics.power_score.compute once Core12 is available.
- data/reports/2025_w9_summary.md + data/reports/2025_w9/manifest.json – present from previous run.
- data/reports/teams/2025_w9/*.md + data/reports/teams/2025_w9/manifest.json – present (BAL, MIA) with PNG assets under ssets/.
- data/reports/comparisons/2025_w9/*.md + data/reports/comparisons/2025_w9/manifest.json – present (BAL_vs_MIA.md, BUF_vs_KC.md, placeholder AAA_vs_BBB.md).

## A.5 Checklisty weryfikacyjne
- Szczególowy runbook komend w sekcji D; uzywaj go do odtwarzania i walidacji artefaktów.

## D. RUNBOOK VERIFICATION

### D.1 Komendy bazowe (PowerShell)
`powershell
. .\.venv\Scripts\Activate.ps1
python -m app.cli build-week --season 2025 --week 9
python -m app.cli build-weekly-reports --season 2025 --week 9 --pairs-only
`
Oczekiwane: pelny ETL L1?L4, raport tygodniowy, matchup manifest uzupelniony (exit code 0).

### D.2 Szybkie sanity-checki Parquet/kolumn
`powershell
python -c "import polars as pl; df=pl.read_parquet(r'data/l4_core12/2025/8.parquet'); print(df.columns); print(df.height)"
python -c "import polars as pl; df=pl.read_parquet(r'data/l4_powerscore/2025/8.parquet'); print(df.columns); print(df.height)"
`
Oczekiwane: kolumny z tabeli Core12/PowerScore, liczba wierszy > 0; uzyj 8 dopóki 9.parquet nie zostanie przeliczone.

### D.3 Raport porównawczy
`powershell
python -m app.cli compare-report --season 2025 --week 9 --team-a MIA --team-b BAL
`
Oczekiwane: markdown w data/reports/comparisons/2025_w9/MIA_vs_BAL.md, nowe PNG w ssets/MIA_vs_BAL, manifest zaktualizowany.

### D.4 Raport tygodniowy (summary)
- Test-Path data/reports/2025_w9_summary.md
- Sprawdz sekcje: PowerScore Top 10, Core12 preview, listy linków do team/comparison manifest entries.

### D.5 Manifesty
- Zweryfikuj JSON-y: data/reports/2025_w9/manifest.json, data/reports/teams/2025_w9/manifest.json, data/reports/comparisons/2025_w9/manifest.json.
- Kazdy wpis powinien miec path, sha256, size; brakujace wpisy = blad w generowaniu.

### D.6 Testy regresyjne
`powershell
python -m pytest -q
`
Najwazniejsze: 	ests/test_l1_ingest.py, 	ests/test_l2_clean.py, 	ests/test_l3_counts.py, 	ests/test_metrics_core12.py, 	ests/test_powerscore.py, 	ests/test_cli_reports.py, 	ests/test_reports_renderers.py – pokrywaja warstwy ETL, metryki i raporty.

## E. Findings & Recommendations
1. Garbled delta arrows in _fmt_delta_arrow (pp/reports.py:64-69) – zastap niekodowalny tekst ASCII (np. +?, -?) i dopasuj do _comparison_edges.
2. _build_comparison_metrics (pp/reports.py:692-724) nie jest uzywane; raporty matchup traca Core12/PowerScore zestawienie. Wlacz sekcje tabelaryczna przed manifestem.
3. Placeholdery "AAA"/"BBB" w TEAM_ALIASES (metrics/power_score.py:34-52) powoduja zla normalizacje i raporty z fikcyjnymi kodami – usun aliasy po unifikacji zródel.
4. Funkcja 	eam_report w CLI (pp/cli.py:84-147) zawiera zduplikowany kod po 	yper.echo, co grozi podwójnym wykonaniem i trudnym debugiem; uprosc do jednej sciezki.
5. Warstwy L1-L3 nadal uzywaja starego podpisu write_manifest(target, payload, manifest_path=...) (etl/l1_ingest.py:62-75, etl/l2_clean.py:52-83, etl/l3_aggregate.py:97-116); zrefaktoruj do nowego API (path=...) aby zachowac spójnosc i uniknac regresji.
6. Brak artefaktów l4_core12/l4_powerscore dla tygodnia 9 moze lamac API /metrics/core12/preview oraz sekcje raportowe – po naprawie PowerScore schema odtwórz uild-week i manualnie zweryfikuj manifesty.

