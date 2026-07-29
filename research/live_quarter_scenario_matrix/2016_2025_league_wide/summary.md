# NFL Quarter Scenario Matrix

Generated at UTC: `2026-07-28T20:34:06.449631+00:00`
Seasons: `2016-2025`
Sample mode: `LEAGUE_WIDE`
Team-game rows: `47`

## Files

- `research\live_quarter_scenario_matrix\2016_2025_league_wide\team_game_quarter_rows.csv`
- `research\live_quarter_scenario_matrix\2016_2025_league_wide\full_quarter_path_matrix.csv`
- `research\live_quarter_scenario_matrix\2016_2025_league_wide\quarter_transition_matrix.csv`
- `research\live_quarter_scenario_matrix\2016_2025_league_wide\margin_bucket_matrix.csv`
- `research\live_quarter_scenario_matrix\2016_2025_league_wide\segment_transition_matrix.csv`
- `research\live_quarter_scenario_matrix\2016_2025_league_wide\scenario_lookup.json`

## Notes

- Quarter Reset View liczy wynik pojedynczej kwarty od 0:0.
- Cumulative Game View liczy skumulowany wynik meczu po danej kwarcie.
- Dogrywka nie jest doliczana do Q4; final_including_overtime jest osobnym polem.
- Skrypt nie pobiera live kursow. Kurs live wpisujesz recznie przez parametry lookup.
- Male sample size oznacza wyzsza niepewnosc, nie automatyczny blad.
