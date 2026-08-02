# Stage 11.2 Acceptance Fixture

Classification: TEST_ONLY
Production eligible: NO
Purpose: Stage 11.2 single-candidate CLI acceptance testing

This fixture is not a production pick.
This fixture is not a real market audit.

Candidate:
`tests/fixtures/stage_11_2/acceptance/candidate.json`

Evidence:
`tests/fixtures/stage_11_2/acceptance/evidence.json`

Rules:
`config/variant_b_rules_prekick.yaml`

Fixed UTC build timestamp:
`2026-09-10T18:00:00Z`

```powershell
python scripts/build_structured_variant_b_audit.py `
  --candidate "tests\fixtures\stage_11_2\acceptance\candidate.json" `
  --evidence "tests\fixtures\stage_11_2\acceptance\evidence.json" `
  --rules "config\variant_b_rules_prekick.yaml" `
  --build-timestamp "2026-09-10T18:00:00Z" `
  --output "<temporary-directory>\stage_11_2_acceptance_audit.json"
```

Do not edit candidate.json manually.
Do not edit evidence.json manually.
Regenerate them only through the committed TEST_ONLY generator.
Do not derive production evidence from these fixtures.
Do not save acceptance output in production artifact directories.
