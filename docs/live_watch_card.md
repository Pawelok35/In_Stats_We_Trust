# Live Watch Card

## Cel

`live_watch_card` ma byc szybka karta decyzyjna do uzycia w trakcie meczu NFL, szczegolnie po Q3. Nie ma zastapic pelnego modelu live odds. Ma odpowiedziec na jedno praktyczne pytanie:

> Czy pregame underdog, ktory prowadzi w Q3, jest nadal wart zagrania live ML przy aktualnej cenie z booka?

Karta pracuje na historycznej mapie stanow z `nfl_data_py` oraz recznie wpisanej cenie live z booka. Bez archiwalnych live odds nie traktujemy tego jako dowodu zyskownosci live bettingu, tylko jako filtr decyzyjny i price discipline.

## Dane Wejsciowe

Minimalne pola, ktore trzeba wpisac podczas meczu:

| Pole | Opis | Przyklad |
|---|---|---|
| `season` | sezon aktualnego meczu | `2026` |
| `week` | tydzien | `1` |
| `game_id` | identyfikator meczu, jesli znany | `2026_01_DAL_PHI` |
| `underdog_team` | druzyna, ktora byla underdogiem pregame | `DAL` |
| `underdog_side` | `home` albo `away` | `away` |
| `pregame_spread_abs` | absolutna wartosc spreadu underdoga | `6.5` |
| `snapshot` | moment decyzji | `Q3` |
| `underdog_margin_now` | iloma punktami underdog prowadzi | `4` |
| `live_ml_price` | aktualna cena moneyline z booka | `-120` |
| `book` | book lub opis zrodla ceny | `manual_multi_book` |
| `decision_ts_utc` | czas zapisu decyzji | `2026-09-13T02:44:00Z` |

Opcjonalne pola:

| Pole | Opis |
|---|---|
| `live_spread_line` | live spread, jesli book pokazuje atrakcyjna linie |
| `live_spread_price` | cena live spread |
| `notes` | kontuzje, weather, QB status, game script |
| `screen_count` | ile bookow sprawdzono |
| `best_live_ml_price` | najlepsza cena z kilku bookow |

## Buckety

Karta ma przypisac sytuacje do bucketow z badania 2017-2025:

Pregame spread underdoga:

| Bucket | Warunek |
|---|---|
| `<=3` | underdog +3 lub mniej |
| `3.5-7` | underdog od +3.5 do +7 |
| `7.5+` | underdog +7.5 lub wiecej |

Prowadzenie po Q3:

| Bucket | Warunek |
|---|---|
| `1-3` | prowadzi 1-3 pkt |
| `4-7` | prowadzi 4-7 pkt |
| `8+` | prowadzi 8+ pkt |

Lokalizacja:

| Bucket | Warunek |
|---|---|
| `home dog` | underdog gra u siebie |
| `away dog` | underdog gra na wyjezdzie |

Fair ML bucket:

| Bucket | Warunek |
|---|---|
| `favorite fair` | modelowa/fair win probability powyzej 50% |
| `plus-money fair` | modelowa/fair win probability ponizej 50% |

Na start fair bucket moze pochodzic z historycznej tabeli `research/in_game_underdog_study_2017_2025.md`. Pozniej mozemy dodac live `wp` z play-by-play albo wlasny model.

## Logika Decyzji

Podstawowy algorytm:

1. Znajdz Q3 bucket po `pregame_spread_abs`, `underdog_margin_now` i `underdog_side`.
2. Odczytaj historyczne `cases`, `su_win_rate` i `break_even_live_ml`.
3. Jesli `cases < 30`, decyzja domyslna: `NO BET - sample too small`.
4. Jesli `su_win_rate < 55%`, decyzja domyslna: `NO ML - historical win rate too low`.
5. Jesli cena live ML jest lepsza niz `break_even_live_ml`, decyzja: `PLAY ML WATCH`.
6. Jesli cena live ML jest gorsza lub rowna break-even, decyzja: `PRICE TOO SHORT`.

Interpretacja ceny:

| Przyklad | Znaczenie |
|---|---|
| Break-even `-138`, book daje `+100` | cena lepsza, potencjalny play |
| Break-even `-138`, book daje `-120` | cena lepsza, potencjalny play |
| Break-even `-138`, book daje `-160` | cena za krotka, no bet |
| Break-even `+133`, book daje `+150` | cena lepsza, potencjalny play |
| Break-even `+133`, book daje `+110` | cena za krotka, no bet |

## Aktualne Wnioski Q3 Z Badania 2017-2025

Najmocniejsze stany obserwacyjne:

| Stan Q3 | Cases | SU Win% | Break-even ML | Robocza Decyzja |
|---|---:|---:|---:|---|
| underdog `<=3`, away dog, lead `8+` | 101 | 90.1% | `-910` | ML watch, ale czesto cena bedzie za droga |
| underdog `<=3`, home dog, lead `8+` | 95 | 92.6% | `-1257` | ML watch, ale cena prawie zawsze bedzie bardzo droga |
| underdog `3.5-7`, away dog, lead `8+` | 85 | 88.2% | `-750` | ML watch |
| underdog `3.5-7`, home dog, lead `8+` | 50 | 82.0% | `-456` | ML watch |
| underdog `3.5-7`, home dog, lead `4-7` | 37 | 78.4% | `-362` | ML watch |
| underdog `7.5+`, away dog, lead `8+` | 32 | 78.1% | `-357` | ML watch |

Stany slabe albo wymagajace ostroznosci:

| Stan Q3 | Cases | SU Win% | Break-even ML | Robocza Decyzja |
|---|---:|---:|---:|---|
| underdog `<=3`, home dog, lead `1-3` | 32 | 46.9% | `+113` | no ML |
| underdog `3.5-7`, away dog, lead `1-3` | 31 | 51.6% | `-107` | no ML |
| underdog `7.5+`, away dog, lead `4-7` | 31 | 54.8% | `-121` | no ML / za slabe |

## Ograniczenia

- `nfl_data_py` nie daje historycznych wykonanych live moneyline ani live spread lines.
- `Break-even live ML` pochodzi z historycznego SU win rate dla bucketu, nie z rynku.
- To nie jest jeszcze proof P&L.
- Do proof potrzebujemy recznego albo automatycznego zapisu rzeczywistej ceny live z booka przed decyzja.
- Live spread wymaga osobnej logiki, bo nie mamy archiwalnych live spreadow do pelnego backtestu.

## Docelowy Output Skryptu

Przyszly skrypt powinien zwracac cos w tym stylu:

```text
LIVE WATCH CARD
Game: DAL at PHI
Pregame underdog: DAL +6.5
Snapshot: Q3
Underdog lead: 4
Bucket: spread 3.5-7 / lead 4-7 / away dog

Historical cases: 50
Historical SU: 29-21
Historical SU win rate: 58.0%
Break-even live ML: -138
Book live ML: -120

Decision: PRICE SENSITIVE ML WATCH
Reason: book price -120 is better than historical break-even -138.
Proof status: manual live price required.
```

## Jak Odpalac

Skrypt:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_card.py --season 2026 --week 1 --game-id 2026_01_DAL_PHI
```

## Skanowanie Tygodnia Po Q3

Najwygodniejszy tryb w trakcie live:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_card.py --season 2026 --week 1 --list-candidates
```

Skrypt sam przechodzi po meczach z danego tygodnia i pokazuje tylko te, gdzie pregame underdog prowadzi w wybranym snapshocie.

Output zawiera:

- `game_id`,
- underdoga i jego pregame spread,
- aktualny lead,
- `binary_path`,
- model/prog uzyty do decyzji,
- historyczne `cases`,
- historyczny `SU Win%`,
- minimalna cene decimal do EV+,
- strong EV+ decimal,
- decyzje bez ceny live.

Mozesz filtrowac po druzynie:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_card.py --season 2026 --week 1 --list-candidates --team DAL
```

Bez ceny live skrypt pokazuje tylko prog:

```text
Fair price
Minimum EV+ price
Strong EV+ price
Decision: WATCH_PRICE_REQUIRED
```

To jest tryb do uzycia, gdy chcesz tylko wiedziec, jaka minimalna cena musi pojawic sie u booka.

## Odpalanie Z Cena Decimal

Jesli book pokazuje kurs europejski/decimal, np. `1.90`:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_card.py `
  --season 2026 `
  --week 1 `
  --game-id 2026_01_DAL_PHI `
  --live-decimal 1.90 `
  --book MANUAL_MULTI_BOOK `
  --notes "Q3 live check"
```

## Odpalanie Z Cena American

Jesli book pokazuje cene amerykanska, np. `-120` albo `+145`:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_card.py `
  --season 2026 `
  --week 1 `
  --game-id 2026_01_DAL_PHI `
  --live-ml -120 `
  --book MANUAL_MULTI_BOOK
```

Nie podawaj jednoczesnie `--live-decimal` i `--live-ml`.

## Tryb Testowy Bez Zapisu

Do sprawdzania historycznych meczow albo testow technicznych uzywaj `--no-ledger`:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_card.py `
  --season 2025 `
  --week 1 `
  --game-id 2025_01_KC_LAC `
  --live-decimal 1.50 `
  --book TEST_MANUAL `
  --no-ledger
```

## Gdzie Zapisuje Ledger

Domyslnie kazde uruchomienie zapisuje rekord JSONL:

```text
data/live_watch/{season}/week_{week}.jsonl
```

Przyklad:

```text
data/live_watch/2026/week_01.jsonl
```

Tryb `--list-candidates` niczego nie zapisuje. Ledger zapisuje dopiero konkretna karta z `--game-id`.

## Rozliczanie Po Meczu

Po zakonczeniu meczow rozliczasz live watch ledger:

```powershell
.\.venv\Scripts\python.exe scripts\settle_live_watch.py --season 2026 --week 1
```

Domyslnie skrypt czyta:

```text
data/live_watch/2026/week_01.jsonl
```

I zapisuje:

```text
data/live_watch/2026/week_01_settled.jsonl
data/live_watch/2026/week_01_settlement.md
```

Rozliczane jako realne zagrania sa tylko decyzje:

- `PLAY_ML`
- `STRONG_PLAY_ML`

Pozostale decyzje sa traktowane jako `NO BET`, ale nadal zostaja w raporcie, zeby bylo widac, co system odrzucil.

Profit liczony jest przy stawce `1u`:

| Wynik | Profit |
|---|---:|
| wygrany ML po kursie `1.90` | `+0.90u` |
| przegrany ML | `-1.00u` |
| no bet | `0.00u` |

Raport settlementu pokazuje tez rozbicie wedlug `model_source`:

```text
combined_flow_q3_lead
margin_trajectory_q3_lead
delta_trajectory_q3_lead
binary_path_micro_spread
binary_path_q3_lead
broad_q3_bucket
unknown
```

Dzieki temu po kilku tygodniach mozemy sprawdzic, czy faktycznie najlepszy jest micro path, czy lepiej zostac przy samym binary path.

## Weekly Review

Po settlement mozna wygenerowac ranking modeli:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_weekly_review.py --season 2026 --week 1
```

Domyslnie czyta:

```text
data/live_watch/2026/week_01_settled.jsonl
```

I zapisuje:

```text
data/live_watch/2026/week_01_weekly_review.md
```

Review pokazuje:

- ranking `model_source`,
- liczbe rekordow,
- liczbe realnych playow,
- W-L,
- profit units,
- ROI,
- sredni offered EV,
- srednia liczbe historycznych przypadkow,
- flage decyzyjna.

Flagi:

| Flaga | Znaczenie |
|---|---|
| `NO_SETTLED_PLAYS` | brak rozliczonych zagran |
| `KEEP_OBSERVING_SMALL_SAMPLE` | za malo playow, nic nie zmieniac |
| `TIGHTEN_BUFFER` | podniesc wymagany bufor EV |
| `TIGHTEN_OR_DISABLE` | rozwazyc pauze lub mocne zaostrzenie modelu |
| `RAISE_PLAY_BUFFER` | edge jest za cienki, podniesc `--play-buffer` |
| `KEEP` | brak zmiany zasad |

## Week Flow

Po zakonczeniu tygodnia mozna wykonac settlement i weekly review jednym poleceniem:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_week_flow.py --season 2026 --week 1
```

To odpala kolejno:

```text
scripts/settle_live_watch.py
scripts/live_watch_weekly_review.py
```

Opcje:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_week_flow.py --season 2026 --week 1 --min-review-plays 5
```

Mozna pominac settlement, jesli juz byl wykonany:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_week_flow.py --season 2026 --week 1 --skip-settlement
```

Mozna pominac review:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_week_flow.py --season 2026 --week 1 --skip-review
```

Rekord zawiera:

- timestamp utworzenia,
- sezon i tydzien,
- game_id,
- underdoga pregame,
- wynik i prowadzenie w snapshocie,
- bucket historyczny,
- cene live z booka,
- fair price,
- minimalna cene EV+,
- strong EV+ price,
- finalna decyzje.

## Decyzje Skryptu

| Decyzja | Znaczenie |
|---|---|
| `WATCH_PRICE_REQUIRED` | underdog spelnia warunek obserwacji, ale nie wpisano ceny live |
| `STRONG_PLAY_ML` | cena live przebija prog strong EV+ |
| `PLAY_ML` | cena live przebija minimalny prog EV+ |
| `THIN_EDGE_NO_BET` | cena jest minimalnie ponad fair, ale bez wystarczajacego bufora |
| `PRICE_TOO_SHORT` | cena jest za niska wzgledem fair |
| `NO_ML_LOW_WIN_RATE` | bucket historycznie wygrywa za rzadko |
| `NO_BET_SMALL_SAMPLE` | za malo przypadkow w bucketcie |
| `NO_WATCH_NOT_LEADING` | pregame underdog nie prowadzi w danym snapshocie |
| `NO_BET_NO_BUCKET` | brak dopasowanego bucketu historycznego |

## Flow Path + Micro Spread Filter

Obecna wersja najpierw probuje uzyc combined flow path, czyli polaczenia:

```text
wynik samej kwarty + stan sumaryczny po tej kwarcie
```

Przyklad:

```text
P1_WIN_AFTER_Q1_WIN__P2_NOT_WIN_AFTER_Q2_WIN__P3_WIN_AFTER_Q3_WIN__Q3_LEAD_8+
```

To oznacza:

```text
underdog wygral sama Q1 i prowadzil po Q1,
nie wygral samej Q2, ale nadal prowadzil po H1,
wygral sama Q3 i prowadzil po Q3 przewaga 8+.
```

Jesli flow path ma za mala probe, skrypt probuje sciezki binarnej z micro bucketem spreadu:

```text
Q1_WIN__Q2_WIN__Q3_WIN__Q3_LEAD_8+__SPREAD_2-3
Q1_WIN__Q2_WIN__Q3_WIN__Q3_LEAD_8+__SPREAD_3.5-4.5
Q1_NOT_WIN__Q2_NOT_WIN__Q3_WIN__Q3_LEAD_4-7__SPREAD_2-3
```

Jesli ta probka jest za mala, skrypt wraca do samej sciezki binarnej:

```text
Q1_WIN__Q2_WIN__Q3_WIN__Q3_LEAD_8+
Q1_NOT_WIN__Q2_WIN__Q3_WIN__Q3_LEAD_1-3
Q1_NOT_WIN__Q2_NOT_WIN__Q3_WIN__Q3_LEAD_4-7
```

`NOT_WIN` oznacza remis albo przegrywanie po danym kwartale.

Domyslne zrodla progow:

```text
research/quarter_path_underdog_study_2015_2025_flow_q3_leads.csv
research/quarter_path_underdog_study_2015_2025_q3_micro.csv
research/quarter_path_underdog_study_2015_2025_binary_q3_leads.csv
```

Fallback:

```text
1. Jesli flow path ma `cases >= --min-cases`, skrypt uzywa flow path.
2. Jesli flow path ma za mala probe albo nie ma dopasowania, skrypt probuje margin trajectory.
3. Jesli margin trajectory ma za mala probe albo nie ma dopasowania, skrypt probuje delta trajectory.
4. Jesli delta trajectory ma za mala probe albo nie ma dopasowania, skrypt probuje micro path.
5. Jesli micro path ma za mala probe albo nie ma dopasowania, skrypt probuje binary path.
6. Jesli binary path ma za mala probe albo nie ma dopasowania, skrypt wraca do broad Q3 bucket.
7. Broad Q3 bucket nadal pochodzi z `research/in_game_underdog_study_2017_2025.csv`.
```

W output zobaczysz:

```text
Model source: combined_flow_q3_lead
```

albo:

```text
Model source: margin_trajectory_q3_lead
```

albo:

```text
Model source: delta_trajectory_q3_lead
```

albo:

```text
Model source: binary_path_micro_spread
```

albo:

```text
Model source: binary_path_q3_lead
```

albo:

```text
Model source: broad_q3_bucket
```

To mowi, czy prog EV pochodzi z pelnego przebiegu kwartowego, trajektorii przewagi, trajektorii zmiany przewagi, konkretnej sciezki Q1/Q2/Q3 z micro spreadem, samej sciezki Q1/Q2/Q3, czy z szerszego bucketu Q3.

## Parametry Ryzyka

Domyslne ustawienia:

| Parametr | Domyslnie | Znaczenie |
|---|---:|---|
| `--min-cases` | `30` | minimalna liczba historycznych przypadkow |
| `--min-win-rate` | `0.55` | minimalny SU win rate bucketu |
| `--play-buffer` | `0.03` | minimalny bufor EV do decyzji `PLAY_ML` |
| `--strong-buffer` | `0.07` | bufor EV do decyzji `STRONG_PLAY_ML` |

Przyklad ostrzejszej wersji:

```powershell
.\.venv\Scripts\python.exe scripts\live_watch_card.py `
  --season 2026 `
  --week 1 `
  --game-id 2026_01_DAL_PHI `
  --live-decimal 1.85 `
  --min-cases 50 `
  --play-buffer 0.05 `
  --strong-buffer 0.10
```

## Jak To Obslugiwac W Praktyce

1. Po Q3 sprawdzasz, czy mecz ma pregame underdoga prowadzacego.
2. Odpalasz skrypt bez ceny live, z `--season`, `--week`, `--game-id`.
3. Skrypt pokazuje minimalna cene EV+.
4. Patrzysz u booka na live ML underdoga.
5. Odpalasz skrypt drugi raz z `--live-decimal` albo `--live-ml`.
6. Jesli decyzja to `PLAY_ML` albo `STRONG_PLAY_ML`, cena przeszla filtr historyczny.
7. Ledger zapisuje dowod decyzji.

## Aktualny Status Implementacji

Pierwsza wersja istnieje:

```text
scripts/live_watch_card.py
```

Zakres obecnej wersji:

- Q1, H1 albo Q3 jako snapshot, domyslnie Q3,
- skanowanie tygodnia przez `--list-candidates`,
- automatyczny odczyt wyniku, spreadu i underdoga z `nfl_data_py`,
- combined flow path jako pierwszy filtr EV,
- margin trajectory jako drugi filtr EV,
- delta trajectory jako trzeci filtr EV,
- binary path Q1/Q2/Q3 + micro spread jako kolejny filtr EV,
- fallback do samego binary path, jesli micro path ma za mala probe,
- fallback do szerokiego bucketu Q3, jesli binary path ma za mala probe,
- historyczna mapa Q3 z `research/in_game_underdog_study_2017_2025.csv`,
- reczna cena live z booka,
- EV, fair price, minimal EV+ price i strong EV+ price,
- zapis JSONL do `data/live_watch/`.
- settlement po meczu przez `scripts/settle_live_watch.py`.

Pomocniczy plik notatek dziennych:

```text
config/live_watch_games.yaml
```

Na razie jest to checklist/notes file. Skrypt go jeszcze nie wymaga.

Ograniczenie obecnej wersji:

- logika historyczna jest zbudowana na Q3 bucket map, wiec Q1/H1 traktujemy ostroznie dopoki nie zrobimy osobnych bucketow dla Q1/H1.
