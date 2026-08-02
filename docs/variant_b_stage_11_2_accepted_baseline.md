# Variant B Stage 11.2 Single-Candidate Accepted Baseline

## 1. Baseline Status

- Status: `ACCEPTED`
- Verdict: `STAGE_11_2_SINGLE_CANDIDATE_ACCEPTED`
- Accepted repository HEAD before baseline documentation: `6433d907`
- Acceptance date: `2026-08-02`
- Fixture timestamp: `2026-09-10T18:00:00Z` is `TEST_ONLY`, not the baseline date.

This is an accepted Variant B Stage 11.2 single-candidate operator/audit workflow layered after candidate generation. It does not automatically generate production picks.

## 2. Accepted Scope

One authoritative `CandidateRecord`, one `VariantBGptEvidenceSidecar`, one explicit single-stage rules profile, one UTC timestamp, and one output path are handled per manual invocation: source model record -> adapter -> candidate -> explicit evidence -> CLI -> orchestrator -> pure core -> immutable canonical audit.

## 3. Excluded Scope

Excluded: batch/week orchestration, scanning/discovery, automatic candidate/evidence selection, GPT generation/matching, Markdown, GUI/bot, schedule/market lookup, migration, and automatic production wiring.

## 4. Implementation Chain

- `pregame/contracts.py`: authoritative candidate and evidence contracts.
- `pregame/model_output_adapter.py`: preserves identity, matchup sides, model fields, and quote provenance in `CandidateRecord`.
- `pregame/variant_b_audit_integration.py`: deterministic in-memory validation and canonical construction.
- `pregame/variant_b_audit_orchestrator.py`: explicit inputs and success-only immutable persistence.
- `scripts/build_structured_variant_b_audit.py`: five arguments, one invocation, stable JSON, documented exit codes.

## 5. Accepted Commits

```text
cf72b623 feat(pregame): add core regression guard and data contracts
013aafa5 feat(pregame): add append-only event store
2ad19650 feat(pregame): add current-state projector
a879dab9 feat(pregame): add persistent JSONL event store
c232394c feat(pregame): add market snapshot history service
d158d643 feat(pregame): add weekly candidate registry
70a9fbb4 test(pregame): verify current matchup output integration
d8259b9d feat(pregame): add final quote gate
54acc30c feat(pregame): add Variant B research adapter
35b0af9f feat(pregame): add Variant B final quote policy adapter
f0543bcb feat(pregame): add structured GPT evidence sidecar
2e0ea73a feat(variant-b): add structured evidence audit API
df106a73 test(variant-b): add legacy audit golden parity
8a65ddc5 feat(variant-b): add deterministic structured audit timestamp
37f66dcf feat: add pure structured Variant B audit integration core
fecb819f feat: add structured Variant B audit persistence orchestrator
74e519bd feat: add single-candidate Variant B audit entry point
129a0eb9 docs: add Variant B stage 11.2 operator runbook
3f43e33b test: add Stage 11.2 acceptance fixture generator
96ec4214 config: add single-stage Variant B PREKICK rules
1d5153d4 fix: require model generation quote provenance
6433d907 test: add canonical Stage 11.2 acceptance fixtures
```

## 6. Authoritative Input Contracts

`CandidateRecord` owns candidate identity, season/week, away/home, selected team, market type/scope, spread/price, book/source, quote timestamp, model tag/variant, edge, model and market margins, confidence, preflight metadata, and `model_generation_quote_id`.

`VariantBGptEvidenceSidecar` owns only structured research/audit evidence: 19 points, their statuses, and observations. It cannot overwrite any candidate identity, matchup, model, or market provenance.

## 7. Rules Profile

Required profile: `config/variant_b_rules_prekick.yaml`, with `audit_stages == ["PREKICK"]`. Multi-stage `config/variant_b_rules.yaml` is invalid for this CLI. `--rules` is mandatory and never auto-selected.

## 8. Canonical Acceptance Fixtures

- `tests/fixtures/stage_11_2/acceptance/candidate.json`
- `tests/fixtures/stage_11_2/acceptance/evidence.json`
- `tests/fixtures/stage_11_2/acceptance/README.md`

```text
candidate.json SHA-256: 821D0F91A6DF9C8AEF02A9FC7E57A4DA4FD8EEDEE992D922E6E625215FFB4E43
evidence.json SHA-256: 19CE1723CCAAE2E51951CC994CE55D444A964C74BFF29FC4357C12E32611336F
```

Fixtures are deterministic `TEST_ONLY` inputs, not production candidates, market evidence, or executable market decisions. Generate only with `tests/tools/generate_stage_11_2_acceptance_fixtures.py`; do not edit manually.

## 9. Manual Acceptance Execution

```powershell
python scripts/build_structured_variant_b_audit.py `
  --candidate tests/fixtures/stage_11_2/acceptance/candidate.json `
  --evidence tests/fixtures/stage_11_2/acceptance/evidence.json `
  --rules config/variant_b_rules_prekick.yaml `
  --build-timestamp 2026-09-10T18:00:00Z `
  --output <external-temporary-output>\stage_11_2_acceptance_audit.json
```

`first run: WRITTEN / written=true / exit 0`.

`second run: ALREADY_EXISTS_IDENTICAL / written=false / exit 0`.

The manual output was written outside the repository. It is a temporary acceptance artifact, not tracked and not a production artifact.

## 10. Artifact Validation

```text
canonical digest: dc684db6ab43591c443b64e45a87a5453f402c29ab853c95579523f415657667
artifact size: 18556 bytes
```

Validation confirmed canonical schema, 19 audit points, candidate ID, canonical game ID, season/week, away/home, selected team, market type, `market_scope`, model variant, spread, price, edge, margins, confidence, model tag, book/source, quote timestamp, preflight metadata, and `model_generation_quote_id`.

## 11. Authority Boundaries

Matchup sides: authoritative model record -> model output adapter -> `CandidateRecord.away/home` -> `source_pick.event.away/home` -> canonical artifact. Accepted identity: `BUF = away`, `HOU = home`. No inference from selected team, spread, game ID, GPT evidence, or schedule.

Quote provenance: authoritative model record -> `source_metadata.model_pick.model_generation_quote_id` -> `source_pick.model_generation_quote_id` -> canonical artifact. Accepted value: `quote-1`. No reconstruction from candidate ID, game ID, timestamp, book/source, evidence, filename, path, hash, UUID, or current time.

## 12. Fail-Closed Guarantees

The accepted workflow fails closed for missing/invalid away/home; equal home/away; missing `market_scope`; missing, null, empty, whitespace, or non-string `model_generation_quote_id`; invalid candidate/evidence contracts; incomplete 19-point evidence; identity, selected-team, or market mismatch; non-acceptable preflight; invalid/non-UTC timestamp; a different immutable artifact collision; invalid rules; and multi-stage rules supplied to this CLI.

## 13. Determinism and Idempotence

Identical inputs produced identical canonical bytes, filesystem SHA-256, artifact size, build ID, and canonical digest. The rerun returned `ALREADY_EXISTS_IDENTICAL` with `written = false`; mtime remained unchanged. No current time, random UUID, or auto-discovered path is used.

## 14. Operator Entry Point

Required arguments: `--candidate`, `--evidence`, `--rules`, `--build-timestamp`, `--output`.

Exit codes: `0` = `WRITTEN` or `ALREADY_EXISTS_IDENTICAL`; `2` = pure-core blocked; `3` = invalid input/rules; `4` = immutable collision; `5` = I/O failure. Blocked, invalid, and collision outcomes are non-zero.

## 15. Known Limitations

- Historical candidates without authoritative `market_scope` fail closed.
- Historical candidates without authoritative `model_generation_quote_id` fail closed.
- No migration is included.
- Evidence remains manually prepared outside this workflow.
- Exactly one candidate is handled per invocation.
- PREKICK retains its existing blocking configuration.
- Fixtures are `TEST_ONLY` and cannot be market evidence.

## 16. Change-Control Policy

Changes to `CandidateRecord`, adapter provenance, away/home or quote-ID authority, sidecar schema, 19-point completeness, PREKICK rules, pure core, `source_pick`, canonical serialization, digest/build-ID calculation, persistence, collision policy, CLI arguments/statuses/exit codes, or fixtures invalidate this baseline until revalidated.

Revalidation requires focused tests, full `pytest`, Champion CORE regression, fixture integrity, first-run and identical-rerun manual acceptance, and a clean worktree. Batch or GUI integration requires separately approved scope.

## 17. Baseline Verification Commands

```bash
pytest -q
git status --short
```

Champion CORE expected: `74 bets`, `61-12-1`, `+128.70u`, `222.00u risk`, `57.97% ROI`, `-6.30u max drawdown`.

```powershell
python tests/tools/generate_stage_11_2_acceptance_fixtures.py `
  --output-dir "tests\fixtures\stage_11_2\acceptance"
```

Use the single-candidate command in section 9 with an external temporary output. Expected `git status --short`: clean working tree.
