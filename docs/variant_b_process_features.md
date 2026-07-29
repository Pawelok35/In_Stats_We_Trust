# Variant B - dodatkowe feature'y procesowe

Od sezonu 2026 prowadzimy dwie wersje:

```text
Wersja A: CORE
Model + tagi: GOY, GOM, GOW, VALUE PLAY.

Wersja B: CORE + PROCESS FILTERS
To samo co A, ale przed decyzja sprawdzamy rynek, kontuzje, pogode, schedule i inne ryzyka.
```

Wersja B nie ma zgadywac wiecej. Jej cel to odpowiedziec:

```text
Czy modelowy edge nadal jest realny po rynku i kontekście?
```

## Minimalny zestaw dla Wersji B

Te pola powinny byc wypelnione przy kazdym realnym kandydacie do gry:

```yaml
argument_against:
market_move_notes:
injury_role_notes:
schedule_spot_notes:
weather_notes:
no_chase_limit:
final_operator_decision:
```

## Pelny zestaw dla Wersji B

```yaml
argument_against:
market_move_notes:
key_number_check:
no_chase_limit:
price_quality:
injury_role_notes:
schedule_spot_notes:
weather_notes:
roster_change_check:
matchup_specific_risk:
game_script_risk:
market_snapshot:
final_operator_decision:
closing_line:
closing_price:
clv_points:
```

## 1. argument_against

Najwazniejszy kontrargument przeciw pickowi.

Nie wpisujemy tutaj, dlaczego pick jest dobry. Wpisujemy, dlaczego moze byc zly.

Przyklad:

```yaml
argument_against: "Model moze przeceniac forme ofensywy, bo ostatnie dobre wyniki przyszly przeciw slabym defensywom."
```

Cel:

```text
Chroni przed potwierdzaniem wlasnej tezy.
```

## 2. market_move_notes

Opis ruchu linii.

Sprawdzamy:

```text
jaki byl opener?
jaka jest aktualna linia?
czy ruch przeszedl przez 3 albo 7?
czy rynek poszedl z nami czy przeciwko nam?
czy po ruchu nadal mamy value?
```

Przyklad:

```yaml
market_move_notes: "Open +3.5, current +2.5. Rynek poszedl z naszym underdogiem, ale stracilismy key number +3; gra tylko jesli wroci +3."
```

Cel:

```text
Nie gonic zlej ceny.
```

## 3. injury_role_notes

Kontuzje oceniane przez realna role zawodnika, nie przez sama liste nazwisk.

Sprawdzamy:

```text
czy zawodnik jest starterem?
ile gra snapow?
czy ma wazna role w konkretnym matchupie?
kto go zastepuje?
czy absencja powoduje chain reaction?
```

Przyklad:

```yaml
injury_role_notes: "LT questionable; jesli inactive, downgrade picka, bo pass rush rywala atakuje glownie te strone."
```

Cel:

```text
Oceniac realny wplyw kontuzji, nie liczbe kontuzjowanych.
```

## 4. schedule_spot_notes

Kontekst terminarza.

Sprawdzamy:

```text
krotki tydzien?
dlugi odpoczynek?
travel?
drugi wyjazd z rzedu?
divisional game?
lookahead?
letdown po duzej wygranej?
revenge spot?
bye week?
```

Przyklad:

```yaml
schedule_spot_notes: "Drugi wyjazd z rzedu i short week; nie odrzuca picka, ale zmniejsza pewnosc."
```

Cel:

```text
Zlapac sytuacje, ktorych czysty boxscore/model moze nie widziec.
```

## 5. weather_notes

Pogoda i warunki meczu.

Najwazniejsze:

```text
wiatr
deszcz/snieg
temperatura
stadion indoor/outdoor
murawa
czy pogoda wplywa bardziej na passing, kicking, total czy underdoga
```

Przyklad:

```yaml
weather_notes: "Prognoza 18 mph wind; downgrade passing-heavy favorite, spread bardziej ryzykowny."
```

Cel:

```text
Nie ignorowac warunkow, ktore zmieniaja styl gry.
```

## 6. key_number_check

Sprawdzenie, czy linia przeszla przez kluczowy numer.

W NFL najwazniejsze:

```text
3
7
```

Przyklad:

```yaml
key_number_check: "Open +3.5, current +2.5; utracono +3, value mocno slabsze."
```

Cel:

```text
Nie traktowac +2.5 i +3.5 tak samo.
```

## 7. no_chase_limit

Maksymalna albo minimalna linia, po ktorej jeszcze gramy.

Przyklad dla underdoga:

```yaml
no_chase_limit: "Play only +3 or better; pass at +2.5."
```

Przyklad dla faworyta:

```yaml
no_chase_limit: "Play -3 or better; pass at -3.5."
```

Cel:

```text
Decyzja przed emocjami. Jesli cena ucieknie, nie gonimy.
```

## 8. price_quality

Ocena jakosci aktualnej ceny dla dokladnego spreadu i wybranej strony.

Mozliwe wartosci:

```text
quote_quality_status:
  FRESH_EXECUTABLE
  FRESH_UNVERIFIED
  STALE
  SUSPENDED
  MISSING
  CONFLICTING

price_status:
  ACCEPTABLE
  UNACCEPTABLE
  REVIEW_REQUIRED
  NOT_ASSESSABLE
```

Przyklad:

```yaml
price_quality:
  selected_team: LA
  quote_quality_status: FRESH_EXECUTABLE
  price_status: ACCEPTABLE
  valuation_method: FULL_MODEL_EV
  ev_per_unit: 0.026
  reason_codes: []
```

Cel:

```text
Nie kazdy dodatni edge jest tak samo grywalny. Price quality ma potwierdzic,
czy konkretna aktualna oferta ma wymagany EV albo miesci sie w zamrozonej
acceptable_quote_frontier.
```

Zasady:

```text
1. Spread i cena musza pochodzic z tego samego quote/snapshotu.
2. Cena z agregatora jest tylko discovery, nie dowodem wykonania.
3. Bez p_cover/p_push/p_loss albo frozen frontier nie raportujemy EV.
4. Stary lub niepotwierdzony quote daje NOT_ASSESSABLE, nie automatycznie UNACCEPTABLE.
5. Standard cash bet, boost i bonus bet maja osobne formuly EV.
```

## 9. market_snapshot

Dowod rynku: zapisujemy, jaka oferta istniala, z jakiego zrodla pochodzi i jaki ma poziom wykonania.

Przyklad:

```yaml
market_snapshot:
  evidence_grade: DIRECT_BOOK_GRADE
  quote_integrity_status: VALID
  market_state: ACTIVE
  executable_status: BETSLIP_VERIFIED_AT_TARGET_STAKE
  captured_at_utc: "2026-09-10T15:00:00Z"
  quote:
    book: DraftKings
    spread: +3
    price_american: -110
    price_decimal: 1.9091
  executability:
    target_stake: 100
    stake_check_status: DISPLAYED_IN_BETSLIP
```

Cel:

```text
Miec dowod, czy cena byla tylko widoczna w feedzie, wyswietlona w booku,
sprawdzona przy docelowej stawce, czy faktycznie zaakceptowana jako ticket.
```

Poziomy dowodu:

```text
EXECUTED_GRADE    - zaklad zaakceptowany, ticket/receipt.
DIRECT_BOOK_GRADE - betslip booka sprawdzony przy target stake.
PROVIDER_GRADE    - named-book quote z feedu/API.
PREVIEW_ONLY      - manual consensus, consensus line, brak booka/timestampu.
INVALID           - niespojny quote, zly event, zly market scope, brak ceny/spreadu.
```

Zasada:

```text
Feed quote != betslip quote != accepted ticket.
```

## 10. public_bias / tickets_handle

Dane o pozycjonowaniu publicznym z konkretnych probek providerow/bookow.

Pola:

```yaml
data_status:
bias_status:
policy_id:
provider_observations:
  - provider:
    underlying_book:
    independence_group:
    sample_scope:
    sample_type:
    captured_at_utc:
    current_spread_at_capture:
    selected_team_tickets_pct:
    selected_team_handle_pct:
    opponent_tickets_pct:
    opponent_handle_pct:
    total_ticket_count:
    accumulation_window:
    splits_include_prior_line_versions:
    reason_codes:
```

Przyklad:

```yaml
public_bias:
  data_status: AVAILABLE
  bias_status: PUBLIC_ON_SELECTED_TEAM
  selected_team: LA
  provider_observations:
    - provider: DRAFTKINGS_NETWORK
      underlying_book: DRAFTKINGS_SPORTSBOOK
      sample_scope: SINGLE_BOOK_MULTI_STATE
      sample_type: REAL_WAGERS
      selected_team_tickets_pct: 68
      selected_team_handle_pct: 54
      opponent_tickets_pct: 32
      opponent_handle_pct: 46
      splits_include_prior_line_versions: true
      derived:
        handle_minus_tickets_gap_pp: -14
        average_ticket_ratio_selected_vs_opponent: 0.55
```

Cel:

```text
Rozpoznac publiczny hype, ale nie robic z tego samodzielnego typu.
Nie opisywac tego jako sharp money bez niezaleznego dowodu.
Nie laczyc procentow z roznych providerow bez denominators.
```

Zasada:

```text
Tickets/handle opisuja konkretna probke od otwarcia rynku.
Nie dowodza, kto jest sharp, ani dlaczego linia sie ruszyla.
Covers Consensus to community_sentiment, nie sportsbook handle.
```

## 11. power_rankings_check

Zewnetrzne ratingi/rankingi jako sanity check wzgledem neutralnej sily druzyn.

Sprawdzamy:

```text
czy zewnetrzne modele zgadzaja sie co do kierunku wzglednej sily?
czy zgadzaja sie takze co do wielkosci neutral-field rating gap?
czy model jest outlierem, czy tylko ma dodatkowe game-specific adjustments?
```

Przyklad:

```yaml
power_rankings_check:
  data_status: PARTIAL
  benchmark_period_status: PRESEASON_ONLY
  alignment_status: NOT_ASSESSABLE
  directional_context: RAMS_NOT_DIRECTIONALLY_ISOLATED
  reason_codes:
    - INTERNAL_NEUTRAL_POWER_GAP_MISSING
    - GAME_MARGIN_NOT_DIRECTLY_COMPARABLE_TO_POWER_RATING
```

Cel:

```text
Wykryc konflikt modelu z neutral-field benchmarkami bez mylenia miejsc 1-32
z punktowa roznica sily druzyn.
```

Zasady:

```text
1. Do punktowego porownania uzywamy internal_neutral_power_gap, nie final_model_margin.
2. ESPN FPI/PFF point ratings mozna porownywac punktowo tylko do neutral power gap.
3. FTN DVOA/EPA/Elo bez konwersji daja kierunek/tier, nie punkty.
4. NFL.com/The Athletic/media to narrative context, nie trigger MODEL_MAJOR_OUTLIER.
5. Preseason Week 1 moze miec data_status PRESEASON_ONLY i alignment_status NOT_ASSESSABLE.
```

## 12. roster_change_check

Szczegolnie wazne w Week 1-4.

Sprawdzamy:

```text
czy sklad/role/sztab roznia sie od baseline'u modelu?
czy zmiana dotyczy zawodnika/trenera materialnego dla modelu?
czy zmiana nastapila po cutoffie modelu?
```

Przyklad:

```yaml
roster_change_check:
  data_status: PARTIAL
  risk_status: NOT_ASSESSABLE
  workflow_status: PENDING_BASELINE_AND_FINAL_ROLE_RESEARCH
  reason_codes:
    - INTERNAL_ROSTER_BASELINE_MISSING
    - INTERNAL_ROLE_BASELINE_MISSING
    - FINAL_53_NOT_AVAILABLE
    - DEPTH_CHART_PRESEASON_UNRESOLVED
```

Cel:

```text
Ograniczyc blad priors przez porownanie modelowego baseline'u z aktualnym
stanem rosteru, rol, sztabu i playcallingu.
```

Zasady:

```text
1. Ruch kadrowy nie jest automatycznie ryzykiem modelowym.
2. Materialna zmiana istnieje dopiero, gdy roznica dotyczy baseline'u i waznej roli.
3. Oficjalny roster potwierdza membership, ale nie zawsze role.
4. Depth chart przed Week 1 to zwykle PRESEASON_UNRESOLVED.
5. GPT opisuje fakty; Python liczy severity/materiality.
```

## 13. matchup_specific_risk

Konkretny matchup, ktory moze zlamac driver modelowego edge.

Przyklad:

```yaml
matchup_specific_risk:
  data_status: PARTIAL
  risk_status: NOT_ASSESSABLE
  model_dependency:
    edge_driver: UNKNOWN
    dependency_status: INTERNAL_MATCHUP_REPORT_MISSING
  risk_hypotheses:
    - risk_id: SF_21_PERSONNEL_PASSING_VS_LA_21_DEFENSE
      hypothesis_type: PERSONNEL_PACKAGE_STRESS
      hypothesis_status: PRESEASON_PERSONNEL_CONFIRMATION_REQUIRED
      severity: NOT_ASSESSABLE
```

Cel:

```text
Nie opierac sie tylko na srednich druzynowych i nie tworzyc narracji
matchupowej, ktora nie dotyczy faktycznego drivera modelu.
```

Zasady:

```text
1. Najpierw model_dependency, potem szukanie kontrmatchupu.
2. Hipoteza wymaga obu stron konfliktu i sample size.
3. Historyczny matchup wymaga potwierdzenia aktualnego personnel.
4. Bez dependency map status pozostaje NOT_ASSESSABLE.
5. LLM opisuje hipoteze; Python liczy severity/risk_score.
```

## 14. game_script_risk

Czy EV picka utrzymuje sie po zdefiniowanych scenariuszach przebiegu meczu.

Przyklad:

```yaml
game_script_risk:
  data_status: NOT_ASSESSABLE
  risk_status: NOT_ASSESSABLE
  baseline_simulation:
    margin_pmf_available: false
    p_cover: null
    p_push: null
    p_loss: null
    ev: null
    simulator_type: UNKNOWN
  reason_codes:
    - MARGIN_PMF_MISSING
    - OUTCOME_PROBABILITIES_MISSING
    - SCENARIO_SIMULATION_MISSING
```

Cel:

```text
Wiedziec, czy edge jest odporny na kilka sensownych game-state stress testow,
a nie przewidywac jeden konkretny przebieg meczu.
```

Zasady:

```text
1. Scenariusze sa interwencjami w stanie meczu, nie prognozami.
2. Kazdy scenariusz musi zwrocic p_cover/p_push/p_loss i EV.
3. Dla spreadu -3 push jest osobnym wynikiem.
4. Oddzielamy prawdopodobienstwo scenariusza od jego wplywu na EV.
5. Bez stanowego symulatora status to NOT_ASSESSABLE.
```

## 15. closing_line

Post-close zapis closing quote'u: spread + cena, wyprowadzony z historii rynku.

Przyklad:

```yaml
closing_line:
  status: PENDING_NOT_CLOSED
  policy_id: NFL_PREGAME_CLOSE_V2
  decision_reference:
    spread: -3.0
    price_american: -110
    source_type: MANUAL_CONSENSUS
  closing_main_quote: null
  closing_exact_decision_line: null
  reason_codes:
    - EVENT_NOT_STARTED
    - PREGAME_MARKET_NOT_CLOSED
```

Cel:

```text
Dostarczyc atomowy closing spread + price do pozniejszego CLV,
bez mieszania same-book close z reference-market close.
```

Zasady:

```text
1. Closing line istnieje dopiero po zamknieciu pregame marketu.
2. Przed meczem status to PENDING_NOT_CLOSED, nie NOT_APPLICABLE.
3. Closing spread bez closing price jest niekompletny.
4. Closing main line i exact decision line zapisujemy osobno.
5. Close timestamp nie jest automatycznie scheduled kickoff.
```

## 16. closing_price

Cena zamkniecia rynku, czytana z tego samego `close_snapshot_id` co punkt 15.

Przyklad:

```yaml
closing_price:
  status: PENDING_NOT_CLOSED
  close_snapshot_id: null
  decision_reference:
    spread: -3.0
    price_american: -110
    source_type: MANUAL_CONSENSUS
  closing_main_quote:
    status: PENDING
    price_american: null
  closing_exact_decision_line:
    status: PENDING
    spread: -3.0
    available_at_close: UNKNOWN
    price_american: null
```

Cel:

```text
Zachowac closing price, jego pochodzenie i atomowosc bez liczenia CLV.
Punkt 17 dopiero interpretuje CLV.
```

Zasady:

```text
1. closing_price i closing_line pochodza z jednego closing_market_snapshot.
2. Zapisujemy main price i exact decision line price osobno.
3. Jesli exact line nie byla oferowana po sprawdzeniu drabiny: NOT_OFFERED_AT_CLOSE.
4. Jesli nie wiemy, czy sprawdzono alternates: MISSING/UNKNOWN.
5. Warto zapisac druga strone rynku do pozniejszego no-vig CLV.
```

## 17. clv_points

Deterministyczne obliczenie CLV z punktu 9 oraz wspolnego close snapshotu punktow 15-16.

Przyklad:

```yaml
clv_points:
  status: PENDING_NOT_CLOSED
  decision_quote:
    spread: -3.0
    price_american: -110
    evidence_grade: PREVIEW_ONLY
  closing_reference:
    close_snapshot_id: null
  spread_clv:
    status: PENDING
    spread_clv_points: null
  raw_same_line_price_clv:
    status: PENDING
  price_inclusive_clv:
    status: PENDING
    method: NOT_AVAILABLE
```

Cel:

```text
Dlugoterminowo mierzyc jakosc timing/ceny bez uzywania wyniku meczu.
```

Zasady:

```text
1. Punkt 17 nie pobiera rynku; uzywa decision_snapshot_id i close_snapshot_id.
2. Liczymy osobno spread_clv_points, raw_same_line_price_clv i price_inclusive_clv.
3. Nie sumujemy punktow spreadu i ruchu ceny.
4. Same-book, reference-book, no-vig consensus i best-available to osobne benchmarki.
5. Key-number context z punktu 6 jest wymagany do interpretacji ruchu przez 3/7.
```

## 18. process_quality

Aktualna definicja:

```text
process_quality = wewnetrzna bramka jakosci procesu, nie research internetowy i nie decyzja betu.
```

Punkt 18 czyta wyniki punktow 1-17, ich dowody, timestampy, hashe, zaleznosci i wersje regul. Rozdziela:

```text
run_status       = czy punkt wykonal sie technicznie
domain_status    = jaki natywny wynik zwrocil punkt
due_status       = czy punkt jest juz wymagany w tej fazie
criticality      = czy brak jest hard blockiem, warningiem czy kontekstem
effective_status = finalny status punktu po due/criticality
```

Readiness raportujemy osobno:

```text
research_readiness
model_audit_readiness
execution_readiness
final_prekick_readiness
post_close_readiness
```

Zasady:

```text
1. Due hard block zawsze przebija liczbowy score.
2. NOT_DUE nie obniza readiness.
3. Punkty 15-17 przed close sa PENDING_NOT_DUE, a nie bledem.
4. Punkt wykonany poprawnie moze zwrocic NOT_ASSESSABLE i nadal blokowac proces.
5. LLM moze pisac note, ale statusy bramek i liczby musza pochodzic ze skryptu/rule engine.
6. Future information leakage blokuje audyt.
```

Automatyczny status jakosci procesu.

Mozliwe statusy:

```text
basic_price_proof
complete_pre_kick
complete_with_clv
result_only
legacy_no_process_snapshot
```

Cel:

```text
Odróżnic pick z pelnym procesem od picka z samym wynikiem.
```

## 19. final_operator_decision

Aktualna definicja:

```text
final_operator_decision = deterministyczny router dzialan na bazie punktu 18.
```

Punkt 19 nie jest pickiem, rekomendacja bettingowa ani nowa analiza meczu. Nie czyta internetu, nie analizuje druzyn, nie przelicza EV/CLV/no-chase i nie zmienia blockerow z punktu 18.

Rozdzielamy dwie osie:

```text
gate_state      = OPEN | HOLD | INVALID
operator_action = HOLD_PENDING_DATA | RETURN_FOR_DATA_CORRECTION | RETURN_FOR_MODEL_RERUN | READY_FOR_NEXT_AUDIT_STAGE | AUDIT_COMPLETE | INVALID_AUDIT
```

Priorytet:

```text
1. INVALID_AUDIT
2. RETURN_FOR_DATA_CORRECTION
3. RETURN_FOR_MODEL_RERUN
4. HOLD_PENDING_DATA
5. READY_FOR_NEXT_AUDIT_STAGE
6. AUDIT_COMPLETE
```

Dla SF-LA obecnie:

```yaml
gate_state: HOLD
operator_action: RETURN_FOR_MODEL_RERUN
legacy_single_status: HOLD_PENDING_DATA
substatus: MODEL_RERUN_AND_MARKET_GRADE_SNAPSHOT_REQUIRED
hold_type: ACTIVE_REMEDIATION_REQUIRED
secondary_action: CAPTURE_MARKET_GRADE_SNAPSHOT
```

## Zasada interpretacji

```text
Wersja A = model mowi: grać / nie grać.
Wersja B = czlowiek + proces sprawdza, czy modelowy edge nadal jest realny po rynku i kontekście.
```

## Najwazniejsza zasada

Nie wpisujemy fikcyjnych danych tylko po to, zeby pick wygladal lepiej.

Jesli nie wiemy, zostawiamy pole puste albo piszemy:

```yaml
final_operator_decision: "WATCH - missing injury/market confirmation"
```
