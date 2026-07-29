# Variant B Week Flow Summary

Total audits: 5

| Pick | Tag | Process | Gate | Operator Action | Hard Blockers | Audit |
| --- | --- | --- | --- | --- | ---: | --- |
| BUF_at_HOU BUF VALUE PLAY | VALUE PLAY | PREKICK_NOT_READY | HOLD | RETURN_FOR_MODEL_RERUN | 5 | research\variant_b_week_flow\2026\week_01\2026_w01_BUF_at_HOU_BUF.json |
| NO_at_DET DET GOW | GOW | PREKICK_NOT_READY | HOLD | RETURN_FOR_MODEL_RERUN | 5 | research\variant_b_week_flow\2026\week_01\2026_w01_NO_at_DET_DET.json |
| CLE_at_JAX JAX GOY | GOY | PREKICK_NOT_READY | HOLD | RETURN_FOR_MODEL_RERUN | 5 | research\variant_b_week_flow\2026\week_01\2026_w01_CLE_at_JAX_JAX.json |
| GB_at_MIN GB GOW | GOW | PREKICK_NOT_READY | HOLD | RETURN_FOR_MODEL_RERUN | 5 | research\variant_b_week_flow\2026\week_01\2026_w01_GB_at_MIN_GB.json |
| MIA_at_LV MIA GOM | GOM | PREKICK_NOT_READY | HOLD | RETURN_FOR_MODEL_RERUN | 5 | research\variant_b_week_flow\2026\week_01\2026_w01_MIA_at_LV_MIA.json |

## Action Picks

```yaml
pick: BUF_at_HOU BUF VALUE PLAY
selected_team: BUF
tag: VALUE PLAY
edge_vs_line: 4.88
line: -1.5
price: -102
process_quality: PREKICK_NOT_READY
gate_state: HOLD
operator_action: RETURN_FOR_MODEL_RERUN
hard_blockers_count: 5
```

```yaml
pick: NO_at_DET DET GOW
selected_team: DET
tag: GOW
edge_vs_line: 4.17
line: -7.0
price: -109
process_quality: PREKICK_NOT_READY
gate_state: HOLD
operator_action: RETURN_FOR_MODEL_RERUN
hard_blockers_count: 5
```

```yaml
pick: CLE_at_JAX JAX GOY
selected_team: JAX
tag: GOY
edge_vs_line: 12.42
line: -7.5
price: -102
process_quality: PREKICK_NOT_READY
gate_state: HOLD
operator_action: RETURN_FOR_MODEL_RERUN
hard_blockers_count: 5
```

```yaml
pick: GB_at_MIN GB GOW
selected_team: GB
tag: GOW
edge_vs_line: 7.7
line: 1.0
price: -105
process_quality: PREKICK_NOT_READY
gate_state: HOLD
operator_action: RETURN_FOR_MODEL_RERUN
hard_blockers_count: 5
```

```yaml
pick: MIA_at_LV MIA GOM
selected_team: MIA
tag: GOM
edge_vs_line: 12.71
line: 3.5
price: 102
process_quality: PREKICK_NOT_READY
gate_state: HOLD
operator_action: RETURN_FOR_MODEL_RERUN
hard_blockers_count: 5
```


## Next

- Model proof MVP zostal wygenerowany: p_cover, p_push, p_loss i acceptable frontier sa w pliku model_proof.
- Nadal trzeba uzupelnic model-generation quote, bo nie wolno go rekonstruowac po fakcie.
- Market quote file zostal wczytany; sprawdz, czy executable status i timestamp przechodza gate.
- Ponownie uruchomic ten sam flow po uzupelnieniu danych.
