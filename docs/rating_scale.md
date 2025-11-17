## ISWT Weather Rating Scale

| Rating Range | Stake | Codename  | Opis sygnału |
|--------------|-------|-----------|--------------|
| (specjalne)  | 4.0 u | **Ultimate Supercell** | Wszystkie warianty = GOY + `confidence ≥ 98` + `edge_vs_line ≥ 27` dla każdego modelu. Historycznie 100% skuteczności (2022–2025). |
| ≥ 6.0        | 3.5 u | **Supercell** | Ekstremalna burza – pełna zgodność modeli, top pick tygodnia. |
| 5.0–5.9      | 3.0 u | **Vortex**    | Silny wir – minimalny dryf, nadal bardzo wysoki edge. |
| 4.0–4.9      | 2.5 u | **Cyclone**   | Poważny front – stabilne wsparcie, solidna ofensywa. |
| 3.0–3.9      | 2.0 u | **Gale**      | Mocny wiatr – warto grać, zwłaszcza gdy linia sprzyja. |
| 2.0–2.9      | 1.5 u | **Breeze**    | Lekki powiew – sygnał testowy lub eksperymentalny. |
| < 2.0        | 1.0 u | **Calm**      | Cisza – tylko obserwacja, brak rekomendacji gry. |
| Tylko M      | 0.5 u | **Base**      | Samotny sygnał M (bez D/B) – czysto trackingowy wpis. |

Rating = Σ(tag_points × model_weight), gdzie:
- Tag points: Crown/GOY = 3, Prime/GOM = 2, Core/GOW = 1.
- Wagi modeli: M = 1.0, D = 0.7, B = 0.4.
