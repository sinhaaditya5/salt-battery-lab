# Salt Battery Lab (external SSD)

A complete, rebuildable study of a water-based sodium battery startup idea. It covers:
- the YC W27 application;
- simulations, an atomistic screen and a DFT+U check on AWS;
- cost and market models;
- concept CAD, drawings, PCB and renders;
- an investor deck, report and one-pager;
- a go/no-go memo.

**Stage:** pre-prototype. No cell has been built. Every number is tagged [LIT], [VENDOR], [CALC], [SIM], [ASSUMPTION] or [TARGET] and resolves in `CLAIMS_LEDGER.csv`.

**Verdict** (`DELIVERABLES/STARTUP_DECISION_MEMO.md`): no-go on a factory company today. Go-with-conditions on a 12-week falsification sprint that starts with a near-free buyer test. The alternative wedge is battery fire-code / hazard-analysis software.

## Deliverables (`DELIVERABLES/`)

| Folder | Contents |
|---|---|
| `0_YC_APPLICATION` | `YC_W27_answers.md` (v2, corrected), founder video script, submit checklist |
| `1_investor_docs` | `SaltBattery_Investor_Deck.pptx/.pdf` (28 slides, speaker notes), `SaltBattery_Technical_and_Business_Report.docx/.pdf`, `SaltBattery_OnePager.pdf`, `SaltBattery_Financial_Model.xlsx` (live formulas) |
| `2_video` | Turntable MP4 (if rendered) |
| `3_cad_3d` | STEP/STL/GLB: R0 test cell, R1 12 V block, 48 V tray, UPS cabinet; part lists |
| `4_engineering_drawings` | CADCraft drawings (DXF/PDF/PNG), concept only |
| `5_pcb` | KiCad BMS/monitor board: ERC/DRC reports, Gerbers, drill, BOM, 3D renders |
| `6_prototype_images` | Blender concept renders, plain and annotated |
| `7_simulation_charts` | Every chart, as PNG 300 dpi + SVG + a caption carrying claim tags |
| `8_diagrams` | Nine diagrams: architecture, process, capex, validation ladder, safety, positioning, unit economics, roadmap, use of funds |
| `9_data` | Result JSONs, `CLAIMS_LEDGER.csv`, `TEST_REPORT.md` |
| `10_data_room` | `Data_Room_Index.md`, decision docs, sources, grants list, outreach pack (nothing sent) |
| `11_screenshots` | Console snapshots and images captured while running tests, simulations, Blender, KiCad, DFT and document QA |
| `STARTUP_DECISION_MEMO.md` | Go/no-go, proven vs simulated vs assumed, cheapest experiment, first 90 days |


## Project Salt extension (2 Nov 2026, second brief): `PROJECT_SALT/`

**Start at `PROJECT_SALT/00_START_HERE/EXECUTIVE_VERDICT.md`.**

**Outcome B:** no salt-derived chemistry meets 360 Wh/kg + 5-min / 1,500 km + $3 + non-flammable. The closest candidates are:
- N08 anode-free Na solid-state (energy);
- S03 salt-iron molten-salt cell (salt is the active material);
- N02 NFPP Na-ion (balance; commercial, no novelty).

| New piece | Where | Rebuild |
|---|---|---|
| S11 DFT(+U) on Na/NaCl/Cl2/Fe-Co-Ni chlorides: relax, U-scan, FM/AFM, gaps, PDOS (QE 7.6; local M4 + EC2 c8g.8xlarge) | `sim/s11_dft_chlorides` | `campaign.py write/run <stage>`; `analyze.py`; EC2: `ec2/ec2_s11.sh push/status/pull` |
| S12 30-architecture feasibility matrix (calibrated build-up, Pareto, ranking) | `sim/s12_chemistry_matrix` | `matrix.py` |
| S13 founder targets ($3 ×6, 1,500 km / 5 min, salt feedstock) + PyBaMM fast charge/degradation | `sim/s13_founder_targets` | `targets.py`; `fast_charge_pybamm.py` (~10 min) |
| S14 salt-iron cell model; S15 factory scenarios + tornado | `sim/s14_scell_model`, `sim/s15_factory` | scripts |
| S-cell R0 CAD + drawing SB-SC-001 | `cad/make_scell.py`, `params/scell_params.py` | `python cad/make_scell.py` |
| SCM-1 test-monitor KiCad (ERC 0; layout DRAFT) + firmware core | `pcb/scell_monitor` | `pcb/build_scm.sh`; `make -C pcb/scell_monitor/firmware test` |
| Package assembly (BOM, ledger, status, manifest) | `tools/project_salt/` | `assemble.py` |
| **v1.1** D3 P1 cell + SM-48T 48 V module, D4 thermal (S16), D5 SC-UPS-1 cabinet: STEP, part lists, CADCraft drawings SB-SM-001/SB-TM-001/SB-UPS-001 | `cad/make_smodule.py`, `params/smodule_params.py`, `sim/s16_module_thermal` | `python cad/make_smodule.py` |
| **v1.1** Blender renders + turntable of the salt designs | `renders/blender_salt.py` → `renders/out_salt` | `python renders/run_salt_renders.py` |
| **v1.1** Diagrams ds1–ds5, MATLAB stem scripts (run with Octave) | `diagrams/make_salt_diagrams.py`, `tools/matlab/make_stem.py` → `matlab/stem` | `--run` executes the .m files |
| **v1.1** SaltIron_Engineering_Model.xlsx (live formulas, LibreOffice-verified) | `finance/make_salt_model.py` → `PROJECT_SALT/10_ECONOMICS` | `python finance/make_salt_model.py` |
| **v1.1** Complete technical record (.docx/.pdf) and deck (.pptx/.pdf) | `docs/make_full_report.py`, `docs/make_full_deck.py` → `DELIVERABLES/1_investor_docs` | run on the build host |
| **v1.1** EC2 x86 build host (all heavy work since 3 Nov 03:10 IST) | `tools/ec2_build/` | `ec2_build.sh push / bootstrap / bg / pull`; `rebuild_salt.sh` |

`./run_all.sh` now runs all of the above. `--fast` skips the PyBaMM S13a runs. QE jobs are never re-run automatically.

## Rebuild

```bash
source "/Volumes/Aditya ssd/Salt-Battery-Lab/tools/env.sh"
./run_all.sh --fast     # ~15 min: reuses ML-potential runs and renders
./run_all.sh            # full: also re-runs the uMLIP screen (~1 h) and Blender renders
```

`run_all.sh` never launches EC2. DFT results are re-analysed from `sim/s06_dft_ec2/runs*/` and `sim/s11_dft_chlorides/runs/`. To run DFT again, launch with `sim/s06_dft_ec2/launch.sh` (per-job overrides `S06_HARD_HOURS`, `S06_CAP_USD`, `S06_ITYPE`), then `sim/s11_dft_chlorides/ec2/ec2_s11.sh push`; finish with `sim/s06_dft_ec2/terminate.sh`. It costs money and needs founder approval.

## Layout

```
00_source_kit/   untouched, read-only kit copy (50/50 SHA256 verified)
params/          single source of truth: product_params.py (tagged values), design.py (derived geometry/mass/energy)
sim/s01…s10/     one folder per simulation: README, code, out/
research/        sources.csv (164 rows), RESEARCH_NOTES.md, COMPETITORS.csv, GRANTS_AND_FUNDING.md
decisions/       IDEA_v2.md, DECISIONS.md, RED_TEAM.md, chemistry matrix
cad/ drawings/ renders/ pcb/ diagrams/ finance/ docs/   generators
tests/           pytest suites (params, models, document linter, CAD, PCB)
tools/           env.sh (all caches on the SSD), plotstyle, snap.py (console → PNG), assembly, AWS helpers
```

## Environment

- Everything lives on the SSD (`tools/env.sh`).
- Software: Python 3.12 venv (`.venv`), PyBaMM 26.10, MACE / CHGNet, build123d, Blender 5.0.1, KiCad 10, CADCraft, LibreOffice 26.8 (installed from the SSD image into `/Volumes/Aditya ssd/Applications`).
- AWS: the DFT job used the founder-approved envelope (c8g.8xlarge spot, Mumbai, $25 cap, 48 h hard stop).
- **Delete the AWS root access key after the run.**
