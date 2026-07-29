# In Stats We Trust - Plan Ulepszen

Ten dokument zbiera propozycje ulepszen projektu. Bedziemy mogli przechodzic je punkt po punkcie, dopisywac decyzje, zakres prac i status.

## 1. Porzadek w danych i artefaktach

Repo wyglada na mocno obciazone wygenerowanymi plikami: raportami, pickami, audytami, obrazami i katalogami tymczasowymi.

Status: rozpoczete.

Decyzja robocza:

- Nowe artefakty generowane pod `data/` sa domyslnie ignorowane przez git.
- Wyjatki dla danych testowych powinny trafiac do `data/fixtures/` albo `data/samples/`.
- Pliki juz sledzone przez git wymagaja osobnego kroku `git rm --cached`; nie usuwamy ich bez oddzielnej decyzji.
- Szczegolowa polityka jest opisana w `docs/artifact_policy.md`.

Proponowane dzialania:

- Ustalic, ktore pliki sa kodem i konfiguracja, a ktore sa artefaktami generowanymi.
- Przeniesc lub ignorowac artefakty typu `data/reports/generated`, `data/tmp_*`, `data/picks_variant_*`.
- Rozwazyc DVC, artifact store albo osobny katalog poza git dla duzych danych.
- Zostawic w repo tylko male przyklady testowe, potrzebne do smoke/E2E.

Cel:

- Czystszy `git status`.
- Szybsze review.
- Latwiejsze odtwarzanie pipeline bez mieszania kodu z wynikami.

## 2. Jeden oficjalny pipeline tygodnia

W projekcie jest duzo skryptow pomocniczych w `scripts/`, co sugeruje, ze czesc logiki zyje poza glownym CLI.

Status: rozpoczete.

Decyzja robocza:

- Oficjalnym wejsciem operacyjnym jest `python -m app.cli`.
- Skrypty w `scripts/` moga zostac jako implementacja pomocnicza albo narzedzia developerskie.
- Nowe komendy uzytkowe powinny byc dodawane do `app.cli`.
- Szczegoly sa opisane w `docs/cli_workflow.md`.

Proponowane dzialania:

- Ustalic jeden oficjalny interfejs do budowania tygodnia.
- Przeniesc najwazniejsze operacje do `app.cli`.
- Zostawic skrypty jako cienkie wrappery albo narzedzia developerskie.

Docelowe komendy:

```bash
python -m app.cli build-week --season 2025 --week 12
python -m app.cli evaluate-picks --season 2025
python -m app.cli generate-matchups --season 2025 --week 12
```

Cel:

- Jedno miejsce uruchamiania glownego workflow.
- Mniej rozproszonej logiki.
- Latwiejszy onboarding i automatyzacja.

## 3. Backtesting jako pierwszorzedny produkt

Projekt generuje picki i warianty, wiec kluczowe pytanie brzmi: czy model realnie bije baseline.

Status: rozpoczete.

Decyzja robocza:

- Reuzywalna logika backtestingu trafia do `metrics/backtest.py`.
- Oficjalna komenda to `python -m app.cli evaluate-picks`.
- Pierwsza wersja raportuje W/L/P/Pending, win rate, units i ROI.
- ROI zaklada domyslne -110, dopoki picki nie zapisuja jawnych kursow.
- Szczegoly sa opisane w `docs/backtesting.md`.

Proponowane dzialania:

- Dodac modul backtestingu, np. `metrics/backtest.py` albo `app/evaluation.py`.
- Liczyc wyniki per sezon, tydzien, wariant i market.
- Porownywac model do prostych baseline.

Metryki do raportowania:

- Win rate.
- ROI.
- Closing line value.
- Hit rate per confidence bucket.
- Wynik per wariant.
- Wynik per typ sygnalu.

Cel:

- Oddzielenie realnie skutecznych sygnalow od szumu.
- Latwiejsze decyzje o tym, ktory wariant rozwijac.
- Mocniejsza wiarygodnosc calego projektu.

## 4. Mniej wariantow, wiecej selekcji

W projekcie istnieje wiele wariantow pickow. To pomaga eksperymentowac, ale utrudnia decyzje produktowe.

Status: rozpoczete.

Decyzja robocza:

- Warianty dostaja statusy w `config/tag_variants.yaml`.
- Statusy: `champion`, `challenger`, `experimental`, `retired`.
- Dokladnie jeden wariant powinien miec status `champion`.
- `scripts/tag_variant_runner.py` domyslnie uruchamia tylko `champion` + `challenger`.
- Szczegoly sa opisane w `docs/variant_policy.md`.

Proponowane dzialania:

- Wprowadzic podejscie champion/challenger.
- Wybrac jeden wariant produkcyjny.
- Utrzymywac tylko kilka aktywnych challengerow.
- Automatycznie porownywac warianty po kazdym tygodniu.

Proponowane statusy wariantow:

- `champion`
- `challenger`
- `experimental`
- `retired`

Cel:

- Mniej szumu.
- Jasna odpowiedz, ktory wariant jest obecnie najlepszy.
- Latwiejsza kontrola eksperymentow.

## 5. Silniejsze kontrakty dla L4 i pickow

Projekt ma dobre fundamenty kontraktow dla warstw ETL. Warto rozszerzyc te zasady na metryki i picki.

Status: rozpoczete.

Decyzja robocza:

- `config/contracts.yaml` obejmuje teraz `L4_CORE12`, `L4_POWERSCORE` i `PICK_OUTPUT`.
- Core12 i PowerScore waliduja dane przed zapisem.
- Backtesting waliduje picki JSONL przed ocena.
- Minimalny kontrakt pickow odpowiada obecnemu formatowi plikow; pola `market`, `model_version` i `created_at` zostaja jako kolejny etap po zmianie generatora.
- Szczegoly sa opisane w `docs/contracts_l4_picks.md`.

Proponowane dzialania:

- Dodac kontrakty dla `l4_core12`.
- Dodac kontrakty dla `l4_powerscore`.
- Dodac kontrakty dla plikow pickow JSONL.
- Dodac walidacje raportow matchup.

Minimalne pola picka:

- `season`
- `week`
- `game_id`
- `team`
- `opponent`
- `market`
- `pick`
- `confidence`
- `edge`
- `model_version`
- `created_at`

Cel:

- Mniej cichych bledow.
- Stabilny format danych.
- Latwiejszy backtesting i frontend.

## 6. Metadata wersji modelu i danych

Kazdy pick i raport powinien byc odtwarzalny. Trzeba wiedziec, z jakiej wersji kodu, configu i danych powstal.

Status: rozpoczete.

Decyzja robocza:

- Wspolny helper metadanych jest w `utils/run_metadata.py`.
- Manifesty dostaja `commit_sha` i `code_is_dirty`.
- Nowe picki JSONL dostaja `model_version`, `commit_sha`, `config_hashes`, `config_sha256`, `data_cutoff` i `source_report`.
- Pola metadanych sa opcjonalne w `PICK_OUTPUT`, zeby stare picki nadal byly czytelne.
- Szczegoly sa opisane w `docs/run_metadata.md`.

Proponowane dzialania:

- Dodac `model_version` do pickow i raportow.
- Zapisywac hash configu.
- Zapisywac commit hash, jesli repo jest w git.
- Zapisywac data cutoff.
- Zapisywac wersje wag i profilu wariantu.

Przykladowe pola:

- `commit_sha`
- `config_sha256`
- `weights_profile`
- `data_cutoff`
- `generated_at`

Cel:

- Pelna odtwarzalnosc wynikow.
- Latwiejsze wyjasnianie zmian po rerunie.
- Lepsza kontrola eksperymentow.

## 7. Frontend jako dashboard operacyjny

Frontend juz istnieje, wiec warto przesunac go w strone narzedzia decyzyjnego, nie tylko prezentacji raportow.

Status: rozpoczete.

Decyzja robocza:

- Frontend ma endpoint `GET /api/picks?season=&week=`.
- Dashboard pokazuje operacyjna kolejke pickow z JSONL wariantow.
- Widok obsluguje filtry statusu wariantu i decyzji (`bet`, `lean`, `avoid`, `no bet`).
- Klikniecie picka probuje otworzyc odpowiadajacy mu raport matchup.
- Szczegoly sa opisane w `docs/frontend_dashboard.md`.

Proponowane dzialania:

- Dodac widok tygodnia z sortowaniem po `edge`, `confidence`, `PowerScore`.
- Dodac drilldown dla matchup.
- Dodac porownanie wariantow.
- Dodac historie wynikow dla typu sygnalu.
- Dodac flagi `bet`, `lean`, `avoid`, `no bet`.

Cel:

- Szybsze podejmowanie decyzji.
- Lepsze wykorzystanie danych.
- Mniej recznego przegladania plikow `.md` i `.jsonl`.

## 8. Dokumentacja decyzyjna

README opisuje projekt, ale warto dodac dokumentacje odpowiadajaca na pytania operacyjne.

Status: rozpoczete.

Decyzja robocza:

- Glowny przewodnik decyzyjny jest w `docs/decision_guide.md`.
- Indeks dokumentacji jest w `docs/README.md`.
- README wskazuje przewodnik operacyjny zamiast duplikowac wszystkie instrukcje.
- Przewodnik opisuje flow tygodnia, ocene wynikow, zrodla prawdy, artefakty, elementy eksperymentalne i interpretacje sygnalow.

Proponowane dzialania:

- Opisac jak wygenerowac tydzien od zera.
- Opisac jak sprawdzic, czy wynik jest dobry.
- Wskazac zrodla prawdy dla kodu, configu i artefaktow.
- Oznaczyc elementy eksperymentalne.
- Opisac interpretacje `PowerScore`, `confidence`, `edge` i wariantow.

Cel:

- Latwiejszy onboarding.
- Mniej zgadywania.
- Lepsza kontrola nad rozwojem projektu.

## Priorytet startowy

Najpierw warto zajac sie dwoma tematami:

1. Porzadek w danych i artefaktach.
2. Backtesting jako pierwszorzedny produkt.

Te dwa punkty dadza najwiekszy zwrot, bo oczyszcza repo i pokaza, ktore czesci modelu faktycznie tworza wartosc.
