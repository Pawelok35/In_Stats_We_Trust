# Run Metadata

Point 6 adds reproducibility metadata to generated artifacts.

## Helper

The shared helper lives in `utils/run_metadata.py`.

It records:

- `commit_sha`
- `code_is_dirty`
- `model_version`
- `data_cutoff`
- `config_hashes`
- `config_sha256`

## Manifests

`utils.manifest.write_manifest()` now adds git metadata to every manifest by default.

## Pick Outputs

`scripts/matchup_batch.py` now adds metadata to new pick JSONL records:

- `model_version`: derived from the tag config filename, e.g. `variant_j`
- `commit_sha`
- `code_is_dirty`
- `config_hashes`
- `config_sha256`
- `data_cutoff`
- `source_report`

Older pick files remain readable because these metadata fields are optional in the `PICK_OUTPUT` contract.

## Next Step

Reports can also surface this metadata in their markdown footer/header once the desired display format is settled.

