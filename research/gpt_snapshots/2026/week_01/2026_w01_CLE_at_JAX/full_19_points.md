# GPT Snapshot

season: 2026
week: 1
game_id: 2026_w01_CLE_at_JAX
snapshot_type: full_19_points
created_at_local: 2026-07-28T19:01:55.464509+02:00
source_thread: GPT

## GPT Output

audit_metadata:
game_identity:
season: 2026
week: 1
game_id: "2026_w01_CLE_at_JAX"
game_date_local: "2026-09-13"
game_date_usa: "2026-09-13"
scheduled_kickoff_local: "2026-09-13T13:00:00-04:00 — 13:00 EDT"
scheduled_kickoff_utc: "2026-09-13T17:00:00Z"
away_team: "CLE"
home_team: "JAX"
designated_home_team: "JAX"
venue: "EverBank Stadium"
venue_city_country: "Jacksonville, Florida, USA"
neutral_site: false
international_game: false
schedule_verification: "Termin, godzina, przeciwnicy i stadion są zgodne w oficjalnych terminarzach obu klubów. "
market: "full-game spread"
selected_team: "JAX"
current_spread_selected_team_raw: -7.5
current_spread_selected_team_rounded_to_0_5: -7.5
current_price: -102
total: 40.5
book_or_source: "SIM_PREGAME_COM"
quote_timestamp_utc: "2026-09-08T18:00:00Z"
executable_status: "displayed_unverified"
market_evidence_grade: "PREVIEW_ONLY"
model_version: "MISSING"
model_run_id: "MISSING"
model_generated_at_utc: "MISSING"
model_fair_margin_selected_team_raw: 19.92
model_fair_margin_selected_team_rounded_to_0_5: 20.0
model_fair_spread_selected_team_raw: -19.92
model_fair_spread_selected_team_rounded_to_0_5: -20.0
market_margin_selected_team_raw: 7.5
edge_vs_line_points_raw: 12.42
edge_vs_line_points_rounded_to_0_5: 12.5
model_tag: "GOY"
p_cover: "MISSING"
p_push: "MISSING"
p_loss: "MISSING"
margin_pmf_available: "UNKNOWN"
acceptable_quote_frontier_available: "UNKNOWN"
research_timestamp_utc: "2026-07-28T15:53:14Z"
research_cutoff_utc: "2026-07-28T15:53:14Z"
source_policy:
framework_file: "Główna instrukcja Variant B: "
hierarchy: "Oficjalne źródła NFL/klubów/obiektu/NWS jako dowód podstawowy; strony oddsowe i rankingi zewnętrzne wyłącznie jako kontekst; dane modelowe wymagają wewnętrznych, niezmiennych artefaktów."
temporal_policy: "Stan danych oceniany na rzeczywisty research cutoff 2026-07-28, a nie na przyszły timestamp symulowanego snapshotu."
calculation_policy: "Wykonano jedynie proste kontrole arytmetyczne i zaokrąglenia. EV, no-chase, price quality, scenariusze i CLV pozostawiono wewnętrznemu Pythonowi/rule engine."
warnings:
- "Quote SIM_PREGAME_COM ma timestamp 2026-09-08T18:00:00Z, czyli znajduje się w przyszłości względem research cutoff. Nie może być traktowany jako obecnie zaobserwowana ani wykonalna linia."
- "Nazwa źródła wskazuje na symulację; nie potwierdzono konkretnego operatora, quote_id, betslipu, limitu ani dostępności przy docelowej stawce."
- "Tag GOY jest wyłącznie wewnętrzną etykietą modelu i nie stanowi decyzji operatorskiej."
- "Brak model_version, model_run_id, czasu generacji, input/commit hash, PMF oraz p_cover/p_push/p_loss."
- "Oficjalne raporty kontuzji Week 1, game statuses, inactives i prognoza pogody dla okna meczu nie są jeszcze należne."
- "EverBank Stadium będzie użytkowany w sezonie 2026 przy trwającej przebudowie i ograniczonej pojemności; operacje stadionowe należy ponownie potwierdzić w tygodniu meczu. "

points:

point_number: 1
point_name: "argument_against"
purpose: "Najsilniejszy argument przeciw bezkrytycznemu przyjęciu wyniku modelu."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Kontrola arytmetyczna przechodzi: 19.92 - 7.50 = 12.42."
"Modelowa marża wynosi dokładnie 19.92 punktu, a jej prezentacja do najbliższego 0.5 wynosi 20.0."
"Edge wynosi dokładnie 12.42 punktu, a prezentacja do najbliższego 0.5 wynosi 12.5."
"Na zewnętrznej skali Spread Value nfelo JAX ma +4.5, a CLE -4.0, co daje różnicę 8.5 punktu. Jest to znacznie mniejsza wielkość niż modelowa marża 19.92, ale skale nie są bezpośrednio porównywalne bez znajomości korekt QB, home field i metodologii modelu. "
missing_data:
"model_version"
"model_run_id"
"model_generated_at_utc"
"commit_hash / input_hash / feature snapshot"
"model-generation market snapshot"
"p_cover, p_push, p_loss"
"margin PMF i raport kalibracji dla podobnych ekstremalnych marż"
"uncertainty interval / prediction interval"
"log korekty home-field i Week 1"
pending_not_due:
"Oficjalne Week 1 injury reports, game statuses, inactives i prognoza meczowa."
not_assessable:
"Pełny EV."
"Czy etykieta GOY jest skalibrowana dla edge rzędu 12.42."
"Czy marża 19.92 jest stabilna po zmianach rosteru, sztabu i startera QB CLE."
source_evidence:
source_name: "User-provided model and quote input"
source_url: "N/A — dane wejściowe użytkownika"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Model margin 19.92, market margin 7.5, edge 12.42, tag GOY i symulowany quote."
source_name: "nfelo NFL Power Ratings"
source_url: ""
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Zewnętrzny punktowy benchmark siły JAX i CLE."
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Surowy edge nie jest pełnym EV bez rozkładu prawdopodobieństwa."
deterministic_checks:
edge_formula_check: "PASS"
calculation: "19.92 - 7.50 = 12.42"
model_margin_rounding: "19.92 -> 20.0"
edge_rounding: "12.42 -> 12.5"
full_ev_check: "NOT_ASSESSABLE"
manual_review_needed:
"Wyjaśnić, które cechy wygenerowały fair margin 19.92."
"Sprawdzić, czy podobne historyczne predykcje były poprawnie skalibrowane i czy model nie produkuje nadmiernie skrajnych wartości w Week 1."
"Zweryfikować założenia dotyczące QB CLE, zmian sztabu i rosteru."
recommended_machine_fields:
"model_lineage_id"
"feature_snapshot_hash"
"fair_margin_interval_low/high"
"p_cover/p_push/p_loss"
"calibration_bucket_count"
"model_edge_driver_contributions"
test_game_output:
strongest_argument_against: "Największym kontrargumentem jest obecnie brak dowodu, że bardzo duża marża 19.92 jest skalibrowana i została wyliczona na aktualnym rosterze oraz na rzeczywistym rynku. Towarzyszący quote jest przyszłodatowany i symulowany, a brak PMF uniemożliwia przełożenie 12.42 punktu surowego edge na prawdopodobieństwo pokrycia lub EV."
external_sanity_check: "nfelo kierunkowo uznaje JAX za silniejsze, ale nie potwierdza skali 19.92; wynik traktowany wyłącznie jako kontekst."
full_ev: "NOT_ASSESSABLE"
reason_codes:
"RAW_EDGE_NOT_FULL_EV"
"MODEL_LINEAGE_MISSING"
"PMF_MISSING"
"EXTREME_MARGIN_REQUIRES_CALIBRATION"
"FUTURE_SIMULATED_QUOTE"
point_number: 2
point_name: "market_move_notes"
purpose: "Oddzielić opener, quote z chwili generacji modelu i aktualny wykonalny quote."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Przekazany snapshot to JAX -7.5 przy -102, ale ma przyszły timestamp i źródło SIM_PREGAME_COM; nie jest obserwowalnym quote na research cutoff."
"ScoresAndOdds pokazuje kontekstowo opener JAX -7 przy -110 oraz późniejszą prezentację JAX -7.5 przy -110. Źródło nie dostarcza audytowalnego named-book quote_id ani dokładnych timestampów każdego kroku, dlatego ścieżka nie jest dowodem klasy execution/provider. "
"Bezpośrednia strona Sky Bet prezentowała JAX -7.5 po kursie 10/11 i total 40.5, ale nie potwierdza ceny -102, źródła SIM ani dostępności przy docelowej stawce. "
missing_data:
"Audytowalny opener: named book, spread, price, timestamp, quote_id."
"Niezmienny model-generation quote."
"Rzeczywisty current executable quote z betslipu."
"Append-only quote ledger."
"Jednolita konwencja źródeł i zakres rynku."
pending_not_due: []
not_assessable:
"Dokładna zmiana od opener do model-generation quote."
"Dokładna zmiana od model-generation quote do current executable quote."
"Atrybucja przyczyny ruchu."
"No-chase status."
source_evidence:
source_name: "ScoresAndOdds NFL odds board"
source_url: ""
source_tier: "SECONDARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Kontekstowa prezentacja open -7 i późniejszego -7.5; nie zastępuje wewnętrznego ledgera."
source_name: "Sky Bet event page"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Bezpośrednia prezentacja JAX -7.5 po 10/11 i total 40.5 na moment dostępu."
source_name: "User-provided SIM snapshot"
source_url: "N/A — dane wejściowe użytkownika"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "JAX -7.5, -102, timestamp 2026-09-08T18:00:00Z."
deterministic_checks:
opener_to_current_delta: "NOT_ASSESSABLE"
model_quote_to_current_delta: "NOT_ASSESSABLE"
key_number_path: "NOT_CONFIRMED"
attribution_label: "NONE"
manual_review_needed:
"Nie przepisywać wtórnego opener -7 do oficjalnego ledgera bez named-book i timestampu."
"W dniu snapshotu uchwycić linię i cenę z jednego atomowego quote."
recommended_machine_fields:
"quote_event_id"
"quote_type: opener/model_generation/current"
"book_id"
"spread"
"price"
"captured_at_utc"
"provider_timestamp_utc"
"market_scope"
"max_stake"
test_game_output:
opener: "MISSING — istnieje wyłącznie wtórny kontekst -7."
model_generation_quote: "MISSING"
supplied_scenario_quote: "JAX -7.5 / -102 / SIM_PREGAME_COM / 2026-09-08T18:00:00Z"
current_executable_quote: "MISSING"
movement_summary: "Nie można sporządzić audytowalnej ścieżki ruchu. Jedno źródło wtórne sugeruje -7 do -7.5, ale nie jest to wystarczające do przypisania ruchu ani do no-chase."
reason_codes:
"OPENER_NOT_AUDIT_GRADE"
"MODEL_GENERATION_QUOTE_MISSING"
"CURRENT_EXECUTABLE_QUOTE_MISSING"
"NO_MOVEMENT_ATTRIBUTION"
"DO_NOT_RECONSTRUCT_QUOTE"
point_number: 3
point_name: "injury_role_notes"
purpose: "Zidentyfikować kontuzje, statusy i niepewności ról mogące zmieniać modelowy edge."
automation_level: "SEMI"
due_status: "NOT_DUE"
criticality: "HARD_WHEN_DUE"
confirmed_facts:
"Oficjalna strona Browns informuje, że sezon 2025 się zakończył i aktualny raport kontuzji 2026 pojawi się dopiero na początku sezonu. "
"Oficjalna strona NFL nie publikuje jeszcze inactives dla sezonu 2026. "
"CLE umieściło DT Malieka Collinsa na active/PUP 23 lipca. Jest to status obozowy, a nie potwierdzenie nieobecności w Week 1. "
"JAX umieściło OL Garrett DiGiorgio i OL Cole’a Van Lanena na active/PUP 26 lipca. Status nie przesądza ich Week 1 availability. "
"Na research cutoff CLE nadal miało otwartą rywalizację QB obejmującą Dillona Gabriela, Taylena Greena, Shedeura Sandersa i Deshauna Watsona; starter Week 1 nie był potwierdzony. "
"Oficjalny primer Jaguars wskazywał, że Travis Hunter miał rozpocząć camp po rehabilitacji kolana, lecz jego zakres gry ofensywa/defensywa pozostawał tematem do monitorowania. Nie jest to formalny status Week 1. "
missing_data:
"Pierwszy oficjalny Week 1 practice participation report obu klubów."
"Final game-status report."
"Official inactives."
"Starter QB CLE i plan podziału snapów."
"Snap/role projection dla Huntera."
"Statusy Van Lanena, DiGiorgio i Collinsa po zakończeniu campu."
"Replacement quality i chain-reaction map dla każdej potencjalnej absencji."
pending_not_due:
"Pierwszy practice report w tygodniu meczu."
"Final injury designation około 48 godzin przed meczem."
"Inactives przed kickoffem."
not_assessable:
"Ostateczny injury impact na spread."
"Czy wskazani zawodnicy zagrają w Week 1."
"Wpływ wyboru QB CLE na fair margin."
source_evidence:
source_name: "Cleveland Browns official injury report"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Formalny raport 2026 nie został jeszcze opublikowany."
source_name: "NFL official inactives"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Brak aktualnych inactives dla sezonu."
source_name: "Official team transactions and role reports"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Active/PUP, nierozstrzygnięty QB CLE i aktualny kontekst Huntera."
deterministic_checks:
formal_report_due: false
inactives_due: false
healthy_team_inference_allowed: false
active_pup_equals_week1_out: false
manual_review_needed:
"Po publikacji raportów przypisać starter/backup, przewidywany snap share, replacement i unit impact."
"Nie importować starych statusów out z agregatorów jako Week 1 2026."
recommended_machine_fields:
"player_id"
"team"
"official_status"
"practice_participation"
"role_tier"
"expected_snap_share"
"replacement_player_id"
"unit_impact"
"report_timestamp_utc"
test_game_output:
injury_status_now: "PENDING_NOT_DUE"
current_monitor_list:
"CLE DT Maliek Collins — active/PUP"
"JAX OL Cole Van Lanen — active/PUP"
"JAX OL Garrett DiGiorgio — active/PUP"
"CLE starting QB — UNKNOWN"
"JAX Travis Hunter role/workload — UNKNOWN"
no_health_assumption: true
reason_codes:
"FORMAL_INJURY_REPORT_NOT_DUE"
"INACTIVES_NOT_DUE"
"ACTIVE_PUP_NOT_EQUAL_WEEK1_OUT"
"CLE_QB_ROLE_UNRESOLVED"
"HUNTER_WORKLOAD_UNRESOLVED"
point_number: 4
point_name: "schedule_spot_notes"
purpose: "Ocenić termin, rest, podróż, strefę czasową, neutralność i kontekst obiektu."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Mecz odbędzie się w niedzielę 13 września 2026 o 13:00 EDT w EverBank Stadium. "
"JAX jest rzeczywistym gospodarzem; mecz nie jest neutral-site ani international game."
"Jest to Week 1, dlatego nie istnieje regular-season rest differential wynikający z meczu w poprzednim tygodniu."
"Oba oficjalne terminarze podają godzinę w EDT, więc nie występuje zmiana zegarowa między Cleveland i Jacksonville w dniu meczu. "
"Jaguars rozgrywają sezon 2026 w Jacksonville przy ograniczonej pojemności w związku z przebudową EverBank Stadium. "
missing_data:
"Dokładny plan podróży CLE."
"Data i godzina przylotu do Jacksonville."
"Hotel, miejsce walk-through i plan aklimatyzacji."
"Ewentualne opóźnienia lub zmiany operacyjne wynikające z przebudowy."
pending_not_due:
"Oficjalne informacje klubowe o podróży i praktykach w tygodniu meczu."
"Game-day stadium operations notice."
not_assessable:
"Przewaga lub niekorzystna asymetria podróżna."
"Wpływ czasu przyjazdu CLE na performance."
source_evidence:
source_name: "Jacksonville Jaguars official schedule"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Week 1, data, kickoff, przeciwnik i EverBank Stadium."
source_name: "Cleveland Browns official schedule"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "CLE jako drużyna wyjazdowa, identyczna data, godzina i stadion."
source_name: "Jaguars Stadium of the Future"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Sezon 2026 w Jacksonville przy ograniczonej pojemności i trwającej przebudowie."
deterministic_checks:
local_to_utc_conversion: "2026-09-13 13:00 EDT -> 2026-09-13 17:00 UTC"
neutral_site_check: "FALSE"
international_game_check: "FALSE"
regular_season_rest_differential: "NONE — Week 1"
timezone_clock_shift: "0 hours"
manual_review_needed:
"Nie przypisywać przewagi podróżnej bez planu podróży lub informacji o aklimatyzacji."
"Ponownie sprawdzić komunikaty stadionowe przed meczem."
recommended_machine_fields:
"travel_departure_utc"
"travel_arrival_utc"
"time_zone_shift_hours"
"distance_km"
"days_on_site"
"venue_operations_status"
test_game_output:
schedule_spot: "Standardowy krajowy road game CLE w Week 1, bez zmiany strefy zegarowej."
travel_advantage_claim: "NOT_ASSESSABLE"
venue_context: "EverBank Stadium, przebudowa i ograniczona pojemność w sezonie 2026."
reason_codes:
"WEEK1_NO_PRIOR_GAME_REST_DIFFERENTIAL"
"DOMESTIC_ROAD_GAME"
"NO_TIMEZONE_SHIFT"
"TRAVEL_ITINERARY_MISSING"
"VENUE_CONSTRUCTION_MONITOR"
point_number: 5
point_name: "weather_notes"
purpose: "Ocenić pogodę w oknie meczu oraz ryzyko operacyjne obiektu i murawy."
automation_level: "SEMI"
due_status: "NOT_DUE"
criticality: "HARD_WHEN_DUE"
confirmed_facts:
"Oficjalny punkt prognozowy NWS dla lokalizacji stadionu obejmuje tylko bieżący krótki horyzont i nie obejmuje 13 września 2026. "
"Oficjalne materiały Jaguars opisują obecny EverBank Stadium jako obiekt bez dachu, podczas gdy przyszły zadaszony projekt ma zostać ukończony w 2028; jest to przesłanka, że pogoda pozostaje operacyjnie istotna w sezonie 2026. "
"Stadion jest w przebudowie; oficjalny fan guide opisuje możliwe zmiany w poruszaniu się i operacjach obiektu. "
missing_data:
"Prognoza NWS dla dokładnego game window."
"Temperatura, heat index, wiatr średni i porywy."
"Prawdopodobieństwo i intensywność opadów."
"Burze, lightning protocol i ewentualne ostrzeżenia."
"Wilgotność."
"Potwierdzenie nawierzchni i jej stanu dla Week 1 2026."
"Oficjalny field/venue operations notice."
pending_not_due:
"Pierwsza prognoza obejmująca 2026-09-13."
"Aktualizacja około 72/48/24/6 godzin przed kickoffem."
"Radar, observations i warnings w dniu meczu."
not_assessable:
"Weather adjustment do fair margin."
"Wpływ pogody na game script, kicking, passing i tempo."
source_evidence:
source_name: "National Weather Service point forecast"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Oficjalna prognoza nie obejmuje jeszcze daty meczu."
source_name: "Jaguars official stadium sources"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Brak obecnego dachu, przebudowa oraz kontekst operacyjny."
deterministic_checks:
official_forecast_covers_game_window: false
roof_protection: "NO — inference from official current/future stadium descriptions"
surface_2026_verified: false
manual_review_needed:
"Nie używać obecnej pogody ani norm klimatycznych jako prognozy meczowej."
"Potwierdzić nawierzchnię po zakończeniu letnich prac stadionowych."
recommended_machine_fields:
"forecast_issued_at_utc"
"game_window_temperature"
"heat_index"
"wind_sustained"
"wind_gust"
"precip_probability"
"thunderstorm_probability"
"surface_condition"
"weather_alerts"
test_game_output:
weather_status: "PENDING_NOT_DUE"
venue_weather_exposure: "OUTDOOR/UNROOFED — recheck game week"
surface: "UNKNOWN_FOR_2026"
reason_codes:
"FORECAST_WINDOW_NOT_OPEN"
"UNROOFED_VENUE"
"SURFACE_RECHECK_REQUIRED"
"CONSTRUCTION_OPERATIONS_MONITOR"
point_number: 6
point_name: "key_number_check"
purpose: "Określić pozycję spreadu względem kluczowych liczb i logiki push."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Dokładny spread to JAX -7.5; wartość prezentacyjna do 0.5 również wynosi -7.5."
"Linia znajduje się pół punktu po niekorzystnej stronie podstawowego key number 7 dla faworyta."
"Przy zakończonym meczu i standardowym rozliczeniu wynik punktowy jest całkowity, dlatego dokładny push na -7.5 nie występuje. Modelowe pole p_push pozostaje jednak MISSING, ponieważ nie dostarczono PMF ani house rules."
"Wtórny board pokazuje opener -7 i późniejsze -7.5, ale nie jest to wystarczający dowód, aby w audycie stwierdzić przekroczenie 7 przez konkretny, wykonalny rynek. "
missing_data:
"Wewnętrzny quote event ledger."
"Named-book opener i cała ścieżka quote."
"Wersjonowana konfiguracja key numbers."
"Sportsbook house rules dotyczące OT, anulowania i settlement."
"Margin PMF."
pending_not_due: []
not_assessable:
"Wartość probabilistyczna pół punktu między -7 i -7.5."
"Czy modelowy quote pierwotnie był na -7, -7.5 lub innym poziomie."
"Key-number-adjusted EV."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "3 i 7 jako podstawowe key numbers oraz wymóg zachowania logiki push."
source_name: "ScoresAndOdds context board"
source_url: ""
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Wtórny kontekst -7 do -7.5, bez statusu audytowego."
deterministic_checks:
exact_spread: -7.5
rounded_spread: -7.5
nearest_primary_key_number: 7
distance_from_key_number_points: 0.5
current_position: "FAVORITE_SIDE_BEYOND_7"
standard_completed_game_push_possible: false
confirmed_market_crossing: false
manual_review_needed:
"Nie oznaczać crossed 7 bez właściwego ledgera."
"Po dostarczeniu PMF policzyć cenę pół punktu 7 -> 7.5."
recommended_machine_fields:
"key_number_config_version"
"spread_path"
"settlement_rules_id"
"probability_margin_exact_7"
"half_point_value_7_to_7_5"
test_game_output:
key_number_status: "JAX -7.5 jest 0.5 punktu poza kluczowym 7."
arrived_or_crossed: "UNKNOWN"
push_logic: "Brak standardowego push na -7.5; p_push modelu nadal MISSING."
reason_codes:
"HALF_POINT_LINE"
"BEYOND_KEY_7"
"PATH_NOT_CONFIRMED"
"HOUSE_RULES_MISSING"
point_number: 7
point_name: "no_chase_limit"
purpose: "Sprawdzić, czy aktualny quote mieści się w zamrożonym acceptable frontier."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Przekazany quote nie może pełnić funkcji aktualnego executable quote, ponieważ jest przyszłodatowany i symulowany."
"Nie dostarczono model-generation quote, frozen no-chase policy ani acceptable quote frontier."
missing_data:
"Immutable model-generation quote."
"No-chase policy version."
"Acceptable quote frontier."
"PMF oraz p_cover/p_push/p_loss."
"Eligible-books policy."
"Current direct-book quote przy docelowej stawce."
"House rules."
pending_not_due: []
not_assessable:
"ALLOWED / REVIEW / BLOCKED."
"Maksymalny spread i minimalna cena."
"Czy ruch od model-generation quote naruszył limit."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Zakaz ręcznego rekonstruowania model-generation quote i wymóg frozen frontier."
source_name: "User-provided SIM snapshot"
source_url: "N/A — dane wejściowe użytkownika"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Future-dated JAX -7.5 / -102."
deterministic_checks:
frozen_policy_present: false
model_generation_quote_present: false
executable_quote_present: false
no_chase_result: "NOT_ASSESSABLE"
manual_review_needed:
"Nie odtwarzać model-generation quote z obecnych stron oddsowych."
"Dostarczyć oryginalny artefakt z momentu uruchomienia modelu."
recommended_machine_fields:
"policy_version"
"model_quote_id"
"max_allowed_spread"
"min_allowed_price"
"acceptable_quote_frontier_id"
"chase_distance_points"
test_game_output:
no_chase_status: "NOT_ASSESSABLE"
blocking_reason: "Brak frozen frontier, model-generation quote i aktualnego executable quote."
reason_codes:
"NO_CHASE_POLICY_MISSING"
"ACCEPTABLE_FRONTIER_MISSING"
"MODEL_QUOTE_MISSING"
"EXECUTABLE_QUOTE_MISSING"
"MANUAL_RECONSTRUCTION_PROHIBITED"
point_number: 8
point_name: "price_quality"
purpose: "Ocenić wykonalność ceny i jej wystarczalność przy push-aware EV."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Cena -102 pochodzi wyłącznie z future-dated SIM_PREGAME_COM."
"Sky Bet na moment dostępu prezentował tę samą linię -7.5 po 10/11, a ScoresAndOdds -7.5 przy -110; źródła te nie walidują ceny -102 ani jej dostępności przy docelowej stawce. "
missing_data:
"p_cover, p_push, p_loss."
"Margin PMF."
"Acceptable quote frontier."
"Direct betslip i target stake."
"Quote_id i limit."
"House rules."
"Aktualny eligible book."
pending_not_due: []
not_assessable:
"Expected value."
"Minimalna akceptowalna cena."
"Price edge."
"Czy -102 jest rzeczywiście osiągalne."
source_evidence:
source_name: "Sky Bet event page"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Kontekstowa, bezpośrednia oferta -7.5 po 10/11; nie jest ofertą -102 z SIM."
source_name: "ScoresAndOdds board"
source_url: ""
source_tier: "SECONDARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Wtórny kontekst -7.5 przy -110."
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Price quality wymaga prawdopodobieństw, frontier i executable quote."
deterministic_checks:
atomic_sim_price_present: true
independently_verified: false
target_stake_verified: false
break_even_probability: "PENDING_INTERNAL_PYTHON"
ev: "NOT_ASSESSABLE"
manual_review_needed:
"Sprawdzić betslip u kwalifikującego się operatora przy rzeczywistej stawce."
"Nie zastępować ceny -102 kursem z innego źródła."
recommended_machine_fields:
"direct_quote_id"
"target_stake"
"max_stake"
"available_price"
"minimum_required_price"
"push_adjusted_ev"
"book_eligibility"
test_game_output:
price_quality_status: "NOT_ASSESSABLE"
supplied_price: -102
evidence_status: "PREVIEW_ONLY"
reason_codes:
"SIM_PRICE_UNVERIFIED"
"PROBABILITIES_MISSING"
"TARGET_STAKE_NOT_CHECKED"
"HOUSE_RULES_MISSING"
point_number: 9
point_name: "market_snapshot"
purpose: "Uchwycić dokładny, atomowy quote decyzji lub wykonania."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dostarczony rekord zawiera event, stronę JAX, full-game spread -7.5, cenę -102, źródło SIM_PREGAME_COM i timestamp 2026-09-08T18:00:00Z."
"Timestamp znajduje się po research cutoff, dlatego rekord może być zachowany jako scenario/simulation input, lecz nie jako obecnie zaobserwowany snapshot."
"Zewnętrzne strony kierunkowo potwierdzają linię -7.5 i total 40.5, lecz nie potwierdzają ceny -102 ani źródła SIM. "
missing_data:
"Rzeczywisty named book."
"Quote_id."
"Direct betslip."
"Target stake i max stake."
"Provider receive timestamp."
"Potwierdzenie atomicity spread + price."
"Sportsbook jurisdiction i house rules."
pending_not_due: []
not_assessable:
"Czy cena była kiedykolwiek wykonalna."
"Czy rekord pochodzi z aktualnego rynku czy wyłącznie symulatora."
source_evidence:
source_name: "User-provided SIM_PREGAME_COM snapshot"
source_url: "N/A — dane wejściowe użytkownika"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Wszystkie pola przekazanego snapshotu."
source_name: "Direct and secondary external odds context"
source_url: ""
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Kontekst -7.5/40.5; brak walidacji -102."
deterministic_checks:
event_identity_present: true
market_scope_present: true
spread_and_price_present: true
timestamp_present: true
timestamp_observable_at_cutoff: false
quote_id_present: false
target_stake_check_present: false
evidence_grade: "PREVIEW_ONLY"
manual_review_needed:
"Zachować rekord jako simulation_scenario, nie current_executable_quote."
"Utworzyć nowy, append-only snapshot, gdy realna oferta zostanie odczytana."
recommended_machine_fields:
"snapshot_id"
"scenario_or_observation"
"book_id"
"quote_id"
"captured_at_utc"
"provider_timestamp_utc"
"target_stake"
"max_stake"
"evidence_grade"
test_game_output:
event: "CLE at JAX"
side: "JAX"
market_scope: "full-game spread"
spread: -7.5
price: -102
source: "SIM_PREGAME_COM"
timestamp: "2026-09-08T18:00:00Z"
executable_status: "displayed_unverified"
evidence_grade: "PREVIEW_ONLY"
usability: "Scenario input only; not valid as current execution evidence."
reason_codes:
"FUTURE_DATED_QUOTE"
"SIMULATED_SOURCE"
"QUOTE_ID_MISSING"
"TARGET_STAKE_MISSING"
"NOT_EXECUTION_GRADE"
point_number: 10
point_name: "public_bias"
purpose: "Dostarczyć kontekst tickets/handle bez przypisywania jakości pieniądza."
automation_level: "SEMI"
due_status: "UNKNOWN"
criticality: "CONTEXT_ONLY"
confirmed_facts:
"Action Network wyświetla dla tego meczu 100% Bets i 0% Money po stronie prezentowanej jako Jaguars, ale strona nie pokazuje denominatora, liczby zakładów, źródła booka ani czasu aktualizacji. Dane zostały wykluczone z oceny. "
missing_data:
"Provider-specific tickets percentage."
"Provider-specific handle percentage."
"Sample size."
"Market scope."
"Book/jurisdiction."
"Timestamp i denominator rules."
"Frozen public-splits capture policy."
pending_not_due:
"Wiarygodne, opisane splity bliżej kickoffu, o ile pojawią się w kwalifikującym źródle."
not_assessable:
"Public concentration."
"Znaczenie wyświetlonych procentów."
"Jakakolwiek atrybucja jakości ruchu."
source_evidence:
source_name: "Action Network matchup page"
source_url: ""
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Istnienie wyświetlonych procentów bez wystarczających metadanych."
deterministic_checks:
usable_split_sources: 0
cross_provider_average_allowed: false
public_bias_result: "UNKNOWN"
manual_review_needed:
"Nie importować procentów bez denominatora i timestampu."
"Nie łączyć danych z różnych operatorów."
recommended_machine_fields:
"provider"
"book"
"market_scope"
"tickets_pct"
"handle_pct"
"sample_size"
"captured_at_utc"
"denominator_definition"
test_game_output:
tickets_handle_status: "MISSING/UNUSABLE"
public_bias_conclusion: "UNKNOWN"
reason_codes:
"SPLITS_WITHOUT_DENOMINATOR"
"SPLITS_TIMESTAMP_MISSING"
"NO_PUBLIC_BIAS_CONCLUSION"
point_number: 11
point_name: "power_rankings_check"
purpose: "Porównać wewnętrzną ocenę siły z zewnętrznym benchmarkiem punktowym."
automation_level: "SEMI"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"nfelo prezentuje JAX na miejscu 8 z nfelo 1600 i Spread Value +4.5. "
"nfelo prezentuje CLE na miejscu 26 z nfelo 1386 i Spread Value -4.0. "
"Różnica na tej skali wynosi +8.5 punktu na korzyść JAX."
"Modelowa marża JAX 19.92 jest o 11.42 punktu większa od tego zewnętrznego benchmarku, ale porównanie nie jest apples-to-apples bez korekt QB, HFA, daty bazowej i metodologii."
missing_data:
"internal_neutral_power_gap"
"internal market-implied neutral rating"
"Aktualne wartości ESPN FPI, PFF Point Spread Ratings i FTN DVOA/DAVE w porównywalnym formacie."
"Dokładna interpretacja modelowego HFA zawartego w 19.92."
pending_not_due:
"Aktualizacje rankingów po campie, preseason i potwierdzeniu startera QB CLE."
not_assessable:
"Pełna triangulacja rankings."
"Czy różnica 11.42 wynika z unikalnych informacji modelu czy z błędu/starego baseline."
source_evidence:
source_name: "nfelo NFL Power Ratings"
source_url: ""
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Punktowy zewnętrzny benchmark JAX i CLE."
deterministic_checks:
nfelo_spread_value_jax: 4.5
nfelo_spread_value_cle: -4.0
external_gap_jax: 8.5
model_margin_jax: 19.92
unadjusted_difference: 11.42
directly_comparable: false
manual_review_needed:
"Ustalić, czy modelowa marża zawiera HFA i założenie konkretnego QB."
"Porównać z co najmniej dwoma dodatkowymi punktowymi ratingami."
recommended_machine_fields:
"internal_neutral_power_gap"
"external_rating_provider"
"external_point_gap"
"qb_adjustment"
"home_field_adjustment"
"rating_timestamp"
test_game_output:
external_direction: "JAX stronger"
external_magnitude_support_for_19_92: "NOT_CONFIRMED"
power_rankings_status: "PARTIAL"
reason_codes:
"EXTERNAL_DIRECTIONAL_SUPPORT"
"MAGNITUDE_DIVERGENCE"
"INTERNAL_NEUTRAL_GAP_MISSING"
"NOT_APPLES_TO_APPLES"
point_number: 12
point_name: "roster_change_check"
purpose: "Sprawdzić, czy zmiany rosteru, sztabu i ról czynią baseline modelu nieaktualnym."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Todd Monken został head coachem Browns 28 stycznia 2026. "
"Browns zbudowali nowy sztab na 2026, w tym OC Travisa Switzera i DC Mike’a Rutenberga. "
"Browns oficjalnie odnotowują transfer Mylesa Garretta do Rams w zamian m.in. za Jareda Verse’a i wybory draftowe. "
"Jaguars utrzymali na sezon 2026 koordynatorów Granta Udinskiego, Anthony’ego Campanile i Heatha Farwella. "
"JAX wymieniło Maasona Smitha do Falcons, otrzymując Ruke’a Orhorhoro. "
"Na końcu lipca aktywne były obozowe oznaczenia PUP dla Malieka Collinsa oraz OL JAX Cole’a Van Lanena i Garretta DiGiorgio. "
"Rola starting QB CLE pozostaje nierozstrzygnięta. "
missing_data:
"Frozen internal roster baseline użyty przy model run."
"Frozen staff baseline."
"Frozen depth-chart i role baseline."
"Starter assumptions w modelu."
"Snap-weighted roster deltas."
"Model rerun trigger policy."
pending_not_due:
"Finalny 53-man roster."
"Week 1 depth chart."
"Ostateczne role po preseason."
not_assessable:
"Czy model uwzględnił nowy sztab Browns, wymianę Garretta, nową strukturę frontu oraz nierozstrzygniętego QB."
"Czy baseline jest stale."
source_evidence:
source_name: "Official Browns coaching and transaction sources"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Nowy HC/sztab i ważne zmiany rosteru CLE."
source_name: "Official Jaguars staff and transaction sources"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Ciągłość koordynatorów i zmiany rosteru JAX."
deterministic_checks:
frozen_internal_baseline_present: false
baseline_delta_computable: false
roster_staleness_status: "NOT_ASSESSABLE"
manual_review_needed:
"Porównać każdy potwierdzony ruch z datą i zawartością modelowego snapshotu."
"Sprawdzić, którego QB CLE model traktuje jako startera."
recommended_machine_fields:
"baseline_cutoff_utc"
"baseline_roster_hash"
"baseline_staff_hash"
"baseline_depth_chart_hash"
"current_roster_hash"
"material_change_flag"
"rerun_required"
test_game_output:
current_material_change_candidates:
"CLE: nowy HC i koordynatorzy"
"CLE: Garrett out / Verse in"
"CLE: starter QB UNKNOWN"
"JAX: Maason Smith out / Ruke Orhorhoro in"
"PUP monitor dla obu linii"
baseline_stale: "NOT_ASSESSABLE"
reason_codes:
"FROZEN_BASELINE_MISSING"
"CLE_NEW_COACHING_STAFF"
"CLE_MAJOR_FRONT_CHANGE"
"CLE_QB_ASSUMPTION_UNKNOWN"
"JAX_ROSTER_DELTA_PRESENT"
point_number: 13
point_name: "matchup_specific_risk"
purpose: "Przetestować konkretne konflikty matchupowe wobec przyczyn modelowego edge."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Nie dostarczono feature contributions ani internal matchup dependency report, dlatego nie można rozpocząć od faktycznych driverów modelu."
"Istnieją trzy potwierdzone obszary wymagające testu: nierozstrzygnięty QB CLE, dostępność/role OL JAX oraz nowa kompozycja frontu CLE po transferze Garretta i przy PUP Collinsa. "
"Zakładany dwustronny workload Travisa Huntera pozostaje nieustalony i może wpływać na modelowe założenia snapów. "
missing_data:
"Internal edge drivers."
"Feature contribution report."
"Sensitivity report."
"Projected starters i snap shares."
"Current EPA/success splits dopasowane do nowych składów."
"Protection/pass-rush matchup po zmianach personalnych."
"Model dependence on CLE QB identity."
pending_not_due:
"Role clarity po campie i preseason."
"Week 1 official depth charts i injuries."
not_assessable:
"Czy JAX ma konkretną przewagę matchupową uzasadniającą marżę 19.92."
"Czy zmiany CLE neutralizują lub wzmacniają założenia modelu."
source_evidence:
source_name: "Official role, transaction and injury-designation sources"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Kandydaci do testów matchupowych, bez przesądzania przewagi."
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Analiza ma rozpoczynać się od driverów modelu, a nie losowej narracji."
deterministic_checks:
model_driver_report_present: false
matchup_dependency_report_present: false
matchup_conclusion: "NOT_ASSESSABLE"
manual_review_needed:
"Przetestować fair margin pod każdym realnym kandydatem na QB CLE."
"Zmapować status OL JAX na protection metrics."
"Zaktualizować front CLE i snap assumptions po wymianie Garretta."
"Ustalić oddzielne snap projections Huntera w ofensywie i defensywie."
recommended_machine_fields:
"edge_driver_name"
"driver_contribution_points"
"dependency_player_id"
"dependency_status"
"sensitivity_delta_points"
"matchup_conflict_flag"
test_game_output:
matchup_specific_result: "NOT_ASSESSABLE"
candidate_tests:
"CLE QB identity sensitivity"
"JAX OL availability vs rebuilt CLE front"
"Hunter two-way snap allocation"
narrative_status: "No unsupported matchup advantage asserted."
reason_codes:
"MODEL_EDGE_DRIVERS_MISSING"
"MATCHUP_DEPENDENCY_REPORT_MISSING"
"ROLE_UNCERTAINTY"
"NO_RANDOM_NARRATIVE"
point_number: 14
point_name: "game_script_risk"
purpose: "Stress-testować edge pod alternatywnymi scenariuszami przebiegu meczu."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Nie dostarczono simulatora, possession modelu, margin PMF ani p_cover/p_push/p_loss."
"Duży raw edge 12.42 nie mówi samodzielnie, jak kruchy jest wynik na early turnovers, wybór QB CLE, tempo, pass rate lub wariancję krótkiego pola."
missing_data:
"Possession/play-by-play simulator."
"Margin PMF."
"Scenario policy."
"Pace/pass-rate inputs."
"Turnover and field-position distributions."
"Lead/neutral/trail efficiency."
"Roster, injury i weather overrides."
pending_not_due:
"Finalne roster/injury/weather inputs."
not_assessable:
"Cover probability w poszczególnych game scripts."
"Tail risk i downside scenarios."
"Czy edge jest zależny od szybkiego prowadzenia JAX."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Bez simulatora lub PMF game-script risk ma być NOT_ASSESSABLE."
deterministic_checks:
simulator_available: false
margin_pmf_available: "UNKNOWN"
scenario_matrix_generated: false
game_script_result: "NOT_ASSESSABLE"
manual_review_needed:
"Nie tworzyć procentów scenariuszy narracyjnie."
"Uruchomić frozen scenario set po ustaleniu QB, injuries i weather."
recommended_machine_fields:
"scenario_policy_version"
"scenario_id"
"scenario_probability"
"cover_probability_by_scenario"
"expected_possessions"
"turnover_delta"
"lead_state_distribution"
test_game_output:
game_script_risk: "NOT_ASSESSABLE"
required_scenarios:
"JAX early lead"
"One-score neutral game through three quarters"
"CLE early lead"
"High-turnover variance"
"Weather/pace suppression if applicable"
reason_codes:
"SIMULATOR_MISSING"
"PMF_MISSING"
"SCENARIO_POLICY_MISSING"
"NO_NARRATIVE_PROBABILITIES"
point_number: 15
point_name: "closing_line"
purpose: "Uchwycić końcowy pregame spread."
automation_level: "HYBRID"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts:
"Kickoff jest zaplanowany na 2026-09-13T17:00:00Z. "
"Rynek nie został jeszcze zamknięty."
missing_data:
"close_snapshot_id"
"Final pregame spread."
"Named book/provider."
"Actual market close timestamp."
"Full closing ladder."
pending_not_due:
"Capture rzeczywistego close po zamknięciu rynku."
not_assessable:
"Closing line."
source_evidence:
source_name: "Official team schedules"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Planowana godzina kickoffu; nie jest automatycznie timestampem zamknięcia rynku."
source_name: "Internal append-only quote ledger"
source_url: "MISSING"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "N/A"
supports_claim: "Wymagany przyszły close snapshot."
deterministic_checks:
market_closed: false
scheduled_kickoff_used_as_close: false
closing_line: "POST_EVENT_ONLY"
manual_review_needed:
"Nie utożsamiać zaplanowanego kickoffu z faktycznym zamknięciem rynku."
recommended_machine_fields:
"close_snapshot_id"
"market_closed_at_utc"
"closing_spread"
"closing_book"
"full_ladder"
test_game_output:
closing_line: "POST_EVENT_ONLY"
reason_codes:
"MARKET_NOT_CLOSED"
"CLOSE_SNAPSHOT_NOT_DUE"
"KICKOFF_NOT_ASSUMED_AS_CLOSE"
point_number: 16
point_name: "closing_price"
purpose: "Uchwycić cenę z tego samego snapshotu co closing line."
automation_level: "HYBRID"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts:
"Nie istnieje jeszcze close snapshot."
missing_data:
"close_snapshot_id"
"Closing price."
"Closing spread z tego samego atomowego rekordu."
"Obie strony closing ladder."
pending_not_due:
"Capture closing price po zamknięciu rynku."
not_assessable:
"Closing price."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Closing price musi pochodzić z tego samego snapshotu co closing line."
deterministic_checks:
close_snapshot_present: false
closing_line_price_atomicity: "NOT_ASSESSABLE"
manual_review_needed:
"Nie łączyć spreadu z jednego źródła z ceną z innego źródła."
recommended_machine_fields:
"close_snapshot_id"
"closing_spread"
"closing_price"
"opposite_side_price"
"captured_at_utc"
test_game_output:
closing_price: "POST_EVENT_ONLY"
reason_codes:
"CLOSE_SNAPSHOT_NOT_DUE"
"ATOMIC_CLOSE_REQUIRED"
point_number: 17
point_name: "clv_points"
purpose: "Policzyć CLV osobno dla spreadu i ceny."
automation_level: "FULL"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts:
"Decision snapshot nie ma obecnie klasy execution-grade."
"Closing line i closing price nie istnieją."
missing_data:
"Valid decision_snapshot_id."
"close_snapshot_id."
"Closing spread i price."
"Selected-team spread convention."
"Key-number-aware CLV policy."
pending_not_due:
"CLV calculation po uzyskaniu close."
not_assessable:
"Spread CLV."
"Price CLV."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Zakaz liczenia CLV bez punktów 15 i 16 oraz zakaz łączenia spread i price CLV."
deterministic_checks:
valid_decision_snapshot: false
valid_close_snapshot: false
spread_clv: "POST_EVENT_ONLY"
price_clv: "POST_EVENT_ONLY"
combined_fake_clv_created: false
manual_review_needed:
"Po meczu uruchomić rule engine na dwóch atomowych snapshotach."
recommended_machine_fields:
"decision_snapshot_id"
"close_snapshot_id"
"spread_clv_points"
"price_clv"
"key_number_context"
test_game_output:
clv_points: "POST_EVENT_ONLY"
price_clv: "POST_EVENT_ONLY"
reason_codes:
"DECISION_SNAPSHOT_NOT_EXECUTION_GRADE"
"CLOSE_MISSING"
"NO_CLV_CALCULATION"
point_number: 18
point_name: "process_quality"
purpose: "Zastosować wewnętrzny gate jakości do punktów 1–17."
automation_level: "FULL"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Tożsamość meczu, data, kickoff i stadion zostały potwierdzone dwoma oficjalnymi terminarzami. "
"Prosta matematyka model margin minus market margin przechodzi."
"Quote rynkowy nie spełnia obecnie wymogów current executable evidence."
"Formalne injury/weather są prawidłowo sklasyfikowane jako NOT_DUE, a closing/CLV jako POST_EVENT_ONLY; nie powinny być liczone jako bieżące błędy procesu."
missing_data:
"Process policy registry i criticality registry."
"Model lineage bundle."
"Model-generation quote."
"Current executable snapshot."
"PMF/probabilities/frontier."
"Frozen roster baseline."
"Simulator/scenario artifacts."
"Evidence manifest i calculation manifest."
pending_not_due:
"Official Week 1 injury report."
"Inactives."
"Game-window weather."
"Closing line, closing price i CLV."
not_assessable:
"Numeryczny process-quality score."
"Pełna zgodność z nieudostępnionym policy registry."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Not-due nie jest failure; due hard blockers mają pierwszeństwo."
source_name: "Official schedules"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Identity/schedule domain jest potwierdzony."
deterministic_checks:
due_hard_blockers_override_score: true
not_due_counted_as_failure: false
post_event_counted_as_current_failure: false
numeric_process_score: "NOT_ASSESSABLE"
manual_review_needed:
"Potwierdzić krytyczność punktów 12 i 14 w wewnętrznym policy registry."
"Zarejestrować ewentualne manual overrides."
recommended_machine_fields:
"run_status"
"domain_status"
"gate_effect"
"effective_status"
"readiness_phase"
"blocker_id"
"override_log_id"
test_game_output:
run_status: "HOLD"
domain_status:
game_identity: "PASS"
schedule_venue: "PASS"
model_arithmetic: "PASS_LIMITED"
model_lineage: "BLOCKED"
market_evidence: "BLOCKED"
probabilities_and_ev: "BLOCKED"
injury_report: "PENDING_NOT_DUE"
weather: "PENDING_NOT_DUE"
roster_baseline: "BLOCKED"
matchup_review: "LIMITED"
game_script_simulation: "BLOCKED"
closing_and_clv: "POST_EVENT_ONLY"
due_status:
due_domains: "PARTIAL/BLOCKED"
not_due_domains: "PROPERLY_DEFERRED"
post_event_domains: "EXCLUDED_FROM_CURRENT_GATE"
criticality:
effective_hard_blockers:
"Market snapshot"
"Model lineage"
"PMF/probabilities/frontier"
"Frozen roster baseline"
"Game-script simulator/PMF"
gate_effect: "HOLD"
effective_status: "PRE-RESEARCH PARTIAL; NOT READY FOR DECISION-QUOTE PHASE"
readiness_by_phase:
identity_and_schedule_research: "READY"
preseason_context_research: "PARTIAL_READY"
execution_quote_audit: "NOT_READY"
game_week_injury_weather_refresh: "NOT_DUE"
post_event_clv: "POST_EVENT_ONLY"
reason_codes:
"IDENTITY_VERIFIED"
"MARKET_EVIDENCE_BLOCKER"
"MODEL_LINEAGE_BLOCKER"
"PROBABILITY_INPUT_BLOCKER"
"ROSTER_BASELINE_BLOCKER"
"NOT_DUE_ITEMS_EXCLUDED"
"POST_EVENT_ITEMS_EXCLUDED"
point_number: 19
point_name: "final_operator_decision"
purpose: "Deterministycznie skierować audyt do następnego działania bez decyzji bettingowej."
automation_level: "FULL"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Punkt 18 ma status HOLD z powodu due hard blockers."
"Braki injury/weather nie są obecnie przyczyną niepowodzenia, ponieważ nie są jeszcze należne."
missing_data:
"Frozen operator decision policy."
"Manual override log."
"Operator decision ledger."
pending_not_due:
"Game-week injuries, inactives i weather."
"Closing/CLV."
not_assessable:
"Przejście do pełnej decision/execution stage."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:53:14Z"
supports_claim: "Dozwolone stany gate/operator_action i zakaz wyniku PLAY/PASS."
deterministic_checks:
point_18_status: "HOLD"
prohibited_betting_recommendation_generated: false
manual_review_needed:
"Dostarczyć brakujące artefakty i ponownie uruchomić deterministic gate."
recommended_machine_fields:
"decision_id"
"gate_state"
"operator_action"
"hold_type"
"required_action_ids"
"policy_version"
"override_log_id"
test_game_output:
gate_state: "HOLD"
operator_action: "HOLD_PENDING_DATA"
hold_type: "MARKET_EVIDENCE_MODEL_LINEAGE_AND_INTERNAL_PROBABILITY_ARTIFACTS"
required_actions:
"Zachować przekazany SIM_PREGAME_COM rekord jako future simulation scenario, a nie current executable quote."
"Dostarczyć model_version, model_run_id, model_generated_at_utc, input/commit hash i immutable model-generation quote."
"Dostarczyć margin PMF oraz p_cover/p_push/p_loss."
"Dostarczyć acceptable quote frontier, no-chase policy, eligible-books policy i house rules."
"Uchwycić realny named-book quote: spread i price z jednego betslipu, timestamp, quote_id oraz target-stake check."
"Dostarczyć frozen roster/staff/depth-chart baseline."
"Dostarczyć feature contributions oraz simulator/scenario policy albo formalnie oznaczyć je jako nieobowiązkowe w policy registry."
nonblocking_pending_items:
"Official Week 1 injury reports."
"Official inactives."
"NWS game-window forecast."
"Closing spread/price i CLV."
prohibited_transitions:
"Nie obliczać EV."
"Nie wyznaczać no-chase status."
"Nie zatwierdzać price quality."
"Nie wyliczać CLV."
"Nie oznaczać audit complete."
"Nie wydawać decyzji PLAY/PASS."
decision_provenance:
framework: ""
research_cutoff_utc: "2026-07-28T15:53:14Z"
process_snapshot_status: "PARTIAL"
manual_override: "MISSING/NONE PROVIDED"
reason_codes:
"GATE_HOLD"
"HOLD_PENDING_DATA"
"NO_BETTING_DECISION"
"FUTURE_SIM_SNAPSHOT"
"INTERNAL_ARTIFACTS_REQUIRED"

summary:
hard_blockers:
- "Brak bieżącego, wykonalnego i atomowego market snapshotu. Future-dated SIM quote jest wyłącznie scenario input."
- "Brak model lineage: version, run_id, generated_at, hashes i model-generation quote."
- "Brak PMF oraz p_cover/p_push/p_loss, więc EV i price quality są NOT_ASSESSABLE."
- "Brak acceptable quote frontier i frozen no-chase policy."
- "Brak frozen roster/staff/role baseline, mimo istotnych zmian CLE i nierozstrzygniętego QB."
- "Brak simulatora lub PMF potrzebnego do game-script stress test."
warnings:
- "Wtórne źródło pokazuje kontekst -7 do -7.5, ale nie może zastąpić append-only quote ledgera. "
- "Bezpośrednia oferta Sky Bet potwierdza tylko kontekst -7.5/40.5, nie cenę -102 ani wykonanie. "
- "nfelo kierunkowo wspiera wyższą ocenę JAX, lecz nie potwierdza modelowej skali 19.92. "
- "Obiekt jest w przebudowie i będzie działał z ograniczoną pojemnością. "
pending_not_due:
- "Official Week 1 practice reports i final game statuses."
- "Official inactives."
- "NWS forecast/observations dla game window."
- "Game-day venue operations."
- "Closing spread, closing price i CLV."
internal_inputs_required_from_me:
- "model_version"
- "model_run_id"
- "model_generated_at_utc"
- "commit/input/feature hashes"
- "model-generation quote snapshot"
- "p_cover/p_push/p_loss"
- "margin PMF"
- "acceptable quote frontier"
- "no-chase policy"
- "eligible-books policy i house rules"
- "frozen roster/staff/role baseline"
- "feature contribution report"
- "scenario simulator/policy"
data_to_capture_manually:
- "Named-book betslip przy docelowej stawce."
- "Spread, price, book, timestamp i quote_id z jednego atomowego rekordu."
- "Pierwszy i finalny official injury report."
- "Official inactives."
- "NWS forecast w oknach 72/48/24/6h."
- "Close snapshot z linią i ceną."
next_best_action: "Traktować ten dokument jako pre-research audit. Najpierw uzupełnić model lineage, PMF/frontier i frozen baseline. Przekazany future SIM quote zachować w osobnym polu scenario_quote; nie przepisywać go do current_executable_quote. Kolejny audyt quote powinien korzystać z rzeczywiście uchwyconej oferty z timestampem niepóźniejszym niż cutoff danego uruchomienia."

final_summary:
audit_readiness_now: "HOLD — identity/schedule research jest gotowy, ale audyt nie jest gotowy do decision/execution stage."
due_hard_blockers:
- "Current executable atomic quote: MISSING."
- "Model lineage i immutable model-generation quote: MISSING."
- "PMF oraz p_cover/p_push/p_loss: MISSING."
- "Acceptable quote frontier/no-chase policy: MISSING."
- "Frozen roster/staff/role baseline: MISSING."
- "Game-script simulator lub formalna polityka zastępcza: MISSING."
not_due_items:
- "Official injury reports."
- "Final game statuses."
- "Inactives."
- "Game-window weather."
- "Final venue operations notice."
post_event_only_items:
- "Closing line."
- "Closing price."
- "Spread CLV."
- "Price CLV."
data_i_must_enter_manually:
- "Model version/run ID/generated_at/hashes."
- "Model-generation quote."
- "PMF i cover/push/loss probabilities."
- "Frontier i no-chase policy."
- "Frozen roster baseline."
- "Realny named-book betslip z target-stake check."
data_gpt_found_with_sources:
- "Mecz: Cleveland Browns at Jacksonville Jaguars, 13 września 2026, 13:00 EDT / 17:00 UTC, EverBank Stadium. "
- "Jaguars pozostają w Jacksonville w 2026 przy ograniczonej pojemności i trwającej przebudowie stadionu. "
- "Formalny injury report i inactives nie są jeszcze opublikowane. "
- "Aktualne active/PUP: CLE Maliek Collins; JAX Garrett DiGiorgio i Cole Van Lanen. "
- "CLE ma nowego HC/sztab i nierozstrzygniętą rolę starting QB. "
- "Zewnętrzny kontekst rynku potwierdza występowanie JAX -7.5 i totalu 40.5, ale nie waliduje ceny -102. "
- "Oficjalna prognoza NWS nie obejmuje jeszcze dnia meczu. "
data_that_requires_internal_python:
- "Push-aware EV."
- "Break-even i minimalna wymagana cena."
- "Acceptable quote frontier."
- "No-chase classification."
- "PMF/key-number value dla -7 vs -7.5."
- "Roster-adjusted rerun."
- "Game-script simulation."
- "Spread CLV i price CLV po close."
next_step_for_me: "Uzupełnić artefakty modelowe i utworzyć poprawny current_executable_quote. Injury/weather pozostawić jako PENDING_NOT_DUE do właściwych okien czasowych."
safe_to_advance_to_next_audit_stage: false
betting_pick_or_recommendation_generated: false
