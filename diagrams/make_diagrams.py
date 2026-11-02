"""Diagrams (SVG + PNG): architecture, process flow, manufacturing line & capex, validation ladder,
safety comparison, positioning map, unit-economics waterfall, 18-month roadmap, use of funds.
All numbers are read from params / simulation outputs; tags printed on each diagram.
"""
import json, pathlib, sys
import numpy as np
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
import plotstyle as ps
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from params.product_params import MONOBLOC, CABINET, MODULE48, MAT, COST
import params.design as D

OUT = LAB / "diagrams" / "out"; OUT.mkdir(parents=True, exist_ok=True)
FILL = "#eef4fc"; FILL2 = "#fdf1ea"; FILL3 = "#e9f7f1"; EDGE = "#c9c8c2"


def box(ax, x, y, w, h, text, fill=FILL, size=8.2, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.015", fc=fill, ec=EDGE, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=ps.TEXT, wrap=True,
            fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, x0, y0, x1, y1, text=None):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=9, color=ps.TEXT2, lw=1.0))
    if text:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.012, text, ha="center", va="bottom", fontsize=6.8, color=ps.TEXT2)


def canvas(w=10, h=5.2, title=""):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    if title:
        ax.set_title(title, loc="left")
    return fig, ax


def architecture():
    mb, mod, cab = D.monobloc(), D.module48(), D.cabinet()
    fig, ax = canvas(10, 5.0, "R1 system architecture (concept)")
    box(ax, 0.02, 0.55, 0.15, 0.25, f"Cell\nNa-birnessite // NTP-C\n0.5 M Na₂SO₄\n~{mb['v_cell_nom']:.2f} V, {mb['cap_Ah']:.0f} Ah\n[TARGET]")
    box(ax, 0.22, 0.55, 0.16, 0.25, f"12 V monobloc\n{MONOBLOC['cells_in_series']} cells in series\n{mb['energy_Wh']:.0f} Wh, {mb['mass_kg']:.1f} kg\nvent + flame arrestor\n[CALC/TARGET]")
    box(ax, 0.43, 0.68, 0.18, 0.2, f"48 V telecom tray\n{MODULE48['monoblocs']} monoblocs + DC/DC\n{mod['energy_Wh']/1000:.2f} kWh", fill=FILL3)
    box(ax, 0.43, 0.40, 0.18, 0.22, f"UPS cabinet\n{cab['monoblocs']} monoblocs\n~{cab['string_V']:.0f} V string\n{cab['energy_kWh']:.1f} kWh", fill=FILL3)
    box(ax, 0.68, 0.68, 0.14, 0.2, "Telecom\n-48 V DC bus\nrectifier", fill=FILL2)
    box(ax, 0.68, 0.40, 0.14, 0.22, "UPS\n(rectifier /\ninverter)", fill=FILL2)
    box(ax, 0.86, 0.52, 0.12, 0.24, "Critical load\n(BTS, servers)", fill=FILL2)
    box(ax, 0.22, 0.10, 0.39, 0.20, "BMS / monitor board (pcb/bms_monitor)\nper-block voltage · NTC · shunt current\nH₂ sensor · pressure\nisolated CAN + RS-485 · contactor & alarm outputs", fill="#f4f3ef", size=7.6)
    box(ax, 0.68, 0.10, 0.30, 0.20, "Room ventilation sized to keep\nH₂ ≤ 25 % LFL (S4)\ndetection → ventilation / alarm\nNFPA 855-2026: HMA required", fill="#f4f3ef", size=7.6)
    arrow(ax, 0.17, 0.675, 0.22, 0.675); arrow(ax, 0.38, 0.70, 0.43, 0.77); arrow(ax, 0.38, 0.62, 0.43, 0.52)
    arrow(ax, 0.61, 0.78, 0.68, 0.78); arrow(ax, 0.61, 0.51, 0.68, 0.51); arrow(ax, 0.82, 0.78, 0.86, 0.66); arrow(ax, 0.82, 0.51, 0.86, 0.60)
    arrow(ax, 0.52, 0.30, 0.52, 0.40); ax.text(0.53, 0.345, "sense / control", fontsize=6.8, color=ps.TEXT2)
    arrow(ax, 0.61, 0.255, 0.68, 0.255); ax.text(0.645, 0.27, "gas alarm", fontsize=6.8, color=ps.TEXT2, ha="center")
    ps.save(fig, OUT / "d1_system_architecture", "R1 concept system architecture from cell to critical load, including the aqueous-specific gas monitoring path.",
            "[TARGET] design values from params; [CALC] energies from params/design.py")


def process_flow():
    fig, ax = canvas(11, 4.6, "Material and cell process flow (no dry room) — concept")
    steps = [("Mn precursor\n(MnSO₄/MnCl₂ → Mn₃O₄)", "precipitation reactor,\ncentrifuge/filter"),
             ("Na insertion\nNaOH, 270 °C, 6 h, air", "belt / rotary kiln"),
             ("Wash, dry, mill\n(QC: XRD, ICP, TGA)", "filter press, dryer,\njet mill"),
             ("Water-based slurry\n80:10:10", "planetary / twin-screw\nmixer"),
             ("Coat + calender\non coated 316L foil", "slot-die coater,\ncalender"),
             ("Cut plates,\nstack with separator", "die cutter,\nstacker"),
             ("Case, intercell welds,\nfill 0.5 M Na₂SO₄", "ultrasonic / laser\nwelding, vacuum fill"),
             ("Seal, vent,\nformation + test", "heat-seal, cyclers,\nleak & gas test")]
    n = len(steps); w = 0.112; gap = (1 - n * w) / (n + 1)
    for i, (s, eq) in enumerate(steps):
        x = gap + i * (w + gap)
        box(ax, x, 0.50, w, 0.28, s, fill=FILL, size=7.4)
        box(ax, x, 0.16, w, 0.20, eq, fill="#f4f3ef", size=6.8)
        if i < n - 1:
            arrow(ax, x + w, 0.64, x + w + gap, 0.64)
    ax.text(0.02, 0.90, "Steps 1–3: cathode (R0 route per Shan et al. 2019); NTP anode made separately (solid-state, carbon-coated). Equipment row = typical, not specified.",
            fontsize=7.6, color=ps.TEXT2)
    ax.text(0.02, 0.05, "No NMP solvent, no dry room: aqueous processing at ambient humidity. All laboratory work under a qualified partner's EHS approval.", fontsize=7.6, color=ps.TEXT2)
    ps.save(fig, OUT / "d2_process_flow", "Material and cell process flow from manganese precursor to formed 12 V monobloc, with typical equipment per step.",
            "Process steps [LIT] Shan 2019 for cathode synthesis; equipment [ASSUMPTION]")


def manufacturing_capex():
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    stages = ["Lab / R0-R1\n(partner lab)", "Pilot line\n10 MWh/yr", "Demo line\n100 MWh/yr", "First plant\n500 MWh/yr"]
    capex = [0.08, 2.0, 8.0, COST["capex_per_GWh"].value * COST["plant_GWh"].value / 1e6]
    lo = [0.05, 1.0, 5.0, COST["capex_per_GWh"].rng[0] * COST["plant_GWh"].value / 1e6]
    hi = [0.15, 4.0, 15.0, COST["capex_per_GWh"].rng[1] * COST["plant_GWh"].value / 1e6]
    ax.bar(range(4), capex, color=ps.SERIES[0], width=0.45)
    for i in range(4):
        ax.plot([i, i], [lo[i], hi[i]], color=ps.TEXT2, lw=1.2)
        ax.text(i + 0.27, capex[i], f"${capex[i]:.2g}M", va="center", fontsize=8, color=ps.TEXT2)
    ax.set_yscale("log"); ax.set_xticks(range(4)); ax.set_xticklabels(stages); ax.set_ylabel("Capex ($ million, log)")
    ax.set_title("Manufacturing scale-up steps and capex (no dry room)")
    ps.note(ax, "whiskers = assumption range", "upper left")
    ps.save(fig, OUT / "d3_manufacturing_capex", "Concept scale-up path for an aqueous line (no dry room) with indicative capex at each step.",
            "[ASSUMPTION] capex ranges (params COST capex_per_GWh for the plant; pilot/demo values are estimates, not quotes)")


def validation_ladder():
    fig, ax = canvas(10, 5.4, "Validation ladder with kill gates")
    rungs = [("R0  Reproduce published powder (3 batches)", "XRD/ICP/TGA match paper", "wk 0–6"),
             ("R0-D  Electrode method at 3 / 20 / 40 mg/cm²", "K1 ≥60 mAh/g @40 · K3 ≥60 % at 15 min", "wk 6–12"),
             ("R1 cell  Pouch / prismatic, 0.5 M Na₂SO₄", "K2 CE ≥99.5 % (→99.88 %) · gas within vent", "M3–M6"),
             ("R1 monobloc  12 V, 10 cells", "≥20 Wh/kg block · float gas test", "M6–M10"),
             ("Module / cabinet + BMS", "UL 9540A cell & unit tests · HMA", "M10–M15"),
             ("Certification & field pilot", "UL 1973 / IEC 62619-type; 2 pilot sites", "M15–M18")]
    for i, (a, gate, t) in enumerate(rungs):
        y = 0.08 + i * 0.145
        x0 = 0.02 + i * 0.025
        box(ax, x0, y, 0.40, 0.11, a, fill=FILL, size=7.8)
        box(ax, x0 + 0.42, y, 0.36, 0.11, "Gate: " + gate, fill=FILL2, size=7.2)
        ax.text(x0 + 0.80, y + 0.055, t, fontsize=7.6, color=ps.TEXT2, va="center")
        if i < len(rungs) - 1:
            arrow(ax, x0 + 0.20, y + 0.11, x0 + 0.225, y + 0.145)
    ax.text(0.05, 0.96, "Business gates run in parallel: K4 ≥3/20 buyers name a ≥\\$150/kWh Li-ion indoor premium (wk 8); K5 cost path ≤\\$250/kWh (wk 12); K6 code path (wk 12).",
            fontsize=7.4, color=ps.TEXT2)
    ps.save(fig, OUT / "d4_validation_ladder", "Validation ladder from reproducing the published material to field pilots, with the kill gate at each rung.",
            "[TARGET] gates from decisions/IDEA_v2.md; timings [ASSUMPTION]")


def safety_comparison():
    s8 = json.loads((LAB / "sim/s08_thermal/out/s08_results.json").read_text())
    fig, ax = canvas(10.5, 5.2, "Safety: the Li-ion runaway chain vs the R1 aqueous cell")
    ax.text(0.02, 0.92, "Li-ion step", fontsize=8.5, fontweight="bold"); ax.text(0.40, 0.92, "R1 aqueous cell", fontsize=8.5, fontweight="bold")
    ax.text(0.86, 0.92, "Status", fontsize=8.5, fontweight="bold")
    for i, r in enumerate(s8["runaway_chain"]):
        y = 0.83 - i * 0.082
        rem = r["status"].startswith("REMAINS")
        fill = "#fbeaea" if rem else FILL3
        box(ax, 0.02, y, 0.36, 0.07, r["li_ion_step"], fill="#f4f3ef", size=6.9)
        box(ax, 0.40, y, 0.44, 0.07, r["aqueous_R1"], fill=fill, size=6.9)
        ax.text(0.86, y + 0.035, ("⚠ " if rem else "✓ ") + r["status"].split(" (")[0], fontsize=6.9, va="center", color=ps.TEXT)
    ps.save(fig, OUT / "d5_safety_comparison", "Step-by-step comparison of the Li-ion thermal-runaway chain with the R1 aqueous cell, including the hazards that remain (hydrogen, plastic case, leakage, Mn²⁺, freezing).",
            "[CALC] S8 energy balance; [LIT] general Li-ion runaway sequence; remaining hazards from S4/S8")


def positioning():
    s7 = json.loads((LAB / "sim/s07_buildup/out/s07_results.json").read_text())
    s9 = json.loads((LAB / "sim/s09_tea/out/s09_results.json").read_text())
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    pts = [("LFP stationary pack", 140, 70, ps.ENTITY["LFP"], "[LIT] $70/kWh BNEF; Wh/kg [ASSUMPTION]"),
           ("Na-ion cells (CATL/Alsym claims; cost assumed)", 155, 85, ps.ENTITY["Na-ion"], "[VENDOR]; cost [ASSUMPTION]"),
           ("VRLA block (India)", 40, 84, ps.ENTITY["VRLA"], "[CALC] ₹7.1–7.6k/kWh"),
           ("Aquion module (2016)", 18.6, 300, ps.ENTITY["Aquion"], "[CALC] datasheet; $300 target [LIT]"),
           ("R1 bottom-up (cost)", s7["R1_nominal"]["monobloc_Wh_kg"], s9["monobloc_ups"]["cost_per_kWh"], ps.ENTITY["R1"], "[CALC]")]
    for name, x, y, c, tag in pts:
        ax.scatter([x], [y], s=70, color=c, edgecolor=ps.SURFACE, linewidth=2, zorder=3)
        dy = -12 if name.startswith("LFP") or name.startswith("Aquion") else 5
        ax.annotate(name, (x, y), xytext=(7, dy), textcoords="offset points", fontsize=7.8, color=ps.TEXT)
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
    ax.xaxis.set_major_locator(FixedLocator([10, 20, 50, 100, 200])); ax.xaxis.set_major_formatter(FixedFormatter(["10", "20", "50", "100", "200"]))
    ax.yaxis.set_major_locator(FixedLocator([50, 100, 200, 400])); ax.yaxis.set_major_formatter(FixedFormatter(["50", "100", "200", "400"]))
    ax.xaxis.set_minor_locator(NullLocator()); ax.yaxis.set_minor_locator(NullLocator())
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(10, 300); ax.set_ylim(40, 600)
    ax.set_xlabel("Specific energy (Wh/kg, block/module level, log)"); ax.set_ylabel("$ per kWh (price or cost, log)")
    ax.set_title("Competitive position: energy vs cost per kWh")
    ps.note(ax, "Mixed bases (price vs cost); indicative only. Tags in caption.", "lower left")
    ps.save(fig, OUT / "d6_positioning_map", "Indicative positioning of R1 against LFP, sodium-ion claims, VRLA and Aquion on specific energy and cost per kWh.",
            "LFP [LIT]/[ASSUMPTION]; Na-ion [VENDOR]; VRLA [CALC]; Aquion [CALC]/[LIT]; R1 [CALC] (cost, not price)")


def waterfall():
    s9 = json.loads((LAB / "sim/s09_tea/out/s09_results.json").read_text())
    m = s9["monobloc_ups"]; k = m["kWh"]
    mats = sum(m["materials_breakdown"].values()) / k
    parts = [("Materials", mats), ("Yield loss", m["materials_after_yield"] / k - mats), ("Labour", m["labour"] / k),
             ("Energy", m["energy"] / k), ("Overhead", m["overhead"] / k), ("Depreciation", m["depreciation"] / k)]
    cost = sum(v for _, v in parts); gm = COST["gross_margin"].value
    price = cost / (1 - gm)
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    cum = 0
    for i, (n, v) in enumerate(parts):
        ax.bar(i, v, bottom=cum, color=ps.SERIES[0], width=0.55); ax.text(i, cum + v + 4, f"${v:.0f}", ha="center", fontsize=7.6, color=ps.TEXT2)
        cum += v
    ax.bar(len(parts), cost, color=ps.SERIES[2], width=0.55); ax.text(len(parts), cost + 4, f"${cost:.0f}", ha="center", fontsize=8)
    ax.bar(len(parts) + 1, price - cost, bottom=cost, color=ps.SERIES[3], width=0.55); ax.text(len(parts) + 1, price + 4, f"+${price-cost:.0f}", ha="center", fontsize=7.6, color=ps.TEXT2)
    ax.bar(len(parts) + 2, price, color=ps.SERIES[1], width=0.55); ax.text(len(parts) + 2, price + 4, f"${price:.0f}", ha="center", fontsize=8)
    ax.axhline(70, color=ps.ENTITY["LFP"], lw=1); ax.text(len(parts) + 2.4, 74, "LFP pack $70 [LIT]", fontsize=7, color=ps.TEXT2, ha="right")
    ax.set_xticks(range(len(parts) + 3)); ax.set_xticklabels([p for p, _ in parts] + ["Cost", f"Margin {gm:.0%}", "Price"], fontsize=7.6)
    ax.set_ylabel("$ per nominal kWh"); ax.set_title("Unit economics per kWh: R1 monobloc (UPS design)")
    ps.save(fig, OUT / "d7_unit_economics_waterfall", "Unit-economics waterfall from bottom-up cost to selling price per kWh for the R1 monobloc at a 0.5 GWh/yr plant.",
            "[CALC] S9 from [ASSUMPTION] inputs; margin [TARGET]; LFP [LIT]")


def roadmap():
    tasks = [("Lab partner + author clarification", 0, 1.5, 0), ("Reproduce R0 powder (3 batches)", 1, 3, 0),
             ("Electrode method 3/20/40 mg/cm²", 2.5, 3, 0), ("20 buyer interviews + fire-cost quotes", 0.5, 2, 1),
             ("R1 pouch/prismatic cells + gas test", 4, 4, 0), ("Hire electrochemist co-founder", 0, 4, 1),
             ("R1 monobloc build (10 cells)", 7, 4, 0), ("BMS board bring-up", 8, 3, 2),
             ("UL 9540A cell/unit testing", 10, 4, 2), ("Pilot sites (2) + HMA", 13, 5, 1), ("Seed raise", 11, 4, 1)]
    gates = [(2.0, "K4 buyers"), (3.0, "K1/K3 K5 K6"), (8.0, "CE ≥99.88 %"), (14.0, "9540A result")]
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    cols = [ps.SERIES[0], ps.SERIES[1], ps.SERIES[2]]
    for i, (n, s, d, c) in enumerate(tasks):
        ax.barh(i, d, left=s, color=cols[c], height=0.5)
    for j, (m, g) in enumerate(gates):
        ax.axvline(m, color=ps.STATUS["critical"], lw=1)
        ax.text(m + 0.12, len(tasks) + 0.25 + (0.0 if j % 2 == 0 else 0.55), "◆ " + g, fontsize=6.8, color=ps.TEXT, va="center")
    ax.set_yticks(range(len(tasks))); ax.set_yticklabels([t[0] for t in tasks], fontsize=7.8)
    ax.set_xlim(0, 18); ax.set_xlabel("Months from start"); ax.set_title("18-month roadmap with kill gates (red lines)")
    ax.set_ylim(len(tasks) + 1.1, -0.6)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in cols], labels=["technical", "business", "product/cert"],
              loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=3)
    ps.save(fig, OUT / "d8_roadmap_gantt", "18-month plan from lab reproduction to pilots, with kill gates.", "[TARGET] plan; durations [ASSUMPTION]")


def use_of_funds():
    items = [("Partner-lab work: synthesis, characterisation, cells", 110), ("Electrochemist co-founder / staff (12 mo)", 120),
             ("Fire & safety testing (UL 9540A cell/unit, gas)", 90), ("Equipment: cycler channels, gas/pressure rig", 50),
             ("BMS + monobloc prototypes", 40), ("Customer pilots, travel, HMA/code consultant", 40), ("Founder runway + contingency", 50)]
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.barh([i[0] for i in items], [i[1] for i in items], color=ps.SERIES[0], height=0.5)
    for k, (_, v) in enumerate(items):
        ax.text(v + 2, k, f"${v}k", va="center", fontsize=8, color=ps.TEXT2)
    ax.invert_yaxis(); ax.set_xlabel("$ thousand (of a $500k YC-standard investment)")
    ax.set_title("Use of funds (plan, if the battery path passes week-12 gates)")
    ax.set_xlim(0, 150)
    ps.save(fig, OUT / "d9_use_of_funds", "Indicative allocation of a $500k raise across 18 months; spending beyond the week-12 gates is conditional on passing them.",
            "[TARGET]/[ASSUMPTION] allocation; no quotes yet")


if __name__ == "__main__":
    for f in (architecture, process_flow, manufacturing_capex, validation_ladder, safety_comparison, positioning, waterfall, roadmap, use_of_funds):
        f(); print("ok", f.__name__)
