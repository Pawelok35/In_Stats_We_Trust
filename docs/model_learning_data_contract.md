# Model Learning Data Contract

## Cel

Ten dokument definiuje wspolny kontrakt danych dla modelu uczacego sie, Variant B, ledgeru i pozniejszego backtestu as-of.

Najwazniejsza zasada:

```text
model, audyt i post-event review musza liczyc margin, spread, quote i timestampy tak samo
```

## Selected Team

`selected_team` to druzyna oceniana przez model albo audyt.

Przyklad:

```text
SF at LA
selected_team = LA
```

Wszystkie pola marginu, spreadu, p_cover i wyniku zakladu sa liczone z perspektywy `selected_team`.

## Margin

Definicja:

```text
selected_team_margin = selected_team_score - opponent_score
```

Przyklad:

```text
LA 27 - SF 20
selected_team = LA
selected_team_margin = +7
```

```text
LA 20 - SF 27
selected_team = LA
selected_team_margin = -7
```

## Spread

`selected_team_spread` to spread przypisany do `selected_team`.

Przyklady:

```text
LA -3.0 = selected_team_spread = -3.0
LA +3.0 = selected_team_spread = +3.0
```

Settlement ATS:

```text
ats_margin = selected_team_margin + selected_team_spread
```

Wynik:

```text
ats_margin > 0 = COVER
ats_margin = 0 = PUSH
ats_margin < 0 = LOSS
```

## Model Margin vs Fair Spread

Trzymamy osobno:

```text
predicted_margin_selected_team
fair_spread_selected_team
market_spread_selected_team
```

Znaczenie:

```text
predicted_margin_selected_team = oczekiwany wynik punktowy selected_team minus opponent
fair_spread_selected_team = spread fair z perspektywy selected_team
market_spread_selected_team = realna linia rynku dla selected_team
```

Przyklad:

```text
predicted_margin_selected_team = +4.99
fair_spread_selected_team = -4.99
market_spread_selected_team = -3.0
```

Nie wolno tych pol mieszac, bo odwraca to znaki edge, CLV i cover probability.

## Probability Output

Kazdy model run docelowo powinien miec:

```text
p_cover
p_push
p_loss
margin_pmf
```

Definicja:

```text
p_cover = P(selected_team_margin + selected_team_spread > 0)
p_push  = P(selected_team_margin + selected_team_spread = 0)
p_loss  = P(selected_team_margin + selected_team_spread < 0)
```

`p_cover + p_push + p_loss` musi sumowac sie do 1.0, z tolerancja techniczna.

## Timestampy

Uzywamy tych timestampow:

```text
captured_at_utc
published_at_utc
available_to_model_at_utc
generated_at_utc
kickoff_utc
ledger_recorded_at_utc
```

Znaczenie:

```text
captured_at_utc = kiedy nasz system zapisal dane
published_at_utc = kiedy zrodlo opublikowalo informacje
available_to_model_at_utc = od kiedy model mogl legalnie uzyc informacji
generated_at_utc = kiedy powstal model run / audit
kickoff_utc = start meczu
ledger_recorded_at_utc = kiedy rekord trafil do append-only ledgeru
```

Pregame model nie moze uzywac informacji, ktore maja:

```text
available_to_model_at_utc > generated_at_utc
```

## Availability Status

Braki danych nie sa zerami.

Dozwolone statusy:

```text
AVAILABLE
MISSING
UNKNOWN
NOT_ASSESSABLE
PENDING_NOT_DUE
POST_EVENT_ONLY
```

Przyklady:

```yaml
days_in_melbourne:
  value: null
  status: MISSING
```

To nie jest to samo co:

```yaml
days_in_melbourne:
  value: 0
  status: AVAILABLE
```

## Append-Only Ledger Tables

Minimalne tabele:

```text
games.jsonl
feature_snapshots.jsonl
market_quotes.jsonl
model_runs.jsonl
model_predictions.jsonl
audit_results.jsonl
process_failures.jsonl
outcomes.jsonl
closing_snapshots.jsonl
```

MVP tworzy pierwsze szesc tabel pregame:

```text
games
feature_snapshots
market_quotes
model_runs
model_predictions
audit_results
process_failures
```

`outcomes` i `closing_snapshots` sa post-event.

## ID Fields

Kazdy rekord powinien miec stabilne ID:

```text
game_id
feature_snapshot_id
market_quote_id
model_run_id
model_prediction_id
audit_id
process_failure_id
outcome_id
closing_snapshot_id
```

MVP generuje ID jako hash deterministycznych pol rekordu.

## Pregame vs Post-Event

Pregame:

```text
schedule
pregame model features
model-generation quote
current quote
injury research dostepny przed cutoffem
weather forecast przed cutoffem
Variant B points 1-14, 18-19
```

Post-event:

```text
final score
actual margin
settlement
closing line
closing price
CLV
snap counts
official participation
Variant B points 15-17
```

## Leakage Rules

Pregame model nie moze uzywac:

```text
final score
closing line po czasie predykcji
final inactives, jesli nie byly jeszcze opublikowane
snap counts
post-game injuries
final weather observation
operator decision po meczu
CLV
```

## Current MVP Status

Wdrozone:

```text
basic pick fields
p_cover / p_push / p_loss MVP
acceptable quote frontier
Variant B audit output
append-only learning ledger MVP
```

Jeszcze do rozszerzenia:

```text
pelny margin_pmf
feature snapshots z rzeczywistymi feature values
post-event outcomes
closing snapshots
walk-forward backtest as-of
champion/challenger registry
```

