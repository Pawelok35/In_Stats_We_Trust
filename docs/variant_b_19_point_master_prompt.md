# Variant B - master prompt dla 19 punktow audytu

Aktualny finalny prompt do wklejania GPT jest tutaj:

```text
docs/variant_b_final_gpt_research_prompt.md
```

Ten plik ponizej zostaje jako starszy roboczy prompt z etapu budowy frameworka.

Uzycie:

```text
Wklej ten prompt do GPT Pro / Deep Research dla konkretnego meczu.
Podmien tylko sekcje "Specific test game" oraz, jesli juz masz, wyniki punktow 1-3.
```

Mapa zrodel dla wszystkich punktow jest tutaj:

```text
docs/variant_b_sources_by_point.md
```

## Prompt

```text
We are building an NFL betting model audit process called Variant B.

The model already produces candidate NFL spread picks with:
- season
- week
- game date
- teams
- market
- current spread
- price
- model fair line
- edge_vs_line
- confidence tier: VALUE PLAY, GOW, GOM, GOY

I do not want picks.
I do not want a betting recommendation.
I do not want a prediction.

I want to define a full audit framework for 19 process fields.

Specific test game:
- Season: 2026
- Week: 1
- Game date USA: 2026-09-10
- Local game date Australia: 2026-09-11
- Matchup: San Francisco 49ers at Los Angeles Rams
- Venue: Melbourne Cricket Ground, Melbourne, Australia
- Location type: neutral-site international game
- Market: spread
- Current line: Los Angeles Rams -3.0
- Price: -110
- Model pick: Los Angeles Rams -3.0
- Model tag: VALUE PLAY
- Model fair margin raw: Los Angeles Rams -4.99
- Model fair margin rounded to nearest 0.5: Los Angeles Rams -5.0
- Edge vs line raw: +1.99 points
- Edge vs line rounded to nearest 0.5: +2.0 points

Already completed:

POINT 1: argument_against
"LA -3 looks like a VALUE PLAY, but the +1.99-point edge is currently only the difference between fair margin and market line, not full EV. At -3 we need p_cover, p_push, and p_loss because a Rams win by exactly 3 is a push. This is also a Week 1 neutral-site international game in Australia, so we must check for home-field leakage and whether model uncertainty erases the edge. The market snapshot is incomplete because book, timestamp, and executable -3/-110 confirmation are missing."

POINT 2: market_move_notes
"Opener data is unavailable. The stored current quote is Los Angeles Rams -3 at -110 from MANUAL_CONSENSUS, which places the spread on key number 3, but sportsbook, capture timestamp, and executable status are not market-grade. Opener-to-current movement, price movement, and whether the market touched or crossed 3 or 7 cannot be determined. The exact quote available at model generation is also not independently timestamped, so no-chase status is NOT_ASSESSABLE."

POINT 3: injury_role_notes
"Official Week 1 injury reports are not yet available. This is PRE_REPORT_WINDOW, so injury status is PENDING, not cleared. No official DNP/LP/FP/OUT/DOUBTFUL/QUESTIONABLE entries are available for this matchup, so QB, OL, secondary, pass rush, skill-position role impact, replacement quality, chain reactions, and injury effect on the +1.99 raw edge are NOT_ASSESSABLE. Do not infer that either team is healthy."

Now define the full framework for all 19 points:

1. argument_against
2. market_move_notes
3. injury_role_notes
4. schedule_spot_notes
5. weather_notes
6. key_number_check
7. no_chase_limit
8. price_quality
9. market_snapshot
10. public_bias / tickets_handle
11. power_rankings_check
12. roster_change_check
13. matchup_specific_risk
14. game_script_risk
15. closing_line
16. closing_price
17. clv_points
18. process_quality
19. final_operator_decision

For EACH point, answer in this exact structure:

point_number:
point_name:
purpose:
can_be_automated: FULL / SEMI / MANUAL / HYBRID
required_data:
approved_sources:
automatic_rules:
  - rule_id:
    risk_level: LOW / MEDIUM / HIGH
    condition:
    explanation:
    auto_possible:
manual_checks:
output_format:
test_game_output:
implementation_priority: HIGH / MEDIUM / LOW

Important rules:
- Do not give a betting recommendation.
- Do not say whether to bet Rams or 49ers.
- Do not invent injuries, weather, market movement, public betting data, or roster facts.
- If data is not available, mark it as MISSING, PENDING, UNKNOWN, or NOT_ASSESSABLE.
- Do not call market movement "sharp" unless supported by evidence.
- Do not claim travel favors one team unless itinerary/acclimation data exists.
- Separate confirmed facts from conditional risks and missing data.
- Keep each point concise but complete.
- The output should be usable to create YAML rules and Python validation code.
- Use deterministic rules wherever possible; a language model may summarize but should not calculate.
- Store raw model values for calculation and nearest-0.5 rounded values only for display.
- Missing future game-week data should be PENDING_NOT_DUE, not treated as a failed check.
- Missing due data should be MISSING_DUE or NOT_ASSESSABLE, depending on whether the field can be evaluated.

At the end, provide:

summary:
  top_10_rules_to_implement_first:
  fields_that_can_be_fully_automated_now:
  fields_that_require_manual_input:
  fields_that_should_remain_pending_until_game_week:
  recommended_yaml_schema:
```

## Najwazniejsza interpretacja wyniku

Po otrzymaniu odpowiedzi z GPT Pro nie kopiujemy jej 1:1 do systemu. Najpierw dzielimy wynik na:

```yaml
implementation_groups:
  implement_now:
    - argument_against
    - market_move_notes
    - key_number_check
    - no_chase_limit
    - price_quality
    - market_snapshot
    - process_quality
    - final_operator_decision
  pending_game_week:
    - injury_role_notes
    - schedule_spot_notes
    - weather_notes
    - public_bias / tickets_handle
    - roster_change_check
    - matchup_specific_risk
    - game_script_risk
  pending_post_close:
    - closing_line
    - closing_price
    - clv_points
```

## Zasada operacyjna

```text
Python/rule engine liczy.
LLM moze tylko streszczac wynik.
```

## Lokalny MVP rule engine

Po wdrozeniu szkieletu Variant B lokalny audyt dla picka uruchamiamy tak:

```powershell
python scripts/variant_b_audit.py `
  --picks-file data/picks_variant_m/2026/week_01.jsonl `
  --home LA `
  --away SF `
  --output research/variant_b_audit_2026_w01_sf_at_la.json
```

Pierwszy MVP obejmuje punkty:

```text
1. argument_against
2. market_move_notes
6. key_number_check
7. no_chase_limit
8. price_quality
9. market_snapshot
18. process_quality
19. final_operator_decision
```

Obecny oczekiwany wynik dla `SF at LA` na etapie `EARLY_PREVIEW`:

```yaml
process_quality: INCOMPLETE
operator_decision: HOLD_PENDING_DATA
substatus: RETURN_FOR_MARKET_SNAPSHOT_AND_MODEL_INPUT_COMPLETION
```

To nie jest rekomendacja zakladu. To znaczy tylko:

```text
system nie ma jeszcze danych wymaganych do pelnego audytu Variant B
```

Najwazniejsze braki:

```text
- market-grade sportsbook / timestamp / executable quote
- model-generation market snapshot
- p_cover / p_push / p_loss
- frozen acceptable_quote_frontier albo price-quality policy
```
