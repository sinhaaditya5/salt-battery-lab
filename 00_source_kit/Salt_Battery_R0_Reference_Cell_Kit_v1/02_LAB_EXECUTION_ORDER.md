# R0 laboratory execution order — what the lab actually does

**Scope:** a trained electrochemistry/materials laboratory reproduces a published aqueous sodium-birnessite reference. This document is a controlled work order, not a home/child experiment. The laboratory's EHS officer and principal investigator must approve the local SOP before any chemicals are opened.

## Work order A — close the method gaps before ordering

1. Obtain the paper and supporting information from the source DOI.
2. Email the corresponding author requesting: (a) full-cell slurry solvent and solids concentration; (b) exact carbon-paper grade/thickness/treatment; (c) separator grade, thickness and diameter; (d) fixture insert, spacer, spring and compression details; (e) exact active-mass normalization for the full-cell current density and capacity; (f) raw cycler data or additional protocol notes.
3. Ask the facility operator whether the MTI EQ-STC is suitable for this aqueous cell and how gas evolution/pressure risk is managed. Do not assume a closed split cell is a pressure-rated gas vessel.
4. Freeze the method version and create a deviation log. If the solvent or separator has to be selected locally, label the work R0-D (method-development variant), not an exact reproduction.

## Work order B — material preparation

The source paper's nominal route uses a manganese salt precursor and sodium hydroxide to produce Mn3O4, followed by solid-state sodium insertion at 270 °C. Exact values copied from the source are in `01_R0_REFERENCE_CELL_SPEC.md`. Only a trained laboratory may execute the source procedure under its approved SOP.

For a 3-batch reproducibility study, use three independently logged precursor preparations. The reported 0.700 g MnCl2·4H2O input per batch has a theoretical Mn3O4 upper-bound yield of approximately 0.27 g by manganese mass balance; actual isolated yield is unknown and must be measured. A 100 mg Mn3O4 insertion batch at NaOH:Mn3O4 = 4:1 molar ratio uses approximately 70 mg NaOH by formula-mass calculation. The paper's recipe does not establish the yield at a new laboratory.

Each batch is released only after XRD, ICP-OES/MS, TGA and SEM results are recorded. A nominal recipe is not a material certificate.

## Work order C — electrode process development

The paper reports 5.00 mg active material + 1.25 mg carbon black per 15 mm Toray paper disc. It does not specify full-cell slurry solvent volume/solids concentration in the main method. Do not silently guess it.

1. Request clarification from the authors.
2. Characterise the exact supplied carbon paper: grade, thickness, areal weight, PTFE treatment and sheet resistance.
3. Perform a small wetting/adhesion screening on sacrificial carbon-paper coupons with lab-approved candidate dispersants/solvents.
4. Select one formulation based on coating continuity, adhesion, electrical resistance and no visible material loss after electrolyte exposure.
5. Record all masses before and after drying. The locally selected method is R0-D until an author-confirmed protocol is used.

## Work order D — electrochemical safety map

1. Start with an instrumented three-electrode half-cell using a calibrated Ag/AgCl reference.
2. Measure OCP, pH, conductivity, CV and galvanostatic response at conservative limits selected by the PI/EHS review.
3. Record temperature and gas observation/analysis. Theoretical water stability is not a safe operating specification; overpotential and electrode surface effects vary.
4. Do not test the literature's 2.5 V symmetric-cell window in a closed fixture until gas evolution and pressure compatibility are quantified and written approval is given.
5. Use current limits, voltage cutoffs, temperature cutoffs and remote test shutdown. Any uncontrolled gas, heating, pressure, leak or short ends the test.

## Work order E — symmetric-cell replication

Only after the previous gates pass: document the actual fixture ID, insert diameter, spacer stack, separator datasheet, compression method, active-mass convention and electrolyte amount. Assemble at least three replicate cells with a qualified operator. Preserve raw cycler data, lot IDs and photographs. Do not quote specific capacity without both mass denominator definitions.

## Work order F — report

Report mean, standard deviation, all replicate data, failed cells, coulombic efficiency, energy efficiency, impedance changes, voltage profile, capacity retention and test temperature. Separate literature value, internal measurement, simulation and target in every table.
