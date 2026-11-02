"""SaltBattery_Technical_and_Business_Report.docx + SaltBattery_OnePager.docx (→ PDF via LibreOffice in run_all).
Numbers only via docs/claims.py; every figure caption carries its claim tags (from the .caption.txt files)."""
import csv, glob, json, pathlib, sys
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "docs"))
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from claims import build

C = build()
OUT = LAB / "DELIVERABLES/1_investor_docs/SaltBattery_Technical_and_Business_Report.docx"
ONE = LAB / "DELIVERABLES/1_investor_docs/SaltBattery_OnePager.docx"
FIG = {"n": 0}


def base_doc():
    d = Document()
    st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
    for s in d.sections:
        s.left_margin = s.right_margin = Cm(2.0); s.top_margin = s.bottom_margin = Cm(1.8)
    return d


def P(d, text, size=None, italic=False, bold=False, color=None, align=None):
    p = d.add_paragraph(); r = p.add_run(text); r.italic = italic; r.bold = bold
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor.from_string(color)
    if align: p.alignment = align
    return p


def B(d, items, where):
    for it in items:
        d.add_paragraph(it, style="List Bullet")


def figure(d, path, width_cm=15.5):
    path = pathlib.Path(path)
    if not path.exists():
        P(d, f"(figure pending: {path.name}; run_all.sh regenerates it)", italic=True); return
    FIG["n"] += 1
    d.add_picture(str(path), width=Cm(width_cm))
    d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap = path.with_suffix(".caption.txt")
    text = cap.read_text().strip() if cap.exists() else "Concept image / diagram. [TARGET] design values from params."
    P(d, f"Figure {FIG['n']}. {text}", size=8.5, italic=True, color="52514E")


def table(d, rows, widths=None, size=9):
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Light Grid Accent 1"
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            c = t.cell(i, j); c.text = str(v)
            for p in c.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(size); run.bold = (i == 0)
            if widths:
                c.width = Cm(widths[j])
    d.add_paragraph()
    return t


def x(cid, w="report"):
    return C.txt(cid, where=w)


def g(cid, w="report"):
    return C.tag(cid, where=w)


def report():
    d = base_doc(); W = "report"
    P(d, "Salt Battery", size=26, bold=True)
    P(d, "Technical and business report: a water-based sodium battery for indoor backup", size=14)
    P(d, "Pre-prototype · simulations, calculations and literature only · 2 Nov 2026 · every number carries one tag ([LIT] [VENDOR] [CALC] [SIM] [ASSUMPTION] [TARGET]) and a claim ID that resolves in CLAIMS_LEDGER.csv. No result here is measured.", italic=True, color="52514E")

    d.add_heading("1. Executive summary", 1)
    B(d, [f"We tested whether a water-based sodium battery (sodium-birnessite cathode, NaTi₂(PO₄)₃ anode, sodium-sulfate electrolyte) can be a company selling 'the battery you are allowed to put indoors'.",
          f"Bottom-up, a 12-volt block in the lead-acid box size stores {x('C-116')} at {x('C-115')}, the same class as Aquion's last module ({x('C-013')}); Aquion went bankrupt after raising {x('C-015')}.",
          f"It costs about {x('C-122')} to make, against stationary LFP packs at {x('C-005')}; over 15 years of indoor UPS duty R1 / LFP / VRLA cost {x('C-123')} per kWh of 15-minute backup.",
          f"Fire codes do not hand water-based chemistry an advantage: an unlisted chemistry gets {x('C-008')} under IFC 2024 versus {x('C-007')} for Li-ion; NFPA 855-2026 requires hazard analysis and fire testing for everyone {g('C-010')}.",
          f"India's backup-battery market for this wedge is about {x('C-126')} (SAM {x('C-127')}).",
          "Verdict: no-go on a factory company today; go-with-conditions on a 12-week falsification sprint that starts with a near-free buyer test; the alternative wedge is battery fire-code and hazard-analysis software."], W)

    d.add_heading("2. Method and claims discipline", 1)
    B(d, ["One parameter file (params/product_params.py) and one derived-design module (params/design.py) feed every simulation, the CAD, the PCB ratings, the cost model and these documents.",
          "Each simulation lives in sim/sNN_name with a README (question, model, inputs, validation, limits), code and out/ data and charts.",
          f"The kit's own software was re-run first and reproduced its expected outputs: {x('C-101')}.",
          "A test suite checks units, conservation, regression against literature, parameter consistency and, for these documents, that no forbidden phrase appears and every number has a claim tag."], W)

    d.add_heading("3. Simulations and tests: method and results", 1)
    d.add_heading("3.1 Validation of the electrochemical model (S2)", 2)
    P(d, f"PyBaMM's sodium-ion DFN with the Chayambuka2022 parameter set was compared with experimental curves digitised from the source paper at four rates. As shipped it misses by {x('C-102')}, failing our pre-set 60 mV gate; a one-parameter kinetic calibration reaches {x('C-103')} (calibration, not validation). Conclusion: use the framework for capacity and loading trends; quote voltages with at least ±0.1 V {g('C-103')}.")
    figure(d, LAB / "sim/s02_pybamm_validation/out/s02_validation_discharge.png")
    d.add_heading("3.2 R1 cell model (S3)", 2)
    P(d, f"A DFN with literature-range parameters and Monte Carlo bands shows the rate cliff that sets the design point: at 40 mg/cm² a 15-minute discharge keeps {x('C-104')}, at 60 mg/cm² only {x('C-105')}. Electrochemical round-trip efficiency is {x('C-106')}.")
    figure(d, LAB / "sim/s03_r1_cell/out/s03_retention_vs_loading.png")
    figure(d, LAB / "sim/s03_r1_cell/out/s03_discharge_curves.png")
    d.add_heading("3.3 Water window, gas and water budget (S4)", 2)
    P(d, f"The anode sits {x('C-109')} the hydrogen line at pH 7. A sealed cell needs {x('C-107')} coulombic efficiency to last 3,000 cycles before losing 20 % of its water; at 99.5 % it lasts {x('C-108')}. UPS float duty is the worst case.")
    figure(d, LAB / "sim/s04_gas/out/s04_water_window.png")
    figure(d, LAB / "sim/s04_gas/out/s04_water_loss_vs_CE.png")
    d.add_heading("3.4 Atomistic screen (S5) and DFT+U check (S6)", 2)
    P(d, f"Universal ML potentials reproduce oxide and phosphate voltages but fail for NaTi₂(PO₄)₃ and Prussian white ({x('C-110')}). The ordered birnessite model gives an interlayer of {x('C-111')} against the paper's XRD; barriers: LiFePO₄ {x('C-112')}, birnessite Na hop {x('C-113')}. DFT+U on AWS gave LiFePO₄ {x('C-114')}, an offset consistent with QE atomic-projector U; the first spot instance was reclaimed by AWS and the queue was restarted (spend {x('C-212')}).")
    figure(d, LAB / "sim/s05_atomistic/out/s05_voltage_parity.png", 12)
    figure(d, LAB / "sim/s05_atomistic/out/s05_birnessite_interlayer.png", 12)
    figure(d, LAB / "sim/s05_atomistic/out/s05_barriers.png", 12)
    d.add_heading("3.5 Cell → block → rack (S7)", 2)
    P(d, f"Block {x('C-115')}, {x('C-117')}; a 600 × 800 × 2,000 mm UPS cabinet holds {x('C-118')}.")
    figure(d, LAB / "sim/s07_buildup/out/s07_energy_density_comparison.png")
    d.add_heading("3.6 Thermal and abuse (S8)", 2)
    P(d, f"A 15-minute UPS discharge raises block temperature by {x('C-119')}; even if all stored energy became heat the rise is {x('C-120')}; the case fire load is {x('C-121')}.")
    figure(d, LAB / "sim/s08_thermal/out/s08_monobloc_ups_temperature.png")
    figure(d, LAB / "sim/s08_thermal/out/s08_abuse_energy_budget.png")
    d.add_heading("3.7 Software tests", 2)
    tr = LAB / "DELIVERABLES/9_data/TEST_REPORT.md"
    P(d, "Full results: DELIVERABLES/9_data/TEST_REPORT.md (pass/fail counts per suite) and console snapshots in DELIVERABLES/11_screenshots/02_tests.")

    d.add_heading("4. Chemistry decision matrix", 1)
    rows = [["Criterion (weight)", "A", "B", "C", "D"]]
    for r in csv.DictReader(open(LAB / "decisions/chemistry_matrix.csv")):
        rows.append([f"{r['criterion'].replace('_', ' ')} ({r['weight']}) [CALC]", r["A_R0_symmetric_birnessite"], r["B_birnessite_NTP_Na2SO4"], r["C_MnFe_PBA_NTP_nonperchlorate"], r["D_birnessite_AC_hybrid"]])
    sc = json.loads((LAB / "decisions/chemistry_matrix_scores.json").read_text())
    rows.append(["Weighted score [CALC]"] + [f"{v:.2f}" for v in sc.values()])
    table(d, rows, widths=[7, 2, 2, 2, 2])
    P(d, "A = R0 symmetric birnessite; B = birnessite // NaTi₂(PO₄)₃; C = Mn/Fe Prussian white // NaTi₂(PO₄)₃; D = birnessite // activated carbon. Evidence per score: decisions/chemistry_matrix.csv. R1 uses the birnessite cathode with two anode builds (B and D) because one reproduction experiment de-risks both; C is the upgrade path.")

    d.add_heading("5. Design: CAD, drawings, PCB and renders", 1)
    P(d, "All dimensions come from params; drawings are marked CONCEPT – NOT FOR FABRICATION. Files: DELIVERABLES/3_cad_3d (STEP/STL/GLB), 4_engineering_drawings (DXF/PDF/PNG), 5_pcb (KiCad, Gerbers, BOM), 6_prototype_images (renders).")
    figure(d, LAB / "diagrams/out/d1_system_architecture.png")
    for gpat in ("renders/out/*hero*annot*.png", "renders/out/*exploded*annot*.png", "renders/out/*cutaway*annot*.png", "renders/out/*cabinet*annot*.png",
                 "drawings/out/*GA-001*.png", "DELIVERABLES/5_pcb/bms_monitor/*top*.png"):
        hits = sorted(glob.glob(str(LAB / gpat)))
        if hits:
            figure(d, hits[0], 14)

    d.add_heading("6. Safety and hazard register", 1)
    figure(d, LAB / "diagrams/out/d5_safety_comparison.png")
    rows = [["Hazard", "Control", "Source"]]
    rows += [["Hydrogen from side reactions or overcharge (S4)", "One-way vent + flame arrestor; H₂ sensor input on BMS; room ventilation to ≤ 25 % LFL", f"[CALC; C-107]"],
             ["Plastic case in an external fire (S8)", "Flame-retardant PP-GF (UL 94 V-0); spacing per hazard analysis", "[CALC; C-121]"],
             ["Electrolyte leakage (conductive, Mn²⁺ traces)", "Bunded trays, leak test at formation, insulation of busbars", "[ASSUMPTION]"],
             ["Salt crystallisation / freezing", "0.5 M electrolyte; operating floor 5 °C", "[TARGET; C-204]"],
             ["Caustic NaOH, Mn compounds in synthesis (lab)", "Qualified partner lab under EHS approval only", "[LIT] kit hazard register"]]
    try:
        hz = list(csv.reader(open(LAB / "00_source_kit/Salt_Battery_R0_Reference_Cell_Kit_v1/safety/HAZARD_REGISTER.csv")))
        for r in hz[1:7]:
            rows.append([r[0][:60] + (" — " + r[1][:40] if len(r) > 1 else ""), (r[-2] if len(r) > 2 else "")[:80], "[LIT] kit hazard register"])
    except Exception:
        pass
    table(d, rows, widths=[6, 8, 3])

    d.add_heading("7. Certification path", 1)
    B(d, [f"US/international: UL 1973 (stationary batteries), UL 9540 / UL 9540A (fire propagation test), IEC 62619-type safety; NFPA 855-2026 hazard mitigation analysis {g('C-010')}.",
          f"Code listing is the strategic step: an unlisted chemistry starts at {x('C-008')}; Zn-MnO₂ obtained its own row at {x('C-009')}.",
          "India: no BIS standard or TEC generic requirement for aqueous sodium was found; IS 16805 mirrors IEC 62619 (lithium); CEA BESS rules (from April 2027) name lithium, nickel-cadmium and lead-acid only (research/RESEARCH_NOTES.md §C) [LIT].",
          "Cost and time of UL 9540A testing are vendor estimates in research/sources.csv SRC-102 [VENDOR]."], W)

    d.add_heading("8. Manufacturing and scale-up", 1)
    figure(d, LAB / "diagrams/out/d2_process_flow.png")
    figure(d, LAB / "diagrams/out/d3_manufacturing_capex.png", 12)

    d.add_heading("9. Techno-economics and LCOS", 1)
    figure(d, LAB / "diagrams/out/d7_unit_economics_waterfall.png", 13)
    figure(d, LAB / "sim/s09_tea/out/s09_ups_tco.png", 12)
    figure(d, LAB / "sim/s09_tea/out/s09_tornado_ups.png", 13)
    figure(d, LAB / "sim/s09_tea/out/s09_breakeven_map.png", 12)
    figure(d, LAB / "sim/s09_tea/out/s09_learning_curve.png", 12)
    P(d, f"Telecom daily-cycling LCOS R1 / LFP / VRLA: {x('C-124')}. The financial model (SaltBattery_Financial_Model.xlsx, live formulas, LibreOffice-recalculated) shows that R1 breaks even with Li-ion for indoor UPS only if Li-ion fire protection costs {x('C-211')}.")

    d.add_heading("10. Market", 1)
    figure(d, LAB / "sim/s10_market/out/s10_tam_sam_som.png", 13)
    P(d, f"Inputs: {x('C-024')} towers, data-centre capacity {x('C-023')}, India BESS additions {x('C-025')}; cross-check {x('C-029')}. TAM {x('C-126')}, SAM {x('C-127')}, SOM {x('C-128')}.")

    d.add_heading("11. Competition", 1)
    rows = [["Player", "Approach", "Number", "Status"],
            ["LFP", "Li-ion", x("C-005"), "Default"], ["CATL Naxtra", "Na-ion non-aqueous", x("C-020"), "Production"],
            ["Peak Energy", "Na-ion non-aqueous", f"{x('C-017')}; orders {x('C-018')}", "Scaling"],
            ["Alsym", "Na-ion 'NFPP+'", f"{x('C-019')}; {x('C-028')}", "Targets data centres"],
            ["Aquion", "Water-based Na / Mn oxide", x("C-013"), "Bankrupt 2017"],
            ["Natron", "Prussian blue", g("C-016"), "Shut 2025"], ["R1", "Water-based Na / Mn oxide", x("C-115"), "Pre-prototype"]]
    table(d, rows, widths=[3, 4, 6, 3])
    figure(d, LAB / "diagrams/out/d6_positioning_map.png", 12)

    d.add_heading("12. Risks and mitigations", 1)
    rows = [["Risk", "Mitigation / test", "Gate"],
            ["No buyer pays an indoor premium", "20 interviews + fire-protection quotes before lab spend", g("C-207")],
            ["Capacity collapses at real loading", "3 / 20 / 40 mg/cm² electrodes", g("C-206")],
            ["Side reactions dry the cell", "Gas + CE measurement; anode inside water window for float", g("C-107")],
            ["Cost stays above LFP + fire costs", "Supplier quotes; re-run S9 on measured data", g("C-122")],
            ["Code listing takes years", "Early UL 9540A; AHJ conversations", g("C-008")],
            ["Solo, non-electrochemist founder", "Electrochemist co-founder as precondition", "[TARGET]"]]
    table(d, rows, widths=[5, 8, 3])

    d.add_heading("13. IP strategy and freedom-to-operate notes", 1)
    B(d, ["We hold no patents and have filed none. Notes from a first Google Patents pass (claims not yet read in full; not legal advice):",
          "Aquion-lineage patents: US 8,298,701 and US 8,962,175 'Aqueous electrolyte energy storage device'; US 8,945,756 and US 9,728,775 cover a composite NaTi₂(PO₄)₃ + activated-carbon anode, directly relevant to R1's anode builds; Carnegie Mellon US 9,088,046 'Sodium based aqueous electrolyte electrochemical secondary energy storage device' [LIT; patents.google.com].",
          "Aquion's assets were sold after the 2017 bankruptcy; current ownership and expiry dates must be checked before any product decision [LIT; research/sources.csv SRC-032].",
          "Published birnessite routes (Shan 2019 and later) are prior art that limits what we could claim; any IP would be in electrode processing, electrolyte additives, gas management or the BMS gas-sensing logic [ASSUMPTION]."], W)

    d.add_heading("14. 18-month plan and budget", 1)
    figure(d, LAB / "diagrams/out/d8_roadmap_gantt.png")
    figure(d, LAB / "diagrams/out/d4_validation_ladder.png")
    figure(d, LAB / "diagrams/out/d9_use_of_funds.png", 13)
    P(d, f"Budget: {x('C-208')} on standard YC terms, released against the week-8 and week-12 gates; first lab experiment {x('C-205')}.")

    d.add_heading("15. Limitations and claims boundary", 1)
    B(d, ["No cell, electrode or powder has been made or measured by us; no measured-data claim exists anywhere in this package.",
          f"The electrochemical model failed independent voltage validation {g('C-102')}; R1 results are trends.",
          "All costs are bottom-up from assumed or low-confidence prices; no supplier quotation exists.",
          "Market sizing uses secondary sources and assumptions; no customer has been interviewed.",
          "DFT and ML-potential results are screening calculations with known projector and model errors.",
          "Concept CAD, drawings, PCB and renders are not designs for fabrication."], W)

    d.add_heading("16. References", 1)
    refs = ["Shan X. et al., Nat. Commun. 10, 4975 (2019), doi:10.1038/s41467-019-12939-3 [LIT]",
            "Chayambuka K. et al., Electrochim. Acta 404, 139764 (2022) [LIT]",
            "Wu et al., Alkaline-based aqueous sodium-ion batteries, Nat. Commun. (2024) [LIT]",
            "BNEF battery price survey 2025 via energy-storage.news [LIT]",
            "NFPA 855 (2026 edition) summaries: MeyerFire, RiskLogic [LIT]; IFC 2024 Table 1207.1.3 via Clark County NV guide [LIT]",
            "Aquion Aspen 48S-2.2 datasheet; MIT Technology Review (2017) [VENDOR]/[LIT]",
            "Company sources: Peak Energy, Alsym, CATL, Gotion press coverage [VENDOR]",
            "Full source list with access dates and confidence: research/sources.csv (164 rows) [LIT]"]
    B(d, refs, W)
    d.save(OUT)


def one_pager():
    d = base_doc(); W = "one-pager"
    for s in d.sections:
        s.top_margin = s.bottom_margin = Cm(1.2); s.left_margin = s.right_margin = Cm(1.6)
    P(d, "Salt Battery: one page", size=18, bold=True)
    P(d, "Water-based sodium battery for indoor backup · pre-prototype · simulations and literature only · 2 Nov 2026", size=9.5, italic=True, color="52514E")
    P(d, "What it is", bold=True)
    P(d, f"A 12-volt block in the lead-acid box size, using a sodium-birnessite cathode, NaTi₂(PO₄)₃ anode and {x('C-204', W)} sodium sulfate in water, so the electrolyte cannot burn.", size=10)
    P(d, "What we found", bold=True)
    B(d, [f"Energy {x('C-115', W)}, the Aquion class {g('C-013', W)}",
          f"Cost {x('C-122', W)} vs LFP pack {x('C-005', W)}",
          f"15-yr indoor UPS cost R1 / LFP / VRLA {x('C-123', W)} per kWh of 15-min backup",
          f"Codes: unlisted chemistry {x('C-008', W)} vs Li-ion {x('C-007', W)}",
          f"India SAM {x('C-127', W)}"], W)
    d.add_picture(str(LAB / "sim/s07_buildup/out/s07_energy_density_comparison.png"), width=Cm(11.5))
    P(d, "Specific energy by level: R1 bottom-up vs Aquion, VRLA, sodium-ion claims and LFP [CALC]/[VENDOR]/[ASSUMPTION] (S7).", size=8, italic=True, color="52514E")
    d.add_picture(str(LAB / "sim/s09_tea/out/s09_ups_tco.png"), width=Cm(11.5))
    P(d, "15-year cost per kWh of 15-minute indoor UPS backup incl. replacements, floor and Li-ion fire protection [CALC; C-123] (S9).", size=8, italic=True, color="52514E")
    P(d, "Verdict and next step", bold=True)
    P(d, f"No-go on a factory company today. Go-with-conditions on a 12-week sprint: buyer test first ({x('C-207', W)}), then a partner-lab test at real loading ({x('C-205', W)}). Alternative wedge: battery fire-code / hazard-analysis software {g('C-010', W)}.", size=10)
    P(d, "Every number is tagged and resolves in CLAIMS_LEDGER.csv. Concept only; nothing has been built.", size=8.5, italic=True, color="52514E")
    d.save(ONE)


if __name__ == "__main__":
    report(); one_pager(); C.write()
    print("wrote", OUT.name, ONE.name)
