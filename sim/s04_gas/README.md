# S4: Water window, gas, water loss and vent requirement
**Question:** How much gas and water loss do side reactions cause in a sealed R1 block, and what does that imply for vent design, ventilation and life?
**Model:**
- Nernst lines for HER/OER versus pH.
- Two side-reaction estimates:
  - (a) a coulombic-efficiency budget (CE 99.0–99.9%, assumed);
  - (b) Tafel kinetics, calibrated to (a), then used for float current and pH sensitivity.
- Gas into the headspace (isothermal) gives pressure rise per cycle.
- Overcharge fault case.
- Cabinet ventilation needed to keep H₂ ≤ 1% (25% LFL).
**Inputs:** `params` GAS, MAT, MONOBLOC.
**Key results** (`out/s04_results.json`):
- CE ≥ 99.88% is needed to reach 3,000 cycles before 20% water loss [C-107]. At 99.5% it's ~700 cycles [C-108].
- The NTP anode sits ~0.2 V below the H₂ line at pH 7 [C-109].
- The Tafel extrapolation predicts float water loss far above a 10-year budget. Treat this as a qualitative warning, not a number.
**Validation:** none. All inputs are assumptions.
**Limits:**
- No O₂/H₂ recombination.
- No local pH dynamics.
- Single-temperature model.
Run: `python run_s04.py`
