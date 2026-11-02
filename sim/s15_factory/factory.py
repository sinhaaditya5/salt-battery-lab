#!/usr/bin/env python3
"""S15 - Factory scenario economics at 1 MWh, 10 MWh, 100 MWh and 1 GWh per year (brief §9C, §11). Scenarios, not plans.

Lines: 'S03' salt-iron planar molten-salt cells; 'N02' NFPP Na-ion on a Li-ion-style line (comparison).
Anchors: molten-salt capex EUR 156 M for 120 MWh/yr (Altech DFS) [VENDOR CLAIM PS-032]; Li-ion-style line ~$80 per kWh/yr at
1 GWh [ASSUMPTION, public gigafactory range $50-150]. Every other input is an [ASSUMPTION] listed in ASSUME.
Materials cost per kWh comes from the S12 build-up (P50), with a purchasing-scale factor.  Output: out/s15_results.json + charts.
"""
from __future__ import annotations
import copy, json, math, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent; LAB = HERE.parents[1]; OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(LAB / "sim/s12_chemistry_matrix")); sys.path.insert(0, str(LAB / "tools"))
import matrix as MX            # noqa: E402
from candidates import C       # noqa: E402
import prices as PR            # noqa: E402
CAND = {c["id"]: c for c in C}
S12 = json.load(open(LAB / "sim/s12_chemistry_matrix/out/s12_results.json"))["results"]
SCALES = [1, 10, 100, 1000]     # MWh/yr

ASSUME = dict(
    capex_ref=dict(S03=(120, 156e6 * 1.08, 0.70), N02=(1000, 80e6, 0.60)),   # (ref MWh/yr, ref capex USD, scaling exponent)
    crf=0.163,                                   # 10 yr, 10 %
    headcount=(8, 0.45),                         # n = a * Q^b   (Q in MWh/yr)
    salary_usd=dict(India=12000, USA=85000), overhead_on_labour=0.25, maintenance_of_capex=0.04,
    elec_kwh_per_kwh=dict(S03=(80, 35), N02=(50, 25)), elec_price=dict(India=0.09, USA=0.08),   # (at 1 MWh, at 1 GWh) linear in log Q
    yield_=(0.70, 0.85, 0.90, 0.94), recycle_credit=0.30, qc_share_of_conversion=0.08,
    area_m2_per=(4000, 0.7, 200), area_factor=dict(S03=1.5, N02=1.0),
    wc_days=dict(materials=60, finished=30),
)

def mat_cost_p50(cid, overrides=None, price_over=None, n=4000):
    c = copy.deepcopy(CAND[cid]); c.update(overrides or {})
    saved = dict(PR.PRICE)
    if price_over: MX.PRICE.update(price_over)
    b = MX.buildup(c); tot, parts = MX.materials_cost(c, b)
    MX.PRICE.clear(); MX.PRICE.update(saved)
    return float(np.median(tot)), float(np.median(b["cell"]))

def scenario(cid, Q, region):
    A = ASSUME; qref, cref, ex = A["capex_ref"][cid]
    capex = cref * (Q / qref) ** ex
    lg = math.log10(Q) / 3.0
    yld = A["yield_"][SCALES.index(Q)]
    mats = S12[cid]["mat_cost_P50"] * (1 + 2 * (1 - lg))          # lab-quantity purchasing x3 -> x1 at 1 GWh
    out_kwh = Q * 1000 * yld
    heads = A["headcount"][0] * Q ** A["headcount"][1]
    labour = heads * A["salary_usd"][region] * (1 + A["overhead_on_labour"])
    e0, e1 = A["elec_kwh_per_kwh"][cid]; ekwh = e0 + (e1 - e0) * lg
    energy = ekwh * Q * 1000 * A["elec_price"][region]
    dep = capex * A["crf"]; maint = capex * A["maintenance_of_capex"]
    conversion = (dep + maint + labour + energy) / out_kwh
    qc = conversion * A["qc_share_of_conversion"]
    scrap = mats * (1 / yld - 1) * (1 - A["recycle_credit"])
    cost = mats + scrap + conversion + qc
    area = (A["area_m2_per"][0] * (Q / 1000) ** A["area_m2_per"][1] + A["area_m2_per"][2]) * A["area_factor"][cid]
    wc = mats * Q * 1000 * A["wc_days"]["materials"] / 365 + cost * out_kwh * A["wc_days"]["finished"] / 365
    return dict(line=cid, MWh_per_yr=Q, region=region, capex_usd=round(capex), capex_per_kWh_yr=round(capex / (Q * 1000)), floor_m2=round(area),
                headcount=round(heads), power_MWh_per_yr=round(ekwh * Q, 1), yield_=yld, materials_usd_kWh=round(mats, 1),
                scrap_usd_kWh=round(scrap, 1), conversion_usd_kWh=round(conversion, 1), qc_usd_kWh=round(qc, 1), cell_cost_usd_kWh=round(cost, 1),
                working_capital_usd=round(wc), x_over_3usd=round(cost / 3.0, 0))

def tornado():
    """S03 cell materials cost at 1 GWh: one-at-a-time swings."""
    base, _ = mat_cost_p50("S03")
    swings = {
        "beta''-alumina price $15 / $200 per kg": ({}, {"beta_alumina": (15, 15, 15)}, {}, {"beta_alumina": (200, 200, 200)}),
        "disc thickness 0.5 / 1.5 mm": ({"base_mm": (0.5, 0.5, 0.5)}, {}, {"base_mm": (1.5, 1.5, 1.5)}, {}),
        "areal capacity 150 / 30 mAh/cm2": ({"Qa": (150, 150, 150)}, {}, {"Qa": (30, 30, 30)}, {}),
        "metal excess 1.6 / 3.0x": ({"ni_excess": (1.6, 1.6, 1.6)}, {}, {"ni_excess": (3.0, 3.0, 3.0)}, {}),
        "NaAlCl4 1.8 / 3.2 g/Ah": ({"melt_gAh": (1.8, 1.8, 1.8)}, {}, {"melt_gAh": (3.2, 3.2, 3.2)}, {}),
        "packaging 18 / 30 %": ({"pkg": (0.18, 0.18, 0.18)}, {}, {"pkg": (0.30, 0.30, 0.30)}, {}),
    }
    rows = []
    for k, (ol, pl, oh, ph) in swings.items():
        lo, _ = mat_cost_p50("S03", ol, pl); hi, _ = mat_cost_p50("S03", oh, ph); rows.append((k, lo, hi))
    best, _ = mat_cost_p50("S03", {"base_mm": (0.5, 0.5, 0.5), "Qa": (100, 100, 100)}, {"beta_alumina": (15, 15, 15)})
    return base, rows, best

def main():
    res = dict(assumptions=ASSUME, scenarios=[], notes=__doc__)
    for cid in ("S03", "N02"):
        for region in ("India", "USA"):
            for Q in SCALES:
                res["scenarios"].append(scenario(cid, Q, region))
    base, rows, best = tornado()
    res["tornado_S03_materials"] = dict(base=round(base, 1), rows=[(k, round(a, 1), round(b, 1)) for k, a, b in rows],
                                        G4_case_0p5mm_100mAh_15usdkg=round(best, 1))
    json.dump(res, open(OUT / "s15_results.json", "w"), indent=1)
    for s in res["scenarios"]:
        print(f"{s['line']} {s['region']:5} {s['MWh_per_yr']:5} MWh/yr capex ${s['capex_usd']/1e6:7.1f}M ({s['capex_per_kWh_yr']} $/kWh-yr) heads {s['headcount']:4} "
              f"mat {s['materials_usd_kWh']:6.1f} conv {s['conversion_usd_kWh']:7.1f} cell ${s['cell_cost_usd_kWh']:7.1f}/kWh")
    print("tornado base", res["tornado_S03_materials"])
    import plotstyle as ps; import matplotlib.pyplot as plt
    ps.apply(); fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
    for i, (cid, region) in enumerate([("S03", "India"), ("S03", "USA"), ("N02", "India"), ("N02", "USA")]):
        ss = [s for s in res["scenarios"] if s["line"] == cid and s["region"] == region]
        axs[0].plot(SCALES, [s["cell_cost_usd_kWh"] for s in ss], "o-" if cid == "S03" else "s--", color=ps.SERIES[i], label=f"{cid} {region}")
    axs[0].axhline(3, color=ps.STATUS["critical"], ls="--"); axs[0].text(1.1, 3.4, "$3/kWh [TARGET]", fontsize=7.5, color=ps.STATUS["critical"])
    axs[0].axhline(36, color=ps.TEXT2, ls=":"); axs[0].text(1.1, 39, "lowest LFP cell price 2025 $36 [PUBLISHED PS-017]", fontsize=7, color=ps.TEXT2)
    axs[0].set_xscale("log"); axs[0].set_yscale("log"); axs[0].set_xlabel("Factory scale (MWh/yr)"); axs[0].set_ylabel("Cell cost $/kWh (materials+scrap+conversion+QC)")
    axs[0].legend(fontsize=7); axs[0].set_title("Scenario cell cost vs scale")
    ax = axs[1]; rows = sorted(rows, key=lambda r: abs(r[2] - r[1]))
    for j, (k, lo, hi) in enumerate(rows):
        ax.barh(j, hi - base, left=base, color=ps.SERIES[1]); ax.barh(j, lo - base, left=base, color=ps.SERIES[0])
    ax.axvline(base, color=ps.TEXT); ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=7.5)
    ax.set_xlabel("S03 cell materials $/kWh (P50)"); ax.set_title(f"S03 materials sensitivity (base ${base:.0f}; G4 case ${best:.0f})")
    ps.save(fig, OUT / "s15_factory_and_tornado", "Factory scenario cell cost vs scale (India/USA) for the salt-iron and NFPP lines, and S03 materials-cost tornado.",
            "[CALCULATED] from [ASSUMPTION] inputs; Altech capex [VENDOR CLAIM]")

if __name__ == "__main__":
    main()
