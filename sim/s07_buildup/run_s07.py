"""S7 — Cell -> module -> rack bottom-up mass/volume/energy build-up for R1, with Monte Carlo over the
material assumptions, compared with LFP, sodium-ion (CATL, Alsym claims), Aquion and VRLA.

R1 numbers: [CALC] from params (no cell built). Comparators: [VENDOR]/[LIT]/[ASSUMPTION] as tagged.
"""
import json, pathlib, sys, copy
import numpy as np
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
from params.product_params import MAT, P, VRLA_REF, MONOBLOC
import params.design as D
import plotstyle as ps
import matplotlib.pyplot as plt

OUT = pathlib.Path(__file__).parent / "out"; OUT.mkdir(exist_ok=True)
N = 600
SAMPLED = ["cathode_capacity", "cathode_avg_potential_SHE", "anode_capacity", "cathode_density", "anode_density",
           "active_fraction", "electrode_porosity", "np_ratio", "cc_thickness_um", "separator_thickness_um", "electrolyte_excess"]

# Comparators: (cell Wh/kg, module/block Wh/kg, system Wh/kg, block Wh/L), tag, source
COMP = {
    "LFP (stationary)": {"cell": (160, 180), "module": (120, 150), "system": (90, 130), "Wh_L_block": (250, 350),
                         "tag": "ASSUMPTION", "src": "typical 280-314 Ah LFP storage cells and racks (datasheet ranges; not individually sourced)"},
    "Na-ion (CATL Naxtra)": {"cell": (175, 175), "tag": "VENDOR", "src": "SRC-021 electrek 2026-04-22"},
    "Na-ion (Alsym NFPP+)": {"cell": (135, 135), "Wh_L_cell": 250, "tag": "VENDOR", "src": "SRC-011 ESS News 2025-10-22"},
    "VRLA 12 V 100 Ah": {"module": (37.5, 42.9), "module_15min": (17, 26), "Wh_L_block": (92, 100),
                         "tag": "CALC", "src": "1.2 kWh / 28-32 kg, 12.6 L block; 15-min fraction 0.45-0.60 [ASSUMPTION]"},
    "Aquion Aspen 48S-2.2": {"module": (18.6, 18.6), "Wh_L_block": (23.3, 23.3), "system": (17.3, 17.3),
                             "tag": "CALC", "src": "SRC-035/036 datasheet; system 26 kWh/1,504 kg incl. rack (mission brief)"},
}


def sample_mat(rng):
    m = copy.deepcopy(MAT)
    for k in SAMPLED:
        x = MAT[k]
        if x.rng:
            m[k] = P(float(rng.uniform(*x.rng)), x.unit, x.tag, x.source, x.rng)
    return m


def main():
    rng = np.random.default_rng(7)
    s3 = json.loads((LAB / "sim/s03_r1_cell/out/s03_results.json").read_text())
    f15_p50 = s3["mc"]["40.0"]["4.0"]["p50"] * s3["nominal"]["40.0"]["4.0"]["Vavg"] / s3["nominal"]["40.0"]["0.1"]["Vavg"]
    rows = []
    for _ in range(N):
        m = sample_mat(rng)
        mb = D.monobloc(None, m)
        rows.append({"stack": mb["cell_Wh_per_kg_stack_only"], "block": mb["Wh_per_kg"], "block_L": mb["Wh_per_L"],
                     "block_Wh": mb["energy_Wh"]})
    arr = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    nom = D.monobloc(); mod = D.module48(); cab = D.cabinet()
    pct = lambda a: {"p10": float(np.percentile(a, 10)), "p50": float(np.percentile(a, 50)), "p90": float(np.percentile(a, 90))}
    # module / cabinet scale with the same ratio as nominal
    r_mod = mod["Wh_per_kg"] / nom["Wh_per_kg"]; r_cab = cab["Wh_per_kg"] / nom["Wh_per_kg"]
    res = {"label": "[CALC] bottom-up from params; Monte Carlo over material assumptions; comparators tagged individually",
           "R1_nominal": {"stack_Wh_kg": nom["cell_Wh_per_kg_stack_only"], "monobloc_Wh_kg": nom["Wh_per_kg"], "monobloc_Wh_L": nom["Wh_per_L"],
                          "monobloc_Wh": nom["energy_Wh"], "monobloc_kg": nom["mass_kg"], "module48_Wh_kg": mod["Wh_per_kg"],
                          "module48_kWh": mod["energy_Wh"] / 1000, "cabinet_Wh_kg": cab["Wh_per_kg"], "cabinet_kWh": cab["energy_kWh"],
                          "cabinet_Wh_L": cab["Wh_per_L"], "fraction_at_15min_p50": f15_p50},
           "R1_mc": {"stack_Wh_kg": pct(arr["stack"]), "monobloc_Wh_kg": pct(arr["block"]), "monobloc_Wh_L": pct(arr["block_L"]),
                     "monobloc_Wh": pct(arr["block_Wh"]), "module48_Wh_kg": pct(arr["block"] * r_mod), "cabinet_Wh_kg": pct(arr["block"] * r_cab)},
           "mass_breakdown_monobloc_kg": {"electrode stack": nom["stack_kg"], "case": nom["case_kg"], "hardware": nom["hardware_kg"],
                                          "free electrolyte": nom["free_electrolyte_kg"]},
           "comparators": COMP, "N": N}
    (OUT / "s07_results.json").write_text(json.dumps(res, indent=1, default=float))
    charts(res)
    print(json.dumps(res["R1_nominal"], indent=1, default=lambda x: round(x, 2)))
    print({k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in res["R1_mc"].items()})


def charts(res):
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    levels = ["cell", "module", "system"]
    rows = []
    mc = res["R1_mc"]
    rows.append(("R1 (this work)", {"cell": (mc["stack_Wh_kg"]["p10"], mc["stack_Wh_kg"]["p90"]),
                                    "module": (mc["monobloc_Wh_kg"]["p10"], mc["monobloc_Wh_kg"]["p90"]),
                                    "system": (mc["cabinet_Wh_kg"]["p10"], mc["cabinet_Wh_kg"]["p90"])}, ps.ENTITY["R1"]))
    rows.append(("Aquion Aspen (2016)", res["comparators"]["Aquion Aspen 48S-2.2"], ps.ENTITY["Aquion"]))
    rows.append(("VRLA 12 V block", res["comparators"]["VRLA 12 V 100 Ah"], ps.ENTITY["VRLA"]))
    rows.append(("Na-ion (CATL / Alsym claims)", {"cell": (135, 175)}, ps.ENTITY["Na-ion"]))
    rows.append(("LFP stationary", res["comparators"]["LFP (stationary)"], ps.ENTITY["LFP"]))
    off = {"cell": -0.22, "module": 0.0, "system": 0.22}
    mk = {"cell": "o", "module": "s", "system": "D"}
    for i, (name, d, col) in enumerate(rows):
        for lv in levels:
            if lv in d:
                lo, hi = d[lv]
                y = i + off[lv]
                ax.plot([lo, hi], [y, y], color=col, lw=2.5, solid_capstyle="round")
                ax.scatter([(lo + hi) / 2], [y], marker=mk[lv], s=40, color=col, edgecolor=ps.SURFACE, linewidth=1.5, zorder=3)
    ax.set_xscale("log"); ax.set_xlim(8, 300)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows]); ax.invert_yaxis()
    ax.set_xlabel("Specific energy (Wh/kg, log scale)")
    handles = [plt.Line2D([], [], marker=mk[lv], color=ps.TEXT2, lw=0, markersize=6) for lv in levels]
    ax.legend(handles, ["cell", "module / 12 V block", "rack / cabinet"], loc="upper center", bbox_to_anchor=(0.45, -0.16), ncol=3)
    ax.set_title("Where a water-based sodium battery sits")
    ax.axvline(res["R1_nominal"]["monobloc_Wh_kg"], color=ps.DEEMPH, lw=0.8)
    ps.save(fig, OUT / "s07_energy_density_comparison",
            "Specific energy at cell, module and rack level: R1 bottom-up (P10–P90 over material assumptions) vs Aquion's last module, a VRLA block, sodium-ion claims and LFP.",
            "R1 [CALC]; Aquion [CALC from VENDOR datasheet]; VRLA [CALC]; Na-ion [VENDOR]; LFP [ASSUMPTION typical ranges]")
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    mb = res["mass_breakdown_monobloc_kg"]
    items = sorted(mb.items(), key=lambda kv: -kv[1])
    ax.barh([k for k, _ in items], [v for _, v in items], color=ps.SERIES[0], height=0.5)
    for i, (_, v) in enumerate(items):
        ax.text(v + 0.2, i, f"{v:.1f} kg", va="center", fontsize=8, color=ps.TEXT2)
    ax.invert_yaxis(); ax.set_xlabel("Mass per 12 V monobloc (kg)")
    ax.set_title(f"R1 monobloc mass: {sum(mb.values()):.1f} kg for {res['R1_nominal']['monobloc_Wh']:.0f} Wh")
    ps.save(fig, OUT / "s07_monobloc_mass", "Mass breakdown of one R1 12 V monobloc at the design point.", "[CALC] params/design.py")


if __name__ == "__main__":
    main()
