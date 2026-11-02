# START HERE — R0 first-cell programme

**Version:** 1.2  
**Current status:** literature-reproduction and method-development kit. No cell has been built or tested by this team.

## The honest one-line description

This package lets a qualified battery/materials laboratory reproduce the *material* in a published aqueous sodium-birnessite study, characterise it, and develop a traceable electrode/cell process. It is not a home experiment, not a finished battery design, and not proof of the new battery company’s target performance.

## What you do first — in this order

### Step 1 — secure a laboratory partner; do not buy chemicals yet

Ask a battery/electrochemistry laboratory to confirm it can provide:

- trained operator and approved chemical risk assessment;
- fume hood / local exhaust, centrifuge, vacuum oven and controlled tube furnace;
- XRD, ICP-OES or ICP-MS, TGA and preferably SEM;
- three-electrode potentiostat with calibrated Ag/AgCl reference;
- gas monitoring or an approved gas-evolution assessment;
- battery cycler / EIS and a documented test fixture;
- manganese- and caustic-waste disposal.

India facility leads (access is not guaranteed):

- IIT Roorkee Energy Materials Laboratory: `anjan.sil@mt.iitr.ac.in`, `indranil.lahiri@mt.iitr.ac.in`. Published equipment includes an Arbin BT-2000, LCR impedance analyser, glovebox and powder-density equipment.
- IIT Bombay Electrochemical Energy Laboratory: `sagar.mitra@iitb.ac.in`, `+91-22-25767849`. Published facilities include Arbin/Biologic battery testing, glovebox, slurry mixer/coater, electrode cutter and pouch-cell sealing.

Use `docs/OUTREACH_EMAILS.md` to request access and a paid or collaborative scope. Ask for fees, sample policy, instrument availability and waste charges in writing.

### Step 2 — obtain method clarification

Email the corresponding author of the 2019 reference paper using the template in `docs/OUTREACH_EMAILS.md`. Ask about:

1. Full-cell slurry solvent, solids concentration and dispersion procedure.
2. Exact E-TEK/Toray carbon paper grade and thickness.
3. Whatman separator grade, diameter and thickness.
4. EQ-STC inserts, spacer, spring and compression details.
5. Full-cell current/capacity mass-normalisation convention.
6. Supplementary calculation details and raw data if shareable.

The full-cell article method says “slurry” but does not give the slurry solvent/concentration in the main Methods. The half-cell method uses a DI-water ink, but that is a different electrode preparation and must not be silently substituted.

### Step 3 — approve the chemical purchase list with the lab

Open `procurement/THREE_CELL_ORDER_LIST.md` and `procurement/BOM.csv`.

The calculated three-batch minimum is a *planning quantity*, not a purchase release. Supplier catalogue grades may not meet the metals-basis purity in the paper. The lab must compare each proposed lot COA and SDS with the source specification, approve quantities, and check the waste route.

### Step 4 — reproduce the powder before building the cell

Follow Work Orders A and B in `02_LAB_EXECUTION_ORDER.md` under the laboratory’s approved SOP. Prepare three independent batches. Weigh and label every batch. Do not pool batches before quality release.

Release each powder batch only after the agreed XRD + ICP-OES/MS + TGA checks. SEM is useful for morphology. Record actual mass yield; do not substitute theoretical yield for measured yield.

### Step 5 — perform electrode method development

The source full-cell formulation is incomplete. Use the lab’s controlled design-of-experiments plan to choose a dispersion process. Record solvent, binder (if any), solids concentration, mixing, sonication, coating, drying, loading, adhesion and resistance. This becomes **R0-D**, a documented deviation from exact replication.

Do not infer that a binder or solvent is source-paper validated. Do not move to sealed symmetric cells until the lab has approved separator, fixture and gas/pressure controls.

### Step 6 — map the electrochemical window before cycling a closed cell

Use the test matrix and a qualified three-electrode setup. Establish the practical window for the *actual* electrode batch and electrolyte with gas/temperature observation or analysis. The literature’s 2.5 V full-cell window is not an automatic safe setting for a different fixture or reproduced cell.

### Step 7 — assemble and test only after gates pass

The source describes two symmetric electrodes, cellulose filter-paper separator, 150 µL of 1 M Na2SO4 electrolyte and an MTI EQ-STC split test fixture. Obtain the current manufacturer drawing and confirm suitability for aqueous cells and gas management. Do not fabricate or seal an improvised fixture from the visual CAD.

Use at least three independent cells. Save untouched instrument exports and photograph each cell. Analyse data with `simulation/analyze_cycler_csv.py` after checking instrument sign conventions and mass basis.

## What is ready in this package

- Exact literature-reported precursor and sodium-insertion quantities, plus transparent arithmetic.
- A procurement BOM with CAS numbers and supplier leads.
- Chemistry comparison and reaction register.
- Lab work orders and gates.
- CAD for the **known 15 mm electrode-disc outline** and a separate visual stack model.
- A cycler-data analysis script, quantity calculator, and parameterised equivalent-circuit model.
- A cost model that refuses to fabricate unit economics when real prices/yields/performance are missing.
- Manufacturing scale-up architecture and YC claim-control ledger.

## What is not ready / what must not be misrepresented

- No proprietary chemistry has been invented or validated.
- R0 is a manganese-containing research reference; it does not meet the final low-toxicity specification.
- No complete symmetric-cell full-cell slurry recipe is reported in the main article.
- The DXF is a 15 mm circle outline only. The STL/SCAD is a visual layout, not a sealed-cell mechanical design.
- The RC simulation is an equivalent-circuit model, not DFT/MD or an electrochemical chemistry prediction.
- No team experiment, performance result, production yield, factory cost or safety certification is included.

## Folder map

- `01_R0_REFERENCE_CELL_SPEC.md` — reference chemistry, measurements and known gaps.
- `02_LAB_EXECUTION_ORDER.md` — laboratory work orders.
- `chemistry/` — feasibility and reaction registers.
- `procurement/` — materials and sourcing.
- `cad/` — editable outline, SCAD model, STL and preview.
- `simulation/` — executable scripts and synthetic test data.
- `validation/` — test matrix and stop conditions.
- `manufacturing/` — lab-to-pilot-to-industrial process design.
- `economics/` — cost-input template and model.
- `yc/` — claim-control sheet.

## Run the software checks

Windows PowerShell:

```powershell
py -3 simulation/cell_sizing_calculator.py --cells 3
py -3 simulation/analyze_cycler_csv.py simulation/demo_synthetic_data.csv --positive-active-mg 5 --negative-active-mg 5 --out-dir simulation/demo_analysis_output
py -3 simulation/equivalent_circuit_model.py simulation/rc_model_demo_synthetic_parameters.json simulation/current_profile_demo_synthetic.csv --output simulation/rc_demo_synthetic_output.csv
py -3 simulation/moonshot_requirements.py --consumption-low 15 --consumption-high 20 --range-km 1500 --charge-minutes 5
```

The demo cycler/current/RC inputs are synthetic test data, not battery results. The unit cost model intentionally has no price/yield/performance inputs and must not be treated as a quote.
