# R0 build cards — operator sequence

**Audience:** trained battery/materials laboratory personnel working under a PI-approved SOP and site EHS approval. These are controlled work cards, not instructions for a home, classroom or child-operated experiment.

Each card is a gate. Do not skip ahead when a card fails.

---

## CARD 0 — qualify the lab (BLOCKER)

**Input:** source paper, SDS/COA package, lab risk assessment, equipment list.

**Required stations:** chemical hood; calibrated balance; stirred glass reactor; metering pump/syringe; chemical-compatible centrifuge; DI-water supply; vacuum oven; tube furnace with exhaust; XRD; ICP-OES/MS; TGA; three-electrode potentiostat; EIS/battery cycler; approved cell fixture; waste route.

**Actions:**
1. Name the principal investigator and trained operator.
2. Approve chemical handling, manganese waste, alkaline waste, solvent storage and furnace work.
3. Confirm calibrations and equipment operating limits.
4. Obtain written fixture suitability and pressure/gas guidance from the fixture provider / lab engineer.
5. Open a batch record and deviation log.

**Pass:** signed EHS/PI approval, trained operator, current SDS/COA, calibrated equipment and waste route.

**Stop:** any missing control. No chemical purchase or synthesis until this card passes.

---

## CARD 1 — make the Mn3O4 precursor (literature-reported material step)

**Purpose:** prepare the manganese-oxide precursor used by the 2019 source paper.

**Published inputs per independent batch:**

| Part | Source-reported quantity |
|---|---:|
| MnCl2·4H2O | 0.700 g; 99% metals basis in paper |
| DI water | 140 mL; 18.2 MΩ·cm |
| NaOH solution | 0.123 g/mL |
| NaOH solution metering | 0.167 mL/min for 50 min = 8.35 mL |
| Additional reaction time | 30 min after addition |
| Vessel | 500 mL flask |
| Mixing | vigorous stirring at room temperature |

**Equipment:** approved hood, 500 mL flask, stirrer, calibrated syringe pump, centrifuge and compatible tubes, vacuum drying system.

**Operator sequence:**
1. Verify reagent identity, grade, lot, COA and SDS against the source specification.
2. Create a unique batch ID; tare and record all receiving vessels.
3. Dissolve the source-specified MnCl2·4H2O input in the stated DI-water volume under the approved SOP.
4. Meter the source-specified NaOH solution at the reported rate/time while maintaining the approved mixing and containment conditions.
5. Continue the reported post-addition reaction period.
6. Separate the precipitate by centrifugation using the lab-approved rotor, RCF and tube limits. The paper does not specify centrifuge RCF/time; record the lab-selected value as a deviation.
7. Wash sequentially with DI water and ethanol using the approved lab SOP. The paper does not give wash volumes/endpoints; record them.
8. Vacuum-dry using the lab-approved temperature/time; the paper states vacuum drying but does not supply all settings in the main Methods.
9. Weigh recovered powder and calculate actual yield. Do not assume theoretical yield.
10. Retain a labelled sample for phase/composition analysis.

**Calculated planning values:** 8.35 mL NaOH solution contains approximately 1.027 g NaOH. A 0.700 g MnCl2·4H2O input has a theoretical Mn3O4 upper bound of about 0.270 g by manganese mass balance. This is not an actual yield or process guarantee.

**Pass:** powder yield recorded; batch traceability complete; XRD / composition screening consistent with Mn3O4 reference and lab acceptance criteria.

**Stop:** unknown phase, cross-contamination, unrecorded process deviation, spill/exposure or missing waste disposition.

---

## CARD 2 — sodium-insert the precursor to make reference birnessite

**Purpose:** reproduce the sodium-rich manganese oxide material described in the paper.

**Published parameters:**

| Part | Source-reported quantity / condition |
|---|---:|
| Mn3O4 | 100 mg per insertion batch |
| NaOH:Mn3O4 molar ratios studied | 0.5, 1, 1.5, 2 and 4 |
| Ratio associated with Na/Mn ≈ 0.27 | 4:1 |
| Furnace | tube furnace, open air |
| Temperature | 270 °C |
| Hold | 6 h |
| Post-treatment | thoroughly wash with DI water; vacuum dry overnight |

**For the 4:1 target batch:** 100 mg Mn3O4 requires approximately 69.9 mg NaOH by formula-mass calculation. It is a calculated reagent amount, not an experimentally measured yield.

**Operator sequence:**
1. Use a released Mn3O4 batch from Card 1.
2. Record exact Mn3O4 and NaOH masses, reagent lot IDs and balance IDs.
3. Homogenise according to the paper's mortar/pestle mixing description under the lab-approved contamination and exposure controls.
4. Load an approved compatible crucible and record its ID and tare mass.
5. Run the source-reported 270 °C / 6 h / open-air heat treatment using an approved furnace program and local exhaust.
6. Cool under the lab's approved handling procedure.
7. Wash thoroughly with DI water to remove residual NaOH; record wash conditions and endpoint.
8. Vacuum-dry overnight using a documented local SOP.
9. Weigh product and retain representative aliquots.
10. Do not label the powder Na0.27MnO2·0.63H2O until the composition and hydration are measured.

**Pass:** XRD phase assessment, ICP-OES/MS Na:Mn ratio and TGA hydration measurement support the intended product within predefined laboratory tolerances.

**Stop:** residual caustic, unverified phase, Na/Mn not at target, material loss/contamination outside approved limits, furnace event.

---

## CARD 3 — qualify the active powder (BLOCKER before any cell)

**Required analyses:**

- XRD: phase identity, secondary phases, repeatability among three independently prepared batches.
- ICP-OES or ICP-MS: Na:Mn elemental ratio; report method, calibration and uncertainty.
- TGA: hydration / mass-loss profile; distinguish measured value from the source's nominal 0.63 H2O.
- SEM: morphology and batch variation (recommended).
- Optional XPS: Mn oxidation-state assessment, if facility has validated method.

**Pass:** three powder batches meet pre-agreed composition and phase criteria; actual mass yield and all failed batches disclosed.

**Stop:** no electrode preparation if identity and composition are unknown.

---

## CARD 4 — develop the full-cell electrode process (R0-D; not exact replication)

**Source-reported full-cell target per electrode:** approximately 5.00 mg active powder + 1.25 mg carbon black (4:1 mass ratio) on 15 mm E-TEK/Toray carbon paper; weigh after vacuum drying overnight.

**Important missing data:** the main article does not specify the full-cell slurry solvent, solids concentration, dispersion energy/time, binder (if any), carbon-paper grade/thickness/treatment, or the full fixture dimensions. Do not call a locally selected formulation an exact paper reproduction.

**Method-development actions:**
1. Obtain the authors' clarification if possible.
2. Obtain carbon-paper datasheet and separator datasheet.
3. Design a controlled, small coupon screening plan with the PI. Change one factor at a time or use a documented DOE.
4. Record solvent identity, solids fraction, mixing sequence/energy/time, optional binder identity and mass, coating method, drying history and actual dry mass.
5. Measure coating adhesion, mass uniformity, sheet resistance, electrolyte wetting and material loss.
6. Select a formulation only against written acceptance criteria.
7. Mark every resulting electrode and cell as R0-D with the deviation ID.

**Pass:** reproducible loading, adhesion and resistance across at least three independent electrodes, accepted by the lab.

**Stop:** delamination, cracking, excessive material loss, unknown solvent/binder, unapproved exposure or electrical short.

---

## CARD 5 — map the electrochemical window (open-cell / three-electrode research only)

**Published half-cell reference details:** a three-electrode setup with glassy-carbon working electrode, Pt-wire counter and Ag/AgCl reference; 0.1 M Na2SO4 electrolyte for CV. The paper describes a 7 mg active + 3 mg carbon mixture dispersed in DI water to 0.5 mg/mL for its half-cell ink, and a 10 µL drop-cast amount on a 0.5 cm glassy-carbon disc. This is a half-cell recipe only; it is not the missing full-cell slurry recipe.

**Required operator sequence:**
1. Calibrate/check the reference electrode using facility protocol.
2. Record electrolyte concentration, pH, conductivity and temperature.
3. Use PI/EHS-approved initial potential/current limits; do not assume the paper's broad potential span is safe for local cells.
4. Record CV, galvanostatic response, impedance and visual/gas observations as approved.
5. Expand the window only through a pre-approved stepwise test plan with stop conditions.
6. Log gas analysis or a justified gas-monitoring method when potential range may drive water reactions.

**Pass:** repeatable reversible response and a defensible operating window supported by measurements and safety review.

**Stop:** unanticipated gas, heating, pressure, pH excursion, unstable reference, current runaway or leakage.

---

## CARD 6 — build the symmetric reference cell (blocked until Cards 0–5 pass)

**Source-reported stack:**

1. 15 mm carbon-paper electrode with about 5 mg active + 1.25 mg carbon black.
2. Cellulose-based Whatman filter-paper separator.
3. Second symmetric 15 mm electrode with same nominal loading.
4. 150 µL of 1 M aqueous Na2SO4 electrolyte.
5. Stainless contact plates and compression spring.
6. MTI EQ-STC split button-cell fixture.

**Before assembly:** obtain the actual current fixture drawing, component part numbers, manufacturer limits, separator grade and thickness, compression method, and written confirmation that the fixture is appropriate for the aqueous test and its possible gas evolution. The original article does not supply all these values.

**Do not:** fabricate a pressure-bearing cell from the visual STL/SCAD, substitute table salt for sodium sulfate, assume the 2.5 V literature window is a safe setting, or test a sealed cell without gas/pressure controls.

**Pass:** at least three independently assembled replicate cells; complete mass and assembly record; no leak/short; approved test plan; raw instrument data preserved.

---

## CARD 7 — report measured outcomes

For every cell report:

- powder batch and electrode IDs;
- actual dry active masses on both sides;
- current collector mass and area;
- separator grade and dimensions;
- electrolyte lot, concentration and volume;
- fixture ID and assembly record;
- voltage/current/temperature/time raw data;
- capacity, energy, coulombic efficiency, energy efficiency and impedance;
- both mass-normalisation bases until source convention is reconciled;
- failed cells, deviations and measurement uncertainty.

Only measured data from this programme may appear as company experimental results. Synthetic fixtures are labelled synthetic in the dataset.
