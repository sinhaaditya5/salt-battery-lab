# S7: Cell, module and rack build-up
**Question:** What specific energy and energy density does R1 reach at cell-stack, 12 V block, 48 V tray and UPS-cabinet level? How does that compare with LFP, sodium-ion, VRLA and Aquion?
**Model:** `params/design.py`, a bottom-up geometry and mass model: electrode coatings, collectors, separators, electrolyte, case, hardware. Monte Carlo (600 samples) over 11 material assumptions.
**Results** (`out/s07_results.json`):
- Block: 17.6 Wh/kg (P10–P90: 13.7–22.1) [C-115]. Nominal 0.40 kWh [C-116], 32 Wh/L [C-117].
- UPS cabinet: 15.9 kWh [C-118].
**Comparators:**
- Aquion 18.6 Wh/kg module [CALC from VENDOR].
- VRLA ~40 Wh/kg [CALC].
- Sodium-ion 135–175 Wh/kg [VENDOR].
- LFP [ASSUMPTION ranges].
**Limits:** Concept geometry. No measured densities or porosities.
Run: `python run_s07.py`
