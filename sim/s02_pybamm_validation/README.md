# S2 — Validation of the electrochemical model (PyBaMM sodium-ion DFN)

**Question.** Before trusting any PyBaMM model of an aqueous cell, does PyBaMM's sodium-ion DFN
(`pybamm.sodium_ion.BasicDFN` + `ParameterValues("Chayambuka2022")`, PyBaMM 26.10) reproduce
published sodium-ion discharge curves?

**Reference data.** Experimental symbols in Fig. 4a of Chayambuka et al., *Electrochim. Acta* 404,
139764 (2022), HC//NVPF coin cell at 1, 5, 10, 12 A m⁻² (0.1–1.4 C). The PDF came from the
UTS open repository (`research/papers/`). The raster figure was digitised by colour segmentation
(`ref/`, overlay check in `out/digitise_check.png`). Digitising error is about ±0.01 mAh and ±10 mV.
The paper's own model errors (Table 1) are 19.9 / 34.6 / 32.2 / 48.1 mV.

**Acceptance criteria (fixed before running).** Mean absolute voltage error ≤ 60 mV and end-of-discharge
capacity within 5% at every rate.

**Results** (`out/s02_validation.json`, chart `out/s02_validation_discharge.png`):

| Variant | MAE per rate (mV) | Capacity | Verdict |
|---|---|---|---|
| A: parameters as shipped | 74 / 121 / 80 / 67 | within 5% | **FAIL** (independent validation) |
| B: A + the paper's contact resistance | 83 / 173 / 182 / 189 | – | FAIL |
| C: exchange-current units restored to the paper's Eq. 6 (×√1000) + contact R | 66 / 74 / 119 / 113 | within 5% | FAIL |
| D: one-parameter kinetic calibration (k ×2) | 42–55 at all rates | within 5% | PASS, but **calibration, not validation** |

**Finding.** The shipped `Chayambuka2022` exchange-current function normalises c_e by c_e0 but keeps k
values whose paper units are m^2.5 mol^-1.5 s^-1 with c_e not normalised. Fixing the units corrects the upper
plateau but overshoots the lower one. The shipped k(c) tables probably differ from the paper's final
optimised curves. This is noted here only; nothing was reported upstream.

**What this means for S3.** The DFN framework is fine for capacity versus rate and loading trends (±5%).
Absolute voltages from any model whose kinetics are not measured carry at least ±0.1 V uncertainty. For the
aqueous R1 cell, the kinetic and transport parameters are literature ranges, so S3 results are
**[SIM], not validated**. They become validated only after GITT/EIS on real electrodes.

**Limits.** Isothermal; single-particle-size DFN; digitised data; non-aqueous chemistry (validates the
framework and solver, not aqueous physics).

Run: `python run_s02.py` (about 1 minute).
