# Atomistic simulation readiness — R0

## Status

**DFT/MD has not been run for this team's material.** No calculation result is included in the kit.

## Why no ready-made QE/CP2K input is supplied

The R0 active material is reported as disordered, hydrated Na0.27MnO2·0.63H2O (triclinic birnessite). A single small idealized ordered cell is not a faithful representation of its sodium occupancy, water occupancy, defects and disorder. A public Na-birnessite CIF from a different sample is not interchangeable with the exact R0 sample. Starting DFT from an unverified structure would produce precise-looking output for the wrong model.

The paper itself reports DFT work using WIEN2k and an idealized NaMnO2·H2O model, alongside experiments; this does not provide an experimentally validated atomistic supercell that automatically reproduces every disordered/hydrated R0 batch.

## Required inputs before simulation

1. CIF or refined structural model from the source supplementary information, or a model derived from the team's measured XRD/PDF and composition.
2. Measured Na:Mn ratio from ICP-OES/MS.
3. TGA-informed structural-water bounds.
4. Occupancy/disorder model and supercell size, documented explicitly.
5. Mn oxidation/spin-state assumptions and magnetic ordering candidates.
6. Exchange-correlation functional, Hubbard U decision, pseudopotential family, cutoff convergence and k-point convergence plan.
7. Charge state, defect model and reference chemical potentials for the property being calculated.

## Proposed computational sequence

| Stage | Tool family | Computation | Gate |
|---|---|---|---|
| S0 | ASE / CIF tools | Parse, validate formula, occupancies, symmetry and cell | No invalid/disordered occupancy silently rounded |
| S1 | ASE + supercell builder | Generate ensemble of explicit Na/H2O configurations | Report ensemble and seed, not one convenient structure |
| S2 | Quantum ESPRESSO or CP2K | Converged spin-polarized structure relaxation | Energy/force/stress convergence documented |
| S3 | DFT + NEB | Candidate Na migration barriers | Converged pathway and image count; do not infer cell rate directly |
| S4 | DFT | Voltage / insertion energies for specified x states | Chemical potential reference and corrections explicit |
| S5 | LAMMPS / validated interatomic potential | MD only if a transferable validated potential exists | Do not use an unvalidated force field for predictive claims |
| S6 | PyBaMM / equivalent circuit | Cell-level model from measured parameters | Fit and validate on separate experimental profiles |

## Output contract

Every calculation must export: input structure hash, code/version, pseudopotential hashes/licences, parameter file, convergence evidence, stdout/stderr, final structure, energy/force files, and a `calculation_manifest.json`. Every result is labelled **theoretical/computational**, never measured cell performance.

## Next blocking action

Obtain the source supplementary information and/or complete a structural refinement of the first team's powder. Until then, do not fabricate an R0 CIF or issue a “simulated battery performance” claim.
