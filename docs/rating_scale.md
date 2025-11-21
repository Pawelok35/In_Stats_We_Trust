## ISWT Weather Rating Scale 2.0

Oparte na historii 2022–2025 (GOY/GOM/GOW) dla trzech silników:
- **V1 = variant_j** (precision) – waga 1.00 — ~13.5 ATS avg, 86% W/L.
- **V2 = variant_c_psdiff** (stability) – waga 0.91 — ~12.3 ATS avg, 86% W/L.
- **V3 = variant_k** (momentum) – waga 0.88 — ~11.8 ATS avg, 86% W/L.

Rating = Σ(tag_points × variant_weight), gdzie tag_points: GOY = 3, GOM = 2, GOW = 1.
Maksymalny rating ≈ 8.25.

| Rating Range | Stake | Codename             | Opis sygnału |
|--------------|-------|----------------------|--------------|
| ≥ 8.0        | 4.0 u | **Ultimate Supercell** | Pełna zgodność top sygnałów, ekstremalny edge (3×GOY + progi conf/edge). |
| 6.0–7.9      | 3.5 u | **Supercell**        | Silna zbieżność trzech wariantów, top pick tygodnia. |
| 4.8–5.9      | 2.5 u | **Cyclone**          | Stabilny front, solidne wsparcie modeli. |
| 3.2–4.7      | 2.0 u | **Gale**             | Mocny wiatr – warto grać przy sprzyjającej linii. |
| 2.9–3.1      | 1.5 u | **Breeze**           | Lekki sygnał testowy/eksperymentalny. |
| < 2.9        | 0–1.0 u | **Calm**           | Obserwacja, brak rekomendacji. |
