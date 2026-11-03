# Salt Battery: co-founder pack (3 Nov 2026)

This folder holds everything built so far for the Salt Battery idea: the deck and reports, the YC application, spreadsheets, 3D CAD, engineering drawings, Blender renders, KiCad boards, charts, diagrams and screenshots.

**Stage: pre-prototype.** No cell, module or circuit board has been built, so nothing in here is measured. Every number carries a tag that says where it came from:

| Tag | Meaning |
|---|---|
| [LIT] / [PUBLISHED] | from a paper, standard or report |
| [VENDOR] / [VENDOR CLAIM] | a company's own claim |
| [CALC] / [CALCULATED] | our arithmetic or model |
| [SIM] / [SIMULATED] | our simulation |
| [ASSUMPTION] | our assumption |
| [TARGET] | a goal, not a result |

Each tagged number traces to a row in the two claims ledgers in folder `01`.

## Read these three first (about 30 minutes)

1. `02_Pitch_Deck_and_Reports/A_LATEST_complete_record_3Nov/SaltBattery_Complete_Technical_Deck.pdf`: 23 slides, the whole story.
2. `01_Start_Here_Verdict_and_Decisions/EXECUTIVE_VERDICT.md`: can a battery made from salt meet the original targets?
3. `01_Start_Here_Verdict_and_Decisions/STARTUP_DECISION_MEMO.md`: go / no-go on the first business idea.

For full detail, read `SaltBattery_Complete_Technical_Record.pdf` (48 pages, same folder as the deck).

## Two tracks were studied

- **Track A, "Project Salt" (latest, 2–3 Nov).** Batteries where common salt is the active material: a molten salt-iron cell (R0 test cell, P1 cell), a 48 V module (SM-48T) and a 3-module backup cabinet (SC-UPS-1). Folders are marked `A_..._LATEST`.
- **Track B, the first pitch (2 Nov).** A water-based sodium-ion battery for indoor UPS backup in India. Folders are marked `B_..._first_pitch`.

## Bottom line so far

- **The original targets cannot all be met.** No chemistry made from salt reaches 360 Wh/kg together with a 5-minute charge for 1,500 km, $3 cost and non-flammability. The best salt-derived cell reaches about 259 Wh/kg (P50) [CALC]. A 5-minute, 1,500 km charge needs about 3.8 MW, roughly 3× the best charger in service [CALC].
- **Salt-iron 48 V module (Track A):**
  - stores 2.27 kWh and weighs about 80 kg, so 28 Wh/kg [CALC];
  - materials alone cost about $970/kWh [CALC];
  - keeping it at 190 °C costs about 20 W, or 21 % of its stored energy per day [SIM];
  - a full discharge at maximum power takes about 1.7 h [SIM]. That suits 2–8 hour telecom backup, not 15-minute data-centre UPS.
- **Water-based UPS battery (Track B):** its 12 V block stores 17.6 Wh/kg [CALC] and costs about $350/kWh to make [CALC], against $70/kWh for LFP lithium packs [LIT]. The memo's verdict:
  - **no-go** on a battery factory company today;
  - **go-with-conditions** on a 12-week falsification sprint (≤ ₹10 lakh) that starts with buyer interviews.
- **No defensible invention at the chemistry level.** Every design examined has close prior art (`11_.../01_SCIENTIFIC_RESEARCH/patent_landscape.csv`). The memo names battery fire-code / hazard-analysis software as the stronger alternative company.

## Folder map

| Folder | What is inside |
|---|---|
| `01_Start_Here_Verdict_and_Decisions` | Verdict, decision memo, build status, known limitations, independent review, changelog, both claims ledgers, decision log and red-team notes |
| `02_Pitch_Deck_and_Reports` | **A:** latest deck (.pptx/.pdf) and complete technical record (.docx/.pdf). **B:** first investor deck (28 slides), business report, one-pager. Read `READ_FIRST_Deck_Errata.md` before showing deck B |
| `03_YC_Application` | YC W27 answers v3, plus the v4 changes to apply on top of it, the submit checklist, the founder video script, the company thesis and the evidence register |
| `04_Spreadsheets_and_BOMs` | `SaltIron_Engineering_Model.xlsx` and `SaltBattery_Financial_Model.xlsx` (live formulas), procurement BOMs (India/US suppliers, equipment), part lists, electronics BOM |
| `05_3D_CAD_Engineering_Designs` | STEP / STL / GLB models. **A:** R0 test cell, P1 cell, SM-48T module (assembled, exploded, cutaway), SC-UPS-1 cabinet, thermal design, parametric source scripts. **B:** R0/R1 cells, 12 V block, 48 V tray, UPS cabinet |
| `06_Engineering_Drawings_CADCraft` | PDF + DXF + PNG. **A:** SB-SC-001, SB-SM-001, SB-TM-001, SB-UPS-001. **B:** SB-GA-001 to 003 |
| `07_Blender_Renders_and_Video` | **A:** 8 renders, each plain and captioned, plus the module turntable video. **B:** 7 renders, each plain and annotated. **C:** narrated explainer video with subtitles |
| `08_PCB_KiCad` | **A:** SCM-1 salt-cell test monitor: KiCad 10 project, fabrication files, check reports, firmware. **B:** BMS monitor board from the first pitch |
| `09_Charts_and_Simulations` | Every simulation chart (PNG + SVG + caption with tags) and its result data. **A:** s11–s16. **B:** s02–s10. **C:** 9 MATLAB stem plots with their .m scripts |
| `10_Diagrams` | **A:** ds1–ds5 (cell chemistry, module wiring, thermal budget, P1 manufacturing flow, pass/kill gate ladder). **B:** d1–d9 (architecture, process, capex, validation ladder, safety, positioning, unit economics, roadmap, use of funds) |
| `11_Technical_Package_Project_Salt` | Deep-dive documents: research and patents, DFT chemistry, electrochemical models, procurement, step-by-step build manual, manufacturing, test protocols, economics, market. Also holds the R0 test-cell build kit (.zip) |
| `12_Research_and_Data_Room` | 201 logged sources, research notes, competitors, grants (India/US), data-room index, outreach pack (draft; nothing has been sent), papers and datasheets |
| `13_Screenshots` | Captures from simulations, tests, Blender, CAD, DFT on AWS, document checks, KiCad and the spreadsheet |
| `FILE_LIST.csv` | Every file with its size and SHA-256 checksum, to confirm nothing was lost in transfer |

## Not finished yet

- **Circuit boards are drafts. Do not order them.**
  - SCM-1: the schematic passes its electrical check with 0 errors. The board layout still has 37 unrouted connections and 185 design-rule errors, so its Gerber files are for review only.
  - The first-pitch BMS board has 98 unrouted connections.
  - Both boards need hand placement and routing.
- **The salt-iron cell model has a gap.** It reports 100 % capacity use at every electrode loading, so it cannot predict the loading pass/fail test (gate G2). Only building the R0 test cell can answer that.
- **MATLAB.** No MATLAB licence was available. The `.m` scripts were run with GNU Octave and are written to MATLAB syntax, but they have not been run in MATLAB itself.
- **Renders** were made on a CPU, not a GPU, at preview quality.
- **Track B documents are older** than Track A. The deck errata file lists what changed.
- **Not included here:** raw DFT output files (about 48 MB), the rebuild scripts and the software toolchain. They stay in the lab repository and can be shared on request.

## Opening the files

| File type | Open with |
|---|---|
| .pdf | any PDF reader. Every document has a PDF copy |
| .pptx / .docx / .xlsx | PowerPoint / Word / Excel, LibreOffice or Google Drive |
| .step | FreeCAD (free), Fusion 360, SolidWorks or Onshape |
| .stl / .glb | any 3D viewer or slicer, Blender, or Windows 3D Viewer |
| .dxf | AutoCAD, LibreCAD (free) or DraftSight. PDF copies sit beside them |
| .kicad_pro | KiCad 10 (free). Gerber files open in any Gerber viewer |
| .md / .csv / .json | any text editor. .csv also opens in Excel |
| .svg / .png / .mp4 | a web browser or any image / video player |
