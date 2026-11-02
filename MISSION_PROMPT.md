# MISSION PROMPT — Salt Battery: from idea to an investor-ready, YC-ready startup package

Paste this whole file into a fresh Claude Code session started in `/Volumes/Aditya ssd/Salt-Battery-Lab`.
Prompt written 2 Nov 2026. Facts in section 2 were web-verified that day; re-verify before quoting.

---

## 1. Who you are working for and what "done" means

You are the technical co-founder, research engineer and analyst for a solo founder applying to
**Y Combinator Winter 2027**. The founder has a research kit for a "salt battery" (aqueous
sodium-ion; reference chemistry is sodium-birnessite from Shan et al., *Nat. Commun.* 2019).
No cell has been built or tested yet.

Your job, in this order:
1. Produce the YC application text **first**, because the deadline is hours away (section 3).
2. Run software tests and simulations with open-source tools, all on the external SSD.
3. Stress-test the idea and improve it. You are allowed to change the product, chemistry,
   market wedge and positioning. Record every change and the reason for it.
4. Turn the results into claims that hold up under scrutiny, each tagged with its evidence type.
5. Design the prototype: CAD (build123d → STEP), engineering drawings (CADCraft), PCB (KiCad),
   photoreal renders (Blender), plus charts and diagrams.
6. Build an investor-ready **.docx report**, **.pptx deck**, one-pager, financial model and data
   room containing all the tests, images, charts, diagrams, designs and simulation results.
7. Finish with an honest **go/no-go decision memo**: should the founder start this company, and
   what is the cheapest experiment that would change that answer?

"Done" means every deliverable in section 9 exists, `run_all.sh` rebuilds it from source, all
tests pass, and every number in the deck traces to a row in `CLAIMS_LEDGER.csv`.

---

## 2. Verified facts snapshot (2 Nov 2026). Start from these; do not re-derive them.

### Prior validation verdict (from the previous session)
- Rebuilding the R0 cell is **possible**. It is a published, open-access result, and a
  university battery lab can reproduce it.
- A sodium battery business is **possible but crowded**.
- **5× energy density, 1,500 km range and 5-minute charging are not possible** with this chemistry,
  and no sodium chemistry has come close.
  - Commercial Li-ion cells are about 250–300 Wh/kg, so 5× means 1,250–1,500 Wh/kg.
  - Water's thermodynamic window is about 1.23 V, which caps aqueous cell voltage.
  - 1,500 km in 5 minutes needs 225–300 kWh delivered at 2.7–3.6 MW. The kit's own
    `moonshot_requirements.py` computes this.
  - The fastest car charger is about 1 MW (BYD).
- **Drop every EV, drone, 5× and 1,500 km claim permanently.**
- Weak points inside R0:
  - Electrode loading is about 2.8 mg/cm² (5 mg on a 15 mm disc), against roughly 15–25 mg/cm²
    in commercial electrodes.
  - The 83 mAh/g figure counts only electrode material.
  - The symmetric-cell layout is a research setup, not a product.
  - The 2.5 V test window is about twice water's stability limit, so expect gas and Mn dissolution.
  - It is ambiguous whether the per-gram basis is one electrode or both.

### Market and competition (cite these in the docs, after re-checking)
- **CATL Naxtra** sodium-ion: about 175 Wh/kg cell, in passenger cars in 2026.
  https://electrek.co/2026/04/22/catl-launching-sodium-ion-batteries-evs-2026/
- **Gotion "Gnascent"** sodium-ion: up to 261 Wh/kg claimed (company claim).
  https://carnewschina.com/2026/05/17/volkswagen-backed-gotion-launches-gnascent-sodium-ion-battery-up-to-261-wh-kg-with-mass-production-ready/
- **Peak Energy** (US, non-aqueous sodium-ion, passively cooled grid BESS):
  - $108M Series B led by GM Ventures, Oct 2026: https://www.pv-magazine.com/2026/10/23/sodium-ion-storage-maker-peak-energy-raises-108-million-in-gm-led-round/
  - Up to 4.75 GWh contracted with Jupiter Power for 2027–2030.
  - 4 GWh factory: https://www.ess-news.com/2026/07/09/peak-energy-to-build-4-gwh-grid-scale-sodium-ion-bess-factory-in-california/
- **Alsym Energy** (US): water-based, manganese-oxide, non-flammable; $78M Series C (2024).
  This is the closest direct competitor.
  https://www.energy-storage.news/non-lithium-cobalt-free-ess-battery-startup-alsym-energy-tight-lipped-on-product-chemistry/
- **Offgrid Energy Labs** (India): non-flammable zinc-based battery, $15M Series A.
  https://themachinemaker.com/news/offgrid-energy-labs-raises-usd-15-million/
- **Aquion Energy** (aqueous sodium "saltwater"): bankrupt in 2017.
  - About 15× heavier/bigger per kWh than Li-ion; the bill of materials killed it.
  - Its module works out to about 17 Wh/kg (26 kWh / 1,504 kg including the rack).
  - https://greentechmedia.com/amp/article/aquion-the-bill-gates-and-kleiner-perkins-funded-advanced-battery-startup
  - https://www.technologyreview.com/2017/08/08/150080/inside-the-fall-and-rebirth-of-a-bill-gates-backed-battery-startup/
- **Natron Energy** (sodium-ion, Prussian blue): shut down Sept 2025 after lithium prices fell.
  https://spectrum.ieee.org/natron-sodium-ion-battery-failure
- **BNEF 2025:**
  - Stationary-storage Li-ion pack average $70/kWh, the lowest of any segment.
  - Lowest LFP cell $36/kWh; turnkey BESS $117/kWh.
  - About 3% further decline expected in 2026.
  - https://www.energy-storage.news/li-ion-battery-pack-prices-fell-8-since-last-year-despite-metals-prices-rising-bloombergnef-says/
  - https://www.energy-storage.news/battery-storage-system-prices-continue-to-fall-sharply-bnef-and-ember-reports-find/
  - **Consequence: you cannot win on cell $/kWh against LFP. Compete on installed cost under
    fire-code constraints, safety, and levelized cost of storage (LCOS).**
- **India storage market:**
  - 281 GWh tendered as of H1 2026; 8.2 GWh added in H1 2026.
  - New VGF round for 30 GWh approved 14 May 2026.
  - Cell manufacturing is nascent; most cells are imported.
  - https://www.ess-news.com/2026/09/14/india-adds-8-2-gwh-of-new-bess-capacity-in-h1-2026/
- **Fire codes:**
  - NFPA 855:2026 tightened indoor lithium-ion rules (thresholds per fire area, dedicated rooms).
  - Fire and Rescue NSW requires 240-minute fire-resistant rooms for Li-ion in data centres.
  - FM Global DS 5-32 applies to rack batteries.
  - Thresholds conflict between sources (20/50/600 kWh); verify against primary text.
  - https://www.energy-storage.news/nfpa-855-2026-edition-updates-and-what-they-mean-for-energy-storage-projects/
  - https://www.energy-storage.news/fire-and-rescue-nsw-mandates-240-minute-fire-resistance-for-lithium-ion-battery-storage-rooms-in-data-centres/
- **India funding leads (verify each):**
  - ENTICE 3.0 grants for non-lithium storage: https://www.pulse.bot/emerging-markets/news/indias-entice-30-challenge-offers-100000-grants-for-nonlithium-storage-and-ai-grid-solutions-81a64394-5c09-44cb-b987-640909629746/
  - RDI Fund (₹1 lakh crore), which has backed a battery startup: https://yourstory.com/2026/05/india-rdi-fund-first-deep-tech-startups-funding
  - IIT incubators; ANRF/DST/NIDHI.

### Tools and science facts
- **PyBaMM** has `pybamm.sodium_ion.BasicDFN` with the `Chayambuka2022` parameter set. The
  lithium-ion DFN/SPMe models can take sodium parameters.
  https://www.ionworks.com/blog/sodium-ion-battery-model-now-available-in-pybamm
- **Universal ML interatomic potentials** (MACE-MP-0, CHGNet, Orb, SevenNet) are benchmarked as
  usable zero-shot screens for alkali-ion migration barriers.
  - MACE-MP-0 and Orb-v3 have the lowest errors; good/bad conductor classification is above 82%.
  - https://arxiv.org/html/2512.03642v1
  - https://arxiv.org/pdf/2601.10938
- **Quantum ESPRESSO** on conda-forge has **no osx-arm64 build** (linux-64, osx-64 and
  linux-aarch64 only). DFT+U is therefore an EC2 job (section 4).
- **R0 paper:**
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC6823464/ (CC BY 4.0; figures may be reused with attribution).
  - The Ragone-plot energy counts "mass of electrode materials" only.
  - The full-cell slurry solvent/binder is not specified.

---

## 3. DEADLINE FIRST: Phase 1 is the YC application (finish within about 2 hours)

- **YC W27 deadline: Mon 2 Nov 2026, 8:00 pm PT = Tue 3 Nov 2026, 9:30 am IST.**
- Late applications are still reviewed, but YC does not guarantee timing.
- Verify the deadline at https://www.ycombinator.com/apply before anything else.

Do this before any simulation work:

1. Fetch the **current** YC application questions and YC's own guidance pages from
   ycombinator.com (application, "how to apply", the Request for Startups). Use YC's own pages,
   not blogs.
2. Write `DELIVERABLES/0_YC_APPLICATION/YC_W27_answers.md` with one answer per question, copy-paste
   ready, within YC's length limits. Use only facts from section 2 plus the kit.
   - Be plainly honest about the stage ("pre-prototype; literature reproduction planned").
   - YC partners reward clarity, a sharp insight, founder determination and a concrete
     riskiest-experiment plan. Include:
     - the riskiest assumption;
     - the first experiment and its cost/time;
     - what result would kill the idea.
3. Write `YC_founder_video_script.md`: a 1-minute script for the founder to record. The founder
   must record it; you cannot.
4. Write `YC_SUBMIT_CHECKLIST.md`: account, co-founder fields, equity, entity (none yet is fine),
   video upload, links.
5. **Stop and tell the founder: "YC answers are ready at …; submit before 9:30 am IST
   3 Nov. You can update the application later as results come in."** Then continue to Phase 2.
   Do not wait for a reply. Update the answers at the end if the work changes the story.

---

## 4. Ground rules (non-negotiable)

### Storage and environment
- **SSD only.** Every download, install, cache, venv, model weight, temp file and output goes
  under `/Volumes/Aditya ssd/`. Never install to the Mac internal disk (it is small).
- Create `tools/env.sh` by copying the pattern from
  `/Volumes/Aditya ssd/PARC-Delta-Lab/tools/env.sh`. Point these at the SSD:
  - `XDG_CACHE_HOME`, `UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR`
  - `PIP_CACHE_DIR`, `HF_HOME`, `TORCH_HOME`
  - `MPLCONFIGDIR`, `npm_config_cache`
  - `BLENDER_USER_RESOURCES`, `TMPDIR`
  - `CONDA_PKGS_DIRS` and `MAMBA_ROOT_PREFIX` (if you use micromamba, install it on the SSD).
  - `source tools/env.sh` in every shell.
- **Reuse existing SSD tools; do not re-download them:**
  - Blender 5.0.1: `/Volumes/Aditya ssd/Applications/Blender.app/Contents/MacOS/Blender`
  - KiCad: `/Volumes/Aditya ssd/Applications/KiCad/KiCad.app` (use `kicad-cli` inside the bundle for ERC/DRC/exports)
  - CADCraft CLI: `/Volumes/Aditya ssd/PARC-Delta-Lab/tools/cadcraft/target/release/cadcraft-cli`
  - uv-managed Python 3.12: `/Volumes/Aditya ssd/PARC-Delta-Lab/tools/python`
  - Rust toolchain, Docker, the LibreOffice installer (`tools/downloads/lo/lo.dmg`), and
    node packages in `PARC-Delta-Lab/tools/node`.
- Create a **new** venv for this lab. **Do not modify anything in `PARC-Delta-Lab`.** Read its
  `README.md` and its `prototype/` scripts as patterns:
  - `make_docx.js`, `make_deck.js`
  - `blender_scene.py`, `annotate.py`
  - `make_ga_drawing.py`, `run_all.sh`
- Free, open-source tools may be downloaded without asking. **Ask before anything that costs
  money** (EC2, paid APIs, paid data) **or is outward-facing** (sending emails, posting, submitting).

### Honesty and claims
- **No fabricated data, ever.** You cannot run wet-lab experiments, so there are no "our measured
  results". Simulations are simulations. Synthetic demo data never appears in investor material.
- Every claim gets exactly one tag, and the tag must appear next to the number in the
  docx/pptx (as a footnote or small label):
  - `[LIT]` peer-reviewed or primary-source fact, with citation
  - `[VENDOR]` company claim, not independently verified
  - `[CALC]` arithmetic from cited inputs
  - `[SIM]` our simulation, with model name, validation status and uncertainty band
  - `[ASSUMPTION]` our input, with range and justification
  - `[TARGET]` a goal, not a result
  - `[MEASURED]` is **forbidden** until real lab data exists.
- Banned phrases:
  - "zero risk", "cannot fail", "proven", "breakthrough"
  - "5×", "1,500 km", "EV-ready"
  - "patented" (unless filed), "partnership" or "LOI" (unless signed)
- No fake logos, testimonials, customers or team members.
- Keep and extend the kit's claim-control discipline (`yc/CLAIM_CONTROL_AND_EVIDENCE.md`).
- **Safety:** laboratory procedures stay at "qualified lab partner under EHS approval". Never
  write home-chemistry instructions.

### Reproducibility
- `git init` the lab. Commit at each phase end with clear messages.
- One single source of truth for design numbers: `params/product_params.py`. CAD, drawings, PCB
  ratings, simulations, cost model and docs all import from it. **No hand-copied numbers.**

---

## 5. Compute plan: Mac first, EC2 only if justified

The founder's Mac is an **Apple M4 (4 performance + 6 efficiency cores, 8-core GPU) with 16 GB RAM**.

| Workload | Run on |
|---|---|
| PyBaMM DFN/SPMe, equivalent circuit, thermal, LCOS/TEA, Monte Carlo | Mac (minutes) |
| ML interatomic potentials (MACE-MP-0 / CHGNet / Orb via ASE + pymatgen): relaxations, voltages, NEB on ≤ ~300-atom cells | Mac CPU (hours). Try MPS only after checking it matches CPU on a small test. |
| Small classical MD (LAMMPS from conda-forge osx-arm64, or ASE MD with a MLIP), water + Na⁺ in the interlayer | Mac (keep under about 2,000 atoms) |
| Blender Cycles renders (Metal GPU), KiCad, CADCraft, build123d | Mac |
| **DFT+U verification** (Quantum ESPRESSO, spin-polarized Mn, ~50–150 atoms) | **EC2.** There is no native Apple-Silicon QE build and 16 GB is tight. |

**EC2 rule:** only propose EC2 if an MLIP result supports a headline claim and needs DFT
confirmation. Before launching, **stop and ask the founder**, and give them:
- the instance type (e.g. a compute-optimized 64 vCPU / 128 GB instance, spot);
- estimated hours and cost;
- a cloud-init script (QE install from a Linux package, input files rsynced from the SSD);
- an auto-shutdown timer;
- the rsync-back command for results to the SSD.

DFT is optional. The package must be complete without it, with MLIP results labeled
"[SIM] uMLIP screen, not DFT-verified".

At the start, print a one-paragraph compute verdict to the founder. Expected: "Mac is enough for
everything except optional DFT+U".

---

## 6. Phase 0: setup (do this first, then Phase 1)

Lab root: `LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"` (already created; this file is inside it).

1. Copy the kit untouched, excluding `.DS_Store`:
   - from `/Users/aditya/CODING/startup_2/Salt_Battery_R0_Reference_Cell_Kit_v1/`
   - to `$LAB/00_source_kit/Salt_Battery_R0_Reference_Cell_Kit_v1/`
   - Verify every file against the SHA256s in its `BUILD_MANIFEST.json`.
   - Report mismatches or unlisted files. Do not "fix" them.
   - Make the copy read-only (`chmod -R a-w`).
   - Work only on copies in `work/`.
2. Create the layout:
   ```
   00_source_kit/   tools/   research/   decisions/   params/   sim/   tests/
   cad/   drawings/   pcb/   renders/   diagrams/   finance/   docs/   work/
   DELIVERABLES/{0_YC_APPLICATION,1_investor_docs,2_video,3_cad_3d,4_engineering_drawings,
                 5_pcb,6_prototype_images,7_simulation_charts,8_diagrams,9_data,10_data_room}
   CLAIMS_LEDGER.csv   README.md   run_all.sh
   ```
3. Write `tools/env.sh` and create the venv. Install with uv:
   - Simulation and science: `pybamm`, `pymatgen`, `ase`, `mace-torch`, `chgnet`, `numpy`,
     `scipy`, `pandas`, `matplotlib`, `pytest`
   - CAD and drawing: `build123d`, `ezdxf`
   - Documents: `python-docx`, `python-pptx`, `openpyxl`
   - Diagrams: `graphviz` (or render diagrams with matplotlib/SVG)
   - Put all model weights on the SSD.
4. Run the kit's own smoke tests on the copy (the macOS equivalents of
   `scripts/run_software_checks.ps1`). Confirm the outputs match the kit's `*_smoke_test.txt`
   and `cost_model_expected_block.txt`.

---

## 7. Phase 2: research refresh, then Phase 3: idea stress test and improvement

### Phase 2: research (web search; save every source to `research/sources.csv` with URL, date, claim, confidence)
- Competitors: chemistry, Wh/kg, $/kWh, funding, status. Include:
  - Alsym, Peak, CATL, BYD, HiNa, Gotion, Natron (dead), Aquion (dead),
  - Offgrid Energy Labs, Faradion/Reliance, KPIT sodium-ion, Indi Energy,
  - and any aqueous sodium players found in 2025–2026.
- Literature from 2023–2026 on **aqueous sodium-ion full cells at realistic loadings**:
  - Mn-oxide and birnessite cathodes; Mn/Fe Prussian-blue analogues;
  - NaTi₂(PO₄)₃ anodes; moderate-concentration "water-in-salt" electrolytes
    (avoid perchlorate oxidizers);
  - Mn-dissolution mitigation; bipolar stacking.
- Standards and certification for the chosen market:
  - IEC 62619, UL 1973, UL 9540 / 9540A, NFPA 855:2026;
  - Indian BIS / CEA requirements for stationary storage and data-centre / telecom UPS.
  - Read primary texts or official summaries for thresholds.
- Prices (cited, dated) for: MnO₂/Mn₃O₄/MnSO₄, Na₂SO₄, carbon black, current collectors, separator,
  casing, BMS, and LFP racks in India.
- Market sizing inputs:
  - India data-centre capacity growth; telecom tower backup;
  - commercial-building and apartment storage; UPS market.
- YC: the Request for Startups text for hard tech and energy, and YC energy/battery companies
  funded so far.

### Phase 3: stress test and improvement (write `decisions/IDEA_v2.md` and `decisions/DECISIONS.md`)
Recommended direction (you may overrule it with evidence): **"the battery you're allowed to put
indoors."** A water-based, non-flammable sodium battery for places where fire code or insurance
makes lithium expensive or forbidden:
- data-centre / telecom backup;
- indoor commercial and residential storage;
- hospitals and Indian urban buildings.

Sell on **installed cost including fire-protection, room, spacing and insurance costs, plus
LCOS**, not on cell $/kWh.

Evaluate at least these chemistry candidates in a weighted scoring matrix. Criteria:
- energy density (cell and system)
- cycle life
- rate capability
- $/kWh and LCOS
- safety (gas, toxicity)
- material availability in India
- manufacturability on existing lines (no dry room)
- IP freedom-to-operate risk
- distance from Alsym

Candidates:
- **A.** R0 symmetric Na-birnessite. Benchmark only.
- **B.** Asymmetric Na-birnessite or Na₀.₄₄MnO₂ cathode // NaTi₂(PO₄)₃/C anode in Na₂SO₄ (the
  Aquion lineage). Explain how you avoid Aquion's failure.
- **C.** Mn/Fe Prussian-blue-analogue cathode // NaTi₂(PO₄)₃ anode, moderate-concentration
  non-perchlorate electrolyte.
- **D.** Hybrid capacitor: Na-birnessite // activated carbon, for **UPS ride-through
  (5–15 minutes)**, where power, safety and cycle life matter more than energy density. Evaluate
  this wedge seriously.

Output:
- the chosen product ("R1"), with a datasheet-style target spec, every line tagged `[TARGET]`;
- the wedge market and its first customer profile;
- a **unique insight** statement (what we believe that competitors don't), or an honest
  statement that none was found;
- kill criteria;
- what changed from the kit and why.

---

## 8. Phase 4: simulations and tests

Each simulation has its own folder `sim/sNN_name/` containing:
- `README.md` (question, model, inputs with sources, validation, limits)
- code
- `out/` (CSV/JSON + PNG/SVG charts)

All of them import `params/product_params.py`.

| ID | Simulation | Must include |
|---|---|---|
| S1 | Kit re-run | All kit scripts on the copy; outputs compared to the kit's expected files |
| S2 | **Validation of the electrochemical model** | Run PyBaMM `sodium_ion.BasicDFN` + `Chayambuka2022`. Reproduce the published discharge curves/rates within stated tolerance before trusting any aqueous model. |
| S3 | R1 cell electrochemical model | PyBaMM DFN/SPMe (or an equivalent-circuit model where parameters are missing) with **parameter ranges** from literature. Rate capability, voltage curves, energy efficiency, sensitivity to loading (2.8 → 25 mg/cm²). Monte Carlo uncertainty bands. |
| S4 | Water-window / gas model | Nernst + Tafel overpotentials for HER/OER vs pH. Side-reaction current → gas volume per Ah and per cycle → sealed-cell pressure rise → vent design requirement. |
| S5 | Atomistic screen (uMLIP) | Build a birnessite-type Na_xMnO₂·yH₂O structure (and the chosen R1 cathode). Relax and compare the interlayer spacing to the paper's XRD. Compute average insertion voltages and Na migration barriers (NEB). Validation set: ≥ 3 compounds with literature voltage/barrier values; report error bars. If error is too large, say so. |
| S6 | (Optional, EC2) DFT+U check | Only for the claim S5 supports. Follow the section 5 rule. |
| S7 | Cell → module → rack build-up | Bottom-up mass/volume BOM: Wh/kg and Wh/L at cell, module and system level. Compare against LFP, CATL sodium-ion and Aquion on one chart. |
| S8 | Thermal and abuse model | Lumped + 1D/2D module heat model at 0.25C–2C (UPS rates for D). Show that there is no exothermic runaway chain for the aqueous system, and state honestly what failure modes remain (gas, leakage, Mn²⁺). |
| S9 | Techno-economics | Bottom-up $/kWh (materials from cited prices, yields, labour, energy, capex depreciation). **LCOS and installed cost vs LFP, including fire-protection/room/spacing costs.** Tornado sensitivity chart, break-even map, learning curve. The kit's `economics/cost_model.py` refusal logic stays: missing inputs become labeled assumption ranges, never silent defaults. |
| S10 | Market sizing | Bottom-up TAM/SAM/SOM for the wedge, every input cited |
| T | **Software tests** | `pytest` covering: unit tests for every model, conservation/mass-balance checks, regression against literature values, params-consistency test (CAD dimensions == params == docs), and a "no forbidden phrases / every number has a claim ID" linter over the generated docx/pptx text. Write `DELIVERABLES/9_data/TEST_REPORT.md` with pass/fail counts. |

Charts: one consistent style; readable in print and on screen; every chart's caption carries its
claim tags. Export PNG (300 dpi) and SVG.

---

## 9. Phase 5: prototype design, then Phases 6–8: claims, documents and handover

### Phase 5: design (all dimensions from `params/product_params.py`)
1. **CAD (build123d → STEP + STL + GLB):**
   - (a) the R0 lab test cell, using the known 15 mm electrode;
   - (b) the **R1 product cell** (pouch or prismatic, possibly bipolar stack), with vent;
   - (c) a **module** (e.g. 48 V nominal for telecom/data-centre, or a UPS cabinet for candidate D);
   - (d) a rack or cabinet.
   - Labelled parts and a part list.
2. **Engineering drawings (CADCraft CLI → DXF + PDF + PNG):**
   - general arrangement plus cell detail;
   - dimensions, tolerances marked "concept", title block, revision, "NOT FOR FABRICATION";
   - reuse the PARC-Delta `make_ga_drawing.py` pattern.
3. **PCB (KiCad 9 via `kicad-cli`):**
   - (a) **module BMS / monitor board**: per-series-group voltage sense, NTC temperature, shunt
     current sense, gas/pressure sensor input (aqueous-specific), CAN or RS-485, MCU, isolation
     where needed;
   - (b) optional **low-cost 8-channel cell-cycler / potentiostat board** for in-house testing.
     This is a real capital-saving story.
   - Schematic + PCB layout, **ERC and DRC with zero errors**, Gerbers, drill files, BOM CSV,
     3D render images.
4. **Blender renders** (reuse `blender_scene.py` / `annotate.py` patterns):
   - hero shot, exploded cell, cutaway showing the water-based electrolyte and vent;
   - module in rack; installed in a data-centre / telecom-shelter scene;
   - plain and annotated versions; a 20–30 s turntable MP4.
5. **Diagrams** (SVG + PNG):
   - system architecture; material process flow (precursor → powder → electrode → cell →
     module), with equipment;
   - manufacturing line concept (no dry room) and capex steps;
   - validation ladder (R0 → R1 → module → certification);
   - safety comparison vs Li-ion; competitive positioning map;
   - unit-economics waterfall; 18-month roadmap/Gantt with milestones and kill gates;
   - use-of-funds.
6. **Video (optional if time allows):** a 2–3 minute narrated explainer MP4 + SRT captions in
   `DELIVERABLES/2_video` (reuse the PARC-Delta video pattern).

### Phase 6: claims ledger and red team
- `CLAIMS_LEDGER.csv` columns: id, claim text, tag, value, unit, source/evidence file, confidence,
  where used (slide/page).
- Red-team pass with two critiques, written to `decisions/RED_TEAM.md`:
  - **(1)** a skeptical battery-industry investor (an ex-Aquion/Natron board member mindset);
  - **(2)** a YC partner reading for founder–market fit and the riskiest assumption.
  - Fix or remove every claim that fails.

### Phase 7: investor documents (`DELIVERABLES/1_investor_docs` and `10_data_room`)
- **`SaltBattery_Investor_Deck.pptx`**: 12–15 core slides plus appendix, with speaker notes.
  - Flow: title/one-liner → problem (fire-code pain, with numbers) → why now (NFPA 855:2026,
    India storage boom, sodium supply-chain maturity) → solution/product → **unique insight** →
    how it works → simulation evidence → prototype design renders → competition (honest, including
    Aquion's failure and Alsym) → business model and unit economics → market (bottom-up) →
    go-to-market wedge → roadmap with kill gates → team/hiring needs → the ask and use of funds.
  - Appendix: every simulation, test report, assumptions and the claims ledger.
  - Every slide uses real charts/renders from this lab, and every number carries a claim tag.
- **`SaltBattery_Technical_and_Business_Report.docx`**:
  - executive summary;
  - the full method/results of every simulation and test with figures;
  - chemistry decision matrix; design (CAD/drawings/PCB/renders); safety and hazard register;
  - certification path; manufacturing and scale-up; techno-economics and LCOS;
  - market; competition; risks and mitigations; IP strategy (prior-art/FTO search notes from
    Google Patents; nothing claimed as patented); 18-month plan; budget;
  - limitations and claims boundary; references.
- **`SaltBattery_OnePager.pdf`**, **`SaltBattery_Financial_Model.xlsx`** (live formulas, with an
  assumptions sheet linked to the claims ledger), `Data_Room_Index.md`, a lab-partner outreach
  pack (update the kit's `docs/OUTREACH_EMAILS.md`; **do not send anything**), and a grants and
  funding list for India and the US with deadlines (verified, dated).
- **QA:**
  - Convert docx/pptx to PDF with LibreOffice (install from the SSD dmg into
    `/Volumes/Aditya ssd/Applications` if not already installed).
  - Render every page and slide to PNG and **look at each one**. Fix overflow, overlaps, tiny
    fonts and missing images.
  - Re-run the forbidden-phrase / claim-ID linter.

### Phase 8: handover
1. Update `DELIVERABLES/0_YC_APPLICATION/YC_W27_answers.md` with the strongest honest new evidence,
   and mark what changed.
2. Write `DELIVERABLES/STARTUP_DECISION_MEMO.md` containing:
   - go / no-go / go-with-conditions, with reasons;
   - what is proven vs simulated vs assumed;
   - the single riskiest assumption and the cheapest experiment to test it (cost, time, lab);
   - the first 90 days; the founder's skill gaps and who to recruit (an electrochemist co-founder
     is very likely required).
3. Write `README.md`: a deliverables table and how to rebuild (`source tools/env.sh && ./run_all.sh`).
4. Make `run_all.sh` rebuild everything end to end, and confirm it does.
5. Zip `DELIVERABLES/`.
6. Final message to the founder (short):
   - where everything is;
   - test pass counts;
   - whether EC2 was needed;
   - the go/no-go verdict;
   - the three actions to do next.

---

## 10. Working style
- Phases are sequential except where independent (research, CAD and some sims can run in
  parallel if you can spawn helpers).
- Commit after each phase.
- If a tool fails twice, switch approach and note it. Do not loop.
- If evidence says the idea is weak, **say so plainly** and propose the best alternative wedge.
  A clear "no" is more valuable to this founder than a polished deck for a bad idea.
- Keep messages to the founder short: what was done, what was found, what is next.
