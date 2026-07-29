# L4 and Pick Contracts

Point 5 extends schema contracts beyond L1-L3.

## Added Contracts

`config/contracts.yaml` now includes:

- `L4_CORE12`
- `L4_POWERSCORE`
- `PICK_OUTPUT`

## Enforcement

`metrics/core12.py` validates `L4_CORE12` before writing the Core12 parquet.

`metrics/power_score.py` validates `L4_POWERSCORE` before writing the PowerScore parquet.

`metrics/backtest.py` validates loaded pick JSONL records against `PICK_OUTPUT` before evaluating results.

## Minimum Pick Fields

- `season`
- `week`
- `home`
- `away`
- `tag`
- `model_winner`
- `confidence`
- `handicap`

The wider target contract from the improvement plan still includes fields such as `market`, `edge`, `model_version`, and `created_at`. Those should be added after the pick generator is upgraded to emit them consistently.

