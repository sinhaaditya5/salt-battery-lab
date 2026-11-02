# IDEA v2: stress test and improvement (Phase 3)

**Date:** 2 Nov 2026 · **Status:** pre-prototype; every performance figure below is [TARGET], [SIM] or [CALC], never measured.

## 1. The idea after stress-testing

**Recommended direction tested:** "The battery you're allowed to put indoors." This is a water-based sodium battery for places where fire code or insurance makes lithium expensive or forbidden. It would be sold on installed cost including fire protection, plus cost per cycle, not on cell $/kWh.

**What the evidence says**

1. **Energy.** A bottom-up 12 V block lands at **17.6 Wh/kg** median (P10–P90: 13.7–22.1) [CALC, S7]. That is essentially Aquion's last module (18.6 Wh/kg [CALC from VENDOR datasheet, SRC-035]). It is below a VRLA block's ~40 Wh/kg and far below sodium-ion cells claiming 135–175 Wh/kg [VENDOR].
2. **Cost.** It costs **$350/kWh** to make (about $200 with optimistic inputs) [CALC, S9]. A stationary LFP pack sells for **$70/kWh** [LIT, BNEF 2025]. A Prussian-white variant (C) reaches $150–260/kWh [CALC].
3. **Indoor total cost.** Over 15 years per kWh of 15-minute backup, R1 comes to $1,228, LFP to $720 including $60/kWh of fire protection, and VRLA to $990 [CALC, base assumptions]. R1 only wins with all of these together:
   - an optimistic chemistry,
   - a ≥15-year float life,
   - lithium fire and room costs of $150–250/kWh or more.
4. **Codes do not grant the advantage.** IFC 2024 puts "other battery technologies" at **3 kWh**, below Li-ion's 20 kWh [LIT, SRC-081]. NFPA 855-2026 requires a hazard mitigation analysis plus UL 9540A and large-scale fire testing for essentially all systems. It exempts lead-acid and aqueous nickel from explosion control, but not aqueous sodium [LIT, SRC-085…088]. "Allowed indoors" has to be *earned* with test data and, eventually, a code listing. Zn-MnO₂'s 70 kWh row is the precedent [LIT, SRC-082].
5. **Physics risks found by simulation:**
   - 1 M Na₂SO₄ crystallises below ~15–20 °C [CALC from LIT], so R1 uses 0.5 M.
   - A sealed cell needs CE ≥ 99.88% or it loses 20% of its water before 3,000 cycles [CALC, S4].
   - The NTP anode runs ~0.2 V below the H₂ line at pH 7, so UPS float duty is the worst case [CALC, S4].
   - Thick electrodes (≥60 mg/cm²) can't deliver a 15-minute discharge [SIM, S3].
6. **The space is crowded and well funded.**
   - Peak Energy ($108M Series B, >$1B orders) and Alsym (135 Wh/kg "NFPP+", AI data centres) already sell non-flammable sodium-ion.
   - Natron (Prussian blue, data-centre backup) shut down in 2025, and Aquion went bankrupt in 2017 [LIT/VENDOR].
7. **The India market is small.** The backup-battery TAM is ~$340M/yr, SAM ~$74M/yr, and SOM ~$3.5M/yr after 5 years [CALC, S10]. Paid reports agree on the TAM (~$305–401M) [LIT, low confidence].

**Verdict on the idea as framed: weak.** The decision is in `DELIVERABLES/STARTUP_DECISION_MEMO.md`.

## 2. Chemistry decision matrix (weighted, 1–5)

Full table with evidence: `decisions/chemistry_matrix.csv`. Totals:

| Candidate | Score | One-line reason |
|---|---|---|
| A. R0 symmetric Na-birnessite | 2.55 | Benchmark only. Its 2.5 V window sits well outside water's stability range |
| B. Na-birnessite // NaTi₂(PO₄)₃-C, Na₂SO₄ (Aquion lineage) | 2.65 | Reproducible from R0, but ~18 Wh/kg and $350/kWh. The anode sits below the H₂ line |
| C. Mn/Fe Prussian-white // NTP-C, non-perchlorate | 3.10 | Best energy and cost of the aqueous options, but cyanide-ligand perception and Mn dissolution. Strong results so far rely on perchlorate |
| D. Na-birnessite // activated carbon (hybrid capacitor) | 3.25 | Best cycle life, rate and float safety, but ~6 Wh/kg and $840/kWh. The floor space is impractical for 5–15-minute UPS |

No candidate scores above 3.5. Weight sensitivity: if cost and energy together carry ≥0.45 of the weight, C ranks first; if safety and cycle life dominate, D does.

**How Candidate B avoids Aquion's failure (and where it can't):**
- **What it can change:**
  - Sell only where non-flammability is priced, not into off-grid or grid storage on $/kWh.
  - Design for power from day one. Aquion managed 0.45C; UPS needs 4–12C.
  - Stay capital-light (contract manufacturing, no gigafactory before product–market fit).
  - Earn a code listing early.
- **What it can't change:** the energy density. This is why B is a test vehicle, not a committed product.

## 3. R1: chosen product hypothesis

**R1 = a birnessite-cathode platform in a 12 V VRLA-format block (330 × 173 × 220 mm), with two electrode builds that share the cathode:**
- **R1-E** (Candidate B, NTP anode) for cycling telecom duty.
- **R1-P** (Candidate D, activated-carbon anode) for float and short ride-through.

**Why this and not C:** the founder's first 12 weeks can only test a material with a published, fully specified synthesis. R0 is that material, and it is shared by B and D. A single reproduction experiment therefore de-risks two product builds. C is the upgrade path if B misses the energy gate.

### R1-E datasheet: every line is [TARGET] unless tagged otherwise

| Parameter | Value | Tag / basis |
|---|---|---|
| Nominal voltage | 12 V block (10 cells × ~1.16 V) | [TARGET]; cell voltage [CALC] from electrode potentials |
| Cell voltage window | 0.60–1.75 V | [TARGET] |
| Energy per block (C/10) | 0.40 kWh (P10–P90: 0.26–0.43) | [TARGET] from [CALC] S7 |
| Specific energy (block) | ≥ 20 Wh/kg (go/no-go ≥ 25 by M6) | [TARGET] |
| Energy density (block) | ≥ 30 Wh/L | [TARGET] |
| 15-minute rate | ≥ 80% of C/10 energy at 40 mg/cm² | [TARGET]; S3 median 86% [SIM] |
| Round-trip efficiency | ≥ 93% (C/5–1C, system) | [TARGET]; S3 cell 96–99% [SIM] |
| Coulombic efficiency | ≥ 99.9% per cycle | [TARGET]; S4 requirement |
| Cycle life | 3,000 cycles to 80% | [TARGET] |
| Float life (R1-P) | 10–15 years | [TARGET] |
| Electrolyte | 0.5 mol/L Na₂SO₄, pH ~7, no perchlorate | [TARGET] (D-05) |
| Operating temperature | 5–45 °C (salt crystallisation sets the low limit) | [TARGET]/[CALC] |
| Thermal runaway | No exothermic runaway chain; plastic case is the fire load | [CALC] S8 |
| Gas | One-way vent at ~15 kPa; H₂ ventilation sized to ≤25% LFL | [TARGET]/[CALC] S4 |
| Monitoring | Per-block V, T, string current, H₂ and pressure inputs | [TARGET] (PCB `pcb/`) |
| Certification path | UL 1973 + UL 9540A cell/unit; IEC 62619 analogue; BIS/TEC in India | [TARGET] |
| Cost | ≤ $150/kWh by the first 0.5 GWh line | [TARGET]; base [CALC] $350 |

## 4. Wedge and first customer profile

- **Wedge (if hardware continues):** indoor and in-building telecom equipment rooms, and small data-centre or enterprise UPS rooms in Indian cities, where lead-acid is being replaced and lithium triggers fire-engineering cost or landlord or insurer objections.
- **First customer profile:** a tower company or neutral-host operator with in-building sites (malls, hospitals, metro stations), or a mid-size colocation operator with UPS rooms under 1 MWh. The buyer is a facilities head who already pays for VRLA replacement every 3–5 years.
- **Not targeted:** grid BESS (LFP wins on $/kWh), EVs, hyperscale data centres (space-critical).

## 5. Unique insight

The original insight ("indoors, the bar is lead-acid, not lithium") **did not survive.** Bottom-up, our block falls short of lead-acid by volume, and Li-ion's indoor premium is too small at base assumptions to close the cost gap.

What survived is narrower, and it is a market observation, not a technical moat: **fire codes reward *tested, listed* chemistries, not "safe" ones.**
- An unlisted water-based chemistry starts *stricter* than lithium.
- From 2026, every installation needs a hazard mitigation analysis.

The defensible asset is therefore test data plus code listing plus permitting know-how. That points to the alternative wedge in the decision memo (battery fire-code / HMA software) more than to a cell factory.

We found **no unique technical insight** that lets an aqueous cell beat sodium-ion or LFP on cost per delivered kWh.

## 6. Kill criteria (any one stops the battery path)

| # | Gate | Threshold | When |
|---|---|---|---|
| K1 | Cathode capacity at real loading | < 60 mAh/g at 40 mg/cm², C/5, 0.5 M Na₂SO₄ | Week 10 |
| K2 | Side reactions | CE < 99.5% at 1C (needs ≥ 99.88% for 3,000 cycles) | Week 10–12 |
| K3 | Power | < 60% of C/10 capacity at a 15-minute rate, 40 mg/cm² | Week 12 |
| K4 | Customer value | < 3 of 20 interviewed buyers name a lithium indoor premium ≥ $150/kWh, or a prohibition | Week 8 |
| K5 | Cost path | Re-run S9 with measured capacity and two supplier quotes; block cost > $250/kWh with no credible path to $150 | Week 12 |
| K6 | Code path | Two AHJs or fire engineers confirm that UL 9540A data would not lift the unlisted-chemistry limits | Week 12 |

## 7. What changed from the kit, and why

See `decisions/DECISIONS.md` (D-01…D-10). In short:
- **Dropped:** EV, 5× and 1,500 km claims; the symmetric cell as a product; 1 M electrolyte.
- **Added:** VRLA-format block; 0.5 M electrolyte; power-first electrode design; gas and water budget gates; code-listing work; cost-model gates.
- **Reframed:** the "unique insight", downgraded honestly.
