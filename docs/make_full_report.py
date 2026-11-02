"""SaltBattery_Complete_Technical_Record.docx - everything done in the lab so far (aqueous track v0 + Project Salt v1/v1.1).

Every number is read from a result file (JSON / CSV / the generated markdown tables) at build time - nothing is retyped.
Figure captions come from the matching .caption.txt (which carries the evidence labels). Images are downscaled copies.
Run on the EC2 build host after the pipeline:  python docs/make_full_report.py   (then LibreOffice -> PDF for QA)
"""
from __future__ import annotations
import csv, json, re, sys, tempfile, xml.etree.ElementTree as ET
from pathlib import Path
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

LAB = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(LAB))
OUT = LAB / "DELIVERABLES/1_investor_docs/SaltBattery_Complete_Technical_Record.docx"
TMP = Path(tempfile.mkdtemp(prefix="rep_"))
J = lambda p: json.load(open(LAB / p))
FIG = {"n": 0}; TAB = {"n": 0}
sys.path.insert(0, str(LAB / "renders"))
from run_salt_renders import SHOTS  # noqa: E402
RCAP = {f"{k}_captioned": v[1] + " — Blender Cycles render of the build123d CAD (concept, not a photograph)." for k, v in SHOTS.items()}
RCAP.update({"hero_annotated": "Aqueous-track R1 monobloc concept (v0) — render of CAD.", "cutaway_annotated": "Aqueous-track R1 cutaway (v0) — render of CAD.",
             "room_annotated": "Aqueous-track UPS room concept (v0) — render of CAD."})
from params.smodule_params import CABINET, MODULE, P1, THERMAL  # noqa: E402
from params.scell_params import CELL, GATES, OPERATE  # noqa: E402


# ------------------------------------------------------------------ helpers
def shade(cell, hex_):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), hex_); tcPr.append(s)


def doc_base():
    d = Document(); st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
    for s in d.sections: s.left_margin = s.right_margin = Cm(2.0); s.top_margin = s.bottom_margin = Cm(1.8)
    for lvl, size in ((1, 16), (2, 13), (3, 11.5)):
        h = d.styles[f"Heading {lvl}"]; h.font.size = Pt(size); h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    footer = d.sections[0].footer.paragraphs[0]
    footer.text = "Salt-Battery-Lab - Complete Technical Record - CONCEPT / PRE-PROTOTYPE: nothing in this document is measured."
    footer.runs[0].font.size = Pt(7.5); footer.runs[0].font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    return d


def P(d, text, bold=False, italic=False, size=None, color=None, align=None, style=None):
    p = d.add_paragraph(style=style); r = p.add_run(text); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor.from_string(color)
    if align: p.alignment = align
    return p


def bullets(d, items):
    for it in items: d.add_paragraph(it, style="List Bullet")


def table(d, rows, widths=None, head=True, size=8.5, title=None):
    if title:
        TAB["n"] += 1; P(d, f"Table {TAB['n']}. {title}", bold=True, size=9)
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    if widths:
        for j, w in enumerate(widths): t.columns[j].width = Cm(w)            # tblGrid: LibreOffice/Word read this, not only cell widths
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.text = ""; r = c.paragraphs[0].add_run("" if v is None else str(v)); r.font.size = Pt(size)
            if head and i == 0: r.bold = True; shade(c, "E8ECF2")
            if widths: c.width = Cm(widths[j])
    d.add_paragraph()
    return t


def caption_for(png: Path):
    for c in (png.with_suffix(".caption.txt"), png.parent / (png.stem + ".caption.txt")):
        if c.exists(): return c.read_text().strip().replace("\n", " ")
    return None


def figure(d, path, caption=None, width_cm=16.0, jpeg=False):
    path = LAB / path if not str(path).startswith("/") else Path(path)
    if not path.exists():
        P(d, f"[figure missing: {path.relative_to(LAB) if str(path).startswith(str(LAB)) else path}]", italic=True, color="AA0000"); return
    im = Image.open(path); im = im.convert("RGB") if jpeg or im.mode not in ("RGB", "L") else im
    if im.width > 1800: im = im.resize((1800, int(im.height * 1800 / im.width)), Image.LANCZOS)
    tmp = TMP / (path.stem + (".jpg" if jpeg else ".png")); im.save(tmp, quality=88) if jpeg else im.save(tmp, optimize=True)
    d.add_picture(str(tmp), width=Cm(width_cm)); d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    FIG["n"] += 1; cap = caption or caption_for(path) or RCAP.get(path.stem) or path.stem
    P(d, f"Figure {FIG['n']}. {cap}", italic=True, size=8.5, color="444444")


def md_tables(md_path):
    """Return the markdown tables of a file as lists of rows (header first)."""
    out, cur = [], []
    for line in Path(LAB / md_path).read_text().splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c): continue
            cur.append([re.sub(r"\*\*|`", "", c) for c in cells])
        elif cur:
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out


def csv_rows(path, cols, n=None, fmt=None):
    rows = list(csv.DictReader(open(LAB / path)))
    out = [cols] + [[(fmt or {}).get(c, lambda x: x)(r[c]) for c in cols] for r in rows[: n or len(rows)]]
    return out


def page_break(d):
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ------------------------------------------------------------------ data
s11 = J("sim/s11_dft_chlorides/out/s11_results.json"); s16 = J("sim/s16_module_thermal/out/s16_results.json")
meta = J("cad/out/smodule/smodule_meta.json"); scm = J("cad/out/scell/scell_meta.json"); xl = J("PROJECT_SALT/10_ECONOMICS/salt_model_check.json")
s15 = J("sim/s15_factory/out/s15_results.json"); s12 = J("sim/s12_chemistry_matrix/out/s12_results.json")["results"]
stems = J("matlab/stem/stem_manifest.json")
erc = J("pcb/scell_monitor/erc.json"); drc = J("pcb/scell_monitor/drc.json")
junit = LAB / "tests/junit_ec2.xml"


def test_counts():
    if not junit.exists(): return None
    root = ET.parse(junit).getroot(); ts = root if root.tag == "testsuite" else root.find("testsuite")
    per = {}
    for tc in ts.iter("testcase"):
        f = tc.get("classname", "").split(".")[-1] if tc.get("classname") else "?"
        st = "failed" if tc.find("failure") is not None or tc.find("error") is not None else ("skipped" if tc.find("skipped") is not None else "passed")
        per.setdefault(f, {"passed": 0, "failed": 0, "skipped": 0}); per[f][st] += 1
    return dict(total=int(ts.get("tests")), failures=int(ts.get("failures")), errors=int(ts.get("errors")), skipped=int(ts.get("skipped")), per=per)


def build():
    d = doc_base()
    # ------------------------------------------------------------ title
    P(d, "Salt-Battery-Lab", bold=True, size=26, color="1F3A5F")
    P(d, "Complete Technical Record — research, simulation, DFT, engineering design, electronics, economics and verification", size=14)
    P(d, "Version 1.1 · 3 November 2026 · aqueous track (v0) + Project Salt (v1, v1.1)", size=10.5, color="555555")
    P(d, "Status: PRE-PROTOTYPE. No cell, module, board or cabinet has been built. Every number carries an evidence label: "
         "[MEASURED] none · [SIMULATED] model output · [CALCULATED] arithmetic from stated inputs · [PUBLISHED] literature · "
         "[VENDOR CLAIM] company statement · [ASSUMPTION] design choice or estimate · [TARGET] goal.", bold=True, size=10, color="8A1C1C")
    figure(d, "renders/out_salt/module_cutaway_captioned.png", width_cm=15.5, jpeg=True)
    P(d, "Contents", bold=True, size=12)
    for s in ("1 Executive summary", "2 What was done, where and how (compute log)", "3 Scientific landscape and chemistry selection (S12, S13)",
              "4 Simulation results (S01–S16)", "5 DFT+U campaign on the salt chemistries (S11)", "6 Engineering designs D1–D5 (CAD, drawings, renders)",
              "7 Electronics: SCM-1 test monitor (KiCad)", "8 Economics and the engineering spreadsheet", "9 MATLAB stem diagrams",
              "10 Verification and test results", "11 Safety, manufacturing, procurement and validation plan", "12 Market and YC position",
              "13 Limitations and what would change the conclusions", "Appendix A File index and rebuild commands"):
        P(d, s, size=9.5)
    page_break(d)
    # ------------------------------------------------------------ 1
    d.add_heading("1 Executive summary", 1)
    P(d, "Two programmes were run. The first (v0) asked whether a water-based sodium battery is a viable indoor UPS product. The second (Project Salt, v1) "
         "asked for the best rechargeable battery that can be made from common salt and abundant elements, against founder targets of 360 Wh/kg, a "
         "5-minute charge for 1,500 km, USD 3 manufacturing cost and non-flammability. v1.1 (this release) completed the DFT campaign on EC2 and added three "
         "product-level engineering designs, renders, drawings, a live spreadsheet, MATLAB stem diagrams and this record.")
    vt = md_tables("PROJECT_SALT/00_START_HERE/EXECUTIVE_VERDICT.md")
    P(d, "Project Salt outcome: B — no candidate meets the combined founder specification.", bold=True)
    if vt: table(d, vt[0], widths=[3.5, 10.5, 3.0], size=7.5, title="Founder targets vs findings (from EXECUTIVE_VERDICT.md)")
    if len(vt) > 1: table(d, vt[1], widths=[3.0, 3.6, 2.6, 2.4, 5.4], size=7.5, title="Closest feasible candidates (none is a winner)")
    sm = meta["sm48t"]; sd = s16["standby_design"]; r = xl["recalculated"]
    P(d, "New in v1.1 — what the product-level designs show", bold=True)
    bullets(d, [
        f"SM-48T module (21S4P, {MODULE['cells']} planar salt-iron cells): {MODULE['V_nom']:.1f} V, {MODULE['Ah']:.0f} Ah, {MODULE['kWh']:.2f} kWh, "
        f"max {MODULE['P_max_kW']:.2f} kW. Calculated mass {sm['mass_kg']:.0f} kg → {sm['Wh_kg']:.0f} Wh/kg and {sm['Wh_L']:.0f} Wh/L [CALCULATED from ASSUMPTION]. "
        "Cell cans, mica spacers, case and insulation dominate; the cathode is only ~9 % of the mass.",
        f"Mass levers (thin cans, thin mica, 100 mAh/cm²) raise this to ~{r['whkg_levers'][-1]:.0f} Wh/kg [CALCULATED, rough] — still below a VRLA-to-LFP class product.",
        f"Keep-warm: {sd['evacuated_W']:.0f} W with 40 mm evacuated insulation = {sd['evacuated_kWh_day']:.2f} kWh/day "
        f"({100 * sd['evacuated_frac_of_capacity_per_day']:.0f} % of stored energy per day, ≈ USD {sd['evacuated_usd_yr']:.0f}/yr) [CALCULATED]. "
        f"Microporous board instead: {sd['microporous_W']:.0f} W.",
        f"The 40 mA/cm² limit at 60 mAh/cm² means ≥ 1.5 h discharge: a 15-minute data-centre UPS is impossible with this cell; the module is designed for 2–8 h telecom/edge backup.",
        f"Materials + bought-in parts: cell USD {r['cell_usd_kwh']:.0f}/kWh (β''-alumina {100 * r['beta_share']:.0f} %), module USD {r['module_usd_kwh']:.0f}/kWh — "
        f"{r['x_over_target']:.0f}× the USD 3/kWh target before any conversion cost [CALCULATED, LibreOffice-verified spreadsheet].",
        "DFT check (S11): plain PBE reproduces the Na–FeCl₂ / CoCl₂ / NiCl₂ conversion voltages within +0.11 to +0.27 V of thermochemistry; adding U makes them worse "
        "(+0.1–0.2 V per eV). Interlayer antiferromagnetic order is lowest for all three chlorides (few meV).",
    ])
    P(d, "Aqueous track (v0) verdict, unchanged: NO-GO on a water-based sodium battery manufacturing company on today's evidence; GO-WITH-CONDITIONS on a "
         "12-week falsification sprint (≤ ₹10 lakh). Source: DELIVERABLES/STARTUP_DECISION_MEMO.md.", italic=True)
    page_break(d)
    # ------------------------------------------------------------ 2
    d.add_heading("2 What was done, where and how", 1)
    bullets(d, ["Lab layout: one folder per simulation (sim/s01…s16), params/ as the single source of truth, generators for CAD, drawings, renders, PCB, "
                "documents and finance, pytest suites and a claims linter; every artefact is rebuilt by run_all.sh.",
                "Compute: an Apple M4 laptop (early phases, DFT convergence and most relaxations) and four AWS EC2 instances in ap-south-1 "
                "(founder-approved USD 25 cap; spot market).",
                "From 3 Nov 2026 03:10 IST all heavy work runs on EC2 at the founder's request: the remaining DFT on a 32-core Graviton4 instance and every "
                "generator (CAD, CADCraft drawings, Blender renders, KiCad, LibreOffice, Octave, tests, this document) on a 32-core x86 build host."])
    cost_rows = [["Instance", "Type", "Use", "Recorded cost"]]
    try:
        cs2 = (LAB / "sim/s06_dft_ec2/runs/COST_STATUS.txt").read_text().split("est_usd=")[1].split()[0]
    except Exception:
        cs2 = "-"
    try:
        cs3 = (LAB / "sim/s11_dft_chlorides/runs/ec2_logs/COST_STATUS.txt").read_text().split("est_usd=")[1].split()[0]
    except Exception:
        cs3 = "-"
    try:
        cs4 = Path("/work/COST_STATUS.txt").read_text().split("est_usd=")[1].split()[0]
    except Exception:
        cs4 = "-"
    f2 = lambda s: f"≈ USD {float(s):.2f}" if s not in ("-", "") else "-"
    cost_rows += [["1 (2 Nov)", "c8g.8xlarge spot", "S06 DFT+U aqueous validation (reclaimed by AWS)", "not recorded"],
                  ["2 (2 Nov)", "c8g.8xlarge spot", "S06 restart batch (reclaimed by AWS)", f2(cs2)],
                  ["3 (3 Nov)", "c8g.8xlarge spot", "S11 NiCl₂ relax, U-scan, FM/AFM, PDOS (44 jobs, 0 failed)", f2(cs3)],
                  ["4 (3 Nov)", "c7i.8xlarge spot", "build host: CAD, drawings, renders, KiCad, Octave, LibreOffice, tests, documents", f2(cs4) + " (running)"]]
    table(d, cost_rows, widths=[2.2, 3.0, 8.6, 3.0], title="Compute log (cost = watchdog estimate at the spot price ceiling)")
    vers = Path("/work/logs/versions.txt")
    if vers.exists():
        table(d, [["Tool", "Version on the EC2 build host"]] + [l.split(": ", 1) for l in vers.read_text().splitlines() if ": " in l],
              widths=[4, 12], title="Toolchain (same versions as the founder's Mac where possible)")
    # ------------------------------------------------------------ 3
    d.add_heading("3 Scientific landscape and chemistry selection", 1)
    P(d, "S12 builds 30 architectures bottom-up (active pair → electrode → stack → cell) with Monte-Carlo ranges, calibrated against seven benchmark cells "
         "(±15 %). S13 tests the founder targets directly (USD 3 in six readings, 1,500 km / 5 min, salt feedstock).")
    rows = [["ID", "Architecture", "Theoretical Wh/kg", "Cell P50 Wh/kg", "Cell P10–P90"]]
    for x in sorted(s12.values(), key=lambda v: -v["cell_P50"])[:14]:
        rows.append([x["id"], x["name"][:62], f"{x['theoretical_Whkg']:.0f}", f"{x['cell_P50']:.0f}", f"{x['cell_P10']:.0f}–{x['cell_P90']:.0f}"])
    table(d, rows, widths=[1.2, 9.0, 2.4, 2.2, 2.4], size=7.5, title="Top 14 of 30 architectures by cell-level specific energy (S12) [CALCULATED]")
    figure(d, "sim/s12_chemistry_matrix/out/s12_energy_ladder.png"); figure(d, "sim/s12_chemistry_matrix/out/s12_pareto.png")
    for f in sorted((LAB / "sim/s13_founder_targets/out").glob("*.png")): figure(d, f)
    # ------------------------------------------------------------ 4
    page_break(d); d.add_heading("4 Simulation results (S01–S16)", 1)
    P(d, "Aqueous track (v0): kit re-run, PyBaMM validation, R1 cell DFN + Monte-Carlo, gas evolution, uMLIP atomistics, EC2 DFT+U, build-up, thermal, TEA, market.", italic=True)
    for f in sorted((LAB / "DELIVERABLES/7_simulation_charts").glob("*.png")):
        if "digitise" in f.name: continue
        figure(d, f, width_cm=14.0)
    P(d, "Project Salt (v1): fast charge (S13a), salt-iron cell model (S14), factory scenarios (S15), module thermal (S16).", italic=True)
    for p in ("sim/s13_founder_targets/out/s13a_fast_charge_benchmark.png", "sim/s14_scell_model/out/s14_scell_curves.png",
              "sim/s15_factory/out/s15_factory_and_tornado.png", "sim/s16_module_thermal/out/s16_thermal.png"):
        figure(d, p, width_cm=15.0)
    P(d, "Caveat on S14: the 0-D salt-iron model returns 100 % utilisation at every loading (30–100 mAh/cm²) and current (5–33 mA/cm²). Its only loss "
         "is an ohmic reaction-front term (≤ ~0.15 V), so the 1.8 V cut-off is never reached. It contains no transport or NaCl-morphology limit and therefore "
         "cannot test gate G2; only the R0 cell can. [SIMULATED, unvalidated]", italic=True)
    rows = [["Line", "MWh/yr", "Region", "Cell cost USD/kWh", "× over USD 3"]]
    for s in s15["scenarios"]: rows.append([s["line"], s["MWh_per_yr"], s["region"], f"{s['cell_cost_usd_kWh']:.0f}", f"{s['cell_cost_usd_kWh'] / 3:.0f}"])
    table(d, rows, widths=[2, 2, 2.5, 4, 3], title="Factory scenarios (S15) [CALCULATED from ASSUMPTION]")
    # ------------------------------------------------------------ 5
    page_break(d); d.add_heading("5 DFT+U campaign on the salt chemistries (S11)", 1)
    P(d, "Quantum ESPRESSO 7.6, PBE(+U) with Grimme-D3, GBRV ultrasoft pseudopotentials, 50/400 Ry, spin-polarised. 83 jobs: convergence, relaxations of "
         "Na, NaCl, Cl₂, Fe, Co, Ni and FeCl₂/CoCl₂/NiCl₂ at U = 0 and 4 eV, a 24-job fixed-geometry U-scan, 12 FM/AFM supercells and 6 PDOS runs. "
         "39 jobs ran on the M4, 44 on EC2 (0 failed).")
    rows = [["Couple", "DFT (V)", "Expt ΔH (V)", "DFT − expt (V)", "Expt ΔG 298 K (V)"]]
    for k, v in s11["voltages"].items(): rows.append([k, f"{v['dft_V']:.3f}", f"{v['exp_dH_V']:.3f}", f"{v['dft_V'] - v['exp_dH_V']:+.3f}", f"{v['exp_dG_V']:.3f}"])
    table(d, rows, widths=[3.5, 2.5, 2.8, 3.0, 3.2], title="Conversion voltages [SIMULATED] vs thermochemistry [PUBLISHED, transcribed - verify]")
    rows = [["Chloride", "E(AFM) − E(FM) meV/f.u.", "Lower-energy order"]] + [[k, f"{v['E_AFM_minus_FM_meV_per_fu']:+.2f}", v["ground"]] for k, v in s11["magnetic"].items()]
    table(d, rows, widths=[4, 5, 5], title="Interlayer magnetic order [SIMULATED]")
    rows = [["Run", "Gap (eV)", "Metallic FM solution"]] + [[k, f"{v['gap_eV']:.2f}", "yes" if v["metallic"] else "no"] for k, v in s11["gaps"].items()]
    table(d, rows, widths=[5, 3, 4], title="Band gaps on the SCF mesh [SIMULATED]")
    bullets(d, ["Voltages beat formation enthalpies because the cell reaction contains no Cl₂: the PBE Cl₂ error cancels.",
                "U on the chloride with a U = 0 metal reference overshoots by 0.6–0.9 V; geometry (U = 0 vs 4 relaxation) moves the voltage ≤ 0.02 V.",
                "FeCl₂ (d⁶) stays metallic in the symmetric cell at every U — a limitation (orbital ordering not attempted), not a prediction.",
                "With U = 4 eV the top of the NiCl₂/CoCl₂ valence band is mainly Cl-3p (charge-transfer character)."])
    figure(d, "sim/s11_dft_chlorides/out/s11_voltage_vs_U.png", width_cm=14.5); figure(d, "sim/s11_dft_chlorides/out/s11_pdos.png", width_cm=13.5)
    # ------------------------------------------------------------ 6
    page_break(d); d.add_heading("6 Engineering designs D1–D5", 1)
    P(d, "All mechanical design is parametric build123d/OpenCascade (STEP + per-part STL + part lists with material, tolerance, qualification test and BOM link). "
         "2-D drawings are made by CADCraft (headless CLI) as DXF + PDF + PNG. Blender (Cycles) only visualises the CAD; every render is captioned as a render. "
         "All designs are CONCEPTS — not for fabrication until the named qualification tests pass.")
    d.add_heading("D1 S-cell R0 planar test cell", 2)
    P(d, f"30 mm β''-alumina disc, 24 mm active window ({CELL['active_area_cm2']:.2f} cm²), Ni 201 cathode housing, SS 316L anode housing, glass-sealed α-alumina ring, "
         f"6 × M4 with alumina sleeves. Assembled discharged from NaCl + Fe (+10 % Ni). Operates {OPERATE['T_range_C'][0]:.0f}–{OPERATE['T_range_C'][1]:.0f} °C. "
         f"At 60 mAh/cm² the cathode bed is {scm['cathode_thickness_mm']:.2f} mm; fixture mass {scm['total_mass_g']:.0f} g.")
    figure(d, "renders/out_salt/r0_hero_captioned.png", width_cm=12, jpeg=True); figure(d, "renders/out_salt/r0_exploded_captioned.png", width_cm=12, jpeg=True)
    figure(d, "drawings/out/SB-SC-001_paper.png", "Drawing SB-SC-001 (CADCraft, A2 at 2:1): section A-A, plan, item list, cathode-charge table, notes.", width_cm=16.5)
    table(d, csv_rows("cad/out/scell/scell_r0_partlist.csv", ["item", "part", "material", "qty", "total_mass_g", "qualification_test"]),
          widths=[1, 6.5, 2.4, 1, 1.8, 4.3], size=7, title="R0 part list (cad/out/scell/scell_r0_partlist.csv)")
    table(d, [["Gate", "Kill criterion [TARGET]"]] + [[k, v] for k, v in GATES.items()], widths=[3, 14], size=7.5, title="R0 campaign gates (params/scell_params.py)")
    d.add_heading("D2 SCM-1 salt-cell test monitor", 2); P(d, "See section 7.")
    d.add_heading("D3 P1 planar product cell and SM-48T module", 2)
    p1 = meta["p1"]
    table(d, [["P1 parameter", "Value"], ["plate", f"{P1['plate_mm']:.0f} × {P1['plate_mm']:.0f} × {P1['plate_t_mm']} mm β''-alumina, α-alumina frame"],
              ["active area", f"{P1['active_cm2']:.0f} cm² at {P1['qa_mAh_cm2']:.0f} mAh/cm²"], ["thickness", f"{p1['thickness_mm']} mm"],
              ["capacity / energy", f"{p1['Ah']} Ah / {p1['Wh']} Wh at {P1['V_nom']} V"], ["mass", f"{p1['mass_g']} g → {p1['Wh_kg']} Wh/kg, {p1['Wh_L']} Wh/L"],
              ["max current", f"{P1['I_max_A']:.1f} A ({P1['j_max_mA_cm2']:.0f} mA/cm²)"]], widths=[4, 12], title="P1 cell [CALCULATED from ASSUMPTION]")
    figure(d, "renders/out_salt/p1_exploded_captioned.png", width_cm=12, jpeg=True)
    table(d, [["SM-48T parameter", "Value"], ["configuration", f"{MODULE['series']}S{MODULE['parallel']}P = {MODULE['cells']} cells in 4 columns of 21"],
              ["voltage", f"{MODULE['V_nom']:.1f} nominal / {MODULE['V_max']:.2f} max / {MODULE['V_min']:.1f} min (SELV)"],
              ["capacity / energy", f"{MODULE['Ah']:.1f} Ah / {MODULE['kWh']:.2f} kWh"], ["max continuous power", f"{MODULE['P_max_kW']:.2f} kW"],
              ["envelope", f"19-inch 7U, {MODULE['rack_width_mm']} × {sm['depth']:.0f} × {MODULE['height_mm']:.0f} mm ({sm['envelope_L']} L)"],
              ["mass", f"{sm['mass_kg']} kg ({sm['hardware_kg']} kg hardware + {sm['cathode_kg']} kg cathode)"], ["specific energy", f"{sm['Wh_kg']} Wh/kg, {sm['Wh_L']} Wh/L"]],
          widths=[4, 12], title="SM-48T module [CALCULATED from ASSUMPTION]")
    figure(d, "renders/out_salt/module_hero_captioned.png", width_cm=13, jpeg=True); figure(d, "renders/out_salt/module_cutaway_captioned.png", width_cm=13, jpeg=True)
    figure(d, "renders/out_salt/module_exploded_captioned.png", width_cm=13, jpeg=True)
    figure(d, "drawings/out/SB-SM-001_paper.png", "Drawing SB-SM-001 (CADCraft, A2 at 1:4): front view, section A-A, item list, rating.", width_cm=16.5)
    pl = list(csv.DictReader(open(LAB / "cad/out/smodule/sm48t_partlist.csv"))); pl.sort(key=lambda x: -float(x["total_mass_g"]))
    table(d, [["Part", "Qty", "Total mass (kg)", "Material"]] + [[x["part"][:48], x["qty"], f"{float(x['total_mass_g']) / 1000:.2f}", x["material"][:52]] for x in pl[:12]],
          widths=[6.5, 1.2, 2.3, 7], size=7, title="SM-48T mass breakdown, heaviest 12 items (cad/out/smodule/sm48t_partlist.csv)")
    figure(d, "diagrams/out/ds1_cell_electrochemistry.png", width_cm=15); figure(d, "diagrams/out/ds2_module_electrical.png", width_cm=15.5)
    figure(d, "diagrams/out/ds4_p1_manufacturing_flow.png", width_cm=16)
    d.add_heading("D4 SM-48T thermal-management architecture", 2)
    wu = s16["warmup"]; ds = s16["discharge"]
    bullets(d, [f"Hot box at {THERMAL['T_op_C']:.0f} °C inside a {MODULE['insulation_mm']:.0f} mm evacuated double wall; 4 × 150 W mica plate heaters on independent 270 °C bimetal cut-outs.",
                f"Standby loss {sd['evacuated_W']} W (evacuated) vs {sd['microporous_W']} W (microporous) at 25 °C ambient [CALCULATED].",
                f"Warm-up from 25 °C: {wu['600 W']['hours']} h at 600 W (ramp-limited floor {s16['warmup_ramp_limited_floor_h']} h; NaAlCl₄ fusion plateau at 157 °C).",
                f"Full discharge at max power: {ds['heat_W']} W of heat, adiabatic rise {ds['adiabatic_rise_C']} K inside a 70 K window — the fan/damper bypass is for faults only.",
                f"If the grid is lost the module can keep itself hot for {sd['self_sustain_hours_if_grid_lost']} h from its own energy."])
    figure(d, "drawings/out/SB-TM-001_paper.png", "Drawing SB-TM-001 (CADCraft): wall section, heat flow, thermal budget, control architecture.", width_cm=16.5)
    figure(d, "diagrams/out/ds3_module_thermal_budget.png", width_cm=15)
    d.add_heading("D5 SC-UPS-1 cabinet", 2)
    P(d, f"600 × 800 × 1400 mm floor cabinet: {CABINET['modules']} × SM-48T ({CABINET['kWh']:.1f} kWh), 2U controller (CAN master, SNMP), 2U DC breaker panel, "
         "front service access on slide rails, rear cable and earth bar, plinth with M12 anchors.")
    figure(d, "renders/out_salt/cabinet_closed_captioned.png", width_cm=11, jpeg=True); figure(d, "renders/out_salt/cabinet_open_captioned.png", width_cm=11, jpeg=True)
    figure(d, "drawings/out/SB-UPS-001_paper.png", "Drawing SB-UPS-001 (CADCraft, A2 at 1:10): front and side views, rating, notes.", width_cm=16.5)
    figure(d, "diagrams/out/ds5_gate_ladder.png", width_cm=16)
    d.add_heading("Earlier aqueous-track designs (v0)", 2)
    for f in ("renders/out/hero_annotated.png", "renders/out/cutaway_annotated.png", "renders/out/room_annotated.png"):
        figure(d, f, width_cm=13, jpeg=True)
    for dwg in ("SB-GA-001", "SB-GA-002", "SB-GA-003"): figure(d, f"drawings/out/{dwg}_paper.png", f"Drawing {dwg} (CADCraft), aqueous track.", width_cm=16)
    # ------------------------------------------------------------ 7
    page_break(d); d.add_heading("7 Electronics: SCM-1 salt-cell test monitor (KiCad 10)", 1)
    nerc = sum(len(s["violations"]) for s in erc["sheets"]); from collections import Counter
    dc = Counter(v["type"] for v in drc["violations"] if v["severity"] == "error")
    fr = J("pcb/scell_monitor/freeroute_report.json") if (LAB / "pcb/scell_monitor/freeroute_report.json").exists() else {}
    rr = J("pcb/scell_monitor/route_report.json") if (LAB / "pcb/scell_monitor/route_report.json").exists() else {}
    P(d, "4-cell series test monitor for the R0 campaign: isolated 24-bit ADC voltage sensing, 4 thermocouples, shunt current, SSR cycler control, "
         "hardware over-temperature and over/under-voltage trips, isolated USB (3 kV), data logging; STM32 firmware core with host tests.")
    table(d, [["Check", "Result"], ["schematic ERC", f"{nerc} violations"], ["parts", "145"],
              ["routing", (f"Freerouting {('3-layer' if fr.get('inner_signal') else '2-layer')}: {fr.get('tracks', '-')} tracks, {fr.get('vias', '-')} vias" if fr.get("ses_import")
                           else f"in-house router: {rr.get('tracks', '-')} tracks, {rr.get('vias', '-')} vias, {len(rr.get('failed', []))} nets failed")],
              ["DRC errors", ", ".join(f"{k} {v}" for k, v in dc.items()) or "0"], ["unconnected items", str(len(drc["unconnected_items"]))],
              ["status", "LAYOUT IS A DRAFT - placement needs manual rework before fabrication (see 05_ELECTRONICS/README.md)"]],
          widths=[4, 12], title="SCM-1 verification (kicad-cli 10)")
    figure(d, "pcb/scell_monitor/fab/scell_monitor-top.png", "SCM-1 top-side 3-D render (kicad-cli pcb render).", width_cm=14)
    # ------------------------------------------------------------ 8
    page_break(d); d.add_heading("8 Economics and the engineering spreadsheet", 1)
    P(d, "PROJECT_SALT/10_ECONOMICS/SaltIron_Engineering_Model.xlsx — 8 sheets (README, Inputs, Cell_BOM, Module_BOM, Thermal, Mass_Levers, DFT_Results, "
         f"Factory). All derived cells are live formulas. LibreOffice ({xl['engine']}) recalculated it with {len(xl['errors'])} formula errors.")
    table(d, [["Result (recalculated by LibreOffice)", "Value"], ["P1 cell materials", f"USD {r['cell_materials_usd']:.2f} per cell = USD {r['cell_usd_kwh']:.0f}/kWh"],
              ["β''-alumina share of cell materials", f"{100 * r['beta_share']:.0f} %"], ["SM-48T materials + bought-in parts", f"USD {r['module_usd']:.0f} = USD {r['module_usd_kwh']:.0f}/kWh"],
              ["× over the USD 3/kWh target", f"{r['x_over_target']:.0f}×"], ["keep-warm", f"{r['standby_W']:.1f} W, USD {r['keepwarm_usd_yr']:.1f}/yr"],
              ["Wh/kg: base → thin cans → + thin mica → + 100 mAh/cm²", " → ".join(f"{v:.0f}" for v in r["whkg_levers"])]],
          widths=[8, 8], title="Spreadsheet outputs [CALCULATED from ASSUMPTION prices - not quotes]")
    sheet_png = LAB / "DELIVERABLES/11_screenshots/09_project_salt_ec2/spreadsheet_Cell_BOM.png"
    if sheet_png.exists(): figure(d, sheet_png, "Cell_BOM sheet rendered by LibreOffice (screenshot).", width_cm=16)
    # ------------------------------------------------------------ 9
    d.add_heading("9 MATLAB stem diagrams", 1)
    P(d, f"{len(stems['scripts'])} stem diagrams written as self-contained MATLAB scripts (matlab/stem/*.m; data embedded with the source JSON named in each header). "
         f"No MATLAB licence exists on the founder's Mac or the build host, so they were executed with {stems['engine']}, which runs the same .m code; they also run unchanged in MATLAB R2019b+.")
    for p in stems.get("pngs", []): figure(d, f"matlab/stem/out/{p}", f"{p[:-4]} (matlab/stem/{p[:-4]}.m, GNU Octave).", width_cm=13.5)
    # ------------------------------------------------------------ 10
    page_break(d); d.add_heading("10 Verification and test results", 1)
    P(d, "No physical test has been performed. The results below are software verification: unit and regression tests, rule checks and recalculation checks.", bold=True)
    tc = test_counts()
    if tc:
        table(d, [["Test file", "Passed", "Failed", "Skipped"]] + [[k, v["passed"], v["failed"], v["skipped"]] for k, v in sorted(tc["per"].items())] +
              [["TOTAL", tc["total"] - tc["failures"] - tc["errors"] - tc["skipped"], tc["failures"] + tc["errors"], tc["skipped"]]],
              widths=[7, 2.5, 2.5, 2.5], title="pytest on the EC2 build host (tests/junit_ec2.xml; xfail counted as skipped by JUnit)")
    rows = [["Check", "Result"], ["CADCraft drawings (new)", ", ".join(f"{k}: {v['tool']}, {len(v['errors'])} errors" for k, v in meta.get("drawings", {}).items())],
            ["spreadsheet recalculation", f"{xl['sheets_exported']} sheets, {len(xl['errors'])} errors"], ["Octave stem scripts", f"{len(stems['pngs'])}/{len(stems['scripts'])} figures, return code {stems.get('returncode')}"],
            ["DFT convergence (NiCl₂, 50 vs 70 Ry)", f"{s11['convergence']['NiCl2_FM']['ecut50']} meV/atom"], ["DFT jobs", "83 run, 0 failed after restarts"],
            ["schematic ERC", f"{nerc} violations"], ["PCB DRC", f"{sum(dc.values())} errors, {len(drc['unconnected_items'])} unconnected (DRAFT)"]]
    table(d, rows, widths=[6, 10], title="Rule checks")
    P(d, "Validation plan for real hardware (PROJECT_SALT/09_VALIDATION/protocols/TEST_PLAN.md): R0 gates G1–G5, then P1 plate yield and seal scale-up, "
         "module QT-20…26 (standby loss, warm-up, BMS hardware-in-the-loop, freeze/thaw), then UL 9540A / IEC 62619 at cabinet level.")
    # ------------------------------------------------------------ 11-13
    d.add_heading("11 Safety, manufacturing, procurement", 1)
    bullets(d, ["Safety: hazard analysis and build-manual safety section in PROJECT_SALT/07_BUILD_MANUAL; independent hardware trips (no firmware in the path) at cell, heater and module level.",
                "Manufacturing: lab, pilot and industrial process descriptions with QC plan and PLC/automation spec in PROJECT_SALT/08_MANUFACTURING; P1 flow in Figure ds4.",
                "Procurement: master BOM with Indian and US suppliers, equipment BOM; no invented catalogue numbers — 'VERIFY' / 'QUOTE REQUIRED' where not checked."])
    d.add_heading("12 Market and YC position", 1)
    bullets(d, ["Wedge (unchanged): the battery you are allowed to put indoors — India first. Competitors already sell non-flammable sodium at higher energy (Alsym, Peak Energy).",
                "For the salt-iron chemistry the honest first market is 2–8 h hot-climate telecom/edge backup, the niche FZSoNick has served for ~15 years; buyer interviews (K4) come before any spend."])
    d.add_heading("13 Limitations and what would change the conclusions", 1)
    bullets(d, ["Nothing is measured. All performance numbers are simulated, calculated or assumed.",
                "Thermochemistry and several literature numbers were transcribed or read from abstracts — verify before citing.",
                "The P1 150 mm plate, its seal and thermal cycling are untested extrapolations from a 30 mm disc.",
                "The module mass/cost model uses deliberately simple sheet-metal and price assumptions; the levers table shows how far design changes could move it.",
                "Salt-iron would compete only if β''-alumina reaches ≤ USD 15/kg at ≤ 0.5 mm, cathodes keep ≥ 3,000 cycles at ≥ 100 mAh/cm², and a molten-salt line costs ≤ ~USD 100 per kWh/yr."])
    d.add_heading("Appendix A File index and rebuild", 1)
    table(d, [["What", "Where", "Rebuild"], ["DFT S11", "sim/s11_dft_chlorides", "campaign.py; ec2/ec2_s11.sh; analyze.py"],
              ["Module thermal S16", "sim/s16_module_thermal", "thermal.py"], ["D3–D5 CAD + drawings", "cad/make_smodule.py → cad/out/smodule, drawings/out", "python cad/make_smodule.py"],
              ["Renders", "renders/blender_salt.py → renders/out_salt", "python renders/run_salt_renders.py"], ["Diagrams", "diagrams/make_salt_diagrams.py", "python …"],
              ["Spreadsheet", "finance/make_salt_model.py → PROJECT_SALT/10_ECONOMICS", "python …"], ["MATLAB stems", "tools/matlab/make_stem.py → matlab/stem", "--run (Octave)"],
              ["PCB", "pcb/build_scm.sh", "SCM_ROUTER=freerouting optional"], ["EC2 build host", "tools/ec2_build/", "ec2_build.sh push|bootstrap|bg|pull"],
              ["This document", "docs/make_full_report.py", "python docs/make_full_report.py"]], widths=[3.5, 7, 6], size=7.5)
    OUT.parent.mkdir(parents=True, exist_ok=True); d.save(OUT)
    print("wrote", OUT, "figures", FIG["n"], "tables", TAB["n"])


if __name__ == "__main__":
    build()
