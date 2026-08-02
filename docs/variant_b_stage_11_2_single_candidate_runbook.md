# Variant B Stage 11.2 Single-Candidate Operator Runbook

## 1. Purpose

Build one canonical structured Variant B audit artifact from one authoritative `CandidateRecord`, one `VariantBGptEvidenceSidecar`, one explicit rules file, one explicit UTC build timestamp, and one explicit output path. The tool does not select a candidate, generate evidence, run GPT, fetch data, find files, repair fields, or make a final operator decision.

## 2. Scope

Single candidate only. Single evidence sidecar only. Manual invocation only. Explicit paths only. Persistence occurs only after a successful build and output is immutable. Batch/week processing, GUI, daily-bot integration, automatic discovery, evidence generation, candidate migration, and fallback reconstruction are out of scope.

## 3. Safety Invariants

- `CandidateRecord` is authoritative for matchup and model-pick fields.
- GPT evidence cannot overwrite candidate identity or market provenance.
- All inputs and the build timestamp are explicit.
- `home` and `away` come from `CandidateRecord`.
- `game_id` is never parsed to repair missing fields.
- `BLOCKED_PRECONDITION` creates no artifact.
- A different existing artifact is never overwritten.
- An identical artifact is accepted idempotently.
- Missing required fields remain fail-closed.

## 4. Required Inputs

`--candidate` is one JSON file containing a valid `CandidateRecord`.

`--evidence` is one JSON file containing a valid `VariantBGptEvidenceSidecar`.

`--rules` is one explicit YAML rules mapping. It must contain exactly one explicit audit stage for this run. Use `config/variant_b_rules_prekick.yaml` for this single-candidate PREKICK workflow. `config/variant_b_rules.yaml` is the existing multi-stage configuration and is not accepted by this entry point.

`--build-timestamp` is an explicit UTC ISO-8601 timestamp, for example `2026-09-08T18:30:00Z`.

`--output` is the explicit target JSON path. Its parent directory must already exist.

## 5. Input Preparation

Use a candidate produced by the model adapter with authoritative `away`, `home`, model fields, and `source_metadata.model_pick`. Confirm that its provenance includes `market_scope`, `model_generation_quote_id`, book, and quote timestamp. Prepare a structurally valid 19-point evidence sidecar. Do not derive or fill any missing values from GPT, the filename, a schedule, or `game_id`.

## 6. Pre-Run Checklist

- Confirm the candidate and evidence paths point to one intended matchup.
- Confirm `CandidateRecord.home != CandidateRecord.away`.
- Confirm candidate/evidence IDs, game, season, week, selected team, and model variant match.
- Confirm the rules file has one intended `audit_stages` value.
- Confirm the timestamp is UTC and the output parent exists.
- Confirm the output path is new, or intentionally refers to the exact same prior run.

## 7. Command

```powershell
python scripts/build_structured_variant_b_audit.py `
  --candidate path/to/candidate.json `
  --evidence path/to/variant_b_evidence.json `
  --rules config/variant_b_rules_prekick.yaml `
  --build-timestamp 2026-09-08T18:30:00Z `
  --output path/to/canonical_variant_b_audit.json
```

The command prints one stable JSON result to stdout.

## 8. Result Statuses

- `WRITTEN`: a new canonical artifact was atomically written.
- `ALREADY_EXISTS_IDENTICAL`: the target already contained identical canonical bytes.
- `BLOCKED`: pure-core preconditions failed; no artifact was written.
- `INVALID_INPUT`: a path, contract, rules mapping, or timestamp was invalid.
- `COLLISION`: the target contains different bytes and was preserved.
- `IO_ERROR`: loading or atomic persistence failed.

## 9. Exit Codes

| Exit code | Meaning |
| --- | --- |
| `0` | `WRITTEN` or `ALREADY_EXISTS_IDENTICAL` |
| `2` | `BLOCKED` |
| `3` | `INVALID_INPUT` |
| `4` | `COLLISION` |
| `5` | `IO_ERROR` |

## 10. Successful Build Verification

For `WRITTEN`, confirm `written` is `true`, the output exists, and stdout includes the expected `build_id`, `canonical_digest`, `candidate_id`, and `game_id`. The artifact is canonical JSON produced by the existing integration core.

## 11. Idempotent Rerun

Run the identical command again only when all five inputs are unchanged. `ALREADY_EXISTS_IDENTICAL` with `written:false` and exit `0` is the expected safe result. Do not manually rewrite the artifact.

## 12. Blocked Precondition Handling

For `BLOCKED`, inspect `blocking_reasons`. Correct the authoritative upstream input outside this command, then rerun with explicit corrected inputs. Do not create a placeholder artifact or retry with synthesized values.

## 13. Invalid Input Handling

For `INVALID_INPUT`, correct the reported path, JSON/YAML contract, rules mapping, or timestamp. Naive/local timestamps such as `2026-09-08T18:30:00` are invalid.

## 14. Immutable Artifact Collision Handling

For `COLLISION`, preserve the existing file. Compare the explicit inputs and select a different explicit output path only when it represents a different legitimate build. Never overwrite or use a force option.

## 15. I/O Failure Handling

For `IO_ERROR`, verify read permissions, output-parent existence, write permissions, and available storage. The atomic writer removes its temporary file after a controlled write failure; do not manually replace an existing artifact.

## 16. Historical Candidate Limitations

`model_generation_quote_id` is required in `source_metadata.model_pick` as a non-empty authoritative string. Historical candidate records without it are intentionally incompatible with Stage 11.2 until an authoritative migration exists. The command does not infer a market scope, synthesize a quote ID, or repair provenance.

## 17. Do Not Do

Do not use current time as a substitute for `--build-timestamp`. Do not glob for candidates/evidence, choose the newest file, use a schedule fallback, parse `game_id`, alter the evidence to match the candidate, or modify an existing different artifact.

## 18. End-to-End Operator Checklist

1. Prepare one candidate and one validated evidence sidecar.
2. Prepare a one-stage rules YAML file.
3. Choose an explicit UTC timestamp and output path.
4. Run the command.
5. Read stdout JSON and exit code.
6. Verify a successful artifact or resolve the reported fail-closed condition upstream.

## 19. Troubleshooting Matrix

| Symptom | Action |
| --- | --- |
| Exit `2`, `BLOCKED` | Read `blocking_reasons`; correct upstream authoritative inputs. |
| Exit `3`, `INVALID_INPUT` | Fix path, JSON/YAML validation, stage mapping, or UTC timestamp. |
| Exit `4`, `COLLISION` | Preserve existing output; compare inputs and use a legitimate distinct path if needed. |
| Exit `5`, `IO_ERROR` | Fix filesystem permissions or output-parent availability. |
| Missing `market_scope` or quote ID | Do not synthesize it; obtain a complete model record. |

## 20. Audit Trail

Retain the explicit command inputs, stdout JSON, exit code, and the immutable canonical artifact. The artifact digest and build ID identify the exact successful build; a blocked run has no canonical artifact.
