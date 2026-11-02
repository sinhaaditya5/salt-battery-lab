# S6: DFT+U check on AWS (optional; founder-approved)
**Approval:** Founder, 2 Nov 2026. Ubuntu 24.04 arm64; c8g.8xlarge spot in ap-south-1; $25 cap; 48 h hard stop; cost watchdog; root key used for this job only. **Rotate the key afterwards.**
**Software:** Ubuntu's apt QE 6.7 aborts on noble ("buffer overflow detected", fortify). Conda-forge **QE 7.6** was used instead.
**Settings:**
- PBE+U (Mn 3.9 eV, Fe 5.3 eV; atomic projectors); GBRV USPP; 40/240 Ry.
- Spin-polarised, ferromagnetic start.
- Grimme-D3 for the hydrated birnessite.
- Screening k-grids.
**Jobs:**
- `jobs/`: vc-relax of every validation end member and the birnessite models.
- Mn-vacancy proxy at fixed cell.
- Static DFT on the MACE NEB images (`make_qe_inputs.py relax|neb`).
**Known issue:** QE 7.6 (conda) segfaults in the *optional* final fresh-basis SCF after vc-relax. The BFGS-converged energies are used and flagged as "bfgs-converged; final SCF crashed".
**Scripts:**
- `launch.sh`, `cloud_init.sh` (hard stop + watchdog), `run_queue.sh`
- `sync_up.sh`, `sync_back.sh [--loop]`, `status.sh`
- `terminate.sh` (also deletes the key pair and security group)
**First result:** LiFePO₄ 3.75 V vs 3.45 V literature (+0.30 V) [C-114]. This is consistent with QE atomic-projector U being stronger than the VASP-calibrated value. Treat the DFT numbers as screening.
