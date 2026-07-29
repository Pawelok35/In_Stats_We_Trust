# Variant B - uproszczona instrukcja tygodnia NFL

## Cel

Variant B ma dzialac prosto:

```text
skan kolejki -> tylko VP/GOW/GOM/GOY -> GPT research -> reczny quote z booka -> lokalny gate -> finalny werdykt
```

Nie gramy z samego modelu. Model tylko wskazuje kandydatow. Decyzja przechodzi dopiero po sprawdzeniu rynku, kontuzji, pogody, zmian skladu i finalnego quote.

## Najwazniejsza zasada

Pelny 19-punktowy research GPT robimy tylko raz dla danego meczu, gdy model znajdzie `VALUE PLAY`, `GOW`, `GOM` albo `GOY`.

Codziennie nie robimy od nowa 19 punktow. Codziennie robimy tylko refresh rzeczy, ktore mogly sie zmienic:

- line / price / book quote;
- kontuzje i statusy zawodnikow;
- inactives;
- pogoda;
- roster moves;
- public splits, jesli sa dostepne;
- nowe informacje o travel / schedule spot;
- nowe ryzyka matchup albo game script, jesli pojawily sie po pierwszym researchu.

## Pliki, ktorych uzywasz

Glowna instrukcja GPT:

```text
docs/variant_b_final_gpt_research_prompt.md
```

Krotki tekst do wklejenia GPT razem z plikiem:

```text
docs/variant_b_gpt_short_wrapper.md
```

Reczny quote z booka:

```text
data/market_quotes/{season}/week_{week}.jsonl
```

Przyklad dla week 1 sezonu 2026:

```text
data/market_quotes/2026/week_01.jsonl
```

Wynik tygodniowego flow:

```text
research/variant_b_week_flow/{season}/week_{week}/summary.md
```

## Komenda bazowa

Ta komenda nie tworzy pierwszych pickow od zera. Ona bierze juz przygotowany plik:

```text
data/picks_variant_m/{season}/week_{week}.jsonl
```

i robi audyt Variant B.

```powershell
python scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof
```

Jesli chcesz od razu zamrozic wynik do ledgeru modelu uczacego sie:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof --write-learning-ledger
```

Co robi ta komenda:

- bierze mecze i picki dla danego tygodnia;
- filtruje tylko `VALUE PLAY`, `GOW`, `GOM`, `GOY`;
- liczy model proof: `p_cover`, `p_push`, `p_loss`;
- sprawdza reczny quote z booka, jesli go wpisales;
- tworzy summary;
- pokazuje, czy pick jest gotowy, czy nadal `HOLD`.
- opcjonalnie dopisuje append-only rekordy do `data/learning_ledger/`.

## Format recznego quote z booka

Jeden wiersz JSON na jeden pick:

```json
{"season":2026,"week":1,"away":"SF","home":"LA","selected_team":"LA","market":"full-game spread","spread":-3.0,"line":-3.0,"price":-110,"book":"DraftKings","quote_timestamp_utc":"2026-09-08T18:42:00Z","quote_id":"","executable_status":"displayed_unverified","target_stake":100,"accepted_stake":"","source_type":"DIRECT_BOOK","market_scope":"FULL_GAME","jurisdiction":"US","house_rules_checked":true,"betslip_verified_at_utc":"","notes":"Rams -3 checked on DraftKings screen."}
```

Najwazniejsze pola:

```yaml
book: konkretny bukmacher
spread: spread dla selected_team
price: cena przy tym spreadzie
quote_timestamp_utc: kiedy sprawdziles quote
executable_status: displayed_unverified | betslip_checked | accepted_ticket
target_stake: stawka testowa, jesli sprawdzales betslip
house_rules_checked: true albo false
```

`MANUAL_CONSENSUS` jest tylko preview. Nie daje market-grade proof.

## Tygodniowy workflow

### Wtorek - glowny skan kolejki

1. Pobierz schedule i linie skanowe z `nfl_data_py`:

```powershell
python -m app.cli sync-nfl-schedule --season 2026
python -m app.cli export-lines-from-nfl --season 2026 --week 1
```

Te komendy tworza / aktualizuja:

```text
config/lines/2026/week1_lines.yaml
```

W tym pliku sa mecze kolejki oraz podstawowe linie:

```yaml
season:
week:
away:
home:
spread:
total:
price:
book:
```

To jest linia do skanu modelu. Nie traktujemy jej jako market-grade quote, bo nie jest to potwierdzony, wykonywalny kurs z Twojego booka.

Jesli `nfl_data_py` nie ma jeszcze linii dla przyszlej kolejki albo zwroci puste / stare dane, wtedy recznie poprawiasz `config/lines/2026/week1_lines.yaml`.

2. Wygeneruj picki modelu:

```powershell
python scripts\prospective_week_flow.py --season 2026 --week 1 --variant variant_m --skip-freeze
```

Ta komenda tworzy plik:

```text
data/picks_variant_m/2026/week_01.jsonl
```

Ten plik zawiera wszystkie mecze kolejki z tagami:

```text
NEUTRAL / VALUE PLAY / GOW / GOM / GOY
```

3. Dopiero teraz odpal Variant B:

```powershell
python scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof
```

4. Otworz:

```text
research/variant_b_week_flow/2026/week_01/summary.md
```

5. Jesli nie ma `VALUE PLAY`, `GOW`, `GOM`, `GOY`, koniec pracy na ten dzien.

6. Jesli sa kandydaci, dla kazdego meczu osobno wyslij do GPT:

- plik `docs/variant_b_final_gpt_research_prompt.md`;
- krotki wrapper z `docs/variant_b_gpt_short_wrapper.md`;
- dane meczu: sezon, week, data, away, home, venue, selected team, spread, price, book jesli juz znasz.

7. Odpowiedz GPT zapisujemy jako research snapshot.

8. Wpisz reczny quote z booka do:

```text
data/market_quotes/2026/week_01.jsonl
```

9. Odpal ponownie Variant B i sprawdz, czy gate nadal pokazuje `HOLD`, czy pick jest blizej finalnej decyzji:

```powershell
python scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof
```

### Sroda - refresh przed Thursday Night Football

Robimy tylko mecze czwartkowe oraz kazdy pick, ktory ma status VP/GOW/GOM/GOY.

1. Nie wysylaj pelnych 19 punktow od zera.

2. Sprawdz delty:

- czy spread albo cena sie zmienily;
- czy quote nadal jest grywalny;
- czy pojawily sie nowe injury reports;
- czy sa wazne roster moves;
- czy pogoda ma znaczenie;
- czy GPT research wskazal nowe ryzyko.

3. Jesli quote sie zmienil, popraw `data/market_quotes/...`.

4. Odpal ponownie:

```powershell
python scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof
```

5. Dla meczu czwartkowego ustaw status:

```text
WAIT / WATCH / HOLD / READY_FOR_FINAL_CHECK
```

### Czwartek - finalny check dla meczu czwartkowego

Dotyczy tylko meczow granych w czwartek.

1. Kilka godzin przed kickoffem sprawdz:

- finalny quote z booka;
- czy cena nadal miesci sie w acceptable frontier;
- inactives;
- injury status;
- weather;
- late roster news.

2. Wpisz aktualny quote do pliku quote.

3. Odpal flow.

4. Finalna decyzja:

```text
PASS - mozna wpisac do ledgeru / WATCH - jeszcze nie / HOLD - nie gramy / NO BET
```

5. Po meczu uzupelnij wynik i pozniej closing line / CLV, jesli masz dane.

### Piatek - refresh pod niedziele

Dotyczy glownie meczow niedzielnych.

1. Nie rob pelnego audytu GPT od nowa.

2. Aktualizuj tylko:

- injury reports po treningach;
- status questionable / doubtful / out;
- line movement;
- quote z booka;
- pogode;
- roster moves;
- public splits, jesli sa dostepne.

3. Jesli zmienila sie linia albo cena, zaktualizuj quote file.

4. Odpal flow i sprawdz, czy pick nadal przechodzi warunki.

### Sobota - pre-final dla niedzieli

To jest przygotowanie przed glownym dniem meczowym.

1. Sprawdz, czy kazdy niedzielny kandydat ma:

- GPT research snapshot;
- aktualny quote z booka;
- timestamp quote;
- sprawdzony spread i price;
- brak twardych blockerow;
- znane injury concerns;
- pogode oceniona, jesli ma znaczenie.

2. Odpal flow.

3. Picki podziel na:

```text
READY_FOR_SUNDAY_CHECK
WATCH
HOLD
NO BET
```

### Niedziela - finalny check dla meczow niedzielnych

Dotyczy meczow niedzielnych.

1. Kilka godzin przed kickoffem sprawdz:

- inactives;
- finalny quote;
- betslip albo realny executable status;
- weather;
- late line movement.

2. Zaktualizuj quote file.

3. Odpal flow.

4. Finalny werdykt:

```text
PASS / WATCH / HOLD / NO BET
```

5. Po zakonczeniu meczow uzupelnij wynik, closing line i CLV, jesli dane sa dostepne.

### Poniedzialek - finalny check dla Monday Night Football

Dotyczy tylko meczow poniedzialkowych.

1. Rano / w poludnie zrob delta refresh:

- kontuzje;
- roster;
- pogoda;
- rynek;
- quote.

2. Kilka godzin przed kickoffem zrob finalny check jak w niedziele.

3. Odpal flow.

4. Finalny werdykt:

```text
PASS / WATCH / HOLD / NO BET
```

5. Po meczu uzupelnij wynik i closing data.

### Wtorek po kolejce - review

1. Zapisz wyniki pickow.

2. Uzupelnij:

- closing line;
- closing price;
- CLV;
- wynik zakladu;
- czy decyzja byla dobra procesowo.

3. Oznacz bledy:

```text
model error
market error
injury miss
weather miss
bad quote
bad timing
process mistake
good no-bet
```

4. Dopiero po review przechodzimy do kolejnej kolejki.

## Kiedy uzywamy GPT

Pelny GPT 19-punktowy research:

- tylko po znalezieniu VP/GOW/GOM/GOY;
- najlepiej we wtorek;
- jeden raz dla meczu.

GPT delta refresh:

- sroda/czwartek dla meczu czwartkowego;
- piatek/sobota/niedziela dla meczow niedzielnych;
- poniedzialek dla MNF.

Delta refresh ma sprawdzac tylko zmiany od poprzedniego snapshotu.

## Minimalny prompt do daily refresh GPT

```text
Uzyj poprzedniego research snapshotu jako baseline. Nie rob pelnego audytu 19 punktow od zera.

Mecz:
- Season:
- Week:
- Date:
- Away:
- Home:
- Selected team:
- Market: full-game spread
- Poprzedni snapshot:
- Aktualny check time:

Sprawdz tylko delty:
- market_move_notes: line/price/book changes
- injury_role_notes: nowe injury reports, inactives, status changes
- weather_notes: game-window forecast changes
- roster_change_check: transactions, depth chart, inactives
- public_bias/tickets_handle, jesli dostepne
- schedule_spot_notes tylko jesli pojawily sie nowe travel/acclimation informacje
- matchup_specific_risk i game_script_risk tylko jesli pojawily sie nowe informacje

Zwroc:
changed_items:
unchanged_items:
new_blockers:
resolved_blockers:
manual_fields_to_update:
recommended_status: WATCH / RECHECK / WAIT / READY_FOR_LOCAL_GATE

Nie dawaj finalnego picka. Nie rekomenduj zakladu. Tylko aktualizacja procesu.
```

## Prosta decyzja operacyjna

```text
Brak VP/GOW/GOM/GOY = nie analizujemy dalej.
VP/GOW/GOM/GOY bez GPT research = kandydat, nie pick.
GPT research bez realnego quote = nadal HOLD.
Quote bez timestampu/booka = nadal HOLD.
Kontuzje/inactives nieaktualne = WATCH albo HOLD.
Finalny quote poza limitem = NO BET.
Wszystkie bramki OK = PASS do ledgeru.
```
