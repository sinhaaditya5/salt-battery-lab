# S11: DFT(+U) campaign on the salt-literal chemistries (Apple M4 + EC2)

**Why these systems.** Na | NaCl | MCl₂ (M = Fe, Co, Ni) and Na | Cl₂ are the only couples in which common salt is the active material (S12).

## Record (brief §6.1)

| Item | Value |
|---|---|
| Software | Quantum ESPRESSO 7.6 + OpenMPI 5 from conda-forge. **Local:** osx-arm64 build `qe-7.6-mpi_openmpi_h7d45502_104` on an Apple M4 (10 cores, 16 GB), 2 lanes × 4 MPI ranks: conv stage and the Na, NaCl, Cl₂, Fe, Co, Ni, FeCl₂, CoCl₂ relaxations. **EC2 (3 Nov 2026):** linux-aarch64 build `qe-7.6-mpi_openmpi_h8cbc21f_104` on a c8g.8xlarge spot instance (32 Graviton4 cores), 2–4 lanes × 8–16 ranks with 4 k-point pools: NiCl₂ relaxations, U-scan, magnetic and PDOS stages. Same inputs, pseudopotentials and cutoffs; per-job platform in `../validation/s11_results.json` → `platform`; driver scripts in `ec2/` |
| Functional | PBE + Grimme D3(BJ) (`vdw_corr='dft-d3', dftd3_version=4`) on every phase, for the layered chlorides |
| Hubbard | ortho-atomic projectors on M-3d; U = 0 and 4 eV (vc-relax) and U = 0/2/4/6 eV (fixed-geometry scan); metals always U = 0 (mixing uncorrected, see limitations) |
| Pseudopotentials | GBRV USPP (see `../pseudopotentials/PROVENANCE.md`) |
| Cutoffs | 50 / 400 Ry. Convergence: NiCl₂ at 50 Ry is within ~2 meV/atom of 70 Ry; pressure within 1 kbar |
| k-mesh | linear density 20 Å (insulators; 15 Å for chloride vc-relax) and 40 Å (metals). NiCl₂ k15 vs k25: 0.4 meV/atom |
| Smearing | Marzari–Vanderbilt 0.01 Ry (metals and magnetic chlorides) |
| Magnetism | spin-polarised; FM start (Fe²⁺ 4 µB, Co²⁺ 3 µB, Ni²⁺ 2 µB); interlayer-AFM supercell (A1 = a1−a2, A2 = a2−a3, A3 = 2a3) in stage `mag` |
| Convergence | SCF 1e-9 Ry (1e-8 for conv tests, 1e-7 for chloride vc-relax); BFGS etot 1e-5 Ry, force 1e-4 Ry/bohr, press 0.5 kbar |
| Structures | CdCl₂-type R-3m MCl₂ (3-atom primitive); NaCl rocksalt; bcc Na and Fe; fcc Ni; hcp Co; Cl₂ in a 12 × 12.5 × 13 Å box |
| Inputs / outputs | `../raw_results/<stage>/<job>/job.in, job.out, STATUS, wall.txt, cmd.txt`; log `../raw_results/campaign.log` |
| Analysis | `analyze.py` → `../validation/s11_results.json`, `s11_voltage_vs_U.png`, `s11_pdos.png`. Band gaps by electron counting on the SCF k-mesh (`campaign.band_gap`) |
| Relaxed structures | `../structures/*.cif` |

## Key results (all numbers: `RESULTS.md`, generated from `../validation/s11_results.json`)

1. **Plain PBE (U = 0) gets the salt-cathode voltages to within +0.11 to +0.27 V** of the experimental enthalpy-based values: FeCl₂ 2.60 vs 2.49 V, CoCl₂ 2.92 vs 2.64 V, NiCl₂ 2.85 vs 2.68 V [SIMULATED vs PUBLISHED]. It ranks Fe below Ni correctly. It ranks Co and Ni the wrong way round, but they are only 0.04 V apart in experiment, below the method error.
2. **Why the voltages beat the formation enthalpies.** Formation enthalpies are off by 0.3 eV (NaCl) to 1.2 eV (CoCl₂) per formula unit, largely from the PBE Cl₂ molecule. The cell reaction 2 Na + MCl₂ → 2 NaCl + M contains no Cl₂, so that error cancels. The Na + ½Cl₂ couple does contain it: 3.92 V vs 4.26 V.
3. **Adding U makes these voltages worse.** Each eV of U on the chloride raises the voltage by 0.1–0.2 V, because the metal reference stays at U = 0. Using the U = 0 or U = 4 eV geometry changes the voltage by ≤ 0.02 V, so the mixing of energies, not the structure, causes it. Using U would need a fitted mixing correction (Materials-Project style), which was not attempted. **Screen these couples with U = 0.**
4. **Electronic structure.** NiCl₂ and CoCl₂ are insulators once U is applied: 2.4 and 2.9 eV at U = 4 eV on the SCF mesh. FeCl₂ (Fe²⁺ d⁶) stays metallic in the symmetric 3-atom cell at every U; opening its gap needs an orbital-ordered, lower-symmetry cell, which was not run. This is a limitation, not a prediction. With U = 4 eV the top 1 eV of the NiCl₂ and CoCl₂ valence band is 85 % and 75 % Cl-3p (charge-transfer character); at U = 0 it is ~75 % metal-3d (`s11_pdos.png`). So the electrons removed on charging come largely from Cl-3p states in the +U description; which description is closer to reality is an experimental question (XAS), not settled here.
5. **Magnetic order.** Interlayer antiferromagnetic order (each layer ferromagnetic) is lower in energy than all-ferromagnetic, by only a few meV per formula unit, in every chloride and U tested. That matches the known magnetic structure of these layered dichlorides. A few meV per formula unit, shared over two electrons, is ≤ 2–3 mV of cell voltage. That is far below the 0.1–0.3 V method error, so the voltages above do not depend on the magnetic order.
6. **Lattices** are within −3.2 % (bcc Na; D3 over-binds the alkali metal) to +1.1 %.

**What this means for the programme.** DFT here is a check on thermodynamics, not a discovery engine. It confirms that the salt–iron and salt–nickel couples sit at 2.5–2.9 V vs Na, and that standard PBE is good enough to screen dopants or mixed-metal chlorides for the S-cell. It cannot say anything about kinetics, ceramic separator survival or cycle life. Those are the gates G1–G5 in the R0 build.

## Failure log
1. Ubuntu-apt QE 6.7 crash on EC2 (earlier session) → conda-forge QE.
2. First k-mesh (40 Å for chlorides) was too slow (22 s per SCF step) → stopped and re-planned.
3. A duplicate runner (20:29–20:33) corrupted the Cl₂ job → re-queued; a lock file was added.
4. Chloride vc-relax at 4 U values was too slow → vc-relax at U = 0 and 4 only, plus a fixed-geometry U-scan.
5. **QE 7.6 (conda) segfaults in the optional final SCF after a converged vc-relax** (same bug as on EC2). BFGS-converged energies and geometries are used; STATUS records this.
6. The session running the campaign was cut off at 21:17 IST on 2 Nov, killing the two NiCl₂ relaxations mid-run → re-queued.
7. The runner skipped only jobs whose STATUS was exactly `DONE`, so it would have re-run the `DONE bfgs-converged` jobs → fixed (prefix test).
8. The founder asked for heavy work to move off the laptop (3 Nov 03:10 IST) → local runs stopped; Ni_fcc had already finished locally. The remaining 44 jobs ran on EC2 between 21:44 and 22:05 UTC (≈ 21 min, 0 failures) for ≈ $0.15 at the $0.45/h price ceiling (cost watchdog log in `../raw_results/ec2_logs/`).

## Not done
Band structures along high-symmetry paths, defects and NEB (NaCl vacancy migration), the Na₆FeCl₈ intermediate phase, Na⁺ migration in β''-alumina and MD, plus an orbital-ordered (symmetry-broken) FeCl₂ cell to open its gap. All are listed in `00_START_HERE/BUILD_STATUS.md` as next computations.
**A converged calculation does not show that any material is synthesisable** — and here every phase is a known, synthesised compound.
