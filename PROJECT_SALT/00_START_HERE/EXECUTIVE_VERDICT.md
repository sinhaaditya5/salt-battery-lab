# Project Salt — Executive Verdict

**Date:** 2 Nov 2026 · **Stage:** pre-prototype. Nothing in this package is [MEASURED]. No cell exists.
**Basis:** 30-architecture feasibility engine (S12), founder-target tests (S13), PyBaMM DFN fast-charge and degradation runs (S13a), a salt-cell model (S14), DFT+U on the salt chemistries (S11; Apple M4 + EC2), and earlier EC2 DFT+U and aqueous work (S01–S10). The previous verdict on the aqueous track is in `DELIVERABLES/STARTUP_DECISION_MEMO.md`.
Every number carries a label from §16 of the brief and traces to `CLAIMS_LEDGER.csv`.

---

## Outcome: **B — no candidate meets the combined founder specification.**

This is not a near miss. Four of the founder targets conflict with each other, and with physics or economics, for any chemistry built from salt:

| Founder target [TARGET] | What the analysis found | Label |
|---|---|---|
| **360 Wh/kg at cell level** | No non-lithium architecture reaches 360 Wh/kg even at its optimistic P90. The best salt-derived cell is the anode-free Na solid-state design (N08): P50 259 Wh/kg, P90 292 Wh/kg. Only the lithium benchmarks get there: Si-anode 380, Li-metal SSB 372, Li-S 338. The build-up model reproduces seven benchmark cells within ±15 %. | [CALCULATED]; calibration vs [PUBLISHED]/[VENDOR CLAIM] |
| **~5-minute charge for 1,500 km** | A mid-size SUV with the founder's own 360 Wh/kg cell needs about 289 kWh usable and a 1.1 t battery. It must accept **3.8 MW for 5 min** (11.7C, 4.7 kA at 800 V). That is 2.9× the best charger deployed (1.3 MW claimed) and above the 3.75 MW MCS connector ceiling. A 40 t truck needs 29 MW. Heat to reject while charging is 184–735 kW. | [CALCULATED] |
| | In 5 minutes of CC-CV charging, a *validated* Li-ion cell model reaches only 8 % (1C), 29 % (4C) and about 31 % (10C) of capacity. It crosses the lithium-plating criterion after 28 s at 4C. | [SIMULATED] (Chen2020 DFN; Li benchmark, not a salt cell) |
| | For a liquid electrolyte, a 5-minute charge caps electrode loading at about 1.9 mAh/cm². Thinner electrodes cut Na-ion cell energy from 177 to 168 Wh/kg. | [CALCULATED] |
| | Salt-iron (molten-salt) cell: a 5-minute charge needs 0.8–4.3 V of overpotential. That drives the cell past the 3.05 V overcharge reaction. **Impossible.** | [SIMULATED] (S14, unvalidated) |
| **$3 manufacturing cost** | Six readings were tested (§1.1). As **$/kWh of cell, pack or conversion cost it is not physically plausible**. Every architecture's inactive parts alone (foils, separator, electrolyte, ceramic, case) cost more than $3/kWh. Cell cost floors are $41/kWh (LFP benchmark) to $152/kWh (ZEBRA). **$3/kg** of cells equals $15–23/kWh at 130–195 Wh/kg, which is also implausible. **$3 per unit** is plausible only for units of about 20–70 Wh. **$3 per kWh delivered over life** is met by every chemistry (LCOS $0.04–1.1/kWh), so as a target it is meaningless; **3 ¢/kWh delivered** is close for long-life LFP and NFPP only. | [CALCULATED] from [ASSUMPTION] prices |
| | What *is* below $3/kWh: the theoretical reactant cost of salt + iron ($0.26/kWh) and of Na–Cl₂ ($0.03/kWh). **The salt is almost free; the battery is not.** | [THEORETICAL]/[CALCULATED] |
| **Non-flammable, low toxicity, from salt** | Common salt is the active material only in the metal-chloride family (ZEBRA-type Na–NiCl₂ / Na–FeCl₂, assembled from NaCl + metal powder) and in Na–Cl₂. The metal chlorides are non-flammable but run at 190–350 °C. Na–Cl₂ uses thionyl chloride and Cl₂, both acutely toxic, so it fails the toxicity target. In Na-ion, salt is only the soda-ash feedstock. Its chloride leaves as CaCl₂ effluent (Solvay), and the cells still carry a flammable electrolyte. | [PUBLISHED]/[CALCULATED] |

## The closest feasible candidates (none is a winner)

| Goal it gets closest to | Candidate | Cell Wh/kg P50 [P10–P90] | Materials $/kWh P50 | Gap that remains |
|---|---|---|---|---|
| Energy (from salt-derived Na) | **N08** anode-free Na solid-state, layered oxide / sulfide-or-halide SE | 259 [228–292] | 285 | Cathode ceiling of about 550 Wh/kg-CAM (needs ≥750 for a 360 Wh/kg cell). A 5-min charge needs about 42 mA/cm² versus a critical current density of about 1–10 mA/cm². SE cost. TRL 3. |
| Salt as the active material + no organic solvent | **S03** salt-iron Na–FeCl₂ (10 % Ni), planar, 190 °C | 131 [111–149] | 191 | β''-alumina is about 85 % of materials cost. Only 200 cycles have been published for this cathode (PS-005). Self-heating losses. It cannot fast-charge. |
| Best balance under the founder's own weights | **N02** NFPP Na-ion / hard carbon (commercial) | 145 [138–152] | 56 | Flammable electrolyte. Commercial chemistry owned by CATL, BYD and others; **no defensible novelty for a start-up.** |

- **Pareto frontier** over (energy ↑, safety ↑, cost ↓) among non-lithium candidates: S02, S03, S04, N01, N02, N03, N08, A03 (Fe-air), A05 (Al-air, primary). [CALCULATED]
- **Ranking under founder-spec weights:** N02 > N01 > N03 > N04 > A01 (Zn-ion) > S01 (ZEBRA) > A03 > A02 > S03. The ranking changes with the weights; see `01_SCIENTIFIC_RESEARCH/chemistry_candidates.csv` for all three weight sets.
- The earlier aqueous track (N05/N06, 19–26 Wh/kg) is **dominated** in this landscape. It is never Pareto-optimal, and aqueous Zn-ion (A01) beats it under stationary weights.

## Is there a defensible invention?

**Not at the chemistry level.** Every architecture examined has close prior art:
- ZEBRA: Coetzer patents, now expired.
- Discharged-state Na–FeCl₂: Battelle US10615407B2.
- Na–Cl₂: Stanford WO2022067110 / US20230369594.
- Anode-free Na SSB: UCSD application filed.
- Na-ion cathodes: Faradion, Natron, CATL families.

See `01_SCIENTIFIC_RESEARCH/patent_landscape.csv`.

The one **testable engineering hypothesis** found (not yet a patentable invention) is a cost lever in the salt-iron cell. Ceramic mass per kWh scales with disc thickness ÷ areal capacity, so a **≤0.5 mm β''-alumina separator combined with a ≥75 mAh/cm² salt-iron cathode** brings the dominant cost item under 1 kg/kWh. That is about $60/kWh at $60/kg ceramic, or about $15/kWh at mass-production ceramic prices [CALCULATED]. Whether thick cathodes stay usable at 190 °C is unknown. The S-cell R0 package exists to test exactly that (gates G1–G5, `params/scell_params.py`).

**The factory model (S15) shows that even this lever is not enough on its own:**
- At 1 GWh/yr in India, the salt-iron cell costs about **$380/kWh** ($191 materials + $167 conversion).
- The comparison NFPP Na-ion line costs about **$83/kWh**; the lowest LFP cell price in 2025 was $36/kWh [PUBLISHED PS-017].
- If G4 passes (0.5 mm disc, 100 mAh/cm², ceramic at $15/kg), materials fall to **$31.5/kWh**. But molten-salt factory capex, anchored to Altech's ~€1,300 per kWh/yr [VENDOR CLAIM], still dominates.

**The exact breakthrough required for salt-iron to compete with LFP is all three together:**
1. β''-alumina at ≤ $15/kg in ≤ 0.5 mm, large-area form;
2. cathodes at ≥ 100 mAh/cm² that keep ≥ 3,000-cycle life;
3. a molten-salt cell line at ≤ ~$100 per kWh/yr of capacity (about 7× below the only published anchor).

[CALCULATED from ASSUMPTION]

## Recommendation

1. **Do not start a battery-manufacturing company on this specification.** Not investable on today's evidence: no prototype, no measured data, no novelty, and every founder target except "from salt" fails physically or economically.
2. **Re-state the specification before spending money.** A coherent salt product would be: 100–150 Wh/kg cell, 2–5 h charge, ≥3,000 cycles, non-flammable, for hot-climate stationary backup. That is the space FZSoNick has served for ~15 years and that Inlyte (US) and Altech/Fraunhofer (DE) are now entering [VENDOR CLAIM]. The market has not rewarded it strongly so far, which is itself evidence.
3. **If the founder still wants a salt battery, the cheapest decisive steps are, in order:**
   - (a) the 4-week buyer test from the earlier memo (K4). It applies whatever the chemistry.
   - (b) a 10–12-week partner-lab campaign on the S-cell R0: replicate PS-005, then test the thin-ceramic / thick-cathode lever. The full build package is in `06_PROCUREMENT`, `07_BUILD_MANUAL` and `04_MECHANICAL_CAD`.
     - **Budget:** about ₹12.5 lakh for materials and parts [ASSUMPTION]. Of that, ~₹4 lakh is β''-alumina discs and ~₹3.6 lakh is machined housings. Partner-lab instrument time is extra.
     - Every price in the BOM is "quote required".
   - **Kill the battery path** if K4 fails, or if G2/G4 fail at 60–100 mAh/cm².
4. **Mobility (EV, drone, aerospace)** is out of reach for any salt-derived chemistry on this evidence. The nearest research route is the anode-free Na solid-state cell, which belongs in a university group, not a start-up's first product.

## What is real in this package and what is not

| Real, reproducible ([SIMULATED]/[CALCULATED]) | Not done / not real |
|---|---|
| S11 DFT+U campaign on Na, NaCl, Cl₂, Fe/Co/Ni and their chlorides (QE 7.6, Apple M4 + EC2), with convergence, U-scan, FM/AFM order, band gaps and PDOS; voltages vs thermochemistry | No cell built; no electrochemical data; no supplier quotes; no customer interviews |
| S12 matrix, S13 targets, S13a PyBaMM, S14 salt-cell model | "BFT+U" could not be identified, so nothing was run under that name (`02_COMPUTATIONAL_CHEMISTRY/bft_u/README.md`) |
| S-cell R0 CAD (STEP/STL/GLB, exploded) + CADCraft drawing SB-SC-001 | Seal and gasket materials are candidates awaiting qualification tests QT-02…08 |
| SCM-1 KiCad project (ERC 0 violations), firmware core (19/19 host tests) | SCM-1 layout is a **draft**: 37 unrouted nets, 178 DRC clearance errors, **not for fabrication** |
| Procurement BOM with named suppliers | Catalogue numbers and prices are marked "verify / quote required" wherever they were not checked online |

## The one-line answer

A fundamentally better battery *made from salt* is possible only in the narrow sense of the salt-iron molten-salt cell: safer than lithium and cheap in active materials, but heavy, hot, slow to charge and ceramic-limited. The 360 Wh/kg, 5-minute, 1,500 km and $3 targets are not reachable by any salt-derived chemistry known today. The package is complete enough for a qualified lab to test the one open hypothesis, and to stop cleanly if it fails.
