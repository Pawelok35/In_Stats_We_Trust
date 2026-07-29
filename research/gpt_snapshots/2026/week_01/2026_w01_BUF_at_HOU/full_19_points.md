# GPT Snapshot

season: 2026
week: 1
game_id: 2026_w01_BUF_at_HOU
snapshot_type: full_19_points
created_at_local: 2026-07-28T18:05:43.949569+02:00
source_thread: GPT

## GPT Output

audit_metadata:
game_identity:
season: 2026
week: 1
game_id: "2026_w01_BUF_at_HOU"
away_team: "BUF"
home_team: "HOU"
designated_home_team: "HOU"
game_date_local: "2026-09-13"
game_date_usa: "2026-09-13"
scheduled_kickoff_local: "2026-09-13T12:00:00-05:00"
scheduled_kickoff_timezone: "America/Chicago — CDT"
scheduled_kickoff_utc: "2026-09-13T17:00:00Z"
venue: "Reliant Stadium"
venue_alias: "NRG Stadium — poprzednia nazwa tego samego obiektu"
venue_city_country: "Houston, Texas, USA"
neutral_site: false
international_game: false
market: "full-game spread"
selected_team: "BUF"
supplied_current_spread_selected_team_raw: -1.5
supplied_current_spread_selected_team_rounded_to_0_5: -1.5
supplied_current_price: -102
supplied_book_or_source: "SIM_PREGAME_COM"
supplied_quote_timestamp_utc: "2026-09-08T18:00:00Z"
classified_executable_status: "displayed_unverified"
classified_evidence_grade: "PREVIEW_ONLY"
model_tag: "VALUE PLAY"
model_fair_margin_selected_team_raw: -6.38
model_fair_margin_selected_team_rounded_to_0_5: -6.5
edge_vs_line_points_raw: 4.88
edge_vs_line_points_rounded_to_0_5: 5.0
supplied_total_raw: 44.0
supplied_total_rounded_to_0_5: 44.0
schedule_confirmation: "Oficjalne terminarze Bills i Texans wskazują niedzielę 13 września 2026, 13:00 ET / 12:00 CDT, w Houston. NFL Game Center identyfikuje stadion jako Reliant Stadium."
venue_confirmation: "Obiekt wraca w sierpniu 2026 do nazwy Reliant Stadium; wcześniejsze materiały mogą nadal używać nazwy NRG Stadium. Jest to ten sam stadion."
research_timestamp_utc: "2026-07-28T15:46:48Z"
research_cutoff_utc: "2026-07-28T15:46:48Z"
source_policy:
framework_authority: "Załączony plik Variant B jest nadrzędną instrukcją metodologiczną."
external_priority: "Źródła oficjalne NFL, drużyn, stadionu i NWS mają pierwszeństwo; nfelo i TeamRankings wykorzystano wyłącznie jako kontekst."
market_policy: "Nie rekonstruowano openerów, ruchu rynku ani aktualnej oferty z agregatorów. Nie przypisano określeń sharp, steam ani public."
temporal_policy: "Stan źródeł został oceniony według rzeczywistego cutoffu 28 lipca 2026, a nie według przyszłego znacznika czasu symulowanego quote."
calculation_policy: "EV, price quality, no-chase, CLV i końcowy gate wymagają deterministycznych danych wewnętrznych i nie zostały oszacowane przez model językowy."
warnings:
- "Quote timestamp 2026-09-08T18:00:00Z przypada po research_cutoff_utc. Może być zachowany jako wejście scenariusza lub przyszły snapshot symulacyjny, ale nie jako oferta potwierdzona 28 lipca 2026."
- "SIM_PREGAME_COM nie jest wykazanym market-grade sportsbookem ani dostawcą historycznych quote’ów."
- "Brakuje quote_id, potwierdzenia betslipu, sprawdzenia dostępności przy docelowej stawce i zasad rozliczenia."
- "Model version, model_run_id, model_generated_at_utc, input hash, PMF, p_cover, p_push, p_loss i raport kalibracyjny są MISSING."
- "Składy 53-osobowe, Week 1 injury reports, inactives, prognoza meczowa i decyzja o dachu nie są jeszcze należne."
- "Raport nie zawiera picka, rekomendacji zakładu ani decyzji PLAY/PASS."

points:

point_number: 1
point_name: "argument_against"
purpose: "Sformułować najmocniejszy argument przeciwko bezkrytycznemu przyjęciu wyniku modelu."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dostarczony model fair margin dla BUF wynosi dokładnie -6.38, po zaokrągleniu do 0.5 punktu: -6.5."
"Dostarczony edge_vs_line wynosi dokładnie 4.88 punktu, po zaokrągleniu do 0.5 punktu: 5.0."
"Edge 4.88 jest różnicą punktową, a nie pełnym, push-aware EV."
"Quote BUF -1.5 przy -102 pochodzi ze źródła oznaczonego SIM_PREGAME_COM i ma przyszły względem cutoffu timestamp."
"Zewnętrzny kontekst punktowy nie potwierdza niezależnie aż tak dużej przewagi: nfelo pokazuje wartości 5.9 dla BUF i 4.6 dla HOU, a TeamRankings w tabeli last-season predictive 5.3 dla BUF i 2.6 dla HOU. Różnice wynoszą odpowiednio 1.3 i 2.7 punktu, ale nie są one bezpośrednimi fair line tego spotkania."
"Bills rozpoczynają sezon z nowym head coachem Joe Bradym oraz nowymi koordynatorami ofensywy i defensywy, co zwiększa niepewność przeniesienia historycznego baseline’u na Week 1."
missing_data:
"model_version"
"model_run_id"
"model_generated_at_utc"
"model commit/input hash"
"margin PMF"
"p_cover"
"p_push"
"p_loss"
"calibration/uncertainty report"
"model-generation quote snapshot"
"neutral-site/home-field adjustment log"
"sportsbook house rules"
pending_not_due:
"Finalne składy 53-osobowe."
"Oficjalne Week 1 injury reports i inactives."
"Meczowa prognoza pogody i status dachu."
not_assessable:
"Pełne EV."
"Push-aware przewaga cenowa."
"Kalibracja prawdopodobieństwa coveru."
"To, czy modelowy edge przetrwa aktualizację składu, kontuzji i warunków."
source_evidence:
source_name: "USER_INPUT"
source_url: "N/A — dane wejściowe użytkownika"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Model margin -6.38, edge 4.88, spread -1.5, price -102 i źródło SIM_PREGAME_COM."
source_name: "nfelo — 2026 preseason ratings"
source_url: "Strona ratingów nfelo."
source_tier: "SECONDARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Point-based rating context dla BUF i HOU; nie jest to game-specific fair line."
source_name: "Buffalo Bills — coaching announcements"
source_url: "Oficjalne komunikaty Bills."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Zmiana head coacha oraz koordynatorów przed sezonem 2026."
deterministic_checks:
rounding_check:
fair_margin_raw: -6.38
fair_margin_rounded_to_0_5: -6.5
edge_raw: 4.88
edge_rounded_to_0_5: 5.0
full_ev_check: "BLOCKED_MISSING_PROBABILITIES_AND_PMF"
quote_evidence_check: "PREVIEW_ONLY"
manual_review_needed:
"Sprawdzić, czy 2026 Week 1 był objęty właściwą kalibracją modelu po zmianie sztabu BUF."
"Porównać model fair margin z raportem feature contributions i roster baseline."
"Zweryfikować, czy SIM_PREGAME_COM jest wyłącznie testowym źródłem."
recommended_machine_fields:
"argument_against_primary_code"
"model_lineage_complete"
"probability_bundle_complete"
"external_rating_gap_nfelo"
"external_rating_gap_teamrankings"
"quote_evidence_grade"
"week1_uncertainty_flag"
test_game_output:
status: "BLOCKED_FOR_FULL_EVALUATION"
strongest_counterargument: "Duży raw edge opiera się na nieweryfikowalnym dziś, przyszłym quote symulacyjnym oraz modelu bez PMF, prawdopodobieństw, kalibracji i lineage; dodatkowo BUF przechodzi znaczącą zmianę sztabu."
full_ev_status: "NOT_ASSESSABLE"
reason_codes:
"RAW_EDGE_NOT_EV"
"MISSING_MODEL_LINEAGE"
"MISSING_MARGIN_PMF"
"MISSING_PCOVER_PPUSH_PLOSS"
"FUTURE_DATED_SIM_QUOTE"
"WEEK1_STRUCTURAL_UNCERTAINTY"
"EXTERNAL_RATING_MAGNITUDE_NOT_CORROBORATED"
point_number: 2
point_name: "market_move_notes"
purpose: "Opisać ruch od openera, quote’u z momentu generowania modelu i aktualnej oferty wykonawczej."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_WHEN_DUE"
confirmed_facts:
"Dostarczono tylko jeden punkt danych: BUF -1.5 przy -102, SIM_PREGAME_COM, timestamp 2026-09-08T18:00:00Z."
"Ten timestamp przypada po cutoffie raportu, dlatego quote nie jest aktualnym, historycznie potwierdzonym snapshotem."
"Nie znaleziono ani nie rekonstruowano openera, model-generation quote ani bieżącego executable quote."
missing_data:
"opener spread i price"
"opener timestamp oraz source"
"model-generation spread i price"
"model-generation quote timestamp"
"current direct-book quote"
"quote path/event ledger"
"named-book provider history"
"line movement timestamps"
pending_not_due:
"Rzeczywisty quote z 8 września 2026, o ile zostanie wtedy przechwycony."
not_assessable:
"Liczba punktów ruchu."
"Zmiana ceny przy tej samej linii."
"Przejście przez key number."
"Kierunek rynku."
"No-chase status."
"Źródło lub charakter przepływu pieniędzy."
source_evidence:
source_name: "USER_INPUT"
source_url: "N/A — przyszły snapshot scenariusza"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Jedyny przekazany quote: BUF -1.5/-102 z SIM_PREGAME_COM."
source_name: "Variant B source policy"
source_url: "Załączona instrukcja frameworka."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Wymaga oddzielnego openera, model-generation quote i current executable quote; zabrania rekonstruowania brakującego snapshotu."
deterministic_checks:
opener_to_model_move: "NOT_CALCULATED"
model_to_current_move: "NOT_CALCULATED"
opener_to_current_move: "NOT_CALCULATED"
crossed_key_number: "UNKNOWN"
manual_review_needed:
"Zaimportować append-only quote ledger."
"Potwierdzić, czy przyszły rekord jest zaplanowanym test fixture, czy błędnym timestampem."
recommended_machine_fields:
"opener_snapshot_id"
"model_generation_snapshot_id"
"current_snapshot_id"
"movement_points"
"price_only_movement"
"crossed_key_numbers"
"quote_temporal_validity"
test_game_output:
opener: "MISSING"
model_generation_quote: "MISSING"
supplied_future_preview:
side: "BUF"
spread: -1.5
price: -102
source: "SIM_PREGAME_COM"
timestamp_utc: "2026-09-08T18:00:00Z"
evidence_grade: "PREVIEW_ONLY"
movement_status: "NOT_ASSESSABLE"
reason_codes:
"OPENER_MISSING"
"MODEL_GENERATION_QUOTE_MISSING"
"CURRENT_EXECUTABLE_QUOTE_MISSING"
"QUOTE_FUTURE_RELATIVE_TO_CUTOFF"
"MOVEMENT_NOT_ASSESSABLE"
"NO_SHARP_OR_PUBLIC_ATTRIBUTION"
point_number: 3
point_name: "injury_role_notes"
purpose: "Wykryć kontuzje, statusy i zmiany ról mogące zmienić modelowy edge."
automation_level: "SEMI"
due_status: "NOT_DUE"
criticality: "HARD_WHEN_DUE"
confirmed_facts:
"NFL Game Center nie udostępnia jeszcze injury report dla tego spotkania."
"Dla niedzielnego meczu praktyka raportowania NFL przewiduje practice reports w środę, czwartek i piątek oraz Game Status Report w piątek. Dla tego spotkania odpowiada to 9–11 września 2026."
"Termin redukcji składów do 53 zawodników przypada 30 sierpnia 2026, więc składy z 28 lipca nie są finalnymi składami Week 1."
missing_data:
"Official practice report BUF"
"Official practice report HOU"
"Game Status Report"
"Official inactives"
"snap expectations"
"replacement quality"
"role and unit impact"
"chain-reaction analysis"
pending_not_due:
"BUF/HOU Wednesday practice reports — 2026-09-09."
"BUF/HOU Thursday practice reports — 2026-09-10."
"BUF/HOU Friday reports i game statuses — 2026-09-11."
"Official game-day inactives — 2026-09-13."
not_assessable:
"Wpływ urazów na spread."
"Dostępność starterów."
"Replacement-level downgrade."
"Wpływ ograniczonych snapów."
source_evidence:
source_name: "NFL Game Center — BUF at HOU"
source_url: "Oficjalna karta meczu NFL."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Brak dostępnego injury report na dzień cutoffu."
source_name: "NFL Football Operations — Important Dates 2026"
source_url: "Oficjalny kalendarz i harmonogram raportów."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Daty finalizacji składów i game-week injury reporting."
deterministic_checks:
official_report_due_now: false
health_inference_allowed: false
roster_finalized: false
manual_review_needed:
"Nie oznaczać żadnej drużyny jako zdrowej przed publikacją raportów."
"W game week powiązać każdego zawodnika z rolą, snap share i następcą."
recommended_machine_fields:
"injury_report_due_state"
"player_status"
"practice_participation"
"starter_backup_role"
"expected_snap_delta"
"replacement_grade"
"unit_impact"
test_game_output:
status: "PENDING_NOT_DUE"
current_injury_conclusion: "UNKNOWN"
healthy_team_assumption: "PROHIBITED"
reason_codes:
"PENDING_OFFICIAL_INJURY_REPORT"
"PENDING_GAME_STATUS_REPORT"
"PENDING_INACTIVES"
"ROSTER_NOT_FINAL"
"DO_NOT_INFER_HEALTH"
point_number: 4
point_name: "schedule_spot_notes"
purpose: "Ocenić rest, travel, timezone, Week 1 i następny spot terminarzowy bez wymyślania przewagi podróżnej."
automation_level: "SEMI"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"BUF zagra na wyjeździe z HOU w niedzielę 13 września 2026 o 12:00 czasu Houston, czyli 13:00 czasu Buffalo i 17:00 UTC."
"Spotkanie odbędzie się w Reliant Stadium w Houston; HOU jest designated home team."
"Nie jest to neutral site ani international game."
"Jest to pierwszy mecz regular season obu drużyn, więc nie istnieje asymetria restu wynikająca z poprzedniego meczu regular-season."
"BUF będzie miało następny mecz w czwartek 17 września, co tworzy krótki turnaround po Week 1; HOU ma następny mecz w niedzielę 20 września."
"Buffalo przechodzi z Eastern Time do Central Time, ale kickoff o 12:00 CDT odpowiada 13:00 EDT; nie stanowi to dowodu przewagi ani niekorzystnej aklimatyzacji."
missing_data:
"BUF travel itinerary"
"czas wylotu i przylotu"
"hotel/acclimation plan"
"game-week practice location"
"indywidualne ograniczenia podróżne"
"wewnętrzna schedule-spot policy"
pending_not_due:
"Oficjalne informacje drużyn o podróży i praktykach w game week."
not_assessable:
"Travel advantage."
"Acclimation advantage."
"Wpływ krótkiego Week 2 na strategię Week 1."
source_evidence:
source_name: "Houston Texans 2026 schedule"
source_url: "Oficjalny terminarz Texans."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Data, lokalna godzina, przeciwnik i status meczu domowego."
source_name: "Buffalo Bills 2026 schedule"
source_url: "Oficjalny terminarz Bills."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Godzina ET oraz kolejny czwartkowy mecz BUF."
source_name: "NFL Game Center"
source_url: "Oficjalna karta meczu."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Houston jako lokalizacja oraz Reliant Stadium jako obiekt."
deterministic_checks:
kickoff_utc_conversion: "PASS"
neutral_site_check: false
international_game_check: false
prior_regular_season_rest_asymmetry: false
next_game_turnaround_BUF: "4 calendar days"
travel_advantage_claim_allowed: false
manual_review_needed:
"W game week sprawdzić oficjalne informacje o podróży i harmonogramie treningów BUF."
"Nie zamieniać krótkiego Week 2 w automatyczny downgrade Week 1."
recommended_machine_fields:
"travel_distance_km"
"timezone_delta_hours"
"body_clock_kickoff"
"days_since_previous_game"
"days_until_next_game"
"travel_itinerary_confirmed"
"acclimation_evidence"
test_game_output:
schedule_status: "CONFIRMED"
schedule_spot: "WEEK_1_ROAD_GAME_BUF"
verified_travel_advantage: "NONE"
future_short_week_flag_BUF: true
reason_codes:
"OFFICIAL_SCHEDULE_CONFIRMED"
"WEEK1_BOTH_TEAMS"
"DOMESTIC_TRAVEL"
"ONE_TIMEZONE_WEST"
"BUF_NEXT_GAME_SHORT_WEEK"
"TRAVEL_ITINERARY_MISSING"
"NO_TRAVEL_ADVANTAGE_CLAIM"
point_number: 5
point_name: "weather_notes"
purpose: "Ocenić game-window weather oraz ryzyko związane z dachem i nawierzchnią."
automation_level: "SEMI"
due_status: "NOT_DUE"
criticality: "HARD_WHEN_DUE"
confirmed_facts:
"Reliant Stadium ma rozsuwany dach i sztuczną nawierzchnię nad betonowym podłożem."
"Oficjalne prognozy NWS mają obecnie horyzont wielokrotnie krótszy niż okres do meczu 13 września; game-window forecast nie jest jeszcze dostępny."
"Procedura NFL dla stadionów z rozsuwanym dachem przewiduje przekazanie statusu dachu sędziemu przed meczem; obecnie nie ma podstaw do założenia open lub closed."
missing_data:
"official game-window forecast"
"temperature"
"wind sustained"
"wind gusts"
"precipitation probability and intensity"
"humidity"
"roof status"
"field-operation notice"
pending_not_due:
"Pierwszy oficjalny forecast obejmujący kickoff."
"Aktualizacje 72h, 24h i game-day."
"Decyzja lub komunikat dotyczący dachu."
not_assessable:
"Wpływ pogody na passing/kicking."
"Ekspozycja na wiatr lub deszcz."
"Wpływ warunków na total 44.0."
source_evidence:
source_name: "NRG Park/Reliant Stadium venue information"
source_url: "Oficjalna informacja o obiekcie."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Rozsuwany dach, sztuczna nawierzchnia i charakter obiektu."
source_name: "National Weather Service — Houston/Galveston"
source_url: "Oficjalny forecast NWS."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Brak prognozy obejmującej tak odległe okno meczowe."
source_name: "NFL Football Operations — stadium preparation"
source_url: "Oficjalna procedura operacyjna NFL."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Game-day operational handling rozsuwanego dachu."
deterministic_checks:
official_forecast_covers_game_window: false
roof_type: "RETRACTABLE"
roof_status: "UNKNOWN"
surface: "ARTIFICIAL_TURF"
manual_review_needed:
"Pobrać forecast NWS dla godzin bezpośrednio obejmujących kickoff."
"Zweryfikować status dachu przez NFL/team/venue communication."
recommended_machine_fields:
"forecast_issue_time_utc"
"forecast_valid_time_utc"
"temperature_f"
"wind_mph"
"gust_mph"
"precipitation_probability"
"roof_status"
"surface_status"
test_game_output:
weather_status: "PENDING_NOT_DUE"
operational_weather_risk: "UNKNOWN"
roof_assumption: "NONE"
reason_codes:
"FORECAST_OUTSIDE_OFFICIAL_WINDOW"
"RETRACTABLE_ROOF"
"ROOF_STATUS_PENDING"
"ARTIFICIAL_TURF"
"NO_WEATHER_INFERENCE"
point_number: 6
point_name: "key_number_check"
purpose: "Sprawdzić pozycję quote’u względem liczb kluczowych i zachować prawidłową logikę push."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dostarczony spread BUF wynosi dokładnie -1.5 i po zaokrągleniu do 0.5 pozostaje -1.5."
"Linia -1.5 nie jest liczbą całkowitą, dlatego sama w sobie nie tworzy możliwości pushu wynikającego z równego, całkowitego marginesu zwycięstwa."
"Linia -1.5 nie znajduje się na głównych liczbach 3 ani 7 wskazanych przez politykę Variant B."
"Bez historii quote’ów nie wiadomo, czy rynek wcześniej znajdował się na -1, -2, -2.5, -3 lub po przeciwnej stronie pick’em."
missing_data:
"quote event ledger"
"opener"
"model-generation line"
"market path"
"margin PMF"
"internal key-number configuration"
"sportsbook settlement and overtime rules"
pending_not_due:
"Aktualizacja key-number status po uzyskaniu rzeczywistej oferty we wrześniu."
not_assessable:
"Czy quote przybył na -1.5, czy odszedł z -1.5."
"Czy rynek przeciął 3 lub inną zamrożoną granicę."
"Koszt przejścia między alternatywnymi liniami."
source_evidence:
source_name: "Variant B methodology"
source_url: "Załączona instrukcja."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "3 i 7 jako główne key numbers oraz obowiązek zachowania push logic dla spreadów całkowitych."
source_name: "USER_INPUT"
source_url: "N/A — dostarczony spread"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "BUF -1.5."
deterministic_checks:
exact_spread: -1.5
rounded_spread: -1.5
is_integer_spread: false
direct_push_possible_at_this_spread: false
on_primary_key_number_3_or_7: false
crossed_key_number: "UNKNOWN"
manual_review_needed:
"Połączyć quote ledger z wewnętrznym key-number config."
"Potwierdzić book-specific rules przed obliczeniami push-aware."
recommended_machine_fields:
"is_integer_line"
"is_primary_key_number"
"distance_to_3"
"distance_to_7"
"key_numbers_crossed"
"push_probability_at_line"
test_game_output:
key_number_state: "OFF_PRIMARY_KEY_NUMBERS"
current_line_push_logic: "NO_INTEGER_PUSH_AT_MINUS_1_5"
path_check: "NOT_ASSESSABLE"
reason_codes:
"CURRENT_SPREAD_MINUS_1_5"
"HALF_POINT_LINE"
"OFF_PRIMARY_KEY_NUMBERS"
"QUOTE_PATH_MISSING"
"KEY_NUMBER_CROSSING_UNKNOWN"
point_number: 7
point_name: "no_chase_limit"
purpose: "Ustalić, czy quote pozostaje w zamrożonych granicach modelu."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dostarczono przyszły preview quote BUF -1.5/-102."
"Nie dostarczono żadnej zamrożonej granicy no-chase ani acceptable quote frontier."
missing_data:
"immutable model-generation quote"
"versioned no-chase policy"
"acceptable quote frontier"
"margin PMF"
"p_cover/p_push/p_loss"
"eligible-books policy"
"direct executable quote"
"house rules"
pending_not_due:
"Rzeczywista oferta wykonawcza w odpowiednim oknie decyzyjnym."
not_assessable:
"No-chase status."
"Maksymalny dopuszczalny spread."
"Maksymalna dopuszczalna cena."
"Czy zmiana spreadu wymaga ponownego model run."
source_evidence:
source_name: "Variant B no-chase requirements"
source_url: "Załączona instrukcja frameworka."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Zakaz odtwarzania brakującego model-generation quote oraz wymóg frontier/policy."
source_name: "USER_INPUT"
source_url: "N/A — preview quote"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "BUF -1.5/-102 z SIM_PREGAME_COM."
deterministic_checks:
immutable_origin_quote_available: false
acceptable_frontier_available: false
direct_quote_available: false
no_chase_rule_result: "NOT_CALCULATED"
manual_review_needed:
"Dostarczyć frozen no-chase policy i frontier zapisane w chwili model run."
"Nie generować granicy retrospektywnie."
recommended_machine_fields:
"policy_version"
"origin_quote_snapshot_id"
"max_allowed_spread"
"min_allowed_price"
"acceptable_quote_frontier_id"
"no_chase_status"
test_game_output:
no_chase_status: "NOT_ASSESSABLE"
gate_effect: "HARD_BLOCKER"
reason_codes:
"MISSING_FROZEN_NO_CHASE_POLICY"
"MISSING_ACCEPTABLE_QUOTE_FRONTIER"
"MISSING_MODEL_GENERATION_QUOTE"
"NON_EXECUTABLE_SIM_QUOTE"
"RETROSPECTIVE_RECONSTRUCTION_PROHIBITED"
point_number: 8
point_name: "price_quality"
purpose: "Ocenić wykonawczość i wystarczalność ceny z użyciem push-aware prawdopodobieństw."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dostarczona cena wynosi -102, ale jest związana wyłącznie z przyszłym, nieweryfikowanym źródłem SIM_PREGAME_COM."
"Nie ma potwierdzenia, że cena była dostępna w bezpośrednim betslipie przy docelowej stawce."
missing_data:
"p_cover"
"p_push"
"p_loss"
"margin PMF"
"acceptable quote frontier"
"minimum required price"
"direct betslip verification"
"target stake"
"maximum stake"
"house rules"
pending_not_due:
"Wykonawcza oferta w rzeczywistym oknie decyzyjnym."
not_assessable:
"Expected value."
"Break-even comparison z modelem."
"Minimalna akceptowalna cena."
"Wpływ push probability."
"Price quality grade."
source_evidence:
source_name: "Variant B price-quality policy"
source_url: "Załączona instrukcja."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Pełna ocena wymaga PMF, p_cover/p_push/p_loss, frontier i wykonawczego quote’u."
source_name: "USER_INPUT"
source_url: "N/A — preview price"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Cena -102."
deterministic_checks:
price_present: true
price_executable_verified: false
probability_bundle_complete: false
push_aware_ev: "NOT_CALCULATED"
price_quality: "NOT_ASSESSABLE"
manual_review_needed:
"Potwierdzić cenę w named-book betslipie z target stake."
"Uruchomić obliczenia dopiero po dostarczeniu probability bundle i house rules."
recommended_machine_fields:
"direct_book"
"quote_id"
"target_stake"
"max_stake"
"p_cover"
"p_push"
"p_loss"
"expected_value"
"minimum_required_price"
"price_quality_status"
test_game_output:
supplied_price: -102
evidence_grade: "PREVIEW_ONLY"
ev_status: "NOT_ASSESSABLE"
price_quality_status: "NOT_ASSESSABLE"
reason_codes:
"MISSING_PCOVER_PPUSH_PLOSS"
"MISSING_MARGIN_PMF"
"MISSING_ACCEPTABLE_FRONTIER"
"NO_EXECUTABLE_QUOTE"
"EV_NOT_ASSESSABLE"
"PUSH_AWARE_INPUTS_MISSING"
point_number: 9
point_name: "market_snapshot"
purpose: "Ocenić kompletność i jakość dowodu dokładnego decision/execution quote."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Zidentyfikowano event BUF at HOU, full-game spread, selected side BUF."
"Użytkownik przekazał razem spread -1.5 i price -102 ze źródła SIM_PREGAME_COM oraz timestamp 2026-09-08T18:00:00Z."
"Nie ma niezależnego potwierdzenia, że spread i cena stanowiły dostępny atomic quote."
"Timestamp przypada po research cutoff; snapshot nie może otrzymać klasy PROVIDER_GRADE, DIRECT_BOOK_GRADE ani EXECUTED_GRADE."
missing_data:
"quote_id"
"provider event id"
"direct book name"
"betslip screenshot/API response"
"target-stake check"
"max stake"
"eligible-book confirmation"
"market settlement rules"
pending_not_due:
"Rzeczywiste przechwycenie oferty 8 września lub w późniejszym oknie przedmeczowym."
not_assessable:
"Executability."
"Atomic quote integrity."
"Dostępność dla użytkownika w Norwegii."
"Dostępność przy planowanej stawce."
source_evidence:
source_name: "USER_INPUT"
source_url: "N/A — scenariuszowy snapshot"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Event, side, spread, price, source i przyszły timestamp."
source_name: "NFL Game Center"
source_url: "Oficjalna karta meczu."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Istnienie i tożsamość spotkania BUF at HOU."
deterministic_checks:
event_identity_complete: true
side_and_market_scope_complete: true
spread_and_price_present: true
timestamp_present: true
timestamp_not_after_research_cutoff: false
quote_id_present: false
direct_execution_check_present: false
evidence_grade: "PREVIEW_ONLY"
manual_review_needed:
"Zachować rekord jako SIMULATION_FIXTURE, a nie live market snapshot."
"W dniu audytu wykonać atomic capture z named book/provider."
recommended_machine_fields:
"snapshot_id"
"quote_id"
"event_provider_id"
"book_name"
"market_scope"
"spread"
"price"
"captured_at_utc"
"target_stake"
"executable_status"
"evidence_grade"
"simulation_flag"
test_game_output:
event: "2026_w01_BUF_at_HOU"
market: "full-game spread"
selected_side: "BUF"
spread: -1.5
price: -102
source: "SIM_PREGAME_COM"
timestamp_utc: "2026-09-08T18:00:00Z"
executable_status: "displayed_unverified"
evidence_grade: "PREVIEW_ONLY"
valid_decision_grade_snapshot: false
reason_codes:
"PREVIEW_ONLY"
"SIMULATED_SOURCE"
"FUTURE_DATED_AS_OF_RESEARCH_CUTOFF"
"QUOTE_ID_MISSING"
"TARGET_STAKE_CHECK_MISSING"
"DIRECT_BOOK_PROOF_MISSING"
point_number: 10
point_name: "public_bias"
purpose: "Zapisać provider-specific tickets/handle jako kontekst, bez utożsamiania go z sharp money."
automation_level: "SEMI"
due_status: "NOT_DUE"
criticality: "CONTEXT_ONLY"
confirmed_facts:
"Nie dostarczono żadnego provider-specific splitu dla BUF–HOU."
"Nie ma denominatora, czasu pomiaru ani reguł próby."
"Nie przypisano żadnego określenia sharp, public, steam ani respected."
missing_data:
"tickets percentage"
"handle percentage"
"provider"
"book population"
"market-specific denominator"
"capture timestamp"
"sample methodology"
pending_not_due:
"Splity publikowane bliżej meczu przez konkretnego operatora lub dostawcę."
not_assessable:
"Koncentracja ticketów."
"Koncentracja handle."
"Public bias."
"Znaczenie ewentualnej różnicy tickets/handle."
source_evidence:
source_name: "Variant B public-bias policy"
source_url: "Załączona instrukcja."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Zakaz uśredniania różnych dostawców i traktowania splitów jako dowodu sharp money."
deterministic_checks:
provider_present: false
tickets_present: false
handle_present: false
denominator_present: false
public_bias_status: "UNKNOWN"
manual_review_needed:
"Pobrać jeden spójny market-specific snapshot z nazwanym providerem."
"Nie mieszać DK, Circa, Action i community consensus."
recommended_machine_fields:
"split_provider"
"split_book"
"tickets_pct"
"handle_pct"
"sample_size"
"captured_at_utc"
"market_scope"
test_game_output:
status: "PENDING_NOT_DUE"
tickets_pct: "MISSING"
handle_pct: "MISSING"
sharp_money_claim: "PROHIBITED"
reason_codes:
"PUBLIC_SPLITS_NOT_AVAILABLE"
"PROVIDER_MISSING"
"DENOMINATOR_MISSING"
"NO_SHARP_LABEL"
point_number: 11
point_name: "power_rankings_check"
purpose: "Porównać wewnętrzny obraz siły zespołów z zewnętrznymi benchmarkami punktowymi."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"nfelo pokazuje Spread Value 5.9 dla BUF i 4.6 dla HOU, czyli różnicę 1.3 punktu na korzyść BUF."
"TeamRankings w tabeli oznaczonej jako last-season predictive pokazuje 5.3 dla BUF i 2.6 dla HOU, czyli różnicę 2.7 punktu."
"Oba źródła są kontekstem zewnętrznym, a nie niezależnym wyliczeniem fair line BUF at HOU."
"Obie różnice są liczbowo mniejsze niż dostarczona wielkość model fair margin 6.38, lecz skale i korekty home-field nie są bezpośrednio równoważne."
missing_data:
"internal neutral PowerScore BUF"
"internal neutral PowerScore HOU"
"internal_neutral_power_gap"
"internal market-implied neutral rating"
"model home-field adjustment"
"model feature contribution report"
"ESPN FPI 2026 game-specific projection"
"PFF/FTN point-based current benchmark"
pending_not_due:
"Aktualizacje ratingów po finalizacji składów i preseason."
not_assessable:
"Czy wewnętrzna przewaga 6.38 jest właściwie skalibrowana."
"Dokładne game-specific fair spread z benchmarków zewnętrznych."
source_evidence:
source_name: "nfelo"
source_url: "Modelowe ratingi nfelo."
source_tier: "SECONDARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Point-based comparison BUF 5.9 vs HOU 4.6."
source_name: "TeamRankings"
source_url: "Last-season predictive ratings."
source_tier: "CONTEXT_ONLY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Contextual comparison BUF 5.3 vs HOU 2.6."
deterministic_checks:
nfelo_displayed_gap_BUF_minus_HOU: 1.3
teamrankings_last_season_gap_BUF_minus_HOU: 2.7
supplied_model_margin_magnitude: 6.38
direct_scale_comparability: false
internal_power_gap_available: false
manual_review_needed:
"Porównać z internal neutral-field rating po zastosowaniu dokładnie tej samej konwencji znaków."
"Nie przeliczać ordinal rankings na punkty."
"Nie traktować last-season TeamRankings jako aktualnego 2026 fair line."
recommended_machine_fields:
"internal_power_BUF"
"internal_power_HOU"
"internal_neutral_gap"
"external_source"
"external_point_gap"
"rating_as_of_date"
"scale_comparable"
test_game_output:
external_context_direction: "BUF_HIGHER"
external_context_magnitude: "1.3_TO_2.7_POINTS_ON_NON_EQUIVALENT_SCALES"
internal_comparison_status: "PARTIAL"
model_magnitude_independently_corroborated: false
reason_codes:
"INTERNAL_POWER_GAP_MISSING"
"EXTERNAL_CONTEXT_ONLY"
"NON_EQUIVALENT_RATING_SCALES"
"MODEL_MAGNITUDE_NOT_INDEPENDENTLY_CORROBORATED"
point_number: 12
point_name: "roster_change_check"
purpose: "Sprawdzić, czy zmiany składu, sztabu i ról mogły zdezaktualizować modelowy baseline."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Bills zwolnili Seana McDermotta w styczniu 2026 i zatrudnili Joe Brady’ego jako head coacha."
"Oficjalny sztab Bills na 2026 obejmuje Pete’a Carmichaela jako offensive coordinatora oraz Jima Leonharda jako defensive coordinatora."
"Oficjalny tracker Bills odnotowuje istotne ruchy personalne, między innymi pozyskanie WR D.J. Moore’a i odejście CB Tarona Johnsona; klub dodał również zawodników do wnętrza OL."
"Texans utrzymują na 2026 główną strukturę DeMeco Ryans–Nick Caley–Matt Burke–Frank Ross, obecną także w zestawieniu sztabu 2025."
"Obie drużyny nadal znajdują się przed finalnym cięciem do 53 zawodników wyznaczonym na 30 sierpnia 2026."
missing_data:
"internal frozen roster baseline"
"internal role baseline"
"internal staff baseline"
"baseline cutoff timestamp"
"player-level model sensitivity"
"projected Week 1 starters"
"final 53-man rosters"
"final depth charts"
pending_not_due:
"Finalne cięcia składów."
"Waiver claims po cutdown."
"Week 1 depth-chart confirmations."
"Game-week role announcements."
not_assessable:
"Czy model baseline jest aktualny."
"Punktowy wpływ zmiany sztabu BUF."
"Punktowy wpływ poszczególnych transferów."
"Czy nowe role zostały już uwzględnione w model run."
source_evidence:
source_name: "Buffalo Bills official coaching announcements"
source_url: "Oficjalne komunikaty organizacji."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Zmiana head coacha oraz koordynatorów."
source_name: "Buffalo Bills official transaction/free-agency trackers"
source_url: "Oficjalne zestawienia ruchów składowych."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Przykłady istotnych zmian personalnych."
source_name: "Houston Texans official coaching staff"
source_url: "Oficjalne zestawienia sztabu 2025 i 2026."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Kontynuacja głównych stanowisk sztabu Texans."
deterministic_checks:
internal_baseline_available: false
BUF_major_staff_change: true
HOU_top_staff_continuity: true
final_53_available: false
model_staleness_result: "NOT_ASSESSABLE"
manual_review_needed:
"Porównać bieżące roster/staff/role records z dokładnym frozen baseline modelu."
"Nie uznawać samej liczby transferów za automatyczny upgrade lub downgrade."
recommended_machine_fields:
"baseline_id"
"baseline_cutoff_utc"
"staff_change_flags"
"starter_change_count"
"role_change_count"
"roster_delta_since_baseline"
"model_rerun_required"
test_game_output:
roster_baseline_status: "MISSING"
current_external_roster_research: "PARTIAL"
BUF_staff_change_flag: true
final_roster_status: "PENDING_NOT_DUE"
model_staleness: "NOT_ASSESSABLE"
reason_codes:
"INTERNAL_FROZEN_BASELINE_MISSING"
"BUF_COACHING_OVERHAUL"
"OFFSEASON_ROSTER_CHANGES_PRESENT"
"BOTH_ROSTERS_PRE_FINAL_53"
"BASELINE_STALENESS_NOT_ASSESSABLE"
point_number: 13
point_name: "matchup_specific_risk"
purpose: "Sprawdzić, czy konkretne zależności matchupowe podważają główne źródła modelowego edge."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Nie dostarczono internal matchup dependency report ani feature contribution report."
"Jako wyłącznie historyczny kontekst nfelo pokazuje dla 2025 BUF offensive EPA/play +0.15 i HOU defensive EPA/play -0.17; po drugiej stronie HOU offensive EPA/play -0.02 i BUF defensive EPA/play +0.04."
"Te wartości sugerują interesujący strength-on-strength profil BUF offense kontra HOU defense, ale nie są wystarczające do wniosku o 2026 matchup edge."
"Zmiany sztabu, składu, kontuzje i role Week 1 nie są jeszcze w pełni ustalone."
missing_data:
"internal edge drivers"
"feature contributions"
"matchup dependency report"
"2026 projected starters"
"OL versus pass-rush matchup inputs"
"WR/TE versus coverage inputs"
"run efficiency and front alignment inputs"
"injury-adjusted snap projections"
"sensitivity analysis"
pending_not_due:
"Finalny depth chart."
"Game-week injuries i role."
"Aktualne 2026 preseason/team efficiency inputs."
not_assessable:
"Który matchup generuje modelowe 4.88 punktu."
"Czy HOU defense neutralizuje główny driver BUF."
"Czy model jest nadmiernie zależny od jednego komponentu."
"Punktowy matchup adjustment."
source_evidence:
source_name: "nfelo team efficiency context"
source_url: "Tabela zespołowych EPA z sezonu 2025."
source_tier: "SECONDARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Historyczny profil ofensywy i defensywy obu drużyn."
source_name: "Variant B matchup policy"
source_url: "Załączona instrukcja."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Analiza powinna rozpoczynać się od wewnętrznych edge drivers, a nie od dowolnej narracji."
deterministic_checks:
internal_driver_report_available: false
2025_context_available: true
2026_role_adjustment_available: false
matchup_risk_grade: "NOT_ASSESSABLE"
manual_review_needed:
"Uruchomić matchup audit dopiero od listy top feature contributions modelu."
"Oddzielić dane 2025 od projekcji 2026."
recommended_machine_fields:
"top_edge_drivers"
"driver_sensitivity"
"matchup_conflict_flags"
"injury_adjusted_matchup"
"roster_baseline_id"
"data_season"
test_game_output:
status: "NOT_ASSESSABLE"
historical_context: "BUF_OFFENSE_VS_HOU_DEFENSE_STRENGTH_ON_STRENGTH"
actionable_2026_matchup_conclusion: "NONE"
reason_codes:
"MATCHUP_DRIVER_REPORT_MISSING"
"FEATURE_CONTRIBUTIONS_MISSING"
"2025_CONTEXT_ONLY"
"2026_ROLES_PENDING"
"NO_RANDOM_MATCHUP_NARRATIVE"
point_number: 14
point_name: "game_script_risk"
purpose: "Przetestować edge w realistycznych scenariuszach tempa, prowadzenia, odrabiania strat i wariancji."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Dostarczono spread BUF -1.5 i total 44.0."
"Nie dostarczono PMF, possession simulatora, scenario policy ani prawdopodobieństw cover/push/loss."
"Sam spread i total nie wystarczają do wyprowadzenia rozkładu game script."
missing_data:
"possession/play-by-play simulator"
"margin PMF"
"p_cover"
"p_push"
"p_loss"
"frozen scenario policy"
"pace/pass-rate assumptions"
"turnover sensitivity"
"injury-adjusted inputs"
"weather-adjusted inputs"
pending_not_due:
"Aktualizacja symulatora po finalnych roster, injury i weather inputs."
not_assessable:
"Kruchość modelowego edge przy prowadzeniu HOU."
"Kruchość edge w one-score game."
"Wpływ tempa i pass rate."
"Turnover dependency."
"Cover probability w poszczególnych scenariuszach."
source_evidence:
source_name: "Variant B game-script requirements"
source_url: "Załączona instrukcja."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Game-script audit wymaga wewnętrznego symulatora/PMF i zamrożonej polityki scenariuszy."
source_name: "USER_INPUT"
source_url: "N/A — spread i total"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "BUF -1.5 oraz total 44.0."
deterministic_checks:
simulator_available: false
PMF_available: false
probability_bundle_available: false
scenario_stress_test: "NOT_RUN"
manual_review_needed:
"Nie generować game-script probabilities z narracji tekstowej."
"Uruchomić deterministyczny symulator po zamrożeniu aktualnych wejść."
recommended_machine_fields:
"simulator_version"
"scenario_policy_version"
"leading_trailing_scenarios"
"pace_sensitivity"
"turnover_sensitivity"
"cover_probability_by_scenario"
test_game_output:
status: "NOT_ASSESSABLE"
scenario_results: "MISSING"
narrative_substitution_allowed: false
reason_codes:
"SIMULATOR_MISSING"
"PMF_MISSING"
"SCENARIO_POLICY_MISSING"
"PROBABILITY_BUNDLE_MISSING"
"NARRATIVE_SIMULATION_PROHIBITED"
point_number: 15
point_name: "closing_line"
purpose: "Przechwycić ostatni rzeczywisty spread przed zamknięciem rynku."
automation_level: "HYBRID"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts:
"Mecz jest zaplanowany na 13 września 2026 o 17:00 UTC."
"Na cutoff 28 lipca 2026 closing line nie istnieje."
"Zaplanowany kickoff nie może zostać automatycznie użyty jako timestamp close."
missing_data:
"close_snapshot_id"
"closing spread"
"closing timestamp"
"closing book/provider"
"full closing ladder"
pending_not_due:
"Finalny snapshot rynku tuż przed rzeczywistym zamknięciem."
not_assessable:
"Closing line."
source_evidence:
source_name: "Official schedule"
source_url: "Oficjalne terminarze Texans/Bills."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Mecz jeszcze się nie odbył i rynek nie osiągnął close."
source_name: "Variant B closing-line policy"
source_url: "Załączona instrukcja."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Close wymaga rzeczywistego snapshotu i nie może być zastąpiony godziną kickoffu."
deterministic_checks:
market_closed: false
closing_line_available: false
closing_line_capture: "NOT_RUN"
manual_review_needed:
"Zaplanować append-only close capture."
recommended_machine_fields:
"close_snapshot_id"
"closing_spread"
"closing_timestamp_utc"
"closing_source"
"provider_declared_close"
test_game_output:
closing_line: "POST_EVENT_ONLY"
reason_codes:
"MARKET_NOT_CLOSED"
"CLOSE_SNAPSHOT_MISSING"
"KICKOFF_NOT_ASSUMED_AS_CLOSE"
point_number: 16
point_name: "closing_price"
purpose: "Przechwycić closing price z dokładnie tego samego snapshotu co closing line."
automation_level: "HYBRID"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts:
"Nie istnieje jeszcze close snapshot."
"Closing price musi być związana z tym samym close_snapshot_id co closing spread."
missing_data:
"close_snapshot_id"
"closing price"
"closing spread"
"closing source"
"both-side closing ladder"
pending_not_due:
"Closing price dostępna przy rzeczywistym zamknięciu rynku."
not_assessable:
"Closing price."
"Price movement przy stałym spreadzie."
source_evidence:
source_name: "Variant B closing-price policy"
source_url: "Załączona instrukcja."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Closing price i line muszą pochodzić z tego samego snapshotu."
deterministic_checks:
close_snapshot_available: false
same_snapshot_integrity_check: "NOT_RUN"
manual_review_needed:
"Przechwycić obie strony spreadu i pełną cenę z identycznym timestampem."
recommended_machine_fields:
"close_snapshot_id"
"closing_price"
"closing_spread"
"opposite_side_price"
"closing_timestamp_utc"
test_game_output:
closing_price: "POST_EVENT_ONLY"
reason_codes:
"MARKET_NOT_CLOSED"
"CLOSING_PRICE_MISSING"
"SAME_SNAPSHOT_REQUIRED"
point_number: 17
point_name: "clv_points"
purpose: "Obliczyć spread CLV oraz oddzielnie zmianę ceny między decision snapshot i close."
automation_level: "INTERNAL_ONLY"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts:
"Dostarczony snapshot decyzyjny ma jedynie klasę PREVIEW_ONLY."
"Closing line i closing price nie są dostępne."
"Nie połączono spread CLV i price CLV w jeden sztuczny wskaźnik."
missing_data:
"valid decision_snapshot_id"
"close_snapshot_id"
"closing spread"
"closing price"
"selected-team spread convention"
"full closing ladder"
pending_not_due:
"Obliczenie po przechwyceniu rzeczywistego close."
not_assessable:
"CLV points."
"Price CLV."
"Key-number-aware CLV context."
source_evidence:
source_name: "Variant B CLV policy"
source_url: "Załączona instrukcja."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Zakaz liczenia CLV bez punktów 15–16 i zakaz łączenia spread/price CLV."
deterministic_checks:
valid_decision_snapshot: false
closing_snapshot_available: false
spread_clv: "NOT_CALCULATED"
price_clv: "NOT_CALCULATED"
manual_review_needed:
"Po close zweryfikować konwencję znaku z perspektywy BUF."
"Uruchomić Python/rule engine oddzielnie dla spreadu i ceny."
recommended_machine_fields:
"decision_snapshot_id"
"close_snapshot_id"
"spread_clv_points"
"price_clv"
"key_number_context"
test_game_output:
clv_points: "POST_EVENT_ONLY"
clv_price: "POST_EVENT_ONLY"
reason_codes:
"DECISION_SNAPSHOT_PREVIEW_ONLY"
"CLOSE_MISSING"
"CLV_NOT_CALCULABLE"
point_number: 18
point_name: "process_quality"
purpose: "Zastosować wewnętrzny quality gate dla punktów 1–17 z rozróżnieniem braków i elementów jeszcze nienależnych."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Tożsamość meczu, data, kickoff, venue i home/away są potwierdzone oficjalnie."
"Market evidence pozostaje PREVIEW_ONLY."
"Model lineage i probability bundle są MISSING."
"Injury, weather i inactives są prawidłowo sklasyfikowane jako NOT_DUE, a nie jako failures."
"Closing line, closing price i CLV są POST_EVENT_ONLY."
missing_data:
"immutable audit bundle"
"process policy registry"
"event-clock/due-window engine output"
"evidence manifest"
"calculation manifest"
"model lineage"
"manual override log"
pending_not_due:
"Game-week injury package."
"Game-window weather package."
"Roof status."
"Inactives."
"Closing package."
not_assessable:
"Numeryczny process-quality score."
"Execution readiness."
"Model validation readiness."
source_evidence:
source_name: "Variant B process-quality policy"
source_url: "Załączona instrukcja frameworka."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Not-due items nie są błędami, ale due hard blockers mają pierwszeństwo."
source_name: "Official schedule and venue evidence"
source_url: "NFL/team/venue sources."
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Game identity domain jest potwierdzony."
deterministic_checks:
due_hard_blockers_present: true
not_due_items_count_as_failure: false
post_event_items_count_as_failure_now: false
numeric_quality_score_generated: false
manual_review_needed:
"Zbudować immutable evidence manifest."
"Uzupełnić model lineage, probability bundle i model-generation snapshot."
"Zarejestrować symulowany quote jako fixture, nie live evidence."
recommended_machine_fields:
"run_status"
"domain_status"
"due_status"
"criticality"
"gate_effect"
"effective_status"
"readiness_by_phase"
"evidence_manifest_id"
"calculation_manifest_id"
test_game_output:
run_status: "HOLD"
effective_status: "HOLD"
gate_effect: "BLOCK_ADVANCEMENT"
domain_status:
game_identity: "PASS"
schedule_and_venue: "PASS"
model_lineage: "BLOCKED"
model_probabilities: "BLOCKED"
market_snapshot: "BLOCKED_PREVIEW_ONLY"
market_movement: "BLOCKED"
injuries: "NOT_DUE"
weather: "NOT_DUE"
roster_baseline: "BLOCKED"
power_rankings: "PARTIAL"
matchup_specific: "BLOCKED"
game_script: "BLOCKED"
closing_and_clv: "POST_EVENT_ONLY"
readiness_by_phase:
identity_and_schedule_research: "READY"
early_preseason_context: "PARTIAL"
model_validation: "NOT_READY"
decision_grade_market_audit: "NOT_READY"
game_week_audit: "NOT_DUE"
execution_audit: "NOT_READY"
post_event_audit: "NOT_DUE"
reason_codes:
"HARD_BLOCKERS_PRESENT"
"MARKET_EVIDENCE_PREVIEW_ONLY"
"MODEL_LINEAGE_MISSING"
"PROBABILITY_BUNDLE_MISSING"
"INTERNAL_BASELINE_MISSING"
"NOT_DUE_ITEMS_EXCLUDED_FROM_FAILURES"
"RUN_STATUS_HOLD"
point_number: 19
point_name: "final_operator_decision"
purpose: "Deterministycznie skierować audyt do właściwej kolejnej czynności bez wydawania decyzji bettingowej."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Punkt 18 wykazuje due hard blockers."
"Brak jest decision-grade market snapshotu i wymaganych artefaktów modelu."
"Część danych jest prawidłowo PENDING_NOT_DUE, a closing/CLV są POST_EVENT_ONLY."
missing_data:
"frozen process_quality snapshot id"
"operator decision policy version"
"blocker classification registry"
"action routing registry"
"manual override log"
pending_not_due:
"Injury, weather, roof, inactives i close capture."
not_assessable:
"Przejście do execution-ready stage."
"Audit completion."
source_evidence:
source_name: "Variant B operator-routing policy"
source_url: "Załączona instrukcja."
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:46:48Z"
supports_claim: "Dozwolone stany HOLD/OPEN/INVALID oraz zakaz używania PLAY/PASS."
deterministic_checks:
point_18_effective_status: "HOLD"
hard_blockers_present: true
invalid_or_fabricated_evidence_confirmed: false
gate_state_result: "HOLD"
manual_review_needed:
"Zarejestrować decyzję w append-only operator ledger."
"Po uzupełnieniu danych ponownie uruchomić punkty 1, 2, 7, 8, 9, 12, 13, 14 i 18."
recommended_machine_fields:
"operator_decision_id"
"process_quality_snapshot_id"
"policy_version"
"gate_state"
"operator_action"
"hold_type"
"required_actions"
"decision_timestamp_utc"
test_game_output:
gate_state: "HOLD"
operator_action: "HOLD_PENDING_DATA"
hold_type: "INTERNAL_DATA_AND_TEMPORAL_EVIDENCE_HOLD"
required_actions:
"Oznaczyć SIM_PREGAME_COM 2026-09-08T18:00:00Z jako simulation fixture, nie jako potwierdzony live quote."
"Dostarczyć model_version, model_run_id, model_generated_at_utc, input/commit hash i calibration report."
"Dostarczyć margin PMF oraz p_cover, p_push i p_loss."
"Dostarczyć immutable model-generation quote, acceptable quote frontier i frozen no-chase policy."
"Przechwycić rzeczywisty atomic quote z named book/provider wraz z quote_id, timestampem, executability i target-stake check."
"Dostarczyć frozen roster/staff/role baseline oraz feature-contribution/matchup report."
"Dostarczyć simulator/scenario policy albo pozostawić punkty 13–14 jako NOT_ASSESSABLE."
"W odpowiednich terminach dodać oficjalne injury reports, weather, roof status i inactives."
nonblocking_pending_items:
"Official Week 1 injury reports — nienależne na obecnym cutoffie."
"Official game-window weather — nienależne."
"Roof status — nienależny."
"Closing line, closing price i CLV — POST_EVENT_ONLY."
prohibited_transitions:
"Nie przechodzić do READY_FOR_NEXT_AUDIT_STAGE."
"Nie wyliczać EV ani price quality z samego raw edge."
"Nie przypisywać no-chase status bez frozen frontier."
"Nie rekonstruować openera ani model-generation quote."
"Nie nazywać ruchu sharp/public/steam."
"Nie wydawać rekomendacji bettingowej ani PLAY/PASS."
decision_provenance:
process_quality_status: "HOLD"
framework: "Variant B"
research_cutoff_utc: "2026-07-28T15:46:48Z"
decisive_blockers:
"MODEL_LINEAGE_MISSING"
"PROBABILITY_BUNDLE_MISSING"
"DECISION_GRADE_MARKET_SNAPSHOT_MISSING"
"NO_CHASE_FRONTIER_MISSING"
"INTERNAL_ROSTER_BASELINE_MISSING"
reason_codes:
"GATE_HOLD"
"HOLD_PENDING_DATA"
"NOT_INVALID_BECAUSE_SIMULATION_IS_EXPLICIT"
"NO_BETTING_DECISION"

summary:
hard_blockers:
- "Model lineage: version, run id, generation timestamp i hash."
- "Margin PMF oraz p_cover/p_push/p_loss."
- "Immutable model-generation quote."
- "Acceptable quote frontier i frozen no-chase policy."
- "Decision-grade atomic market snapshot."
- "Frozen roster/staff/role baseline."
- "Internal feature-contribution/matchup dependency report."
- "Simulator/scenario policy dla game-script risk."
warnings:
- "SIM_PREGAME_COM jest źródłem symulacyjnym, nie market-grade evidence."
- "Quote timestamp przypada po research cutoff."
- "BUF ma nowy sztab na 2026, a finalne składy obu drużyn nie są jeszcze znane."
- "Zewnętrzne ratingi są wyłącznie kontekstem i nie potwierdzają bezpośrednio fair margin -6.38."
- "Venue może występować w starszych materiałach jako NRG Stadium, ale oficjalna nazwa na termin meczu to Reliant Stadium."
pending_not_due:
- "Final 53-man rosters."
- "Week 1 injury reports i game statuses."
- "Official inactives."
- "Game-window weather."
- "Roof status."
- "Provider-specific public splits."
internal_inputs_required_from_me:
- "Model lineage bundle."
- "Probability/PMF bundle."
- "Model-generation quote snapshot."
- "No-chase policy i acceptable frontier."
- "Roster/staff/role baseline."
- "Feature contributions."
- "Simulator/scenario policy."
data_to_capture_manually:
- "Named-book atomic quote z timestampem i quote_id."
- "Target-stake executability."
- "Game-week official injury reports."
- "Official weather i roof status."
- "Closing line i price z jednego snapshotu."
next_best_action: "Zachować obecny raport jako early-preseason research shell, oznaczyć przyszły SIM quote jako fixture i uzupełnić najpierw model lineage, PMF oraz rzeczywisty model-generation snapshot."

final_summary:
audit_readiness_now: "HOLD — GAME IDENTITY CONFIRMED, BUT MODEL AND MARKET EXECUTION LAYERS ARE NOT READY"
due_hard_blockers:
- "MISSING model lineage."
- "MISSING PMF i p_cover/p_push/p_loss."
- "MISSING immutable model-generation quote."
- "MISSING acceptable quote frontier i no-chase policy."
- "MISSING decision-grade executable market snapshot."
- "MISSING internal frozen roster baseline."
- "MISSING internal matchup/game-script artifacts."
not_due_items:
- "Finalne składy 53-osobowe."
- "Oficjalne injury reports z 9–11 września 2026."
- "Game-day inactives."
- "Prognoza obejmująca kickoff."
- "Status rozsuwanego dachu."
- "Provider-specific public splits."
post_event_only_items:
- "closing_line"
- "closing_price"
- "clv_points"
- "price CLV"
data_i_must_enter_manually:
- "model_version"
- "model_run_id"
- "model_generated_at_utc"
- "commit/input hash"
- "p_cover"
- "p_push"
- "p_loss"
- "margin PMF reference"
- "acceptable quote frontier"
- "frozen no-chase policy"
- "model-generation quote snapshot"
- "target stake"
- "eligible book policy"
- "internal roster/staff/role baseline"
- "internal feature contributions"
- "simulator/scenario policy"
data_gpt_found_with_sources:
- "Mecz: BUF at HOU, Sunday 13 September 2026."
- "Kickoff: 12:00 CDT / 13:00 EDT / 17:00 UTC."
- "Venue: Reliant Stadium, Houston; wcześniejsza nazwa NRG Stadium."
- "Retractable roof i artificial turf."
- "Official injury reporting nie jest jeszcze należny; final roster cut przypada 30 sierpnia."
- "Bills wchodzą w 2026 z nowym head coachem i koordynatorami."
- "Zewnętrzny rating context: nfelo gap 1.3; TeamRankings last-season predictive gap 2.7, oba na nieporównywalnych bezpośrednio skalach."
data_that_requires_internal_python:
- "Push-aware EV."
- "Minimum required price."
- "Acceptable quote frontier evaluation."
- "No-chase gate."
- "PMF-derived p_cover/p_push/p_loss checks."
- "Matchup sensitivity."
- "Game-script simulation."
- "Spread CLV i oddzielny price CLV."
- "Final process-quality gate po uzupełnieniu evidence manifest."
next_step_for_me: "Nie traktować BUF -1.5/-102 jako live quote. Najpierw podpiąć pełny model artifact bundle i immutable quote z momentu model run; następnie w odpowiednim dniu przechwycić wykonawczą ofertę z named book/provider i wykonać delta refresh."
safe_to_advance_to_next_audit_stage: false
