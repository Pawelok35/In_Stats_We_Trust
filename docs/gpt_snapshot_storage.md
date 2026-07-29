# GPT Snapshot Storage

Tu zapisujemy odpowiedzi GPT uzywane przez Variant B.

## Struktura

```text
research/gpt_snapshots/{season}/week_{week:02d}/{game_id}/
```

Przyklad dla SF at LA:

```text
research/gpt_snapshots/2026/week_01/2026_w01_SF_at_LA/
```

## Pelne 19 Punktow

Pelny raport GPT wklejamy do:

```text
research/gpt_snapshots/2026/week_01/2026_w01_SF_at_LA/full_19_points.md
```

## Delta Refresh

Kolejne aktualizacje GPT wklejamy jako osobne pliki:

```text
research/gpt_snapshots/2026/week_01/2026_w01_SF_at_LA/delta_2026-09-09_wednesday.md
research/gpt_snapshots/2026/week_01/2026_w01_SF_at_LA/delta_2026-09-10_thursday.md
research/gpt_snapshots/2026/week_01/2026_w01_SF_at_LA/delta_2026-09-13_sunday.md
```

Nie nadpisujemy starego delta refresh. Kazdy dzien ma osobny plik.

## Minimalny Szablon

```markdown
# GPT Snapshot

season:
week:
game:
snapshot_type: full_19_points / delta_refresh
created_at_local:
source_thread:

## Input Sent To GPT

Wklej prompt albo krotki opis promptu.

## GPT Output

Wklej pelna odpowiedz GPT.

## Codex Notes

Tu Codex moze dopisac, co zostalo przeniesione do Variant B.
```

## Jak Bot To Sprawdza

Pelne GPT 19 punktow:

```text
research/gpt_snapshots/{season}/week_{week:02d}/**/full_19_points.md
```

Delta refresh:

```text
research/gpt_snapshots/{season}/week_{week:02d}/**/delta_*.md
```
