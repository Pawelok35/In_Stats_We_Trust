# Variant B - etapy wdrozenia modelu uczacego sie

## Cel

Docelowo chcemy system, ktory uczy sie na kolejnych meczach, ale pozostaje audytowalny:

```text
dane -> snapshot as-of -> model probabilistyczny -> Variant B gate -> wynik -> ewaluacja -> trening kandydata -> promocja albo odrzucenie
```

Model moze sie uczyc. Reguly audytu, bramki jakosci, no-chase, quote proof, CLV i finalny router musza zostac deterministyczne.

## Zasada glowna

Nie budujemy jednego "samodzielnie myslacego" modelu.

Budujemy cztery warstwy:

1. Wersjonowane dane i snapshoty.
2. Probabilistyczny model wyniku meczu.
3. Deterministyczny silnik audytu Variant B.
4. Kontrolowana petla trenowania i promocji nowej wersji.

## Etap 1 - kontrakt danych

Cel: ustalic jednoznaczne definicje, zeby model, backtest i audyt liczyly to samo.

Status MVP: WDROZONE.

Kontrakt:

```text
docs/model_learning_data_contract.md
```

Do zrobienia:

- zdefiniowac `selected_team`;
- zdefiniowac margin:

```text
selected_team_margin = selected_team_score - opponent_score
```

- rozdzielic:

```text
predicted_margin_selected_team
fair_spread_selected_team
market_spread_selected_team
```

- ustalic konwencje spreadu:

```text
Rams -3.0 = selected_team_spread = -3.0
Rams +3.0 = selected_team_spread = +3.0
```

- ustalic timestampy:

```text
captured_at_utc
published_at_utc
available_to_model_at_utc
generated_at_utc
kickoff_utc
```

- ustalic statusy dostepnosci danych:

```text
AVAILABLE
MISSING
UNKNOWN
NOT_ASSESSABLE
PENDING_NOT_DUE
POST_EVENT_ONLY
```

Wynik etapu:

```text
spojny slownik pol i definicji dla modelu, quote, researchu i audytu
```

## Etap 2 - append-only ledger

Cel: niczego nie nadpisywac po czasie.

Status MVP: WDROZONE.

Skrypt:

```text
scripts/variant_b_learning_ledger.py
```

Domyslny output:

```text
data/learning_ledger/{season}/week_{week}/
```

Kazda zmiana tworzy nowy rekord. To pozwala odtworzyc, co bylo wiadomo w konkretnym momencie.

Minimalne rekordy:

```text
games
market_quotes
model_runs
model_predictions
feature_snapshots
audit_results
outcomes
closing_snapshots
process_failures
```

Najwazniejsze zasady:

- quote z booka zapisujemy jako osobny snapshot;
- nie nadpisujemy starego quote;
- model run jest zamrozony;
- wynik meczu nie zmienia historycznej predykcji;
- closing line i closing price sa post-event / close-event, nie pregame inputem.

Wynik etapu:

```text
kazdy pick ma model_run_id, quote_id, audit_id i pozniejszy outcome_id
```

## Etap 3 - model proof MVP

Cel: kazdy kandydat VP/GOW/GOM/GOY ma podstawowe probabilistyczne uzasadnienie.

Status MVP: WDROZONE.

Do zrobienia:

- generowac:

```text
p_cover
p_push
p_loss
```

- liczyc je wedlug spreadu wybranej druzyny;
- zapisywac acceptable quote frontier;
- blokowac pick, jesli brakuje probability outputu;
- blokowac pick, jesli quote nie jest market-grade.

Mamy juz pierwsza wersje MVP:

```text
scripts/variant_b_model_proof.py
```

Integracja tygodniowa:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof --write-learning-ledger
```

Wynik etapu:

```text
Variant B nie opiera sie tylko na fair margin, ale ma p_cover / p_push / p_loss
```

## Etap 4 - margin PMF

Cel: model ma przewidywac pelny rozklad marginu, nie tylko jedna liczbe.

Status: CZESCIOWO WDROZONE.

Obecny MVP uzywa historycznych residuali i zapisuje `p_cover`, `p_push`, `p_loss` oraz frontier. Pelny jawny `margin_pmf` jako slownik margin -> probability nadal jest do zrobienia.

Zamiast samego:

```text
fair margin = +4.99
```

model powinien zwracac:

```yaml
margin_pmf:
  -10: 0.008
  -9: 0.009
  0: 0.032
  1: 0.041
  2: 0.051
  3: 0.073
  4: 0.050
  7: 0.061
```

Dzieki temu deterministycznie liczymy:

```text
p_cover = P(M + spread > 0)
p_push  = P(M + spread == 0)
p_loss  = P(M + spread < 0)
```

Wynik etapu:

```text
lepsza obsluga spreadow calkowitych, key numbers 3/7 i push probability
```

## Etap 5 - frozen pregame snapshots

Cel: kazda predykcja ma byc mozliwa do odtworzenia.

Status MVP: CZESCIOWO WDROZONE.

Ledger zapisuje teraz:

```text
feature_snapshot_id
market_quote_id
model_run_id
model_prediction_id
audit_id
```

Na razie `feature_snapshots` zawiera metadata/config/data_cutoff, a nie pelny zestaw feature values.

Przed meczem zapisujemy:

```text
game_id
feature_snapshot_id
market_quote_id
model_run_id
model_version
model_code_hash
training_data_hash
generated_at_utc
prediction_horizon
```

Jesli w piatek pojawia sie nowy injury report, nie edytujemy wtorkowej predykcji.

Tworzymy nowy run:

```text
parent_model_run_id = wtorkowy_run
new_model_run_id = piatkowy_run
```

Wynik etapu:

```text
mozemy porownac wtorkowy model, piatek refresh i finalny pre-kickoff run
```

## Etap 6 - post-event evaluation

Cel: po meczu ocenic nie tylko wynik zakladu, ale jakosc procesu.

Status MVP: WDROZONE.

Skrypt:

```text
scripts/variant_b_post_event_evaluation.py
```

Output:

```text
data/learning_ledger/{season}/week_{week}/outcomes.jsonl
data/learning_ledger/{season}/week_{week}/post_event_evaluations.jsonl
```

Dla meczow bez wyniku zapisuje `PENDING_RESULT`. Po pojawieniu sie wyniku dopisze outcome i evaluation jako nowe rekordy append-only.

Po meczu zapisujemy:

```text
final_score
actual_margin
cover / push / loss
closing_spread
closing_price
CLV
prediction_error
process_errors
```

Analizujemy:

- czy model mial dobry kierunek;
- czy PMF byl dobrze skalibrowany;
- czy edge przetrwal closing line;
- czy przegrana wynikala z procesu, modelu, rynku czy wariancji;
- czy `NO BET` bylo dobra decyzja.

Wynik etapu:

```text
ledger uczy nas, gdzie model i proces faktycznie popelniaja bledy
```

## Etap 7 - walk-forward backtest

Cel: testowac model tak, jakby przyszlosc nie byla znana.

Status: SZKIELET RAPORTOWANIA WDROZONY, pelny walk-forward do zrobienia po wiekszej probie settled outcomes.

Raport learningowy:

```text
scripts/variant_b_learning_report.py
research/variant_b_learning_report.md
```

Nie robimy losowego train/test splitu.

Robimy chronologicznie:

```text
train: wszystko przed week X
test: week X

train: wszystko przed week X+1
test: week X+1
```

Kazdy feature musi byc dostepny historycznie w tym samym momencie, w ktorym model mialby go uzyc.

Metryki:

```text
MAE marginu
RMSE marginu
bias
Brier score
log loss
calibration error
p_push calibration
CLV
ROI jako metryka pomocnicza
max drawdown jako ryzyko
```

Wynik etapu:

```text
wiemy, czy model dziala poza jednym sezonem i bez data leakage
```

## Etap 8 - prosty baseline model

Cel: zaczac od modelu, ktory jest latwy do kontroli.

Status MVP: OBECNY `variant_m` jest zapisany jako champion baseline.

Registry:

```text
config/model_registry.json
```

Nie zaczynamy od duzej sieci neuronowej.

Pierwszy baseline:

```text
team strength
offense rating
defense rating
special teams
quarterback value
home / away / neutral
rest days
travel
early / middle / late season
market spread snapshot
```

Mozliwe algorytmy:

```text
regularized regression
gradient boosting
Elo z rozszerzeniami
ensemble prostych modeli
```

Wynik etapu:

```text
kontrolowany model bazowy, ktory mozna porownac z obecnym Variant M
```

## Etap 9 - kalibracja

Cel: model nie tylko wskazuje kierunek, ale dobrze wycenia prawdopodobienstwa.

Status MVP: RAPORT KALIBRACJI WDROZONY, ale bedzie pusty do czasu settled outcomes.

Raport tworzy buckety `p_cover` i porowna predicted probability z realnym cover rate.

Sprawdzamy:

- czy `p_cover = 60%` faktycznie wygrywa okolo 60% po uwzglednieniu push;
- czy Week 1 ma zbyt waski rozklad;
- czy faworyci sa przeszacowani;
- czy underdogi sa niedoszacowane;
- czy neutral-site games maja wyzsza niepewnosc;
- czy key numbers maja poprawna mase PMF.

Wynik etapu:

```text
probabilities sa bardziej wiarygodne niz sam raw edge
```

## Etap 10 - champion / challenger

Cel: model moze sie uczyc, ale nie moze sam siebie promowac po jednej dobrej kolejce.

Status MVP: REJESTR I POLITYKA PROMOCJI WDROZONE.

Plik:

```text
config/model_registry.json
```

Na razie `variant_m` jest championem. Kandydaci beda dodawani dopiero po pelnym walk-forward backtest i kalibracji.

Proces:

```text
champion_model = aktualna wersja produkcyjna
candidate_model = nowo wytrenowana wersja
```

Candidate przechodzi:

- walk-forward backtest;
- calibration test;
- segment risk test;
- no data leakage check;
- stability check;
- porownanie z championem;
- review.

Promocja tylko wtedy, gdy przejdzie predefiniowane gate'y.

Wynik etapu:

```text
system uczy sie kontrolowanie, z mozliwoscia rollbacku
```

## Etap 11 - rola GPT / LLM

GPT nie jest glownym modelem predykcyjnym.

Status: PROCESOWO USTALONE, techniczna automatyzacja research snapshots nadal do zrobienia.

GPT moze:

- szukac oficjalnych injury reports;
- streszczac roster moves;
- porownywac zrodla;
- generowac research snapshot;
- opisywac ryzyka;
- wyjasniac wynik modelu;
- wskazywac missing data.

GPT nie moze:

- sam liczyc EV;
- rekonstruowac brakujacych quote;
- promowac nowego modelu;
- zmieniac regul Variant B;
- traktowac narracji jako danych;
- uzywac informacji post-event w pregame modelu.

Wynik etapu:

```text
LLM = research and explanation layer, Python = kalkulacje i decyzje
```

## Modul dodatkowy - Live Quarter Scenario Matrix

To jest osobny modul live-scenario, a nie zamiennik modelu pregame.

Cel:

```text
po Q1 / H1 / Q3 pokazac historyczne prawdopodobienstwa dalszego przebiegu meczu
```

Modul korzysta z `nfl_data_py` i buduje:

- pelne 81 sciezek kwartowych WIN / LOSS / TIE;
- 120 przejsc miedzy wezlami drzewa;
- quarter reset view;
- cumulative game view;
- buckety prowadzenia / straty punktowej;
- segmenty favorite / underdog, home / away, spread bucket, season phase;
- fair odds i EV dla kursu live wpisanego recznie.

Glowny skrypt:

```text
scripts/live_quarter_scenario_matrix.py
```

Instrukcja:

```text
docs/live_quarter_scenario_matrix.md
```

Wynik:

```text
research/live_quarter_scenario_matrix/2016_2025_league_wide/
```

Zasada:

```text
ten modul pokazuje historyczne scenario support, ale nie daje samodzielnego finalnego betu
```

## Kolejnosc wdrozenia

Najblizsza praktyczna kolejnosc:

1. Uporzadkowac kontrakt danych i nazwy margin/spread.
2. Rozbudowac append-only ledger.
3. Zamrozic model runs i quote snapshots.
4. Rozszerzyc model proof MVP do pelnego margin PMF.
5. Dodac post-event evaluation.
6. Zrobic walk-forward backtest as-of.
7. Dopiero potem trenowac candidate model.
8. Na koncu wdrozyc champion/challenger.

## Najwazniejszy wniosek

Najpierw budujemy pamiec systemu:

```text
co wiedzielismy, kiedy to wiedzielismy, jaka byla predykcja, jaki byl quote, jaka byla decyzja i jaki byl wynik
```

Dopiero potem budujemy bardziej zaawansowany model uczacy sie.
