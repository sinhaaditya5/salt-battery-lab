# Electrochemical models: what each one represents (and does not)

| Folder | Model | Chemistry it actually represents | Validation status |
|---|---|---|---|
| `cell_models/scell_model.py` (S14) | 0-D ohmic + reaction-front model | Na \| β''-alumina \| NaAlCl₄ \| Fe/Ni-NaCl (the S-cell) | **Unvalidated**; ohmic-only upper bound |
| `cell_models/s03_aqueous_r1_results.json` | PyBaMM Na-ion DFN (Chayambuka params) | aqueous R1 (earlier track), trends only | failed S02 gate |
| `fast_charging/` (S13a) | PyBaMM DFN Chen2020 + OKane2022 | **Li-ion NMC811 / graphite benchmark** (physics of fast charging) | parameter set validated by its authors; not a salt cell |
| `fast_charging/` (Na trend) | PyBaMM Na-ion BasicDFN Chayambuka2022 | HC \| NVPF Na-ion | failed our S02 validation → trend only |
| `gas_generation/s04_aqueous_gas` | water-loss vs CE model | aqueous track | analytic |
| `thermal_models/s08_aqueous_thermal` | lumped thermal | aqueous monobloc | analytic |
| `validation_data/s02_na_dfn_validation` | digitised published curves vs PyBaMM | Na-ion DFN | documented FAIL |

**No lithium-ion model is labelled as validated for a sodium or salt cell anywhere in this package.**
