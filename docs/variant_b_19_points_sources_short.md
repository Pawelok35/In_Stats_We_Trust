# Variant B - 19 punktow i zrodla

## 1. argument_against

Zrodla:

- Immutable internal model-run artifact: run_id, model version, commit, input hash.
- Internal model output: fair margin, fair line, edge type, edge formula, tag.
- Internal model distribution: margin PMF, p_cover, p_push, p_loss.
- Internal calibration report: out-of-sample error, calibration, uncertainty.
- Internal model logs: home-field adjustment, neutral-site flag, feature attribution.
- Internal market snapshot at model generation: line, price, book, timestamp, quote id.
- Official schedule/venue source: neutral-site, international, home designation.
- Specific sportsbook house rules: push/OT/settlement rules for the captured quote.
- nflverse / nflreadpy for historical margin and calibration validation.

## 2. market_move_notes

Zrodla:

- Own append-only model-generation quote snapshot.
- Direct sportsbook / betslip confirmation for current executable quote.
- OpticOdds as best API automation candidate.
- Betstamp PRO, SpotOdds, Unabated as professional/manual odds screens.
- The Odds API as budget API with our own snapshots.
- SportsDataIO as historical warehouse candidate.
- Don Best as secondary validation.
- OddsPortal/Covers only as sanity check, not source of record.
- Documented consensus only if constituent books and timestamps are stored.

## 3. injury_role_notes

Zrodla:

- NFL official injury report.
- NFL official inactives.
- Official team injury reports for both teams.
- Official team transactions and roster designations.
- Official team PR / communications account.
- Official gamebooks / participation / snap counts.
- 32BeatWriters + original beat reporters only as role/workload context.
- RotoWire as all-in-one injury/depth/player-news aggregator.
- Footballguys Gameday Injury Expectations and SICScore as medical/workload context.
- Fantasy Life Utilization for snap share, routes, targets, carries and role transfer.
- Establish The Run for updated projections/workload context.
- Rotoworld / FantasyPros as alert/context, verify primary source.

## 4. schedule_spot_notes

Zrodla:

- NFL official schedule.
- NFL Football Operations / International Games.
- Official team schedules.
- Official venue/event page.
- nflreadpy / nflverse schedule.
- IANA Time Zone Database for timezone and UTC conversion.
- Audited venue registry with coordinates and timezone.
- GeographicLib for WGS84 geodesic distance.
- Official team travel/practice/acclimation info if available.
- Team PR, coach press conferences, official transcripts.
- Credentialed beat reporters, AP/Reuters only as itinerary confirmation/context.

## 5. weather_notes

Zrodla:

- Official weather service for the venue jurisdiction.
- Official venue operating notices.
- Licensed weather provider with issue timestamp and valid game-window timestamp.
- For Australia: Bureau of Meteorology.
- For USA: NOAA / National Weather Service API.
- BOM MetEye / BOM Weather for Australia official forecast.
- BOM ADFD for machine-readable Australia forecast.
- BOM observations, radar and warnings for nowcast/game-day validation.
- Venue/NFL/team PR for roof, surface and field operations.
- Meteomatics as paid secondary provider with provenance.
- Open-Meteo as budget secondary model-data provider.
- Internal model-run artifact for weather features and weather adjustment.

## 6. key_number_check

Zrodla:

- Own append-only quote event ledger.
- Internal market snapshot and model-generation quote path.
- Internal model margin PMF / affected probability mass.
- Internal rules: integer settlement and key-number significance config.
- Official house rules for settlement/push/overtime.
- OpticOdds / SportsDataIO for external quote path validation.
- nflverse / nflreadpy for historical key-number config validation.
- Unabated for manual visual QA.

## 7. no_chase_limit

Zrodla:

- Immutable model-generation quote.
- Versioned no-chase policy registry.
- Model margin PMF / p_cover / p_push / p_loss.
- Acceptable quote frontier generated at model run.
- Direct sportsbook / betslip confirmation at target stake.
- Eligible-books policy.
- Official house rules for settlement/push/overtime.
- OpticOdds for main and alternate quote discovery.
- SportsDataIO for history/backfill/validation.
- Betstamp PRO / Unabated for manual QA.

## 8. price_quality

Zrodla:

- Internal model-run artifact and margin PMF.
- p_cover, p_push, p_loss for exact spread.
- Frozen acceptable_quote_frontier generated at model run.
- Direct sportsbook / betslip confirmation at target stake.
- Official house rules for push/overtime/settlement.
- OpticOdds for quote discovery, alternates, timestamps, locked market status.
- SportsDataIO as second feed and historical/backfill validation.
- Betstamp PRO / Unabated for manual line-price QA.
- The Odds API as budget quote snapshot source.

## 9. market_snapshot

Zrodla:

- Accepted ticket / digital receipt for EXECUTED_GRADE.
- Direct sportsbook betslip checked at target stake for DIRECT_BOOK_GRADE.
- OpticOdds for atomic named-book provider quote.
- SportsDataIO as second feed, history, backfill, market-scope validation.
- The Odds API as budget current snapshot.
- Betstamp PRO / Unabated for manual odds-screen QA.
- Internal append-only raw payload / hash / timestamp store.
- Manual consensus only for PREVIEW_ONLY, never market-grade proof.

## 10. public_bias / tickets_handle

Zrodla:

- DraftKings direct betting splits: named single-book real wagers.
- VSiN Pro: separate DraftKings and Circa samples.
- Sports Insights: real wagers, multi-book pool, per-book breakdown if available.
- Action Network: broad multi-book sample, underlying pool undisclosed.
- Official book publications such as BetMGM/FanDuel/Caesars when market-specific.
- ScoresAndOdds as secondary cross-check.
- Covers Consensus only as community sentiment, not sportsbook tickets/handle.

## 11. power_rankings_check

Zrodla:

- Internal neutral-field PowerScore / internal_neutral_power_gap.
- ESPN FPI for direct point comparison.
- PFF Point Spread Team Ratings for direct neutral-field point comparison.
- FTN projected DVOA / DAVE for efficiency direction and tier.
- nfelo for transparent market-informed Elo direction / translated gap if available.
- Internal leave-one-game-out market-implied neutral rating.
- SumerSports EPA / success rate as prior-season component context.
- NFL.com / The Athletic / ESPN editorial only as narrative context.

## 12. roster_change_check

Zrodla:

- Internal model roster baseline, role baseline, staff baseline, and cutoff timestamp.
- Official team roster pages.
- Official team transactions.
- NFL official transactions.
- Official coaching announcements / staff pages.
- NFL Draft Tracker for rookie additions.
- Official gamebooks, starters, inactives.
- nflverse / nflreadpy rosters, status, snap counts, player IDs.
- Sportradar or SportsDataIO for paid roster/depth/transaction automation.
- PFF for role quality and snap-count context.
- Ourlads for projected-role manual QA.
- Over The Cap / Spotrac for contract and free-agency context.

## 13. matchup_specific_risk

Zrodla:

- Internal matchup dependency report and model edge-driver map.
- Internal feature contribution and model sensitivity to matchup conflict.
- nflverse / nflreadpy for reproducible EPA, success, pace, xpass, and split queries.
- Official injuries, inactives, rosters, roles, gamebooks from points 3 and 12.
- ESPN Analytics win rates for trench matchups.
- Next Gen Stats / NFL Pro / All-22 for tracking, separation, time to throw, route/coverage context.
- PFF Premium Stats for player-level blocking, pressure, coverage, and matchup charts.
- FTN DVOA/DAVE, adjusted line yards, defense vs receivers, special teams.
- SumerSports for public EPA, success, and personnel tendencies.
- SIS / TruMedia for professional charting and filtered matchup queries.

## 14. game_script_risk

Zrodla:

- Internal stateful play-by-play or possession-level simulator.
- Internal margin PMF and p_cover, p_push, p_loss.
- Frozen scenario policy and scenario definition hash.
- nflverse / nflreadpy / nflfastR for play-by-play, EP/WP, xpass, score-state behavior.
- Next Gen Stats / NFL Pro for tracking and player-level script response context.
- Sports Info Solutions or TruMedia for pace, expected pass rate, on/off, probability tools.
- SumerSports for public EPA, success, personnel, pass-rate priors.
- Current roster, injury, weather, market snapshot, and price-quality inputs.

## 15. closing_line

Zrodla:

- Internal append-only quote ledger.
- Direct sportsbook close capture near market close.
- OpticOdds full quote history with active/locked/removed events.
- SportsDataIO provider-declared close and line movement.
- The Odds API interval snapshot fallback / budget backfill.
- Betstamp PRO / Unabated for manual same-book and best-market QA.
- Manual screenshot only as fallback evidence.

## 16. closing_price

Zrodla:

- Same close_snapshot_id as point 15.
- Internal append-only quote ledger.
- Direct sportsbook close capture / betslip near close.
- OpticOdds full quote history including alternates.
- SportsDataIO provider-declared close with spread and payout fields.
- The Odds API interval snapshot fallback.
- Betstamp / Unabated for manual same-book, best-market, and alternate-line QA.
- Full closing ladder and both sides of the market when available.

## 17. clv_points

Zrodla:

- Point 9 atomic decision snapshot.
- Point 15/16 shared atomic close snapshot.
- Internal append-only quote ledger.
- Full closing ladder and both sides of the market when available.
- Point 6 key-number context.
- Internal selected-team spread convention.
- Python rule engine calculation.
- Frozen CLV benchmark, devig, and pricing policy.

## 18. process_quality

Zrodla:

- Internal immutable audit bundle with outputs from points 1-17.
- Internal process policy registry.
- Internal event clock / due-window engine.
- Internal evidence manifest.
- Internal calculation manifest.
- Internal model lineage.
- Internal manual override log.
- Python/rule engine.

## 19. final_operator_decision

Zrodla:

- Frozen process_quality snapshot from point 18.
- Internal operator decision policy.
- Internal audit phase state.
- Internal blocker classification registry.
- Internal action routing registry.
- Internal manual override log.
- Append-only operator decision ledger.
- Python/rule engine.
