# S-cell R0 build manual: salt-assembled planar Na | β''-alumina | NaAlCl₄ | (Fe,Ni)Cl₂ test cell

**Rev A, 2 Nov 2026. CONCEPT — never executed.** This is a work package for a **qualified, supervised laboratory** with an argon glovebox, furnaces and a chemical-safety approval. It is **not** for home or unsupervised use.

- **Single source of truth:** `params/scell_params.py`.
- **Drawing:** SB-SC-001 (`04_MECHANICAL_CAD/drawings`).
- **Parts:** `06_PROCUREMENT/master_bom.csv`, items PS-C-xx, PS-M-xx and PS-E-xx.
- **Assembly map:** `assembly_maps/ASSEMBLY_MAP.md`.

**Why assemble discharged?** The cell is built from NaCl + Fe. **No sodium metal is handled at any step.** Sodium forms inside the sealed cell on the first charge.

**Step-card fields:** ID · Purpose · Parts · Tools · Input condition · Action · Expected output · Measurement · Acceptance · Failure conditions · Safety · Next.
Any deviation from an acceptance limit stops the build; log it in `results/cell_record.csv` (template in `acceptance_tests/`).

---

## A — Preparation and safety (before any material is opened)

### A-01 Authorisation
- **Purpose:** legal and safe operation.
- **Parts:** none.
- **Tools:** partner-lab safety file.
- **Input:** partner lab identified.
- **Action:**
  1. Obtain written approval from the lab safety officer for AlCl₃, NaAlCl₄, Ni powder, operation at 190–300 °C, and molten Na formed in situ.
  2. File this manual, `safety/HAZARD_ANALYSIS.md` and the SDS index.
- **Output:** signed approval.
- **Measurement:** n/a.
- **Acceptance:** signature, date and named supervisor.
- **Failure:** no approval → **STOP**.
- **Safety:** none.
- **Next:** A-02.

### A-02 Training record
- **Purpose:** competent operators.
- **Action:** operators complete glovebox, hot-work, HCl-release and Na-fire (Class D) training. A two-person rule applies to every heated step.
- **Acceptance:** two trained people listed.
- **Failure:** only one person → no heated steps.
- **Next:** A-03.

### A-03 Glovebox readiness
- **Purpose:** H₂O/O₂ control.
- **Tools:** glovebox, analysers.
- **Action:** regenerate the purifier if needed, then purge to spec.
- **Measurement:** H₂O and O₂ (ppm), logged for 1 h.
- **Acceptance:** H₂O < 1 ppm and O₂ < 1 ppm, stable for 1 h.
- **Failure:** > 1 ppm → regenerate and leak-check the gloves.
- **Safety:** asphyxiation risk in the antechamber area; O₂ monitor in the room.
- **Next:** A-04.

### A-04 Incoming inspection
- **Purpose:** right parts.
- **Parts:** all PS-M items.
- **Tools:** calipers, micrometer, flatness gauge or optical flat, 10× loupe.
- **Action:** measure every machined part against SB-SC-001 and the part list in `04_MECHANICAL_CAD/cell/scell_r0_partlist.csv`.
- **Measurement:**
  - disc OD and thickness;
  - ring counterbore depth;
  - sealing-face flatness on items 2, 5 and 12.
- **Acceptance:**
  - disc OD 30.0 +0/−0.1 mm and thickness ±0.05 mm;
  - flatness ≤ 0.02 mm;
  - no chips or cracks on items 1–2 (loupe).
- **Failure:** any crack in item 1 → reject (cracks propagate to Na/melt leaks).
- **Safety:** ceramic edges.
- **Next:** B-01.

## B — Materials (all inside the glovebox unless stated)

### B-01 Bake-out of hardware
- **Purpose:** remove adsorbed water.
- **Parts:** items 4–16.
- **Tools:** vacuum oven.
- **Action:** 150 °C under vacuum for 12 h, then transfer hot into the glovebox antechamber.
- **Output:** dry hardware.
- **Measurement:** oven log.
- **Acceptance:** ≥ 12 h at ≥ 140 °C, < 1 mbar.
- **Failure:** vacuum lost → repeat.
- **Next:** B-02.

### B-02 Dry the salt
- **Purpose:** NaCl at < 100 ppm H₂O.
- **Parts:** PS-C-01.
- **Tools:** vacuum oven, Karl Fischer titrator.
- **Action:** 250 °C under vacuum for 24 h, then transfer into the glovebox and store in a sealed vial.
- **Measurement:** Karl Fischer moisture (QT-06).
- **Acceptance:** < 100 ppm.
- **Failure:** > 100 ppm → repeat; if still high, change lot.
- **Safety:** hot glassware.
- **Next:** B-03.

### B-03 Weigh and mix the cathode powder
- **Purpose:** discharged cathode recipe.
- **Parts:** PS-C-01…07.
- **Tools:** balance (0.1 mg) inside the glovebox; ZrO₂ jar; planetary mill or agate mortar.
- **Input:** recipe for the target loading (table below, from `cathode_charge()`).
- **Action:**
  1. Weigh NaCl, Fe, Ni, FeS, NaF, NaI and Al.
  2. Mix gently (no high-energy milling: it would alloy or contaminate). Planetary mill at 200 rpm, 30 min, ZrO₂ media.
- **Output:** homogeneous grey powder.
- **Measurement:** masses (record to 0.1 mg).
- **Acceptance:** each mass within ±1 % of target.
- **Failure:** spill outside the vial → re-weigh the batch.
- **Safety:** Ni and Fe powders are inhalation hazards; they stay inside the glovebox.
- **Next:** B-04.

| mAh/cm² | NaCl g | Fe g | Ni g | FeS g | NaF g | NaI g | Al g | granules g | NaAlCl₄ g | bed mm |
|---|---|---|---|---|---|---|---|---|---|---|
| 30 | 0.370 | 0.280 | 0.033 | 0.020 | 0.007 | 0.007 | 0.014 | 0.730 | 0.254 | 0.85 |
| 60 | 0.740 | 0.560 | 0.065 | 0.041 | 0.014 | 0.014 | 0.027 | 1.461 | 0.507 | 1.70 |
| 100 | 1.233 | 0.933 | 0.109 | 0.068 | 0.023 | 0.023 | 0.046 | 2.435 | 0.846 | 2.83 |

### B-04 Synthesise the NaAlCl₄ melt
- **Purpose:** secondary electrolyte.
- **Parts:** PS-C-08 (AlCl₃) and PS-C-01 (NaCl), in a 1:1.02 molar ratio (slight NaCl excess gives a basic melt); Al foil scraps.
- **Tools:** borosilicate or quartz ampoule (or glassy-carbon crucible) inside a sealed vessel; hot plate in the glovebox.
- **Action:**
  1. Combine the salts.
  2. Heat slowly to 200 °C in a closed vessel.
  3. Add Al foil to scavenge impurities, and hold 12 h at 200 °C.
  4. Decant, cool and crush.
- **Output:** white to off-white solid NaAlCl₄.
- **Measurement:** melting point (DSC or visual, ~157 °C); colour.
- **Acceptance:**
  - colourless to white;
  - melts at 150–160 °C;
  - no visible AlCl₃ sublimate on cold surfaces at the end.
- **Failure:** grey or black (metal or carbon contamination) or yellow (Fe³⁺) → discard.
- **Safety:** **AlCl₃ + moisture → HCl**. Glovebox only. Sublimed AlCl₃ condenses on cold parts; clean inside the box. The vessel must not be sealed gas-tight while heating (pressure).
- **Next:** B-05.

### B-05 Granulate the cathode
- **Purpose:** porous granule bed (melt infiltration path).
- **Parts:** B-03 powder.
- **Tools:** 13 mm die, hydraulic press, sieves.
- **Action:** press at 100 MPa, crush, sieve, and keep the 125–425 µm fraction.
- **Output:** granules.
- **Measurement:** sieve yield; tap density.
- **Acceptance:** yield ≥ 70 % in range; tap density 1.7–2.1 g/cm³ (design 1.9).
- **Failure:** yield < 50 % → re-press at a different pressure.
- **Next:** C-01.

## C — Ceramic sub-assembly (may be bought pre-sealed; then do C-03 only)

### C-01 Clean the disc and ring
- **Parts:** items 1–2.
- **Action:** ultrasonic clean in isopropanol, then fire at 900 °C for 2 h in air (removes organics and adsorbed water). Store hot in a desiccator, then move into the glovebox.
- **Acceptance:** no residues (loupe).
- **Safety:** furnace hot work.
- **Next:** C-02.

### C-02 Glass-seal the disc into the ring
- **Purpose:** hermetic, insulating joint.
- **Parts:** items 1–3.
- **Tools:** glass-sealing furnace.
- **Action:**
  1. Place the disc in the counterbore and apply the glass paste fillet.
  2. Fire to the supplier's sealing profile (typically 900–1050 °C), ramping ≤ 5 °C/min.
- **Output:** sealed sub-assembly.
- **Measurement:** visual inspection; sub-assembly mass.
- **Acceptance:** continuous, bubble-free fillet; disc unchipped.
- **Failure:** crack or void → reject.
- **Safety:** high-temperature furnace.
- **Next:** C-03.

### C-03 Leak test (QT-02)
- **Purpose:** prove the seal.
- **Tools:** He leak detector and fixture.
- **Action:** He spray, sniffing across the joint.
- **Measurement:** leak rate.
- **Acceptance:** < 1 × 10⁻⁸ mbar·L/s.
- **Failure:** ≥ limit → reject.
- **Next:** C-04 (dummies) or D-01 (cells).

### C-04 Thermal-cycle qualification (QT-03; 4 dummies only)
- **Action:** 20 cycles of 25 ↔ 190 °C at 2 °C/min in Ar, then repeat C-03.
- **Acceptance:** all 4 dummies still < 1 × 10⁻⁸ mbar·L/s.
- **Failure:** any fails → change glass or profile **before building any cell (gate G5)**.
- **Next:** D-01.

## D — Cell assembly (glovebox)

### D-01 Lay out the parts
- **Action:** lay out a kit per cell using the assembly map: anode housing (12), wick and shim (13), gasket (11), sealed sub-assembly (1–3), gasket (4), cathode housing (5), Mo mesh (7), spring (8), fill tube (9), TC well (10), and bolts with sleeves and washers (14–16).
- **Acceptance:** every item present and labelled with the cell ID.
- **Next:** D-02.

### D-02 Braze or weld the fill tube and TC well into the cathode housing
- Done **outside** the glovebox, before bake-out.
- **Tools:** micro-TIG or laser welding service.
- **Measurement:** He leak test of the housing.
- **Acceptance:** < 1 × 10⁻⁸ mbar·L/s.
- **Next:** D-03.

### D-03 Stack the anode side
- **Action:**
  1. Place anode housing (12) on the fixture, sealing face up.
  2. Insert the wick roll and shim (13).
  3. Place gasket (11).
  4. Place the sealed sub-assembly with the **disc anode face down** (z = 0 face; mark it in C-01).
- **Measurement:** wick protrusion above the housing face before compression.
- **Acceptance:** wick touches the disc anode face with 0.2–0.4 mm compression (feeler gauge).
- **Next:** D-04.

### D-04 Wet the anode face (optional, recommended)
- **Purpose:** first Na plating needs a wettable surface.
- **Action:** paint a thin graphite ink or carbon-evaporated layer on the anode face before C-02 (vendor option). Record whether it was done.
- **Acceptance:** recorded.
- **Next:** D-05.

### D-05 Load the cathode
- **Action:**
  1. With the ring cathode face up, place gasket (4).
  2. Pour the B-05 granules into the 24 mm window and level them with a PTFE spatula.
  3. Place the Mo mesh (7) and Mo spring (8).
- **Measurement:** bed height (depth gauge).
- **Acceptance:** height within ±0.15 mm of the table in B-03.
- **Failure:** granules on the gasket → clean (a leak path otherwise).
- **Next:** D-06.

### D-06 Close and torque
- **Action:**
  1. Place the cathode housing (5).
  2. Insert sleeves (15), washers (16) and bolts (14).
  3. Torque in a star pattern to 1.2 N·m.
- **Measurement:**
  - insulation resistance between + and − at 500 V DC;
  - continuity from the + housing to the Mo mesh.
- **Acceptance:** > 100 MΩ (QT-08 at RT); continuity < 1 Ω.
- **Failure:** low insulation → re-seat the sleeves.
- **Next:** D-07.

### D-07 Infiltrate the melt
- **Action:**
  1. In the glovebox well furnace at 200 °C, feed molten NaAlCl₄ (mass from the B-03 table) through the fill tube.
  2. Evacuate and back-fill with Ar 3× to pull the melt into the granule bed.
- **Measurement:** mass gain.
- **Acceptance:** within ±5 % of the table value.
- **Failure:** < 90 % → the bed is blocked; disassemble.
- **Safety:** melt at 200 °C; AlCl₃ vapour → work inside the box; face shield at the antechamber.
- **Next:** D-08.

### D-08 Seal the fill tube
- **Action:** crimp the Ni tube, cut it, and seal-weld the tip (micro-TIG through a glovebox port, or a sealed transfer to the welding station).
- **Measurement:** He leak test of the whole cell at RT.
- **Acceptance:** < 1 × 10⁻⁸ mbar·L/s.
- **Failure:** leak → re-weld.
- **Next:** E-01.

## E — Fixture, electronics and heating

### E-01 Wire the SCM-1 monitor
- **Parts:** PS-E-02 (or the alternative DAQ + independent over-temperature controller).
- **Action:** connect:
  - J2 cell taps (cell −: J2.1; cell +: J2.2);
  - J3 cycler negative through the shunt;
  - J5 NO-COM to the cycler's external interlock;
  - J6 to the E-stop auxiliary NC contact.
- **Measurement:** electrical test procedure `acceptance_tests/ELECTRICAL_TEST_PROCEDURE.md`, TP-E01…E06.
- **Acceptance:** all TP-E steps pass.
- **Failure:** any → no heating.
- **Next:** E-02.

### E-02 Thermocouples
- **Action:**
  1. TC1 (control) in the cathode TC well (item 10).
  2. TC2 on the anode housing.
  3. TC3 in the furnace air.
  4. TC4 as the independent trip sensor next to TC1.
  - Use **ungrounded-junction** TCs only.
- **Measurement:** all read RT ± 2 °C.
- **Acceptance:** spread < 2 °C at RT; open-TC detect works (unplug TC4 → FAULT).
- **Next:** E-03.

### E-03 Interlock chain check
- **Action:**
  1. With the furnace empty, run the heater to 60 °C.
  2. Force a TC trip by setting a test threshold of 50 °C.
- **Measurement:** heater current drops; SSR LED off.
- **Acceptance:** heater off in < 1 s with **firmware halted** (hardware AND gate); E-stop also cuts it.
- **Failure:** heater stays on → **STOP**; the electronics are not safe.
- **Next:** E-04.

### E-04 Mains safety
- **Action:** confirm the bimetal cut-out (300 °C) and the E-stop NC contact are wired in series with the SSR load (off-board), and that the furnace sits on a steel drip tray filled with dry sand.
- **Acceptance:** visual check and continuity.
- **Next:** F-01.

## F — Heat-up and formation

### F-01 Heat to operating temperature
- **Action:** SCM-1 command `S`; the ramp is 2 °C/min to 190 °C.
- **Measurement:** TC1 and TC2; cell OCV.
- **Acceptance:**
  - ramp ≤ 2 °C/min;
  - OCV appears once the melt is liquid (~157 °C). In the discharged state expect **≈ 0–1.6 V** (no Na yet).
- **Failure:** OCV > 2.95 V or a temperature overshoot > 10 °C → SCM-1 FAULT.
- **Safety:** two people present for the first heat-up.
- **Next:** F-02.

### F-02 First charge (formation)
- **Purpose:** generate Na in situ.
- **Action:** charge at 2 mA/cm² (≈ 9 mA) to 2.75 V and hold until the current falls to C/50.
- **Measurement:** charge capacity; voltage curve.
- **Acceptance:**
  - a plateau appears at ~2.35 V (Fe/FeCl₂) and a short one at ~2.58 V (Ni);
  - capacity ≥ 70 % of design Q at the first charge.
- **Failure:**
  - voltage jumps to 2.75 V with no plateau → no Na wetting (see troubleshooting T-03);
  - > 3.0 V → overcharge reaction; stop.
- **Next:** F-03.

### F-03 Formation cycles
- **Action:** 3 cycles between 1.80 and 2.75 V at 5 mA/cm².
- **Measurement:** CE; capacity; EIS at 50 % SOC.
- **Acceptance:** CE ≥ 99 % by cycle 3; ASR (from EIS) recorded.
- **Next:** G-01.

## G — Acceptance tests (gates; protocols in `09_VALIDATION/protocols/TEST_PLAN.md`)

| ID | Test | Pass criterion |
|---|---|---|
| G-01 | Replication (G1) | ≥ 100 mAh/g-cathode at 10 mA/cm², 190 °C |
| G-02 | Loading (G2) | at 60 mAh/cm²: ≥ 80 % NaCl utilisation at 10 mA/cm², ASR ≤ 4 Ω·cm² over 0–80 % DoD |
| G-03 | CE (G3) | mean CE ≥ 99.9 % over cycles 10–100 |
| G-04 | Cost lever (G4) | passing loading with the 0.5 mm disc → β''-alumina ≤ 1.0 kg/kWh |
| G-05 | Seal (G5) | QT-03 passed (C-04) |

## H — Shutdown, disassembly and waste

### H-01 Normal shutdown
- **Action:**
  1. Fully **discharge** to 1.80 V (sodium returns into NaCl; the cell becomes safe).
  2. SCM-1 `X`; the cool-down ramp is 2 °C/min.
- **Acceptance:** OCV < 2.0 V before cooling.
- **Failure:** cannot discharge → cool while charged, and label "CONTAINS Na METAL".
- **Next:** H-02.

### H-02 Disassembly
- In the glovebox only.
- A charged or unknown-state cell contains Na metal: quench Na residues in the box with dry isopropanol, small amounts at a time, and keep a Class D extinguisher ready.
- Cathode material goes to labelled waste.
- **Next:** H-03.

### H-03 Waste
- Chloroaluminate and metal-chloride residues are hydrolysed slowly in a fume hood (HCl evolution) and neutralised.
- Ni-containing solids are disposed of as heavy-metal waste through the lab's licensed contractor.
- **Acceptance:** waste log signed.
