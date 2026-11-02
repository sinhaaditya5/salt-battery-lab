# Validation test plan (protocols only: **no measurements exist**)

**Units.** C-rates refer to design capacity. All tests at 190 °C unless stated. At least n = 3 cells per condition.

## 1. Qualification tests (components)

| ID | Test | Protocol | Pass |
|---|---|---|---|
| QT-01 | β''-alumina conductivity | 2-probe EIS with sputtered Au or molten NaNO₃ electrodes, 150–350 °C | σ(300 °C) ≥ 0.1 S/cm; Arrhenius Eₐ reported |
| QT-02 | Hermeticity | He leak | < 1e-8 mbar·L/s |
| QT-03 | Seal thermal cycling | 20 × (25 ↔ 190 °C, 2 °C/min) + QT-02 | pass on 4/4 |
| QT-04 | Cathode-side material compatibility | coupons (graphite foil, Ni 201, Mo, glass) in NaAlCl₄ + NaCl at 260 °C for 500 h, Ar | mass change < 0.5 %; no Fe/Ni/C in melt by ICP above 100 ppm |
| QT-05 | Ni housing chloridisation | cell held at 2.75 V for 100 h; post-mortem section | < 10 µm attack |
| QT-06 | Granule moisture | Karl Fischer | < 100 ppm |
| QT-07 | Anode-side compatibility | coupons in molten Na at 260 °C for 500 h | no wetting failure; mass change < 0.5 % |
| QT-08 | Insulation hot | 500 V at 260 °C | > 10 MΩ |

## 2. Electrochemical gates (G1–G5, `params/scell_params.py`)

- **G1 replication:** capacity at 5, 10, 20 and 33.3 mA/cm².
- **G2 loading:** 30/60/100 mAh/cm² at 10 mA/cm²; utilisation; ASR vs DoD (EIS every 10 % DoD).
- **G3 Coulombic efficiency:** 100 cycles at 10 mA/cm², 1.80–2.75 V; mean CE over cycles 10–100. High-precision coulometry is needed (cycler accuracy ≤ 0.02 % of FS) — **check the partner cycler spec**.
- **G4 cost lever:** repeat G2 with the 0.5 mm disc.
- **G5:** QT-03.

## 3. Cycle life and calendar
After G1–G3 pass: 1,000 cycles at C/5 (n = 3); calendar storage charged at 190 °C for 3 months, with capacity check monthly.

## 4. Fast charging (to document the limit, not to pass)
Charge at 0.5, 1, 2 and 4C until 2.75 V or the over-potential exceeds 0.4 V; then 50 cycles at the highest rate that passes, versus C/5 controls. The S14 model predicts a ceiling of about 1–6C on ohmic grounds and impossibility at 12C.

## 5. Abuse testing (partner with an accredited lab; not in the R0 budget)
Overcharge to 3.3 V (expect the AlCl₃ reaction); external short at temperature; deliberate ceramic fracture (pre-notched disc) in a sealed vessel with gas and temperature logging; external heating to 400 °C. Run these only at a facility equipped for Na/HCl incidents.

## 6. What does not exist
No raw measurements, no cycle-life data, no abuse data, no independent reports.
The folders `09_VALIDATION/raw_measurements`, `independent_reports`, `cycle_life`, `fast_charging` and `abuse_testing` were deliberately **not** created: empty folders would misrepresent the evidence.
