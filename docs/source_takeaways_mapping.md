# Source takeaways mapping

Ten dokument laczy materialy, ktore analizowalismy, z realnymi elementami wdrozonymi w projekcie. Cel: wiedziec, co zostalo wykorzystane, co odlozone, a czego nie bierzemy do systemu.

## Zrodla

1. `NFL_przedmeczowa_rutyna_i_zrodla_2026_ver_2_0.pdf`
2. `Rozmowy_o_NFL_transkrypcja_forum.pdf`
3. Wnioski z rozmow o ksiazce Billy Walters `Gambler`
4. Nasze badania `nfl_data_py` dotyczace underdogow, quarter paths i live watch
5. Obecny kod projektu `In Stats We Trust`

## Statusy

- `WDROZONE` - jest w kodzie, dokumentacji albo workflow.
- `CZESCIOWO` - mamy strukture, ale wymaga recznego uzupelniania albo dalszej automatyzacji.
- `PLAN` - wartosciowe, ale jeszcze nie wdrozone.
- `ODRZUCONE` - nie pasuje do rygoru procesu albo jest zbyt spekulacyjne.

## Mapa zrodel do wdrozen

| Zrodlo | Pomysl / zasada | Status | Gdzie jest w projekcie | Co to znaczy praktycznie |
|---|---|---|---|---|
| Rutyna 2026 | GOM/model generuje kandydatow, a rynek/injuries/media tylko potwierdzaja albo odrzucaja | WDROZONE | `scripts/prospective_week_flow.py`, `docs/prospective_edge_ledger.md`, `docs/project_work_status.md` | Nie robimy pickow z samego newsa albo opinii. Najpierw model, potem kontrola rynku i ryzyk. |
| Rutyna 2026 | Glowny rynek to spread / ATS | WDROZONE | `config/lines/*`, `scripts/matchup_batch.py`, `scripts/freeze_prospective_picks.py` | Ledger wymaga `market`, `line`, `price`; domyslnie pracujemy na spreadzie. |
| Rutyna 2026 | PASS jest pelnoprawna decyzja | WDROZONE | `docs/prospective_edge_ledger.md`, `docs/project_work_status.md`, `docs/decision_guide.md` | Brak betu nie jest porazka. Jesli cena uciekla albo proces jest niepelny, nie gramy. |
| Rutyna 2026 | Fair line przed rynkiem | WDROZONE | `process_snapshot.fair_line`, `model_margin`, settlement `Fair` | Kazdy pick moze pokazac nasza linie/fair margin i edge wzgledem rynku. |
| Rutyna 2026 | Edge vs line jako centralne pytanie | WDROZONE | `edge_vs_line`, settlement `Edge`, `docs/prospective_edge_ledger.md` | Nie pytamy tylko kto wygra, ale czy cena nadal daje przewage po vig i marginesie bledu. |
| Rutyna 2026 | Zapis opening/current spread, total, price, timestamp | CZESCIOWO | `config/lines/2026/week1_lines.yaml`, `market_snapshot` w instrukcji | Current line/price/timestamp sa wdrozone. Opening i pelny multi-book snapshot sa opcjonalne/reczne. |
| Rutyna 2026 | Key numbers 3 i 7 | CZESCIOWO | `market_move_notes`, dokumentacja | Mamy pole na notatke i no-chase limit, ale nie ma jeszcze automatycznego alarmu key-number. |
| Rutyna 2026 | Nie nazywac kazdego ruchu sharp money | WDROZONE | `market_move_notes`, `docs/prospective_edge_ledger.md` | Ruch linii opisujemy jako fakt i mozliwa przyczyne, nie jako pewny dowod sharp action. |
| Rutyna 2026 | Rozroznic tickets vs handle | PLAN | brak dedykowanych pol | Wartosc zostawiona jako przyszle pola `tickets_pct`, `handle_pct`, `source_ts_utc`, jesli bedziemy recznie zbierac dane. |
| Rutyna 2026 | Power rankings jako diagnostyka, nie pick source | WDROZONE W DOKUMENTACJI | `docs/project_work_status.md`, `docs/gom_research_process.md` | Power rankings moga tlumaczyc narracje/public bias, ale nie tworza samodzielnego betu. |
| Rutyna 2026 | Kontuzje oceniac przez role, snap share, replacement i chain reaction | CZESCIOWO | `injury_role_notes` w YAML i `process_snapshot.notes` | Mamy miejsce w procesie. Automatyczne snap/depth injury scoring jeszcze nie jest gotowe. |
| Rutyna 2026 | Inactive list jako finalne potwierdzenie | PLAN | przyszly week review / pre-kick checklist | Warto dodac osobny pre-kick check przed freeze albo przed betem. |
| Rutyna 2026 | Argument przeciw wlasnemu pickowi | WDROZONE | `argument_against`, `has_argument_against`, `process_quality` | Bez realnego argumentu przeciw pick zostaje maksymalnie `basic_price_proof`, nie `complete_pre_kick`. |
| Forum | Uczyc sie struktury z darmowych preview i porownywac z wlasna ocena | WDROZONE W PROCESIE | `data/reports/comparisons`, `docs/project_work_status.md` | Zewnetrzne preview moga uczyc struktury, ale nie sa zrodlem pickow. |
| Forum | Szukac overreaction/letdown spots | PLAN | brak dedykowanego modulu | Wartosc duza, ale trzeba to zamienic na mierzalne filtry: blowout previous week, upset, market move, media jump. |
| Forum | Patrzec na public bias / lopsided money | CZESCIOWO | `market_move_notes`; brak tickets/handle pol | Uznane jako sygnal pomocniczy, nie samodzielny typ. |
| Forum | "Books always screw everyone" / rigged narrative | ODRZUCONE | brak | Nie wdrazamy jako zalozenia. Mozna traktowac tylko jako ostrzezenie przed publicznym hype. |
| Forum | Pro sports stats bywaja mniej stabilne niz college | CZESCIOWO | `docs/project_work_status.md` | W NFL szczegolnie wazne sa injuries, role, coaching, matchup i rynek. NCAAF bedzie osobna sciezka. |
| Forum | Skupic sie na jednej lidze/rynku zamiast wszystkim naraz | WDROZONE | NFL spread/ATS jako glowny workflow | Nie budujemy naraz totals, props, ML i NCAAF. Najpierw proof dla NFL ATS + live watch. |
| Forum | Organizowac notatki i wracac po meczu do jakosci analizy | WDROZONE | prospective settlement, `process_quality`, plan week review | Settlement juz istnieje. Osobny `week_review.md` jest w planie. |
| Billy Walters | Wlasna liczba/fair price przed rynkiem | WDROZONE | `model_margin`, `fair_line`, `edge_vs_line` | Najpierw nasza liczba, potem rynek. |
| Billy Walters | Dyscyplina ceny: nie grac po zlej cenie | CZESCIOWO | `market_move_notes`, `line`, `price`, `process_snapshot` | Mamy zapis i reczny no-chase. Brakuje automatycznego `max_acceptable_line`. |
| Billy Walters | Bet tylko przy przewadze, nie dla akcji | WDROZONE W DOKUMENTACJI | `PASS`, `proof_qualified`, `process_quality` | Process ma chronic przed graniem kazdego meczu. |
| Billy Walters | Oddzielic dobry proces od wyniku | WDROZONE | settlement `process_quality`, `docs/prospective_edge_ledger.md` | Wygrany pick bez procesu nie jest tak samo wartosciowy jak wygrany pick z kompletnym procesem. |
| Billy Walters | CLV jako wazny element oceny | CZESCIOWO | `closing_line`, `closing_price`, `clv_points` | Pola istnieja, ale dane wpisujemy recznie. Brak automatycznego closing-line feed. |
| Nasze badania | Q3 lead underdoga jest mocniejszy niz Q1/H1 | WDROZONE | `scripts/live_watch_card.py`, `research/in_game_underdog_study_2017_2025.md` | Live watch mocno opiera sie na stanie po Q3. |
| Nasze badania | Sam lead nie wystarczy, wazny jest przebieg kwart | WDROZONE | `scripts/analyze_quarter_paths.py`, `scripts/live_watch_card.py` | Card korzysta z flow path, margin trajectory i delta trajectory. |
| Nasze badania | Minimalna cena EV+ moze byc liczona z historycznego SU% | WDROZONE | `scripts/live_watch_card.py` | Skrypt pokazuje fair decimal i minimalna cene EV+. |
| Nasze badania | Brak historycznych live odds w `nfl_data_py` | WDROZONE JAKO OGRANICZENIE | `docs/live_watch_card.md`, `docs/project_work_status.md` | Live price wpisujesz recznie. Skrypt nie udaje, ze zna executable historical odds. |
| Obecny kod | Proof-ready validation przed freeze | WDROZONE | `scripts/validate_proof_ready_lines.py` | Nie przechodzimy dalej, jesli linie nie maja wymaganych pol proof. |
| Obecny kod | Append-only ledger | WDROZONE | `scripts/freeze_prospective_picks.py` | Rekord jest hashowany i dopisywany bez nadpisywania starych rekordow. |
| Obecny kod | Manual TODO placeholders nie moga poprawiac oceny procesu | WDROZONE | `scripts/matchup_batch.py`, `scripts/freeze_prospective_picks.py` | `TODO:` jest ignorowane, dopoki nie wpiszesz prawdziwej tresci. |

## Co wdrozylismy w kodzie po analizie zrodel

### Prospective ledger

- `process_snapshot` w kazdym frozen picku.
- `fair_line`, `market_line`, `edge_vs_line`, `price`, `decision timestamp`.
- Pola notatek: `argument_against`, `market_move_notes`, `injury_role_notes`, `schedule_spot_notes`, `weather_notes`.
- Pola przyszlego CLV: `closing_line`, `closing_price`, `clv_points`.
- `process_quality` w settlement report.
- Warningi przy braku fair line, edge lub argumentu przeciw.

### Matchup batch

- Przenoszenie opcjonalnych pol procesowych z `config/lines/.../weekX_lines.yaml` do pick JSONL.
- Ignorowanie placeholderow `TODO:`.

### Week 1 2026 config

- Dodane pola robocze przy 16 meczach.
- Walidacja proof-ready przechodzi.
- Placeholdery nie licza sie jako realne notatki.

### Live watch

- Model historycznych stanow meczu.
- Break-even / minimum EV+ live price.
- Ledger live watch i settlement.
- Weekly review po live decisions.

## Co jest odlozone do planu

### Automatyczny odds feed

Powod odlozenia: book nie jest rowny bookowi, a user bedzie wpisywal ceny recznie.

Docelowo:

- API-backed snapshots;
- kilka bookow;
- line/price timestamp;
- closing line;
- CLV.

### Tickets / handle

Powod odlozenia: bez stabilnego zrodla dane moga byc bardziej mylace niz pomocne.

Docelowo mozemy dodac pola:

```yaml
tickets_pct:
handle_pct:
betting_splits_source:
betting_splits_ts_utc:
```

### Automatyczny no-chase / max acceptable line

Powod odlozenia: trzeba ustalic reguly per spread bucket i key number.

Docelowo:

```yaml
max_acceptable_line:
min_edge_required:
key_number_crossed:
price_status:
```

### Injury role scoring

Powod odlozenia: wymaga danych depth chart, snap counts i inactive list.

Docelowo:

- starter / rotational / backup;
- snap share;
- positional value;
- replacement quality;
- chain reaction.

### Week review

Powod odlozenia: settlement juz istnieje, ale nie ma jeszcze pelnej narracyjnej recenzji procesu.

Docelowo:

- dobry proces / zly wynik;
- zly proces / dobry wynik;
- brak ceny;
- chase po key number;
- injury miss;
- market overreaction;
- model miss category.

## Co odrzucamy

1. Tezy o ustawianiu meczow jako fundament modelu.
2. Typowanie przeciw public tylko dlatego, ze public jest po jednej stronie.
3. Granie ruchu linii bez ceny, godziny i przyczyny.
4. Dopisywanie fikcyjnych argumentow przeciw po to, by podbic `process_quality`.
5. Traktowanie Week 1 jako pelnej wiarygodnosci modelu.
6. Uznawanie backtestu za dowod forward edge.

## Jak korzystac z tej mapy

Przy kazdej nowej sugestii sprawdzamy:

1. Czy da sie ja zamienic na pole, test, raport albo decyzje?
2. Czy jest mierzalna?
3. Czy jest znana przed meczem?
4. Czy nie wymaga zgadywania danych, ktorych nie mamy?
5. Czy poprawia proof ledger albo live watch?

Jesli odpowiedz brzmi tak, pomysl trafia do workflow. Jesli nie, zostaje jako notatka albo jest odrzucany.

## Aktualny brakujacy element z najwyzszym priorytetem

Najbardziej wartosciowy nastepny element to helper do wypelniania process notes dla kandydatow:

```powershell
.\.venv\Scripts\python.exe scripts\build_process_notes.py `
  --season 2026 `
  --week 1 `
  --variant variant_m
```

Docelowo helper powinien:

1. przeczytac wygenerowane picki;
2. wybrac tylko kandydatow z realnym edge;
3. przeczytac matchup report;
4. zaproponowac `argument_against`, `market_move_notes`, `injury_role_notes`, `schedule_spot_notes`, `weather_notes`;
5. zapisac propozycje do osobnego pliku review, bez automatycznego udawania finalnej decyzji.

Operator nadal zatwierdza albo poprawia notatki recznie.
