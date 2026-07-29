# GPT Snapshot

season: 2026
week: 1
game_id: 2026_w01_NO_at_DET
snapshot_type: full_19_points
created_at_local: 2026-07-28T19:02:16.962539+02:00
source_thread: GPT

## GPT Output

audit_metadata:
game_identity:
season: 2026
week: 1
game_id: "2026_w01_NO_at_DET"
game_date_local: "2026-09-13"
game_date_usa: "2026-09-13"
scheduled_kickoff_local: "2026-09-13T13:00:00-04:00"
scheduled_kickoff_utc: "2026-09-13T17:00:00Z"
away_team: "NO"
home_team: "DET"
designated_home_team: "DET"
venue: "Ford Field"
venue_city_country: "Detroit, Michigan, USA"
neutral_site: false
international_game: false
official_schedule_confirmation: "Detroit oficjalnie podaje Week 1 vs New Orleans, niedziela 13 września 2026 o 13:00 EDT na Ford Field; oficjalny terminarz Saints potwierdza ten sam mecz jako wyjazdowy o 12:00 CDT."
venue_confirmation: "Ford Field jest krytym stadionem w centrum Detroit; oficjalna strona obiektu wskazuje również wydarzenie Saints vs Lions 13 września 2026 o 13:00."
market: "full-game spread"
selected_team: "DET"
current_spread_selected_team_exact: -7.0
current_spread_selected_team_rounded_to_0_5: -7.0
market_margin_selected_team: 7.0
current_price_american: -109
current_price_decimal_reference: 1.9174
total: 49.5
book_or_source: "SIM_PREGAME_COM"
quote_timestamp_utc: "2026-09-08T18:00:00Z"
quote_temporal_status: "FUTURE_DATED_RELATIVE_TO_RESEARCH_CUTOFF"
quote_after_research_cutoff_by: "42 days, 02:01:52"
quote_before_scheduled_kickoff_by: "4 days, 23:00:00"
executable_status: "UNKNOWN"
evidence_grade: "PREVIEW_ONLY"
model_version: "MISSING"
model_run_id: "MISSING"
model_generated_at_utc: "MISSING"
model_input_hash: "MISSING"
model_fair_margin_selected_team_raw: 11.17
model_fair_margin_selected_team_rounded_to_0_5: 11.0
model_fair_spread_selected_team_equivalent_raw: -11.17
model_fair_spread_selected_team_equivalent_rounded_to_0_5: -11.0
edge_vs_line_points_raw: 4.17
edge_vs_line_points_rounded_to_0_5: 4.0
model_tag: "GOW"
model_tag_interpretation: "Wewnętrzna etykieta modelowa; nie jest rekomendacją bettingową."
p_cover: "MISSING"
p_push: "MISSING"
p_loss: "MISSING"
margin_pmf_available: "UNKNOWN"
acceptable_quote_frontier_available: "UNKNOWN"
research_timestamp_utc: "2026-07-28T15:58:08Z"
research_cutoff_utc: "2026-07-28T15:58:08Z"
source_policy:
framework_instruction: "Nadrzędną instrukcją jest załączony prompt Variant B."
primary_sources_used:
- "Oficjalne terminarze NFL i obu klubów."
- "Oficjalne strony Ford Field, NFL Football Operations, transakcji i sztabów obu klubów."
- "NOAA/National Weather Service dla zasad dostępności prognoz."
secondary_sources_used:
- "nfelo jako bezpośrednie źródło własnego modelu zewnętrznego."
- "Wtórne zestawienie wartości ESPN FPI wyłącznie jako kontekst, nie jako ostateczny dowód."
internal_input_treatment:
- "Spread, cena, total, model margin, edge i tag pochodzą z danych przekazanych przez użytkownika."
- "Nie zastępowano przyszłego quote inną znalezioną linią i nie rekonstruowano brakującego opener/model-generation quote."
- "SIM_PREGAME_COM nie jest traktowany jako nazwany sportsbook ani jako dowód wykonalności."
warnings:
- "FUTURE_DATED_QUOTE: quote 2026-09-08T18:00:00Z znajduje się ponad 42 dni po cutoffie badania."
- "NON_MARKET_GRADE_SOURCE: prefiks SIM i brak nazwanego sportsbooku, betslipu, quote ID oraz stake check."
- "RAW_EDGE_NOT_EV: różnica fair margin 4.17 punktu nie zastępuje PMF ani p_cover/p_push/p_loss."
- "KEY_NUMBER_7: linia DET -7.0 zachowuje realny stan push przy zwycięstwie dokładnie siedmioma punktami."
- "WEEK_1_UNCERTAINTY: ostateczne składy, role, raporty kontuzji i game-status reports nie są jeszcze ustalone."
- "ROSTER_CUTDOWN_PENDING: ostateczna redukcja do 53 zawodników przypada 30 sierpnia 2026."

points:

point_number: 1
point_name: "argument_against"
purpose: "Zbudować najmocniejszy, oparty na danych kontrargument przeciwko bezkrytycznemu przyjęciu wyniku modelu."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Arytmetyka inputu jest spójna: 11.17 - 7.00 = 4.17 punktu edge."
"Modelowa marża +11.17 odpowiada fair spread DET -11.17; wyświetlenie do 0.5 punktu wynosi DET -11.0."
"Aktualny input DET -7.0 znajduje się dokładnie na podstawowym key number 7; zwycięstwo DET dokładnie siedmioma punktami tworzy push, a nie wygraną zakładu."
"Detroit zmieniło koordynatora ofensywy z Johna Mortona w 2025 na Drew Petzinga w 2026, co musi być uwzględnione w wersji modelowego baseline’u."
"Oficjalny log Detroit pokazuje znaczące zmiany personalne przed sezonem, w tym odejścia Taylora Deckera, Grahama Glasgow i Davida Montgomery’ego oraz szereg nowych graczy; sam fakt zmian jest potwierdzony, ale ich wartość modelowa nie została dostarczona."
missing_data:
"model_version"
"model_run_id"
"model_generated_at_utc"
"commit_hash / input_hash"
"margin PMF"
"p_cover"
"p_push"
"p_loss"
"calibration and uncertainty report"
"home-field adjustment log"
"model-generation market snapshot"
"sportsbook settlement and overtime rules"
pending_not_due:
"Oficjalne raporty kontuzji i role Week 1."
"Ostateczny skład po redukcji do 53 zawodników."
not_assessable:
"Pełne EV."
"Kalibracja tagu GOW dla tego konkretnego poziomu niepewności."
"Czy modelowy baseline uwzględnia wszystkie zmiany roster/staff z 2026."
source_evidence:
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Raw fair-margin edge nie może zostać potraktowany jako pełne EV bez PMF i prawdopodobieństw."
source_name: "Detroit Lions official coaching announcements"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Petzing został koordynatorem ofensywy w 2026, podczas gdy w sztabie 2025 funkcję tę pełnił Morton."
source_name: "Detroit Lions official transactions"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Potwierdza offseasonowe zmiany kadrowe Detroit."
deterministic_checks:
edge_formula:
formula: "model_margin_selected_team - market_margin_selected_team"
calculation: "11.17 - 7.00 = 4.17"
status: "PASS"
rounding:
fair_margin_to_nearest_0_5: 11.0
edge_to_nearest_0_5: 4.0
current_spread_to_nearest_0_5: -7.0
full_ev: "NOT_CALCULATED"
push_state_preserved: true
manual_review_needed:
"Zweryfikować, czy fair margin +11.17 zawiera prawidłowy home-field adjustment dla Ford Field."
"Sprawdzić model lineage i datę zamrożenia roster baseline."
"Sprawdzić PMF w przedziale marginesów 6/7/8."
recommended_machine_fields:
"model_lineage_complete"
"roster_baseline_cutoff_utc"
"staff_baseline_version"
"p_margin_exactly_7"
"p_cover_at_minus_7"
"p_loss_at_minus_7"
"calibration_bucket_GOW"
test_game_output:
strongest_argument_against: "Podane 4.17 punktu jest wyłącznie różnicą fair margin względem linii. Nie dowodzi dodatniego EV przy cenie -109, ponieważ nie ma p_cover, p_push ani p_loss, a dokładnie na -7 część rozkładu kończy się pushem. Dodatkowo quote jest przyszłą symulacją, a Week 1 obejmuje potwierdzone zmiany sztabu i składu, których uwzględnienia w modelu nie można potwierdzić."
status: "HARD_BLOCKED_FOR_EV"
betting_recommendation: "NOT_PROVIDED"
reason_codes:
"RAW_MARGIN_NOT_EV"
"PMF_MISSING"
"PROBABILITIES_MISSING"
"KEY_7_PUSH"
"FUTURE_SIMULATED_QUOTE"
"MODEL_LINEAGE_MISSING"
"WEEK1_BASELINE_STALENESS_RISK"
point_number: 2
point_name: "market_move_notes"
purpose: "Opisać ruch od opener przez model-generation quote do aktualnego wykonywalnego quote."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Dostarczono tylko jeden scenariuszowy punkt: DET -7.0 przy -109 z timestampem 2026-09-08T18:00:00Z."
"Timestamp tego punktu jest przyszły względem cutoffu 2026-07-28T15:58:08Z."
missing_data:
"Opener wraz z timestampem i źródłem."
"Quote użyty dokładnie przy generowaniu modelu."
"Rzeczywisty aktualny executable quote na moment cutoffu."
"Append-only quote path."
"Zmiany ceny przy niezmienionym spreadzie."
pending_not_due:
"Rzeczywisty snapshot rynku z 8 września 2026."
not_assessable:
"Liczba punktów ruchu."
"Czy rynek doszedł do 7, odszedł od 7 lub przeszedł przez 7."
"Czy ruch dotyczył spreadu, ceny czy obu."
"No-chase status."
"Jakakolwiek etykieta sharp/public/steam."
source_evidence:
source_name: "User-supplied game input"
source_url: "N/A — supplied in request"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Jedyny przekazany quote to scenariusz DET -7.0/-109 z przyszłym timestampem."
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Wymaga osobnego przechowywania opener, model-generation quote i executable quote oraz zakazuje nieudokumentowanych etykiet rynku."
deterministic_checks:
opener_to_model_move: "NOT_CALCULATED"
model_to_current_move: "NOT_CALCULATED"
opener_to_current_move: "NOT_CALCULATED"
key_number_crossing: "UNKNOWN"
manual_review_needed:
"Dołączyć immutable opener snapshot."
"Dołączyć snapshot z dokładnego czasu uruchomienia modelu."
"Nie zastępować żadnego z nich późniejszą linią z pamięci lub agregatora."
recommended_machine_fields:
"opener_snapshot_id"
"model_generation_snapshot_id"
"decision_snapshot_id"
"spread_delta_points"
"price_delta"
"crossed_key_7"
"quote_provider"
test_game_output:
opener: "MISSING"
model_generation_quote: "MISSING"
current_executable_quote_at_cutoff: "MISSING"
supplied_future_scenario_quote:
side: "DET"
spread: -7.0
price: -109
timestamp_utc: "2026-09-08T18:00:00Z"
evidence_status: "PREVIEW_ONLY_FUTURE_DATED"
market_move: "UNKNOWN"
sharp_public_classification: "NOT_PERMITTED_WITHOUT_SOURCE"
reason_codes:
"OPENER_MISSING"
"MODEL_GENERATION_QUOTE_MISSING"
"CURRENT_EXECUTABLE_QUOTE_MISSING"
"FUTURE_TIMESTAMP"
"MOVEMENT_NOT_ASSESSABLE"
point_number: 3
point_name: "injury_role_notes"
purpose: "Zidentyfikować ryzyka kontuzji, statusu i roli mogące zmienić modelowy edge."
automation_level: "SEMI"
due_status: "NOT_DUE"
criticality: "HARD_WHEN_DUE"
confirmed_facts:
"Dla niedzielnych meczów NFL wymaga Practice Reports w środę, czwartek i piątek oraz Game Status Report w piątek; dla tego meczu odpowiada to 9–11 września 2026."
"Detroit 26 lipca umieściło Briana Brancha, Tylera Conklina i Kerby’ego Josepha na Active/PUP; jest to status campowy, nie oficjalny status meczowy na Week 1."
"New Orleans 12 maja umieściło Nicka Saldiveriego na Reserve/PUP."
"Oficjalna strona raportu kontuzji Saints nie zawierała jeszcze raportu Week 1 na dzień cutoffu."
missing_data:
"Week 1 Practice Reports DET i NO."
"Week 1 Game Status Reports."
"Game-day inactives."
"Docelowe role, snap share i zastępstwa."
"Statusy QB, OL, secondary, pass rush i skill positions w tygodniu meczu."
pending_not_due:
"Practice Report: 2026-09-09."
"Practice Report: 2026-09-10."
"Practice Report oraz Game Status Report: 2026-09-11."
"Oficjalne inactives w dniu meczu."
not_assessable:
"Nie można stwierdzić, że obie drużyny są zdrowe."
"Nie można przeliczyć wpływu obecnych PUP statuses na spread Week 1."
"Nie można ustalić replacement quality ani chain reaction bez finalnego depth chartu."
source_evidence:
source_name: "NFL Football Operations important dates"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Oficjalny harmonogram raportowania kontuzji dla niedzielnych meczów."
source_name: "Detroit Lions official transactions"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Campowe statusy PUP Brancha, Conklina i Josepha."
source_name: "New Orleans Saints official transactions and injury page"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Status Saldiveriego i brak opublikowanego raportu Week 1."
deterministic_checks:
official_report_due_window: "2026-09-09 through 2026-09-11"
game_week_report_available_now: false
health_assumption_allowed: false
manual_review_needed:
"Po każdym raporcie przypisać starter/backup, expected snaps, replacement i wpływ na jednostkę."
"Powtórzyć kontrolę po finalnym Game Status Report oraz po inactives."
recommended_machine_fields:
"player"
"team"
"position"
"practice_status_by_day"
"game_status"
"starter_status"
"expected_snap_share"
"replacement_player"
"unit_impact"
"chain_reaction"
test_game_output:
status: "PENDING_NOT_DUE"
current_context_only:
DET_active_PUP:
"Brian Branch"
"Tyler Conklin"
"Kerby Joseph"
NO_reserve_PUP:
"Nick Saldiveri"
Week_1_availability_conclusion: "UNKNOWN"
reason_codes:
"OFFICIAL_REPORT_NOT_DUE"
"INACTIVES_NOT_DUE"
"DO_NOT_INFER_HEALTH"
"CAMP_PUP_NOT_GAME_STATUS"
point_number: 4
point_name: "schedule_spot_notes"
purpose: "Ocenić terminarz, odpoczynek, podróż, zmianę strefy czasowej i kontekst Week 1."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Mecz odbędzie się w niedzielę 13 września 2026 o 13:00 EDT na Ford Field."
"Terminarz Saints pokazuje ten sam kickoff jako 12:00 CDT, co odzwierciedla jednogodzinną różnicę między strefą czasu New Orleans i Detroit."
"Detroit zagra następnie w czwartek 17 września na wyjeździe z Buffalo."
"New Orleans zagra następnie w niedzielę 20 września na wyjeździe z Baltimore."
"Mecz nie jest neutral-site ani international game; oficjalne terminarze oznaczają Detroit jako gospodarza na Ford Field."
missing_data:
"Dokładny plan podróży Saints."
"Data i godzina przylotu do Detroit."
"Informacja o hotelu, aklimatyzacji i miejscach treningów."
"Ewentualne zmiany rutyny związane z Week 1."
pending_not_due:
"Oficjalne komunikaty travel/practice z tygodnia meczu."
"Konferencje trenerów dotyczące logistycznego przygotowania."
not_assessable:
"Nie można przypisać żadnej drużynie przewagi podróżnej lub aklimatyzacyjnej."
"Nie można stwierdzić look-ahead Detroit na krótki Week 2 bez dowodu dotyczącego przygotowania lub zarządzania składem."
source_evidence:
source_name: "Detroit Lions official schedule"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Data, kickoff, Ford Field i następny czwartkowy mecz Detroit."
source_name: "New Orleans Saints official schedule"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Wyjazdowy status Saints, lokalnie wyświetlany kickoff oraz następny mecz w Baltimore."
deterministic_checks:
kickoff_utc_conversion: "13:00 EDT = 17:00 UTC"
away_timezone_shift: "+1 hour eastbound from CDT to EDT"
DET_next_game_calendar_gap: "4 days"
NO_next_game_calendar_gap: "7 days"
neutral_site_check: "PASS_FALSE"
international_game_check: "PASS_FALSE"
manual_review_needed:
"Sprawdzić itinerary Saints w tygodniu meczu."
"Nie zamieniać samej odległości lub strefy czasowej w automatyczny adjustment bez polityki i dowodów."
recommended_machine_fields:
"travel_departure_utc"
"travel_arrival_utc"
"timezones_crossed"
"distance_km"
"practice_location_by_day"
"days_to_next_game"
"short_week_next_game"
test_game_output:
schedule_spot: "STANDARD_WEEK_1_HOME_GAME_FOR_DET"
travel_context: "NO travels one time zone east; itinerary unknown."
future_schedule_context:
DET: "Thursday road game at BUF on 2026-09-17"
NO: "Sunday road game at BAL on 2026-09-20"
claimed_schedule_advantage: "NONE"
reason_codes:
"WEEK1"
"ONE_TIMEZONE_EASTBOUND"
"ITINERARY_MISSING"
"DET_SHORT_WEEK_FOLLOWS"
"NO_TRAVEL_ADVANTAGE_CLAIM"
point_number: 5
point_name: "weather_notes"
purpose: "Ocenić pogodę w oknie meczu oraz ryzyko operacyjne obiektu i nawierzchni."
automation_level: "SEMI"
due_status: "NOT_DUE"
criticality: "HARD_WHEN_DUE"
confirmed_facts:
"Ford Field jest krytym stadionem."
"Oficjalna strona obiektu podaje nawierzchnię FieldTurf Classic HD."
"NWS udostępnia prognozę godzinową do siedmiu dni naprzód; kickoff pozostaje około 47 dni po cutoffie, więc oficjalna prognoza game-window nie jest jeszcze dostępna."
missing_data:
"Temperatura zewnętrzna w oknie dojazdu i kickoffu."
"Opady, burze, ostrzeżenia i ryzyko transportowe."
"Oficjalne game-day operating notices Ford Field."
"Aktualny field-operation report."
pending_not_due:
"Pierwsza oficjalna prognoza NWS obejmująca 13 września."
"Prognoza godzinowa 72–24 godziny przed kickoffem."
"Game-day observations i ostrzeżenia."
not_assessable:
"Wpływ pogody na tempo, passing, kicking lub turnovers."
"Ryzyko podróży i dotarcia kibiców/drużyn."
source_evidence:
source_name: "Ford Field official stadium information"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Kryty obiekt i oficjalnie wskazana nawierzchnia."
source_name: "NOAA/National Weather Service forecast documentation"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Prognozy godzinowe NWS obejmują następne siedem dni."
deterministic_checks:
venue_type: "INDOOR"
surface: "FieldTurf Classic HD"
game_inside_official_forecast_horizon: false
forecast_status: "PENDING_NOT_DUE"
manual_review_needed:
"Odświeżyć NWS po wejściu meczu w siedmiodniowe okno."
"Sprawdzić komunikaty Ford Field o operacjach obiektu i nawierzchni."
recommended_machine_fields:
"forecast_issued_at_utc"
"forecast_hour"
"temperature"
"wind_speed"
"wind_gust"
"precipitation_probability"
"weather_alerts"
"venue_operating_status"
"surface_status"
test_game_output:
weather_status: "PENDING_NOT_DUE"
indoor_context: "CONFIRMED"
game_window_forecast: "MISSING_NOT_YET_AVAILABLE"
weather_adjustment: "NOT_CALCULATED"
reason_codes:
"INDOOR_VENUE"
"FORECAST_OUTSIDE_NWS_HORIZON"
"GAME_WINDOW_WEATHER_NOT_DUE"
point_number: 6
point_name: "key_number_check"
purpose: "Określić położenie linii względem key numbers i zachować prawidłową logikę push."
automation_level: "FULL"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dokładny spread wybranej drużyny wynosi DET -7.0."
"Zaokrąglony spread pozostaje DET -7.0."
"7 jest podstawowym key number zgodnie z polityką Variant B; każda linia całkowita może zakończyć się pushem."
missing_data:
"Quote path pokazujący, czy rynek doszedł do 7 lub przeszedł przez 7."
"Margin PMF, w szczególności masa na dokładnie 7."
"House rules dotyczące spreadu, overtime i settlement."
pending_not_due: []
not_assessable:
"Wartość przejścia z -6.5 na -7 lub z -7 na -7.5."
"Czy obecne -7 narusza frozen no-chase frontier."
source_evidence:
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Wymaga zachowania push logic i traktuje 3 oraz 7 jako podstawowe key numbers."
deterministic_checks:
current_key_state: "ON_PRIMARY_KEY_7"
standard_margin_boundaries:
DET_cover: "DET wins by 8 or more"
push: "DET wins by exactly 7"
DET_spread_loss: "DET wins by 6 or fewer, ties, or loses"
actual_settlement_rules: "MISSING"
arrived_at_key_7: "UNKNOWN"
crossed_key_7: "UNKNOWN"
manual_review_needed:
"Pobrać PMF dla marginesu dokładnie 7."
"Sprawdzić zasady konkretnego sportsbooku."
"Odtworzyć wyłącznie z append-only ledger, czy linia przekroczyła 7."
recommended_machine_fields:
"key_number"
"on_key"
"crossed_key"
"p_exact_margin_7"
"settlement_push_allowed"
"quote_path_complete"
test_game_output:
key_number: 7
line_position: "EXACTLY_ON_7"
push_logic_preserved: true
path_to_key: "UNKNOWN"
no_chase_conclusion: "NOT_CALCULATED"
reason_codes:
"ON_KEY_7"
"PUSH_POSSIBLE"
"PMF_MISSING"
"QUOTE_PATH_MISSING"
"HOUSE_RULES_MISSING"
point_number: 7
point_name: "no_chase_limit"
purpose: "Sprawdzić, czy quote mieści się w zamrożonych przy generowaniu modelu granicach."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dostarczona linia scenariuszowa to DET -7.0 przy -109."
"Quote ma przyszły timestamp i nie jest aktualnym executable quote na cutoff."
missing_data:
"Immutable model-generation quote."
"Versioned no-chase policy."
"Acceptable quote frontier wygenerowany razem z modelem."
"PMF oraz p_cover/p_push/p_loss."
"Eligible-books policy."
"House rules konkretnego booka."
"Direct betslip/provider-grade quote."
pending_not_due:
"Rzeczywisty quote z planowanego okna 8 września."
not_assessable:
"ALLOWED / REVIEW / BLOCKED."
"Maksymalny dozwolony spread."
"Minimalna dozwolona cena."
"Wpływ przejścia przez -7."
source_evidence:
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Zakazuje ręcznego odtwarzania model-generation quote i wymaga frozen policy/frontier."
deterministic_checks:
quote_vs_frontier: "NOT_CALCULATED"
spread_limit_check: "NOT_CALCULATED"
price_limit_check: "NOT_CALCULATED"
key_number_boundary_check: "INPUT_READY_BUT_POLICY_MISSING"
manual_review_needed:
"Odzyskać oryginalny model bundle zamiast ustalać limit po fakcie."
"Ustalić, czy frontier jest wyrażony jako para spread/price, a nie sam spread."
recommended_machine_fields:
"no_chase_policy_version"
"acceptable_spread_min"
"acceptable_spread_max"
"acceptable_price_by_spread"
"frontier_generated_at_utc"
"frontier_hash"
test_game_output:
no_chase_status: "NOT_ASSESSABLE"
supplied_quote: "DET -7.0 at -109"
gate_effect: "HARD_BLOCK"
reason_codes:
"MODEL_GENERATION_QUOTE_MISSING"
"NO_CHASE_POLICY_MISSING"
"FRONTIER_MISSING"
"FUTURE_NONEXECUTABLE_QUOTE"
point_number: 8
point_name: "price_quality"
purpose: "Ocenić, czy cena jest wykonywalna i wystarczająca dla dodatniego, push-aware EV."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Cena scenariuszowa wynosi -109, co odpowiada kursowi dziesiętnemu około 1.9174."
"Spread -7.0 zawiera stan push, więc prosty próg dwuwynikowy nie jest wystarczającą oceną ceny."
missing_data:
"p_cover"
"p_push"
"p_loss"
"Margin PMF"
"Acceptable quote frontier"
"Direct sportsbook confirmation przy docelowej stawce"
"House rules"
"Limit i możliwy price change przy podaniu stake"
pending_not_due:
"Aktualna wykonywalna cena w docelowym dniu audytu."
not_assessable:
"Expected value."
"Minimalna akceptowalna cena."
"Czy -109 jest wystarczające."
"Maksymalna stawka możliwa po tej cenie."
source_evidence:
source_name: "User-supplied quote"
source_url: "N/A — supplied in request"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Scenariuszowa cena -109 przy DET -7.0."
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Wymaga PMF i push-aware logic oraz nakazuje zwrócić NOT_ASSESSABLE przy słabym quote evidence."
deterministic_checks:
decimal_conversion: 1.9174
two_outcome_break_even_reference_only: "52.1531%"
two_outcome_reference_warning: "Nie uwzględnia p_push i nie jest finalnym progiem."
push_aware_ev_formula_for_risk_109_to_win_100: "EV = 100p_cover - 109p_loss"
push_aware_positive_ev_condition: "p_cover > 109*(1-p_push)/209"
full_ev_result: "NOT_CALCULATED"
manual_review_needed:
"Dostarczyć trzy prawdopodobieństwa sumujące się do 1."
"Sprawdzić cenę bezpośrednio na betslipie przy docelowej stawce."
recommended_machine_fields:
"p_cover"
"p_push"
"p_loss"
"expected_profit_per_unit_risk"
"minimum_acceptable_price"
"maximum_stake_at_quote"
"quote_recheck_timestamp_utc"
test_game_output:
price_quality: "NOT_ASSESSABLE"
nominal_price: -109
executable_price: "UNKNOWN"
ev: "NOT_CALCULATED"
gate_effect: "HARD_BLOCK"
reason_codes:
"P_COVER_MISSING"
"P_PUSH_MISSING"
"P_LOSS_MISSING"
"EXECUTABILITY_NOT_CONFIRMED"
"PUSH_AWARE_EV_REQUIRED"
point_number: 9
point_name: "market_snapshot"
purpose: "Zachować dokładny quote decyzyjny lub wykonawczy wraz z dowodem."
automation_level: "SEMI"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Tożsamość wydarzenia NO @ DET, data, kickoff i Ford Field są potwierdzone oficjalnymi terminarzami."
"Przekazany quote zawiera jedną parę spread/price: DET -7.0 przy -109."
"Quote timestamp 2026-09-08T18:00:00Z jest dokładnie 4 dni i 23 godziny przed planowanym kickoffem, ale pozostaje ponad 42 dni po research cutoff."
"SIM_PREGAME_COM nie identyfikuje rzeczywistego sportsbooku ani dostawcy named-book quote."
missing_data:
"Rzeczywista nazwa booka."
"Quote ID lub snapshot ID."
"Direct betslip."
"Potwierdzenie market scope i overtime settlement."
"Executable status."
"Target stake check."
"Maksymalna dostępna stawka."
pending_not_due:
"Rzeczywisty snapshot z 8 września 2026."
not_assessable:
"Czy quote był dostępny do zawarcia."
"Czy cena zmieniłaby się po wpisaniu stawki."
"Czy source kwalifikuje się według eligible-books policy."
source_evidence:
source_name: "Detroit Lions, Saints and Ford Field official schedules"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Potwierdzają wydarzenie, gospodarza, czas i obiekt."
source_name: "User-supplied scenario quote"
source_url: "N/A — supplied in request"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Podaje spread, cenę, źródło i przyszły timestamp."
deterministic_checks:
event_match: "PASS"
side_market_scope_present: true
spread_and_price_supplied_as_one_pair: true
quote_timestamp_before_kickoff: true
quote_timestamp_at_or_before_research_cutoff: false
target_stake_verified: false
manual_review_needed:
"W docelowym czasie otworzyć bezpośredni betslip i sprawdzić quote po wpisaniu target stake."
"Zachować screenshot/receipt, quote ID, timestamp i book name."
recommended_machine_fields:
"decision_snapshot_id"
"quote_id"
"book"
"market_scope"
"spread"
"price"
"captured_at_utc"
"target_stake"
"max_stake"
"executable_status"
test_game_output:
event: "NO at DET"
selected_side: "DET"
market: "full-game spread"
supplied_spread: -7.0
supplied_price: -109
supplied_source: "SIM_PREGAME_COM"
evidence_grade: "PREVIEW_ONLY"
temporal_validity: "FUTURE_DATED_AT_RESEARCH_CUTOFF"
execution_grade: "NOT_ESTABLISHED"
snapshot_valid_for_real_decision: false
reason_codes:
"PREVIEW_ONLY"
"SIMULATED_SOURCE"
"FUTURE_DATED_QUOTE"
"BOOK_IDENTITY_MISSING"
"TARGET_STAKE_NOT_CHECKED"
point_number: 10
point_name: "public_bias_tickets_handle"
purpose: "Zebrać kontekst koncentracji tickets/handle bez nazywania go dowodem sharp money."
automation_level: "SEMI"
due_status: "NOT_DUE"
criticality: "CONTEXT_ONLY"
confirmed_facts: []
missing_data:
"Market-specific tickets percentage."
"Market-specific handle percentage."
"Provider."
"Timestamp."
"Sample size i denominator rules."
"Rozdzielenie spread/ML/total."
pending_not_due:
"Provider-specific splits bliżej game week i decision timestamp."
not_assessable:
"Public concentration."
"Rozbieżność tickets vs handle."
"Jakakolwiek klasyfikacja sharp/public."
source_evidence:
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Zakazuje agregowania nieporównywalnych splitów i traktowania ich jako automatyczny dowód sharp money."
deterministic_checks:
provider_count: 0
percentages_available: false
cross_provider_average: "NOT_CALCULATED"
manual_review_needed:
"Zapisać osobno każdy provider i rodzaj rynku."
"Nie mieszać DK, Circa, community consensus i innych denominatorów."
recommended_machine_fields:
"provider"
"market"
"side"
"tickets_pct"
"handle_pct"
"sample_rule"
"captured_at_utc"
test_game_output:
status: "PENDING_NOT_DUE"
public_bias: "UNKNOWN"
sharp_money_claim: "PROHIBITED"
reason_codes:
"SPLITS_NOT_AVAILABLE"
"CONTEXT_ONLY"
"NO_SHARP_INFERENCE"
point_number: 11
point_name: "power_rankings_check"
purpose: "Porównać wewnętrzną ocenę siły drużyn z zewnętrznymi benchmarkami punktowymi."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "SOFT_REQUIRED"
confirmed_facts:
"Aktualna tabela nfelo pokazuje dla Detroit wartość spreadową +4.6, a dla New Orleans -2.8; różnica tych dwóch wartości wynosi 7.4 punktu. Wiersze tabeli są jednocześnie oznaczone rekordami sezonu 2025, dlatego jest to kontekst offseasonowy, a nie finalna projekcja meczu Week 1."
"Oficjalny ESPN FPI 2026 jest opublikowany, ale wartości wierszy nie zostały udostępnione w możliwym do bezpośredniego zacytowania odczycie strony."
"Wtórne zestawienie ESPN FPI podaje DET +2.5 oraz NO -2.7, czyli różnicę 5.2 punktu; jest to wyłącznie SECONDARY CONTEXT, nie primary row capture."
missing_data:
"Internal neutral-field PowerScore DET."
"Internal neutral-field PowerScore NO."
"Internal neutral power gap."
"Dokładny home-field adjustment użyty przez model."
"Daty/vintage wszystkich benchmarków."
"Primary captured ESPN FPI rows."
pending_not_due:
"Aktualizacja benchmarków po finalnych składach i po preseason."
not_assessable:
"Bezpośrednie apples-to-apples porównanie model margin +11.17 z neutralnym benchmarkiem."
"Czy różnica wynika z HFA, QB adjustment, rosteru czy innej cechy modelu."
source_evidence:
source_name: "nfelo Power Ratings"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Bezpośrednie wartości własnego modelu nfelo dla DET i NO."
source_name: "ESPN 2026 FPI"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Potwierdza, że edycja FPI 2026 jest aktywna."
source_name: "SportsGrid summary of ESPN 2026 FPI"
source_url: "LINK_VIA_CITATION"
source_tier: "SECONDARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Wtórnie raportuje DET +2.5 i NO -2.7."
deterministic_checks:
nfelo_listed_spread_value_gap: "4.6 - (-2.8) = 7.4"
secondary_reported_ESPN_FPI_gap: "2.5 - (-2.7) = 5.2"
model_game_margin: 11.17
normalized_comparison: "NOT_CALCULATED_DUE_TO_UNKNOWN_HFA_AND_VINTAGE"
manual_review_needed:
"Dodać wewnętrzny neutral-field gap i oddzielny HFA."
"Zarchiwizować pełne wiersze ESPN FPI/PFF/FTN z datą dostępu."
"Nie porównywać ordinal rank z punktowym marginem."
recommended_machine_fields:
"internal_neutral_power_DET"
"internal_neutral_power_NO"
"internal_neutral_power_gap"
"home_field_adjustment"
"external_source"
"external_point_gap"
"external_vintage"
test_game_output:
internal_power_gap: "MISSING"
external_context:
nfelo_listed_gap: 7.4
secondary_reported_ESPN_FPI_gap: 5.2
direction_check: "External context rates DET above NO."
magnitude_check_against_model_11_17: "NOT_ASSESSABLE_WITHOUT_NORMALIZATION"
final_sanity_grade: "PARTIAL"
reason_codes:
"INTERNAL_POWER_GAP_MISSING"
"HFA_NORMALIZATION_MISSING"
"EXTERNAL_BENCHMARK_CONTEXT_ONLY"
"VINTAGE_MISMATCH_RISK"
point_number: 12
point_name: "roster_change_check"
purpose: "Sprawdzić, czy zmiany rosteru, sztabu lub ról czynią modelowy baseline nieaktualnym."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"NFL wyznaczyła ostateczną redukcję składów do 53 zawodników na 30 sierpnia 2026; obecne składy pozostają przed-cut rosterami."
"Detroit zatrudniło Drew Petzinga jako OC na 2026; Kelvin Sheppard pozostaje DC, a Mike Kafka jest pass game coordinator."
"Detroit oficjalnie odnotowało m.in. odejścia Taylora Deckera, Grahama Glasgow i Davida Montgomery’ego oraz pozyskanie Juice’a Scruggsa, Isiaha Pacheco, Bena Bartcha, Cade’a Maysa, Larry’ego Boroma, D.J. Wonnuma i Paytona Turnera."
"Detroit umieściło Brancha, Conklina i Josepha na Active/PUP 26 lipca."
"New Orleans pozyskało w offseason m.in. Zacha Wilsona, Travisa Etienne’a Jr., Noah Fanta, Kadena Ellissa, Anfernee Jenningsa, Martina Emersona Jr. i Tyree Wilsona."
"Sztab Saints na 2026 obejmuje Kellena Moore’a jako HC, Douga Nussmeiera jako OC i Brandona Staleya jako DC."
missing_data:
"Wewnętrzny frozen roster baseline."
"Wewnętrzny frozen staff baseline."
"Modelowy depth chart i role baseline."
"Baseline cutoff timestamp."
"Informacja, które transakcje były już włączone do model run."
"Projected starters oraz snap shares."
pending_not_due:
"Finalny 53-man roster po 30 sierpnia."
"Practice squad i późniejsze waiver claims."
"Week 1 depth charts i inactives."
not_assessable:
"Czy model jest roster-stale."
"Ile punktów każda zmiana dodaje lub odejmuje."
"Czy PUP statuses zmieniają Week 1 projection."
source_evidence:
source_name: "NFL Football Operations"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Termin finalnej redukcji rosterów."
source_name: "Detroit Lions official transactions and coaching staff"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Potwierdzone zmiany zawodników i sztabu Detroit."
source_name: "New Orleans Saints official transactions and coaching staff"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Potwierdzone zmiany zawodników i aktualny sztab Saints."
deterministic_checks:
final_roster_cut_completed: false
internal_baseline_available: false
external_change_log_available: true
stale_baseline_check: "NOT_ASSESSABLE"
manual_review_needed:
"Porównać każdy oficjalny roster/staff delta z frozen baseline modelu."
"Nadać zmianom role importance i expected snaps, zamiast opierać się na samych nazwiskach."
recommended_machine_fields:
"baseline_player_id"
"current_player_id"
"transaction_type"
"role_before"
"role_after"
"expected_snap_delta"
"staff_change"
"included_in_model_run"
test_game_output:
external_roster_changes: "CONFIRMED"
internal_baseline: "MISSING"
roster_staleness: "NOT_ASSESSABLE"
gate_effect: "HARD_BLOCK_UNTIL_BASELINE_COMPARISON"
reason_codes:
"ROSTER_BASELINE_MISSING"
"STAFF_BASELINE_MISSING"
"FINAL_53_NOT_DUE"
"CONFIRMED_OFFSEASON_CHURN"
point_number: 13
point_name: "matchup_specific_risk"
purpose: "Sprawdzić, czy konkretne konflikty matchupowe podważają źródła modelowego edge."
automation_level: "HYBRID"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dostarczono końcowy edge 4.17, ale nie dostarczono feature contributions ani listy driverów tego edge."
"Detroit ma potwierdzoną zmianę OC oraz przebudowę części OL/RB, natomiast Saints dodało kilku zawodników front seven; są to fakty kadrowe, a nie dowód przewagi którejkolwiek strony."
"Campowe statusy Brancha i Josepha oraz status Saldiveriego są potwierdzone, ale ich dostępność Week 1 pozostaje nieznana."
missing_data:
"Internal matchup dependency report."
"Feature contribution/sensitivity report."
"Model drivers tworzące fair margin +11.17."
"Finalne role i availability."
"Aktualne projected OL combinations."
"Comparable 2026 split data."
pending_not_due:
"Preseason role evidence."
"Final depth charts."
"Week 1 injury reports."
not_assessable:
"Końcowy matchup risk grade."
"Czy edge opiera się na pass rush, rushing efficiency, secondary, QB, pace lub turnovers."
"Czy model jest nadmiernie zależny od jednego mismatchu."
source_evidence:
source_name: "Detroit and New Orleans official transactions"
source_url: "LINK_VIA_CITATION"
source_tier: "PRIMARY"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Potwierdzają zmiany, które tworzą pytania do ręcznego audytu matchupów."
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Nakazuje rozpoczynać od wewnętrznych driverów modelu i nie wymyślać przypadkowych narracji matchupowych."
deterministic_checks:
internal_edge_driver_count: "MISSING"
matchup_sensitivity_available: false
final_risk_grade: "NOT_CALCULATED"
manual_review_needed:
"Pytanie kontrolne, nie wniosek: czy przebudowana OL Detroit i nowy system Petzinga zmieniają założenia modelu przeciw frontowi Saints?"
"Pytanie kontrolne, nie wniosek: jeżeli Branch/Joseph pozostaną ograniczeni, jaki jest wpływ na role coverage i komunikację secondary?"
"Pytanie kontrolne, nie wniosek: jeżeli Saldiveri pozostanie niedostępny, jaki jest projected protection matchup przeciw rotacji edge Detroit?"
"Każde pytanie przypisać do konkretnego model feature i sensitivity test."
recommended_machine_fields:
"edge_driver"
"feature_contribution_points"
"opposing_unit"
"availability_dependency"
"sensitivity_low"
"sensitivity_base"
"sensitivity_high"
"matchup_risk_grade"
test_game_output:
matchup_specific_risk: "NOT_ASSESSABLE"
review_hypotheses_only:
"DET offensive-system/OL continuity versus NO front."
"DET secondary availability versus NO passing personnel."
"NO protection continuity versus DET edge rotation."
hypotheses_are_conclusions: false
gate_effect: "HARD_BLOCK"
reason_codes:
"EDGE_DRIVERS_MISSING"
"FEATURE_CONTRIBUTIONS_MISSING"
"FINAL_ROLES_NOT_DUE"
"MATCHUP_GRADE_NOT_ASSESSABLE"
point_number: 14
point_name: "game_script_risk"
purpose: "Przetestować edge pod różnymi realistycznymi przebiegami meczu."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Scenariuszowe total 49.5 i market margin DET +7.0 implikują arytmetyczne team totals DET 28.25 oraz NO 21.25."
"Przy spreadzie DET -7.0 margines końcowy 6, 7 lub 8 prowadzi odpowiednio do loss, push lub cover po stronie spreadu."
missing_data:
"Internal possession/play-by-play simulator."
"Margin PMF."
"p_cover/p_push/p_loss."
"Frozen scenario policy."
"Turnover, explosive-play, pace i late-game dependencies."
"Aktualne roster/injury/weather inputs."
pending_not_due:
"Game-week injuries i weather."
"Finalne role oraz projected starters."
not_assessable:
"Wrażliwość edge na tempo."
"Wrażliwość na dodatni/ujemny turnover differential."
"Backdoor-cover exposure."
"Prawdopodobieństwo lądowania dokładnie na 7."
source_evidence:
source_name: "User-supplied market scenario"
source_url: "N/A — supplied in request"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Dostarcza total 49.5 i margin 7.0 użyte wyłącznie do arytmetyki scenariusza."
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Wymaga simulatora/PMF i zwrotu NOT_ASSESSABLE, gdy ich brakuje."
deterministic_checks:
scenario_implied_DET_points: 28.25
scenario_implied_NO_points: 21.25
margin_6_result_for_DET_minus_7: "LOSS"
margin_7_result_for_DET_minus_7: "PUSH"
margin_8_result_for_DET_minus_7: "COVER"
simulation_run: false
manual_review_needed:
"Uruchomić scenariusze wokół marginesów 6/7/8."
"Oddzielnie przetestować DET prowadzące i kontrolujące tempo, mecz jednoposiadaniowy oraz DET z ujemnym turnover differential."
"Nie przypisywać prawdopodobieństw scenariuszom bez modelu."
recommended_machine_fields:
"scenario_id"
"pace_state"
"turnover_state"
"halftime_margin"
"fourth_quarter_margin"
"final_margin"
"cover_push_loss_result"
"scenario_probability"
test_game_output:
game_script_risk: "NOT_ASSESSABLE"
key_margin_scenarios_identified: true
probabilities_assigned: false
gate_effect: "HARD_BLOCK"
reason_codes:
"SIMULATOR_MISSING"
"PMF_MISSING"
"SCENARIO_POLICY_MISSING"
"KEY_7_SCRIPT_SENSITIVITY"
point_number: 15
point_name: "closing_line"
purpose: "Zachować końcowy pregame spread z rzeczywistego momentu zamknięcia rynku."
automation_level: "SEMI"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts: []
missing_data:
"Closing spread."
"Close timestamp."
"Close snapshot ID."
"Provider-declared close lub direct-book close."
pending_not_due:
"Rynek musi najpierw faktycznie się zamknąć."
not_assessable:
"Closing line."
source_evidence:
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Zakazuje używania planowanego kickoffu jako close, jeżeli rynek nie został wtedy faktycznie zamknięty."
deterministic_checks:
market_closed: false
closing_line_capture: "POST_EVENT_ONLY"
manual_review_needed:
"Zarchiwizować ostatni faktyczny quote przed zamknięciem rynku."
recommended_machine_fields:
"close_snapshot_id"
"closing_spread"
"market_closed_at_utc"
"close_provider"
test_game_output:
closing_line: "POST_EVENT_ONLY"
reason_codes:
"MARKET_NOT_CLOSED"
"POST_EVENT_ONLY"
point_number: 16
point_name: "closing_price"
purpose: "Zachować cenę z tego samego snapshotu co closing line."
automation_level: "SEMI"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts: []
missing_data:
"Closing price."
"Ten sam close_snapshot_id co w punkcie 15."
"Pełna closing ladder, jeżeli dostępna."
pending_not_due:
"Finalny close snapshot."
not_assessable:
"Closing price."
source_evidence:
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Closing price nie może być oddzielona od closing line i snapshotu."
deterministic_checks:
close_snapshot_available: false
closing_price_capture: "POST_EVENT_ONLY"
manual_review_needed:
"Zapisać spread i price atomowo."
recommended_machine_fields:
"close_snapshot_id"
"closing_price"
"closing_spread"
"closing_ladder"
test_game_output:
closing_price: "POST_EVENT_ONLY"
reason_codes:
"CLOSE_SNAPSHOT_MISSING"
"POST_EVENT_ONLY"
point_number: 17
point_name: "clv_points"
purpose: "Obliczyć CLV z decision snapshot i wspólnego close snapshotu."
automation_level: "FULL"
due_status: "POST_EVENT_ONLY"
criticality: "POST_EVENT"
confirmed_facts:
"Decision snapshot nie ma realnego execution grade."
"Closing line i closing price nie istnieją jeszcze."
missing_data:
"Valid decision_snapshot_id."
"close_snapshot_id."
"Closing spread i price."
"Pełna closing ladder dla price-aware porównania."
pending_not_due:
"Faktyczne zamknięcie rynku."
not_assessable:
"Spread CLV."
"Price CLV."
"Key-number-adjusted CLV."
source_evidence:
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "CLV nie może być liczone bez punktów 15 i 16 ani łączone w jeden sztuczny numer."
deterministic_checks:
spread_clv: "NOT_CALCULATED"
price_clv: "NOT_CALCULATED"
combined_fake_clv: "PROHIBITED"
manual_review_needed:
"Po close uruchomić deterministic rule engine z jedną konwencją znaku spreadu."
recommended_machine_fields:
"decision_snapshot_id"
"close_snapshot_id"
"spread_clv_points"
"price_clv"
"crossed_key_number"
test_game_output:
clv_points: "POST_EVENT_ONLY"
reason_codes:
"DECISION_SNAPSHOT_NOT_EXECUTION_GRADE"
"CLOSE_NOT_AVAILABLE"
"POST_EVENT_ONLY"
point_number: 18
point_name: "process_quality"
purpose: "Zastosować wewnętrzną bramkę jakości do punktów 1–17 z uwzględnieniem ich due status."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Game identity, data, kickoff, venue, neutral-site status i schedule spot są potwierdzone oficjalnymi źródłami."
"Punkty dotyczące oficjalnych injury reports, weather, public splits oraz close/CLV nie są obecnie należne i nie powinny być liczone jako failures."
"Kilka należnych domen pozostaje hard-blocked przez brak danych wewnętrznych i realnego market snapshotu."
missing_data:
"Immutable audit bundle."
"Process policy registry."
"Calculation manifest."
"Model lineage."
"Evidence manifest."
"Manual override log."
"Operator decision policy."
pending_not_due:
"Injury reports i inactives."
"Game-window weather."
"Public splits."
"Closing line/price i CLV."
not_assessable:
"Pełny numeric process score, jeżeli taki istnieje."
"Final readiness według nieprzekazanej wewnętrznej polityki wag."
source_evidence:
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Not-due nie jest failure, lecz każdy due hard blocker ma pierwszeństwo nad wynikiem liczbowym."
deterministic_checks:
due_hard_blocker_count: 7
not_due_items_counted_as_failures: false
post_event_items_counted_as_failures: false
gate_result: "HOLD"
manual_review_needed:
"Dołączyć process policy registry i zweryfikować klasyfikację hard/soft."
"Zatwierdzić kompletność evidence manifest."
recommended_machine_fields:
"run_status"
"domain_status"
"due_status"
"criticality"
"gate_effect"
"effective_status"
"readiness_by_phase"
test_game_output:
run_status: "HOLD"
domain_status:
game_identity: "PASS"
schedule_and_venue: "PASS"
edge_arithmetic: "PASS"
model_lineage_and_probabilities: "MISSING_BLOCKING"
market_move_path: "MISSING"
market_snapshot: "MISSING_BLOCKING"
key_number: "PASS_WITH_PUSH_WARNING"
no_chase: "NOT_ASSESSABLE_BLOCKING"
price_quality: "NOT_ASSESSABLE_BLOCKING"
injuries: "PENDING_NOT_DUE"
weather: "PENDING_NOT_DUE"
public_splits: "PENDING_NOT_DUE_NONBLOCKING"
power_rankings: "PARTIAL"
roster_baseline: "MISSING_BLOCKING"
matchup_specific_risk: "NOT_ASSESSABLE_BLOCKING"
game_script_risk: "NOT_ASSESSABLE_BLOCKING"
close_and_clv: "POST_EVENT_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
gate_effect: "HOLD"
effective_status: "HOLD_DUE_TO_DUE_HARD_BLOCKERS"
readiness_by_phase:
early_research: "PARTIAL"
model_validation: "HOLD"
executable_quote_validation: "NOT_READY"
game_week_update: "NOT_DUE"
post_event_close_and_clv: "POST_EVENT_ONLY"
reason_codes:
"DUE_HARD_BLOCKERS_PRESENT"
"NOT_DUE_ITEMS_EXCLUDED_FROM_FAILURES"
"MODEL_BUNDLE_INCOMPLETE"
"MARKET_EVIDENCE_INSUFFICIENT"
"INTERNAL_RISK_REPORTS_MISSING"
point_number: 19
point_name: "final_operator_decision"
purpose: "Skierować audyt do właściwego następnego stanu bez wydawania rekomendacji bettingowej."
automation_level: "INTERNAL_ONLY"
due_status: "DUE"
criticality: "HARD_REQUIRED"
confirmed_facts:
"Dostarczone wartości model margin, market margin i edge są arytmetycznie spójne."
"Źródło quote jest jawnie symulacyjne i przyszłe, dlatego nie stanowi dowodu rzeczywistego wykonania."
"Braki dotyczą zarówno danych modelowych, jak i market evidence."
missing_data:
"Frozen operator decision policy."
"Action routing registry."
"Append-only operator decision ledger."
"Manual override log."
pending_not_due:
"Game-week i post-event updates."
not_assessable:
"Jakakolwiek akcja PLAY/PASS — jest poza zakresem audytu i zakazana przez instrukcję."
source_evidence:
source_name: "Attached Variant B research prompt"
source_url: "ATTACHED_FILE"
source_tier: "INTERNAL_REQUIRED"
captured_or_accessed_at: "2026-07-28T15:58:08Z"
supports_claim: "Definiuje gate states i akcje operatora oraz zakazuje rekomendacji PLAY/PASS."
deterministic_checks:
gate_state_from_available_evidence: "HOLD"
invalid_input_detected: false
transparent_simulation_detected: true
hard_blockers_present: true
manual_review_needed:
"Po uzupełnieniu model bundle i realnego quote ponownie uruchomić punkty 1, 2, 6–9 oraz 12–14."
recommended_machine_fields:
"gate_state"
"operator_action"
"hold_type"
"required_actions"
"nonblocking_pending_items"
"prohibited_transitions"
"decision_provenance"
test_game_output:
gate_state: "HOLD"
operator_action: "HOLD_PENDING_DATA"
hold_type: "MISSING_INTERNAL_DATA_AND_TEMPORALLY_INVALID_MARKET_EVIDENCE"
required_actions:
"Dołączyć model version, run ID, generated_at, hash i calibration bundle."
"Dołączyć margin PMF oraz p_cover/p_push/p_loss."
"Dołączyć immutable model-generation quote."
"Dołączyć frozen no-chase policy i acceptable quote frontier."
"Zastąpić przyszły SIM quote rzeczywistym direct-book/provider-grade snapshotem w chwili decyzji."
"Porównać oficjalne roster/staff deltas z internal frozen baseline."
"Dołączyć matchup dependency report i game-script simulator output."
nonblocking_pending_items:
"Official Week 1 injury reports i inactives."
"Game-window NWS forecast."
"Provider-specific public splits."
"Closing line, closing price i CLV."
prohibited_transitions:
"Nie obliczać EV bez p_cover/p_push/p_loss."
"Nie przypisywać no-chase statusu bez frozen frontier."
"Nie używać SIM_PREGAME_COM jako execution-grade quote."
"Nie przechodzić do AUDIT_COMPLETE."
"Nie wydawać rekomendacji PLAY/PASS."
"Nie obliczać CLV przed close."
decision_provenance:
framework: "Attached Variant B prompt"
process_quality_snapshot: "POINT_18_CURRENT_REPORT"
operator_policy_registry: "MISSING"
manual_override: "NONE_PROVIDED"
decision_basis: "Due hard blockers plus future simulated market quote"
reason_codes:
"GATE_HOLD"
"HOLD_PENDING_DATA"
"NO_BETTING_RECOMMENDATION"
"REASSESS_AFTER_REQUIRED_INPUTS"

summary:
hard_blockers:
- "Brak model lineage: version, run ID, generated_at, hash i calibration report."
- "Brak margin PMF oraz p_cover/p_push/p_loss."
- "Brak immutable model-generation quote i pełnej ścieżki rynku."
- "Brak frozen no-chase policy oraz acceptable quote frontier."
- "Brak realnego, wykonywalnego direct-book/provider-grade snapshotu."
- "Brak wewnętrznego frozen roster/staff baseline."
- "Brak internal matchup dependency report i game-script simulator output."
warnings:
- "DET -7.0 leży dokładnie na key number 7; push musi pozostać osobnym wynikiem."
- "Quote z 8 września 2026 jest przyszły względem badania z 28 lipca 2026."
- "SIM_PREGAME_COM jest PREVIEW_ONLY i nie identyfikuje realnego sportsbooku."
- "Detroit ma nowego OC oraz potwierdzony offseasonowy roster turnover."
- "Finalne rostery nie będą ustalone przed redukcją do 53 zawodników 30 sierpnia."
pending_not_due:
- "Practice Reports DET/NO: 9–11 września 2026."
- "Game Status Reports: 11 września 2026."
- "Game-day inactives."
- "Oficjalna prognoza NWS obejmująca okno meczu."
- "Public tickets/handle splits."
- "Closing line, closing price i CLV."
internal_inputs_required_from_me:
- "model_version, model_run_id, model_generated_at_utc, commit/input hash"
- "margin PMF, p_cover, p_push, p_loss"
- "calibration/uncertainty report"
- "model-generation quote snapshot"
- "no-chase policy version"
- "acceptable quote frontier"
- "eligible-books policy i house rules"
- "frozen roster/staff/role baseline"
- "feature contributions i matchup dependency report"
- "game-script simulator output"
- "process policy registry i operator routing policy"
data_to_capture_manually:
- "Atomiczny betslip: book, DET -spread, price, quote ID, timestamp, target stake i max stake."
- "Opener oraz każdą zmianę spreadu/ceny w append-only ledger."
- "Oficjalne injury reports i game statuses."
- "Finalne inactives."
- "NWS hourly forecast i venue operating notices."
- "Wspólny close snapshot dla spreadu i ceny."
next_best_action: "Najpierw dołączyć oryginalny model-run bundle wraz z PMF, prawdopodobieństwami, immutable model-generation quote i frozen acceptable quote frontier. Bez tych danych scenariusza DET -7/-109 nie można prawidłowo ocenić pod względem EV, ceny ani no-chase."

final_summary:
audit_readiness_now: "EARLY_RESEARCH_PARTIAL; HOLD_FOR_MODEL_VALIDATION_AND_MARKET_EVIDENCE"
due_hard_blockers:
- "MODEL_LINEAGE_MISSING"
- "PMF_AND_PROBABILITIES_MISSING"
- "MODEL_GENERATION_QUOTE_MISSING"
- "NO_CHASE_FRONTIER_MISSING"
- "EXECUTION_GRADE_QUOTE_MISSING"
- "INTERNAL_ROSTER_BASELINE_MISSING"
- "MATCHUP_AND_SIMULATOR_OUTPUT_MISSING"
not_due_items:
- "Official Week 1 injury reports."
- "Game Status Reports i inactives."
- "Game-window weather."
- "Public splits."
post_event_only_items:
- "Closing line."
- "Closing price."
- "CLV."
data_i_must_enter_manually:
- "Pełny model lineage i model-run timestamp."
- "PMF oraz p_cover/p_push/p_loss."
- "Model-generation quote."
- "No-chase policy i acceptable quote frontier."
- "Realny direct-book/provider-grade quote."
- "Frozen roster/staff baseline."
- "Matchup drivers i simulator output."
data_gpt_found_with_sources:
- "Data: 13 września 2026; kickoff: 13:00 EDT / 17:00 UTC."
- "Venue: Ford Field, Detroit; obiekt kryty, nawierzchnia FieldTurf Classic HD."
- "Oficjalne terminy raportów kontuzji oraz redukcji do 53 zawodników."
- "Aktualne oficjalne transakcje i sztaby DET/NO."
- "Zewnętrzny kontekst ratingowy nfelo oraz wtórnie raportowany ESPN FPI."
data_that_requires_internal_python:
- "Push-aware EV."
- "p_cover/p_push/p_loss z margin PMF."
- "Acceptable quote frontier."
- "No-chase gate."
- "Roster-adjusted rerun."
- "Matchup sensitivity i possession simulation."
- "Spread CLV oraz oddzielny price CLV po zamknięciu rynku."
next_step_for_me: "Odtworzyć nie z rynku, lecz z własnego append-only archiwum dokładny model-generation snapshot i połączyć go z model lineage, PMF oraz acceptable quote frontier. Następnie przeprowadzić ponowny audit punktów 1–2 i 6–14; game-week dane uzupełnić dopiero, gdy staną się należne."
safe_to_advance_to_next_audit_stage: false
advance_scope: "Nie jest bezpieczne przejście do etapu operator/decision. Można kontynuować wyłącznie zbieranie i porządkowanie danych."
