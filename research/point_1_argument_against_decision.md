# Punkt 1 - argument_against: decyzja po GPT Pro

## Status

```text
Punkt 1 zaakceptowany.
```

Nie robimy tego jako recznego eseju. Finalny kierunek to:

```yaml
argument_against:
  mode: hybrid_red_team
  auto_rules: true
  statistical_checks: true
  manual_gate: true
```

Czyli system sam generuje kontrargument z danych i reguł, a czlowiek tylko
zatwierdza/usuwa zdania, ktore wymagaja interpretacji.

## Najwazniejszy wniosek

`argument_against` nie ma odpowiadac:

```text
Czy grac?
```

Ma odpowiadac:

```text
Jaki jest najsilniejszy powod, dla ktorego ten pick moze nie miec realnego edge?
```

## Co wdrazamy z odpowiedzi GPT Pro

### 1. Hybrid red-team process

Przyjmujemy jako docelowa architekture:

```text
deterministic validation -> statistical red-team -> domain-shift checks -> evidence layer -> final argument
```

To znaczy:

- najpierw sprawdzamy matematyke picka;
- potem sprawdzamy czy edge jest realny statystycznie;
- potem czy kontekst meczu nie jest poza normalnym zakresem modelu;
- potem dopiero skladamy tekst kontrargumentu.

### 2. `argument_against_auto` ma byc generowany z reguł

Docelowy format:

```yaml
argument_against_auto:
  risk_level:
  strongest_argument:
  confirmed_risks:
  conditional_risks:
  missing_data:
  tests_that_would_clear_the_argument:
  human_review_required:
```

Nie ma byc luznego promptu typu: "wymysl kontrargument".

### 3. Reguly do wdrozenia jako pierwsze

```yaml
rules:
  - ARG-001_PICK_MATH_INTEGRITY
  - ARG-002_MARKET_SNAPSHOT_PROVENANCE
  - ARG-003_ROUNDING_THRESHOLD_ARTIFACT
  - ARG-004_MEAN_MARGIN_WITHOUT_DISTRIBUTION
  - ARG-006_PRICE_OR_PUSH_NOT_MODELED
  - ARG-008_OUT_OF_DISTRIBUTION_CONTEXT
  - ARG-009_NEUTRAL_SITE_HOME_FIELD_LEAKAGE
  - ARG-011_WEEK_1_UNCERTAINTY_NOT_INFLATED
  - ARG-013_EDGE_FRAGILITY
  - ARG-014_CONFIDENCE_TIER_NOT_INDEPENDENT
```

### 4. Najwazniejsze dla naszego modelu juz teraz

Na tym etapie najbardziej praktyczne sa:

```text
1. Czy matematyka picka sie zgadza?
2. Czy linia/cena/book maja timestamp i da sie je odtworzyc?
3. Czy VALUE PLAY nie powstal przez zaokraglenie?
4. Czy fair margin jest tylko srednia, czy mamy p_cover / p_push / p_loss?
5. Czy spread jest na integer/key number, np. -3?
6. Czy mecz jest neutral-site/international i model nie dal zwyklego home field?
7. Czy edge jest zbyt delikatny wobec niepewnosci Week 1?
8. Czy tier VALUE/GOW/GOM/GOY ma osobna kalibracje, czy tylko powtarza edge?
```

## Co odrzucamy albo zostawiamy na pozniej

Nie wdrazamy teraz jako automatycznych argumentow:

- kontuzji konkretnych zawodnikow bez oficjalnego feedu;
- pogody bez wiarygodnego game-window forecast;
- public bias bez tickets/handle;
- narracji typu travel favors one team;
- opinii o motywacji, crowd, revenge, familiarity bez twardych danych;
- automatycznych wnioskow, ze unusual context pomaga przeciwnej stronie.

Te rzeczy moga wejsc pozniej jako `manual_checks`, ale nie jako twarde reguly.

## Finalna odpowiedz na punkt 1

```text
Tak, punkt 1 da sie zautomatyzowac w duzym stopniu.

Najlepszy model pracy to hybrid red-team:
system automatycznie wykrywa najwiekszy kontrargument przeciw pickowi,
a czlowiek zatwierdza tylko te elementy, ktore wymagaja interpretacji.

Wersja 1 nie musi jeszcze znac kontuzji, pogody i public money.
Wersja 1 musi umiec wykryc:
- blad matematyki;
- brak market snapshot;
- rounding artifact;
- fair margin bez p_cover/p_push/p_loss;
- ryzyko push przy spreadzie -3;
- neutral-site home-field leakage;
- out-of-distribution context;
- edge fragility;
- brak niezaleznej kalibracji tieru.
```

## Test game - SF at LA

Dla meczu:

```text
2026 Week 1
San Francisco 49ers at Los Angeles Rams
Melbourne, Australia
LA -3.0
Model fair margin raw: LA -4.99
Model fair margin rounded: LA -5.0
Edge raw: +1.99
Edge rounded: +2.0
```

Najlepszy `argument_against`:

```text
Najsilniejszy argument przeciw traktowaniu LA -3 jako potwierdzonego VALUE PLAY
jest taki, ze +1.99 pkt edge jest na razie roznica miedzy fair margin i market
line, ale nie pelnym dowodem EV. Przy -3 potrzebujemy p_cover, p_push i p_loss,
bo wygrana LA dokladnie 3 punktami jest pushem. Dodatkowo mecz jest w Week 1,
na neutralnym miedzynarodowym obiekcie w Australii, wiec trzeba sprawdzic czy
model nie przypisal Rams zwyklego home-field oraz czy jego niepewnosc dla takiego
kontekstu nie kasuje przewagi. Brakuje tez pelnego market snapshot: book, timestamp
i potwierdzenie, ze -3/-110 bylo realnie dostepne.
```

## Czy mozemy przejsc do punktu 2?

```text
Tak, punkt 1 jest wystarczajaco dobrze zdefiniowany.
```

Przed punktem 2 warto jednak zapisac reguly `ARG-001` do `ARG-014` w pliku YAML,
zeby pozniej skrypt mogl generowac `argument_against_auto` bez recznego promptowania.

