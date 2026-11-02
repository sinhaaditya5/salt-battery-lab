# S3: R1 cell electrochemical model
**Question:** For the R1 cell (Na-birnessite // NaTi₂(PO₄)₃-C, 0.5 M Na₂SO₄), how do rate capability, voltage curves and round-trip efficiency vary with electrode loading from 2.8 to 80 mg/cm²?
**Model:** PyBaMM 26.10 `sodium_ion.BasicDFN`, using the Chayambuka2022 template with R1 values (`r1_parameters.py`).
- OCP curves are assumed shapes: a sloping birnessite curve and a flat NTP plateau. They are not measured.
- Transport and kinetic inputs are literature ranges (`RANGES`).
**Inputs:** `params/product_params.py` (MAT, R1_LOADING) and `params/design.py` (electrode thickness from loading).
**Monte Carlo:** 40 samples per loading. Sampled: diffusivity, particle size, exchange current, conductivity, salt diffusivity, transference, capacity, porosity.
**Validation:** none for this chemistry. S2 shows the framework is off by 67–121 mV without measured kinetics. Results are [SIM] trends, and voltages carry ≥ ±0.1 V.
**Key results** (`out/s03_results.json`):
- 4C retention at 40 mg/cm²: P50 86% (P10–P90: 54–94%) [C-104]. At 60 mg/cm²: 39% [C-105].
- Round-trip efficiency (electrochemical only): 99 / 96 / 81% at C/5 / 1C / 4C [C-106].
**Limits:**
- Na₂SO₄ is a 2:1 salt modelled with the DFN's 1:1 electrolyte.
- Isothermal. No side reactions (see S4). No ageing.
Run: `python run_s03.py` (~4 min, 5 processes)
