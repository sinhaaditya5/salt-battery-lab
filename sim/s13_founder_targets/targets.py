#!/usr/bin/env python3
"""S13b - Founder targets, tested quantitatively.

  A. 1,500 km on one charge, refilled in ~5 minutes        (vehicle energy, pack mass, MW, C-rate, current, heat)
  B. Electrode physics of a 5-minute charge                 (max loading vs electrolyte transport; energy penalty; metal-anode current density)
  C. The '$3' target under six interpretations             (theoretical minimum, BOM, conversion, plausibility)
  D. Common salt as feedstock                               (NaCl, water and energy per kWh for each route)

All founder numbers are [TARGET]; all model inputs are [ASSUMPTION] unless a source ID is shown;
outputs are [CALCULATED]. Run: python sim/s13_founder_targets/targets.py   (~20 s)
"""
from __future__ import annotations
import copy, json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent; LAB = HERE.parents[1]; OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(LAB / "sim/s12_chemistry_matrix")); sys.path.insert(0, str(LAB / "tools"))
import matrix as M          # noqa: E402  (S12 engine: buildup, materials_cost)
from candidates import C    # noqa: E402
CAND = {c["id"]: c for c in C}
S12 = json.load(open(LAB / "sim/s12_chemistry_matrix/out/s12_results.json"))["results"]

TARGET = dict(range_km=1500, charge_min=5, cell_Whkg=360, cost_usd=3.0)

# ------------------------------------------------------------------ A. vehicle
VEH = {  # name: (consumption at battery, Wh/km, at reference mass; vehicle mass without battery, kg)   [ASSUMPTION]
    "efficient sedan": (130, 1500), "mid SUV": (170, 1800), "large SUV / pickup": (230, 2300), "heavy truck (40 t)": (1150, 14000)}
ETA_CHG = 0.92          # grid-to-cell charging efficiency [ASSUMPTION]
USABLE = 0.90           # usable SOC window [ASSUMPTION]
ALPHA = 0.5             # share of consumption that scales with vehicle mass [ASSUMPTION]
MCS_MAX_MW = 3.75       # 3,000 A x 1,250 V [PUBLISHED PS-033]; deployed units 1.0-1.2 MW
DEPLOYED_MAX_MW = 1.3   # CATL Shenxing gen-2 claim 1.3 MW peak [VENDOR CLAIM PS-018]; BYD 1 MW [PS-019]

def vehicle_case(name, cons0, m_body, pack_whkg, ref_batt_kg=500):
    m_ref = m_body + ref_batt_kg
    E_use = TARGET["range_km"] * cons0 / 1000.0
    for _ in range(50):                                   # mass <-> consumption fixed point
        E_inst = E_use / USABLE
        m_batt = E_inst * 1000.0 / pack_whkg
        cons = cons0 * (1 + ALPHA * ((m_body + m_batt) / m_ref - 1))
        E_new = TARGET["range_km"] * cons / 1000.0
        if abs(E_new - E_use) < 1e-3: break
        E_use = E_new
    E_in = E_use / ETA_CHG
    P_MW = E_in / (TARGET["charge_min"] / 60.0) / 1000.0
    return dict(vehicle=name, pack_Whkg=pack_whkg, consumption_Wh_km=round(cons, 1), usable_kWh=round(E_use, 1), installed_kWh=round(E_inst, 1),
                battery_mass_kg=round(m_batt, 0), battery_share_of_vehicle_mass=round(m_batt / (m_body + m_batt), 2),
                avg_charge_power_MW=round(P_MW, 2), avg_C_rate=round(P_MW * 1000 / E_inst, 1),
                current_kA_at_800V=round(P_MW * 1e3 / 800, 2), current_kA_at_1250V=round(P_MW * 1e3 / 1250, 2),
                x_MCS_ceiling=round(P_MW / MCS_MAX_MW, 2), x_best_deployed=round(P_MW / DEPLOYED_MAX_MW, 1))

def heat_case(E_in_kWh, asr_ohm_cm2, Qa, V, C_rate, batt_kg):
    j = C_rate * Qa / 1000.0                      # A/cm2
    frac = j * asr_ohm_cm2 / V                   # fraction of charge energy lost as heat
    Q_kWh = E_in_kWh * frac
    P_kW = Q_kWh / (5 / 60)
    dT_adiabatic = Q_kWh * 3.6e6 / (batt_kg * 1000.0)  # cp ~1000 J/kg/K pack average [ASSUMPTION]
    return dict(ASR_ohm_cm2=asr_ohm_cm2, current_density_mA_cm2=round(1000 * j, 1), heat_fraction=round(frac, 3), heat_kWh=round(Q_kWh, 1),
                heat_rejection_kW=round(P_kW, 0), adiabatic_dT_K=round(dT_adiabatic, 1))

# ------------------------------------------------------------------ B. electrode physics
def transport_limited_loading(t_charge_s=300.0, De=2.5e-6, eps=0.30, brugg=1.5, k=3.0):
    """Max electrode thickness for electrolyte diffusion time L^2/D_eff <= t/k, and the areal capacity that implies."""
    Deff = De * eps ** brugg
    L = math.sqrt(Deff * t_charge_s / k)          # cm
    return Deff, L

def areal_capacity(L_cm, solid_frac, rho, f_active, q_mAh_g):
    return L_cm * solid_frac * rho * f_active * q_mAh_g

def energy_at_loading(cid, Qa, n=4000):
    c = copy.deepcopy(CAND[cid]); c["Qa"] = (Qa, Qa, Qa)
    M.N = n
    b = M.buildup(c)
    M.N = 20000
    return float(np.median(b["cell"]))

# ------------------------------------------------------------------ C. $3 interpretations
FEEDPRICE = {  # USD/kg, cheapest industrial form of each reactant [ASSUMPTION; NaCl/soda ash context PS-021/PS-022]
    "NaCl": 0.06, "Na2CO3": 0.30, "Na_metal": 3.5, "Ni": 15.0, "Fe": 0.45, "Fe_powder": 2.0, "Mn_oxide": 1.5, "H3PO4": 1.0, "hard_carbon_precursor": 0.5,
    "S": 0.15, "Zn": 2.8, "MnO2_EMD": 2.0, "Li2CO3": 10.0, "FePO4": 1.5, "graphite": 3.0, "Na4Fe(CN)6": 2.0, "MnSO4": 0.8}
# grams of feedstock per mol of reaction (discharged-state assembly where that is how the cell is built)
FEED = {
    "S01": dict(n=2, E=2.58, g={"NaCl": 116.89, "Ni": 58.69}),
    "S03": dict(n=2, E=2.35, g={"NaCl": 116.89, "Fe": 55.85}),
    "S04": dict(n=1, E=3.98, g={"NaCl": 58.44}),
    "N01": dict(n=0.6, E=3.15, g={"Na2CO3": 53.0, "Ni": 19.56, "Fe": 18.62, "Mn_oxide": 25.4, "hard_carbon_precursor": 53.6 / 0.5}),
    "N02": dict(n=3, E=3.10, g={"Na2CO3": 212.0, "Fe": 167.5, "H3PO4": 392.0, "hard_carbon_precursor": 268.0 / 0.5}),
    "N03": dict(n=2, E=3.30, g={"Na4Fe(CN)6": 304.0, "MnSO4": 151.0, "hard_carbon_precursor": 178.7 / 0.5}),
    "N09": dict(n=2, E=1.85, g={"Na_metal": 45.98, "S": 32.06}),
    "A01": dict(n=2, E=1.35, g={"Zn": 65.38, "MnO2_EMD": 173.9}),
    "A03": dict(n=2, E=1.28, g={"Fe": 55.85}),
    "B02": dict(n=1, E=3.30, g={"Li2CO3": 36.95, "FePO4": 150.8, "graphite": 72.06}),
}
# conversion cost floor at >=1 GWh/yr ($/kWh, materials excluded): depreciation + labour + energy + overhead + yield loss [ASSUMPTION; see S14]
CONVERSION_1GWH = {"layered": (8, 14, 25), "tubular_molten": (25, 45, 90), "metal_air": (10, 20, 40), "published_only": (10, 15, 25)}
PACK_ADDER = (8, 15, 30)   # $/kWh enclosure, BMS, thermal, assembly at scale [ASSUMPTION]
HEATING_SHARE = {"S01": 0.10, "S02": 0.07, "S03": 0.07}   # fraction of throughput lost to self-heating, stationary daily cycling [PS-011 basis]

def theoretical_min_cost(cid):
    f = FEED[cid]; wh = f["n"] * 26.801 * f["E"]                      # Wh per mol reaction
    usd = sum(g / 1000 * FEEDPRICE[k] for k, g in f["g"].items())
    return usd / (wh / 1000.0), {k: round(g / 1000 * FEEDPRICE[k] / (wh / 1000), 2) for k, g in f["g"].items()}

def lcos(capex_kwh, cycles, dod=0.9, rte=0.9, om_frac=0.015, years=15, disc=0.08, cycles_per_year=330, heat=0.0):
    """Levelised cost per kWh delivered (USD/kWh) - simple annuity model."""
    crf = disc * (1 + disc) ** years / ((1 + disc) ** years - 1)
    life_years = min(years, cycles / cycles_per_year)
    crf_l = disc * (1 + disc) ** life_years / ((1 + disc) ** life_years - 1) if life_years > 0 else 1
    annual = capex_kwh * crf_l + capex_kwh * om_frac
    delivered = cycles_per_year * dod * rte * (1 - heat)
    return annual / delivered

def interpretations(cid):
    r = S12[cid]; c = CAND[cid]
    arch = c["arch"]
    conv = CONVERSION_1GWH.get(arch, (10, 15, 25))
    mat10, mat50 = r.get("mat_cost_P10"), r.get("mat_cost_P50")
    cell_floor = (mat10 or 0) + conv[0]; cell_mid = (mat50 or 0) + conv[1]
    pack_floor = cell_floor + PACK_ADDER[0]; pack_mid = cell_mid + PACK_ADDER[1]
    whkg = r["cell_P50"]
    tmin, tparts = theoretical_min_cost(cid) if cid in FEED else (None, None)
    cyc = c["cycle"][1]
    out = dict(id=cid, name=r["name"], cell_Whkg_P50=whkg, theoretical_min_material_usd_kWh=None if tmin is None else round(tmin, 2),
               theoretical_min_breakdown=tparts, cell_materials_P10=mat10, cell_materials_P50=mat50, conversion_1GWh=conv,
               cell_cost_floor=round(cell_floor, 1), cell_cost_mid=round(cell_mid, 1), pack_cost_floor=round(pack_floor, 1), pack_cost_mid=round(pack_mid, 1))
    # 1 $3/kWh cell
    out["I1_cell_3usd_kWh"] = dict(target=3.0, floor=round(cell_floor, 1), verdict="IMPLAUSIBLE" if cell_floor > 3 else "PLAUSIBLE",
                                   gap_x=round(cell_floor / 3, 1))
    # 2 $3/kWh pack
    out["I2_pack_3usd_kWh"] = dict(target=3.0, floor=round(pack_floor, 1), verdict="IMPLAUSIBLE", gap_x=round(pack_floor / 3, 1))
    # 3 $3/kg finished cells
    eq = 3.0 / (whkg / 1000.0)
    out["I3_3usd_per_kg_cell"] = dict(target_usd_per_kg=3.0, equivalent_usd_kWh=round(eq, 1), floor_usd_kWh=round(cell_floor, 1),
                                      verdict="PLAUSIBLE" if cell_floor <= eq else ("NEAR (within 2x)" if cell_floor <= 2 * eq else "IMPLAUSIBLE"),
                                      floor_usd_per_kg=round(cell_floor * whkg / 1000.0, 2))
    # 4 $3 per finished unit
    out["I4_3usd_per_unit"] = dict(max_unit_energy_Wh_at_floor=round(3.0 / cell_floor * 1000, 1), max_unit_energy_Wh_at_mid=round(3.0 / cell_mid * 1000, 1),
                                   verdict=f"PLAUSIBLE only for units <= ~{3.0 / cell_floor * 1000:.0f} Wh (single small cells); IMPLAUSIBLE for modules/packs")
    # 5 $3/kWh conversion excl. materials
    out["I5_conversion_3usd_kWh"] = dict(target=3.0, floor=conv[0], verdict="IMPLAUSIBLE" if conv[0] > 3 else "PLAUSIBLE", gap_x=round(conv[0] / 3, 1))
    # 6 levelised
    heat = HEATING_SHARE.get(cid, 0.0)
    l_floor = lcos(pack_floor * 1.6, cyc, heat=heat)     # installed system ~1.6x pack (PCS, BOS, EPC) [ASSUMPTION]
    l_mid = lcos(pack_mid * 1.6, cyc, heat=heat)
    out["I6_levelised"] = dict(lcos_floor_usd_per_kWh_delivered=round(l_floor, 3), lcos_mid=round(l_mid, 3),
                               as_3_usd_per_kWh_delivered="TRIVIALLY MET (meaningless as a target)" if l_mid < 3 else "NOT MET",
                               as_3_cents_per_kWh_delivered=("PLAUSIBLE" if l_floor <= 0.03 else ("NEAR" if l_floor <= 0.06 else "IMPLAUSIBLE")))
    return out

# ------------------------------------------------------------------ D. salt feedstock
def salt_routes():
    """kg NaCl, water and energy per kWh of cell for each way NaCl can enter a battery."""
    rows = []
    # direct: ZEBRA/IT Na-MCl2, Na-Cl2. NaCl g/Ah from S12 mass breakdown
    for cid in ("S01", "S03", "S04"):
        g = S12[cid]["mass_breakdown_gAh_P50"]; V = CAND[cid]["V"][1]
        nacl = (g.get("NaCl") or (58.44 / 26.801)) / V          # kg/kWh
        rows.append(dict(route=f"{cid} direct NaCl in cathode", chloride_role="Cl is the electroactive anion (Cl-/Cl2 or MCl2/NaCl)",
                         kg_NaCl_per_kWh=round(nacl, 2), process="dry + purify solar/vacuum salt (low Ca, Mg, SO4, H2O)",
                         energy_kWh_per_kWh_cell=round(nacl * 0.15, 3), water_L_per_kWh=round(nacl * 0.5, 2),
                         byproducts="none from salt (Cl stays in the cell)", label="[CALCULATED]; drying/purification energy 0.15 kWh/kg [ASSUMPTION]"))
    # Na-ion via soda ash (Solvay): Na2CO3 needed per kWh from cathode Na content
    for cid, na_mol_per_mol, M_cam in (("N02", 4, 620.4), ("N01", 1, 111.5)):
        g_cam = S12[cid]["mass_breakdown_gAh_P50"]["cam"]; V = CAND[cid]["V"][1]
        kg_cam = g_cam / V
        kg_na2co3 = kg_cam / M_cam * na_mol_per_mol / 2 * 105.99
        rows.append(dict(route=f"{cid} Na-ion via soda ash (Solvay, India)", chloride_role="Cl leaves as CaCl2 effluent (~1 t per t soda ash)",
                         kg_NaCl_per_kWh=round(kg_na2co3 * 1.6, 2), process="Solvay: NaCl + CaCO3 -> Na2CO3 + CaCl2 (NH3 recycle)",
                         energy_kWh_per_kWh_cell=round(kg_na2co3 * 3.3, 2), water_L_per_kWh=round(kg_na2co3 * 10, 1),
                         byproducts="CaCl2 brine; CO2", label="[CALCULATED]; 1.6 kg NaCl and ~12 GJ (3.3 kWh) per kg soda ash, 10 L water/kg [ASSUMPTION]"))
    # Na metal via Downs cell
    for cid, g_na_per_Ah in (("N09", 0.858 * 2.0),):
        V = CAND[cid]["V"][1]; kg_na = g_na_per_Ah / V
        rows.append(dict(route=f"{cid} Na metal via Downs cell", chloride_role="Cl2 co-product must be sold or handled",
                         kg_NaCl_per_kWh=round(kg_na * 2.54, 2), process="molten NaCl/CaCl2 electrolysis ~600 C",
                         energy_kWh_per_kWh_cell=round(kg_na * 10, 2), water_L_per_kWh=0.0, byproducts="Cl2 (1.54 kg per kg Na)",
                         label="[CALCULATED]; ~10 kWh electricity per kg Na [ASSUMPTION]"))
    sea = dict(route="Seawater direct (any route)", note="35 g/L dissolved salts; ~29 L seawater per kg NaCl plus Mg/Ca/SO4 removal. "
               "Solar salt pans (Gujarat, Tamil Nadu) already do this at near-zero energy; a battery company gains nothing by extracting its own. "
               "Thermal evaporation would cost ~65 MJ/kg NaCl. [CALCULATED from ASSUMPTION]")
    return rows, sea

# ------------------------------------------------------------------ main
def main():
    res = dict(targets=TARGET)
    # A
    packs = {"founder target 360 cell x 0.80": 288.0, "best non-Li P50 (N08 anode-free Na SSB) pack": S12["N08"]["pack_P50"],
             "commercial Na-ion (N01) pack": S12["N01"]["pack_P50"], "ZEBRA (S01) pack": S12["S01"]["pack_P50"]}
    res["A_vehicle"] = [vehicle_case(v, c0, mb, pw) | {"pack_case": pk} for pk, pw in packs.items() for v, (c0, mb) in VEH.items()]
    sedan = next(x for x in res["A_vehicle"] if x["vehicle"] == "mid SUV" and x["pack_case"].startswith("founder"))
    res["A_heat_midSUV_founder_pack"] = [heat_case(sedan["usable_kWh"] / ETA_CHG, asr, 3.0, 3.6, sedan["avg_C_rate"], sedan["battery_mass_kg"]) for asr in (5, 10, 20, 40)]
    res["A_station"] = dict(stalls=8, peak_MW=round(8 * sedan["avg_charge_power_MW"], 1),
                            note="8 stalls at the founder's spec need ~%.0f MW grid connection or on-site buffer storage; a typical 8-stall 350 kW site is ~2.8 MW." % (8 * sedan["avg_charge_power_MW"]))
    # B
    Deff, L = transport_limited_loading()
    qa_cath = areal_capacity(L, 0.70, 4.5, 0.95, 150)        # Na layered oxide
    qa_an = areal_capacity(L, 0.70, 1.6, 0.95, 300) / 1.10   # hard carbon, divided by N/P
    qa_lim = min(qa_cath, qa_an)
    res["B_electrode"] = dict(D_eff_cm2_s=Deff, L_max_um=round(L * 1e4, 1), Qa_max_cathode_mAh_cm2=round(qa_cath, 2), Qa_max_anode_mAh_cm2=round(qa_an, 2),
                              Qa_max_cell=round(qa_lim, 2), particle_radius_max_um_at_Ds_1e10=round(math.sqrt(1e-10 * 100) * 1e4, 2),
                              note="Criterion L^2/D_eff <= t_charge/3 with t=300 s, D_e=2.5e-6 cm2/s, eps=0.30, Bruggeman 1.5 [ASSUMPTION]")
    res["B_energy_vs_loading"] = {cid: {f"{q}": round(energy_at_loading(cid, q), 1) for q in (1.0, 1.5, round(qa_lim, 2), 2.5, 3.5, 5.0)} for cid in ("N01", "N02", "N08", "B01")}
    res["B_metal_anode"] = dict(required_mA_cm2_at_12C={f"{q} mAh/cm2": 12 * q for q in (2.0, 3.5, 5.0)},
                                typical_critical_current_density_mA_cm2="~1-10 at room temperature for Li/Na metal on inorganic solid electrolytes [ASSUMPTION; literature range]")
    # C
    res["C_three_dollar"] = [interpretations(cid) for cid in ("S01", "S03", "S04", "N01", "N02", "N03", "N09", "A01", "A03", "B02")]
    # D
    res["D_salt_routes"], res["D_seawater"] = salt_routes()
    json.dump(res, open(OUT / "s13b_targets.json", "w"), indent=1, default=str)
    report(res); plots(res)

def report(res):
    print("A. 1,500 km / 5 min")
    for x in res["A_vehicle"]:
        if x["vehicle"] in ("mid SUV", "heavy truck (40 t)"):
            print(f"  {x['pack_case'][:45]:45} {x['vehicle']:18} use {x['usable_kWh']:6.0f} kWh  batt {x['battery_mass_kg']:6.0f} kg  "
                  f"P {x['avg_charge_power_MW']:5.2f} MW  {x['avg_C_rate']:4.1f}C  {x['current_kA_at_800V']:4.1f} kA@800V  x{x['x_best_deployed']} best deployed")
    for h in res["A_heat_midSUV_founder_pack"]: print("  heat", h)
    print("B.", res["B_electrode"]); print("  energy vs loading", res["B_energy_vs_loading"])
    print("C. $3")
    for r in res["C_three_dollar"]:
        print(f"  {r['id']} thmin ${r['theoretical_min_material_usd_kWh']}/kWh  cell floor ${r['cell_cost_floor']}  I3 {r['I3_3usd_per_kg_cell']['verdict']} "
              f"(eq ${r['I3_3usd_per_kg_cell']['equivalent_usd_kWh']})  I4 <= {r['I4_3usd_per_unit']['max_unit_energy_Wh_at_floor']} Wh  "
              f"I6 LCOS ${r['I6_levelised']['lcos_floor_usd_per_kWh_delivered']}-{r['I6_levelised']['lcos_mid']}  3c: {r['I6_levelised']['as_3_cents_per_kWh_delivered']}")
    print("D.", *res["D_salt_routes"], sep="\n  ")

def plots(res):
    import plotstyle as ps; import matplotlib.pyplot as plt
    ps.apply()
    # $3 chart: cost floors vs $3 lines
    rows = res["C_three_dollar"]
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    x = np.arange(len(rows))
    ax.bar(x - 0.27, [r["theoretical_min_material_usd_kWh"] for r in rows], 0.27, color=ps.SERIES[2], label="theoretical minimum (reactants at feedstock price)")
    ax.bar(x, [r["cell_materials_P50"] for r in rows], 0.27, color=ps.SERIES[0], label="cell materials P50 (S12 build-up)")
    ax.bar(x + 0.27, [r["cell_cost_mid"] for r in rows], 0.27, color=ps.SERIES[1], label="cell cost mid (materials + conversion at 1 GWh)")
    ax.axhline(3, color=ps.STATUS["critical"], ls="--", lw=1.4); ax.text(-0.4, 3.5, "$3/kWh founder target [TARGET]", color=ps.STATUS["critical"], fontsize=8)
    ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels([r["id"] for r in rows]); ax.set_ylabel("USD per kWh (log)")
    ax.set_title("The $3 target vs theoretical minimum, materials and cell cost"); ax.legend(fontsize=7.5, loc="upper left")
    ps.save(fig, OUT / "s13b_three_dollar", "Theoretical minimum material cost, practical cell materials cost and cell cost at 1 GWh/yr versus the founder's $3/kWh target.",
            "[CALCULATED from ASSUMPTION prices]; target [TARGET]")
    # energy vs loading
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for i, (cid, d) in enumerate(res["B_energy_vs_loading"].items()):
        items = sorted((float(k), v) for k, v in d.items())
        ax.plot([q for q, _ in items], [v for _, v in items], "o-", color=ps.SERIES[i], label=f"{cid} {S12[cid]['name'][:34]}")
    ax.axvline(res["B_electrode"]["Qa_max_cell"], color=ps.STATUS["critical"], ls="--"); ax.text(res["B_electrode"]["Qa_max_cell"] + 0.05, 120, "5-min transport limit\n(liquid electrolyte)", fontsize=7.5, color=ps.STATUS["critical"])
    ax.axhline(360, color=ps.TEXT2, ls=":"); ax.set_xlabel("Areal capacity (mAh/cm²)"); ax.set_ylabel("Cell Wh/kg (P50)"); ax.legend(fontsize=7)
    ax.set_title("Thin electrodes for 5-minute charging cost energy density")
    ps.save(fig, OUT / "s13b_energy_vs_loading", "Cell specific energy versus electrode loading from the S12 build-up, with the electrolyte-transport limit for a 5-minute charge.",
            "[CALCULATED from ASSUMPTION]")

if __name__ == "__main__":
    main()
