"""SaltBattery_Investor_Deck.pptx — 16 core slides + appendix, speaker notes, every number tagged.
Numbers come only from docs/claims.py (which reads params + simulation outputs). Images: sim charts,
diagrams, CAD/Blender renders and PCB renders if present (globbed, so re-running picks up new renders).
"""
import glob, pathlib, sys
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "docs"))
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from claims import build

C = build()
OUT = LAB / "DELIVERABLES/1_investor_docs/SaltBattery_Investor_Deck.pptx"
INK, INK2, MUTED, ACCENT, SURF = RGBColor(0x0B, 0x0B, 0x0B), RGBColor(0x52, 0x51, 0x4E), RGBColor(0x8A, 0x89, 0x84), RGBColor(0x2A, 0x78, 0xD6), RGBColor(0xFC, 0xFC, 0xFB)
W, H = Inches(13.333), Inches(7.5)
prs = Presentation(); prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]
N = {"n": 0}


def img(name_globs):
    for g in name_globs:
        hits = sorted(glob.glob(str(LAB / g)))
        if hits:
            return hits[0]
    return None


def slide(title, kicker=None, where=None):
    s = prs.slides.add_slide(BLANK)
    N["n"] += 1
    s.background.fill.solid(); s.background.fill.fore_color.rgb = SURF
    tb = s.shapes.add_textbox(Inches(0.55), Inches(0.35), Inches(12.2), Inches(0.9))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = title; p.font.size = Pt(28); p.font.bold = True; p.font.color.rgb = INK
    if kicker:
        p2 = tf.add_paragraph(); p2.text = kicker; p2.font.size = Pt(14); p2.font.color.rgb = INK2
    ft = s.shapes.add_textbox(Inches(0.55), Inches(7.05), Inches(12.2), Inches(0.3)).text_frame
    fp = ft.paragraphs[0]
    fp.text = f"Salt Battery · pre-prototype · simulations, calculations and literature only · tags [LIT] [VENDOR] [CALC] [SIM] [ASSUMPTION] [TARGET] → CLAIMS_LEDGER.csv · {N['n']}"
    fp.font.size = Pt(9); fp.font.color.rgb = MUTED
    s._where = where or f"deck s{N['n']}"
    return s


def bullets(s, items, x=0.55, y=1.45, w=6.2, h=5.3, size=15):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    first = True
    for it in items:
        lvl = 0
        if isinstance(it, tuple):
            lvl, it = it
        p = tf.paragraphs[0] if first else tf.add_paragraph(); first = False
        p.text = ("• " if lvl == 0 else "– ") + it; p.level = lvl
        p.font.size = Pt(size - 2 * lvl); p.font.color.rgb = INK if lvl == 0 else INK2
        p.space_after = Pt(7)
    return tb


def picture(s, path, x, y, w=None, h=None, caption=None):
    if not path or not pathlib.Path(path).exists():
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w or 5), Inches(0.5))
        tb.text_frame.text = "(image pending: run_all.sh regenerates it)"; tb.text_frame.paragraphs[0].font.size = Pt(11)
        return
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    pic = s.shapes.add_picture(str(path), Inches(x), Inches(y), **kw)
    if caption:
        cap = pathlib.Path(path).with_suffix(".caption.txt")
        ctext = caption if caption is not True else (cap.read_text().strip() if cap.exists() else "")
        tb = s.shapes.add_textbox(Inches(x), Emu(pic.top + pic.height + Inches(0.05)), Emu(pic.width), Inches(0.6))
        tb.text_frame.word_wrap = True; tb.text_frame.text = ctext
        for p in tb.text_frame.paragraphs:
            p.font.size = Pt(9); p.font.color.rgb = MUTED


def table(s, rows, x, y, w, col_w=None, size=11, h_row=0.36):
    nr, nc = len(rows), len(rows[0])
    shp = s.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(h_row * nr))
    t = shp.table
    for j in range(nc):
        if col_w:
            t.columns[j].width = Inches(col_w[j])
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            cell = t.cell(i, j); cell.text = str(v)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(size); p.font.bold = (i == 0); p.font.color.rgb = INK
            cell.margin_left = cell.margin_right = Inches(0.05)
    return t


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


def t(cid, s, **kw):
    return C.txt(cid, where=s._where, **kw)


def g(cid, s):
    return C.tag(cid, where=s._where)


# ======================= CORE =======================
s = slide("Salt Battery", "A water-based sodium battery for indoor backup: what we tested, what we found, what we'd do next", "deck s1 title")
bullets(s, ["Stage: pre-prototype. No cell has been built or tested by us.",
            "Everything here is a simulation, a calculation or a cited source, and each number carries a tag and ID.",
            "Our own verdict is at the end: no-go on a factory company today; a 12-week falsification sprint with kill gates."], y=1.7, w=6.0, size=16)
picture(s, img(["renders/out/*hero*annot*.png", "renders/out/*hero*.png", "DELIVERABLES/6_prototype_images/*hero*.png", "diagrams/out/d1_system_architecture.png"]), 6.7, 1.6, w=6.2, caption="Concept render / diagram. Not a built product.")
notes(s, "Open with the honest stage. The rigour of the analysis is the asset at this point, not a prototype.")

s = slide("The problem: lithium is cheap, but indoors it brings fire engineering")
bullets(s, [f"NFPA 855 (2026 edition) requires a hazard mitigation analysis for essentially every installation and drops the stored-energy table {g('C-010', s)}",
            f"Fire and Rescue NSW: {t('C-012', s)} fire-rated rooms for Li-ion data-centre UPS batteries",
            f"Indian backup still runs largely on lead-acid at {t('C-021', s)}, replaced every {t('C-209', s)}",
            f"Catch: codes reward tested, listed chemistries. An unlisted battery gets a {t('C-008', s)} permit threshold vs {t('C-007', s)} for Li-ion under IFC 2024"], w=12.2, size=17)
notes(s, "The pain is real but the code advantage is not automatic: an aqueous chemistry starts stricter than lithium until it is tested and listed.")

s = slide("Why now")
bullets(s, [f"Code shift: NFPA 855-2026 makes hazard analysis and large-scale fire testing the default {g('C-010', s)}",
            f"India storage build-out: {t('C-025', s)} of BESS added in H1 2026; data-centre capacity {t('C-023', s)}",
            f"Sodium supply chain maturing: CATL sodium-ion at {t('C-020', s)}; Peak Energy raised {t('C-017', s)}",
            f"YC's own request list includes data-centre supply chain {g('C-030', s)}"], w=12.2, size=17)
notes(s, "Why now cuts both ways: sodium-ion maturity also means better-funded non-aqueous competitors.")

s = slide("Product concept: R1, a 12-volt block in the VRLA box size")
rows = [["Parameter", "Value", "Tag / ID"],
        ["Chemistry", "Na-birnessite // NaTi₂(PO₄)₃-C, water-based", "[TARGET]"],
        ["Electrolyte", t("C-204", s), "[TARGET; C-204]"],
        ["Nominal cell voltage", t("C-210", s), "[CALC; C-210]"],
        ["Energy per block (bottom-up)", t("C-116", s), "[CALC; C-116]"],
        ["Specific energy, median (P10–P90)", t("C-115", s), "[CALC; C-115]"],
        ["15-minute rate retention", t("C-104", s), "[SIM; C-104]"],
        ["Cycle life target", t("C-202", s), "[TARGET; C-202]"],
        ["Cost target at first line", t("C-203", s), "[TARGET; C-203]"]]
table(s, rows, 0.55, 1.5, 7.2, col_w=[2.5, 3.2, 1.5], size=12)
picture(s, img(["renders/out/*cutaway*annot*.png", "renders/out/*cutaway*.png", "renders/out/*monobloc*.png", "diagrams/out/d1_system_architecture.png"]), 8.0, 1.5, w=4.9, caption="Concept render / diagram.")
notes(s, "Form factor chosen so UPS and telecom integrators can rack it like a VRLA block. Energy is the weak point; say it before they do.")

s = slide("Unique insight: what we believed, and what survived")
rows = [["We believed", "Evidence", "Status"],
        ["Indoors, we only need lead-acid energy density", f"Bottom-up block {t('C-115', s)} is below lead-acid", "Withdrawn"],
        ["We'd win on installed cost incl. fire protection", f"15-yr UPS cost R1 / LFP / VRLA = {t('C-123', s)}", "Not at base case"],
        ["Water-based = allowed indoors", f"Unlisted chemistry threshold {t('C-008', s)}", "Must be earned"],
        ["Codes reward tested, listed chemistries", f"NFPA 855-2026 HMA by default {g('C-010', s)}", "Survives"]]
table(s, rows, 0.55, 1.5, 12.2, col_w=[4.0, 6.2, 2.0], size=13, h_row=0.55)
bullets(s, ["What survived is a market observation, not a technical moat: test data plus code listing plus permitting know-how is the defensible asset.",
            "We found no technical insight that lets a water-based cell beat sodium-ion or LFP on cost per delivered kWh."], y=4.7, w=12.2, size=15)
notes(s, "This slide is the core of the honesty story. A YC partner will respect a founder who killed his own pet insight with arithmetic.")

s = slide("How it works, and where the water fights back")
picture(s, LAB / "sim/s04_gas/out/s04_water_window.png", 0.55, 1.45, w=6.3, caption=True)
bullets(s, [f"Cell voltage is set by two electrode potentials: {t('C-210', s)}",
            f"The NTP anode sits {t('C-109', s)} the hydrogen line at pH 7, so side reactions are certain",
            f"A sealed cell needs coulombic efficiency of {t('C-107', s)} to reach 3,000 cycles before losing 20 % of its water",
            f"The paper's 1 M electrolyte would crystallise in a cool room (solubility {t('C-027', s)} at 0 °C), so R1 uses {t('C-204', s)}"], x=7.1, w=5.8, size=14)
notes(s, "These are the things a battery investor would catch. We caught them first, in simulation.")

s = slide("Simulation evidence (screening, not validation)")
picture(s, LAB / "sim/s03_r1_cell/out/s03_retention_vs_loading.png", 0.4, 1.35, h=4.15)
picture(s, LAB / "sim/s05_atomistic/out/s05_voltage_parity.png", 7.2, 1.35, h=4.15)
bullets(s, [f"15-minute retention at 40 mg/cm²: {t('C-104', s)}; at 60 mg/cm²: {t('C-105', s)}",
            f"PyBaMM sodium model misses published curves by {t('C-102', s)} as shipped, so voltages carry ±0.1 V {g('C-103', s)}",
            f"ML-potential voltage error {t('C-110', s)}"], y=5.6, w=12.4, size=12)
notes(s, "Be explicit: S2 failed its own validation gate. We use the electrochemical model for trends only.")

s = slide("Safety: no runaway chain; hydrogen and the case remain")
picture(s, LAB / "diagrams/out/d5_safety_comparison.png", 0.4, 1.35, w=7.6)
picture(s, LAB / "sim/s08_thermal/out/s08_abuse_energy_budget.png", 8.2, 1.45, w=4.8)
bullets(s, [f"15-minute UPS discharge heats a block by {t('C-119', s)}",
            f"Even all stored energy as heat: {t('C-120', s)}, below boiling",
            f"Case fire load {t('C-121', s)}: the case is the fuel"], x=8.2, y=4.35, w=4.9, size=12)
notes(s, "Non-flammable electrolyte is true; 'cannot catch fire' is not. Hydrogen needs ventilation and the case needs a V-0 grade.")

s = slide("Prototype design (concept, not for fabrication)")
pics = [img(["renders/out/*exploded*annot*.png", "renders/out/*exploded*.png", "DELIVERABLES/6_prototype_images/*exploded*.png"]),
        img(["renders/out/*cabinet*annot*.png", "renders/out/*cabinet*.png", "renders/out/*rack*.png", "DELIVERABLES/6_prototype_images/*cabinet*.png"]),
        img(["DELIVERABLES/5_pcb/bms_monitor/*3d*top*.png", "pcb/bms_monitor/out/*top*.png", "DELIVERABLES/5_pcb/*/*.png"])]
for k, pth in enumerate(pics):
    picture(s, pth or (LAB / ["diagrams/out/d1_system_architecture.png", "diagrams/out/d2_process_flow.png", "diagrams/out/d3_manufacturing_capex.png"][k]), 0.4 + k * 4.3, 1.5, w=4.1)
bullets(s, ["Block, 48-volt tray and UPS cabinet modelled in build123d (STEP), drawn in CADCraft and rendered in Blender",
            "Battery-monitor PCB in KiCad: per-block voltage, temperature, current, hydrogen and pressure inputs, isolated CAN and RS-485",
            "All dimensions come from one parameter file; files in DELIVERABLES 3, 4, 5 and 6"], y=5.0, w=12.4, size=13)
notes(s, "Renders are concept renders. Nothing has been fabricated.")

s = slide("Competition: honest map, including the graveyard")
rows = [["Player", "Approach", "Key number", "Status"],
        ["LFP (CATL, BYD, Indian integrators)", "Li-ion, non-aqueous", t("C-005", s), "Default; price leader"],
        ["CATL Naxtra", "Na-ion, non-aqueous", t("C-020", s), "In production"],
        ["Peak Energy (US)", "Na-ion, non-aqueous", f"{t('C-017', s)}; orders {t('C-018', s)}", "Scaling"],
        ["Alsym (US)", "Na-ion 'NFPP+'", f"{t('C-019', s)}; Series C {t('C-028', s)}", "Targets data centres"],
        ["Aquion (US)", "Water-based Na / Mn oxide", f"{t('C-013', s)}; raised {t('C-015', s)}", "Bankrupt 2017"],
        ["Natron (US)", "Prussian blue", g("C-016", s), "Shut down 2025"],
        ["R1 (us)", "Water-based Na / Mn oxide", t("C-115", s), "Pre-prototype"]]
table(s, rows, 0.4, 1.45, 7.6, col_w=[2.2, 1.9, 2.4, 1.1], size=10.5, h_row=0.6)
picture(s, LAB / "diagrams/out/d6_positioning_map.png", 8.15, 1.45, w=4.9, caption=True)
notes(s, "Aquion is the base rate. Our bottom-up energy density lands in the same class; the difference has to come from market choice and power, and we say that is not yet enough.")

s = slide("Business model and unit economics")
picture(s, LAB / "diagrams/out/d7_unit_economics_waterfall.png", 0.4, 1.4, w=6.4, caption=True)
picture(s, LAB / "sim/s09_tea/out/s09_ups_tco.png", 7.0, 1.4, w=5.9, caption=True)
bullets(s, [f"We'd sell blocks and 48-volt trays per kWh. Bottom-up cost {t('C-122', s)} vs LFP pack {t('C-005', s)}",
            f"Telecom daily-cycling LCOS R1 / LFP / VRLA: {t('C-124', s)}",
            f"Break-even only if Li-ion indoor fire protection costs {t('C-211', s)}"], y=5.6, w=12.4, size=12.5)
notes(s, "This is where the factory thesis fails at base assumptions. The tornado in the appendix shows what would have to move.")

s = slide("Market, bottom-up (India first)")
picture(s, LAB / "sim/s10_market/out/s10_tam_sam_som.png", 0.4, 1.4, w=7.4, caption=True)
bullets(s, [f"TAM {t('C-126', s)}: telecom sites ({t('C-024', s)}) plus data-centre UPS ({t('C-023', s)})",
            f"SAM {t('C-127', s)} where 'allowed indoors' plausibly changes the purchase",
            f"5-year SOM {t('C-128', s)}",
            f"Cross-check: paid-report UPS battery market {t('C-029', s)}"], x=8.0, w=5.0, size=13)
notes(s, "India alone is a small prize for this product. Venture scale needs global indoor backup, where incumbents are stronger.")

s = slide("Go-to-market wedge and first customer")
bullets(s, ["First customer profile: tower company or neutral-host operator with in-building sites (malls, hospitals, metro), or a mid-size colocation operator with UPS rooms under one MWh",
            "Buyer: facilities head who already pays for lead-acid replacement every few years and faces landlord or insurer objections to lithium",
            f"First test before any lab spend: 20 buyer interviews plus two fire-protection quotes. Kill rule: {t('C-207', s)} buyers naming a ≥ $150/kWh lithium indoor premium",
            "Channel: UPS integrators and tower-company procurement; code listing and UL 9540A data as part of the product"], w=12.2, size=16)
notes(s, "The cheapest experiment that could change the answer is a market test, not a lab test.")

s = slide("Roadmap with kill gates")
picture(s, LAB / "diagrams/out/d8_roadmap_gantt.png", 1.4, 1.3, h=4.3)
bullets(s, [f"Week 8: buyer gate {g('C-207', s)}. Week 12: capacity, efficiency, power, cost and code gates {g('C-206', s)}",
            f"First lab experiment {t('C-205', s)}; the full validation ladder is in the report"], y=5.75, w=12.4, size=12.5)
notes(s, "Every rung has a stop condition. Spending beyond week 12 is conditional.")

s = slide("Team and hiring needs")
bullets(s, ["Founder: solo; built this analysis lab (simulation, atomistic screens, cost and market models, concept CAD and PCB) with AI coding tools. [Founder adds background]",
            "Gap stated openly: no electrochemistry or cell-building track record",
            "Hire 1, precondition for the battery path: electrochemist co-founder who has built aqueous or sodium-ion cells at real loadings",
            "Advisor, needed either way: fire-protection engineer with NFPA 855, UL 9540A and hazard-analysis practice",
            "Later: manufacturing engineer (lead-acid or supercapacitor lines), power-electronics engineer"], w=12.2, size=16)
notes(s, "Do not list advisors who have not agreed. Placeholders for founder background must be filled before any use.")

s = slide("The ask, and our own verdict")
picture(s, LAB / "diagrams/out/d9_use_of_funds.png", 0.4, 1.4, w=6.6, caption=True)
bullets(s, [f"Ask: {t('C-208', s)} on standard YC terms, released against the week-8 and week-12 gates",
            "Verdict: no-go on a factory company today; go-with-conditions on a 12-week falsification sprint",
            "If the gates fail: pivot to battery fire-code and hazard-analysis software, where NFPA 855-2026 created the demand",
            f"DFT on AWS cost {t('C-212', s)} so far"], x=7.2, w=5.8, size=14)
notes(s, "Close with the verdict. It's unusual for a founder deck, and it is the strongest signal of judgement we can send.")

# ======================= APPENDIX =======================
s = slide("Appendix A1: method and claims discipline")
bullets(s, ["Single source of truth: params/product_params.py and params/design.py feed simulations, CAD, PCB ratings, cost model and documents",
            f"Kit re-run reproduces the kit's expected outputs: {t('C-101', s)}",
            "Every number in this deck carries one tag and a claim ID; CLAIMS_LEDGER.csv lists value, source, confidence and where used",
            "A linter fails the build if a number lacks a tag or a forbidden phrase appears",
            "MEASURED is not used anywhere: no lab data exists"], w=12.2, size=15)
s = slide("Appendix A2: electrochemical model validation (S2)")
picture(s, LAB / "sim/s02_pybamm_validation/out/s02_validation_discharge.png", 0.4, 1.4, w=7.2, caption=True)
bullets(s, [f"As shipped: {t('C-102', s)} against a 60 mV gate: FAIL", f"One-parameter calibration: {t('C-103', s)}: calibration, not validation",
            "Likely cause: exchange-current units in the shipped parameter set"], x=7.9, w=5.1, size=13)
s = slide("Appendix A3: R1 discharge curves (S3)")
picture(s, LAB / "sim/s03_r1_cell/out/s03_discharge_curves.png", 0.4, 1.4, w=7.4, caption=True)
bullets(s, [f"Round-trip efficiency C/5 / 1C / 4C: {t('C-106', s)}"], x=8.0, w=5.0, size=13)
s = slide("Appendix A4: gas and water budget (S4)")
picture(s, LAB / "sim/s04_gas/out/s04_water_loss_vs_CE.png", 0.4, 1.4, w=7.2, caption=True)
bullets(s, [f"At 99.5 % CE: {t('C-108', s)} to 20 % water loss", f"Needed for 3,000 cycles: {t('C-107', s)}"], x=7.9, w=5.0, size=13)
s = slide("Appendix A5: atomistic screen (S5) and DFT+U (S6)")
picture(s, LAB / "sim/s05_atomistic/out/s05_birnessite_interlayer.png", 0.4, 1.35, h=4.1)
picture(s, LAB / "sim/s05_atomistic/out/s05_barriers.png", 6.8, 1.35, h=4.1)
bullets(s, [f"Interlayer {t('C-111', s)}; LiFePO₄ barrier {t('C-112', s)}; birnessite Na hop {t('C-113', s)}",
            f"DFT+U LiFePO₄ voltage {t('C-114', s)}: projector-dependent offset, screening only"], y=5.65, w=12.4, size=12)
s = slide("Appendix A6: cell → block → rack (S7)")
picture(s, LAB / "sim/s07_buildup/out/s07_energy_density_comparison.png", 0.4, 1.4, w=7.6, caption=True)
bullets(s, [f"Block {t('C-115', s)}; {t('C-117', s)}", f"UPS cabinet {t('C-118', s)}", f"Aquion module {t('C-013', s)}"], x=8.2, w=4.8, size=13)
s = slide("Appendix A7: thermal (S8)")
picture(s, LAB / "sim/s08_thermal/out/s08_monobloc_ups_temperature.png", 0.4, 1.4, w=7.6, caption=True)
bullets(s, [f"Max rise in a 15-minute UPS discharge {t('C-119', s)}"], x=8.2, w=4.8, size=13)
s = slide("Appendix A8: what moves the business case (S9)")
picture(s, LAB / "sim/s09_tea/out/s09_tornado_ups.png", 0.3, 1.4, w=6.4, caption=True)
picture(s, LAB / "sim/s09_tea/out/s09_breakeven_map.png", 6.9, 1.4, w=6.0, caption=True)
s = slide("Appendix A9: key assumptions (ranges in the financial model)")
rows = [["Assumption", "Base", "Tag / ID"], ["Li-ion indoor fire-protection extra", t("C-201", s), "[ASSUMPTION; C-201]"],
        ["VRLA float life", t("C-209", s), "[ASSUMPTION; C-209]"], ["First lab experiment", t("C-205", s), "[ASSUMPTION; C-205]"],
        ["Material prices, yield, capex, labour", "see Assumptions sheet", "[ASSUMPTION] all ranged"]]
table(s, rows, 0.55, 1.5, 12.2, col_w=[5.0, 4.4, 2.8], size=13, h_row=0.5)
s = slide("Appendix A10: claims ledger excerpt")
rows = [["ID", "Claim", "Value", "Tag"]]
for cid in ("C-005", "C-008", "C-013", "C-104", "C-107", "C-115", "C-122", "C-123", "C-126"):
    r = C.rows[cid]; C.used.setdefault(cid, set()).add(s._where)
    rows.append([cid, r["claim"][:78], f"{r['value']} {r['unit']}", f"[{r['tag']}]"])
table(s, rows, 0.4, 1.4, 12.5, col_w=[0.8, 7.9, 2.4, 1.4], size=10, h_row=0.48)
s = slide("Appendix A11: process flow and manufacturing scale-up")
picture(s, LAB / "diagrams/out/d2_process_flow.png", 0.5, 1.35, w=12.3)
s = slide("Appendix A12: manufacturing scale-up and capex")
picture(s, LAB / "diagrams/out/d3_manufacturing_capex.png", 0.4, 1.35, w=6.3, caption=True)
picture(s, LAB / "diagrams/out/d4_validation_ladder.png", 6.9, 1.35, w=6.1)

prs.save(OUT)
C.write()
print("deck slides:", len(prs.slides), "->", OUT)
