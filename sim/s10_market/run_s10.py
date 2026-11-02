"""S10 — Bottom-up market sizing for the indoor/backup wedge (India first), every input cited or tagged.

TAM: annual battery demand (GWh/yr x $/kWh) for India telecom-site backup + data-centre UPS.
SAM: the share where non-flammability / no-lead / indoor constraints plausibly change the purchase.
SOM: a 5-year obtainable share for a new entrant.
Monte Carlo over the ranges; cross-checked against paid-report UPS-battery market sizes (SRC-137/138).
"""
import json, pathlib, sys
import numpy as np
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
from params.product_params import USD_INR
import plotstyle as ps
import matplotlib.pyplot as plt

OUT = pathlib.Path(__file__).parent / "out"; OUT.mkdir(exist_ok=True)
INPUTS = {
    "towers": (816763, 816763, "LIT", "DoT tower installations 30 Dec 2024 (SRC-134)"),
    "kWh_per_site": (8.0, 20.0, "ASSUMPTION", "48 V x 150-400 Ah; Amara Raja reports ~1 GWh over ~50k sites = ~20 kWh/site [VENDOR, low conf.]"),
    "telecom_replace_years": (4.0, 7.0, "ASSUMPTION", "VRLA 3-5 y, Li 8-10 y blended"),
    "dc_GW_2026": (1.6, 1.6, "LIT", "JLL June 2026 (SRC-124)"),
    "dc_GW_2029": (6.0, 6.0, "LIT", "JLL 2029 projection (SRC-124)"),
    "ups_minutes": (5.0, 10.0, "LIT/ASSUMPTION", "~5 min colo/cloud, 1-2 min hyperscale (SRC-142); 10 min upper case"),
    "ups_redundancy": (1.0, 2.0, "ASSUMPTION", "N to 2N battery strings"),
    "dc_replace_years": (5.0, 10.0, "ASSUMPTION", "VRLA ~5 y, Li ~10 y"),
    "price_usd_per_kWh": (85.0, 200.0, "CALC", "VRLA INR 7,100-7,600/kWh (SRC-121) to 48 V LFP INR 10,800-21,600/kWh (SRC-119) at INR 88/$"),
    "sam_fraction_telecom": (0.10, 0.30, "ASSUMPTION", "indoor/rooftop/in-building sites, theft-prone or hot unconditioned sites where no-lead/non-flammable matters"),
    "sam_fraction_dc": (0.20, 0.50, "ASSUMPTION", "UPS rooms where Li-ion fire engineering is a real constraint"),
    "som_share_5y": (0.02, 0.08, "ASSUMPTION", "new entrant share of SAM after 5 years"),
}


def draw(rng, k):
    lo, hi = INPUTS[k][:2]
    return lo if lo == hi else float(rng.uniform(lo, hi))


def main():
    rng = np.random.default_rng(11)
    out = []
    for _ in range(5000):
        d = {k: draw(rng, k) for k in INPUTS}
        tel_GWh = d["towers"] * d["kWh_per_site"] / 1e6 / d["telecom_replace_years"]
        dc_GW_avg = (d["dc_GW_2026"] + d["dc_GW_2029"]) / 2
        dc_new = (d["dc_GW_2029"] - d["dc_GW_2026"]) / 3 * d["ups_minutes"] / 60 * d["ups_redundancy"]
        dc_repl = dc_GW_avg * d["ups_minutes"] / 60 * d["ups_redundancy"] / d["dc_replace_years"]
        dc_GWh = dc_new + dc_repl
        tam = (tel_GWh + dc_GWh) * 1e6 * d["price_usd_per_kWh"]
        sam = (tel_GWh * d["sam_fraction_telecom"] + dc_GWh * d["sam_fraction_dc"]) * 1e6 * d["price_usd_per_kWh"]
        som = sam * d["som_share_5y"]
        out.append((tel_GWh, dc_GWh, tam, sam, som))
    a = np.array(out)
    pct = lambda x: {"p10": float(np.percentile(x, 10)), "p50": float(np.percentile(x, 50)), "p90": float(np.percentile(x, 90))}
    res = {"label": "[CALC] Monte Carlo from cited [LIT] and [ASSUMPTION] inputs; India only, annual flow",
           "inputs": {k: {"range": v[:2], "tag": v[2], "source": v[3]} for k, v in INPUTS.items()},
           "telecom_GWh_yr": pct(a[:, 0]), "dc_ups_GWh_yr": pct(a[:, 1]),
           "TAM_usd_yr": pct(a[:, 2]), "SAM_usd_yr": pct(a[:, 3]), "SOM_usd_yr_after_5y": pct(a[:, 4]),
           "crosscheck": {"IMARC India UPS battery market 2024": 305.12e6, "TechSci India UPS battery 2025": 401e6,
                          "sources": "SRC-137, SRC-138 (paid-report press summaries, low confidence)"}}
    (OUT / "s10_results.json").write_text(json.dumps(res, indent=1))
    # chart: TAM / SAM / SOM with P10-P90 whiskers (bars, one axis, log scale)
    fig, ax = plt.subplots(figsize=(5.8, 3.2))
    names = ["TAM (India backup batteries)", "SAM (where 'allowed indoors' matters)", "SOM (5-yr new-entrant share)"]
    keys = ["TAM_usd_yr", "SAM_usd_yr", "SOM_usd_yr_after_5y"]
    for i, k in enumerate(keys):
        p = res[k]
        ax.barh(i, p["p50"] / 1e6, color=ps.SERIES[0], height=0.5)
        ax.plot([p["p10"] / 1e6, p["p90"] / 1e6], [i, i], color=ps.TEXT2, lw=1.2)
        ax.text(p["p90"] / 1e6 * 1.08, i, f"${p['p50']/1e6:,.0f}M  (P10–P90 {p['p10']/1e6:,.0f}–{p['p90']/1e6:,.0f})", va="center", fontsize=7.5, color=ps.TEXT2)
    ax.set_xscale("log"); ax.set_xlim(0.5, 5000)
    ax.set_yticks(range(3)); ax.set_yticklabels(names); ax.invert_yaxis()
    ax.set_xlabel("$ million per year (log scale)")
    ax.set_title("Bottom-up market for the indoor-backup wedge (India)")
    ps.save(fig, OUT / "s10_tam_sam_som", "Annual India market for telecom-site and data-centre UPS backup batteries (TAM), the part where non-flammability plausibly changes the purchase (SAM), and a 5-year obtainable share (SOM).",
            "[CALC] Monte Carlo over [LIT] tower count and data-centre capacity and [ASSUMPTION] kWh/site, runtime, replacement, price and share ranges")
    for k in ("telecom_GWh_yr", "dc_ups_GWh_yr", "TAM_usd_yr", "SAM_usd_yr", "SOM_usd_yr_after_5y"):
        p = res[k]; f = 1e6 if "usd" in k else 1
        print(f"{k:22s} P10 {p['p10']/f:8.2f}  P50 {p['p50']/f:8.2f}  P90 {p['p90']/f:8.2f}")


if __name__ == "__main__":
    main()
