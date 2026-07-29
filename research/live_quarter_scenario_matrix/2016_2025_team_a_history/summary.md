# NFL Quarter Scenario Matrix

Generated at UTC: `2026-07-28T20:32:23.557978+00:00`
Seasons: `2016-2025`
Sample mode: `TEAM_A_HISTORY`
Team-game rows: `14`

## Files

- `research\live_quarter_scenario_matrix\2016_2025_team_a_history\team_game_quarter_rows.csv`
- `research\live_quarter_scenario_matrix\2016_2025_team_a_history\full_quarter_path_matrix.csv`
- `research\live_quarter_scenario_matrix\2016_2025_team_a_history\quarter_transition_matrix.csv`
- `research\live_quarter_scenario_matrix\2016_2025_team_a_history\margin_bucket_matrix.csv`
- `research\live_quarter_scenario_matrix\2016_2025_team_a_history\segment_transition_matrix.csv`
- `research\live_quarter_scenario_matrix\2016_2025_team_a_history\scenario_lookup.json`

## Notes

- Quarter Reset View liczy wynik pojedynczej kwarty od 0:0.
- Cumulative Game View liczy skumulowany wynik meczu po danej kwarcie.
- Dogrywka nie jest doliczana do Q4; final_including_overtime jest osobnym polem.
- Skrypt nie pobiera live kursow. Kurs live wpisujesz recznie przez parametry lookup.
- Male sample size oznacza wyzsza niepewnosc, nie automatyczny blad.
