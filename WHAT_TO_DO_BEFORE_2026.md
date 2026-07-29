# What To Do Before NFL 2026

To jest prosta lista rzeczy, ktore musimy miec gotowe przed startem sezonu 2026.

## 1. Realne Quote Z Booka

Rytm wpisywania:

```text
przed sezonem: raz w tygodniu
w sezonie od Week 1: codziennie we wtorek, srode, czwartek, piatek, sobote i niedziele przed meczami
```

Wpisujemy:

```text
book: 
spread:
price:
timestamp:
executable_status:
target_stake: 100 $
house_rules_checked:
```

Znaczenie pol jednym zdaniem:

```text
book = konkretny bukmacher albo zrodlo, z ktorego pochodzi kurs.
spread = aktualny spread dla selected_team, np. LA -3.0 albo SF +3.0.
price = cena przy tym spreadzie, np. -110 albo 1.91.
timestamp = dokladny czas sprawdzenia kursu.
executable_status = czy kurs byl tylko widoczny, sprawdzony w betslipie, czy faktycznie zaakceptowany.
target_stake = stawka, dla ktorej sprawdzasz, czy kurs jest realnie dostepny.
house_rules_checked = czy sprawdziles podstawowe zasady rozliczenia rynku u danego booka.
```

Procedura dla pregame.com:

```text
1. Robie screen tabeli NFL z pregame.com.
2. Wrzucam screen do GPT z promptem ponizej.
3. GPT przepisuje screen do YAML.
4. Wklejam wynik tutaj do Codex.
5. Codex poprawia format YAML, zapisuje snapshot i pozniej przerabia go na market_quotes JSONL.
```

Prompt do GPT:

```text
Przepisz dane z zaÅ‚Ä…czonego screena z liniami NFL z pregame.com do dokÅ‚adnego formatu YAML.

Zasady:
- ZwrÃ³Ä‡ tylko poprawny YAML, bez komentarzy i bez dodatkowego tekstu.
- book_snapshot fields muszÄ… byÄ‡ wciÄ™te o 2 spacje.
- Sekcja games musi byÄ‡ listÄ… YAML.
- KaÅ¼dy mecz musi zaczynaÄ‡ siÄ™ od "  - game_date_local:".
- Wszystkie pola meczu muszÄ… byÄ‡ wciÄ™te o 4 spacje.
- Zachowaj wszystkie mecze widoczne na screenie.
- Dla nazw druÅ¼yn uÅ¼yj skrÃ³tÃ³w NFL: SF, LA, NE, SEA, BUF, HOU itd.
- JeÅ¼eli widzisz +3Â½, zapisz jako 3.5.
- JeÅ¼eli widzisz -3Â½-105, zapisz spread -3.5 i price -105.
- JeÅ¼eli widzisz pk, zapisz spread 0.
- JeÅ¼eli widzisz o48Â½, zapisz total_over 48.5.
- JeÅ¼eli widzisz u48Â½-107, zapisz total_under 48.5 i total_under_price -107.
- JeÅ¼eli cena przy spreadzie, moneyline albo totalu nie jest widoczna, wpisz null.
- Nie zakÅ‚adaj domyÅ›lnej ceny -110.
- Nie rekonstruuj brakujÄ…cej przeciwnej strony spreadu.
- JeÅ›li spread obu stron jest matematycznie symetryczny, wpisz spread_pair_status: "symmetric".
- JeÅ›li spread obu stron nie jest symetryczny, wpisz spread_pair_status: "asymmetric".
- JeÅ›li total over i under sa takie same, wpisz total_pair_status: "symmetric".
- JeÅ›li total over i under sa rozne, wpisz total_pair_status: "asymmetric".
- JeÅ›li nie da siÄ™ jednoznacznie odczytaÄ‡ linii, wpisz null i dodaj game_notes.
- captured_at_utc zostaw null, jeÅ›li nie podaÅ‚em czasu wykonania screena.
- book wpisz "pregame.com".

Format:

book_snapshot:
  book: "pregame.com"
  season: 2026
  week: 1
  captured_at_utc: null
  executable_status: "displayed_unverified"
  target_stake: 100
  house_rules_checked: false

games:
  - game_date_local: "2026-09-10"
    game_time_local: "02:20 AM"
    away: "NE"
    home: "SEA"
    away_moneyline: 170
    home_moneyline: -190
    away_spread: 3.5
    away_spread_price: -107
    home_spread: -3.5
    home_spread_price: null
    spread_pair_status: "symmetric"
    total_over: 43.5
    total_over_price: null
    total_under: 44.5
    total_under_price: null
    total_pair_status: "asymmetric"
    game_notes: null

Teraz przepisz caÅ‚y screen do tego formatu.
```

Gdzie wpisujemy:

```text
data/market_quotes/2026/week_XX.jsonl
```

Po co:

```text
bez realnego quote Variant B bedzie trzymal pick jako HOLD
```

Status:

```text
DO ZROBIENIA PRZY KAZDYM KANDYDACIE VP/GOW/GOM/GOY
```

## 2. Rutyna GPT 19 Punktow

Krotko:

```text
Pelne 19 punktow GPT robimy tylko dla VP/GOW/GOM/GOY, a w kolejne dni tylko delta refresh.
```

<details>
<summary>Rozwin punkt 2 - pelna rutyna GPT 19 punktow</summary>

Zasada:

```text
pelne 19 punktow robimy tylko dla VALUE PLAY / GOW / GOM / GOY
```

Nie robimy pelnego researchu dla `NEUTRAL`.

Pliki:

```text
docs/variant_b_final_gpt_research_prompt.md
docs/variant_b_gpt_short_wrapper.md
```

Co trzeba robic:

```text
wtorek: pelny research GPT dla kandydatow
sroda/piatek/sobota: tylko delta refresh
dzien meczu: final check
```

Pelny research GPT robimy tylko wtedy, gdy basic model znajdzie:

```text
VALUE PLAY
GOW
GOM
GOY
```

Nie wysylamy GPT meczow `NEUTRAL`, bo to marnuje czas i miesza proces.

**2A. Co wysylam do GPT we wtorek**

Do GPT wrzucam jako zalacznik:

```text
docs/variant_b_final_gpt_research_prompt.md
```

Nastepnie wklejam krotka wiadomosc:

```text
Uzyj zalaczonego pliku jako glownej instrukcji dla frameworka Variant B.

Nie dawaj picka ani rekomendacji bettingowej.
Przygotuj structured research dla 19 punktow audytu.
Oznaczaj braki jako MISSING, UNKNOWN, NOT_ASSESSABLE, PENDING_NOT_DUE albo POST_EVENT_ONLY.
Nie licz EV, CLV, no-chase ani finalnego gate, jesli brakuje wymaganych danych.
Nie wymyslaj faktow.

Mecz do analizy:
- Season: 2026
- Week: [WEEK]
- Date: [GAME_DATE]
- Away: [AWAY_TEAM]
- Home: [HOME_TEAM]
- Venue: znajdz oficjalne venue i potwierdz zrodlem
- Market: full-game spread
- Selected team: [SELECTED_TEAM]
- Current spread selected team: [SPREAD]
- Current price: [PRICE]
- Book/source: [BOOK_OR_SOURCE]
- Quote timestamp UTC: [QUOTE_TIMESTAMP_OR_UNKNOWN]
- Executable status: [displayed_unverified / betslip_checked / accepted_ticket / unknown]
- Model version: variant_m
- Model fair margin selected team raw: [MODEL_MARGIN]
- Model fair margin rounded to 0.5: [MODEL_MARGIN_ROUNDED]
- Edge vs line raw: [EDGE]
- Model tag: [VALUE PLAY / GOW / GOM / GOY]
- p_cover: [P_COVER]
- p_push: [P_PUSH]
- p_loss: [P_LOSS]
- margin_pmf_available: true/false
- acceptable_quote_frontier_available: true/false

Zwroc wynik w strukturze:
audit_metadata:
points 1-19:
summary:
```

**2B. Co potem wklejam do Codex**

Po odpowiedzi GPT wklejam tutaj caly wynik albo zapisujemy go jako plik:

```text
research/gpt_snapshots/2026/week_XX/[away]_at_[home]_[selected_team]_full_research.md
```

Codex robi wtedy:

```text
1. sprawdza, czy GPT nie wymyslil danych;
2. porownuje z naszym quote/model proof;
3. wypisuje hard blockers;
4. aktualizuje status WATCH / HOLD / READY_FOR_FINAL_CHECK;
5. mowi, czego jeszcze brakuje przed finalnym werdyktem.
```

**2C. Daily Delta Refresh**

Codziennie nie robimy od nowa 19 punktow.

Po pelnym wtorkowym researchu GPT zlecam tylko delta refresh:

```text
Uzyj poprzedniego research snapshotu jako baseline.
Nie rob pelnego audytu 19 punktow od zera.
Sprawdz tylko zmiany od ostatniego snapshotu.

Mecz:
- Season: 2026
- Week: [WEEK]
- Date: [GAME_DATE]
- Away: [AWAY_TEAM]
- Home: [HOME_TEAM]
- Selected team: [SELECTED_TEAM]
- Market: full-game spread
- Poprzedni snapshot: [DATA/CZAS]
- Aktualny check time: [DATA/CZAS]

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

Nie dawaj finalnego picka.
Nie rekomenduj zakladu.
Tylko aktualizacja procesu.
```

**2C-1. Podzial Na Dni Tygodnia**

**Wtorek**

Cel:

```text
pierwszy pelny research GPT dla kandydatow VP/GOW/GOM/GOY
```

Robie:

```text
1. Odpalam basic model i Variant B.
2. Sprawdzam summary.md.
3. Jesli sa VALUE PLAY / GOW / GOM / GOY, dla kazdego meczu osobno wysylam GPT pelny prompt 19 punktow.
4. Zapisuje albo wklejam odpowiedz GPT do Codex.
5. Codex sprawdza hard blockers i missing_data.
```

GPT:

```text
pelny audyt 19 punktow
```

Nie robie:

```text
nie zlecam pelnego researchu dla NEUTRAL
```

**Sroda**

Cel:

```text
delta refresh dla meczu czwartkowego oraz kandydatow, ktore maja nowe informacje
```

Robie:

```text
1. Sprawdzam, czy zmienila sie linia/price z punktu 1.
2. Dla meczu czwartkowego wysylam GPT daily delta refresh.
3. Dla niedzielnych meczow tylko jesli pojawily sie wazne newsy.
```

GPT:

```text
delta refresh, nie pelne 19 punktow
```

Najwazniejsze delty:

```text
market move
injury report
weather
roster
travel/schedule spot
```

**Czwartek**

Cel:

```text
final check dla Thursday Night Football
```

Robie:

```text
1. Aktualizuje quote z booka/pregame.com.
2. Sprawdzam injury/inactives, jesli sa dostepne.
3. Zlecam GPT final delta refresh tylko dla meczu czwartkowego.
4. Wklejam odpowiedz do Codex.
5. Codex daje status: PASS / WATCH / HOLD / NO BET.
```

GPT:

```text
final delta refresh dla TNF
```

Nie robie:

```text
nie robie pelnego 19-punktowego audytu od nowa, chyba ze wtorkowego snapshotu w ogole nie bylo
```

**Piatek**

Cel:

```text
glowny refresh pod mecze niedzielne
```

Robie:

```text
1. Aktualizuje quote z punktu 1.
2. Dla kazdego niedzielnego VP/GOW/GOM/GOY wysylam GPT delta refresh.
3. Skupiam sie na injury reports, roster moves, weather, market move.
4. Wklejam odpowiedz GPT do Codex.
```

GPT:

```text
delta refresh dla niedzielnych kandydatow
```

**Sobota**

Cel:

```text
pre-final check przed niedziela
```

Robie:

```text
1. Sprawdzam, czy kazdy kandydat ma pelny wtorkowy snapshot GPT.
2. Sprawdzam, czy ma aktualny quote.
3. Zlecam GPT tylko krotki delta refresh, jesli sa nowe informacje.
4. Dzielimy mecze na READY_FOR_SUNDAY_CHECK / WATCH / HOLD / NO BET.
```

GPT:

```text
krotki delta refresh tylko dla zmian
```

**Niedziela**

Cel:

```text
final check kilka godzin przed kickoffem dla meczow niedzielnych
```

Robie:

```text
1. Aktualizuje quote.
2. Sprawdzam inactives.
3. Sprawdzam weather.
4. Zlecam GPT final delta refresh tylko jesli sa nowe informacje.
5. Wklejam do Codex.
6. Codex daje finalny status: PASS / WATCH / HOLD / NO BET.
```

GPT:

```text
final delta refresh, nie pelny research
```

W trakcie meczu:

```text
opcjonalnie uzywam Live Scenario po Q1 / H1 / Q3
```

**Poniedzialek**

Cel:

```text
final check dla Monday Night Football
```

Robie:

```text
1. Aktualizuje quote dla MNF.
2. Sprawdzam finalne injury/inactives/weather.
3. Zlecam GPT final delta refresh dla MNF.
4. Wklejam do Codex.
5. Codex daje status PASS / WATCH / HOLD / NO BET.
```

**Wtorek Po Kolejce**

Cel:

```text
review i uczenie systemu
```

Robie:

```text
1. Dopisuje wyniki.
2. Dopisuje closing line / closing price, jesli mam.
3. Odpalam post-event evaluation.
4. Odpalam learning report.
5. Oznaczamy, czy blad byl modelem, quote, procesem, injury, weather czy wariancja.
```

**2D. Kiedy punkt 2 jest wykonany dla meczu**

Punkt 2 uznajemy za wykonany dla konkretnego meczu, gdy mamy:

```text
pelny GPT research 19 punktow dla VP/GOW/GOM/GOY
zapisany snapshot odpowiedzi GPT
liste hard blockers
liste missing_data
quote z punktu 1
decyzje co dalej: WATCH / HOLD / READY_FOR_FINAL_CHECK
```

Status:

```text
PROCES GOTOWY, TRZEBA GO STOSOWAC W SEZONIE
```

</details>

## 3. Injury / Weather / Roster Refresh

Krotko:

```text
Punkt 3 pilnuje rzeczy, ktore zmieniaja sie w tygodniu: injury, inactives, roster, weather, travel i late news.
```

<details>
<summary>Rozwin punkt 3 - injury / weather / roster refresh</summary>

Cel:

```text
nie pozwolic, zeby pick przeszedl finalny gate na starych informacjach
```

Do sprawdzania:

```text
injury reports
inactives
transactions
depth chart changes
weather forecast
travel / schedule spot
late news
```

**3A. Zrodla**

Primary / official:

```text
NFL official injury report
official team injury report
official team transactions
official team depth chart, jesli dostepny
official inactives przed kickoffem
official venue / game status
National Weather Service albo inne wiarygodne zrodlo pogody
```

Secondary / context:

```text
beat reporters
team reporters
ESPN / CBS / Rotowire / fantasy injury pages
public weather services
```

Zasada:

```text
secondary sources moga dawac kontekst, ale confirmed status musi pochodzic z official albo bardzo wiarygodnego zrodla
```

**3B. Co Ma Zwrocic GPT**

Format oczekiwany od GPT:

```yaml
refresh_snapshot:
  game:
    season:
    week:
    away:
    home:
    selected_team:
    check_time_utc:

injury_updates:
  confirmed_out:
  questionable:
  doubtful:
  limited_practice:
  full_practice:
  important_unknowns:
  injury_value_assessment:
    - player:
      team:
      position:
      status:
      role: starter / rotational / backup / special_teams / unknown
      recent_snap_share:
      unit_importance: LOW / MEDIUM / HIGH / CRITICAL / UNKNOWN
      replacement_player:
      replacement_quality: UPGRADE / SIMILAR / DOWNGRADE / MAJOR_DOWNGRADE / UNKNOWN
      matchup_impact:
      model_impact:
      severity: LOW / MEDIUM / HIGH / CRITICAL / UNKNOWN
  source_evidence:

roster_updates:
  transactions:
  depth_chart_changes:
  practice_squad_elevations:
  source_evidence:

weather_updates:
  venue:
  game_window_forecast:
  wind_mph:
  precipitation:
  temperature:
  surface_or_roof_status:
  weather_risk_level: NONE / LOW / MEDIUM / HIGH / UNKNOWN
  source_evidence:

schedule_travel_updates:
  rest_days:
  travel_notes:
  international_or_neutral_site_notes:
  source_evidence:

late_news:
  confirmed_news:
  rumors_or_unconfirmed:
  source_evidence:

impact_on_variant_b:
  new_blockers:
  resolved_blockers:
  fields_to_update:
  recommended_status: WATCH / HOLD / READY_FOR_FINAL_CHECK
```

**3B-1. Jak Oceniamy Wartosc Kontuzji**

Nie kazda kontuzja ma znaczenie bettingowe.

GPT/Codex ma oceniac nie tylko status zawodnika, ale tez jego wartosc:

```text
czy to starter czy rezerwowy
ile gra snapow
czy pozycja jest wazna dla tego matchup
kto go zastepuje
czy replacement jest downgrade
czy kontuzja zmienia game script
czy kontuzja powinna zmienic model/gate
```

Przyklady interpretacji:

```text
starting QB OUT = zwykle CRITICAL
starting LT OUT vs elite pass rush = HIGH / CRITICAL
CB1 OUT vs mocny passing offense = HIGH
WR4 questionable = zwykle LOW
rotational DT OUT = LOW/MEDIUM, zalezy od snap share i depth
kicker/punter injury = HIGH tylko przy potwierdzonym problemie albo slabym replacement
```

Minimalny format oceny jednej kontuzji:

```yaml
player:
team:
position:
status:
role:
recent_snap_share:
replacement_player:
replacement_quality:
matchup_impact:
model_impact:
severity:
source:
```

Zasada:

```text
kontuzja bez roli, snapow, replacement i matchup impact nie jest jeszcze pelnym dowodem
```

**3C. Podzial Na Dni**

Wtorek:

```text
pierwszy baseline injury/weather/roster w pelnym GPT 19 punktow
```

Sroda:

```text
refresh dla TNF i tylko najwazniejsze newsy dla niedzielnych kandydatow
```

Czwartek:

```text
final check TNF: injury, inactives, late roster, weather, quote
```

Piatek:

```text
glowny injury/weather/roster refresh dla niedzielnych meczow
```

Sobota:

```text
pre-final: sprawdzic, czy nie ma nowych OUT/questionable, travel, weather movement
```

Niedziela:

```text
final check kilka godzin przed kickoffem: inactives, weather, late news
```

Poniedzialek:

```text
final check MNF
```

**3D. Co Robi Codex Po Wklejeniu Refreshu**

```text
1. Porownuje refresh z poprzednim snapshotem.
2. Oznacza nowe blockery.
3. Oznacza resolved blockers.
4. Mowi, czy trzeba zmienic quote/model status.
5. Daje status WATCH / HOLD / READY_FOR_FINAL_CHECK.
```

**3E. Kiedy Punkt 3 Jest Wykonany Dla Meczu**

```text
injury status jest aktualny
inactives sa sprawdzone, jesli sa juz due
weather jest sprawdzone dla game-window
roster moves sa sprawdzone
travel/schedule spot nie ma nowego blockera
late news nie zmienia zalozen modelu
```

Status:

```text
DO STOSOWANIA OPERACYJNIE
```

</details>

## 4. Closing Line / Closing Price

Krotko:

```text
Punkt 4 zbiera finalna linie rynku po zamknieciu/tuÅ¼ przed kickoffem, zeby pozniej policzyc CLV i ocenic jakosc decyzji.
```

<details>
<summary>Rozwin punkt 4 - closing line / closing price</summary>

Cel:

```text
sprawdzic, czy nasza decyzja pobila rynek zamkniecia
```

Wpisujemy:

```text
closing_spread
closing_price
book/source
timestamp
```

Znaczenie pol:

```text
closing_spread = finalny spread dla selected_team, np. LA -3.5.
closing_price = finalna cena przy tym spreadzie, np. -110 albo -105.
book/source = skad pochodzi close, np. pregame.com, konkretny book, consensus, screen.
timestamp = kiedy closing snapshot zostal sprawdzony.
```

Po co:

```text
bez closing danych nie policzymy dobrze CLV
```

**4A. Czego Nie Wolno Mieszac**

```text
current quote przed decyzja != closing line
model-generation quote != closing line
screen z wtorku != closing line
closing line nie moze byc inputem do pregame modelu, jesli model powstal wczesniej
```

Closing line jest uzywana po meczu do oceny procesu, nie do pierwotnej decyzji.

**4B. Kiedy Zbieramy Closing**

```text
czwartek: dla TNF tuz przed kickoffem
niedziela: dla meczow niedzielnych kilka minut/godzin przed kickoffem
poniedzialek: dla MNF tuz przed kickoffem
wtorek po kolejce: uzupelniamy braki, jesli mamy wiarygodne zrodlo close
```

Najlepiej:

```text
ostatni dostepny snapshot przed kickoffem
```

Jesli nie mamy idealnego close:

```text
oznaczamy closing_status: APPROXIMATE albo MISSING
```

**4C. Format Closing Snapshot**

Docelowy format:

```yaml
closing_snapshot:
  season:
  week:
  away:
  home:
  selected_team:
  market: full-game spread
  closing_spread:
  closing_price:
  source:
  captured_at_utc:
  closing_status: FINAL / APPROXIMATE / MISSING
  notes:
```

Przyklad:

```yaml
closing_snapshot:
  season: 2026
  week: 1
  away: "SF"
  home: "LA"
  selected_team: "LA"
  market: "full-game spread"
  closing_spread: -3.5
  closing_price: -110
  source: "pregame.com"
  captured_at_utc: "2026-09-11T00:25:00Z"
  closing_status: "APPROXIMATE"
  notes: "Last visible pre-kickoff screen snapshot."
```

**4D. Jak Liczymy CLV**

Z perspektywy selected_team:

```text
clv_points = closing_spread_selected_team - bet_spread_selected_team
```

Interpretacja:

```text
ujemny CLV dla faworyta zwykle dobry, np. bet LA -3.0, close LA -3.5 => -0.5 pkt lepsza cena na bet
dodatni CLV dla doga zwykle dobry, np. bet SF +3.0, close SF +2.5 => -0.5 wedlug wzoru spreadowego, dlatego zawsze patrzymy z perspektywy ceny, ktora zagrales
```

Praktyczna zasada:

```text
CLV ma pokazac, czy zagrales lepsza linie niz closing market.
```

Dlatego przy raportowaniu zapisujemy tez opis tekstowy:

```text
beat_close: true / false / unknown
clv_direction: BETTER_THAN_CLOSE / WORSE_THAN_CLOSE / SAME / UNKNOWN
```

**4E. Co Robi Codex**

Po wklejeniu closing snapshotu Codex:

```text
1. sprawdza, czy close pasuje do meczu i selected_team;
2. zapisuje closing snapshot;
3. liczy CLV points, jesli dane wystarcza;
4. dopisuje dane do post-event evaluation;
5. pokazuje, czy decision beat close.
```

Docelowy output:

```text
closing_snapshots.jsonl
clv_points
post_event_evaluation
```

Status:

```text
DO UZUPELNIANIA PO MECZACH
```

</details>

## 5. Wyniki Po Meczu

Krotko:

```text
Punkt 5 zapisuje finalny wynik meczu, zeby rozliczyc pick, policzyc actual margin i uruchomic post-event evaluation.
```

<details>
<summary>Rozwin punkt 5 - wyniki po meczu</summary>

Po kazdym meczu / kolejce trzeba miec:

```text
home_score
away_score
actual_margin
cover / push / loss
prediction_error
```

**5A. Format Wyniku**

Glowne zrodlo wynikow:

```text
nfl_data_py przez lokalny plik data/schedules/2026.parquet
```

Po kolejce najpierw odpalamy:

```powershell
.\.venv\Scripts\python.exe -m app.cli sync-nfl-results --season 2026
```

Ta komenda odswieza finalne wyniki z `nfl_data_py`.

Reczny fallback/override w `manual_results.jsonl`:

```json
{"season":2026,"week":1,"home_team":"LA","away_team":"SF","home_score":27,"away_score":20}
```

Jeden mecz = jeden wiersz JSON. Reczny plik zostaje tylko jako fallback, gdy `nfl_data_py` nie ma jeszcze wyniku albo trzeba poprawic blad.

Gdzie:

```text
home_score = finalny wynik home team
away_score = finalny wynik away team
```

**5B. Co Liczy System**

Z wyniku system liczy:

```text
actual_margin_selected_team
ats_margin
settlement: COVER / PUSH / LOSS
prediction_error
```

Definicja:

```text
actual_margin_selected_team = selected_team_score - opponent_score
ats_margin = actual_margin_selected_team + selected_team_spread
prediction_error = actual_margin_selected_team - predicted_margin_selected_team
```

Przyklad:

```text
selected_team = LA
spread = -3.0
wynik: LA 27 - SF 20
actual_margin_selected_team = +7
ats_margin = +7 + (-3) = +4
settlement = COVER
```

**5C. Kiedy Wpisujemy Wyniki**

```text
czwartek/noc: po TNF, jesli byl kandydat
niedziela: po zakonczeniu meczow niedzielnych
poniedzialek: po MNF
wtorek po kolejce: pelne uporzadkowanie wynikow
```

Nie trzeba wpisywac wynikow dla wszystkich meczow natychmiast, ale do learning report najlepiej miec komplet kolejki.

**5D. Komenda Po Wynikach**

Najpierw pobierz / odswiez wyniki z `nfl_data_py`:

```powershell
.\.venv\Scripts\python.exe -m app.cli sync-nfl-results --season 2026
```

Potem uruchom post-event evaluation:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_post_event_evaluation.py --season 2026 --week 1
```

Potem:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_learning_report.py
```

**5E. Co Robi Codex**

Po wpisaniu wynikow Codex:

```text
1. sprawdza, czy wynik pasuje do home/away;
2. uruchamia post-event evaluation;
3. sprawdza settlement COVER/PUSH/LOSS;
4. pokazuje prediction error;
5. aktualizuje learning report;
6. oznacza, czy blad byl modelem, procesem, quote, injury/weather czy wariancja.
```

**5F. Kiedy Punkt 5 Jest Wykonany**

Punkt 5 dla kolejki jest wykonany, gdy:

```text
wszystkie mecze z kandydatami VP/GOW/GOM/GOY maja wynik
post-event evaluation zostal odpalony
learning report zostal odswiezony
pending zmienilo sie na SETTLED tam, gdzie wynik jest znany
```

Status:

```text
SKRYPT GOTOWY, GLOWNE WYNIKI BIERZEMY Z NFL_DATA_PY, RECZNY PLIK TO FALLBACK
```

</details>

## 6. Learning Ledger

Krotko:

```text
Learning Ledger to pamiec systemu: zapisuje co wiedzielismy, kiedy to wiedzielismy, jaka byla predykcja, quote, audyt i pozniejszy wynik.
```

<details>
<summary>Rozwin punkt 6 - learning ledger</summary>

Mamy gotowy fundament:

```text
data/learning_ledger/{season}/week_{week}/
```

Co ledger zapisuje:

```text
game
feature_snapshot
market_quote
model_run
model_prediction
audit_result
process_failures
outcome
post_event_evaluation
```

**6A. Po Co Jest Ledger**

Ledger sluzy do tego, zeby po czasie nie zgadywac:

```text
jaka byla linia
jaki byl quote
kiedy powstal model run
jaki byl p_cover / p_push / p_loss
co blokowalo pick
jaki byl finalny wynik
czy model byl dobrze skalibrowany
```

Najwazniejsza zasada:

```text
ledger jest append-only: dopisujemy nowe rekordy, nie nadpisujemy starych
```

**6B. Pliki W Ledgerze**

Pregame:

```text
games.jsonl
feature_snapshots.jsonl
market_quotes.jsonl
model_runs.jsonl
model_predictions.jsonl
audit_results.jsonl
process_failures.jsonl
```

Post-event:

```text
outcomes.jsonl
post_event_evaluations.jsonl
```

Manifesty:

```text
manifest_*.json
post_event_manifest_*.json
```

**6C. Kiedy Uruchamiamy Ledger**

Wtorek / pregame po audycie Variant B:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof --write-learning-ledger
```

Po ostatnim meczu kolejki:

```text
zwykle wtorek wieczor po zakonczeniu MNF
```

Wtedy domykamy punkt 6 dla calej kolejki:

```powershell
.\.venv\Scripts\python.exe -m app.cli sync-nfl-results --season 2026
.\.venv\Scripts\python.exe scripts\variant_b_post_event_evaluation.py --season 2026 --week 1
.\.venv\Scripts\python.exe scripts\variant_b_learning_report.py
```

**6D. Co Jest Zamrazane Pregame**

```text
model_run_id
feature_snapshot_id
market_quote_id
model_prediction_id
audit_id
selected_team
model_version
model_margin
market_spread
p_cover
p_push
p_loss
margin_pmf_path
acceptable_quote_frontier_path
hard blockers
missing data
```

**6E. Co Jest Dopisywane Po Meczu**

```text
outcome_id
home_score
away_score
actual_margin_selected_team
settlement
prediction_error
post_event_evaluation_id
```

**6F. Czego Nie Robimy**

```text
nie poprawiamy starego model runu po meczu
nie zmieniamy starego quote po fakcie
nie usuwamy starych blockerow
nie wpisujemy closing line jako pregame input
nie uczymy modelu z danych, ktore nie byly dostepne przed cutoffem
```

**6G. Kiedy Punkt 6 Jest Wykonany**

Punkt 6 dla kolejki jest wykonany, gdy:

```text
pregame ledger zostal zapisany dla kandydatow VP/GOW/GOM/GOY
ostatni mecz kolejki zostal zakonczony
po meczu outcome/post_event_evaluation zostaly dopisane
learning report widzi rekordy
nie ma potrzeby recznego rekonstruowania decyzji po czasie
```

Komenda tygodniowa:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof --write-learning-ledger
```

Status:

```text
GOTOWE TECHNICZNIE, TRZEBA ZBIERAC DANE W SEZONIE
```

</details>

## 7. Learning Report

Krotko:

```text
Learning Report pokazuje, czy system zbiera dane poprawnie i czy model zaczyna byc kalibrowalny po wynikach.
```

<details>
<summary>Rozwin punkt 7 - learning report</summary>

Raport:

```text
research/variant_b_learning_report.md
```

Komenda:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_learning_report.py
```

Pokazuje:

```text
ile mamy model runs
ile mamy predykcji
ile jest pending
ile settled
jakie sa process failures
kalibracje p_cover po bucketach
```

**7A. Kiedy Odpalamy**

Po pregame ledger:

```text
sprawdzamy, czy model_runs, predictions i audit_results zostaly zapisane
```

Po ostatnim meczu kolejki:

```text
wtorek wieczor po MNF, po sync wynikow i post-event evaluation
```

Komendy:

```powershell
.\.venv\Scripts\python.exe -m app.cli sync-nfl-results --season 2026
.\.venv\Scripts\python.exe scripts\variant_b_post_event_evaluation.py --season 2026 --week 1
.\.venv\Scripts\python.exe scripts\variant_b_learning_report.py
```

**7B. Jak Czytamy Raport**

Najwazniejsze sekcje:

```text
Ledger Coverage = czy mamy komplet rekordow
Model Versions = ktory model generowal predykcje
Process Failures = co najczesciej blokuje audyt
Calibration MVP = czy p_cover zgadza sie z realnym cover rate
```

Interpretacja:

```text
pending = mecz nie ma jeszcze wyniku albo evaluation nie jest rozliczone
settled = wynik jest znany i evaluation zostalo policzone
process_failures = braki procesu, niekoniecznie blad modelu
calibration empty = normalne przed wynikami
```

**7C. Co Chcemy Widziec Po Kolejce**

Po domknieciu kolejki raport powinien pokazac:

```text
ile pickow bylo frozen pregame
ile ma wynik
ile nadal jest pending
ile bylo COVER / PUSH / LOSS
jakie byly najczestsze missing_data
czy p_cover zaczyna byc zgodne z wynikami
```

**7D. Kiedy Raport Ma Sens Dla Modelu Uczacego Sie**

Raport technicznie dziala od razu, ale wnioski modelowe maja sens dopiero przy wiekszej probce:

```text
minimum: 50-100 settled predictions
lepiej: kilka sezonow albo pelny sezon 2026
```

Nie wyciagamy mocnych wnioskow po jednej kolejce.

**7E. Co Robi Codex Po Raporcie**

Codex analizuje:

```text
czy ledger dziala
czy sa braki w quote/GPT/closing/wynikach
czy model ma problem kalibracji
czy proces ma powtarzalny blad
co trzeba poprawic przed nastepna kolejka
```

**7F. Kiedy Punkt 7 Jest Wykonany**

Punkt 7 dla kolejki jest wykonany, gdy:

```text
learning report zostal odpalony po post-event evaluation
raport pokazuje pending/settled
process failures zostaly przejrzane
wiemy, co poprawic przed nastepna kolejka
```

Status:

```text
GOTOWE, ALE KALIBRACJA BEDZIE MIALA SENS DOPIERO PO WYNIKACH
```

</details>

## 8. Live Scenario

Krotko:

```text
Live Scenario pokazuje historyczne rozklady po przebiegu kwart, np. co dzialo sie dalej, gdy Team A wygral Q1, przegral Q2, ale nadal prowadzil po H1.
```

<details>
<summary>Rozwin punkt 8 - live scenario</summary>

Mamy gotowy modul:

```text
scripts/live_quarter_scenario_matrix.py
docs/live_quarter_scenario_matrix.md
```

**8A. Do Czego Sluzy**

Ten punkt jest osobnym narzedziem live, a nie czescia pregame picka.

Pokazuje:

```text
jak czesto podobny przebieg kwartowy konczyl sie wygrana Team A
jak czesto Team A wygrywal nastepna kwarte
jak czesto Team A prowadzil po nastepnej kwarcie
jak wygladal finalny wynik po podobnych scenariuszach
jaki jest fair kurs
jaki minimalny kurs live daje EV+
```

**8B. Czego Nie Robi**

```text
nie pobiera kursow live z booka
nie daje automatycznego betu
nie zastapi kontuzji live, czerwonych flag, quarterback injury, weather shift
nie zna realnego marketu, jesli nie wpiszemy kursu recznie
```

**8C. Najwazniejsze Rozroznienie**

Skrypt rozdziela dwie rzeczy:

```text
Quarter Reset View = kto wygral sama kwarte
Cumulative Game View = kto prowadzi w meczu po tej kwarcie
```

Przyklad:

```text
Q1: Team A wygrywa 10:3
Q2: Team A przegrywa 3:7
```

To oznacza:

```text
Q2 result only = LOSS
after H1 cumulative = Team A nadal prowadzi 13:10
```

**8D. Kiedy Uzywamy**

Uzywamy w trakcie meczu po zamknietej kwarcie:

```text
po Q1
po H1
po Q3
opcjonalnie przed Q4, jesli jest realny kurs live i wystarczajaca probka
```

Najbardziej praktyczne momenty:

```text
po Q1 - szybki obraz, ale duzo szumu
po H1 - lepszy kompromis probka/informacja
po Q3 - najblizej decyzji live, ale rynek zwykle jest bardziej efektywny
```

**8E. Jak Kodujemy Sciezke**

`--lookup-path` opisuje wynik kolejnych kwart z perspektywy Team A:

```text
WIN = Team A wygral Q1
LOSS = Team A przegral Q1
TIE = Team A zremisowal Q1
WIN-LOSS = Team A wygral Q1 i przegral Q2
WIN-LOSS-WIN = Team A wygral Q1, przegral Q2, wygral Q3
```

To jest wynik danej kwarty, a nie wynik laczny meczu.

**8F. Jakie Eventy Sprawdzamy**

Dostepne eventy:

```text
TEAM_A_WIN_NEXT_QUARTER = Team A wygra nastepna kwarte
TEAM_A_LEAD_AFTER_NEXT_QUARTER = Team A bedzie prowadzil po nastepnej kwarcie
TEAM_A_WIN_FINAL = Team A wygra mecz
```

Najczesciej uzywamy:

```text
TEAM_A_WIN_FINAL dla live moneyline
TEAM_A_WIN_NEXT_QUARTER dla rynku kolejnej kwarty
TEAM_A_LEAD_AFTER_NEXT_QUARTER jako pomocniczy game-state check
```

**8G. Glowna Komenda**

Pelny zakres 2016-2025 league-wide:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025
```

Wyniki:

```text
research/live_quarter_scenario_matrix/2016_2025_league_wide/
```

**8H. Przyklad Live**

Przyklad: SF at LA, po Q1 jest 7:3 dla SF.

Jesli Team A = SF, to Q1 path:

```text
WIN
```

Sprawdzenie finalnej wygranej SF przy kursie live 1.50:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025 --lookup-path WIN --event TEAM_A_WIN_FINAL --live-decimal 1.50
```

Sprawdzenie, czy SF wygra Q2:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025 --lookup-path WIN --event TEAM_A_WIN_NEXT_QUARTER --live-decimal 2.00
```

**8I. Filtry, Ktore Mozemy Dodac**

Mozemy ograniczyc probe historyczna:

```text
--sample-mode TEAM_A_HISTORY
--sample-mode TEAM_B_HISTORY
--sample-mode HEAD_TO_HEAD
--team SF
--opponent LA
--role UNDERDOG
--role FAVORITE
--side home
--side away
--spread-bucket 2-3
--season-phase EARLY
```

Przyklad bardziej filtrowany:

```powershell
.\.venv\Scripts\python.exe scripts\live_quarter_scenario_matrix.py --start-season 2016 --end-season 2025 --sample-mode TEAM_A_HISTORY --team SF --role UNDERDOG --side away --spread-bucket 2-3 --season-phase EARLY --lookup-path WIN --event TEAM_A_WIN_FINAL --live-decimal 1.50
```

Uwaga:

```text
im wiecej filtrow, tym mniejsza probka
mala probka = informacja pomocnicza, nie sygnal do gry
```

**8J. Co Patrzymy W Wyniku**

Najwazniejsze pola:

```text
sample_size
sample_quality
win_probability
loss_probability
tie_probability
fair_decimal
fair_american
live_decimal
live_american
ev
ev_pct
```

Interpretacja:

```text
fair_decimal = minimalny kurs bez marzy, przy ktorym zaklad jest neutralny
live_decimal > fair_decimal = potencjalne EV+
live_decimal <= fair_decimal = brak przewagi wedlug tej probki
sample_quality LOW/VERY_LOW = nie traktujemy tego jako mocny sygnal
```

**8K. Jak To Laczymy Z Calym Systemem**

Live Scenario jest dodatkiem do Variant B:

```text
pregame model wybiera kandydatow VP/GOW/GOM/GOY
Variant B ocenia 19 punktow przed meczem
Live Scenario pomaga reagowac w trakcie meczu
kurs live wpisujemy recznie
decyzja live musi miec osobny zapis w ledgerze
```

Nie mieszamy tego z pregame trackingiem.

**8L. Co Jeszcze Brakuje**

Do pelnego modulu live jeszcze brakuje:

```text
prostego inputu live_game_state.yaml
ledgeru decyzji live
raportu live po meczu
opcjonalnie filtrow po pregame tagu VP/GOW/GOM/GOY
opcjonalnie podzialu na konkretne rynki: ML live, next quarter, live spread
```

Status:

```text
GOTOWE, KURS LIVE WPISUJEMY RECZNIE
```

</details>

## 9. Basic Model Week Flow

Krotko:

```text
Basic Model Week Flow to pierwszy skan kolejki: pobiera schedule/linie, liczy picki i pokazuje, czy sa VP/GOW/GOM/GOY.
```

<details>
<summary>Rozwin punkt 9 - basic model week flow</summary>

**9A. Cel Punktu**

To jest pierwszy etap pracy przed kolejka.

Ma odpowiedziec na pytanie:

```text
czy w tej kolejce sa kandydaci do dalszego audytu Variant B?
```

Interesuja nas tylko tagi:

```text
VALUE PLAY
GOW
GOM
GOY
```

`NEUTRAL` nie idzie do pelnego audytu 19 punktow.

**9B. Kiedy Odpalamy**

Glowny skan robimy we wtorek przed kolejka.

Potem mozemy powtarzac flow codziennie, gdy zmieniaja sie linie:

```text
sroda - refresh przed TNF
czwartek - final check TNF
piatek - refresh niedzielnych meczow
sobota - pre-final niedziela
niedziela - final check kilka godzin przed meczami
poniedzialek - final check MNF
```

**9C. Dane Wejsciowe**

Potrzebujemy:

```text
schedule kolejki
linie spread/total
realne quote z booka lub snapshot z pregame.com
```

Wazne:

```text
nfl_data_py daje schedule i czesc danych historycznych
linie booka nie sa w pelni automatyczne
linie/screeny bierzemy z pregame.com albo wpisujemy recznie
```

**9D. Krok 1 - Schedule**

Komenda:

```powershell
.\.venv\Scripts\python.exe -m app.cli sync-nfl-schedule --season 2026
```

Cel:

```text
pobrac/przygotowac schedule sezonu
miec liste meczow, week, home, away, game_id
```

**9E. Krok 2 - Linie Do Configu**

Komenda:

```powershell
.\.venv\Scripts\python.exe -m app.cli export-lines-from-nfl --season 2026 --week 1
```

Cel:

```text
przygotowac plik linii dla tygodnia
```

Domyslny plik:

```text
config/lines/2026/week1_lines.yaml
```

Uwaga:

```text
ten plik musi byc sprawdzony i uzupelniony realnymi liniami
nie zakladamy, ze nfl_data_py daje nam market-grade linie booka
```

**9F. Krok 3 - Basic Model**

Komenda:

```powershell
.\.venv\Scripts\python.exe -m app.cli sync-nfl-schedule --season 2026
.\.venv\Scripts\python.exe -m app.cli export-lines-from-nfl --season 2026 --week 1
.\.venv\Scripts\python.exe scripts\prospective_week_flow.py --season 2026 --week 1 --variant variant_m --skip-freeze
```

W praktyce, jesli schedule i linie sa juz gotowe, najwazniejsza jest trzecia komenda:

```powershell
.\.venv\Scripts\python.exe scripts\prospective_week_flow.py --season 2026 --week 1 --variant variant_m --skip-freeze
```

**9G. Wyniki Basic Modelu**

Glowne pliki:

```text
data/picks_variant_m/2026/week_01.jsonl
data/reports/generated/week01_summary.md
data/prospective_ledger/2026/prospective_ytd_report.md
```

Najwazniejszy dla nas:

```text
data/picks_variant_m/2026/week_01.jsonl
```

Tam sprawdzamy:

```text
selected team
tag
edge_vs_line
spread
price
```

**9H. Jak Czytamy Wynik**

Jesli model pokazuje:

```text
VALUE PLAY
GOW
GOM
GOY
```

to mecz przechodzi do punktu 2, czyli GPT 19 punktow.

Jesli model pokazuje:

```text
NEUTRAL
```

to nie robimy pelnego audytu, chyba ze recznie chcemy zbadac mecz edukacyjnie.

**9I. Krok 4 - Variant B Dla Kandydatow**

Po uzupelnieniu quote i GPT 19 punktow odpalamy:

```powershell
.\.venv\Scripts\python.exe scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof --write-learning-ledger
```

Co robi ta komenda:

```text
generuje model proof
liczy p_cover / p_push / p_loss
robi audit Variant B dla VP/GOW/GOM/GOY
wciaga quote z data/market_quotes, jesli istnieje
zapisuje learning ledger
tworzy summary.md
```

Glowne wyjscie:

```text
research/variant_b_week_flow/2026/week_01/summary.md
research/variant_b_week_flow/2026/week_01/*.json
data/learning_ledger/2026/week_01/
```

**9J. Co Oznacza HOLD**

Jesli w summary jest:

```text
operator_action: HOLD
gate: PREKICK_NOT_READY
```

to nie znaczy, ze pick jest zly.

Najczesciej oznacza:

```text
brakuje kompletnego quote
brakuje timestampu
brakuje executable status
brakuje finalnego GPT refresh
brakuje closing/prekick danych, ktore jeszcze nie sa due
```

**9K. Minimalna Codzienna Rutyna**

Codziennie nie musimy od nowa robic wszystkiego od zera.

Minimalnie:

```text
1. aktualizujemy quote/linie
2. sprawdzamy, czy tagi sie zmienily
3. dla aktywnych VP/GOW/GOM/GOY robimy refresh GPT tylko dla zmiennych punktow
4. ponownie odpalamy Variant B
5. patrzymy, czy HOLD zmienil sie w PLAY / PASS / NO BET
```

**9L. Kiedy Punkt 9 Jest Wykonany**

Punkt 9 dla kolejki jest wykonany, gdy:

```text
schedule jest pobrany
linie sa przygotowane
basic model wygenerowal pick file
wiemy, czy sa VP/GOW/GOM/GOY
kandydaci zostali przekazani do Variant B
```

Status:

```text
GOTOWE
```

</details>

## 10. Model Uczacy Sie

Krotko:

```text
Model uczacy sie nie oznacza, ze system sam wybiera bety. Oznacza, ze zapisujemy predykcje, quote, decyzje i wyniki, a potem kontrolowanie uczymy nowa wersje modelu.
```

<details>
<summary>Rozwin punkt 10 - model uczacy sie</summary>

Mamy fundament:

```text
docs/model_learning_data_contract.md
docs/variant_b_learning_model_roadmap.md
config/model_registry.json
```

**10A. Glowna Zasada**

Nie budujemy jednego samodzielnie myslacego modelu.

Budujemy cztery warstwy:

```text
1. wersjonowane dane i snapshoty
2. probabilistyczny model wyniku meczu
3. deterministyczny silnik audytu Variant B
4. kontrolowana petla trenowania i promocji nowej wersji
```

Model moze sie uczyc.

Reguly audytu, quote proof, no-chase, CLV i finalny gate nie moga byc losowe ani opisowe.

**10B. Co Juz Mamy**

Wdrozone albo czesciowo wdrozone:

```text
kontrakt danych
append-only learning ledger
model proof MVP
p_cover / p_push / p_loss
margin PMF MVP
post-event evaluation
learning report
model registry
champion baseline variant_m
```

Najwazniejsze pliki:

```text
docs/model_learning_data_contract.md
docs/variant_b_learning_model_roadmap.md
config/model_registry.json
scripts/variant_b_learning_ledger.py
scripts/variant_b_model_proof.py
scripts/variant_b_post_event_evaluation.py
scripts/variant_b_learning_report.py
```

**10C. Co To Znaczy W Prostym Jezyku**

Po kazdym kandydacie VP/GOW/GOM/GOY system zapisuje:

```text
co model widzial przed meczem
jaki byl quote z booka
jaka byla predykcja
jaki byl tag
jaka byla decyzja Variant B
jaki byl wynik
czy pick pokryl spread
czy mielismy CLV
czy blad byl w modelu, danych, rynku czy procesie
```

Dzieki temu po czasie mozemy sprawdzic:

```text
czy model dobrze wycenial p_cover
czy konkretne typy edge faktycznie dzialaly
czy GOY/GOM/GOW/VP maja sens
czy Week 1 jest zbyt niepewny
czy injury/weather/roster notes poprawiaja decyzje
czy no-bet/HOLD chroni nas przed slabymi wejsciami
```

**10D. Czego Jeszcze Brakuje Do Realnego Uczenia**

Potrzebujemy wiecej danych:

```text
wiecej zamrozonych predykcji
wiecej realnych quote
wyniki po meczach
closing line / closing price
CLV
post-event review
wieksza probka settled outcomes
```

Bez tego model nie ma sie jeszcze z czego uczyc.

**10E. Minimalna Probka**

W polityce promocji mamy:

```text
minimum_settled_predictions: 100
```

Praktycznie:

```text
po 1 tygodniu = tylko sanity check procesu
po 4-6 tygodniach = pierwsze ostrozne sygnaly
po calym sezonie = sensowna ocena modelu 2026
po kilku sezonach/as-of backtest = kandydat do promocji
```

**10F. Champion I Challenger**

Obecny champion:

```text
variant_m
```

Jest zapisany tutaj:

```text
config/model_registry.json
```

Nowy model nie zastapi championa automatycznie.

Candidate musi przejsc:

```text
walk-forward backtest
calibration report
no data leakage check
segment stability check
porownanie z championem
manual approval
```

**10G. Jak Bedzie Wygladac Uczenie**

Docelowy proces:

```text
1. zbieramy dane 2026 w ledgerze
2. po meczach dopisujemy outcomes i post-event evaluation
3. learning report pokazuje bledy i kalibracje
4. budujemy candidate model na historycznych danych as-of
5. testujemy go walk-forward
6. porownujemy z variant_m
7. jesli przejdzie gate'y, dopiero wtedy moze zostac nowym championem
```

**10H. Rola GPT**

GPT nie jest glownym modelem predykcyjnym.

GPT moze:

```text
szukac injury reports
streszczac roster moves
porownywac zrodla
generowac research snapshot
opisywac ryzyka
wskazywac missing data
```

GPT nie moze:

```text
liczyc EV jako finalnej prawdy
rekonstruowac brakujacych quote
promowac nowego modelu
zmieniac regul Variant B
traktowac narracji jako twardych danych
uzywac informacji po meczu jako pregame inputu
```

Zasada:

```text
GPT = research i opis
Python = kalkulacje, ledger, proof, decyzje gate
```

**10I. Co Robimy Przed Startem 2026**

Przed sezonem:

```text
utrzymujemy variant_m jako champion baseline
dopracowujemy quote workflow
dopracowujemy GPT 19 punktow
dopracowujemy post-event evaluation
dopracowujemy learning report
nie promujemy nowego modelu bez danych
```

**10J. Co Robimy W Sezonie 2026**

W kazdej kolejce:

```text
basic model generuje VP/GOW/GOM/GOY
Variant B robi audit
ledger zapisuje predykcje i quote
po meczu zapisujemy wynik
learning report pokazuje proces i kalibracje
```

Po sezonie:

```text
robimy pelny review
liczymy kalibracje
liczymy segmenty
testujemy candidate model
decydujemy, czy variant_m zostaje championem
```

**10K. Kiedy Punkt 10 Jest Wykonany**

Punkt 10 jest gotowy operacyjnie, gdy:

```text
kazdy pick VP/GOW/GOM/GOY trafia do ledgeru
kazdy pick ma quote
kazdy pick ma p_cover/p_push/p_loss
kazdy pick po meczu ma outcome
learning report widzi settled outcomes
model_registry wskazuje championa
candidate model nie moze zostac promowany bez gate'ow
```

Status:

```text
FUNDAMENT GOTOWY, UCZENIE BEDZIE MIALO SENS PO ZEBRANIU DANYCH 2026
```

</details>

## 11. Najprostsza Kolejnosc Pracy W Sezonie

Krotko:

```text
Punkt 11 to prosty kalendarz pracy w sezonie: co robimy we wtorek, srode, czwartek, piatek, sobote, niedziele, poniedzialek i wtorek po kolejce.
```

<details>
<summary>Rozwin punkt 11 - kalendarz pracy w sezonie</summary>

**11A. Glowna Zasada**

Nie robimy codziennie pelnego procesu od zera.

Podzial:

```text
wtorek rano/wieczor po MNF = najpierw zamkniecie poprzedniej kolejki
wtorek = glowny skan kolejki
sroda = TNF delta refresh i pierwsze zmiany
czwartek = ostatni zrzut TNF + zrzuty niedziela i poniedzialek
piatek/sobota = refresh niedziela i poniedzialek
niedziela = ostatni zrzut niedziela + zrzut poniedzialek + live scenario
poniedzialek = ostatni zrzut MNF
wtorek po kolejce = wyniki, CLV, learning report
```

Pelne GPT 19 punktow robimy tylko dla:

```text
VALUE PLAY
GOW
GOM
GOY
```

Pozniej robimy juz tylko delta refresh, czyli sprawdzamy, co sie zmienilo.

**11B. Wtorek - Glowny Skan Kolejki**

Wazna kolejnosc wtorku:

```text
1. Najpierw zamykamy poprzednia kolejke.
2. Dopiero potem zaczynamy skan nowej kolejki.
```

Nie mieszamy danych:

```text
post-event poprzedniej kolejki = wyniki, CLV, learning report
pregame nowej kolejki = schedule, linie, model, GPT, quote, Variant B
```

Cel:

```text
znalezc kandydatow VP/GOW/GOM/GOY
```

Robimy:

```text
1. Pobierz schedule/linie z nfl_data_py.
2. Uzupelnij / sprawdz linie z pregame.com albo booka.
3. Odpal basic model.
4. Sprawdz, czy sa VP/GOW/GOM/GOY.
5. Dla kandydatow zrob pelne GPT 19 punktow.
6. Wpisz quote z booka.
7. Odpal Variant B + model proof + learning ledger.
8. Sprawdz summary.md.
```

Komendy bazowe:

```powershell
.\.venv\Scripts\python.exe -m app.cli sync-nfl-schedule --season 2026
.\.venv\Scripts\python.exe -m app.cli export-lines-from-nfl --season 2026 --week 1
.\.venv\Scripts\python.exe scripts\prospective_week_flow.py --season 2026 --week 1 --variant variant_m --skip-freeze
.\.venv\Scripts\python.exe scripts\variant_b_week_flow.py --season 2026 --week 1 --variant variant_m --with-model-proof --write-learning-ledger
```

Wyniki sprawdzamy tutaj:

```text
data/picks_variant_m/2026/week_01.jsonl
research/variant_b_week_flow/2026/week_01/summary.md
```

**11C. Sroda - TNF Delta Refresh**

Cel:

```text
sprawdzic, czy cos zmienilo sie pod mecz czwartkowy
```

Robimy:

```text
1. Aktualizujemy quote dla TNF.
2. Sprawdzamy line movement.
3. Sprawdzamy injury report.
4. Sprawdzamy roster moves.
5. Sprawdzamy weather / venue.
6. Jesli TNF jest VP/GOW/GOM/GOY, zlecamy GPT delta refresh.
7. Wklejamy wynik do Codex.
8. Odpalamy Variant B ponownie.
```

Nie robimy:

```text
pelnych 19 punktow dla meczow neutralnych
```

**11D. Czwartek - Final Check TNF + Zrzuty Niedziela/MNF**

Cel:

```text
ostatni zrzut przed kickoffem TNF oraz swiezy zrzut dla niedzieli i poniedzialku
```

Robimy dla TNF kilka godzin przed meczem:

```text
1. Aktualizujemy quote.
2. Sprawdzamy final injury/inactives, jesli sa dostepne.
3. Sprawdzamy weather.
4. Sprawdzamy, czy spread/price nadal miesci sie w no-chase.
5. Odpalamy Variant B.
6. Decyzja: PLAY / PASS / HOLD / NO BET.
```

Po meczu TNF:

```text
jesli byl kandydat, zapisujemy wynik pozniej w post-event flow
```

Dodatkowo w czwartek robimy zrzuty dla niedzieli i poniedzialku:

```text
1. Aktualizujemy quote dla niedzielnych kandydatow.
2. Aktualizujemy quote dla MNF, jesli jest kandydatem.
3. Sprawdzamy line movement od wtorku.
4. Sprawdzamy nowe injury/roster/weather news.
5. Jesli cos istotnego sie zmienilo, zlecamy GPT delta refresh.
6. Odpalamy Variant B ponownie dla aktywnych kandydatow.
```

**11E. Piatek - Glowny Refresh Niedzieli I MNF**

Cel:

```text
odswiezyc niedzielne i poniedzialkowe VP/GOW/GOM/GOY po injury reports i ruchach rynku
```

Robimy:

```text
1. Aktualizujemy quote dla niedzielnych kandydatow.
2. Aktualizujemy quote dla MNF, jesli jest kandydatem.
3. Sprawdzamy line movement.
4. Sprawdzamy injury_role_notes.
5. Sprawdzamy roster_change_check.
6. Sprawdzamy weather.
7. Zlecamy GPT delta refresh dla kandydatow.
8. Wklejamy wynik do Codex.
9. Odpalamy Variant B ponownie.
```

**11F. Sobota - Pre-Final Niedzieli I MNF**

Cel:

```text
przygotowac niedziele i poniedzialek tak, zeby w dniu meczowym zostaly tylko finalne braki
```

Robimy:

```text
1. Aktualizujemy quote.
2. Sprawdzamy, czy market przeszedl key number.
3. Sprawdzamy, czy sa nowe kontuzje/roster moves.
4. Sprawdzamy weather.
5. Tworzymy liste brakow na niedziele.
6. Tworzymy liste brakow na MNF.
7. Oznaczamy status: READY_FOR_SUNDAY_CHECK / READY_FOR_MNF_CHECK / WATCH / HOLD / NO BET.
```

**11G. Niedziela - Final Check Niedzieli + Zrzut MNF + Live**

Cel:

```text
ostatni zrzut przed niedzielnymi meczami, zrzut dla poniedzialku oraz live scenario
```

Robimy przed kickoffem niedzielnych meczow:

```text
1. Aktualizujemy quote.
2. Sprawdzamy final inactives.
3. Sprawdzamy weather.
4. Sprawdzamy no-chase.
5. Odpalamy Variant B.
6. Decyzja: PLAY / PASS / HOLD / NO BET.
```

Dodatkowo w niedziele robimy zrzut dla MNF:

```text
1. Aktualizujemy quote dla MNF.
2. Sprawdzamy line movement.
3. Sprawdzamy injury/roster/weather.
4. Jesli MNF jest kandydatem, robimy GPT delta refresh.
5. Odpalamy Variant B dla MNF.
6. Oznaczamy status: READY_FOR_MNF_CHECK / WATCH / HOLD / NO BET.
```

Podczas meczu:

```text
uzywamy Live Scenario tylko pomocniczo
kurs live wpisujemy recznie
decyzji live nie mieszamy z pregame trackingiem
```

**11H. Poniedzialek - Ostatni Zrzut MNF**

Cel:

```text
ostatni zrzut przed Monday Night Football
```

Robimy:

```text
1. Aktualizujemy quote dla MNF.
2. Sprawdzamy final injury/inactives.
3. Sprawdzamy weather.
4. Sprawdzamy no-chase.
5. Robimy GPT final delta refresh, jesli MNF jest kandydatem.
6. Odpalamy Variant B.
7. Decyzja: PLAY / PASS / HOLD / NO BET.
```

**11I. Wtorek Po Kolejce - Zamkniecie Tygodnia**

Cel:

```text
zamknac kolejke i nakarmic learning ledger
```

To robimy jako pierwsza czesc wtorku, przed skanem nowej kolejki.

Robimy po zakonczeniu ostatniego meczu kolejki:

```text
1. Pobieramy wyniki.
2. Dopisujemy closing line / closing price, jesli mamy wiarygodne zrodlo.
3. Odpalamy post-event evaluation.
4. Odpalamy learning report.
5. Sprawdzamy process failures.
6. Zapisujemy, co poprawic przed nastepna kolejka.
```

Komendy:

```powershell
.\.venv\Scripts\python.exe -m app.cli sync-nfl-results --season 2026
.\.venv\Scripts\python.exe scripts\variant_b_post_event_evaluation.py --season 2026 --week 1
.\.venv\Scripts\python.exe scripts\variant_b_learning_report.py
```

**11J. Co Robi Uzytkownik**

Ty robisz recznie:

```text
screeny/pobranie quote z pregame.com albo booka
wklejenie danych do GPT, gdy trzeba research/delta
wklejenie odpowiedzi GPT do Codex
potwierdzenie realnego quote, price, timestamp, executable status
```

**11K. Co Robi Codex / Python**

System robi:

```text
sync schedule
przygotowanie linii
basic model
tagi VP/GOW/GOM/GOY
model proof
Variant B audit
learning ledger
post-event evaluation
learning report
```

**11L. Kiedy Punkt 11 Jest Wykonany**

Punkt 11 jest gotowy, gdy:

```text
masz jasny kalendarz tygodnia
wiesz, kiedy robic pelne GPT 19 punktow
wiesz, kiedy robic tylko delta refresh
wiesz, kiedy odpalac Variant B
wiesz, kiedy zamykac kolejke post-event
```

</details>

## 12. Najwieksze Braki Teraz

Krotko:

```text
Punkt 12 pokazuje, czego jeszcze brakuje, zeby system byl gotowy operacyjnie na sezon 2026.
```

<details>
<summary>Rozwin punkt 12 - najwieksze braki teraz</summary>

**12A. Najwazniejszy Wniosek**

Techniczny fundament juz mamy.

Najwiekszy problem nie jest teraz w samym modelu, tylko w jakosci danych operacyjnych:

```text
quote
timestampy
executable status
GPT research snapshot
closing line
wyniki
regularne zamkniecie kolejki
```

Bez tego model uczacy sie bedzie mial techniczny fundament, ale za malo dobrych danych.

**12B. Hard Blockers**

To sa rzeczy, bez ktorych nie mamy pelnego market-grade proof:

```text
1. realny quote z booka albo pregame.com snapshot
2. timestamp quote
3. executable_status
4. selected_team spread i price
5. GPT 19 punktow dla VP/GOW/GOM/GOY
6. wynik meczu po zakonczeniu
7. post-event evaluation
```

Jesli brakuje tych pol, Variant B powinien trzymac status:

```text
HOLD
PREKICK_NOT_READY
MISSING_DATA
```

**12C. Braki Do Learning Modelu**

Do realnego uczenia brakuje:

```text
wiecej zamrozonych predykcji
wiecej quote snapshots
wiecej settled outcomes
closing line / closing price
CLV
post-event review
calibration sample
minimum 100 settled predictions
```

Na start sezonu to normalne.

Uczenie zacznie miec sens dopiero, gdy ledger bedzie mial prawdziwe rekordy z sezonu 2026.

**12D. Braki W Quote Workflow**

Quote workflow jest opanowany recznie, ale jeszcze nie w pelni automatyczny.

Mamy:

```text
screeny z pregame.com
prompt dla GPT do przepisania screena
Codex poprawia YAML
Codex moze przerobic to na market_quotes
```

Brakuje:

```text
automatycznego parsera screenshot -> YAML
automatycznego walidatora asymetrycznych linii
prostego komunikatu, ktore mecze maja quote complete
prostego importu snapshotu do data/market_quotes/{season}/week_XX.jsonl
```

**12E. Braki W GPT Research Snapshots**

GPT 19 punktow dziala procesowo, ale trzeba jeszcze dopiac zapis.

Brakuje:

```text
jednego folderu na research snapshots per game
jednej nazwy pliku na pelne 19 punktow
jednej nazwy pliku na delta refresh
walidatora, czy kazdy VP/GOW/GOM/GOY ma GPT snapshot
mapowania GPT point 1-19 -> Variant B audit fields
```

Docelowo:

```text
research/gpt_snapshots/{season}/week_XX/{game_id}/full_19_points.md
research/gpt_snapshots/{season}/week_XX/{game_id}/delta_YYYYMMDD.md
```

**12F. Braki W Closing / CLV**

Closing jest potrzebny do oceny procesu po meczu.

Brakuje:

```text
prostego formatu closing_snapshot
regularnego wpisywania closing line / closing price
polaczenia closing snapshot z post-event evaluation
raportu CLV per tag: VP/GOW/GOM/GOY
```

Bez closing danych nadal mozemy rozliczyc COVER/PUSH/LOSS, ale nie ocenimy dobrze:

```text
czy pokonalismy rynek
czy weszlismy za pozno
czy no-chase powinien byc ostrzejszy
```

**12G. Braki W Wynikach I Post-Event**

Mamy kierunek:

```text
nfl_data_py jako glowne zrodlo wynikow
manual fallback tylko awaryjnie
```

Brakuje rutyny:

```text
wtorek po kolejce zawsze sync wynikow
zawsze post-event evaluation
zawsze learning report
zawsze review process failures
```

To jest bardziej dyscyplina procesu niz problem techniczny.

**12H. Braki W Live Scenario**

Live Scenario dziala jako analiza historyczna.

Brakuje:

```text
live_game_state.yaml
ledgeru decyzji live
raportu live po meczu
oddzielenia live tracking od pregame tracking
opcjonalnych filtrow po pregame tagu VP/GOW/GOM/GOY
```

**12I. Braki W Automatyzacji**

Docelowo chcemy bota/orkiestratora.

Brakuje:

```text
automatycznego daily checklist
automatycznego sprawdzania brakow
automatycznego raportu READY / WATCH / HOLD / NO BET
automatycznego przypominania o zrzutach TNF/Sunday/MNF
automatycznego week close po MNF
```

To jest zapisane tez w punkcie 14.

**12J. Kolejnosc Domykania**

Najpierw domykamy:

```text
1. quote workflow
2. GPT research snapshot storage
3. market_quotes import
4. closing snapshot format
5. post-event routine
6. learning report review
7. live ledger
8. bot/orchestrator
```

Nie zaczynamy od trenowania nowego modelu, dopoki nie mamy dobrego ledgeru.

**12K. Co Musi Byc Gotowe Przed Week 1 2026**

Minimum operacyjne:

```text
1. umiesz zrobic screenshot pregame.com
2. GPT zwraca quote YAML w prawidlowym formacie
3. Codex zapisuje/normalizuje quote
4. basic model znajduje VP/GOW/GOM/GOY
5. GPT 19 punktow jest zapisany dla kandydatow
6. Variant B generuje summary
7. po meczu wynik trafia do ledgeru
8. learning report dziala
```

To wystarczy na start sezonu.

**12L. Status**

```text
NAJWIEKSZY BRAK = DANE OPERACYJNE I DYSCYPLINA ZAPISU
MODEL / LEDGER / REPORTING MAJA FUNDAMENT
AUTOMATYZACJA JEST KOLEJNYM KROKIEM
```

</details>

## 13. Badanie Ruchu Linii

Krotko:

```text
Punkt 13 to osobne badanie historyczne: sprawdzamy, czy konkretne ruchy linii byly sygnalem value, warningiem, czy tylko szumem.
```

<details>
<summary>Rozwin punkt 13 - badanie ruchu linii</summary>

**13A. Cel**

Chcemy sprawdzic historycznie:

```text
co dzialo sie z druzynami po konkretnych ruchach linii
czy ruch w strone druzyny zwiekszal jej szanse SU / ATS
czy ruch przeciwko druzynie byl warningiem
czy ruch przez key number 3 / 7 / 10 mial znaczenie
czy rozne wielkosci ruchu dawaly rozne wyniki
```

To nie jest system do nazywania ruchu jako sharp/public.

To jest twarde badanie:

```text
ruch linii -> wynik SU / ATS / ROI / CLV
```

**13B. Zrodlo Danych**

Podstawowe zrodlo:

```text
nfl_data_py
```

Skrypt ma pobierac z `nfl_data_py` historyczne dane NFL i na ich podstawie badac:

```text
ruch linii
wynik SU
wynik ATS
push
margin
ATS margin
ROI przy standardowej cenie
```

**13C. Ograniczenie Danych**

Najpierw sprawdzamy, jakie pola sa dostepne w danych:

```text
spread_line
total_line
closing_spread, jesli dostepne
closing_total, jesli dostepne
opener_spread, jesli dostepne
home_score
away_score
game_id
season
week
home_team
away_team
```

Jesli `nfl_data_py` nie ma pelnego opener/current/closing dla danego sezonu, skrypt ma oznaczyc:

```text
data_status: PARTIAL
missing_market_fields:
```

Nie wolno rekonstruowac openerow ani closing line, jesli nie ma ich w danych.

Wtedy badanie moze miec status:

```text
FULL = mamy opener/current/closing
PARTIAL = mamy tylko czesc linii
NOT_ASSESSABLE = nie mamy danych do ruchu
```

**13D. Konwencja Spreadu**

Wazne:

```text
nfl_data_py spread_line = spread z perspektywy away team
config/lines zapisuje spread z perspektywy home team jako -spread_line
```

Dla badania ruchu linii wszystko przeliczamy na perspektywe `selected_team`.

Definicja:

```text
selected_team_spread = spread przypisany do badanej druzyny
```

Przyklady:

```text
LA -3.0 = selected_team_spread -3.0
SF +3.0 = selected_team_spread +3.0
```

**13E. Co Chcemy Badac**

Chcemy badac nie tylko sam pick, ale tez:

```text
czy linia ruszyla w strone druzyny
czy linia ruszyla przeciwko druzynie
czy druzyna potem wygrala/przegrala SU
czy druzyna pokryla spread ATS
czy ruch linii poprawial albo pogarszal value
```

**13F. Definicja Ruchu**

Definicja z perspektywy selected_team:

```text
line_move_points = current_spread_selected_team - opener_spread_selected_team
```

Interpretacja:

```text
line_move_points < 0 = linia ruszyla w strone selected_team, selected_team stala sie bardziej faworyzowana
line_move_points > 0 = linia ruszyla przeciwko selected_team, selected_team dostaje wiecej punktow
line_move_points = 0 = brak ruchu spreadu
```

Przyklady:

```text
LA opener -3.0 -> current -4.0 = ruch -1.0 pkt w strone LA
LA opener -3.0 -> current -2.0 = ruch +1.0 pkt przeciwko LA
SF opener +3.0 -> current +4.0 = ruch +1.0 pkt przeciwko SF
SF opener +3.0 -> current +2.0 = ruch -1.0 pkt w strone SF
```

**13G. Buckety Ruchu Linii**

Podstawowe buckety:

```text
0
0.5
1
1.5
2
2.5
3
3.5
4
4.5
5+
```

Osobno badamy:

```text
MOVE_FOR_TEAM_0.5
MOVE_FOR_TEAM_1
MOVE_FOR_TEAM_2
MOVE_FOR_TEAM_3
MOVE_FOR_TEAM_4
MOVE_FOR_TEAM_5_PLUS

MOVE_AGAINST_TEAM_0.5
MOVE_AGAINST_TEAM_1
MOVE_AGAINST_TEAM_2
MOVE_AGAINST_TEAM_3
MOVE_AGAINST_TEAM_4
MOVE_AGAINST_TEAM_5_PLUS

NO_MOVE
```

Docelowo rozbijamy tez dokladniej:

```text
0.5
1.0
1.5
2.0
2.5
3.0
3.5
4.0
4.5
5.0+
```

**13H. Key Numbers**

Osobne etykiety:

```text
MOVE_ONTO_3
MOVE_OFF_3
MOVE_THROUGH_3
MOVE_ONTO_7
MOVE_OFF_7
MOVE_THROUGH_7
MOVE_ONTO_10
MOVE_OFF_10
MOVE_THROUGH_10
```

Przyklady:

```text
+3.5 -> +2.5 = move through 3 w strone underdoga
-2.5 -> -3.5 = move through 3 w strone faworyta
+7.5 -> +6.5 = move through 7 w strone underdoga
-6.5 -> -7.5 = move through 7 w strone faworyta
```

**13I. Wyniki, Ktore Liczymy**

Wyniki, ktore chcemy liczyc:

```text
sample_size
SU win %
ATS cover %
push %
average margin
average ATS margin
ROI przy cenie -110
CLV, jesli mamy closing line
```

Definicje:

```text
SU = straight up, czyli wygrana meczu bez spreadu
ATS = against the spread, czyli pokrycie spreadu
ATS margin = selected_team_margin + selected_team_spread
```

Settlement:

```text
ATS margin > 0 = COVER
ATS margin = 0 = PUSH
ATS margin < 0 = LOSS
```

**13J. Dodatkowe Podzialy**

Dodatkowe podzialy:

```text
favorite vs underdog
home vs away
spread bucket: 0.5-1.5 / 2-3 / 3.5-4.5 / 5-6.5 / 7-9.5 / 10+
early / middle / late season
key number crossed: 3 / 7 / 10
move through key number
move onto key number
move off key number
```

Dodajemy tez:

```text
season
week
day type: TNF / Sunday / MNF
prime time vs non-prime
neutral site
preseason spread bucket
```

**13K. Przyklady Pytan**

Przyklad pytania:

```text
Jesli underdog +3.5 przeszedl na +2.5, czyli rynek poszedl w jego strone o 1 punkt przez key number 3, jak czesto potem wygrywal SU i pokrywal ATS?
```

Inne pytania:

```text
Czy faworyt, ktory przeszedl z -2.5 na -3.5, dalej byl value czy rynek juz zabral edge?
Czy underdog, ktory dostal wiecej punktow z +3 na +4.5, byl warningiem czy okazja?
Czy brak ruchu linii przy naszym VP byl lepszy niz mocny ruch za nami?
Czy ruch 0.5 pkt ma znaczenie, czy dopiero 1.5+?
Czy ruch przez 3 jest wazniejszy niz zwykly ruch o 1 punkt poza key number?
```

**13L. Output Skryptu**

Docelowy skrypt:

```text
scripts/line_movement_history_study.py
```

Docelowy output:

```text
research/line_movement_history/
```

Pliki:

```text
line_movement_rows.csv
line_movement_bucket_summary.csv
line_movement_key_number_summary.csv
line_movement_segment_summary.csv
summary.md
data_availability_report.md
```

**13M. Minimalna Komenda Docelowa**

Planowana komenda:

```powershell
.\.venv\Scripts\python.exe scripts\line_movement_history_study.py --start-season 2015 --end-season 2025
```

Opcjonalnie:

```powershell
.\.venv\Scripts\python.exe scripts\line_movement_history_study.py --start-season 2015 --end-season 2025 --team LA
.\.venv\Scripts\python.exe scripts\line_movement_history_study.py --start-season 2015 --end-season 2025 --role UNDERDOG
.\.venv\Scripts\python.exe scripts\line_movement_history_study.py --start-season 2015 --end-season 2025 --bucket MOVE_FOR_TEAM_1
```

**13N. Jak Tego Uzyjemy W Variant B**

To badanie ma pomoc w punktach:

```text
2. market_move_notes
6. key_number_check
7. no_chase_limit
8. price_quality
17. clv_points
18. process_quality
19. final_operator_decision
```

Nie bedzie samo dawalo picka.

Ma dawac kontekst:

```text
czy ruch wspiera nasz pick
czy ruch jest warningiem
czy ruch przez key number kasuje edge
czy no-chase powinien blokowac wejscie
```

**13O. Czego Nie Robimy**

```text
nie nazywamy ruchu sharp bez zrodla
nie zakladamy, ze kazdy ruch z rynkiem jest dobry
nie zakladamy, ze kazdy ruch przeciwko nam jest zly
nie rekonstruujemy brakujacych openerow
nie laczymy danych z roznych bookow bez oznaczenia zrodla
nie uzywamy closing line jako danych dostepnych przed meczem
```

**13P. Po Co**

Po co:

```text
zeby wiedziec, czy dany typ ruchu linii historycznie byl sygnalem value, warningiem, czy tylko szumem
```

**13Q. Kiedy Punkt 13 Jest Wykonany**

Punkt 13 bedzie wykonany, gdy:

```text
skrypt sprawdzi dostepnosc pol w nfl_data_py
utworzy rows per team-game
policzy ruch z perspektywy selected_team
rozbije ruch na buckety
oznaczy key number movement
policzy SU / ATS / ROI / push
wygeneruje summary.md
oznaczy data_status FULL / PARTIAL / NOT_ASSESSABLE
```

Status:

```text
DO ZROBIENIA JAKO OSOBNY SKRYPT HISTORYCZNY
```

</details>

## 14. Bot Automatyzujacy Pregame I Postgame

Cel:

```text
zbudowac bota, ktory sam wykonuje powtarzalne czynnosci przedmeczowe i pomeczowe wedlug naszego workflow
```

Bot nie ma sam decydowac o zakladzie.

Bot ma:

```text
zbierac dane
uruchamiac skrypty
pilnowac checklisty
wykrywac braki
tworzyc raport dzienny
oznaczac status WATCH / HOLD / READY_FOR_REVIEW
czekac na decyzje operatora przy finalnym werdykcie
```

**14A. Co Bot Robi Przed Kolejka**

Wtorek:

```text
1. Pobiera schedule i linie z nfl_data_py.
2. Uruchamia basic model.
3. Tworzy liste VP/GOW/GOM/GOY.
4. Sprawdza, czy istnieje snapshot quote z pregame.com.
5. Tworzy liste meczow wymagajacych GPT 19 punktow.
6. Uruchamia Variant B z model proof.
7. Zapisuje pregame learning ledger.
8. Tworzy raport: co jest READY, WATCH, HOLD, MISSING.
```

Sroda:

```text
1. Sprawdza zmiany quote/line dla kandydatow.
2. Oznacza mecze czwartkowe jako priorytet.
3. Przypomina o GPT delta refresh dla TNF.
4. Sprawdza injury/weather/roster delty.
5. Tworzy raport dzienny.
```

Czwartek:

```text
1. Final check dla TNF.
2. Sprawdza quote, injury, inactives, weather, roster, late news.
3. Oznacza blockery.
4. Tworzy raport finalny przed kickoffem TNF.
5. Po meczu oznacza, ze wynik bedzie potrzebny do post-event.
```

Piatek:

```text
1. Glowny refresh pod niedziele.
2. Sprawdza nowe injury reports.
3. Sprawdza movement linii i quote.
4. Sprawdza weather forecast.
5. Tworzy raport dla wszystkich niedzielnych kandydatow.
```

Sobota:

```text
1. Pre-final check pod niedziele.
2. Sprawdza, ktore mecze maja komplet: quote, GPT snapshot, injury/weather/roster.
3. Oznacza READY_FOR_SUNDAY_CHECK / WATCH / HOLD / NO BET.
4. Tworzy liste brakow do uzupelnienia przed niedziela.
```

Niedziela:

```text
1. Final check kilka godzin przed kickoffem.
2. Sprawdza inactives.
3. Sprawdza finalny quote.
4. Sprawdza pogode.
5. Tworzy finalny raport dla meczow niedzielnych.
6. Opcjonalnie przygotowuje live scenario dla meczow, ktore chcesz monitorowac.
```

Poniedzialek:

```text
1. Final check dla MNF.
2. Sprawdza quote, injury, inactives, weather, late news.
3. Tworzy raport finalny MNF.
```

**14B. Co Bot Robi Po Zakonczeniu Kolejki**

Wtorek wieczor po ostatnim meczu kolejki:

```text
1. Uruchamia sync wynikow z nfl_data_py.
2. Uruchamia post-event evaluation.
3. Odpalaja sie wyniki COVER / PUSH / LOSS.
4. Aktualizuje learning report.
5. Sprawdza pending vs settled.
6. Tworzy weekly review.
7. Wypisuje bledy procesu: missing quote, brak GPT snapshot, brak closing line, stale injury, brak weather.
8. Przygotowuje kolejke do archiwizacji.
```

**14C. Czego Bot Nie Moze Robic**

```text
nie moze sam dawac finalnego betu
nie moze sam nadpisywac starych rekordow ledgeru
nie moze rekonstruowac brakujacych quote po fakcie
nie moze uznawac GPT narracji za dowod bez zrodel
nie moze promowac nowego modelu bez walk-forward i zgody operatora
```

**14D. Docelowy Output Bota**

Codzienny raport:

```text
research/bot_reports/2026/week_XX/YYYY-MM-DD_daily_status.md
```

Tygodniowy raport po kolejce:

```text
research/bot_reports/2026/week_XX/week_close_review.md
```

Statusy:

```text
READY_FOR_REVIEW
WATCH
HOLD
NO_BET
MISSING_INPUT
PENDING_RESULT
SETTLED
```

Status:

```text
DO ZROBIENIA PO USTALENIU WSZYSTKICH 13 PUNKTOW
```
