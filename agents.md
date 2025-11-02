# AGENTS.md — In Stats We Trust (v3.1.1)

> Generated from `codex_tasks.yaml` (version 3.1.1). Ownership, responsibilities, dependencies, I/O contracts, and QA gates per agent.

## Conventions
- **Agent ID**: `Agent_*`
- **Owns tasks**: identyfikatory z `codex_tasks.yaml`
- **Depends on**: jawne zależności między taskami/warstwami
- **Inputs / Outputs / Contracts**: artefakty wej./wyj. i wymuszone kontrakty I/O
- **QA Gates**: kryteria akceptacji / testy / bramki jakości
- **Interfaces**: komendy i moduły wywołaniowe

## Execution Order (Happy Path)
1) T01–T09 (Foundation)  
2) T10–T12 (ETL L1→L3)  
3) T13 (E2E smoke)  
4) T20–T22 (Core Metrics)  
5) T23 (API)  
6) T24 (Report snapshot)  
7) T30–T33 (Hardening)

## Blockers (golden_path.blocked_if)
- Kontrakt I/O niespełniony
- NaN w kluczach lub INF w danych
- Brak audytu L2
- Metryki modyfikują ETL (naruszenie warstw)

## Definition of Done (per build-week)
- Brak hardcodów `season/week`.
- Jedno źródło ścieżek: `utils/paths.py` + loader: `utils/config.py`.
- Każda warstwa zapisuje `.parquet` + `manifest.json`; L2 tworzy audyt JSONL.
- Testy smoke/E2E PASS; kluczowe utils mają testy.
- Ruff/Black czysto; **żadnych `print` w libach** (tylko logger).

## Quick Commands
- `python -m pip install -r requirements.txt`
- `python -m app.cli build-week --season 2025 --week 8`
- `python -m pytest -q`
- `python -m ruff check .`
- `python -m black --check .`

---

## Agents — szczegóły

### Agent_Foundation
**Owns tasks:** `T01_init_repo` — Szkielet v3 + dependency hygiene  
**Milestone:** `M1`  
**Depends on:** —  
**Responsibilities / Steps:**
- Struktura repo: `etl/`, `metrics/`, `app/`, `config/`, `tests/`, `utils/`, `data/`, `templates/`, `scripts/`.
- Zależności bazowe: ruff, black, pytest, pydantic, polars, duckdb, fastapi, typer, pyyaml, jinja2.
- `.env.example`, `.gitignore`.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** —  
- **Outputs:** podstawowy szkielet + `requirements.txt`  
- **Contracts:** narzędzia dostępne jako `python -m ...`  
**QA Gates:**
- Instalacja zależności działa; importy bazowych pakietów przechodzą.  
**Interfaces:** `python -m pip install -U pip` / `python -m pip install -r requirements.txt`

---

### Agent_Config_SSOT
**Owns tasks:** `T02_config` — Konfiguracja i ścieżki (SSOT)  
**Milestone:** `M1`  
**Depends on:** `Agent_Foundation`  
**Key files:** `config/settings.yaml`, `utils/paths.py`, `utils/config.py`  
**Responsibilities / Steps:**
- `settings.yaml`: `DATA_ROOT`, `default_season/week`, `data_sources`, `weights`.
- `config.py`: pydantic loader + walidacja, cache.
- `paths.py`: `path_for(layer, season, week)` + `manifest_path`, `report_path`, `l2_audit_path`.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** `config/settings.yaml`  
- **Outputs:** API `load_settings()`, `path_for()`  
- **Contracts:** brak hardcodów `season/week` poza CLI  
**QA Gates:**
- Brak hardcodów sezon/tydzień w libach; `from utils.paths import path_for` działa w REPL.  
**Interfaces:** —  

---

### Agent_CLI_Orchestrator
**Owns tasks:** `T03_cli` — CLI orkiestracji  
**Milestone:** `M1`  
**Depends on:** `Agent_Config_SSOT`  
**Key files:** `app/cli.py`  
**Responsibilities / Steps:**
- Typer: `build-week --season INT --week INT`.
- Orkiestracja: `l1_ingest → l2_clean → l3_aggregate → reports.generate`.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** parametry CLI (`season`, `week`)  
- **Outputs:** artefakty L1/L2/L3, raport tygodniowy  
- **Contracts:** parametry trafiają do każdego etapu  
**QA Gates:**
- `python -m app.cli --help` działa; parametry propagują się.  
**Interfaces:** `python -m app.cli --help`

---

### Agent_Logging
**Owns tasks:** `T04_logging` — Spójny logging  
**Milestone:** `M1`  
**Depends on:** `Agent_Foundation`  
**Key files:** `utils/logging.py`  
**Responsibilities / Steps:**
- `basicConfig(level=INFO)`, format, `captureWarnings`, `get_logger(name)`.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** —  
- **Outputs:** globalna inicjalizacja logowania  
- **Contracts:** **żadnych `print` w libach**  
**QA Gates (Telemetry Enforcement):**
- Każdy moduł tworzy logger: `logger = get_logger(__name__)`.
- Brak `print` poza CLI/tests.

---

### Agent_Tests_QA
**Owns tasks:** `T05_tests_boot` — Testy smoke + linter  
**Milestone:** `M1`  
**Depends on:** `Agent_Config_SSOT`, `Agent_CLI_Orchestrator`, `Agent_Logging`  
**Key files:** `tests/test_config.py`, `tests/test_pipeline_smoke.py`, `.ruff.toml`, `pyproject.toml`  
**Responsibilities / Steps:**
- Smoke: importy, CLI help.
- Lint: ruff/black, minimalne testy.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** repo zainicjalizowane  
- **Outputs:** zielone testy i linter  
- **Contracts:** komendy uruchamialne `python -m ...`  
**QA Gates:**
- `pytest -q` PASS, `ruff/black` czysto.

---

### Agent_SchemaContracts
**Owns tasks:** `T06_schema_contracts` — Kontrakty I/O  
**Milestone:** `M1`  
**Depends on:** `Agent_Tests_QA`  
**Key files:** `utils/contracts.py`, `config/contracts.yaml`, `tests/test_contracts.py`  
**Responsibilities / Steps:**
- Definicje kontraktów L1/L2/L3 (kolumny/typy/keys).
- Walidator `validate_df(df, contract)`.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** ramki L1/L2/L3  
- **Outputs:** wyjątek przy złamaniu kontraktu (fail-fast)  
- **Contracts:** `config/contracts.yaml`  
**QA Gates:**  
- Złamany kontrakt → brak zapisu artefaktu; testy czerwone.

---

### Agent_Guardrails
**Owns tasks:** `T07_guardrails_nan_inf` — Blokady NaN/INF  
**Milestone:** `M1`  
**Depends on:** `Agent_SchemaContracts`  
**Key files:** `utils/guards.py`, `tests/test_guards.py`  
**Responsibilities / Steps:**
- `check_no_nan_in_keys(df, keys)`, `check_no_inf(df)`.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** ramki L1/L2/L3  
- **Outputs:** wyjątek przy naruszeniach  
- **Contracts:** brak NaN w kluczach; brak INF w floatach  
**QA Gates:**  
- Testy jednostkowe przechodzą.

---

### Agent_Manifest
**Owns tasks:** `T08_manifest_hash` — Manifest (SHA-256)  
**Milestone:** `M1`  
**Depends on:** `Agent_SchemaContracts`, `Agent_Guardrails`  
**Key files:** `utils/manifest.py`, `tests/test_manifest.py`  
**Responsibilities / Steps:**
- `compute_sha256(path)`, `write_manifest(file, payload)`.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** ścieżka do artefaktu warstwy  
- **Outputs:** `manifest.json` obok artefaktu  
- **Contracts:** `layer, season, week, sha256, rows, cols, created_at`  
**QA Gates:**  
- Manifest zapisany; test PASS.

---

### Agent_Reports
**Owns tasks:** `T09_report_md` — Raport tygodniowy (.md)  
**Milestone:** `M1`  
**Depends on:** `Agent_CLI_Orchestrator`, `Agent_L3_TeamWeek` (przy pełnym przebiegu)  
**Key files:** `app/reports.py`, `templates/report_week.md.j2`  
**Responsibilities / Steps:**
- Render .md: shapes L1–L3, audyt L2 (tail), sanity L3, snapshot (jeśli obecny).  
**Inputs / Outputs / Contracts:**  
- **Inputs:** artefakty L1/L2/L3, audyt L2  
- **Outputs:** `data/reports/{season}_w{week}_summary.md`  
- **Contracts:** szablon Jinja spójny ze źródłami  
**QA Gates:**  
- Raport renderuje się na przebiegu E2E.

**Owns tasks:** `T24_report_metrics_snapshot` — Snapshot metryk w raporcie  
**Milestone:** `M3`  
**Depends on:** `Agent_Metrics_Core12`, `Agent_PowerScore`  
**Responsibilities / Steps:**
- Dodać do raportu TOP-N PowerScore + widok Core12 (warunkowo).  
**QA Gates:**  
- Raport pokazuje PowerScore + wdrożone Core12 (tabela/preview).

---

### Agent_L1_Ingest
**Owns tasks:** `T10_l1_ingest` — ETL L1 (IO + schemat)  
**Milestone:** `M2`  
**Depends on:** `Agent_SchemaContracts`, `Agent_Guardrails`, `Agent_Manifest`  
**Key files:** `etl/l1_ingest.py`, `etl/sources/nfl_data_py.py`, `etl/sources/filesystem.py`, `etl/mappers.py`  
**Responsibilities / Steps:**
- Pobór z `settings.data_sources.provider` (nfl_data_py/filesystem).
- Mapowanie surowych kolumn → minimalny schemat L1.
- `validate_df(...,'L1')`, `check_no_nan_in_keys([...])`.
- Zapis: `data/l1/{season}/{week}.parquet` + manifest.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** surowe źródła danych  
- **Outputs:** L1 `.parquet` + `manifest.json`  
- **Contracts:** `contracts:L1`  
**QA Gates:**  
- Kontrakt L1 spełniony; manifest istnieje.

---

### Agent_L2_Clean_Audit
**Owns tasks:** `T11_l2_clean` — ETL L2 (typy, nazwy, filtry) + audyt  
**Milestone:** `M2`  
**Depends on:** `Agent_L1_Ingest`  
**Key files:** `etl/l2_clean.py`, `etl/l2_audit.py`, `etl/mappers.py`  
**Responsibilities / Steps:**
- RENAME/TYPE CASTS/FILTERS; normalizacja aliasów; deduplikacja.
- AUDYT L2 do JSONL (`step`, `details`, `counts`).  
**Inputs / Outputs / Contracts:**  
- **Inputs:** artefakt L1  
- **Outputs:** L2 `.parquet` + `manifest.json` + `*_audit.jsonl`  
- **Contracts:** `contracts:L2`; brak INF  
**QA Gates:**  
- Kontrakt L2 PASS; audyt zapisany.

---

### Agent_L3_TeamWeek
**Owns tasks:** `T12_l3_aggregate` — ETL L3 TeamWeek  
**Milestone:** `M2`  
**Depends on:** `Agent_L2_Clean_Audit`  
**Key files:** `etl/l3_aggregate.py`, `tests/test_l3_counts.py`  
**Responsibilities / Steps:**
- Agregacje per `TEAM/week` (drives, plays, epa, success, tempo, ST).
- Zapis: `data/l3_team_week/{season}/{week}.parquet` + manifest.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** artefakt L2  
- **Outputs:** L3 TeamWeek `.parquet` + `manifest.json`  
- **Contracts:** `contracts:L3`; brak NaN w kluczach  
**QA Gates:**  
- Testy agregacji PASS.

---

### Agent_E2E
**Owns tasks:** `T13_e2e_smoke` — Smoke end-to-end + raport  
**Milestone:** `M2`  
**Depends on:** `Agent_L3_TeamWeek`, `Agent_Reports`  
**Key files:** `tests/test_e2e_build_week.py`  
**Responsibilities / Steps:**
- Uruchom `build-week` od L1 do raportu; asercje artefaktów.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** środowisko M1–M2 gotowe  
- **Outputs:** zielony przebieg E2E na tygodniu testowym  
- **Contracts:** tworzy się raport, manifests, brak wyjątków  
**QA Gates:**  
- E2E PASS (zalecenie: czas przebiegu na próbkach < 60 s).

---

### Agent_Metrics_Core12
**Owns tasks:** `T20_metrics_core12` — Core12 (preview)  
**Milestone:** `M3`  
**Depends on:** `Agent_L3_TeamWeek`  
**Key files:** `metrics/core12.py`, `tests/test_metrics_core12.py`  
**Responsibilities / Steps:**
- Liczenie kolumn Core12 na bazie L3; zapis do `l4_core12`.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** L3 TeamWeek  
- **Outputs:** `data/l4_core12/{season}/{week}.parquet` + manifest  
- **Contracts:** zgodność minimalnych kolumn wej./wyj. (testy)  
**QA Gates:**  
- Test `test_metrics_core12.py` PASS.

---

### Agent_PowerScore
**Owns tasks:** `T21_powerscore` — Wagi z configu  
**Milestone:** `M3`  
**Depends on:** `Agent_Metrics_Core12`  
**Key files:** `metrics/power_score.py`  
**Responsibilities / Steps:**
- Łączna kolumna `PowerScore` z wag (EPA/SR itp.) z `settings.yaml`.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** `l4_core12`  
- **Outputs:** `data/l4_powerscore/{season}/{week}.parquet` + manifest  
- **Contracts:** kolumny pośrednie + finalny `PowerScore`  
**QA Gates:**  
- Plik `.parquet` + `manifest.json` zapisane; brak NaN w kluczach.

---

### Agent_HiddenTrends
**Owns tasks:** `T22_hidden_trends_stub` — Szkielet API  
**Milestone:** `M3`  
**Depends on:** `Agent_L3_TeamWeek`, `Agent_Metrics_Core12`  
**Key files:** `metrics/hidden_trends.py`, `tests/test_hidden_trends_smoke.py`  
**Responsibilities / Steps:**
- Tymczasowy interfejs: (in: L3/L4; out: DataFrame); na razie stub.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** L3 TeamWeek, L4 Core12  
- **Outputs:** DataFrame (stub)  
- **Contracts:** import działa, smoke test PASS  
**QA Gates:**  
- `test_hidden_trends_smoke.py` PASS.

---

### Agent_API
**Owns tasks:** `T23_api_min` — FastAPI minimal  
**Milestone:** `M3`  
**Depends on:** `Agent_Metrics_Core12`, `Agent_PowerScore`  
**Key files:** `app/api.py`, `tests/test_api_health.py`  
**Responsibilities / Steps:**
- Uruchomienie aplikacji: `uvicorn app.api:app`.
- Endpointy (MVP):
  - `GET /health` → `{"status":"ok"}`
  - `GET /metrics/core12/preview?season=&week=&n=20` → 20 wierszy Core12 (domyślnie 20)  
**Inputs / Outputs / Contracts:**  
- **Inputs:** dane L3/L4 z dysku  
- **Outputs:** JSON preview metryk  
- **Contracts:** stabilny kontrakt odpowiedzi (status 200 + kształt)  
**QA Gates:**  
- `GET /health` PASS; serwer startuje lokalnie.

---

### Agent_Report_Snapshot
**Owns tasks:** `T24_report_metrics_snapshot` — Raport: snapshot metryk  
**Milestone:** `M3`  
**Depends on:** `Agent_Metrics_Core12`, `Agent_PowerScore`  
**Key files:** `app/reports.py`, `templates/report_week.md.j2`  
**Responsibilities / Steps:**
- Dodać do raportu: TOP-N PowerScore i dostępne kolumny Core12 (warunkowo).  
**Inputs / Outputs / Contracts:**  
- **Inputs:** `l4_core12`, `l4_powerscore`  
- **Outputs:** sekcja snapshot w raporcie  
- **Contracts:** zgodność tabelaryczna, brak wyjątków  
**QA Gates:**  
- Raport zawiera PowerScore + wdrożone Core12.

---

### Agent_Migrations_And_QA
**Owns tasks:** `T30_keep_rewrite_scan`, `T31_migrate_best`, `T32_ci_local`, `T33_docs_readme`  
**Milestone:** `M4`  
**Depends on:** cała ścieżka M1–M3  
**Key files:** `Makefile`, `scripts/precommit_check.ps1`, `README.md`  
**Responsibilities / Steps:**
- **T30**: skan legacy, decyzje KEEP/REWRITE/PORT; eliminacja hardcodów.
- **T31**: migracja wybranych utili → `utils/` (typy, docstringi, testy).
- **T32**: lokalny quality gate (`make check` / PS1).
- **T33**: README + quickstart + diagram L1→L4.  
**Inputs / Outputs / Contracts:**  
- **Inputs:** repo + wyniki M1–M3  
- **Outputs:** lista decyzji, zmodernizowane utils, QA skrypty, README  
- **Contracts:** coverage utili ≥80% (lokalnie), `pytest/ruff/black` czysto  
**QA Gates:**  
- `python -m pytest -q` PASS, `python -m ruff check .` 0 errors.

---

## Scaffolds & Tooling Hook
- Jednorazowe wygenerowanie plików scaffoldów z `codex_tasks.yaml`:
  - `python scripts/init_scaffolds.py`  
- Kluczowe pliki scaffoldów:
  - `config/settings.yaml`, `config/contracts.yaml`
  - `utils/{config.py,paths.py,logging.py,contracts.py,guards.py,manifest.py}`
  - `metrics/{core12.py,power_score.py,hidden_trends.py}`
  - `templates/report_week.md.j2`
  - `tests/*`, `requirements.txt`, `.ruff.toml`, `pyproject.toml`, `Makefile`, `scripts/precommit_check.ps1`

## Telemetry / Logging Checklist
- [ ] W każdym module: `from utils.logging import get_logger` → `logger = get_logger(__name__)`
- [ ] ŻADNYCH `print` w libach (dopuszczalne w CLI/tests)
- [ ] `warnings` przechwytywane do logów

## API Contracts (MVP)
- `GET /health` → `{"status":"ok"}`  
- `GET /metrics/core12/preview?season=&week=&n=20` → JSON z max `n` wierszami (domyślnie 20)  
- Statusy 200/4xx/5xx zgodne ze standardem; odpowiedzi z polami zgodnymi z L4 Core12.

---

## Notes
- Każda warstwa **pisze** `.parquet + manifest.json (sha256, rows, cols, created_at)`.
- Raport tygodniowy (`report_path`) zawsze ląduje w `data/reports/`.
- Audyt L2 zapisuj do `l2_audit_path(season, week)`.

