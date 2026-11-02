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

## Rebuild

```bash
source "/Volumes/Aditya ssd/Salt-Battery-Lab/tools/env.sh"
./run_all.sh --fast     # ~15 min: reuses ML-potential runs and renders
./run_all.sh            # full: also re-runs the uMLIP screen (~1 h) and Blender renders
```

`run_all.sh` never launches EC2. DFT results are re-analysed from `sim/s06_dft_ec2/runs*/`. To run DFT again, see `sim/s06_dft_ec2/README.md`; it costs money and needs founder approval.

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
