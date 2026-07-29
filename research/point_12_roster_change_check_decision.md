# Point 12 Decision: roster_change_check

Status: accepted for Variant B.

## Core decision

`roster_change_check` asks whether the model is using a stale view of roster, roles, staff, or playcalling.

The most valuable source is not the current depth chart. The required stack is:

```text
frozen model roster/role/staff baseline
        +
official current roster and transaction chronology
        +
prior/current role evidence
        =
model-aware roster delta
```

Without the internal baseline, we can describe offseason roster movement, but we cannot answer whether the model is stale.

## Required model baseline

```yaml
model_baseline:
  model_run_id:
  model_version:
  generated_at_utc:
  roster_cutoff_utc:
  injury_cutoff_utc:
  baseline_roster_hash:
  baseline_role_hash:
  baseline_staff_hash:
  roster_source_snapshot_id:
  depth_chart_source_snapshot_id:
  snap_count_window:
```

If missing:

```yaml
risk_status: NOT_ASSESSABLE
reason_codes:
  - INTERNAL_ROSTER_BASELINE_MISSING
  - INTERNAL_ROLE_BASELINE_MISSING
```

## Change categories

```yaml
change_category:
  ROSTER_MEMBERSHIP_CHANGE:
    - free_agent_added
    - player_departed
    - trade
    - retirement
  ROSTER_STATUS_CHANGE:
    - active_to_ir
    - pup_to_active
    - practice_squad_to_active
  ROLE_CHANGE:
    - backup_to_starter
    - starter_to_rotation
    - outside_cb_to_nickel
    - returner_change
  STAFF_OR_SCHEME_CHANGE:
    - new_head_coach
    - new_coordinator
    - new_playcaller
    - new_ol_coach
```

Do not mix transaction events with projected role changes.

## Model awareness

Every change must say whether the model already knew it:

```yaml
model_awareness:
  status:
    - INCLUDED_IN_BASELINE
    - OCCURRED_AFTER_CUTOFF
    - MISSING_FROM_BASELINE
    - UNKNOWN
  baseline_cutoff_utc:
  transaction_effective_utc:
```

A player signed on March 15 is not a fresh roster risk if the model cutoff was May 1 and the baseline included him.

## Materiality

Materiality should be deterministic, not assigned by GPT from player name recognition.

```text
materiality =
    prior_role_weight
  * position_model_sensitivity
  * projected_role_change
  * evidence_confidence
```

Useful inputs:

```yaml
materiality_inputs:
  prior_season_snap_share:
  recent_snap_share:
  games_started:
  special_teams_snap_share:
  internal_player_value:
  position_group_sensitivity:
  replacement_quality:
  source_confidence:
```

GPT can summarize the evidence. Python/rule engine assigns severity.

## Source hierarchy

1. Internal roster, role, and staff baseline.
2. Official team rosters.
3. Team transactions and NFL Transaction Hub.
4. Snap counts and official gamebooks for prior role.
5. Official coaching announcements and playcaller evidence.
6. NFL Draft Tracker for rookie additions.
7. nflverse / nflreadpy for free automation.
8. Sportradar / SportsDataIO for paid automation.
9. PFF for role quality and snap-count context.
10. Ourlads for projected-role manual QA.
11. Over The Cap / Spotrac for contract/free-agency context.

## Statuses

```yaml
risk_status:
  - NO_MATERIAL_CHANGE
  - MINOR_CHANGE
  - REVIEW_REQUIRED
  - MAJOR_ROSTER_DISCONTINUITY
  - NOT_ASSESSABLE

workflow_status:
  - PENDING_BASELINE
  - PENDING_FINAL_53
  - PENDING_ROLE_RESOLUTION
  - MODEL_RERUN_REQUIRED
  - COMPLETE
```

## Week 1 rule

Before final cutdown, offseason rosters are not final Week 1 rosters.
Preseason depth charts often have:

```yaml
depth_chart_role_status: PRESEASON_UNRESOLVED
```

Do not label an expected starter as confirmed unless supported by official game-week depth chart, coach/team PR, gamebook, or actual usage.

## Current SF-LA status

As of July 24, 2026, current official rosters and transaction histories exist, but final 53-player rosters are not yet due.
The internal roster/role/staff baseline is not available in the current pick record.

Accepted status:

```yaml
roster_change_check:
  data_status: PARTIAL
  risk_status: NOT_ASSESSABLE
  workflow_status: PENDING_BASELINE_AND_FINAL_ROLE_RESEARCH
  current_snapshot:
    roster_phase: PRE_FINAL_CUTDOWN
    official_team_rosters_available: true
    official_transaction_history_available: true
    final_53_available: false
    role_resolution_status: PRESEASON_UNRESOLVED
  reason_codes:
    - INTERNAL_ROSTER_BASELINE_MISSING
    - INTERNAL_ROLE_BASELINE_MISSING
    - CURRENT_OFFICIAL_ROSTERS_AVAILABLE
    - OFFICIAL_TRANSACTION_HISTORY_AVAILABLE
    - FINAL_53_NOT_AVAILABLE
    - DEPTH_CHART_PRESEASON_UNRESOLVED
    - MATERIAL_ROSTER_DELTA_NOT_YET_COMPUTED
```

## Language rule

Allowed:

```text
Current official rosters are available, but material roster delta is not assessable against the model because baseline role hashes are missing.
```

Not allowed:

```text
No roster risk found.
Depth chart confirms starters.
The offseason tracker proves the model is up to date.
```
