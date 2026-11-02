"""SaltBattery_Complete_Technical_Deck.pptx - full-information deck (designs, charts, simulation and verification results).

python-pptx on the EC2 build host. Every number is read from result files at build time. Simple data are native PowerPoint
charts (editable); renders, drawings and multi-panel scientific plots are images. Palette 'salt & iron': slate, salt white,
iron-oxide rust, sea teal. Cambria titles / Calibri body. Speaker notes carry sources and labels.
Usage: python docs/make_full_deck.py
"""
from __future__ import annotations
import csv, json, sys, xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

LAB = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(LAB))
from params.smodule_params import CABINET, MODULE, P1  # noqa: E402
OUT = LAB / "DELIVERABLES/1_investor_docs/SaltBattery_Complete_Technical_Deck.pptx"
J = lambda p: json.load(open(LAB / p))
SLATE, INK, MUTED, RUST, TEAL, SALT, LINE, WHITE = "22303A", "1E2328", "5F6B73", "B4532A", "2A7F86", "F3F5F4", "D5DADD", "FFFFFF"
HEAD, BODY = "Cambria", "Calibri"
W, H = 13.333, 7.5
prs = Presentation(); prs.slide_width = Inches(W); prs.slide_height = Inches(H); BLANK = prs.slide_layouts[6]
TMP = Path("/tmp/deck_img"); TMP.mkdir(exist_ok=True)
rgb = RGBColor.from_string


def bg(slide, color):
    f = slide.background.fill; f.solid(); f.fore_color.rgb = rgb(color)


def text(slide, x, y, w, h, s, size=16, color=INK, bold=False, font=BODY, align=PP_ALIGN.LEFT, italic=False, anchor=MSO_ANCHOR.TOP, name=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.02); tf.vertical_anchor = anchor
    lines = s if isinstance(s, list) else [s]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        r = p.add_run(); r.text = ln; r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic; r.font.name = font; r.font.color.rgb = rgb(color)
    if name: tb.name = name
    return tb


def bullets(slide, x, y, w, h, items, size=15, color=INK, gap=6):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.space_after = Pt(gap)
        pPr = p._p.get_or_add_pPr(); pPr.set("marL", str(Emu(Inches(0.22)))); pPr.set("indent", str(-Emu(Inches(0.22))))
        bu = pPr.makeelement("{http://schemas.openxmlformats.org/drawingml/2006/main}buChar", {"char": "•"}); pPr.append(bu)
        r = p.add_run(); r.text = it; r.font.size = Pt(size); r.font.name = BODY; r.font.color.rgb = rgb(color)
    return tb


def title(slide, s, dark=False, sub=None):
    text(slide, 0.6, 0.38, 12.1, 0.8, s, 32 if len(s) <= 44 else 28, WHITE if dark else SLATE, True, HEAD, name="Title")
    if sub: text(slide, 0.6, 1.12, 12.1, 0.45, sub, 15, "C9D1D6" if dark else MUTED, italic=True)


def card(slide, x, y, w, h, fill=SALT):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = 0.06; s.fill.solid(); s.fill.fore_color.rgb = rgb(fill); s.line.fill.background(); s.shadow.inherit = False
    return s


def stat(slide, x, y, w, big, label, color=RUST, dark=False):
    card(slide, x, y, w, 1.55, "2C3B46" if dark else SALT)
    text(slide, x + 0.2, y + 0.12, w - 0.4, 0.8, big, 34 if len(big) <= 7 else (28 if len(big) <= 10 else 24), color, True, HEAD)
    text(slide, x + 0.2, y + 0.92, w - 0.4, 0.6, label, 12, "D9DEE1" if dark else MUTED)


def picture(slide, path, x, y, w, h, caption=None, cap_color=MUTED):
    p = LAB / path
    if not p.exists():
        text(slide, x, y, w, 0.4, f"[missing {path}]", 11, "AA0000"); return
    im = Image.open(p).convert("RGB"); r = min(w / (im.width / 150), h / (im.height / 150)); pw, ph = im.width / 150 * r, im.height / 150 * r
    if im.width > 2000: im = im.resize((2000, int(im.height * 2000 / im.width)))
    t = TMP / (p.stem + ".jpg"); im.save(t, quality=90)
    slide.shapes.add_picture(str(t), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))
    if caption: text(slide, x, y + h + 0.05, w, 0.35, caption, 10.5, cap_color, italic=True)


def notes(slide, s):
    slide.notes_slide.notes_text_frame.text = s


def chart_style(ch, colors, legend=False, labels=True, fmt='0.00', size=11):
    ch.font.size = Pt(size); ch.font.name = BODY; ch.font.color.rgb = rgb(MUTED)
    ch.has_legend = legend
    if legend: ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(11)
    for i, s in enumerate(ch.series):
        s.format.fill.solid(); s.format.fill.fore_color.rgb = rgb(colors[i % len(colors)])
        if labels:
            s.data_labels.show_value = True; s.data_labels.number_format = fmt; s.data_labels.number_format_is_linked = False
            s.data_labels.font.size = Pt(10); s.data_labels.font.color.rgb = rgb(INK); s.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    try:
        ch.value_axis.major_gridlines.format.line.color.rgb = rgb(LINE); ch.value_axis.format.line.fill.background()
        ch.value_axis.tick_labels.font.size = Pt(10); ch.category_axis.tick_labels.font.size = Pt(10)
    except Exception:
        pass


def slide(dark=False):
    s = prs.slides.add_slide(BLANK); bg(s, SLATE if dark else WHITE)
    if not dark:
        text(s, 0.6, 7.05, 9, 0.3, "Salt-Battery-Lab · complete technical record · concept / pre-prototype — nothing measured", 9, "9AA3A8")
    text(s, 12.2, 7.05, 0.6, 0.3, str(len(prs.slides._sldIdLst)), 9, "9AA3A8" if not dark else "8C9AA3", align=PP_ALIGN.RIGHT)
    return s


# ------------------------------------------------------------------ data
s11 = J("sim/s11_dft_chlorides/out/s11_results.json"); s16 = J("sim/s16_module_thermal/out/s16_results.json"); meta = J("cad/out/smodule/smodule_meta.json")
xl = J("PROJECT_SALT/10_ECONOMICS/salt_model_check.json")["recalculated"]; s15 = J("sim/s15_factory/out/s15_results.json")["scenarios"]
s12 = J("sim/s12_chemistry_matrix/out/s12_results.json")["results"]; stems = J("matlab/stem/stem_manifest.json")
drc = J("pcb/scell_monitor/drc.json"); erc = J("pcb/scell_monitor/erc.json"); sm = meta["sm48t"]; sd = s16["standby_design"]
fra = J("pcb/scell_monitor/freeroute_attempts.json") if (LAB / "pcb/scell_monitor/freeroute_attempts.json").exists() else {"attempts": []}


def tests():
    p = LAB / "tests/junit_ec2.xml"
    if not p.exists(): return None
    r = ET.parse(p).getroot(); t = r if r.tag == "testsuite" else r.find("testsuite")
    return {k: int(t.get(k)) for k in ("tests", "failures", "errors", "skipped")}


def build():
    # 1 title
    s = slide(True)
    text(s, 0.6, 1.2, 6.3, 1.6, "Salt-Battery-Lab", 44, WHITE, True, HEAD)
    text(s, 0.6, 2.35, 6.2, 1.4, "Complete technical record: research, DFT, simulation, engineering designs, electronics, economics, verification", 20, "D9DEE1")
    text(s, 0.6, 4.1, 6.0, 0.9, ["v1.1 · 3 November 2026", "Pre-prototype: nothing in this deck is measured"], 15, "C9D1D6")
    picture(s, "renders/out_salt/module_cutaway.png", 6.9, 0.9, 6.0, 5.6)
    notes(s, "Every number in this deck is read from the lab's result files at build time (docs/make_full_deck.py). Labels: SIMULATED, CALCULATED, PUBLISHED, VENDOR CLAIM, ASSUMPTION, TARGET.")
    # 2 answer
    s = slide(True); title(s, "The answer: salt is almost free, the battery is not", True, "Project Salt outcome B — no candidate meets 360 Wh/kg + 5-min / 1,500 km + USD 3 + non-flammable")
    best = max((v for v in s12.values() if not v["benchmark"]), key=lambda v: v["cell_P50"])
    stat(s, 0.6, 2.0, 2.9, f"{best['cell_P50']:.0f}", f"Wh/kg — best non-lithium cell ({best['id']}, P50) vs 360 target", RUST, True)
    stat(s, 3.7, 2.0, 2.9, "3.8 MW", "to charge a 1,500 km SUV in 5 minutes", "E9A07A", True)
    s03 = [x for x in s15 if x["line"] == "S03" and x["MWh_per_yr"] == 1000 and x["region"] == "India"][0]
    stat(s, 6.8, 2.0, 2.9, f"${s03['cell_cost_usd_kWh']:.0f}", "per kWh — salt-iron cell at 1 GWh/yr in India (S15)", "7FC4C8", True)
    stat(s, 9.9, 2.0, 2.9, "$0.26", "per kWh — theoretical salt + iron reactant cost", "F1D3B5", True)
    bullets(s, 0.6, 4.0, 12.1, 2.6, ["Salt is the active material only in metal-chloride (ZEBRA-type) and Na–Cl₂ cells; both run hot or use toxic chemicals.",
                                     "The one testable lever: thin β''-alumina (≤ 0.5 mm) with thick salt-iron cathodes (≥ 75 mAh/cm²) — the R0 test cell exists to test it.",
                                     "Aqueous track (v0): no-go as a factory company; a 12-week falsification sprint first."], 16, "E3E7EA")
    notes(s, "Sources: EXECUTIVE_VERDICT.md, S12 results, S13 targets, S15 factory. All CALCULATED from ASSUMPTION.")
    # 3 what we did
    s = slide(); title(s, "What was done — and where it ran", sub="One-source parameters → simulations → designs → documents, rebuilt by scripts")
    steps = [("Research", "30 architectures,\n164 sources, patents"), ("Simulate", "S01–S16: DFN, MC,\nfactory, thermal"), ("DFT", "83 QE jobs\nM4 + EC2, 0 failed"),
             ("Design", "5 designs: CAD,\nCADCraft drawings"), ("Visualise", "Blender Cycles\nrenders, turntable"), ("Verify", f"pytest, ERC/DRC,\nLibreOffice, Octave")]
    for i, (h, b) in enumerate(steps):
        x = 0.6 + i * 2.07; card(s, x, 1.9, 1.85, 2.2, SALT)
        c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.65), Inches(2.05), Inches(0.55), Inches(0.55)); c.fill.solid(); c.fill.fore_color.rgb = rgb(RUST if i % 2 == 0 else TEAL); c.line.fill.background()
        text(s, x + 0.65, 2.1, 0.55, 0.45, str(i + 1), 16, WHITE, True, HEAD, PP_ALIGN.CENTER)
        text(s, x + 0.1, 2.7, 1.65, 0.4, h, 17, SLATE, True, HEAD, PP_ALIGN.CENTER); text(s, x + 0.1, 3.15, 1.65, 0.9, b.split("\n"), 12, MUTED, align=PP_ALIGN.CENTER)
    t = tests()
    bullets(s, 0.6, 4.5, 12.1, 2.3, ["Compute: Apple M4 for early work; four EC2 spot instances (USD 25 cap). Since 3 Nov 03:10 IST every heavy job runs on EC2.",
                                     "Build host (c7i.8xlarge, 32 cores): Blender 5.0.1, KiCad 10.0.8, CADCraft 0.15.1, LibreOffice 24.2, Octave 8.4, Freerouting 2.1, build123d 0.13.",
                                     f"Verification: {t['tests'] - t['failures'] - t['errors'] - t['skipped']} tests passed, {t['failures'] + t['errors']} failed, {t['skipped']} skipped/xfail." if t else "Verification: see slide 20."], 15)
    # 4 landscape
    s = slide(); title(s, "Thirty architectures, one ceiling", sub="Cell-level specific energy, calibrated build-up (S12) [CALCULATED]")
    picture(s, "sim/s12_chemistry_matrix/out/s12_energy_ladder.png", 0.6, 1.7, 7.6, 5.1)
    bullets(s, 8.5, 1.9, 4.3, 4.8, [f"Best non-lithium: {best['id']} at {best['cell_P50']:.0f} Wh/kg (P50).", "Only lithium benchmarks pass 360 Wh/kg.",
                                    "The model reproduces seven benchmark cells within ±15 %.", "Aqueous Na-ion (v0 track) is dominated: 19–26 Wh/kg."], 15)
    # 5 founder targets table
    s = slide(); title(s, "Founder targets against physics and economics", sub="From EXECUTIVE_VERDICT.md")
    rows = [("360 Wh/kg cell", "No non-lithium design reaches it, even at P90", "CALCULATED"),
            ("5 min for 1,500 km", "3.8 MW per car; validated Li model reaches ~31 % in 5 min at 10C", "CALC / SIMULATED"),
            ("USD 3 manufacturing", "Inactive parts alone exceed USD 3/kWh; floors USD 41–152/kWh", "CALCULATED"),
            ("Non-flammable, from salt", "Met only by hot metal-chloride cells; Na–Cl₂ fails toxicity", "PUBLISHED / CALC")]
    tb = s.shapes.add_table(len(rows) + 1, 3, Inches(0.6), Inches(1.8), Inches(12.1), Inches(4.4)).table
    for j, (hd, wd) in enumerate((("Target", 2.8), ("Finding", 7.2), ("Label", 2.1))):
        tb.columns[j].width = Inches(wd); c = tb.cell(0, j); c.text = hd
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row): tb.cell(i, j).text = v
    for i in range(len(rows) + 1):
        for j in range(3):
            c = tb.cell(i, j); c.fill.solid(); c.fill.fore_color.rgb = rgb(SLATE if i == 0 else (SALT if i % 2 else WHITE))
            for p in c.text_frame.paragraphs:
                for r in p.runs: r.font.size = Pt(15 if i else 14); r.font.name = BODY; r.font.bold = i == 0; r.font.color.rgb = rgb(WHITE if i == 0 else INK)
    # 6 fast charge + cost
    s = slide(); title(s, "Fast charging and USD 3/kWh fail on physics", sub="S13a PyBaMM (validated Li-ion benchmark) and S13 six readings of USD 3")
    picture(s, "sim/s13_founder_targets/out/s13a_fast_charge_benchmark.png", 0.6, 1.75, 6.0, 4.8); picture(s, "sim/s13_founder_targets/out/s13b_three_dollar.png", 6.8, 1.75, 6.0, 4.8)
    # 7 DFT native chart
    s = slide(); title(s, "DFT matches salt-cathode voltages to 0.11–0.27 V", sub="Quantum ESPRESSO 7.6, PBE-D3 (U = 0) vs experimental ΔH — S11, 83 jobs (44 on EC2)")
    keys = ["Na+1/2Cl2", "FeCl2_U0", "CoCl2_U0", "NiCl2_U0"]; cd = CategoryChartData(); cd.categories = ["Na + ½Cl₂", "FeCl₂", "CoCl₂", "NiCl₂"]
    cd.add_series("DFT (PBE-D3)", [s11["voltages"][k]["dft_V"] for k in keys]); cd.add_series("Experiment (ΔH)", [s11["voltages"][k]["exp_dH_V"] for k in keys])
    ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.7), Inches(7.6), Inches(5.1), cd).chart
    chart_style(ch, [RUST, TEAL], legend=True); ch.value_axis.maximum_scale = 4.8; ch.value_axis.minimum_scale = 0
    bullets(s, 8.5, 1.9, 4.3, 4.8, ["The Cl₂ error cancels: the cell reaction contains no Cl₂.", "Adding U overshoots by 0.6–0.9 V (+0.1–0.2 V per eV).",
                                    "Interlayer AFM order is lowest in all three chlorides (few meV).", "FeCl₂ stays metallic in the symmetric cell — a limitation."], 15)
    notes(s, "Native chart; data from sim/s11_dft_chlorides/out/s11_results.json. Experimental values transcribed from NBS/CRC tables - verify.")
    # 8 DFT images
    s = slide(); title(s, "U sensitivity and electronic structure", sub="Fixed-geometry U-scan (24 jobs) and projected DOS (6 jobs), EC2 c8g.8xlarge")
    picture(s, "sim/s11_dft_chlorides/out/s11_voltage_vs_U.png", 0.6, 1.7, 6.0, 4.9); picture(s, "sim/s11_dft_chlorides/out/s11_pdos.png", 6.9, 1.6, 5.8, 5.2)
    # 9 cell model + electrochemistry
    s = slide(); title(s, "Salt-iron cell: made from salt, limited by current", sub="S14 0-D model [SIMULATED, unvalidated]: it predicts 100 % utilisation everywhere, so it cannot test gate G2")
    picture(s, "diagrams/out/ds1_cell_electrochemistry.png", 0.6, 1.7, 6.1, 4.9); picture(s, "sim/s14_scell_model/out/s14_scell_curves.png", 6.9, 1.7, 5.9, 4.9)
    # 10 D1
    s = slide(); title(s, "D1 · S-cell R0: the test that decides everything", sub="30 mm β''-alumina disc, salt-iron cathode at 30 / 60 / 100 mAh/cm², 190 °C")
    picture(s, "renders/out_salt/r0_exploded.png", 0.6, 1.6, 4.6, 5.2); picture(s, "drawings/out/SB-SC-001_paper.png", 5.4, 1.7, 7.3, 3.4, "Drawing SB-SC-001 (CADCraft, 2:1)")
    bullets(s, 5.5, 5.4, 7.2, 1.5, ["Kill gates G1–G5: replication, ≥ 80 % at 60 mAh/cm², CE ≥ 99.9 %, ≤ 1 kg β''/kWh, seal survives 20 cycles."], 14)
    # 11 D2 PCB
    s = slide(); title(s, "D2 · SCM-1: schematic clean, layout a draft", sub="KiCad 10 · 145 parts · isolated ADC sensing, 4 thermocouples, hardware trips, isolated USB")
    picture(s, "DELIVERABLES/11_screenshots/09_project_salt_ec2/kicad_pcb_top.png", 0.6, 1.7, 7.0, 5.0)
    from collections import Counter
    dc = Counter(v["type"] for v in drc["violations"] if v["severity"] == "error"); nerc = sum(len(x["violations"]) for x in erc["sheets"])
    att = "; ".join(f"{a['config'].split(',')[0]}: best {a['best_unrouted']} unrouted" for a in fra["attempts"]) or "-"
    bullets(s, 7.9, 1.9, 4.9, 4.9, [f"ERC: {nerc} violations.", f"DRC: {sum(dc.values())} errors, {len(drc['unconnected_items'])} unconnected (in-house router).",
                                    f"Freerouting on EC2 — {att}.", "Verdict: placement needs manual rework before fabrication. Gerbers are for review only."], 14)
    # 12 D3 P1 + module spec
    s = slide(); title(s, "D3 · From a 30 mm disc to a 48 V module", sub="P1 planar cell (150 mm plate) and SM-48T 7U module — concept [CALCULATED from ASSUMPTION]")
    picture(s, "renders/out_salt/p1_exploded.png", 0.6, 1.8, 4.3, 4.3, "P1 cell exploded: anode can | β'' plate + α frame | cathode can")
    for i, (big, lab) in enumerate(((f"{MODULE['kWh']:.2f} kWh", f"{MODULE['series']}S{MODULE['parallel']}P · {MODULE['V_nom']:.1f} V · {MODULE['Ah']:.0f} Ah"),
                                    (f"{MODULE['P_max_kW']:.2f} kW", "max continuous (C/1.7) — no 15-min UPS"), (f"{sm['Wh_kg']:.0f} Wh/kg", f"{sm['mass_kg']:.0f} kg calculated mass"),
                                    (f"{sm['Wh_L']:.0f} Wh/L", f"19-inch 7U, {sm['envelope_L']:.0f} L"))):
        stat(s, 5.2 + (i % 2) * 3.85, 1.8 + (i // 2) * 1.9, 3.6, big, lab, RUST if i % 2 == 0 else TEAL)
    text(s, 5.2, 5.75, 7.5, 1.0, f"P1: {P1['Ah']:.1f} Ah, {P1['Wh']:.0f} Wh, {P1['thickness_mm']:.1f} mm thick, {meta['p1']['Wh_kg']:.0f} Wh/kg. The module is aimed at 2–8 h telecom/edge backup.", 14, MUTED)
    # 13 cutaway full bleed
    s = slide(True); title(s, "Inside SM-48T: a hot box in a cold rack", True)
    picture(s, "renders/out_salt/module_cutaway.png", 0.3, 1.25, 8.4, 5.9)
    bullets(s, 8.9, 1.6, 4.0, 5.2, ["84 cells in 4 columns of 21, mica spacers, series straps.", "4 × 150 W heaters on 270 °C bimetal cut-outs.",
                                    "40 mm evacuated double wall around a welded SS hot can.", "Cold bay: BMS, contactor, fuse — only busbars cross the insulation.",
                                    "Rear fan + damper bypass for faults only."], 15, "E3E7EA")
    # 14 mass breakdown native + levers native
    s = slide(); title(s, "Housings, not chemistry, set the module mass", sub="SM-48T part list (CAD) and the spreadsheet mass levers [CALCULATED]")
    pl = list(csv.DictReader(open(LAB / "cad/out/smodule/sm48t_partlist.csv"))); pl.sort(key=lambda x: -float(x["total_mass_g"])); top = pl[:7]
    cd = CategoryChartData(); cd.categories = [x["part"].split("(")[0].replace("P1 ", "")[:26] for x in top]; cd.add_series("kg", [round(float(x["total_mass_g"]) / 1000, 1) for x in top])
    ch = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(1.7), Inches(6.4), Inches(5.0), cd).chart; chart_style(ch, [SLATE], fmt='0.0')
    ch.category_axis.reverse_order = True
    cd = CategoryChartData(); cd.categories = ["concept", "thin cans", "+ thin mica", "+ 100 mAh/cm²"]; cd.add_series("Wh/kg", [round(v, 1) for v in xl["whkg_levers"]])
    ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(7.3), Inches(1.7), Inches(5.5), Inches(5.0), cd).chart; chart_style(ch, [RUST], fmt='0'); ch.value_axis.minimum_scale = 0
    notes(s, "Left: heaviest seven items (kg) from cad/out/smodule/sm48t_partlist.csv. Right: module Wh/kg from the Mass_Levers sheet, LibreOffice-recalculated.")
    # 15 D4 thermal
    s = slide(); title(s, "D4 · Keeping it hot costs ~0.5 kWh a day", sub="Lumped thermal model S16 [CALCULATED from ASSUMPTION]; QT-20 must measure it")
    picture(s, "sim/s16_module_thermal/out/s16_thermal.png", 0.6, 1.7, 7.8, 3.3)
    for i, (big, lab) in enumerate(((f"{sd['evacuated_W']:.0f} W", "standby, 40 mm evacuated"), (f"{100 * sd['evacuated_frac_of_capacity_per_day']:.0f} %/day", "of stored energy"),
                                    (f"{s16['warmup']['600 W']['hours']:.1f} h", "cold start at 600 W"), (f"{s16['discharge']['adiabatic_rise_C']:.0f} K", "rise in a full discharge"))):
        stat(s, 0.6 + i * 3.05, 5.2, 2.85, big, lab, RUST if i % 2 == 0 else TEAL)
    picture(s, "drawings/out/SB-TM-001_paper.png", 8.6, 1.7, 4.2, 3.0, "SB-TM-001 thermal section")
    # 16 D5 cabinet
    s = slide(); title(s, "D5 · SC-UPS-1: three modules, 6.8 kWh, front service", sub="600 × 800 × 1400 mm floor cabinet — concept")
    picture(s, "renders/out_salt/cabinet_open.png", 0.6, 1.6, 5.0, 5.3); picture(s, "drawings/out/SB-UPS-001_paper.png", 5.9, 1.7, 6.9, 3.6, "Drawing SB-UPS-001 (CADCraft, 1:10)")
    bullets(s, 6.0, 5.75, 6.8, 1.1, [f"{CABINET['modules']} × SM-48T, 2U controller (CAN, SNMP), 2U DC breakers, keep-warm {CABINET['modules'] * sd['evacuated_W']:.0f} W."], 14)
    # 17 drawings gallery
    s = slide(); title(s, "Engineering drawings made with CADCraft", sub="Headless CLI → DXF + PDF + PNG, A2 sheets, 1st-angle projection")
    for i, (dwg, lab) in enumerate((("SB-SC-001", "R0 test cell, 2:1"), ("SB-SM-001", "SM-48T module GA, 1:4"), ("SB-TM-001", "thermal section, 1:1"), ("SB-UPS-001", "cabinet GA, 1:10"))):
        picture(s, f"drawings/out/{dwg}_paper.png", 0.6 + (i % 2) * 6.2, 1.65 + (i // 2) * 2.7, 5.9, 2.25, f"{dwg} · {lab}")
    # 18 economics native
    s = slide(); title(s, "Even 1 GWh/yr leaves salt-iron far from USD 3", sub="Cell cost by factory scale (S15) and the module bill of materials (spreadsheet)")
    cd = CategoryChartData(); scales = [1, 10, 100, 1000]; cd.categories = [f"{m} MWh/yr" for m in scales]
    for line, reg, lab in (("S03", "India", "salt-iron, India"), ("N02", "India", "NFPP Na-ion, India")):
        cd.add_series(lab, [next(x["cell_cost_usd_kWh"] for x in s15 if x["line"] == line and x["region"] == reg and x["MWh_per_yr"] == m) for m in scales])
    ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.7), Inches(7.4), Inches(5.0), cd).chart; chart_style(ch, [RUST, TEAL], legend=True, fmt='0')
    stat(s, 8.3, 1.8, 4.5, f"${xl['cell_usd_kwh']:.0f}/kWh", "P1 cell materials (β''-alumina = {:.0f} %)".format(100 * xl["beta_share"]))
    stat(s, 8.3, 3.55, 4.5, f"${xl['module_usd_kwh']:.0f}/kWh", "SM-48T materials + bought-in parts", TEAL)
    stat(s, 8.3, 5.3, 4.5, f"{xl['x_over_target']:.0f}×", "over the USD 3/kWh target, before conversion cost")
    # 19-20 MATLAB stems (two slides, larger)
    pngs = stems["pngs"]
    s = slide(); title(s, f"MATLAB stem diagrams (1/2): DFT results", sub=f"{len(pngs)} scripts in matlab/stem/*.m, run with {stems['engine']} (no MATLAB licence); unchanged in MATLAB")
    for i, pth in enumerate(pngs[:4]):
        picture(s, f"matlab/stem/out/{pth}", 0.6 + (i % 2) * 6.15, 1.65 + (i // 2) * 2.7, 5.95, 2.5)
    s = slide(); title(s, "MATLAB stem diagrams (2/2): design and economics", sub="Convergence, chemistry matrix, cell utilisation, factory cost, module keep-warm")
    for i, pth in enumerate(pngs[4:9]):
        x = 0.6 + (i % 3) * 4.1 if i < 3 else 2.65 + (i - 3) * 4.1
        picture(s, f"matlab/stem/out/{pth}", x, 1.65 + (i // 3) * 2.7, 3.9, 2.5)
    # 20 verification
    s = slide(); title(s, "Verification — software checks only", sub="No physical test exists; these are regression, rule and recalculation checks")
    t = tests(); passed = t["tests"] - t["failures"] - t["errors"] - t["skipped"] if t else 0
    stat(s, 0.6, 1.8, 2.9, f"{passed}", "pytest passed on EC2", TEAL); stat(s, 3.7, 1.8, 2.9, f"{t['failures'] + t['errors'] if t else '-'}", "failed", RUST)
    stat(s, 6.8, 1.8, 2.9, "0", "formula errors (LibreOffice)", TEAL); stat(s, 9.9, 1.8, 2.9, f"{nerc}", "schematic ERC violations", TEAL)
    bullets(s, 0.6, 3.7, 12.1, 3.1, [f"CADCraft: 3 new A2 drawings, 0 command errors; build123d: 5 STEP assemblies with part lists, tolerances and qualification tests.",
                                     f"DFT: 83 jobs, 0 failed after restarts; NiCl₂ cutoff converged to {s11['convergence']['NiCl2_FM']['ecut50']} meV/atom at 50 Ry.",
                                     f"Octave: {len(stems['pngs'])}/{len(stems['scripts'])} stem scripts rendered.",
                                     f"PCB DRC: {sum(dc.values())} errors, {len(drc['unconnected_items'])} unconnected — the layout remains a draft.",
                                     "Hardware validation plan: R0 gates G1–G5 → P1 plate/seal scale-up → module QT-20…26 → UL 9540A / IEC 62619."], 15)
    # 21 limitations
    s = slide(); title(s, "What would have to be true for salt-iron to win", sub="All three together — each is a measurable gate")
    for i, (big, lab) in enumerate((("≤ $15/kg", "β''-alumina at ≤ 0.5 mm in large-area form"), ("≥ 100 mAh/cm²", "cathodes that keep ≥ 3,000 cycles"),
                                    ("≤ $100", "per kWh/yr of molten-salt line capacity (7× below the only anchor)"))):
        stat(s, 0.6 + i * 4.1, 1.9, 3.9, big, lab, RUST if i != 1 else TEAL)
    bullets(s, 0.6, 3.9, 12.1, 2.8, ["Nothing is measured; literature numbers partly read from abstracts and transcribed tables — verify before citing.",
                                     "The 150 mm P1 plate, its seal and its thermal cycling are untested extrapolations from a 30 mm disc.",
                                     "Module mass and cost use simple sheet-metal and price assumptions; the levers show the room, not a design."], 15)
    # 22 next steps
    s = slide(True); title(s, "Next: run the cheapest test that can kill the idea", True)
    picture(s, "diagrams/out/ds5_gate_ladder.png", 0.6, 1.4, 8.1, 5.2)
    bullets(s, 8.9, 1.5, 4.0, 5.2, ["20 buyer interviews (K4) — about 4 weeks, ~INR 50k.", "R0 campaign G1–G5 at a partner lab — 16–20 weeks, ~INR 12.5 lakh parts.",
                                    "Independent review by three experts.", "DFT next on EC2: NaCl vacancy NEB, Na₆FeCl₈, orbital-ordered FeCl₂ (~USD 2–4)."], 15, "E3E7EA")
    OUT.parent.mkdir(parents=True, exist_ok=True); prs.save(OUT); print("wrote", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
