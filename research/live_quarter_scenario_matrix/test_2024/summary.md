# NFL Quarter Scenario Matrix

Generated at UTC: `2026-07-25T08:49:11.787479+00:00`
Seasons: `2024-2024`
Sample mode: `LEAGUE_WIDE`
Team-game rows: `544`

## Files

- `research\live_quarter_scenario_matrix\test_2024\team_game_quarter_rows.csv`
- `research\live_quarter_scenario_matrix\test_2024\full_quarter_path_matrix.csv`
- `research\live_quarter_scenario_matrix\test_2024\quarter_transition_matrix.csv`
- `research\live_quarter_scenario_matrix\test_2024\margin_bucket_matrix.csv`
- `research\live_quarter_scenario_matrix\test_2024\segment_transition_matrix.csv`
- `research\live_quarter_scenario_matrix\test_2024\scenario_lookup.json`

## Notes

- Quarter Reset View liczy wynik pojedynczej kwarty od 0:0.
- Cumulative Game View liczy skumulowany wynik meczu po danej kwarcie.
- Dogrywka nie jest doliczana do Q4; final_including_overtime jest osobnym polem.
- Skrypt nie pobiera live kursow. Kurs live wpisujesz recznie przez parametry lookup.
- Male sample size oznacza wyzsza niepewnosc, nie automatyczny blad.
