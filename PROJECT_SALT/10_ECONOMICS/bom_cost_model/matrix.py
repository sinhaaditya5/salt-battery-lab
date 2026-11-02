#!/usr/bin/env python3
"""S12 - Quantitative chemistry feasibility matrix for Project Salt.

For every candidate in candidates.py:
  1. THEORETICAL specific energy from the balanced reaction (all reactants, both electrodes)  [CALCULATED]
  2. PRACTICAL cell specific energy from a Monte-Carlo mass build-up (triangular inputs, n=20,000) [CALCULATED from ASSUMPTION inputs]
     ladder: active pair -> electrode coatings -> cell -> pack
  3. Cell MATERIALS cost ($/kWh) from the same build-up and prices.py                             [CALCULATED from ASSUMPTION prices]
  4. Calibration gate: the build-up must reproduce benchmark cells (published Wh/kg) within +/-15 %.
  5. Founder-spec gate, weighted score (weights shown), rank under 3 weight sets, Pareto frontier.

Run:  python sim/s12_chemistry_matrix/matrix.py      (≈10 s)
Out:  sim/s12_chemistry_matrix/out/{chemistry_candidates.csv, s12_results.json, balanced_reactions.md, *.png/svg}
"""
from __future__ import annotations
import csv, json, math, re, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(HERE))
from candidates import C           # noqa: E402
from prices import PRICE, SEP_PRICE_M2  # noqa: E402
from pymatgen.core import Composition  # noqa: E402

OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
RNG = np.random.default_rng(20261102)
N = 20000
F_AH = 26.801  # Ah per mol e-
RHO = {"Al": 2.70, "Cu": 8.96, "SS": 7.9, "Ni": 8.9, "none": 0.0}
BASE_RHO = 3.26  # beta''-alumina g/cm3

def tri(t, n=N):
    lo, mo, hi = t
    if hi == lo: return np.full(n, float(lo))
    return RNG.triangular(lo, mo, hi, n)

def molar_mass(formula: str) -> float:
    f = formula.replace(".", "_DOT_") if False else formula
    return Composition(f).weight

# ------------------------------------------------------------------ theoretical
def theoretical(c):
    th = c["th"]
    m = sum(coef * molar_mass(sp) for sp, coef in th["reactants"].items())   # g per mol reaction
    wh_per_kg = th["n"] * F_AH * th["E"] / m * 1000.0
    return wh_per_kg, m

# ------------------------------------------------------------------ build-up
def buildup(c):
    """Return dict of arrays: g/Ah per component, V, pkg, and derived Wh/kg at each level."""
    a = c["arch"]; g = {}
    V = tri(c["V"]) if "V" in c else None
    if a == "layered":
        qc, fc, Qa = tri(c["qc"]), tri(c["fc"]), tri(c["Qa"])
        g["cam"] = 1000.0 / qc
        g["cathode_inactive"] = g["cam"] * (1 - fc) / fc
        an = c["an"]
        if an["type"] == "intercal":
            qa, fa, NP = tri(an["q"]), tri(an["f"]), tri(an["NP"])
            g["anode"] = NP * 1000.0 / qa
            g["anode_inactive"] = g["anode"] * (1 - fa) / fa
        elif an["type"] == "metal":
            g["anode"] = (1 + tri(an["excess"])) * 1000.0 / an["q"]
        # anodefree: nothing
        for side, key in (("cc_c", "cc_cathode"), ("cc_a", "cc_anode")):
            mat, t = c[side]
            g[key] = tri(t) * 1e-4 * RHO[mat] / 2.0 / Qa * 1000.0       # double-sided foil shared by 2 coatings
        if "sep_gm2" in c:
            g["separator"] = tri(c["sep_gm2"]) * 1e-4 / Qa * 1000.0
        if "se" in c:
            g["solid_electrolyte"] = tri(c["se"]["t_um"]) * 1e-4 * c["se"]["rho"] / Qa * 1000.0
        g["electrolyte"] = tri(c["elec_gAh"])
        active = g["cam"] + g.get("anode", 0)
        electrode = active + g["cathode_inactive"] + g.get("anode_inactive", 0)
    elif a == "tubular_molten":
        util, exc, add = tri(c["util"]), tri(c["ni_excess"]), tri(c["additive_frac"])
        Mm = 55.845 if c.get("metal") == "Fe" else 58.693
        g["NaCl"] = 1000 * 58.443 / F_AH / 1000 / util * 1.0   # g/Ah  (2.181/util)
        g["NaCl"] = 58.443 / F_AH / util
        g["metal"] = (Mm / 2) / F_AH * exc
        g["cathode_additives"] = (g["NaCl"] + g["metal"]) * add / (1 - add)
        g["melt_NaAlCl4"] = tri(c["melt_gAh"])
        Qa = tri(c["Qa"])
        g["beta_alumina"] = tri(c["base_mm"]) * 0.1 * BASE_RHO / Qa * 1000.0
        g["current_collector"] = tri(c["cc_gAh"])
        active = 58.443 / F_AH + (Mm / 2) / F_AH          # stoichiometric NaCl + metal per Ah
        electrode = g["NaCl"] + g["metal"] + g["cathode_additives"] + g["melt_NaAlCl4"]
    elif a == "tubular_molten_ns":
        util = tri(c["util"])
        g["Na"] = 22.99 / F_AH * (1 + tri(c["na_excess"]))
        g["S"] = 1.5 * 32.06 / F_AH / util
        g["felt"] = tri(c["felt_gAh"])
        Qa = tri(c["Qa"])
        g["beta_alumina"] = tri(c["base_mm"]) * 0.1 * BASE_RHO / Qa * 1000.0
        g["current_collector"] = tri(c["cc_gAh"])
        active = 22.99 / F_AH + 1.5 * 32.06 / F_AH
        electrode = g["Na"] + g["S"] + g["felt"]
    elif a == "metal_air":
        util = tri(c["anode_util"]); Qa = tri(c["Qa"])
        g["metal"] = 1000.0 / (c["metal_q"] * util)
        g["air_electrode"] = tri(c["air_g_cm2"]) / Qa * 1000.0
        g["electrolyte"] = tri(c["elec_gAh"])
        active = 1000.0 / c["metal_q"]
        electrode = g["metal"] + g["air_electrode"]
    elif a == "published_only":
        lo, hi, _ = c["published_cell"]
        cell = RNG.uniform(lo, hi, N)
        return dict(g={}, V=None, cell=cell, pack=cell * tri(c["pack"]), active=None, electrode=None, stack=None)
    else:
        raise ValueError(a)
    stack = sum(g.values())
    pkg = tri(c["pkg"])
    g["packaging"] = stack * pkg / (1 - pkg)
    cell_gAh = stack + g["packaging"]
    out = dict(g=g, V=V, Qa=Qa, active=V * 1000 / active, electrode=V * 1000 / electrode,
               stack=V * 1000 / stack, cell=V * 1000 / cell_gAh)
    out["pack"] = out["cell"] * tri(c["pack"])
    return out

# ------------------------------------------------------------------ cost
def materials_cost(c, b):
    """Cell materials cost $/kWh = sum(g/Ah * $/kg) / V. Returns array or None."""
    if b["V"] is None: return None
    ck = c.get("costkeys", {}); g = b["g"]; tot = np.zeros(N); parts = {}
    def add(name, gah, key):
        nonlocal tot
        if key is None or key not in PRICE: return
        v = gah * tri(PRICE[key]) / b["V"]; parts[name] = v; tot = tot + v
    a = c["arch"]
    if a == "layered":
        add("cam", g["cam"], ck.get("cam")); add("cathode_inactive", g["cathode_inactive"], "electrode_inactive")
        if "anode" in g: add("anode", g["anode"], ck.get("anode"))
        if "anode_inactive" in g: add("anode_inactive", g["anode_inactive"], "electrode_inactive")
        add("cc_cathode", g["cc_cathode"], ck.get("cc_c")); add("cc_anode", g["cc_anode"], ck.get("cc_a"))
        add("electrolyte", g["electrolyte"], ck.get("elec"))
        if "solid_electrolyte" in g: add("solid_electrolyte", g["solid_electrolyte"], ck.get("se"))
        if "separator" in g and ck.get("sep") in SEP_PRICE_M2:
            v = (0.1 / b["Qa"]) * tri(SEP_PRICE_M2[ck["sep"]]) / b["V"] * 1000.0   # m2/Ah * $/m2 / (Wh/Ah) -> $/kWh
            parts["separator"] = v; tot = tot + v
    elif a == "tubular_molten":
        add("NaCl", g["NaCl"], "NaCl_battery"); add("metal", g["metal"], "Fe_powder" if c.get("metal") == "Fe" else "Ni_powder")
        add("cathode_additives", g["cathode_additives"], "zebra_additives"); add("melt", g["melt_NaAlCl4"], "NaAlCl4")
        add("beta_alumina", g["beta_alumina"], "beta_alumina"); add("current_collector", g["current_collector"], "Ni_rod")
    elif a == "tubular_molten_ns":
        add("Na", g["Na"], "Na_metal"); add("S", g["S"], "sulfur"); add("felt", g["felt"], "graphite_felt")
        add("beta_alumina", g["beta_alumina"], "beta_alumina"); add("current_collector", g["current_collector"], "steel_case")
    elif a == "metal_air":
        add("metal", g["metal"], ck.get("anode")); add("air_electrode", g["air_electrode"], "air_electrode"); add("electrolyte", g["electrolyte"], ck.get("elec"))
    add("packaging", g["packaging"], ck.get("pkg"))
    return tot, parts

# ------------------------------------------------------------------ scoring
FIRE = {"S01": 3.5, "S02": 3.5, "S03": 3.5, "S04": 3, "N01": 2, "N02": 2, "N03": 2, "N04": 2, "N05": 5, "N06": 5, "N07": 3.5, "N08": 3.5,
        "N09": 1.5, "N10": 2, "N11": 1, "N12": 2, "N13": 1.5, "A01": 5, "A02": 5, "A03": 5, "A04": 4, "A05": 5, "A06": 2, "A07": 2,
        "B01": 1.5, "B02": 2.5, "B03": 3.5, "B04": 1.5, "B05": 1.5, "B06": 4}
SALT = {**{k: 5 for k in ("S01", "S02", "S03", "S04")}, **{k: 4 for k in ("N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08", "N09", "N10", "N11", "N12", "N13")},
        "A04": 3, "A06": 3, "A07": 3, "A01": 2, "A02": 2, "A03": 2, "A05": 2, **{k: 1 for k in ("B01", "B02", "B03", "B04", "B05", "B06")}}
SUPPLY = {"S01": 3, "S02": 3, "S03": 4.5, "S04": 4, "N01": 3.5, "N02": 5, "N03": 4.5, "N04": 2, "N05": 4.5, "N06": 4.5, "N07": 2.5, "N08": 3, "N09": 4.5,
          "N10": 4, "N11": 4.5, "N12": 4, "N13": 4.5, "A01": 4, "A02": 4, "A03": 5, "A04": 4, "A05": 4, "A06": 3, "A07": 3,
          "B01": 2, "B02": 3, "B03": 1.5, "B04": 2.5, "B05": 2, "B06": 4}
WEIGHTS = {
    "founder_spec": dict(energy=0.20, fast_charge=0.10, safety=0.15, salt=0.10, cost=0.15, cycle=0.10, trl=0.10, manuf=0.05, supply=0.05),
    "mobility":     dict(energy=0.35, fast_charge=0.20, safety=0.10, salt=0.05, cost=0.10, cycle=0.10, trl=0.05, manuf=0.03, supply=0.02),
    "stationary":   dict(energy=0.05, fast_charge=0.02, safety=0.25, salt=0.08, cost=0.25, cycle=0.20, trl=0.10, manuf=0.03, supply=0.02),
}

def logscore(x, lo, hi, invert=False):
    if x is None or not np.isfinite(x) or x <= 0: return 1.0
    s = (math.log(x) - math.log(lo)) / (math.log(hi) - math.log(lo))
    s = min(1, max(0, s)); s = 1 - s if invert else s
    return 1 + 4 * s

def scores(c, r):
    s = {}
    s["energy"] = logscore(r["cell_P50"], 20, 360)
    s["fast_charge"] = logscore(max(c["maxC_chg"][1], 0.01), 0.1, 12)
    s["safety"] = round((FIRE[c["id"]] + c["tox"]) / 2, 2)
    s["salt"] = SALT[c["id"]]
    s["cost"] = logscore(r.get("mat_cost_P50") or 400, 30, 400, invert=True)
    s["cycle"] = logscore(max(c["cycle"][1], 1), 30, 6000)
    s["trl"] = 1 + 4 * (c["trl"] - 1) / 8
    s["manuf"] = c["manuf"]; s["supply"] = SUPPLY[c["id"]]
    return {k: round(v, 2) for k, v in s.items()}

def pareto(points):
    """points: list of (id, energy(max), safety(max), cost(min)). Return ids not dominated."""
    keep = []
    for i, (a, e1, s1, c1) in enumerate(points):
        dom = False
        for j, (b, e2, s2, c2) in enumerate(points):
            if i != j and e2 >= e1 and s2 >= s1 and c2 <= c1 and (e2 > e1 or s2 > s1 or c2 < c1):
                dom = True; break
        if not dom: keep.append(a)
    return keep

# ------------------------------------------------------------------ main
def pct(x, q): return float(np.percentile(x, q))

def main():
    rows, res = [], {}
    for c in C:
        th, mrx = theoretical(c)
        b = buildup(c)
        r = dict(id=c["id"], name=c["name"], family=c["family"], benchmark=bool(c.get("benchmark")),
                 theoretical_Whkg=round(th, 0), reaction_mass_g_per_mol=round(mrx, 2))
        for lvl in ("active", "electrode", "stack", "cell", "pack"):
            x = b.get(lvl)
            if x is None: continue
            for q in (10, 50, 90): r[f"{lvl}_P{q}"] = round(pct(x, q), 1)
        mc = materials_cost(c, b)
        if mc is not None:
            tot, parts = mc
            for q in (10, 50, 90): r[f"mat_cost_P{q}"] = round(pct(tot, q), 1)
            r["cost_breakdown_P50"] = {k: round(pct(v, 50), 1) for k, v in parts.items()}
        if b["g"]:
            r["mass_breakdown_gAh_P50"] = {k: round(pct(v, 50), 3) for k, v in b["g"].items()}
        # spec gates (founder targets, [TARGET])
        r["gate_360Whkg_cell_P90"] = bool(r["cell_P90"] >= 360)
        r["gate_5min_charge(12C)"] = bool(c["maxC_chg"][1] >= 12)
        r["gate_nonflammable"] = FIRE[c["id"]] >= 4
        r["gate_low_toxicity"] = c["tox"] >= 4
        r["gate_salt_derived"] = SALT[c["id"]] >= 4
        r["gate_cycle_ge_2000"] = c["cycle"][1] >= 2000
        r["gates_passed_of_6"] = sum(r[k] for k in r if k.startswith("gate_"))
        r["scores"] = scores(c, r)
        for wname, w in WEIGHTS.items():
            r[f"score_{wname}"] = round(sum(w[k] * r["scores"][k] for k in w), 3)
        # calibration
        pub = c.get("published_cell")
        if c.get("benchmark") or c["id"] in ("S01", "N01"):
            if pub and pub[0] is not None and c["arch"] != "published_only":
                mid = (pub[0] + pub[1]) / 2
                r["calibration_published_mid"] = mid
                r["calibration_err_pct"] = round(100 * (r["cell_P50"] - mid) / mid, 1)
                r["calibration_pass_15pct"] = abs(r["calibration_err_pct"]) <= 15
        r.update({k: c[k] for k in ("T_op", "flammable", "tox", "tox_note", "moisture", "proc_T", "manuf", "manuf_note", "recyc", "recyc_note", "trl",
                                     "competitors", "refs", "salt_link", "cathode", "anode", "electrolyte", "separator", "collectors",
                                     "rxn_cathode", "rxn_anode", "rxn_overall", "heat_loss")})
        r["E_V_used"] = c["th"]["E"]; r["E_source"] = c["th"]["E_src"]
        r["cycle_life_range"] = f'{c["cycle"][0]}-{c["cycle"][1]} ({c["cycle"][2]})'
        r["max_discharge_C"] = f'{c["maxC_dis"][0]}-{c["maxC_dis"][1]}'; r["max_charge_C"] = f'{c["maxC_chg"][0]}-{c["maxC_chg"][1]}'
        r["published_cell_Whkg"] = (f"{pub[0]}-{pub[1]} ({pub[2]})" if pub else "none found")
        res[c["id"]] = r
    # ranks
    nonb = [r for r in res.values() if not r["benchmark"]]
    for wname in WEIGHTS:
        for i, r in enumerate(sorted(nonb, key=lambda r: -r[f"score_{wname}"]), 1): r[f"rank_{wname}"] = i
    pts = [(r["id"], r["cell_P50"], r["scores"]["safety"], r.get("mat_cost_P50", 1e9)) for r in nonb]
    front = pareto(pts)
    for r in nonb: r["pareto_energy_safety_cost"] = r["id"] in front
    pts2 = [(r["id"], r["cell_P50"], r["scores"]["safety"], 0) for r in nonb]
    front2 = pareto(pts2)
    for r in nonb: r["pareto_energy_safety"] = r["id"] in front2
    json.dump(dict(n_mc=N, seed=20261102, weights=WEIGHTS, results=res, pareto_energy_safety_cost=front, pareto_energy_safety=front2),
              open(OUT / "s12_results.json", "w"), indent=1, default=str)
    write_csv(res); write_reactions(res); plots(res, front)
    print_summary(res, front, front2)

def write_csv(res):
    cols = ["id", "name", "family", "benchmark", "salt_link", "rxn_overall", "rxn_cathode", "rxn_anode", "cathode", "anode", "electrolyte", "separator",
            "collectors", "E_V_used", "E_source", "theoretical_Whkg", "active_P50", "electrode_P50", "cell_P10", "cell_P50", "cell_P90", "pack_P10", "pack_P50",
            "pack_P90", "published_cell_Whkg", "calibration_err_pct", "mat_cost_P10", "mat_cost_P50", "mat_cost_P90", "max_discharge_C", "max_charge_C",
            "cycle_life_range", "T_op", "flammable", "tox", "tox_note", "moisture", "proc_T", "manuf", "manuf_note", "recyc", "recyc_note", "trl", "heat_loss",
            "gate_360Whkg_cell_P90", "gate_5min_charge(12C)", "gate_nonflammable", "gate_low_toxicity", "gate_salt_derived", "gate_cycle_ge_2000",
            "gates_passed_of_6", "score_founder_spec", "rank_founder_spec", "score_mobility", "rank_mobility", "score_stationary", "rank_stationary",
            "pareto_energy_safety_cost", "competitors", "refs"]
    with open(OUT / "chemistry_candidates.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for r in res.values(): w.writerow(r)

def write_reactions(res):
    L = ["# Balanced reactions and theoretical specific energy (S12)", "",
         "Generated by `sim/s12_chemistry_matrix/matrix.py`. Theoretical specific energy = n·F·E / Σ(M_reactants) with F = 26.801 Ah/mol,",
         "masses from pymatgen; the mass basis is **every reactant consumed on discharge (both electrodes)** and no inactive material [CALCULATED].",
         "Intercalation hosts use a reversible-limit stoichiometry (x shown) - not a full-lattice limit. Hard carbon is written C7.44 (≈300 mAh/g).", "",
         "| ID | Overall reaction (discharge unless noted) | Cathode half-reaction | Anode half-reaction | n e⁻ | E (V) | Σ M (g/mol) | Theoretical Wh/kg | E source |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in res.values():
        L.append(f"| {r['id']} | {r['rxn_overall']} | {r['rxn_cathode']} | {r['rxn_anode']} | {next(c['th']['n'] for c in C if c['id']==r['id'])} | "
                 f"{r['E_V_used']} | {r['reaction_mass_g_per_mol']} | **{int(r['theoretical_Whkg'])}** | {r['E_source']} |")
    L += ["", "Charge balance: each half-reaction pair transfers the same n electrons; mass balance verified by pymatgen formula parsing "
          "(test: `tests/test_project_salt.py::test_reactions_balanced`)."]
    (OUT / "balanced_reactions.md").write_text("\n".join(L) + "\n")

def plots(res, front):
    sys.path.insert(0, str(LAB / "tools")); import plotstyle as ps; import matplotlib.pyplot as plt
    ps.apply()
    # 1. ladder: theoretical vs cell P10-P90 vs pack, sorted by cell P50
    rs = sorted(res.values(), key=lambda r: r["cell_P50"])
    fig, ax = plt.subplots(figsize=(8.6, 9.2))
    y = np.arange(len(rs))
    for i, r in enumerate(rs):
        col = ps.DEEMPH if r["benchmark"] else (ps.SERIES[1] if r["id"].startswith("S") else ps.SERIES[0])
        ax.plot([r["cell_P10"], r["cell_P90"]], [i, i], color=col, lw=5, alpha=0.55, solid_capstyle="butt")
        ax.plot(r["cell_P50"], i, "o", color=col, ms=6)
        ax.plot(r["theoretical_Whkg"], i, "|", color=ps.TEXT2, ms=9)
        if "pack_P50" in r: ax.plot(r["pack_P50"], i, "v", color=col, ms=5, mfc="none")
    ax.axvline(360, color=ps.STATUS["critical"], lw=1.4, ls="--")
    ax.text(370, len(rs) - 0.6, "Founder target 360 Wh/kg (cell) [TARGET]", color=ps.STATUS["critical"], fontsize=8, va="top")
    ax.set_yticks(y); ax.set_yticklabels([f"{r['id']}  {r['name'][:52]}" for r in rs], fontsize=7.2)
    ax.set_xscale("log"); ax.set_xlim(8, 4000); ax.set_xlabel("Specific energy (Wh/kg, log scale)")
    ax.set_title("Theoretical (|) vs practical cell P10–P50–P90 (bar, ●) vs pack P50 (▽)")
    ax.text(0.99, 0.01, "orange = NaCl is the active material · blue = other non-Li candidates · grey = Li/Pb benchmarks", transform=ax.transAxes,
            ha="right", fontsize=7, color=ps.TEXT2)
    ps.save(fig, OUT / "s12_energy_ladder", "Theoretical vs practical cell and pack specific energy for 30 architectures; Monte-Carlo build-up n=20,000.",
            "[CALCULATED] theoretical; [CALCULATED from ASSUMPTION inputs] practical; benchmarks calibrated to [PUBLISHED]/[VENDOR CLAIM] cells")
    # 2. Pareto: energy vs cost, marker = safety
    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    for r in res.values():
        if "mat_cost_P50" not in r: continue
        bm = r["benchmark"]; onf = r.get("pareto_energy_safety_cost")
        col = ps.DEEMPH if bm else (ps.SERIES[1] if r["id"].startswith("S") else ps.SERIES[0])
        size = 18 + 22 * r["scores"]["safety"]
        ax.scatter(r["cell_P50"], r["mat_cost_P50"], s=size, color=col, edgecolor=ps.TEXT if onf else "none", lw=1.2, zorder=3)
        ax.annotate(r["id"], (r["cell_P50"], r["mat_cost_P50"]), xytext=(4, 3), textcoords="offset points", fontsize=7, color=ps.TEXT2)
    ax.axvline(360, color=ps.STATUS["critical"], lw=1.2, ls="--"); ax.axhline(3, color=ps.STATUS["critical"], lw=1.2, ls="--")
    ax.text(365, 3.4, "$3/kWh [TARGET]", fontsize=7.5, color=ps.STATUS["critical"])
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(8, 700); ax.set_ylim(2, 3000)
    ax.set_xlabel("Practical cell specific energy P50 (Wh/kg)"); ax.set_ylabel("Cell materials cost P50 ($/kWh)")
    ax.set_title("Energy vs materials cost; marker size = safety score; outlined = Pareto-optimal (energy↑ safety↑ cost↓)")
    ps.save(fig, OUT / "s12_pareto", "Pareto frontier over practical cell Wh/kg, safety score and cell materials cost (non-benchmark candidates).",
            "[CALCULATED from ASSUMPTION prices and inputs]")

def print_summary(res, front, front2):
    print(f"{'id':4} {'theo':>6} {'cell P10/50/90':>18} {'pack50':>7} {'$/kWh50':>8} gates rank_fs  name")
    for r in sorted(res.values(), key=lambda r: -r["cell_P50"]):
        print(f"{r['id']:4} {r['theoretical_Whkg']:6.0f} {r['cell_P10']:6.0f}{r['cell_P50']:6.0f}{r['cell_P90']:6.0f} {r.get('pack_P50',0):7.0f} "
              f"{r.get('mat_cost_P50', float('nan')):8.0f} {r['gates_passed_of_6']}/6  {r.get('rank_founder_spec','-'):>3}  {r['name'][:55]}"
              + (f"  [calib {r['calibration_err_pct']:+.0f}%]" if 'calibration_err_pct' in r else ""))
    print("Pareto (energy, safety, cost):", front); print("Pareto (energy, safety):", front2)

if __name__ == "__main__":
    main()
