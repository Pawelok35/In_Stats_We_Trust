# 2026 Week 1 Full Training Simulation

Status: FICTIONAL TRAINING DATA

Ten plik sluzy tylko do testu procesu Variant B Daily Bot. Linie, kontuzje, newsy, wyniki i ruchy rynku sa wymyslone do symulacji. Nie traktuj tego jako realnych danych bettingowych.

Cel symulacji:

1. Przejsc caly tydzien operacyjny od poniedzialku przed Week 1 do wtorku po Week 1.
2. Codziennie dodawac nowe informacje: linie, kontuzje, roster/news, weather, GPT 19/delta, quote.
3. Sprawdzic, czy bot prowadzi nas przez workflow bez gubienia krokow.
4. Zobaczyc, jak NEUTRAL moze wejsc na watchliste albo przejsc do VP/GOW/GOM/GOY po ruchu linii.

## Jak Tego Uzywac

Kazdego dnia kopiujesz tylko sekcje danego dnia.

Przyklad:

```text
Symulacja Week 1 - Tuesday.
Uzyj ponizszego book_snapshot/news_update jako dzisiejszego inputu treningowego.
```

Do GPT dajesz bloki `FOR GPT`.

Do Codex dajesz bloki `FOR CODEX`.

W bocie wykonujesz bloki `BOT ACTION`.

## Wazne Zasady

- To jest symulacja. Jesli plik mowi `captured_at_utc`, traktujemy go jako timestamp treningowy.
- Book to `SIM_PREGAME_COM`, zeby nie pomylic z realnym pregame.com.
- `executable_status` jest `simulation_only`.
- W realnym sezonie zamiast tych danych wklejasz screeny z booka i realne newsy.
- W Week 1 nie ma poprzedniej kolejki, wiec poniedzialek/wtorek post-event poprzedniego tygodnia ma byc `SKIPPED`.

---

# Monday 2026-09-07 - First Season Setup

## Cel

Pierwszy raz dodajemy Week 1 do systemu. Nie gramy nic. Tworzymy poczatkowy book snapshot i sprawdzamy, czy bot potrafi zbudowac linie oraz skan.

## BOT ACTION

```text
1. Open bot.
2. Season = 2026.
3. Week = 1.
4. Day = monday.
5. Reset week test data, jesli chcesz zaczac calkowicie od zera.
6. Nie klikaj jeszcze Load model picks, dopoki nie wykonasz Tuesday/Execute albo recznej konwersji snapshotu.
```

## FOR CODEX - Initial Book Snapshot

```text
Zapisz ponizszy YAML jako book snapshot dla season=2026, week=1.
To sa dane symulacyjne, nie realny rynek.
Po zapisie uruchom konwersje do config/lines/2026/week1_lines.yaml i sprawdz walidacje.
```

```yaml
book_snapshot:
  book: SIM_PREGAME_COM
  season: 2026
  week: 1
  captured_at_utc: "2026-09-07T18:00:00Z"
  executable_status: simulation_only
  target_stake: 100
  house_rules_checked: false

games:
  - game_date_local: "2026-09-10"
    game_time_local: "02:20"
    away: NE
    home: SEA
    away_moneyline: 2.790
    home_moneyline: 1.485
    away_spread: 4.5
    away_spread_price: 1.854
    home_spread: -4.5
    home_spread_price: 2.040
    total_over: 43.5
    total_over_price: 1.892
    total_under: 43.5
    total_under_price: 1.961
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-11"
    game_time_local: "02:35"
    away: SF
    home: LA
    away_moneyline: 2.700
    home_moneyline: 1.512
    away_spread: 3.0
    away_spread_price: 2.170
    home_spread: -3.0
    home_spread_price: 1.763
    total_over: 48.5
    total_over_price: 1.934
    total_under: 48.5
    total_under_price: 1.917
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "19:00"
    away: ATL
    home: PIT
    away_moneyline: 2.430
    home_moneyline: 1.617
    away_spread: 2.5
    away_spread_price: 2.130
    home_spread: -2.5
    home_spread_price: 1.787
    total_over: 41.5
    total_over_price: 1.877
    total_under: 41.5
    total_under_price: 1.980
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "19:00"
    away: BUF
    home: HOU
    away_moneyline: 1.943
    home_moneyline: 1.943
    away_spread: -1.0
    away_spread_price: 2.010
    home_spread: 1.0
    home_spread_price: 1.884
    total_over: 44.0
    total_over_price: 1.869
    total_under: 44.0
    total_under_price: 1.990
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "19:00"
    away: CHI
    home: CAR
    away_moneyline: 1.689
    home_moneyline: 2.290
    away_spread: -2.5
    away_spread_price: 1.909
    home_spread: 2.5
    home_spread_price: 1.980
    total_over: 45.5
    total_over_price: 1.917
    total_under: 45.5
    total_under_price: 1.934
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "19:00"
    away: NO
    home: DET
    away_moneyline: 3.750
    home_moneyline: 1.301
    away_spread: 7.0
    away_spread_price: 1.970
    home_spread: -7.0
    home_spread_price: 1.917
    total_over: 49.5
    total_over_price: 1.925
    total_under: 49.5
    total_under_price: 1.925
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "19:00"
    away: NYJ
    home: TEN
    away_moneyline: 2.320
    home_moneyline: 1.666
    away_spread: 2.5
    away_spread_price: 2.020
    home_spread: -2.5
    home_spread_price: 1.869
    total_over: 38.5
    total_over_price: 1.934
    total_under: 38.5
    total_under_price: 1.917
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "19:00"
    away: BAL
    home: IND
    away_moneyline: 1.578
    home_moneyline: 2.520
    away_spread: -3.5
    away_spread_price: 2.050
    home_spread: 3.5
    home_spread_price: 1.847
    total_over: 47.5
    total_over_price: 1.909
    total_under: 47.5
    total_under_price: 1.943
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "19:00"
    away: CLE
    home: JAX
    away_moneyline: 3.850
    home_moneyline: 1.289
    away_spread: 7.5
    away_spread_price: 1.909
    home_spread: -7.5
    home_spread_price: 1.980
    total_over: 40.5
    total_over_price: 1.917
    total_under: 40.5
    total_under_price: 1.934
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "19:00"
    away: TB
    home: CIN
    away_moneyline: 2.630
    home_moneyline: 1.537
    away_spread: 3.5
    away_spread_price: 1.909
    home_spread: -3.5
    home_spread_price: 1.980
    total_over: 52.0
    total_over_price: 1.925
    total_under: 52.0
    total_under_price: 1.925
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "22:25"
    away: GB
    home: MIN
    away_moneyline: 2.030
    home_moneyline: 1.862
    away_spread: 1.0
    away_spread_price: 1.952
    home_spread: -1.0
    home_spread_price: 1.934
    total_over: 45.5
    total_over_price: 1.970
    total_under: 45.5
    total_under_price: 1.884
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "22:25"
    away: ARI
    home: LAC
    away_moneyline: 4.940
    home_moneyline: 1.196
    away_spread: 10.5
    away_spread_price: 1.884
    home_spread: -10.5
    home_spread_price: 2.000
    total_over: 46.0
    total_over_price: 1.925
    total_under: 46.0
    total_under_price: 1.925
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "22:25"
    away: WAS
    home: PHI
    away_moneyline: 2.780
    home_moneyline: 1.487
    away_spread: 4.0
    away_spread_price: 1.917
    home_spread: -4.0
    home_spread_price: 1.970
    total_over: 47.5
    total_over_price: 2.000
    total_under: 47.5
    total_under_price: 1.854
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-13"
    game_time_local: "22:25"
    away: MIA
    home: LV
    away_moneyline: 2.760
    home_moneyline: 1.492
    away_spread: 3.5
    away_spread_price: 2.020
    home_spread: -3.5
    home_spread_price: 1.869
    total_over: 40.5
    total_over_price: 1.925
    total_under: 40.5
    total_under_price: 1.925
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-14"
    game_time_local: "02:20"
    away: DAL
    home: NYG
    away_moneyline: 1.628
    home_moneyline: 2.400
    away_spread: -2.0
    away_spread_price: 1.769
    home_spread: 2.0
    home_spread_price: 2.160
    total_over: 47.5
    total_over_price: 1.877
    total_under: 47.5
    total_under_price: 1.980
    game_line_quality: CONSISTENT_DISPLAY
    notes: []

  - game_date_local: "2026-09-15"
    game_time_local: "02:15"
    away: DEN
    home: KC
    away_moneyline: 2.350
    home_moneyline: 1.600
    away_spread: 3.0
    away_spread_price: 1.880
    home_spread: -3.0
    home_spread_price: 1.910
    total_over: 42.5
    total_over_price: 1.900
    total_under: 42.5
    total_under_price: 1.900
    game_line_quality: CONSISTENT_DISPLAY
    notes: []
```

## Simulated Monday News

```yaml
news_update:
  day: monday
  captured_at_utc: "2026-09-07T18:15:00Z"
  status: simulation_only
  items:
    - game: SF_at_LA
      type: injury_watch
      team: LA
      player_role: WR1
      status: limited_practice_estimate
      betting_relevance: medium
      note: "Training simulation: WR1 workload monitored; not a blocker yet."
    - game: BAL_at_IND
      type: offensive_line
      team: IND
      player_role: LT
      status: did_not_practice_estimate
      betting_relevance: high
      note: "Potential pass protection issue vs BAL rush."
    - game: DAL_at_NYG
      type: quarterback
      team: NYG
      player_role: QB1
      status: full_practice_estimate
      betting_relevance: low
      note: "No restriction, but monitor after preseason ankle note."
```

---

# Tuesday 2026-09-08 - Main Week Scan

## Cel

Robimy pierwszy pelny skan tygodnia. Jesli pojawia sie VP/GOW/GOM/GOY, wtedy dla tych meczow robimy pelne 19 punktow GPT.

## BOT ACTION

```text
1. Day = tuesday.
2. Dry run.
3. Execute.
4. Load model picks.
5. Sprawdz Pick oraz Watchlist.
```

## FOR CODEX - Tuesday Full Book Snapshot

```text
To jest pelny book_snapshot na start symulacji od wtorku.
Skopiuj caly YAML ponizej do pola GPT Paste w bocie, potem kliknij Save book snapshot from paste i Convert snapshot to lines.
```

```yaml
book_snapshot:
  book: SIM_PREGAME_COM
  season: 2026
  week: 1
  captured_at_utc: '2026-09-08T18:00:00Z'
  executable_status: simulation_only
  target_stake: 100
  house_rules_checked: false
games:
- game_date_local: '2026-09-10'
  game_time_local: 02:20
  away: NE
  home: SEA
  away_moneyline: 2.79
  home_moneyline: 1.485
  away_spread: 4.5
  away_spread_price: 1.854
  home_spread: -4.5
  home_spread_price: 2.04
  total_over: 43.5
  total_over_price: 1.892
  total_under: 43.5
  total_under_price: 1.961
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
- game_date_local: '2026-09-11'
  game_time_local: 02:35
  away: SF
  home: LA
  away_moneyline: 2.7
  home_moneyline: 1.512
  away_spread: 3.0
  away_spread_price: 2.02
  home_spread: -3.0
  home_spread_price: 1.84
  total_over: 48.5
  total_over_price: 1.934
  total_under: 48.5
  total_under_price: 1.917
  game_line_quality: CONSISTENT_DISPLAY
  notes:
  - 'Tuesday simulation: LA price drifted cheaper but spread stayed -3.'
- game_date_local: '2026-09-13'
  game_time_local: '19:00'
  away: ATL
  home: PIT
  away_moneyline: 2.43
  home_moneyline: 1.617
  away_spread: 2.5
  away_spread_price: 2.13
  home_spread: -2.5
  home_spread_price: 1.787
  total_over: 41.5
  total_over_price: 1.877
  total_under: 41.5
  total_under_price: 1.98
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
- game_date_local: '2026-09-13'
  game_time_local: '19:00'
  away: BUF
  home: HOU
  away_moneyline: 1.943
  home_moneyline: 1.943
  away_spread: -1.5
  away_spread_price: 1.98
  home_spread: 1.5
  home_spread_price: 1.9
  total_over: 44.0
  total_over_price: 1.869
  total_under: 44.0
  total_under_price: 1.99
  game_line_quality: CONSISTENT_DISPLAY
  notes:
  - 'Tuesday simulation: HOU moved to +1.5.'
- game_date_local: '2026-09-13'
  game_time_local: '19:00'
  away: CHI
  home: CAR
  away_moneyline: 1.689
  home_moneyline: 2.29
  away_spread: -2.5
  away_spread_price: 1.909
  home_spread: 2.5
  home_spread_price: 1.98
  total_over: 45.5
  total_over_price: 1.917
  total_under: 45.5
  total_under_price: 1.934
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
- game_date_local: '2026-09-13'
  game_time_local: '19:00'
  away: 'NO'
  home: DET
  away_moneyline: 3.75
  home_moneyline: 1.301
  away_spread: 7.0
  away_spread_price: 1.97
  home_spread: -7.0
  home_spread_price: 1.917
  total_over: 49.5
  total_over_price: 1.925
  total_under: 49.5
  total_under_price: 1.925
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
- game_date_local: '2026-09-13'
  game_time_local: '19:00'
  away: NYJ
  home: TEN
  away_moneyline: 2.32
  home_moneyline: 1.666
  away_spread: 2.5
  away_spread_price: 2.02
  home_spread: -2.5
  home_spread_price: 1.869
  total_over: 38.5
  total_over_price: 1.934
  total_under: 38.5
  total_under_price: 1.917
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
- game_date_local: '2026-09-13'
  game_time_local: '19:00'
  away: BAL
  home: IND
  away_moneyline: 1.578
  home_moneyline: 2.52
  away_spread: -4.0
  away_spread_price: 1.91
  home_spread: 4.0
  home_spread_price: 1.91
  total_over: 47.5
  total_over_price: 1.909
  total_under: 47.5
  total_under_price: 1.943
  game_line_quality: CONSISTENT_DISPLAY
  notes:
  - 'Tuesday simulation: Market moved against IND after LT DNP estimate.'
- game_date_local: '2026-09-13'
  game_time_local: '19:00'
  away: CLE
  home: JAX
  away_moneyline: 3.85
  home_moneyline: 1.289
  away_spread: 7.5
  away_spread_price: 1.909
  home_spread: -7.5
  home_spread_price: 1.98
  total_over: 40.5
  total_over_price: 1.917
  total_under: 40.5
  total_under_price: 1.934
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
- game_date_local: '2026-09-13'
  game_time_local: '19:00'
  away: TB
  home: CIN
  away_moneyline: 2.63
  home_moneyline: 1.537
  away_spread: 3.5
  away_spread_price: 1.909
  home_spread: -3.5
  home_spread_price: 1.98
  total_over: 52.0
  total_over_price: 1.925
  total_under: 52.0
  total_under_price: 1.925
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
- game_date_local: '2026-09-13'
  game_time_local: '22:25'
  away: GB
  home: MIN
  away_moneyline: 2.03
  home_moneyline: 1.862
  away_spread: 1.0
  away_spread_price: 1.952
  home_spread: -1.0
  home_spread_price: 1.934
  total_over: 45.5
  total_over_price: 1.97
  total_under: 45.5
  total_under_price: 1.884
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
- game_date_local: '2026-09-13'
  game_time_local: '22:25'
  away: ARI
  home: LAC
  away_moneyline: 4.94
  home_moneyline: 1.196
  away_spread: 10.5
  away_spread_price: 1.884
  home_spread: -10.5
  home_spread_price: 2.0
  total_over: 46.0
  total_over_price: 1.925
  total_under: 46.0
  total_under_price: 1.925
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
- game_date_local: '2026-09-13'
  game_time_local: '22:25'
  away: WAS
  home: PHI
  away_moneyline: 2.78
  home_moneyline: 1.487
  away_spread: 4.0
  away_spread_price: 1.917
  home_spread: -4.0
  home_spread_price: 1.97
  total_over: 47.5
  total_over_price: 2.0
  total_under: 47.5
  total_under_price: 1.854
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
- game_date_local: '2026-09-13'
  game_time_local: '22:25'
  away: MIA
  home: LV
  away_moneyline: 2.76
  home_moneyline: 1.492
  away_spread: 3.5
  away_spread_price: 2.02
  home_spread: -3.5
  home_spread_price: 1.869
  total_over: 40.5
  total_over_price: 1.925
  total_under: 40.5
  total_under_price: 1.925
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
- game_date_local: '2026-09-14'
  game_time_local: 02:20
  away: DAL
  home: NYG
  away_moneyline: 1.628
  home_moneyline: 2.4
  away_spread: -2.5
  away_spread_price: 1.95
  home_spread: 2.5
  home_spread_price: 1.95
  total_over: 47.5
  total_over_price: 1.877
  total_under: 47.5
  total_under_price: 1.98
  game_line_quality: CONSISTENT_DISPLAY
  notes:
  - 'Tuesday simulation: NYG dog moved from +2 to +2.5.'
- game_date_local: '2026-09-15'
  game_time_local: 02:15
  away: DEN
  home: KC
  away_moneyline: 2.35
  home_moneyline: 1.6
  away_spread: 3.0
  away_spread_price: 1.88
  home_spread: -3.0
  home_spread_price: 1.91
  total_over: 42.5
  total_over_price: 1.9
  total_under: 42.5
  total_under_price: 1.9
  game_line_quality: CONSISTENT_DISPLAY
  notes: []
```

## FOR GPT - Full 19 Points, Only If Action Pick Appears

```text
Uzyj frameworka Variant B 19 punktow.
Mecz: [wklej game_id z bota]
Season: 2026
Week: 1
Day: Tuesday main scan
To jest symulacja treningowa. Nie dawaj realnego picka.
Zwroc audit_metadata, points 1-19 i final_summary.
Oznacz MISSING/PENDING_NOT_DUE tam, gdzie dane sa jeszcze niedostepne.
```

## Simulated Tuesday News

```yaml
news_update:
  day: tuesday
  captured_at_utc: "2026-09-08T19:00:00Z"
  items:
    - game: SF_at_LA
      team: SF
      type: injury
      player_role: EDGE1
      status: limited
      relevance: medium
      note: "Could reduce SF pass rush ceiling, small boost to LA passing script."
    - game: BAL_at_IND
      team: IND
      type: injury
      player_role: LT
      status: did_not_practice
      relevance: high
      note: "Sustains concern from Monday."
    - game: DAL_at_NYG
      team: DAL
      type: roster
      player_role: CB2
      status: questionable
      relevance: medium
      note: "Could matter for NYG explosive pass risk."
```

Expected training behavior:

```text
Pick list may still be empty.
Watchlist should contain near-value games such as LA/SF, IND/BAL, NYG/DAL, HOU/BUF depending on model output.
```

---

# Wednesday 2026-09-09 - TNF / Early Game Delta

## Cel

Nie robimy od nowa 19 punktow dla wszystkiego. Robimy delta refresh: line movement, kontuzje, weather, roster, blockers.

## BOT ACTION

```text
1. Day = wednesday.
2. Dry run.
3. Wybierz watchlist/action game, jesli istnieje.
4. Copy GPT prompt.
5. Wklej GPT delta output do GPT Paste i Save GPT snapshot.
6. Execute.
```

## FOR GPT - Wednesday Delta

```yaml
delta_refresh:
  day: wednesday
  captured_at_utc: "2026-09-09T18:00:00Z"
  scope: TNF_and_early_games
  games:
    - game: NE_at_SEA
      line_move:
        old_home_spread: -4.5
        new_home_spread: -4.0
        old_total: 43.5
        new_total: 42.5
      news:
        - team: SEA
          player_role: RB1
          status: limited
          relevance: medium
          note: "RB workload uncertainty; total down 1 point."
        - team: NE
          player_role: CB1
          status: full
          relevance: low
          note: "Cleared from Monday estimate."
      weather:
        venue_type: outdoor
        condition: light_rain_possible
        wind_mph: 9
        relevance: low_medium

    - game: SF_at_LA
      line_move:
        old_home_spread: -3.0
        new_home_spread: -2.5
        old_total: 48.5
        new_total: 48.0
      news:
        - team: LA
          player_role: WR1
          status: full
          relevance: medium
          note: "Positive for LA; removes Monday uncertainty."
        - team: SF
          player_role: EDGE1
          status: limited
          relevance: medium
          note: "Still not full."
      market_note: "Line moved toward SF from LA -3 to LA -2.5."
```

Expected training behavior:

```text
SF_at_LA can move closer to action if model liked LA at -3.0 and market gives -2.5.
But final proof still needs real quote/timestamp in real workflow.
```

---

# Thursday 2026-09-10 - Final Check First Game

## Cel

Final/pre-kickoff check dla pierwszego meczu. Nie mieszamy live z pregame.

## BOT ACTION

```text
1. Day = thursday.
2. Dla NE_at_SEA zrob final delta.
3. Jesli SF_at_LA gra tego dnia w twojej symulacji, zrob final delta dla SF_at_LA.
4. Execute po zapisaniu GPT delta/quote.
```

## FOR GPT - Thursday Final Delta

```yaml
final_delta:
  day: thursday
  captured_at_utc: "2026-09-10T18:30:00Z"
  games:
    - game: NE_at_SEA
      final_quote:
        home: SEA
        away: NE
        home_spread: -4.0
        home_spread_price: 1.930
        total: 42.5
        book: SIM_PREGAME_COM
        executable_status: simulation_only
      final_news:
        - team: SEA
          player_role: RB1
          status: active_limited_workload_expected
          relevance: medium
        - team: NE
          player_role: WR2
          status: inactive
          relevance: medium
      decision_guardrail:
        stale_quote: false
        no_chase_breached: false
        final_inactives_checked: true
    - game: SF_at_LA
      final_quote:
        home: LA
        away: SF
        home_spread: -2.5
        home_spread_price: 1.870
        total: 48.0
        book: SIM_PREGAME_COM
        executable_status: simulation_only
      final_news:
        - team: LA
          player_role: WR1
          status: active_full
          relevance: medium
        - team: SF
          player_role: EDGE1
          status: active_limited_snap_count_risk
          relevance: medium_high
      decision_guardrail:
        stale_quote: false
        no_chase_breached: false
        final_inactives_checked: true
```

## Optional Live Scenario Test

Po Q1 SF_at_LA:

```yaml
live_scenario_test:
  game: SF_at_LA
  team_a: LA
  q1_result_for_team_a: LOSS
  cumulative_score_after_q1:
    SF: 7
    LA: 3
  lookup_path: LOSS
  event: TEAM_A_WIN_FINAL
  live_decimal: 2.25
```

BOT ACTION:

```text
1. W Live Scenario ustaw Team A = LA, Opponent = SF.
2. Path = LOSS.
3. Event = TEAM_A_WIN_FINAL.
4. Live decimal = 2.25.
5. Run live lookup.
```

---

# Friday 2026-09-11 - Main Sunday/MNF Refresh

## Cel

Odswiezamy niedzielne i poniedzialkowe mecze: injury report, roster, market movement, weather.

## BOT ACTION

```text
1. Day = friday.
2. Dla meczow z Watchlist zrob GPT delta.
3. Execute po zapisaniu delta.
```

## FOR GPT - Friday Delta

```yaml
delta_refresh:
  day: friday
  captured_at_utc: "2026-09-11T19:00:00Z"
  scope: sunday_mnf
  games:
    - game: BAL_at_IND
      line_move:
        old_home_spread: 4.0
        new_home_spread: 4.5
        total_from: 47.5
        total_to: 46.5
      news:
        - team: IND
          player_role: LT
          status: doubtful
          relevance: high
        - team: BAL
          player_role: RB1
          status: full
          relevance: low_medium
      note: "Market continues against IND."

    - game: DAL_at_NYG
      line_move:
        old_home_spread: 2.5
        new_home_spread: 3.0
        total_from: 47.5
        total_to: 47.0
      news:
        - team: DAL
          player_role: CB2
          status: questionable
          relevance: medium
        - team: NYG
          player_role: WR1
          status: full
          relevance: medium
      note: "Key number +3 appears for NYG."

    - game: BUF_at_HOU
      line_move:
        old_home_spread: 1.5
        new_home_spread: 2.0
        total_from: 44.0
        total_to: 43.5
      news:
        - team: HOU
          player_role: WR2
          status: questionable
          relevance: medium
        - team: BUF
          player_role: S1
          status: limited
          relevance: medium
```

Expected training behavior:

```text
NYG +3 should be highlighted as a watchlist/key-number spot.
BAL_at_IND should likely remain watch/HOLD if injury is against IND.
```

---

# Saturday 2026-09-12 - Pre-Final Sunday/MNF

## Cel

Lista brakow przed niedziela. Nie ma jeszcze final inactives, ale wiemy co monitorowac.

## FOR GPT - Saturday Pre-Final

```yaml
prefinal_delta:
  day: saturday
  captured_at_utc: "2026-09-12T18:00:00Z"
  watchlist_priority:
    - game: DAL_at_NYG
      status: WATCH_KEY_NUMBER
      current_quote:
        NYG_spread: 3.0
        NYG_price: 1.980
      blockers:
        - final_inactives_pending
        - confirm_DAL_CB2_status
      note: "If NYG remains +3 or better and DAL CB2 inactive, promote to final review."

    - game: SF_at_LA
      status: WATCH_PRICE
      current_quote:
        LA_spread: -2.5
        LA_price: 1.900
      blockers:
        - no_chase_check
        - confirm_no_late_QB_or_OL_news
      note: "LA no longer expensive compared with Monday line."

    - game: BUF_at_HOU
      status: WATCH_TOTAL_AND_DOG
      current_quote:
        HOU_spread: 2.0
        HOU_price: 1.910
      blockers:
        - HOU_WR2_status
        - weather_check
```

## BOT ACTION

```text
1. Day = saturday.
2. Save GPT delta for relevant watchlist games.
3. Execute.
4. Nie dawaj finalnego werdyktu bez Sunday final check.
```

---

# Sunday 2026-09-13 - Final Sunday + MNF Delta

## Cel

Final Sunday pre-kickoff. Osobno robimy tylko delta dla MNF.

## FOR GPT - Sunday Final

```yaml
final_sunday_delta:
  day: sunday
  captured_at_utc: "2026-09-13T16:30:00Z"
  final_inactives_checked: true
  games:
    - game: DAL_at_NYG
      final_quote:
        selected_team: NYG
        spread: 3.0
        price: 1.970
        book: SIM_PREGAME_COM
        executable_status: simulation_only
      final_news:
        - team: DAL
          player_role: CB2
          status: inactive
          relevance: medium_high
        - team: NYG
          player_role: QB1
          status: active_full
          relevance: medium
      operator_status: READY_FOR_FINAL_REVIEW

    - game: BUF_at_HOU
      final_quote:
        selected_team: HOU
        spread: 2.0
        price: 1.900
        book: SIM_PREGAME_COM
        executable_status: simulation_only
      final_news:
        - team: HOU
          player_role: WR2
          status: active_limited
          relevance: medium
        - team: BUF
          player_role: S1
          status: active
          relevance: low
      operator_status: WATCH_OR_HOLD

    - game: BAL_at_IND
      final_quote:
        selected_team: IND
        spread: 4.5
        price: 1.910
        book: SIM_PREGAME_COM
        executable_status: simulation_only
      final_news:
        - team: IND
          player_role: LT
          status: inactive
          relevance: high
      operator_status: HOLD
      note: "Injury against selected side blocks upgrade despite bigger spread."

  mnf_delta:
    game: DEN_at_KC
    current_quote:
      KC_spread: -3.0
      KC_price: 1.900
      total: 42.5
    news:
      - team: KC
        player_role: TE1
        status: limited
        relevance: medium
      - team: DEN
        player_role: CB1
        status: questionable
        relevance: medium
```

## Live Scenario Sunday Examples

```yaml
live_scenario_examples:
  - game: DAL_at_NYG
    team_a: NYG
    q1_result: WIN
    q2_result: LOSS
    cumulative_after_h1: NYG_LEAD_3
    lookup_path: WIN-LOSS
    event: TEAM_A_WIN_FINAL
    live_decimal: 2.05

  - game: BUF_at_HOU
    team_a: HOU
    q1_result: LOSS
    q2_result: WIN
    cumulative_after_h1: TIE
    lookup_path: LOSS-WIN
    event: TEAM_A_WIN_FINAL
    live_decimal: 2.40
```

## BOT ACTION

```text
1. Day = sunday.
2. Save Sunday final GPT deltas.
3. Execute.
4. Jesli chcesz testowac live, uzyj panelu Live Scenario.
```

---

# Monday 2026-09-14 - Final MNF

## Cel

Finalny check MNF. Nie ruszamy zakonczonych Sunday gier poza live/settlement notes.

## FOR GPT - Monday MNF Final

```yaml
final_mnf_delta:
  day: monday
  captured_at_utc: "2026-09-14T23:30:00Z"
  game: DEN_at_KC
  final_quote:
    selected_team: KC
    spread: -3.0
    price: 1.910
    total: 42.0
    book: SIM_PREGAME_COM
    executable_status: simulation_only
  final_news:
    - team: KC
      player_role: TE1
      status: active_limited
      relevance: medium
    - team: DEN
      player_role: CB1
      status: inactive
      relevance: medium_high
  weather:
    condition: clear
    wind_mph: 6
    relevance: low
  operator_status: READY_FOR_FINAL_REVIEW
```

## BOT ACTION

```text
1. Day = monday.
2. Save MNF final delta.
3. Execute.
4. Po zakonczeniu MNF nie rob jeszcze post-event, dopiero Tuesday.
```

---

# Tuesday 2026-09-15 - Post-Event Week 1 Summary

## Cel

Zamykamy Week 1: wyniki, settlement, post-event evaluation, learning ledger/report. Potem zaczynamy Week 2.

## FOR CODEX - Simulated Final Scores

```text
Zapisz ponizsze final scores jako symulacyjne wyniki Week 1, jesli mamy skrypt/manual results dla post-event.
Jesli nie mamy gotowego miejsca, utworz plik research/simulations/2026_week1_simulated_final_scores.jsonl.
Potem uruchom post-event evaluation, jesli dane sa podlaczone.
```

```jsonl
{"season":2026,"week":1,"away":"NE","home":"SEA","away_score":17,"home_score":24}
{"season":2026,"week":1,"away":"SF","home":"LA","away_score":23,"home_score":27}
{"season":2026,"week":1,"away":"ATL","home":"PIT","away_score":20,"home_score":21}
{"season":2026,"week":1,"away":"BUF","home":"HOU","away_score":24,"home_score":23}
{"season":2026,"week":1,"away":"CHI","home":"CAR","away_score":28,"home_score":20}
{"season":2026,"week":1,"away":"NO","home":"DET","away_score":21,"home_score":31}
{"season":2026,"week":1,"away":"NYJ","home":"TEN","away_score":17,"home_score":19}
{"season":2026,"week":1,"away":"BAL","home":"IND","away_score":27,"home_score":20}
{"season":2026,"week":1,"away":"CLE","home":"JAX","away_score":16,"home_score":24}
{"season":2026,"week":1,"away":"TB","home":"CIN","away_score":27,"home_score":30}
{"season":2026,"week":1,"away":"GB","home":"MIN","away_score":21,"home_score":24}
{"season":2026,"week":1,"away":"ARI","home":"LAC","away_score":14,"home_score":28}
{"season":2026,"week":1,"away":"WAS","home":"PHI","away_score":20,"home_score":27}
{"season":2026,"week":1,"away":"MIA","home":"LV","away_score":22,"home_score":26}
{"season":2026,"week":1,"away":"DAL","home":"NYG","away_score":24,"home_score":27}
{"season":2026,"week":1,"away":"DEN","home":"KC","away_score":20,"home_score":24}
```

## Simulated Betting/Process Notes

```yaml
post_event_notes:
  week: 1
  simulation_only: true
  key_review_items:
    - "Did the model correctly separate action picks from watchlist?"
    - "Did line movement from LA -3.0 to -2.5 improve or reduce model confidence?"
    - "Did NYG +3 become actionable only after DAL CB2 inactive?"
    - "Did IND remain HOLD because bigger spread was offset by LT inactive?"
    - "Were all final decisions timestamped before kickoff?"
  process_failures_to_check:
    - missing_real_quote_timestamp
    - using_simulation_only_book_as_if_executable
    - mixing live scenario with pregame tracking
```

## BOT ACTION

```text
1. Day = tuesday.
2. This is now the Tuesday AFTER Week 1.
3. Run close previous week / post-event flow.
4. Review learning report.
5. Start Week 2 main scan after Week 1 is closed.
```

---

# Expected End State Of Simulation

Po pelnym przejsciu powinienes miec:

```text
data/book_snapshots/2026/week_01_screen_snapshot.yaml
config/lines/2026/week1_lines.yaml
data/picks_variant_m/2026/week_01.jsonl
research/daily_bot/2026/week_01/*.md
research/gpt_snapshots/2026/week_01/{game_id}/full_19_points.md
research/gpt_snapshots/2026/week_01/{game_id}/delta_*.md
research/variant_b_week_flow/2026/week_01/summary.md
data/learning_ledger/2026/week_01/
research/simulations/2026_week1_simulated_final_scores.jsonl
```

Najwazniejszy test:

```text
Czy bot prowadzi cie przez brakujace inputy bez zgadywania?
Czy watchlista pomaga sledzic near-value?
Czy finalny werdykt pojawia sie dopiero po quote + GPT + final blockers?
```
