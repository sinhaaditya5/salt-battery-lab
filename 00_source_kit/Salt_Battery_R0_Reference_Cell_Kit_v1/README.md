# Salt-derived battery programme — R0 reference-cell kit

**Version:** 1.2  
**Status:** published-material reproduction + electrode method development; not yet experimentally reproduced by this team.

## Start here

Read `START_HERE.md` first. It is the operator's plain-language route through the package. `docs/BUILD_CARDS.md` converts the programme into numbered, gated work cards. Work is for a qualified laboratory under site EHS/PI approval, not a home or child experiment.

## What R0 is

R0 is a laboratory reference based on Shan et al., *Nature Communications* (2019), DOI 10.1038/s41467-019-12939-3. It uses sodium-rich birnessite (nominal Na0.27MnO2·0.63H2O) on both sides of a symmetric aqueous research cell, with aqueous 1 M Na2SO4, cellulose filter-paper separator and 15 mm Toray/E-TEK carbon-paper discs. The paper reports 83 mAh/g after 5,000 cycles at 1 A/g on its stated electrode-material normalisation basis. This is not pack-level Wh/kg or a commercial EV cell.

R0 is **not** the new invention, final product chemistry, non-toxic product, or home-build kit. It is an evidence-based reproduction benchmark. It uses manganese compounds and caustic NaOH; aqueous electrolyte can still generate gas. The first programme gate is reproducible powder synthesis and characterisation, not a 2.5 V closed-cell cycle.

## Important source-method gap

The article specifies full-cell active mass, carbon black mass, 15 mm carbon-paper diameter, Whatman cellulose separator, 150 µL 1 M Na2SO4 and an MTI EQ-STC fixture. It does not state the full-cell slurry solvent/concentration or all substrate/separator/fixture mechanical details in the main Methods. The article separately specifies a DI-water ink recipe for its *half-cell* tests (7 mg active + 3 mg carbon black dispersed to 0.5 mg/mL); do not silently copy that different half-cell recipe into the full-cell procedure. See `01_R0_REFERENCE_CELL_SPEC.md` and `docs/BUILD_CARDS.md`.

## Build sequence

1. `CARD 0`: qualify lab, EHS, trained operator, equipment, fixture and waste route.
2. `CARD 1`: prepare Mn3O4 precursor in three independent batches using published nominal quantities.
3. `CARD 2`: sodium-insert precursor using the source-reported 270 °C / 6 h / open-air process; use measured composition, not nominal formula.
4. `CARD 3`: release powder only after XRD, ICP-OES/MS and TGA; SEM recommended.
5. `CARD 4`: develop and document the missing full-cell electrode slurry as R0-D.
6. `CARD 5`: map the electrochemical window in a qualified three-electrode setup with approved controls.
7. `CARD 6`: symmetric-cell assembly only after method gaps and gas/pressure controls are closed.
8. `CARD 7`: preserve all raw data and report uncertainty, failures and mass normalisation.

## Contents

- `START_HERE.md` — plain-language next actions and run commands.
- `01_R0_REFERENCE_CELL_SPEC.md` — chemistry, reported methods, reactions and evidence limits.
- `02_LAB_EXECUTION_ORDER.md` — lab work orders and method-gap closure.
- `docs/BUILD_CARDS.md` — numbered operator cards and stage gates.
- `docs/OUTREACH_EMAILS.md` — lab collaboration and corresponding-author email templates.
- `chemistry/FEASIBILITY_MATRIX.csv` — parallel tracks and evidence status.
- `chemistry/REACTION_REGISTER.md` — balanced precursor mass balance and schematic host reactions.
- `procurement/BOM.csv` — material specifications, CAS numbers and sourcing leads.
- `procurement/THREE_CELL_ORDER_LIST.md` — calculated three-batch planning amounts; not a purchase release.
- `procurement/EQUIPMENT_BOM.csv` — required lab capabilities and equipment, with purchase-vs-outsourcing guidance.
- `cad/electrode_disc_15mm.dxf` — exact 15 mm 2D electrode outline (only geometry fully specified by source for this part).
- `cad/stack_visualizer.scad`, `cad/R0_stack_visual_only.stl`, `cad/R0_stack_preview.png` — visual stack model; not a fabrication drawing.
- `simulation/cell_sizing_calculator.py` — arithmetic for nominal reagent/electrode quantities.
- `simulation/analyze_cycler_csv.py` — analyse actual instrument-export data after canonical-column conversion.
- `simulation/equivalent_circuit_model.py` — one-RC + lumped thermal model; requires measured parameters.
- `simulation/moonshot_requirements.py` — range/energy/charging-power arithmetic, not a battery simulator.
- `simulation/ATOMISTIC_WORKFLOW_STATUS.md` — DFT/MD readiness gate and exact structure inputs required before atomistic simulation.
- `validation/TEST_MATRIX.csv` and `results_template/` — gates and raw-data record templates.
- `safety/HAZARD_REGISTER.csv` — EHS review starter, not a replacement for SDS/risk assessment.
- `manufacturing/01_SCALE_UP_AND_AUTOMATION.md` — conditional lab → pilot → industrial process architecture.
- `economics/` — cost model that refuses to calculate until real costs/yields and measured energy/life are supplied.
- `yc/CLAIM_CONTROL_AND_EVIDENCE.md` and `yc/TECHNICAL_ONE_PAGER.md` — claim control and an investor-safe pre-prototype technical summary.
- `SOURCES.md` — papers, facilities and supplier links.

## Software setup

The included Python scripts use the Python standard library. No web API, paid model or paid software is required to execute the arithmetic/data-analysis scripts. OpenSCAD is required to edit/render the stack visualiser; CAD is not needed to run the Python utilities.

Windows PowerShell:

```powershell
.\scripts\run_software_checks.ps1
```

Or run individually:

```powershell
py -3 simulation/cell_sizing_calculator.py --cells 3
py -3 simulation/analyze_cycler_csv.py path/to/cycler.csv --positive-active-mg 5 --negative-active-mg 5 --out-dir analysis_out
py -3 simulation/equivalent_circuit_model.py simulation/rc_model_parameters_template.json path/to/current_profile.csv
py -3 simulation/moonshot_requirements.py --range-km 1500 --charge-minutes 5
```

The RC model will refuse null parameters. The synthetic demo files are only software test fixtures. Do not put synthetic outputs in an investor deck or YC application.

## Boundaries

- No proprietary battery chemistry, performance, safety or manufacturing result is claimed.
- The 5× energy-density and 1,500 km / 5-minute charging objectives remain unproven long-term ambitions.
- R0 does not satisfy the finished product's low-toxicity requirement.
- No full-cell slurry formula is invented where the paper is silent.
- The CAD layout is not a pressure-rated enclosure or production design.
- No supplier quote, production yield or cell cost is fabricated.

## Immediate action

Secure a lab partner and request author clarification before ordering process-specific materials. Use `docs/OUTREACH_EMAILS.md`. A published equipment list is not a promise of external access; negotiate access, IP, fees, training and waste responsibilities in writing.

## Verification status for this kit snapshot

The Python source files compile. The three-cell quantity calculator, synthetic cycler-data analyser, synthetic equivalent-circuit smoke test, and 1,500 km / five-minute requirement arithmetic run successfully. The cost model correctly refuses to calculate while actual supplier costs, accepted yields, measured cell energy and measured lifetime inputs are absent. The 15 mm DXF contains one 15.000 mm circle; the STL is a watertight **visual-only stack mesh**. No electrochemical experiment, DFT/MD, thermal abuse test or sealed-cell validation was performed by the kit author. The PowerShell runner is provided for Windows; it was not executed in this Linux build environment.
