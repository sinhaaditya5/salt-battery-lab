# R0 — sodium-birnessite aqueous symmetric reference cell

## 1. Decision

**Build R0 first as a literature-reproduction experiment.** The selected reference is Shan et al., *Structural water and disordered structure promote aqueous sodium-ion energy storage in sodium-birnessite*, Nature Communications 10, 4975 (2019), DOI: 10.1038/s41467-019-12939-3.

The authors report a sodium-rich disordered birnessite composition Na0.27MnO2 (hydrated in the working material, reported as Na0.27MnO2·0.63H2O), and a symmetric aqueous full cell using the same active material on both sides. The reported full-cell capacity is 83 mAh/g after 5,000 cycles at 1 A/g. The reported device uses aqueous Na2SO4 and carbon-paper current collectors. This makes it a useful salt-derived, aqueous, manganese-based reference for stationary-storage research.

**This is not a commercial EV battery, not a validated universal battery, and not proof of a new chemistry.** It is a research-cell reproduction target that can establish whether the lab can synthesize, characterise and electrochemically reproduce a published result.

## 2. Why this is the R0 reference

- Sodium-bearing precursor: NaOH is used to insert sodium into a manganese-oxide host. Industrial NaOH can be derived from purified brine (chlor-alkali supply chain), but R0 does not directly put table salt or seawater into the cell.
- Electrolyte: 1 M sodium sulfate in water.
- Active electrode: sodium-rich birnessite, Na0.27MnO2·xH2O.
- No organic carbonate electrolyte is used in the reported cell.
- The material uses manganese, sodium, oxygen, water and carbon; it avoids cobalt, nickel and cyanoferrate in this particular reference chemistry.
- The published route uses ordinary materials-processing equipment (solution precipitation, controlled furnace, washing, vacuum drying, electrode coating/casting and electrochemical test equipment), though it still requires a specialist laboratory.

## 3. Material identity and charge-storage model

### Active material

Nominal dry composition: `Na0.27MnO2`  
Hydrated phase reported after water intercalation: `Na0.27MnO2·0.63H2O`  
Structure: sodium-rich, disordered layered birnessite.

### Simplified charge-transfer representation

At one electrode during charge, sodium and associated interlayer water can be removed from the layered host:

`Na_xMnO2·yH2O ⇌ Na_(x−δ)MnO2·(y−ε)H2O + δNa+ + δe−`

At the opposite, nominally identical electrode, the reverse insertion occurs:

`Na_xMnO2·yH2O + δNa+ + δe− ⇌ Na_(x+δ)MnO2·(y+ε)H2O`

This is a **schematic bookkeeping representation**, not a fully balanced mechanistic equation for every proton, hydration, surface-redox and defect contribution. The paper identifies sodium-ion extraction/insertion and co-deintercalation of hydrated water; its detailed mechanism is not reducible to a single fixed stoichiometric reaction over the complete operating window.

## 4. Published synthesis route — exact reported values

The paper has two material-preparation stages.

### 4.1 Mn3O4 nanoparticle precursor

Paper-reported inputs and conditions:

- Manganese(II) chloride tetrahydrate: 0.700 g.
- Deionised water: 140 mL, reported resistivity 18.2 MΩ·cm.
- Sodium hydroxide solution: 0.123 g/mL.
- Metered addition: 0.167 mL/min for 50 minutes.
- Continued reaction after addition: 30 minutes, until a dark-brown precipitate formed.
- Product isolation: centrifugation.
- Washes: deionised water and ethanol, consecutively.
- Final drying: vacuum drying; the paper does not specify all vacuum/temperature settings for this intermediate.

The stated pump rate and duration imply 8.35 mL of NaOH solution and approximately 1.03 g NaOH delivered. This arithmetic is derived from the reported values; it is not a separately reported mass measurement.

### 4.2 Sodium-birnessite formation

- Mn3O4 precursor: 100 mg per composition-screen batch.
- NaOH: varied at NaOH:Mn3O4 molar ratios of 0.5, 1, 1.5, 2 and 4.
- Mixing: grinding with mortar and pestle as reported.
- Thermal treatment: 270 °C for 6 hours in open air in a tube furnace.
- Post-treatment: thoroughly wash with deionised water to remove residual NaOH; vacuum-dry overnight.
- Target composition: Na/Mn approximately 0.27 was obtained at the higher NaOH:Mn3O4 ratio of 4, according to the paper.

For a 100 mg Mn3O4 batch, the 4:1 molar ratio corresponds to approximately 70 mg NaOH (calculated from formula masses). The source uses a ratio screen; do not assume a 4:1 feed ratio guarantees the target composition for a different precursor morphology, furnace, batch geometry or supplier lot.

### 4.3 Required material release tests

Do not label the powder `Na0.27MnO2` from recipe alone. Release the batch only after:

- Powder X-ray diffraction (XRD): verify birnessite-like phase and check for residual Mn3O4/Mn5O8/other crystalline phases.
- ICP-OES or ICP-MS: verify Na:Mn ratio near the target, with analytical uncertainty reported.
- Thermogravimetric analysis (TGA): measure hydration/water content; compare with the paper's reported approximately 0.63 H2O only as a reference, not an automatic acceptance tolerance.
- SEM: document morphology and particle size distribution.
- Record batch yield, wash conductivity/pH endpoint, drying conditions and moisture exposure.

**Important:** the paper's synthesis method is reproduced here for a trained laboratory. NaOH is a severe corrosive and the synthesis combines caustic solution handling, centrifugation, ethanol washing and hot-furnace processing. Use institutional chemical hygiene, eye/face protection, compatible gloves, local exhaust, written SOPs and approved waste handling. It is not suitable for home or child assembly.

## 5. Published electrode and cell configuration

### 5.1 Electrode composition

The paper reports each electrode as:

- Na0.27MnO2 active powder: approximately 5.00 mg.
- Carbon black: approximately 1.25 mg.
- Active powder:carbon-black mass ratio = 4:1.
- Current collector: Toray carbon paper (E-Tek source named by paper), circular disc, 1.5 cm diameter.
- Coating method: drop-cast slurry containing the stated solids onto carbon paper; dry under vacuum overnight.

**Unreported detail:** the paper's full-cell-method text does not state a fully reproducible slurry-solvent volume/concentration, the exact carbon-paper grade/thickness, coating area/mass uniformity tolerance, or a complete separator specification. These must be obtained from the authors/supporting files or fixed through a documented laboratory process-development experiment. Do not silently invent values.

**Important distinction:** the paper separately specifies a *half-cell* ink: 7 mg sodium-manganese oxide + 3 mg carbon black dispersed in DI water to 0.5 mg/mL, sonicated, then 10 µL cast on a 0.5 cm glassy-carbon disc (3.5 µg active + 1.5 µg carbon). That is not the full-cell 5 mg + 1.25 mg, 15 mm carbon-paper slurry. It may not be transplanted without a documented R0-D method-development decision.

### 5.2 Cell stack

- Two nominally identical Na0.27MnO2/carbon electrodes.
- Cellulose-based filter-paper separator.
- Aqueous 1 M Na2SO4 electrolyte: 150 μL per test cell.
- Stainless-steel plates and compression spring for electrical contact.
- Split button-cell fixture; the paper names MTI model EQ-STC.

**Unreported mechanical details:** exact separator diameter/thickness, current-collector thickness, fixture stack dimensions, spring constant, applied compression force, gasket material and seal specification. Obtain the actual fixture drawing and separator datasheet before generating fabrication-ready CAD.

### 5.3 Electrolyte arithmetic

Anhydrous Na2SO4 molecular mass = 142.04 g/mol.

For 1 M solution:
- 10 mL final volume requires 1.4204 g Na2SO4.
- 100 mL final volume requires 14.204 g Na2SO4.
- The paper's 150 μL per cell corresponds to 0.150 mmol (approximately 21.3 mg) Na2SO4 contained in that volume.

Prepare by molarity to **final solution volume**, not by adding salt to a pre-measured final volume of water. Use reagent-grade anhydrous material and record lot/COA. Never substitute table salt (NaCl) for Na2SO4.

## 6. Electrochemical measurement reference

The paper reports:

- Half-cell electrolyte: 0.1 M Na2SO4 for certain tests.
- Three-electrode half-cell: glassy-carbon working electrode, platinum-wire counter electrode and Ag/AgCl reference electrode.
- Half-cell cyclic voltammetry: −1.25 to +1.25 V vs Ag/AgCl.
- Half-cell galvanostatic tests: −0.75 to +1.25 V vs Ag/AgCl, at current densities in the reported 0.3–2.0 A/g range.
- Symmetric full-cell electrolyte: 1 M Na2SO4.
- Symmetric full-cell potential window: 2.5 V, tested at 1, 2, 5 and 10 A/g.
- Reported full-cell capacity: 83 mAh/g at 1 A/g after 5,000 cycles.
- At the highest reported current density, capacity falls; the paper reports approximately 24 mAh/g at 10 A/g.

**Critical test-safety rule:** the thermodynamic water-stability window is about 1.23 V under standard conditions, although electrode overpotentials and surface chemistry can permit wider practical windows. The paper's 2.5 V symmetric-cell behaviour is a specialised result, not a universal safe operating voltage. Begin with electrochemical-window mapping and gas monitoring in a qualified lab. Do not move to sealed cells or the full reported window until the lab has a documented gas-evolution/pressure assessment and approved test fixture. A water electrolyte does not mean a cell cannot generate hydrogen/oxygen or build pressure.

### Current-normalisation ambiguity

The method reports A/g but full-cell methods do not unambiguously define in the main text whether the denominator is one electrode's active mass or combined active mass of both electrodes. Preserve the raw absolute current in every experiment. Report results on both bases until the supplementary information or authors confirm the original convention. Never compare specific capacity without stating its denominator.

## 7. What is experimentally demonstrated vs not demonstrated

### Demonstrated in the cited paper

- Na-rich disordered sodium-birnessite was synthesised and characterised.
- A symmetric aqueous cell was assembled with Na0.27MnO2 electrodes and Na2SO4 electrolyte.
- The authors reported 83 mAh/g after 5,000 cycles at 1 A/g.
- They studied high-rate performance and gas-evolution overpotential.
- They used XRD, ICP-MS, TGA, neutron total scattering and in-situ XRD to characterise material/structure.

### Not demonstrated by that paper

- 5× current commercial battery energy density.
- 1,500 km EV range or five-minute charging.
- Commercial pack-level 83 mAh/g or complete-pack Wh/kg.
- Automotive, truck, drone or defence suitability.
- Zero fire risk or zero toxic emissions under all failure modes.
- Factory cost, production yield, manufacturing reproducibility at GWh scale.
- A universal cell that fits every application.

## 8. R0 experimental gates

**Gate 0 — Laboratory readiness:** written risk assessment; chemical inventory/SDS; trained operator; fume hood/local exhaust; controlled furnace; vacuum oven; centrifuge; waste disposal; calibrated electrochemical test equipment; cell fixture documentation.

**Gate 1 — Material reproducibility:** three independently prepared powder batches; XRD, ICP-OES/MS and TGA for each; record yield and impurity phases. Fail if sodium composition/phase is not reproducible within pre-agreed analytical tolerances.

**Gate 2 — Electrode reproducibility:** record solids mass, carbon ratio, substrate lot/grade, active loading, geometric area, drying history and electrode resistance. Make at least three electrodes per condition.

**Gate 3 — Half-cell screening:** establish CV/galvanostatic behaviour in a three-electrode setup; document reference electrode calibration, pH, temperature, electrolyte conductivity and gas signals. Do not infer a safe window from literature alone.

**Gate 4 — Symmetric-cell reproduction:** use a documented cell fixture and pressure-management plan; test at a conservative window first; increase the window only after gas evolution is characterised. Use at least three replicate cells.

**Gate 5 — Independent reproduction:** second operator or external lab reproduces capacity, energy, cycle life and failure observations. Report mean, standard deviation and all failures.

## 9. R0 go/no-go criteria

The first success is **reproducible synthesis and repeatable reversible electrochemistry**, not a high energy-density claim.

Minimum gate to continue:
- Target phase and Na:Mn ratio are measured, not assumed.
- Three or more replicate cells show reversible charge/discharge with no unexplained short, leakage or uncontrolled gas generation.
- Coulombic efficiency, energy efficiency, specific capacity and impedance are reported with explicit mass basis.
- All cells and failures are preserved in the dataset.
- Waste and material inventory close within measurement tolerance.

Only after this should the team attempt controlled improvements: morphology, structural water, electrode loading, current-collector mass, electrolyte volume, separator and binder/process choices.

## 10. How the three-track programme continues

- **Track A (R0 aqueous birnessite):** reference chemistry and easiest aqueous sodium research route. It is the first laboratory build.
- **Track B (oxide solid-state sodium):** parallel computational/materials feasibility only until a qualified solid-state lab and verified structural input are available. Avoid sodium-metal anodes in the initial safety-constrained programme.
- **Track C (conventional sodium-ion benchmark):** compare commercially documented hard-carbon / layered-oxide or polyanion cells for energy density and manufacturability; it is a benchmark, not the intrinsically non-flammable target.

The 2024 high-performance alkaline NMF//NTP paper is a literature comparator, not the first build. It uses NaClO4, added NaOH, a Ni/C-Nafion coating prepared with DMF/isopropanol, and cyanoferrate-containing cathode material. Those ingredients/processes conflict with the low-hazard/simple-manufacture priorities and should only be handled by a qualified laboratory if pursued later.

## 11. Chemistry feasibility boundary and idealised synthesis balance

R0 is an aqueous sodium-host reference, not a final low-toxicity chemistry. It contains manganese compounds and requires caustic NaOH during synthesis. The supplier's manganese chloride listing carries serious health hazard classifications, and its sodium hydroxide listing identifies severe skin burns/eye damage. The electrolyte is aqueous, but the cell can still produce gas if driven outside its stable electrochemical conditions. It therefore does **not** satisfy the company's final intrinsic-safety / low-toxicity product requirement.

An idealised oxidation/precipitation mass balance for the Mn3O4 precursor route can be written:

`3 MnCl2 + 6 NaOH + 1/2 O2 -> Mn3O4 + 6 NaCl + 3 H2O`

This is a balanced bulk equation used for elemental bookkeeping. The source paper's method is an aqueous precipitation/oxidation procedure; the equation does not specify every aqueous intermediate or kinetic pathway.

Do not write a single exact balanced overall reaction for the NaOH/Mn3O4-to-hydrated-birnessite anneal without a measured product composition and water balance. The product is disordered, hydration-dependent and formed through Mn3O4 -> Mn5O8 -> Na-rich birnessite according to the paper's proposed mechanism. The electrochemical charge-storage schematic in Section 3 is deliberately written as a variable-composition host reaction.

## 12. R0 is a benchmark, not the winner

| Requirement | R0 status | Consequence |
|---|---|---|
| Sodium derived from a common sodium precursor | Yes, sodium is inserted from NaOH | Salt-derived supply chain is indirect; NaCl is not placed in the cell |
| Non-flammable aqueous electrolyte | Uses aqueous Na2SO4 | Aqueous electrolyte is not proof of zero gas or zero hazard |
| Low toxicity | Not met | Manganese salts and NaOH require occupational controls and waste handling |
| Lightweight / high cell energy | Not established as a practical cell or pack | Do not use for EV/drone claims |
| Fast charging | High current densities were studied | Reported current-density basis and cell-level mass need careful reconciliation |
| Small-scale reproducibility | Published lab method exists | Local method gaps must be closed and reproduced |
| Industrial scale | Not demonstrated | No scale-up, yield, line speed or factory economics data |

R0 is selected because there is a full peer-reviewed synthesis and cell study that can be used as an experimental baseline. It is not selected because it meets the final product specification.
