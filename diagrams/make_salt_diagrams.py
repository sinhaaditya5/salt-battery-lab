"""Diagrams for the salt-iron designs (SVG + PNG, same style as make_diagrams.py). Numbers read from params / sim outputs.

ds1 cell electrochemistry + layer stack (R0 and P1)       ds2 SM-48T electrical / control block diagram
ds3 SM-48T thermal energy budget (S16)                     ds4 P1 cell manufacturing flow with qualification gates
ds5 development gate ladder R0 -> P1 -> SM-48T -> SC-UPS-1
Usage: python diagrams/make_salt_diagrams.py
"""
import json, pathlib, sys
LAB = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
import plotstyle as ps  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
from params.smodule_params import CABINET, MODULE as M, P1, THERMAL  # noqa: E402
from params.scell_params import GATES, OPERATE  # noqa: E402

OUT = LAB / "diagrams" / "out"; OUT.mkdir(parents=True, exist_ok=True)
FILL, FILL2, FILL3, FILL4, EDGE = "#eef4fc", "#fdf1ea", "#e9f7f1", "#f6f0fb", "#c9c8c2"
S16 = json.load(open(LAB / "sim/s16_module_thermal/out/s16_results.json"))


def box(ax, x, y, w, h, text, fill=FILL, size=8.0, bold=False, ec=EDGE):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012", fc=fill, ec=ec, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=ps.TEXT, fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, x0, y0, x1, y1, text=None, color=None, size=6.8, style="-|>"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=9, color=color or ps.TEXT2, lw=1.0))
    if text:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.012, text, ha="center", va="bottom", fontsize=size, color=ps.TEXT2)


def canvas(w=11, h=6.2):
    ps.apply(); fig, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); return fig, ax


def ds1():
    fig, ax = canvas(11, 6.0)
    layers = [("SS 316L anode can (−)", 0.05, "#c9ccd1"), ("Na metal (formed on charge) + SS wick", 0.09, "#d9dde3"),
              ("β''-alumina electrolyte  1.0 mm  (Na⁺ only)", 0.06, "#efe6cc"),
              (f"cathode bed {P1['cathode_t_mm']:.1f} mm @ {P1['qa_mAh_cm2']:.0f} mAh/cm²: NaCl + Fe (+10 % Ni) in molten NaAlCl₄", 0.16, "#5a4a42"),
              ("Mo collector + wave spring", 0.05, "#b5b8bd"), ("Ni 201 cathode can (+)", 0.05, "#a9a69d")]
    y = 0.14
    for name, h, col in layers:
        ax.add_patch(Rectangle((0.06, y), 0.40, h, fc=col, ec="#888", lw=0.6))
        ax.text(0.26, y + h / 2, name, ha="center", va="center", fontsize=7.6, color="white" if col == "#5a4a42" else ps.TEXT); y += h
    ax.text(0.06, y + 0.03, f"Cell stack (R0: Ø30 mm disc · P1: 150 mm plate) — operates {OPERATE['T_range_C'][0]:.0f}–{OPERATE['T_range_C'][1]:.0f} °C", fontsize=9, fontweight="bold")
    arrow(ax, 0.50, 0.30, 0.50, 0.50, "Na⁺ (charge)", ps.SERIES[0]); arrow(ax, 0.53, 0.50, 0.53, 0.30, "Na⁺ (discharge)", ps.SERIES[1])
    box(ax, 0.60, 0.66, 0.36, 0.17, "Cathode (charge →)\n2 NaCl + Fe → FeCl₂ + 2 Na⁺ + 2 e⁻\nE° ≈ 2.35 V vs Na (Fe), 2.58 V (Ni) at ~300 °C", FILL2, 8.2)
    box(ax, 0.60, 0.42, 0.36, 0.17, "Anode (charge →)\nNa⁺ + e⁻ → Na (liquid above 98 °C)\nNo Na metal handled at assembly", FILL, 8.2)
    box(ax, 0.60, 0.14, 0.36, 0.21, f"Assembled DISCHARGED from salt + iron\nLimits {OPERATE['V_discharge_min']}–{OPERATE['V_charge_max']} V, trips {OPERATE['V_trip_low']}/{OPERATE['V_trip_high']} V\n"
        f"(side reactions 1.58 / 3.05 V)\nP1: {P1['Ah']:.1f} Ah, {P1['Wh']:.0f} Wh, ≤ {P1['j_max_mA_cm2']:.0f} mA/cm² (C/1.5)", FILL3, 8.0)
    ax.text(0.06, 0.05, "[PUBLISHED] chemistry (ZEBRA / Na-FeCl₂, PS-005); dimensions [ASSUMPTION] (params/scell_params.py, smodule_params.py); DFT check: S11.", fontsize=7, color=ps.TEXT2)
    ps.save(fig, OUT / "ds1_cell_electrochemistry", "Salt-iron cell: layer stack and half-reactions; assembled from NaCl and Fe in the discharged state.",
            "[PUBLISHED] chemistry; [ASSUMPTION] dimensions")


def ds2():
    fig, ax = canvas(11.5, 6.2)
    box(ax, 0.02, 0.38, 0.20, 0.34, f"HOT BOX 190 °C\n{M['series']}S{M['parallel']}P = {M['cells']} P1 cells\n4 columns × 21\n{M['V_min']:.0f}–{M['V_max']:.1f} V · {M['Ah']:.0f} Ah\n{M['kWh']:.2f} kWh", FILL2, 8.2, True)
    box(ax, 0.02, 0.10, 0.20, 0.20, "4 × 150 W mica heaters\n4 thermocouples\nbypass duct + damper", FILL2, 7.8)
    box(ax, 0.29, 0.50, 0.13, 0.12, "2 ceramic\nfeedthroughs", FILL4, 7.8)
    chain = [("fuse\n125 A", 0.47), ("contactor\n150 A", 0.59), ("isolator\n160 A", 0.71), ("front\nconnectors\n± 120 A", 0.83)]
    for t, x in chain: box(ax, x, 0.50, 0.10, 0.12, t, FILL, 7.6)
    arrow(ax, 0.22, 0.56, 0.29, 0.56); arrow(ax, 0.42, 0.56, 0.47, 0.56)
    for (_, x0), (_, x1) in zip(chain[:-1], chain[1:]): arrow(ax, x0 + 0.10, 0.56, x1, 0.56)
    box(ax, 0.40, 0.14, 0.30, 0.25, "BMS-48T (cold bay, SCM-1 derived)\n21 cell-voltage channels (isolated AFE)\ncurrent shunt · 4 × TC · heater PID\n"
        "contactor + damper drivers · fault latch\ncell-temperature & freeze/thaw log", FILL3, 7.8, True)
    box(ax, 0.76, 0.14, 0.22, 0.25, f"SC-UPS-1 controller\nCAN / RS-485 master\nSNMP to site NMS\n{CABINET['modules']} modules = {CABINET['kWh']:.1f} kWh", FILL, 7.8)
    arrow(ax, 0.22, 0.20, 0.40, 0.24, "heater power / TC", size=6.5); arrow(ax, 0.22, 0.45, 0.40, 0.33, "cell sense ×21", size=6.5)
    arrow(ax, 0.55, 0.39, 0.64, 0.50, "coil", size=6.5); arrow(ax, 0.70, 0.27, 0.76, 0.27, "CAN", size=6.5)
    box(ax, 0.29, 0.80, 0.69, 0.13, "Independent hardware protection (no firmware in the path): bimetal heater cut-outs 270 °C per zone · "
        "cell over/under-voltage comparators 2.95 / 1.65 V → contactor open · fuse for short circuit · SELV < 60 V", "#fff6e5", 7.6)
    ax.text(0.02, 0.96, "SM-48T electrical and control architecture (concept D3/D4)", fontsize=10, fontweight="bold")
    ax.text(0.02, 0.03, "[ASSUMPTION] architecture; component ratings from params/smodule_params.py; BMS-48T is a concept extension of the SCM-1 board.", fontsize=7, color=ps.TEXT2)
    ps.save(fig, OUT / "ds2_module_electrical", "SM-48T power path (cells to front connectors) and BMS / heater control, with independent hardware protection.",
            "[ASSUMPTION] concept architecture")


def ds3():
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.4)); ps.apply()
    sd, ds = S16["standby_design"], S16["discharge"]
    ax = axs[0]
    items = [("standby loss\n(evacuated 40 mm)", sd["evacuated_W"], ps.SERIES[0]), ("standby loss\n(microporous 40 mm)", sd["microporous_W"], ps.SERIES[1]),
             ("heat at max\ndischarge", ds["heat_W"], ps.SERIES[2]), ("installed\nheaters", M["heater_W"], ps.SERIES[3])]
    ax.bar(range(4), [v for _, v, _ in items], color=[c for *_, c in items])
    for i, (_, v, _) in enumerate(items): ax.text(i, v * 1.04, f"{v:.0f} W", ha="center", fontsize=8)
    ax.set_xticks(range(4)); ax.set_xticklabels([n for n, *_ in items], fontsize=8); ax.set_ylabel("W"); ax.set_title("Heat flows, SM-48T at 190 °C, 25 °C ambient")
    ax = axs[1]
    kwh_day = sd["evacuated_kWh_day"]; cap = M["kWh"]
    ax.barh([0], [cap], color=ps.SERIES[0], label=f"stored energy {cap:.2f} kWh")
    ax.barh([1], [kwh_day], color=ps.SERIES[1], label=f"keep-warm {kwh_day:.2f} kWh/day ({100 * sd['evacuated_frac_of_capacity_per_day']:.0f} %)")
    ax.set_yticks([0, 1]); ax.set_yticklabels(["stored", "keep-warm / day"]); ax.set_xlabel("kWh")
    ax.set_title(f"Grid must supply ~{sd['evacuated_kWh_yr']:.0f} kWh/yr (≈ USD {sd['evacuated_usd_yr']:.0f}) per module"); ax.legend(fontsize=7.5, loc="lower right")
    ps.save(fig, OUT / "ds3_module_thermal_budget", "SM-48T thermal budget: keep-warm loss vs discharge heat and heaters; daily keep-warm energy vs stored energy.",
            "[CALCULATED] sim/s16_module_thermal from [ASSUMPTION] inputs")


def ds4():
    fig, ax = canvas(12, 5.6)
    steps = [("β''-alumina\npowder + Li/Mg", FILL), ("press 150 mm\nplate, sinter\n1600 °C", FILL), ("lap both faces\nflat 0.05", FILL), ("glass-seal to\nα-alumina frame", FILL4),
             ("He leak +\nthermal-cycle\nQT-02/03", "#fff6e5"), ("dry NaCl, Fe, Ni,\nadditives\n< 100 ppm H₂O", FILL3), ("granulate +\nfill cathode can\n(Ar glovebox)", FILL3),
             ("NaAlCl₄ vacuum\ninfiltration\n180 °C", FILL3), ("weld cans,\ncrimp fill tube", FILL2), ("He leak\nQT-21", "#fff6e5"), ("formation:\nfirst charge\n2 mA/cm², 190 °C", FILL2),
             ("grade: OCV,\nASR, capacity", FILL2)]
    n = len(steps); w = 0.074; gap = (1 - 0.02 - n * w) / (n - 1)
    for i, (t, f) in enumerate(steps):
        x = 0.01 + i * (w + gap); y = 0.55 if i < 6 else 0.20
        x = 0.01 + (i % 6) * (w * 2 + gap * 1.2) if True else x
        box(ax, x, y, 0.14, 0.20, t, f, 7.6)
        if i % 6 < 5: arrow(ax, x + 0.14, y + 0.10, x + 0.14 + gap * 1.2 + (w * 2 - 0.14), y + 0.10)
    arrow(ax, 0.01 + 5 * (w * 2 + gap * 1.2) + 0.07, 0.55, 0.08, 0.40, "ceramic + cathode sub-assemblies meet", size=7)
    ax.text(0.01, 0.92, "P1 planar cell — manufacturing flow (concept, scaled from the R0 lab procedure)", fontsize=10, fontweight="bold")
    ax.text(0.01, 0.06, "Yellow = qualification gate (part scrapped on fail). Ceramic line is the cost and yield driver (S12/S15). [ASSUMPTION] process; R0 build manual: PROJECT_SALT/07_BUILD_MANUAL.",
            fontsize=7, color=ps.TEXT2)
    ps.save(fig, OUT / "ds4_p1_manufacturing_flow", "P1 planar cell manufacturing flow from beta''-alumina plate to graded cell, with leak-test gates.",
            "[ASSUMPTION] process flow")


def ds5():
    fig, ax = canvas(12, 5.4)
    stages = [("R0 lab cell\nØ30 mm disc", "G1 replicate 190 °C Na-FeCl₂\nG2 ≥80 % @ 60 mAh/cm²\nG3 CE ≥ 99.9 %\nG4 ≤ 1 kg β''/kWh\nG5 seal 20 thermal cycles", FILL),
              ("P1 product cell\n150 mm plate", "plate yield + flatness\nseal scale-up (QT-02/03)\nsame G2/G3 at 196 cm²\nabuse: short, overcharge", FILL2),
              ("SM-48T module\n2.27 kWh", "QT-20 standby ≤ 25 W\nwarm-up ≤ 3 h\nBMS HIL (QT-26)\nfreeze/thaw × 20", FILL3),
              ("SC-UPS-1 cabinet\n6.8 kWh", "UL 9540A cell/module test\nIEC 62619 / 62485\nfield pilot: 2 telecom sites\n(K4 buyer interviews first)", FILL4)]
    for i, (h, body, f) in enumerate(stages):
        x = 0.02 + i * 0.245
        box(ax, x, 0.62, 0.21, 0.18, h, f, 9.0, True); box(ax, x, 0.18, 0.21, 0.38, body, "white", 7.8)
        if i < 3: arrow(ax, x + 0.21, 0.71, x + 0.245, 0.71, "pass →", size=7)
    ax.text(0.02, 0.90, "Development gates — each stage starts only when the previous one passes (kill criteria are real)", fontsize=10, fontweight="bold")
    ax.text(0.02, 0.07, "R0 gates from params/scell_params.py GATES; later gates [ASSUMPTION]. Nothing in this ladder has been executed.", fontsize=7, color=ps.TEXT2)
    ps.save(fig, OUT / "ds5_gate_ladder", "Development gate ladder from the R0 lab cell to the SC-UPS-1 cabinet; each gate is a kill criterion.",
            "[TARGET] gates; nothing executed")


if __name__ == "__main__":
    for f in (ds1, ds2, ds3, ds4, ds5):
        f(); print("ok", f.__name__)
