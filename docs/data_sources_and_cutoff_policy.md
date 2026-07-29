# Data Sources And Cutoff Policy

## Zasada Glowna

Dla analizy przed meczem w Week N system moze uzywac tylko danych z zakonczonych meczow sprzed Week N. Jezeli modul ma dokladny kickoff, dodatkowa zasada brzmi: `record_timestamp < game_start_utc`.

Wspolna logika cutoffu znajduje sie w `utils/data_cutoff.py`.

## Zrodla Danych

Centralny rejestr zrodel jest w `config/data_sources.yaml`.

Pojecia:

- `nflverse` - upstream dataset.
- `nfl_data_py` - adapter/biblioteka Python do pobierania nflverse.
- `nflreadpy` - adapter/biblioteka Python uzywana glownie przez Live Scenario.
- `filesystem` - aktywny provider ETL czytajacy lokalne pliki.
- `local_parquet` - lokalna kopia danych.
- `manual_book_snapshot` - recznie przygotowany snapshot rynku.

## L1 Do L4

1. L1: `etl/l1_ingest.py` czyta provider z `config/settings.yaml`.
2. L2: `etl/mappers.py` normalizuje PBP i dodaje flagi.
3. L3: `etl/l3_aggregate.py` buduje team-week metrics.
4. L4 Core12: `metrics/core12.py` mapuje L3 na kolumny modelowe.
5. Raporty matchup: `app/reports.py`.
6. Picki VP/GOW/GOM/GOY: `scripts/matchup_batch.py` i `scripts/matchup_analyzer.py`.

Aktualny provider glowny w `config/settings.yaml` to `filesystem`, czyli ETL czyta lokalne dane z `data/sources/nfl`.

## Last 3 I Last 5

Rolling windows sa liczone w `metrics/form_windows.py` z `data/l3_team_week/{season}/{week}.parquet`.

Dla Week 6:

- season-to-date: Week 1-5,
- Last 5: Week 1-5,
- Last 3: Week 3-5,
- Week 6 jest zawsze wykluczony.

Kod waliduje zawartosc kolumny `week`, a nie tylko nazwe pliku. Wynik zawiera metadane:

- `analysis_season`,
- `analysis_week`,
- `source_weeks`,
- `max_source_week`,
- `games_in_window`,
- `window_size_requested`,
- `window_size_actual`,
- `data_cutoff_status`.

## Week 1-5

System nie uzupelnia automatycznie brakow priorem z poprzedniego sezonu.

Statusy:

- `AVAILABLE` - pelne okno dostepne,
- `PARTIAL_WINDOW` - okno czesciowe,
- `INSUFFICIENT_CURRENT_SEASON_DATA` - brak biezacych danych sezonu,
- `MISSING_SOURCE_DATA` - brak plikow zrodlowych,
- `CUTOFF_VIOLATION` - dane zawieraja analizowany albo przyszly tydzien.

## Fallbacki

Dozwolony fallback rolling snapshotu:

- requested `through_5` brak,
- istnieje `through_4`,
- analiza jest przed Week 6,
- fallback jest bezpieczny.

Niedozwolony fallback:

- requested `through_5` brak,
- istnieje tylko `through_6`,
- analiza jest przed Week 6.

Takie zachowanie zwraca `MISSING_SAFE_SNAPSHOT`.

## Missing Data Vs True Zero

Zero jest poprawne dla sportowych licznikow i flag, np. turnover w meczu moze wynosic 0.

Null zostaje zachowany dla brakujacych metryk, np. brak EPA nie oznacza EPA = 0.0. L3 zapisuje raport jakosci obok parquet:

`data/l3_team_week/{season}/{week}_data_quality.json`

Core12 dodaje:

- `missing_core_metric_count`,
- `data_quality_status`,
- `nulls_replaced_with_zero`.
- `missing_required_metrics`,
- `missing_optional_metrics`,
- `model_input_complete`.

Zasady:

- prawdziwe zero jest dozwolone dla count/flag, np. `is_turnover = 0`, `turnover_margin = 0`,
- prawdziwe `0.0` jest dozwolone dla rate tylko wtedy, gdy mianownik istnieje i jest `> 0`,
- `0 / 5 = 0.0` jest poprawne,
- `0 / 0`, `null / null` albo brak mianownika daje `null`,
- brak wymaganej kolumny lub wymaganej wartosci daje status missing i blokuje pick,
- brak opcjonalnej tabeli/metryki daje warning i pomija opcjonalny komponent, bez tworzenia sztucznego `0.0`.

Required L3 model metrics:

- `epa_off_mean`,
- `epa_def_mean`,
- `success_rate_off`,
- `success_rate_def`,
- `ypp_off`,
- `ypp_def`,
- `ypp_diff`,
- `tempo`.

Optional/context L3 metrics:

- pass/rush success splits,
- pressure rates,
- explosive rates,
- third-down rates,
- red-zone rates,
- points-per-drive rates/diff,
- field-position metrics.

Required Core12/model parser inputs:

- `core_epa_off`,
- `core_epa_def`,
- `core_sr_off`,
- `core_sr_def`,
- `core_ypp_diff`,
- required matchup report values: PowerScore model components, Success Rate Offense, Turnover Margin, Pressure Rate.

Optional matchup report inputs:

- third-down form,
- red-zone form,
- explosive-play form,
- points-per-drive form,
- field-position edge,
- trend summary,
- analog context.

Optional input missing nie powinien generowac neutralnego edge. Analyzer pokazuje warning i pomija dany komponent.

## Preflight

Preflight jest w `utils/preflight.py` i jest podpinany przed `scripts/matchup_batch.py`.

Sprawdza:

- czy L3 nie zawiera `week >= analysis_week`,
- czy rolling snapshot nie pochodzi z analizowanego albo przyszlego tygodnia,
- duplikaty `season/week/TEAM/game_id`,
- komplet wymaganych metryk modelu,
- jawna liste brakujacych optional metryk jako warning,
- brak pliku lines jako warning.

Przy naruszeniu krytycznym status to `BLOCKED`, a batch nie generuje pickow.

`preflight.status = PASS` jest produkcyjnie dopuszczalny tylko wtedy, gdy:

- cutoff jest bezpieczny,
- `missing_required_metrics` jest puste,
- `data_quality_status` nie jest `FAIL`,
- nie uzyto unsafe bypassu.

Dla technicznych testow istnieje jawny, nieprodukcyjny bypass:

```powershell
python scripts/matchup_batch.py --unsafe-test-only-bypass
```

Output z bypassu ma `preflight.status = BYPASSED_UNSAFE` i
`production_eligible = false`.

## Metryki Proxy

Nie wszystkie metryki sa osobnym zewnetrznym feedem:

- pressure proxy: `etl/mappers.py`, szukane sa sack/QB hit/pressure/hurried w `play_type` albo opisie,
- red zone proxy: play-level `yardline_100 <= 20`, nie drive-level red-zone trip,
- third-down proxy: `down == 3` i `yards_gained >= distance`.

## Dane Automatyczne, Manualne I Niezaimplementowane

Automatyczne lub lokalnie cachowane:

- schedules,
- PBP ETL,
- L1-L4,
- Live Scenario historical dataset,
- backtests i learning ledger na lokalnych plikach.

Manualne:

- market book snapshot,
- market quotes,
- injuries,
- roster/depth chart,
- weather notes,
- public betting,
- power rankings.

Niezaimplementowane jako pelny automatyczny feed:

- penalties,
- pass EPA/rush EPA split,
- official injury feed,
- official depth-chart feed,
- public betting provider.
