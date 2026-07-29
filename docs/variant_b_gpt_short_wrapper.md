# Variant B - krotka wiadomosc do GPT przy zalaczonym pliku

## Wersja uniwersalna

```text
Uzyj zalaczonego pliku jako glownej instrukcji dla frameworka Variant B. Nie dawaj picka ani rekomendacji bettingowej. Przygotuj structured research dla 19 punktow audytu, oznaczajac braki jako MISSING, NOT_ASSESSABLE, PENDING_NOT_DUE albo POST_EVENT_ONLY.

Mecz do analizy:
- Season:
- Week:
- Date:
- Away:
- Home:
- Venue:
- Market:
- Selected team:
- Current spread:
- Current price:
- Book/source:

Zwroc wynik w strukturze z pliku: audit_metadata, points 1-19 oraz final_summary.
```

## Przyklad: Seahawks vs Patriots

```text
Uzyj zalaczonego pliku jako glownej instrukcji dla frameworka Variant B. Nie dawaj picka ani rekomendacji bettingowej. Przygotuj structured research dla 19 punktow audytu, oznaczajac braki jako MISSING, NOT_ASSESSABLE, PENDING_NOT_DUE albo POST_EVENT_ONLY.

Mecz do analizy:
- Season: 2026
- Week: 1
- Date: 2026-09-09
- Away: Seattle Seahawks
- Home: New England Patriots
- Venue: znajdz oficjalne venue i potwierdz zrodlem
- Market: full-game spread
- Selected team: wpisze pozniej albo UNKNOWN
- Current spread: wpisze pozniej albo UNKNOWN
- Current price: wpisze pozniej albo UNKNOWN
- Book/source: wpisze pozniej albo UNKNOWN

Zwroc wynik w strukturze z pliku: audit_metadata, points 1-19 oraz final_summary.
```

## Wersja gdy masz juz linie/model

```text
Uzyj zalaczonego pliku jako glownej instrukcji dla frameworka Variant B. Nie dawaj picka ani rekomendacji bettingowej. Przygotuj structured research dla 19 punktow audytu, oznaczajac braki jako MISSING, NOT_ASSESSABLE, PENDING_NOT_DUE albo POST_EVENT_ONLY.

Mecz do analizy:
- Season: 2026
- Week: 1
- Date: 2026-09-09
- Away: Seattle Seahawks
- Home: New England Patriots
- Venue: znajdz oficjalne venue i potwierdz zrodlem
- Market: full-game spread
- Selected team: [TEAM]
- Current spread selected team: [SPREAD]
- Current price: [PRICE]
- Book/source: [BOOK_OR_SOURCE]
- Quote timestamp UTC: [TIMESTAMP_OR_UNKNOWN]
- Model fair margin selected team raw: [MODEL_MARGIN_OR_UNKNOWN]
- Model fair margin rounded to 0.5: [ROUNDED_OR_UNKNOWN]
- Edge vs line raw: [EDGE_OR_UNKNOWN]
- Model tag: [VALUE PLAY/GOW/GOM/GOY/UNKNOWN]

Zwroc wynik w strukturze z pliku: audit_metadata, points 1-19 oraz final_summary.
```
