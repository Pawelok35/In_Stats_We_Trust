# Variant B Structured 19-Point Evidence Prompt

Prompt version: `variant_b_structured_19_point_evidence.v1`  
Schema version: `variant_b_gpt_evidence.v1`

Return exactly one JSON object. Do not use Markdown fences and do not include text before or after JSON.

This JSON is research input. It is not an operator decision or an instruction to place a bet. Do not provide a final pick, stake, approved pick, operator decision, or place-bet instruction. Do not guess: use `UNKNOWN`, `NO_DATA`, `PENDING`, or `NOT_DUE` with `no_data_reason` when evidence is unavailable.

Candidate input: `{{CANDIDATE_JSON}}`  
Market input: `{{MARKET_JSON}}`

Return all official points, in this exact order:
1 `argument_against`, 2 `market_move_notes`, 3 `injury_role_notes`, 4 `schedule_spot_notes`, 5 `weather_notes`, 6 `key_number_check`, 7 `no_chase_limit`, 8 `price_quality`, 9 `market_snapshot`, 10 `public_bias / tickets_handle`, 11 `power_rankings_check`, 12 `roster_change_check`, 13 `matchup_specific_risk`, 14 `game_script_risk`, 15 `closing_line`, 16 `closing_price`, 17 `clv_points`, 18 `process_quality`, 19 `final_operator_decision`.

For every point include `point_id`, exact `point_name`, `status`, `gpt_assessment`, `blocking_assessment`, `summary`, `evidence_items`, `structured_data`, `data_complete`, and `no_data_reason` where required. Every source needs an ID, reference, factual summary, reliability, and UTC capture timestamp. Use probabilities in 0-1 form, summing to exactly 1. Frontier and no-chase limits must be numeric American odds/spread values. Key numbers must be explicitly listed.

The JSON must use `schema_version`, `prompt_version`, all metadata fields, 19 point results, `probability_assessment`, `acceptable_quote_frontier`, `no_chase`, `key_number_policy`, reported risks/warnings, summary, and source count. `evidence_id` is `variant-b-gpt-evidence:` plus the canonical content digest.
