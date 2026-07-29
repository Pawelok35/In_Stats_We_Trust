# GPT Snapshot

season: 2026
week: 1
game_id: 2026_w01_GB_at_MIN
snapshot_type: full_19_points
created_at_local: 2026-07-28T18:08:10.581553+02:00
source_thread: GPT

## GPT Output

audit_metadata:
game_identity:
season: 2026
week: 1
game_id: "2026_w01_GB_at_MIN"
game_date_local: "2026-09-13"
game_date_usa: "2026-09-13"
scheduled_kickoff_local: "2026-09-13T15:25:00-05:00"
scheduled_kickoff_utc: "2026-09-13T20:25:00Z"
away_team: "GB"
home_team: "MIN"
venue: "U.S. Bank Stadium"
venue_city_country: "Minneapolis, Minnesota, USA"
neutral_site: false
international_game: false
designated_home_team: "MIN"
schedule_confirmation: "Oba oficjalne terminarze klubów wskazują Week 1, niedzielę 13 września 2026, godzinę 3:25 PM CDT i U.S. Bank Stadium. "
venue_address: "401 Chicago Avenue, Minneapolis, MN 55415. "
market: "full-game spread"
selected_team: "GB"
current_spread_selected_team:
exact: 1.0
signed_display: "GB +1.0"
nearest_0_5: 1.0
push_condition: "Push występuje, jeżeli MIN wygra dokładnie 1 punktem, z zastrzeżeniem właściwych zasad rozliczenia booka."
current_price: -105
book_or_source: "SIM_PREGAME_COM"
quote_timestamp_utc: "2026-09-08T18:00:00Z"
executable_status: "displayed_unverified"
market_evidence_grade: "PREVIEW_ONLY"
quote_temporal_status: "FUTURE_DATED_RELATIVE_TO_RESEARCH_CUTOFF"
total: 45.5
model_version: "MISSING"
model_run_id: "MISSING"
model_generated_at_utc: "MISSING"
model_fair_margin_selected_team_raw: -6.7
model_fair_margin_selected_team_rounded_to_0_5: -6.5
model_fair_line_interpretation: "GB -6.7, przyjęte zgodnie z konwencją selected-team spread wynikającą z podanego edge; wymaga potwierdzenia w artefakcie modelu."
edge_vs_line_points_raw: 7.7
edge_vs_line_points_rounded_to_0_5: 7.5
model_tag: "GOW"
p_cover: "MISSING"
p_push: "MISSING"
p_loss: "MISSING"
margin_pmf_available: "UNKNOWN"
acceptable_quote_frontier_available: "UNKNOWN"
research_timestamp_utc: "2026-07-28T15:55:42Z"
research_cutoff_utc: "2026-07-28T15:55:42Z"
research_time_source: "Bieżący czas UTC. "
audit_phase:
requested_phase: "PREGAME_AUDIT"
effective_phase_now: "EARLY_PRESEASON_RESEARCH"
explanation: "Dostarczony quote jest datowany około 42 dni po bieżącym research cutoff. Nie może być traktowany jako istniejący, aktualnie dostępny quote wykonawczy."
source_policy:
framework_instruction: "Zastosowano załączony framework Variant B jako instrukcję nadrzędną. "
hierarchy: "Źródła oficjalne NFL, klubów, stadionu i NWS mają pierwszeństwo. Zewnętrzne projekcje analityczne służą wyłącznie jako kontekst."
internal_data_policy: "Dane modelowe i quote przekazane przez użytkownika są zachowane bez rekonstrukcji, lecz nie są automatycznie uznawane za zweryfikowane."
calculation_policy: "Nie obliczano EV, minimalnej ceny, no-chase, CLV ani prawdopodobieństw bez wymaganych artefaktów modelu."
movement_language_policy: "Nie użyto określeń sharp, steam, respected ani public move."
warnings:
- "CRITICAL_TEMPORAL_MISMATCH: quote_timestamp_utc 2026-09-08T18:00:00Z przypada po research_cutoff_utc 2026-07-28T15:55:42Z."
- "NON_MARKET_GRADE_EVIDENCE: SIM_PREGAME_COM jest nazwą wewnętrzną lub symulacyjną; nie dostarczono dowodu, że jest to wykonywalny sportsbook quote."
- "SOURCE_IDENTITY_UNKNOWN: nie potwierdzono, do jakiej dokładnie strony lub feedu odnosi się SIM_PREGAME_COM."
- "SIGN_CONVENTION_REQUIRES_CONFIRMATION: interpretacja model margin -6.7 jako GB -6.7 jest zgodna z podanym edge 7.7, ale brak schematu danych lub manifestu modelu."
- "WEEK_1_UNCERTAINTY: oficjalne raporty meczowe o urazach, inactives oraz prognoza pogody dla okna meczu nie są jeszcze dostępne."
- "NO_PICK_OR_BETTING_RECOMMENDATION: raport jest audytem danych i procesu, nie decyzją o zakładzie."

points:

point_number: 1
point_name: "argument_against"
purpose: "Zidentyfikować najsilniejszy argument przeciwko wiarygodności modelowego wskazania, bez wydawania rekomendacji."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Użytkownik dostarczył modelową fair line GB -6.7, rynek GB +1.0 i edge 7.7 punktu."
"Po przyjęciu konwencji selected-team spread podany edge jest spójny z różnicą między +1.0 a -6.7."
"Surowy edge względem spreadu nie jest równoznaczny z dodatnim EV, ponieważ brakuje p_cover, p_push, p_loss oraz margin PMF."
"Najsilniejszy kontrargument procesowy: wielkość edge 7.7 nie może zostać zweryfikowana pod kątem kalibracji, ryzyka push, ceny -105 ani aktualności składu."
"Jako kontekst zewnętrzny, projekcja Mike’a Claya dla ESPN pokazuje wynik GB 23.2–MIN 21.2 i 57% szans GB na zwycięstwo, czyli znacznie mniej agresywną przewagę niż modelowa fair line GB -6.7. Nie jest to linia bukmacherska ani neutral-field rating. "
"Oficjalny materiał Packers przewiduje rozpoczęcie sezonu przez Micaha Parsonsa na PUP, co oznaczałoby opuszczenie co najmniej czterech pierwszych spotkań. Jest to istotne ryzyko aktualności założeń modelu. "
"Minnesota nadal prowadzi rywalizację Kylera Murraya z J.J. McCarthym o rolę QB1; obaj dzielili pierwsze repy, a konkurs miał być kontynuowany w training camp. "
missing_data:
"model_version"
"model_run_id"
"commit_hash lub input_hash"
"model_generated_at_utc"
"frozen model-generation market snapshot"
"p_cover"
"p_push"
"p_loss"
"margin PMF"
"calibration/uncertainty report"
"feature-contribution report"
"home-field/neutral-site adjustment log"
"sportsbook settlement and overtime rules"
pending_not_due:
"Ostateczne rozstrzygnięcie pozycji QB1 w MIN."
"Oficjalny status Week 1 Parsonsa oraz innych zawodników."
not_assessable:
"Pełny push-aware EV."
"Czy tag GOW jest prawidłowy według zamrożonej polityki tagów."
"Czy modelowa przewaga wynika ze stabilnych cech, czy z nieaktualnego roster/QB baseline."
"Przedział niepewności dla fair line -6.7."
source_evidence:
source_name: "User-provided model and quote fields"
source_url: "INTERNAL_USER_INPUT_NO_URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Fair line, edge, selected team, spread, price i model tag."
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Raw edge nie zastępuje PMF i pełnego EV; wymagane zachowanie logiki push."
source_name: "ESPN Mike Clay 2026 NFL projections"
source_url: ""
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Game-specific projection GB 23.2–MIN 21.2 oraz 57% dla GB."
source_name: "Green Bay Packers official"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Aktualne oczekiwanie rozpoczęcia sezonu przez Micaha Parsonsa na PUP."
source_name: "Minnesota Vikings official"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Trwająca rywalizacja Murray–McCarthy i podział pierwszych repów."
deterministic_checks:
spread_sign_consistency: "PROVISIONAL_PASS"
calculation: "Przy konwencji selected-team spread: 1.0 - (-6.7) = 7.7."
exact_model_fair_line: -6.7
rounded_model_fair_line: -6.5
exact_edge: 7.7
rounded_edge: 7.5
full_ev: "NOT_ASSESSABLE"
manual_review_needed:
"Potwierdzić, czy model_margin -6.7 rzeczywiście oznacza GB -6.7."
"Sprawdzić, czy model uwzględnia oczekiwaną niedostępność Parsonsa."
"Sprawdzić, jak model obsługuje nieustalonego QB1 Minnesoty."
"Porównać z raportem kalibracji dla tak dużych edge w Week 1."
recommended_machine_fields:
"model_lineage_hash"
"model_fair_line_distribution"
"p_cover_at_GB_plus_1"
"p_push_at_GB_plus_1"
"p_loss_at_GB_plus_1"
"calibration_bucket_edge_7_to_8"
"roster_snapshot_id"
"qb_scenario_weights"
test_game_output:
strongest_argument_against: "Model pokazuje bardzo duże rozminięcie z linią, ale bez PMF, prawdopodobieństw, kalibracji i zamrożonego roster/QB baseline nie wiadomo, czy jest to rzeczywista przewaga, czy efekt zbyt pewnej lub nieaktualnej projekcji."
raw_edge_status: "CONFIRMED_AS_USER_INPUT"
value_status: "NOT_ASSESSABLE"
model_tag_validation: "NOT_ASSESSABLE"
reason_codes:
"RAW_EDGE_NOT_FULL_EV"
"PMF_MISSING"
"PROBABILITIES_MISSING"
"MODEL_LINEAGE_MISSING"
"WEEK1_ROSTER_UNCERTAINTY"
"EXTERNAL_PROJECTION_LESS_AGGRESSIVE"
point_number: 2
point_name: "market_move_notes"
purpose: "Opisać zmianę od openeru, quote’u z momentu generacji modelu oraz aktualnego quote’u wykonawczego."
automation_level: "SEMI"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dostarczono pojedynczy rekord: GB +1.0, -105, SIM_PREGAME_COM, timestamp 2026-09-08T18:00:00Z."
"Timestamp tego rekordu przypada po bieżącym research cutoff, dlatego nie może być obecnie potwierdzony ani wykorzystany jako aktualny quote."
"Nie dostarczono openeru ani quote’u z czasu wygenerowania modelu."
"Publiczna strona meczowa nfelo ma obecnie pola opening, current i model oznaczone jako N/A; jest to wyłącznie informacja o braku danych na tej stronie, nie dowód braku linii na całym rynku. "
missing_data:
"opener spread and price"
"opener timestamp and source"
"model-generation spread and price"
"model-generation quote_timestamp"
"current direct-book executable quote"
"append-only quote path"
"quote identifiers"
"named-book history"
pending_not_due:
"Weryfikacja rzeczywistego rynku w dniu 2026-09-08."
not_assessable:
"Kierunek i wielkość ruchu."
"Czy linia przekroczyła 0, 1, 2, 3 albo inny key number."
"Czy dostarczony spread jest lepszy lub gorszy niż quote model-generation."
"No-chase status."
"Źródło ruchu lub skład uczestników rynku."
source_evidence:
source_name: "User-provided simulated quote"
source_url: "INTERNAL_USER_INPUT_NO_URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Jedyny dostarczony spread, price, source i przyszły timestamp."
source_name: "nfelo game page"
source_url: ""
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Na tej konkretnej stronie opening/current/model są obecnie N/A."
deterministic_checks:
opener_to_model_generation: "NOT_ASSESSABLE"
model_generation_to_current: "NOT_ASSESSABLE"
opener_to_current: "NOT_ASSESSABLE"
future_timestamp_check: "FAIL_FOR_CURRENT_AUDIT"
sharp_public_classification: "PROHIBITED_WITHOUT_SOURCE"
manual_review_needed:
"Dostarczyć historyczny quote ledger z co najmniej trzema odrębnymi checkpointami."
"Potwierdzić book, market scope i czy spread oraz cena pochodzą z jednego atomic quote."
recommended_machine_fields:
"quote_event_id"
"quote_type: opener/model_generation/current"
"book_id"
"spread_selected_team"
"price"
"captured_at_utc"
"provider_received_at_utc"
"executable_status"
test_game_output:
opener: "MISSING"
model_generation_quote: "MISSING"
supplied_future_simulated_quote: "GB +1.0 at -105; TEMPORALLY_UNUSABLE_NOW"
current_executable_quote: "MISSING"
movement_description: "NOT_ASSESSABLE"
reason_codes:
"OPENER_MISSING"
"MODEL_GENERATION_QUOTE_MISSING"
"CURRENT_EXECUTABLE_QUOTE_MISSING"
"FUTURE_DATED_QUOTE"
"NO_MARKET_PATH"
"NO_SHARP_PUBLIC_LABEL"
point_number: 3
point_name: "injury_role_notes"
purpose: "Zidentyfikować urazy, statusy i zmiany ról mogące wpływać na modelowy edge."
automation_level: "SEMI"
due_status: "NOT_DUE"
criticality: "HARD_WHEN_DUE"
confirmed_facts:
"Oficjalne strony injury report Packers i Vikings nie zawierają jeszcze raportu Week 1 dla tego meczu. "
"Nie wolno na tej podstawie uznać żadnej z drużyn za zdrową."
"Aktualny oficjalny kontekst Packers zakłada rozpoczęcie sezonu przez Micaha Parsonsa na PUP; jeżeli ten plan się utrzyma, nie zagra w Week 1. "
"Status pozostałych rehabilitujących się zawodników, w tym ich gotowość do pełnego snap share, nie jest jeszcze ustalony przez oficjalny raport meczowy."
"Rola QB1 Minnesoty pozostaje nieustalona; Murray i McCarthy byli objęci konkursem o pozycję. "
missing_data:
"Week 1 practice participation for GB"
"Week 1 practice participation for MIN"
"official game designations"
"official inactives"
"starter/backup confirmation"
"expected snap shares"
"replacement quality"
"unit-level chain reaction assessment"
pending_not_due:
"Pierwszy oficjalny Week 1 injury report."
"Końcowe game designations."
"Oficjalne inactives przed kickoffem."
"Potwierdzenie QB1 Minnesoty."
not_assessable:
"Pełny injury adjustment w punktach."
"Replacement-level impact."
"Czy model uwzględnił aktualne ograniczenia snapów."
source_evidence:
source_name: "Packers official injury report"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Brak opublikowanego raportu Week 1 na obecnym etapie."
source_name: "Vikings official injury report"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Brak opublikowanego raportu Week 1 na obecnym etapie."
source_name: "Packers official Parsons update"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Oczekiwany regular-season PUP i co najmniej cztery opuszczone mecze."
source_name: "Vikings official QB competition updates"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Brak zamkniętej decyzji QB1 i współdzielenie pierwszych repów."
deterministic_checks:
official_week1_report_due: false
infer_healthy_from_blank_report: "PROHIBITED"
current_preliminary_high_impact_flag: "GB_EDGE_MICAH_PARSONS_EXPECTED_PUP"
final_availability_status: "PENDING_NOT_DUE"
manual_review_needed:
"Odświeżyć po pierwszym środowym raporcie Week 1."
"Ponownie sprawdzić po final designation."
"Wykonać ostatni refresh po publikacji inactives."
recommended_machine_fields:
"player_id"
"team"
"position"
"practice_status_by_day"
"game_status"
"inactive_status"
"expected_snap_share"
"replacement_player_id"
"unit_impact_points"
test_game_output:
injury_report_status: "PENDING_NOT_DUE"
GB_micah_parsons: "CURRENT_EXPECTATION_PUP_WEEK1; FINAL_CONFIRMATION_PENDING"
MIN_starting_qb: "UNKNOWN"
team_health_conclusion: "PROHIBITED"
reason_codes:
"OFFICIAL_INJURY_REPORT_NOT_DUE"
"INACTIVES_NOT_DUE"
"HIGH_IMPACT_PLAYER_EXPECTED_PUP"
"MIN_QB_ROLE_UNRESOLVED"
point_number: 4
point_name: "schedule_spot_notes"
purpose: "Ocenić rest, podróż, strefę czasową, neutral-site, international status i kontekst aklimatyzacji."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Mecz jest zaplanowany na 13 września 2026 o 3:25 PM CDT w U.S. Bank Stadium. "
"Jest to domowy mecz MIN i wyjazdowy mecz GB."
"Mecz jest krajowy, nie neutral-site i nie international."
"Jest to otwarcie sezonu regularnego dla obu drużyn, więc nie występuje klasyczna różnica odpoczynku liczona od poprzedniego meczu regular-season."
"Green Bay rozpoczyna sezon dwoma kolejnymi meczami wyjazdowymi: Week 1 w Minnesota i Week 2 przy Jets. "
"Nie ma oficjalnych danych o dniu podróży, hotelu, planie praktyk ani aklimatyzacji Packers."
missing_data:
"official GB travel itinerary"
"arrival date and time"
"hotel/acclimation plan"
"Week 1 practice logistics"
"preseason workload and starter usage"
"audited geodesic travel calculation"
pending_not_due:
"Oficjalne informacje klubowe o podróży i logistyce game week."
not_assessable:
"Travel advantage."
"Acclimation advantage."
"Wpływ dwóch pierwszych wyjazdów GB bez danych o planowaniu podróży."
source_evidence:
source_name: "Minnesota Vikings official schedule"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Week 1, data, kickoff, przeciwnik i stadion."
source_name: "Green Bay Packers official schedule"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Wyjazdowy status GB oraz kolejność pierwszych spotkań."
source_name: "U.S. Bank Stadium event page"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Minnesota jako gospodarz, data i godzina."
deterministic_checks:
local_timezone: "America/Chicago"
kickoff_utc_conversion: "2026-09-13T20:25:00Z"
neutral_site: false
international_game: false
regular_season_rest_differential: "NONE_APPLICABLE_SEASON_OPENER"
travel_advantage: "UNKNOWN"
manual_review_needed:
"Monitorować oficjalne wypowiedzi o podróży Packers w tygodniu meczowym."
"Nie nadawać przewagi gospodarzom lub gościom wyłącznie na podstawie odległości."
recommended_machine_fields:
"schedule_snapshot_id"
"team_departure_timestamp"
"team_arrival_timestamp"
"origin_timezone"
"venue_timezone"
"travel_distance_km"
"rest_days"
"road_game_sequence"
test_game_output:
schedule_spot: "WEEK1_DIVISIONAL_ROAD_GAME_FOR_GB"
rest_edge: "NONE_CONFIRMED"
travel_edge: "UNKNOWN"
acclimation_edge: "UNKNOWN"
reason_codes:
"OFFICIAL_SCHEDULE_CONFIRMED"
"SEASON_OPENER"
"NO_ITINERARY_EVIDENCE"
"NO_TRAVEL_ADVANTAGE_CLAIM"
point_number: 5
point_name: "weather_notes"
purpose: "Ocenić pogodę w oknie meczu oraz ryzyko operacyjne stadionu i nawierzchni."
automation_level: "SEMI"
due_status: "NOT_DUE"
criticality: "HARD_WHEN_DUE"
confirmed_facts:
"U.S. Bank Stadium ma stały dach i środowisko kontrolowane klimatycznie. "
"NWS udostępnia szczegółową prognozę godzinową do siedmiu dni naprzód. "
"Aktualna oficjalna prognoza dla Minneapolis jest ważna tylko do 3 sierpnia 2026 i nie obejmuje meczu 13 września. "
"Nie należy zastępować brakującej prognozy meczowej bieżącą pogodą ani historyczną średnią klimatyczną."
missing_data:
"official game-window temperature"
"wind and gusts"
"precipitation probability"
"humidity"
"severe-weather alerts"
"official venue operations notice"
"field operations status"
pending_not_due:
"NWS forecast obejmujący 2026-09-13T20:25Z."
"Stadium/NFL game-day operating notices."
not_assessable:
"Wpływ pogody na dojazd i logistykę."
"Ryzyko opóźnienia otwarcia bram lub transportu."
"Jakiekolwiek punktowe weather adjustment."
source_evidence:
source_name: "U.S. Bank Stadium A-Z Guide"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Stały dach i climate-controlled environment."
source_name: "National Weather Service forecast-horizon guidance"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Prognoza godzinowa dostępna do siedmiu dni."
source_name: "NWS Minneapolis point forecast"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Obecna prognoza nie obejmuje okna meczu."
deterministic_checks:
roof_type: "FIXED"
climate_controlled: true
official_forecast_covers_game_window: false
game_weather_status: "PENDING_NOT_DUE"
open_air_weather_adjustment: "NOT_APPLICABLE_WITHOUT_OPERATIONAL_EXCEPTION"
manual_review_needed:
"Odświeżyć prognozę NWS około siedem dni przed meczem."
"Wykonać ponowny check 24 godzin i 3–6 godzin przed kickoffem."
"Monitorować komunikaty stadionu o dostępie, burzach i transporcie."
recommended_machine_fields:
"weather_forecast_run_timestamp"
"forecast_valid_time"
"temperature_f"
"wind_mph"
"gust_mph"
"precip_probability"
"roof_status"
"venue_operations_status"
test_game_output:
weather_status: "PENDING_NOT_DUE"
direct_on_field_weather_risk: "LIMITED_BY_FIXED_ROOF_BUT_NOT_FINALIZED"
external_operations_risk: "UNKNOWN"
reason_codes:
"OFFICIAL_FORECAST_WINDOW_NOT_OPEN"
"FIXED_ROOF"
"NO_CURRENT_GAME_WINDOW_FORECAST"
point_number: 6
point_name: "key_number_check"
purpose: "Sprawdzić położenie spreadu względem liczb kluczowych i zachować logikę push."
automation_level: "FULL"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dokładny spread selected team to GB +1.0; wyświetlenie zaokrąglone do 0.5 pozostaje GB +1.0."
"Jest to spread całkowity, więc push jest możliwy."
"Dla GB +1.0 push następuje przy zwycięstwie MIN dokładnie jednym punktem, pod warunkiem standardowego rozliczenia full-game spread."
"Według polityki frameworka 3 i 7 są podstawowymi key numbers; +1.0 nie znajduje się na 3 ani 7. "
missing_data:
"quote event ledger"
"line path"
"model margin PMF"
"versioned key-number configuration"
"book-specific overtime and settlement rules"
pending_not_due: []
not_assessable:
"Czy rynek przeszedł przez pick’em, 1, 2, 3 albo inny próg."
"Prawdopodobieństwo push przy +1.0."
"Koszt punktowy przejścia z +1.0 do +0.5 lub pick’em."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Każdy integer może pushować; 3 i 7 są podstawowymi key numbers."
source_name: "User-provided quote"
source_url: "INTERNAL_USER_INPUT_NO_URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "GB +1.0."
deterministic_checks:
exact_spread: 1.0
rounded_spread: 1.0
integer_spread: true
push_possible: true
push_score_margin_selected_team: -1
on_primary_key_3_or_7: false
crossed_key_number: "NOT_ASSESSABLE"
manual_review_needed:
"Potwierdzić house rules i uwzględnianie overtime."
"Po dostarczeniu quote path uruchomić key-crossing engine."
recommended_machine_fields:
"spread_exact"
"spread_rounded"
"integer_flag"
"push_margin"
"key_number_set_version"
"crossed_numbers"
"margin_pmf_mass_at_minus_1"
test_game_output:
key_number_status: "INTEGER_PLUS_1_WITH_PUSH"
primary_key_status: "NOT_ON_3_OR_7"
movement_key_check: "NOT_ASSESSABLE"
reason_codes:
"INTEGER_SPREAD_PUSH_LOGIC"
"PMF_MISSING"
"QUOTE_PATH_MISSING"
point_number: 7
point_name: "no_chase_limit"
purpose: "Ustalić, czy aktualny quote mieści się w zamrożonych limitach no-chase."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Nie dostarczono immutable model-generation quote."
"Nie dostarczono acceptable quote frontier."
"Nie dostarczono wersji polityki no-chase."
"Dostarczony przyszły quote nie może zastąpić historycznego model-generation snapshotu."
missing_data:
"model_generation_quote_id"
"model_generation_spread"
"model_generation_price"
"no_chase_policy_version"
"acceptable_quote_frontier"
"p_cover/p_push/p_loss by candidate line"
"eligible-books policy"
"current executable direct-book quote"
pending_not_due:
"Rzeczywisty quote wykonawczy bliżej 8 września."
not_assessable:
"ALLOWED/REVIEW/BLOCKED."
"Maksymalny akceptowalny spread."
"Maksymalna akceptowalna cena."
"Czy doszło do chase względem model-generation line."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Brak model-generation quote lub frontieru nie może być rekonstruowany po fakcie."
deterministic_checks:
no_chase_inputs_complete: false
no_chase_status: "NOT_ASSESSABLE"
manual_reconstruction_allowed: false
manual_review_needed:
"Wyeksportować oryginalny model-generation snapshot z append-only ledger."
"Dostarczyć zamrożoną wersję no-chase policy."
recommended_machine_fields:
"policy_version"
"frontier_id"
"model_generation_quote_id"
"current_quote_id"
"line_status"
"price_status"
"combined_no_chase_status"
test_game_output:
no_chase_status: "NOT_ASSESSABLE"
gate_effect: "HARD_BLOCK"
reason_codes:
"MODEL_GENERATION_QUOTE_MISSING"
"ACCEPTABLE_FRONTIER_MISSING"
"NO_CHASE_POLICY_MISSING"
"FUTURE_QUOTE_NOT_A_REPLACEMENT"
point_number: 8
point_name: "price_quality"
purpose: "Ocenić, czy dostępna cena jest wykonywalna i wystarczająca dla dodatniej wartości oczekiwanej."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Podana cena to -105, ale pochodzi z niezweryfikowanego, przyszłego snapshotu SIM_PREGAME_COM."
"Cena nie została potwierdzona na direct-book betslipie przy docelowej stawce."
"Brakuje push-aware p_cover, p_push i p_loss."
missing_data:
"p_cover"
"p_push"
"p_loss"
"margin PMF"
"acceptable price frontier"
"target stake"
"direct betslip confirmation"
"book house rules"
"quote id"
pending_not_due:
"Sprawdzenie ceny na rzeczywistym rynku w odpowiednim momencie."
not_assessable:
"EV."
"Minimalna wymagana cena."
"Price edge."
"Maksymalna stawka."
"Czy -105 jest wystarczające."
source_evidence:
source_name: "User-provided quote"
source_url: "INTERNAL_USER_INPUT_NO_URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Cena -105 i source label."
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Price quality wymaga PMF, prawdopodobieństw, frontieru i wykonywalnego quote’u."
deterministic_checks:
quoted_price: -105
executable_confirmation: false
probability_inputs_complete: false
price_quality: "NOT_ASSESSABLE"
ev_calculation_performed: false
manual_review_needed:
"Potwierdzić direct-book price i stake limit."
"Uruchomić push-aware EV engine dopiero po dostarczeniu PMF."
recommended_machine_fields:
"price"
"p_cover"
"p_push"
"p_loss"
"ev_per_unit"
"minimum_acceptable_price"
"target_stake"
"max_accepted_stake"
"betslip_capture_id"
test_game_output:
price_quality_status: "NOT_ASSESSABLE"
quoted_price_status: "USER_PROVIDED_UNVERIFIED"
gate_effect: "HARD_BLOCK"
reason_codes:
"PROBABILITIES_MISSING"
"PMF_MISSING"
"DIRECT_BOOK_CONFIRMATION_MISSING"
"TARGET_STAKE_MISSING"
"FUTURE_DATED_PRICE"
point_number: 9
point_name: "market_snapshot"
purpose: "Utrwalić dokładny quote decyzyjny lub wykonawczy: event, side, line, price, source i timestamp."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dostarczona para spread/price jest atomowa w danych wejściowych: GB +1.0 i -105."
"Source label to SIM_PREGAME_COM, a dokładna tożsamość feedu pozostaje UNKNOWN."
"Timestamp 2026-09-08T18:00:00Z jest przyszły względem obecnego audytu."
"Nie ma betslipu, quote ID, potwierdzenia stawki ani dowodu wykonywalności."
"Jeżeli człon PREGAME_COM odnosi się do Pregame.com, sama strona podaje, że nie przyjmuje ani nie zawiera zakładów; nie byłoby to więc źródło direct-book grade. Dokładne mapowanie SIM_PREGAME_COM pozostaje jednak niepotwierdzone. "
missing_data:
"exact source/provider identity"
"sportsbook name"
"quote id"
"direct betslip"
"target stake"
"accepted maximum stake"
"jurisdiction/account context"
"proof that spread and price were executable"
"capture artifact"
pending_not_due:
"Możliwość weryfikacji snapshotu 8 września 2026."
not_assessable:
"Provider-grade lub direct-book-grade status."
"Rzeczywista wykonywalność -105."
"Dostępność ceny dla użytkownika."
source_evidence:
source_name: "User-provided SIM_PREGAME_COM snapshot"
source_url: "INTERNAL_USER_INPUT_NO_URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Event, selected side, spread, price, source label i przyszły timestamp."
source_name: "Pregame.com official site"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Pregame.com informuje, że nie przyjmuje ani nie zawiera zakładów; zastosowanie tylko warunkowe, jeżeli source label odnosi się do tej strony."
deterministic_checks:
event_identity_complete: true
market_scope_complete: true
selected_side_complete: true
atomic_spread_price_present: true
timestamp_present: true
timestamp_not_after_research_cutoff: false
quote_id_present: false
target_stake_check_present: false
executable_status: "displayed_unverified"
evidence_grade: "PREVIEW_ONLY"
manual_review_needed:
"Podać dokumentację SIM_PREGAME_COM."
"Dostarczyć screenshot lub API record zawierający book, quote ID, timestamp i market scope."
"Dla direct-book grade sprawdzić betslip przy docelowej stawce."
recommended_machine_fields:
"decision_snapshot_id"
"book_id"
"provider_id"
"event_id"
"market_scope"
"selected_team"
"spread"
"price"
"quote_timestamp_utc"
"executable_status"
"target_stake"
"capture_hash"
test_game_output:
decision_snapshot_grade: "PREVIEW_ONLY"
current_audit_validity: "INVALID_AS_CURRENT_QUOTE_BECAUSE_FUTURE_DATED"
quote_tuple: "GB +1.0 / -105 / SIM_PREGAME_COM / 2026-09-08T18:00:00Z"
gate_effect: "HARD_BLOCK"
reason_codes:
"FUTURE_DATED_QUOTE"
"SOURCE_IDENTITY_UNKNOWN"
"DISPLAYED_UNVERIFIED"
"NO_QUOTE_ID"
"NO_TARGET_STAKE_CHECK"
"NON_MARKET_GRADE_EVIDENCE"
point_number: 10
point_name: "public_bias"
purpose: "Zebrać market-specific tickets i handle jako kontekst, bez utożsamiania ich z sharp money."
automation_level: "SEMI"
due_status: "NOT_DUE"
criticality: "CONTEXT_ONLY"
confirmed_facts:
"Nie dostarczono żadnego market-specific tickets% ani handle%."
"Nie ma provider name, denominator, sample window ani timestamp."
"Na obecnym, wczesnym etapie preseason brak danych nie jest błędem procesu."
missing_data:
"tickets percentage"
"handle percentage"
"provider"
"book-specific denominator"
"market scope"
"capture timestamp"
"sample methodology"
pending_not_due:
"Market-specific betting splits bliżej meczu."
not_assessable:
"Public concentration."
"Rozbieżność tickets vs handle."
"Jakikolwiek związek splits z ruchem linii."
"Sharp/public attribution."
source_evidence:
source_name: "No qualifying split source supplied"
source_url: "MISSING"
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Brak materiału do oceny."
deterministic_checks:
provider_count: 0
averaging_across_providers: "NOT_PERFORMED"
public_bias_status: "PENDING_NOT_DUE"
sharp_money_inference: "PROHIBITED"
manual_review_needed:
"Zebrać osobno DK, Circa lub inne źródło wraz z denominatorem."
"Nie mieszać danych z różnych operatorów w jedną średnią."
recommended_machine_fields:
"split_provider"
"book"
"market"
"tickets_pct"
"handle_pct"
"sample_size"
"window_start"
"window_end"
"captured_at_utc"
test_game_output:
tickets_pct: "PENDING_NOT_DUE"
handle_pct: "PENDING_NOT_DUE"
public_bias_conclusion: "NOT_ASSESSABLE"
reason_codes:
"SPLITS_NOT_DUE"
"NO_PROVIDER"
"NO_DENOMINATOR"
"NO_SHARP_PUBLIC_INFERENCE"
point_number: 11
point_name: "power_rankings_check"
purpose: "Porównać wewnętrzną ocenę siły drużyn z zewnętrznymi benchmarkami."
automation_level: "SEMI"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Wewnętrzna wartość z danych wejściowych odpowiada fair line GB -6.7."
"Mike Clay/ESPN projektuje dla tego meczu GB 23.2, MIN 21.2 i 57% win probability dla GB. Jest to game projection, nie neutral-field power rating. "
"W tej samej publikacji sezonowa projekcja wynosi około 9.5 zwycięstwa dla GB i 7.6 dla MIN. "
"ESPN unit grades w tej publikacji oceniają GB na 5.7, rank 13, a MIN na 5.3, rank 21. Nie należy przeliczać tych ordinal ranks bezpośrednio na punkty spreadu. "
"nfelo nie ma jeszcze wypełnionych wartości opening/current/model ani danych QB dla tego meczu. "
"Dostępny benchmark ESPN wspiera kierunkowo GB jako silniejszy zespół, ale nie potwierdza wielkości fair line -6.7."
missing_data:
"internal neutral-field PowerScore"
"internal_neutral_power_gap"
"verified current ESPN FPI point ratings"
"PFF point spread team ratings"
"FTN DVOA/DAVE"
"market-implied neutral ratings"
"versioned external snapshot timestamps"
pending_not_due:
"Aktualizacje zewnętrznych modeli po preseason i rozstrzygnięciu QB1."
not_assessable:
"Dokładny zewnętrzny consensus fair line."
"Neutral-field point gap."
"Czy rozbieżność wynika z home-field, QB lub roster inputs."
source_evidence:
source_name: "ESPN Mike Clay 2026 projections"
source_url: ""
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Game projection, projected wins i unit grades."
source_name: "nfelo game page"
source_url: ""
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Brak aktualnie opublikowanych game-line i QB model inputs."
deterministic_checks:
external_directional_support_for_GB: true
external_confirmation_of_GB_minus_6_7: false
ordinal_rank_to_spread_conversion: "NOT_PERFORMED"
sanity_check_status: "PARTIAL"
manual_review_needed:
"Dodać co najmniej dwa zweryfikowane point-based neutral-field ratings."
"Zapisać datę każdej zewnętrznej projekcji i jej założenia QB."
recommended_machine_fields:
"internal_neutral_power_gap"
"external_model_name"
"external_model_version"
"external_neutral_power_GB"
"external_neutral_power_MIN"
"external_game_projection"
"captured_at_utc"
test_game_output:
external_benchmark_status: "PARTIAL"
directional_result: "GB_RATED_STRONGER"
magnitude_validation: "NOT_CONFIRMED"
key_observation: "Dostępna projekcja game-specific jest wyraźnie mniej agresywna niż internal fair line."
reason_codes:
"EXTERNAL_DIRECTIONAL_SUPPORT_ONLY"
"NO_NEUTRAL_POINT_RATING"
"NFelo_NOT_POPULATED"
"INTERNAL_POWER_GAP_MISSING"
point_number: 12
point_name: "roster_change_check"
purpose: "Sprawdzić, czy zmiany składu, sztabu i ról nie dezaktualizują baseline’u modelu."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Green Bay dokonało wielu istotnych zmian: Rashan Gary został wytransferowany, Elgton Jenkins zwolniony, Zaire Franklin pozyskany, a Javon Hargrave, Skyy Moore i Benjamin St-Juste podpisani; Dontayvion Wicks został później wytransferowany. "
"Packers zatrudnili Jonathana Gannona jako nowego defensive coordinatora w miejsce Jeffa Hafleya. "
"Minnesota podpisała Kylera Murraya, który konkuruje z J.J. McCarthym o QB1. "
"Vikings dodali w drafcie m.in. DL Caleba Banksa, LB Jake’a Goldaya oraz kolejnych zawodników, ale rzeczywiste role Week 1 pozostają do ustalenia. "
"Zewnętrzne źródła potwierdzają więc wiele zmian, lecz bez zamrożonego roster baseline modelu nie można określić, które z nich były już uwzględnione."
missing_data:
"internal frozen roster baseline"
"role baseline"
"staff baseline"
"baseline cutoff timestamp"
"baseline hash"
"projected starters used by model"
"snap-share assumptions"
"QB scenario assumptions"
pending_not_due:
"Finalne 53-man rosters."
"Week 1 depth charts i role."
"Rozstrzygnięcie QB1 MIN."
not_assessable:
"Czy model baseline jest aktualny."
"Ile punktów każda zmiana powinna przesunąć fair line."
"Czy roster turnover jest już zawarty w edge 7.7."
source_evidence:
source_name: "Packers official transactions"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Potwierdzone transfery, zwolnienia i podpisania GB."
source_name: "Packers official coaching announcement"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Jonathan Gannon jako nowy defensive coordinator."
source_name: "Vikings official Kyler Murray signing and QB updates"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Pozyskanie Murraya i trwająca rywalizacja o QB1."
source_name: "Vikings official transactions"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Potwierdzone offseason additions."
deterministic_checks:
external_roster_changes_detected: true
internal_baseline_present: false
baseline_staleness_check: "NOT_ASSESSABLE"
automatic_point_adjustment: "NOT_PERFORMED"
manual_review_needed:
"Porównać obecny roster z dokładnym snapshotem użytym podczas model run."
"Zweryfikować staff scheme assumptions i QB weighting."
"Nie przypisywać arbitralnych punktów zmianom bez modelu roli/snapów."
recommended_machine_fields:
"baseline_snapshot_id"
"baseline_cutoff_utc"
"current_roster_snapshot_id"
"player_added_removed"
"role_change"
"staff_change"
"expected_snap_delta"
"model_feature_affected"
test_game_output:
roster_change_status: "NOT_ASSESSABLE_WITHOUT_INTERNAL_BASELINE"
confirmed_change_volume: "MULTIPLE_CONFIRMED_CHANGES"
stale_model_risk: "UNRESOLVED"
reason_codes:
"INTERNAL_ROSTER_BASELINE_MISSING"
"MULTIPLE_OFFSEASON_CHANGES"
"NEW_GB_DEFENSIVE_COORDINATOR"
"MIN_QB_COMPETITION"
"FINAL_ROSTER_NOT_DUE"
point_number: 13
point_name: "matchup_specific_risk"
purpose: "Przetestować źródła modelowego edge pod kątem konkretnych konfliktów matchupowych."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Nie dostarczono wewnętrznych edge drivers ani feature-contribution report, więc analiza nie może prawidłowo rozpocząć się od tego, co model uznał za przewagę."
"Potencjalna niedostępność Parsonsa, nieustalony QB1 Minnesoty i nowy system defensywny Packers są istotnymi zależnościami wejściowymi, lecz nie stanowią jeszcze udowodnionego matchup edge. "
"nfelo nie ma jeszcze wypełnionych statystyk matchupowych ani QB dla tego meczu. "
missing_data:
"internal matchup dependency report"
"feature contributions"
"sensitivity analysis"
"expected starters"
"current offensive-line combinations"
"pass-rush/protection splits"
"coverage/receiver splits"
"run efficiency splits"
"current QB scenario"
pending_not_due:
"Final roles, starters i Week 1 injury information."
"Preseason evidence on new schemes."
not_assessable:
"Pass-rush vs protection edge."
"Coverage vs receiving edge."
"Run-game conflict."
"Który konkretny matchup wyjaśnia 7.7 punktu edge."
source_evidence:
source_name: "Packers official personnel/coaching context"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Parsons recovery/PUP expectation i nowy defensive coordinator."
source_name: "Vikings official QB context"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Nieustalony QB1."
source_name: "nfelo game page"
source_url: ""
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Brak obecnie matchup i QB data na tej stronie."
deterministic_checks:
internal_edge_drivers_available: false
matchup_test_started_from_model_drivers: false
matchup_conclusion: "NOT_ASSESSABLE"
narrative_fabrication_allowed: false
manual_review_needed:
"Dostarczyć trzy do pięciu głównych feature contributions modelu."
"Dla każdego drivera sprawdzić zależność od QB, urazu, składu i scheme."
recommended_machine_fields:
"edge_driver_name"
"feature_value_GB"
"feature_value_MIN"
"contribution_points"
"dependency_player_ids"
"sensitivity_low"
"sensitivity_high"
"evidence_snapshot_id"
test_game_output:
matchup_specific_risk_status: "NOT_ASSESSABLE"
contextual_risk_flags:
"GB_PRIMARY_EDGE_RUSHER_EXPECTED_PUP"
"MIN_QB1_UNKNOWN"
"GB_NEW_DEFENSIVE_SYSTEM"
matchup_edge_claim: "NONE"
reason_codes:
"EDGE_DRIVERS_MISSING"
"STARTERS_NOT_FINAL"
"MATCHUP_DATA_NOT_POPULATED"
"NO_RANDOM_NARRATIVE"
point_number: 14
point_name: "game_script_risk"
purpose: "Przetestować modelowy edge w realistycznych scenariuszach przebiegu meczu."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Nie dostarczono possession simulatora ani margin PMF."
"Nie ma p_cover, p_push ani p_loss dla GB +1.0."
"Nie ma zamrożonej polityki scenariuszy ani wag wariantów QB Minnesoty."
"Total 45.5 został podany przez użytkownika, ale nie jest zweryfikowany jako market-grade input."
missing_data:
"play-by-play/possession simulator"
"margin PMF"
"score-state transition matrix"
"pace and pass-rate assumptions"
"turnover distribution"
"QB scenario weights"
"injury and weather inputs"
"frozen scenario policy"
pending_not_due:
"Final QB, injury, weather i roster inputs."
not_assessable:
"Kruchość edge przy prowadzeniu MIN."
"Kruchość edge w low-possession game."
"Turnover dependency."
"Backdoor-cover profile."
"Push probability przy GB +1.0."
source_evidence:
source_name: "User-provided model/market fields"
source_url: "INTERNAL_USER_INPUT_NO_URL"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Spread, fair line i total 45.5."
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Bez simulatora lub PMF game-script risk należy oznaczyć NOT_ASSESSABLE."
deterministic_checks:
simulator_available: false
margin_pmf_available: "UNKNOWN"
scenario_policy_available: false
game_script_risk: "NOT_ASSESSABLE"
manual_review_needed:
"Uruchomić scenariusze dopiero po zamrożeniu QB1, rosteru i kluczowych statusów."
"Oddzielić scenariusze bazowe od zdarzeń rzadkich, np. turnover spikes."
recommended_machine_fields:
"scenario_id"
"scenario_probability"
"possessions_GB"
"possessions_MIN"
"pace"
"early_lead_team"
"turnover_margin"
"cover_probability"
"push_probability"
test_game_output:
game_script_risk_status: "NOT_ASSESSABLE"
scenario_simulation_performed: false
gate_effect: "INCOMPLETE_QUANTITATIVE_AUDIT"
reason_codes:
"SIMULATOR_MISSING"
"PMF_MISSING"
"SCENARIO_POLICY_MISSING"
"CURRENT_INPUTS_NOT_FINAL"
point_number: 15
point_name: "closing_line"
purpose: "Zapisać finalny pregame closing spread."
automation_level: "HYBRID"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts:
"Mecz jest zaplanowany na 13 września 2026 o 20:25 UTC. "
"Rynek nie został jeszcze zamknięty."
"Zaplanowany kickoff nie może być automatycznie uznany za dokładny timestamp zamknięcia rynku."
missing_data:
"close_snapshot_id"
"closing spread"
"book/provider"
"actual market close timestamp"
"full closing ladder"
pending_not_due:
"Finalny quote bezpośrednio przed rzeczywistym zamknięciem rynku."
not_assessable:
"Closing line."
source_evidence:
source_name: "Official team schedules"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Mecz i kickoff są w przyszłości."
deterministic_checks:
market_closed: false
closing_line: "POST_EVENT_ONLY"
scheduled_kickoff_used_as_close_timestamp: false
manual_review_needed:
"Utrwalić ostatni rzeczywiście dostępny pregame quote z tego samego booka/provider source."
recommended_machine_fields:
"close_snapshot_id"
"closing_spread"
"market_close_timestamp"
"book_id"
"provider_id"
test_game_output:
closing_line: "POST_EVENT_ONLY"
reason_codes:
"MARKET_NOT_CLOSED"
"CLOSE_NOT_DUE"
point_number: 16
point_name: "closing_price"
purpose: "Zapisać closing price powiązany z tym samym snapshotem co closing line."
automation_level: "HYBRID"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts:
"Nie istnieje jeszcze close snapshot dla tego meczu."
"Closing price musi pochodzić z tego samego close_snapshot_id co closing line."
missing_data:
"close_snapshot_id"
"closing price"
"closing spread"
"closing ladder"
"both-side prices"
pending_not_due:
"Capture po zamknięciu pregame market."
not_assessable:
"Closing price."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Closing price nie może być oddzielony od closing line."
deterministic_checks:
close_snapshot_present: false
closing_price: "POST_EVENT_ONLY"
manual_review_needed:
"Capture line i price jako jeden atomowy rekord."
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
"LINE_PRICE_ATOMICITY_REQUIRED"
point_number: 17
point_name: "clv_points"
purpose: "Obliczyć CLV na podstawie prawidłowego decision snapshotu i close snapshotu."
automation_level: "INTERNAL_ONLY"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts:
"Brak prawidłowego bieżącego decision snapshotu: dostarczony quote jest przyszły i niezweryfikowany."
"Brak closing line i closing price."
"Spread CLV i price CLV nie mogą być łączone w jedną sztuczną liczbę."
missing_data:
"valid decision_snapshot_id"
"close_snapshot_id"
"closing spread"
"closing price"
"selected-team spread convention confirmation"
"full closing ladder"
pending_not_due:
"Market close."
not_assessable:
"Spread CLV."
"Price CLV."
"Key-number-adjusted CLV context."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "CLV nie może być liczone bez punktów 9, 15 i 16."
deterministic_checks:
decision_snapshot_valid: false
close_snapshot_present: false
clv_calculation_performed: false
clv_points: "POST_EVENT_ONLY"
manual_review_needed:
"Po close uruchomić rule engine osobno dla spread CLV i price CLV."
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
"VALID_DECISION_SNAPSHOT_MISSING"
"CLOSE_MISSING"
"NO_CLV_CALCULATION"
point_number: 18
point_name: "process_quality"
purpose: "Ocenić kompletność, terminowość, dowody i blokady punktów 1–17."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Tożsamość meczu, termin, stadion, gospodarz i roof type zostały potwierdzone źródłami oficjalnymi."
"Model lineage, PMF, p_cover/p_push/p_loss oraz zamrożone polityki nie zostały dostarczone."
"Quote decyzyjny jest przyszły, niezweryfikowany i bez market-grade execution evidence."
"Punkty injury, weather, public splits oraz close/CLV są odpowiednio NOT_DUE lub POST_EVENT_ONLY i nie powinny być liczone jako błędy."
"Nie jest zasadne tworzenie wyniku procentowego readiness, ponieważ istnieją due hard blockers."
missing_data:
"immutable audit bundle"
"model lineage manifest"
"calculation manifest"
"valid decision snapshot"
"no-chase policy"
"acceptable quote frontier"
"internal roster baseline"
"matchup dependency report"
"scenario simulator output"
"manual override log"
pending_not_due:
"Point 3 official injury report/inactives."
"Point 5 official weather window."
"Point 10 public splits."
"Points 15–17 close and CLV."
not_assessable:
"Final quantitative process score."
"Readiness for execution stage."
"Model value validation."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Not-due nie jest porażką; due hard blockers mają pierwszeństwo."
source_name: "Official schedule/venue evidence"
source_url: ""
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Identity, schedule i venue domain są gotowe."
deterministic_checks:
hard_blockers_present: true
not_due_counted_as_failure: false
numeric_readiness_score_generated: false
gate_effect: "HOLD"
manual_review_needed:
"Uzupełnić due hard blockers, a następnie ponownie uruchomić punkt 18."
"Nie usuwać statusów NOT_DUE tylko po to, aby zwiększyć pozorną kompletność."
recommended_machine_fields:
"audit_bundle_id"
"point_status"
"due_status"
"criticality"
"gate_effect"
"effective_status"
"evidence_manifest_hash"
"calculation_manifest_hash"
test_game_output:
run_status: "HOLD"
domain_status:
game_identity: "READY"
schedule_and_venue: "READY"
model_lineage: "BLOCKED"
model_probability_outputs: "BLOCKED"
market_movement: "BLOCKED"
market_execution_snapshot: "BLOCKED"
key_number_logic: "PARTIAL"
injury_gameweek: "NOT_DUE"
weather_gamewindow: "NOT_DUE"
public_splits: "NOT_DUE"
external_power_context: "PARTIAL"
roster_baseline: "BLOCKED"
matchup_analysis: "BLOCKED"
game_script_simulation: "BLOCKED"
closing_data: "POST_EVENT_ONLY"
clv: "POST_EVENT_ONLY"
readiness_by_phase:
early_research: "PARTIAL_READY"
model_validation: "NOT_READY"
market_execution: "NOT_READY"
gameweek_refresh: "NOT_DUE"
post_event_review: "POST_EVENT_ONLY"
effective_status: "HOLD_PENDING_DATA"
reason_codes:
"DUE_HARD_BLOCKERS_PRESENT"
"NOT_DUE_ITEMS_EXCLUDED_FROM_FAILURE"
"NO_NUMERIC_SCORE_WHEN_BLOCKED"
"MODEL_AND_MARKET_DOMAINS_INCOMPLETE"
point_number: 19
point_name: "final_operator_decision"
purpose: "Wyznaczyć deterministyczny stan procesu bez decyzji PLAY/PASS."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Punkt 18 wykazuje due hard blockers w domenach model lineage, prawdopodobieństw, quote path, market snapshot, no-chase i price quality."
"Status HOLD nie jest oceną jakości strony GB ani rekomendacją zakładu."
missing_data:
"frozen operator decision policy version"
"action routing registry version"
"operator decision ledger id"
"manual override log"
pending_not_due:
"Injury, weather, public splits i post-event data."
not_assessable:
"Jakakolwiek decyzja bettingowa."
source_evidence:
source_name: "Variant B framework"
source_url: ""
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:55:42Z"
supports_claim: "Dozwolone wyjścia operatora i zakaz używania PLAY/PASS."
deterministic_checks:
gate_state: "HOLD"
operator_action: "HOLD_PENDING_DATA"
hold_type: "DATA_AND_TEMPORAL_VALIDITY_HOLD"
required_actions:
"Dostarczyć model_version, model_run_id, model_generated_at_utc oraz lineage/input hash."
"Dostarczyć p_cover, p_push, p_loss i margin PMF."
"Dostarczyć immutable model-generation quote."
"Dostarczyć acceptable quote frontier i versioned no-chase policy."
"Zastąpić przyszły SIM snapshot rzeczywistym market-grade atomic quote, kiedy stanie się dostępny."
"Dostarczyć wewnętrzny roster/staff/role baseline."
"Dostarczyć matchup dependency report i simulator/scenario output."
nonblocking_pending_items:
"Official Week 1 injury reports and inactives."
"NWS game-window forecast."
"Market-specific public splits."
"Closing line, closing price and CLV."
prohibited_transitions:
"READY_FOR_NEXT_AUDIT_STAGE"
"AUDIT_COMPLETE"
"Obliczenie no-chase status."
"Obliczenie price quality lub EV."
"Obliczenie CLV przed close."
"Wydanie decyzji PLAY/PASS."
decision_provenance:
framework: "Variant B attached instruction"
based_on_point_18_snapshot: "CURRENT_REPORT"
manual_override: "NONE"
manual_review_needed:
"Po uzupełnieniu hard blockers uruchomić punkt 18 i router punktu 19 ponownie."
recommended_machine_fields:
"gate_state"
"operator_action"
"hold_type"
"required_action_ids"
"policy_version"
"decision_timestamp_utc"
"decision_ledger_id"
test_game_output:
gate_state: "HOLD"
operator_action: "HOLD_PENDING_DATA"
hold_type: "DATA_AND_TEMPORAL_VALIDITY_HOLD"
betting_recommendation: "NONE"
final_pick: "NONE"
reason_codes:
"HOLD_PENDING_DATA"
"FUTURE_DATED_MARKET_SNAPSHOT"
"MODEL_LINEAGE_BLOCKER"
"PMF_PROBABILITY_BLOCKER"
"NO_CHASE_INPUT_BLOCKER"
"EXECUTION_EVIDENCE_BLOCKER"

summary:
hard_blockers:
- "Brak model_version, model_run_id, generation timestamp i lineage/input hash."
- "Brak p_cover, p_push, p_loss i margin PMF."
- "Brak model-generation quote oraz pełnego quote path."
- "Brak acceptable quote frontier i zamrożonej polityki no-chase."
- "Dostarczony quote jest przyszły względem research cutoff i nie ma market-grade execution evidence."
- "Brak direct-book betslip/quote ID/target-stake confirmation."
- "Brak wewnętrznego roster, role i staff baseline."
warnings:
- "Modelowy edge 7.7 jest surową różnicą spreadów, nie zweryfikowanym EV."
- "Aktualna oficjalna prognoza Packers zakłada regular-season PUP dla Micaha Parsonsa. "
- "MIN nie ustaliło jeszcze QB1 pomiędzy Murrayem i McCarthym. "
- "Zewnętrzna projekcja ESPN kierunkowo preferuje GB, ale wskazuje dużo mniejszą przewagę meczową niż internal fair line. "
pending_not_due:
- "Official Week 1 injury reports."
- "Final game designations and inactives."
- "NWS game-window weather."
- "Public tickets/handle."
- "Final rosters and roles."
- "Closing line, closing price and CLV."
internal_inputs_required_from_me:
- "Model lineage bundle."
- "PMF and push-aware probabilities."
- "Model-generation quote."
- "No-chase policy and acceptable frontier."
- "Internal roster/staff baseline."
- "Feature contributions and sensitivity report."
- "Game-script simulator output."
data_to_capture_manually:
- "Atomic direct-book quote with spread, price, timestamp, book and target stake."
- "Later official injury/inactives snapshots."
- "Later NWS forecast and venue notice."
- "Close snapshot tying line and price together."
next_best_action: "Najpierw skorygować konflikt czasowy quote’u i podłączyć zamrożony model bundle. Dopiero potem ponownie przeliczyć punkty 1, 2, 7, 8, 9, 12, 13, 14, 18 i 19."

final_summary:
audit_readiness_now: "EARLY_RESEARCH_PARTIAL; MODEL_VALIDATION_AND_MARKET_EXECUTION_BLOCKED"
due_hard_blockers:
- "MODEL_LINEAGE_MISSING"
- "PMF_AND_PROBABILITIES_MISSING"
- "MODEL_GENERATION_QUOTE_MISSING"
- "NO_CHASE_FRONTIER_AND_POLICY_MISSING"
- "VALID_CURRENT_MARKET_SNAPSHOT_MISSING"
- "FUTURE_DATED_SIMULATED_QUOTE"
- "INTERNAL_ROSTER_BASELINE_MISSING"
not_due_items:
- "Point 3: official injury reports, final designations and inactives"
- "Point 5: official weather forecast for game window"
- "Point 10: market-specific tickets and handle"
- "Final 53-man roster and confirmed MIN QB1"
post_event_only_items:
- "Point 15: closing_line"
- "Point 16: closing_price"
- "Point 17: clv_points"
data_i_must_enter_manually:
- "model_version"
- "model_run_id"
- "model_generated_at_utc"
- "commit/input hash"
- "p_cover, p_push, p_loss"
- "margin PMF"
- "model-generation quote ID, spread, price and timestamp"
- "acceptable quote frontier"
- "no-chase policy version"
- "direct-book decision snapshot and target-stake evidence"
- "internal roster/role/staff baseline"
- "matchup dependency and feature-contribution report"
- "scenario simulator output"
data_gpt_found_with_sources:
- "Mecz: 13 września 2026, 3:25 PM CDT / 20:25 UTC, U.S. Bank Stadium, Minneapolis; MIN gospodarzem. "
- "Stadion ma stały dach i kontrolowane klimatycznie wnętrze. "
- "Oficjalne raporty injury Week 1 nie są jeszcze opublikowane. "
- "Aktualna oficjalna prognoza zakłada rozpoczęcie sezonu przez Micaha Parsonsa na PUP. "
- "Minnesota nadal prowadzi konkurs Murray–McCarthy o QB1. "
- "Packers mają nowego defensive coordinatora i wiele istotnych zmian personalnych. "
- "ESPN/Mike Clay projektuje GB 23.2–MIN 21.2, ale jest to kontekst, nie market line. "
data_that_requires_internal_python:
- "Push-aware p_cover/p_push/p_loss i EV."
- "Acceptable quote frontier."
- "No-chase status."
- "Key-number PMF mass i line-value deltas."
- "Roster/QB scenario sensitivity."
- "Possession and game-script simulation."
- "Spread CLV i price CLV po zamknięciu rynku."
- "Finalny deterministic process gate po uzupełnieniu danych."
next_step_for_me: "Wyeksportować zamrożony model bundle oraz prawidłowy model-generation snapshot. Quote z 8 września pozostawić jako przyszły planowany checkpoint, a nie bieżący dowód rynku. Następnie wykonać nowy audit refresh, gdy dostępny będzie rzeczywisty market-grade quote."
safe_to_advance_to_next_audit_stage: false
