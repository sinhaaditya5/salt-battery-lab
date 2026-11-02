"""S4 — Water window, side reactions, gas, water loss and vent requirement for the R1 monobloc.

Two independent side-reaction estimates:
  (a) coulombic-efficiency budget: side charge = (1-CE) x charge passed (literature CE range)
  (b) Tafel kinetics: i_side(E) = i0 * 10^(|E - E_eq(pH)| / b), with i0 calibrated so that a 1C cycle
      reproduces the CE budget, then used to predict float current and pH sensitivity.
Label: [CALC]/[SIM] from [ASSUMPTION] inputs — no electrode has been measured.
"""
import json, pathlib, sys
import numpy as np
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
from params.product_params import GAS, MAT, MONOBLOC, F, R1_CELL_V_MAX
from params.design import monobloc, cabinet
import plotstyle as ps
import matplotlib.pyplot as plt

OUT = pathlib.Path(__file__).parent / "out"; OUT.mkdir(exist_ok=True)
VM = 22.414          # L/mol at STP
R_ = 8.314; T = 298.15


def e_her(pH): return -0.0592 * pH
def e_oer(pH): return 1.229 - 0.0592 * pH


def ce_budget(ce, her_share, cap_Ah):
    """Gas, water and pressure per cell per full cycle from a CE budget."""
    q_side = (1 - ce) * cap_Ah * 3600.0                       # C per cycle
    n_e = q_side / F
    h2 = her_share * n_e / 2; o2 = (1 - her_share) * n_e / 4
    water_mol = her_share * n_e + (1 - her_share) * n_e / 2   # HER 1 H2O/e-, OER 0.5 H2O/e-
    return dict(H2_mL=h2 * VM * 1000, O2_mL=o2 * VM * 1000, gas_mL=(h2 + o2) * VM * 1000, water_g=water_mol * 18.015)


def main():
    mb = monobloc()
    cap = mb["cap_Ah"]
    es = mb["electrode"]
    # per-cell water inventory (electrolyte mass x water fraction of 1 M Na2SO4 ~ 0.873)
    elyte_g = es["electrolyte_mg_cm2"] * mb["repeats_per_cell"] * mb["plate_area_cm2"] / 1000.0 + mb["free_electrolyte_kg"] * 1000 / mb["n_cells"]
    water_g = elyte_g * (1 - 0.142 * MAT["electrolyte_molarity"].value / MAT["electrolyte_density"].value)
    headspace_L = MONOBLOC["headspace_mm"] * mb["compartment_mm"] * (MONOBLOC["width_mm"] - 2 * MONOBLOC["wall_mm"]) / 1e6
    res = {"label": "[CALC] from [ASSUMPTION] inputs (params GAS); not measured", "cell_capacity_Ah": cap,
           "cell_water_g": water_g, "cell_headspace_L": headspace_L, "ce_sweep": []}
    for ce in np.linspace(GAS["coulombic_eff"].lo, GAS["coulombic_eff"].hi, 9):
        b = ce_budget(ce, GAS["her_share"].value, cap)
        dp_kPa = b["gas_mL"] / 1000 / headspace_L * 101.325                  # isothermal, gas into fixed headspace
        cycles_20pct_water = 0.2 * water_g / b["water_g"]
        res["ce_sweep"].append({"CE": round(float(ce), 4), **{k: round(v, 3) for k, v in b.items()},
                                "gas_mL_per_Ah": round(b["gas_mL"] / cap, 3), "dP_kPa_per_cycle": round(dp_kPa, 2),
                                "cycles_between_vents": round(GAS["vent_open_kPa"] if False else MONOBLOC["vent_valve_open_kPa"].value / max(dp_kPa, 1e-9), 2),
                                "cycles_to_20pct_water_loss": round(cycles_20pct_water, 0)})
    nom = ce_budget(GAS["coulombic_eff"].value, GAS["her_share"].value, cap)
    res["nominal"] = {**nom, "CE": GAS["coulombic_eff"].value,
                      "cycles_to_20pct_water_loss": 0.2 * water_g / nom["water_g"],
                      "CE_needed_for_3000_cycles": 1 - (0.2 * water_g / 3000) / (cap * 3600 / F * (GAS["her_share"].value + (1 - GAS["her_share"].value) / 2) * 18.015)}
    # --- Tafel model calibrated to the nominal CE over a 1C cycle ------------------------
    pH = GAS["pH"].value
    b_h = GAS["tafel_HER_mV_dec"].value / 1000; b_o = GAS["tafel_OER_mV_dec"].value / 1000
    # electrode potentials over a 1C charge (linear sweep approximations, V vs SHE)
    soc = np.linspace(0, 1, 200)
    E_an = MAT["anode_avg_potential_SHE"].value + 0.03 - 0.12 * soc ** 4         # NTP: flat, dips at top of charge
    E_ca = MAT["cathode_avg_potential_SHE"].value - 0.45 + 0.9 * soc              # sloping birnessite
    eta_h = np.clip(e_her(pH) - E_an, 0, None); eta_o = np.clip(E_ca - e_oer(pH), 0, None)
    shape_h = 10 ** (eta_h / b_h); shape_o = 10 ** (eta_o / b_o)
    q_side_target = (1 - GAS["coulombic_eff"].value) * cap * 3600                 # C per cycle (charge half dominates)
    t_charge = 3600.0
    i0h = GAS["her_share"].value * q_side_target / (np.trapezoid(shape_h, soc) * t_charge)
    i0o = (1 - GAS["her_share"].value) * q_side_target / (np.trapezoid(shape_o, soc) * t_charge)
    # float: hold at float voltage -> top-of-charge potentials scaled to the float V
    frac = (GAS["float_V_per_cell"].value - 0.6) / (R1_CELL_V_MAX.value - 0.6)
    i_float = i0h * 10 ** (np.clip(e_her(pH) - np.interp(frac, soc, E_an), 0, None) / b_h) + \
              i0o * 10 ** (np.clip(np.interp(frac, soc, E_ca) - e_oer(pH), 0, None) / b_o)
    float_mA_per_Ah = i_float * 1000 / cap
    h2_float_L_year = i_float * GAS["her_share"].value / (2 * F) * 3.156e7 * VM
    res["tafel"] = {"i0_HER_A_cell": i0h, "i0_OER_A_cell": i0o, "float_current_mA_per_Ah": float_mA_per_Ah,
                    "float_gas_L_per_cell_year": h2_float_L_year,
                    "float_water_loss_pct_per_year": 100 * i_float / F * 3.156e7 * 18.015 * (GAS["her_share"].value + (1 - GAS["her_share"].value) / 2) / water_g}
    # pH sensitivity of side current at top of charge
    res["pH_sensitivity"] = []
    for p in np.linspace(5, 10, 11):
        eh = np.clip(e_her(p) - E_an[-1], 0, None); eo = np.clip(E_ca[-1] - e_oer(p), 0, None)
        res["pH_sensitivity"].append({"pH": round(float(p), 1), "i_side_rel": float((i0h * 10 ** (eh / b_h) + i0o * 10 ** (eo / b_o)) /
                                                                               (i0h * 10 ** (np.clip(e_her(pH) - E_an[-1], 0, None) / b_h) + i0o * 10 ** (np.clip(E_ca[-1] - e_oer(pH), 0, None) / b_o)))})
    # --- fault case: overcharge -> all current electrolyses water ------------------------
    I_fault = GAS["overcharge_fault_C"].value * cap
    h2_rate_Lmin = I_fault / (2 * F) * VM * 60
    o2_rate_Lmin = I_fault / (4 * F) * VM * 60
    res["fault"] = {"I_A": I_fault, "H2_L_per_min_per_cell": h2_rate_Lmin, "gas_L_per_min_per_cell": h2_rate_Lmin + o2_rate_Lmin,
                    "time_to_vent_s": MONOBLOC["vent_valve_open_kPa"].value / 101.325 * headspace_L / ((h2_rate_Lmin + o2_rate_Lmin) / 60),
                    "vent_min_flow_L_min": 2 * (h2_rate_Lmin + o2_rate_Lmin)}
    # cabinet ventilation to hold H2 < 1 % in the fault case (whole string overcharging) and in float
    cab = cabinet()
    n_cells_cab = cab["monoblocs"] * mb["n_cells"]
    for case, h2_L_min in (("fault", h2_rate_Lmin * n_cells_cab), ("float", h2_float_L_year / 525600 * n_cells_cab)):
        res.setdefault("ventilation", {})[case] = {"H2_L_per_min_cabinet": h2_L_min,
                                                   "air_m3_per_h_for_1pct": h2_L_min * 60 / 1000 / GAS["h2_limit_fraction"].value}
    (OUT / "s04_results.json").write_text(json.dumps(res, indent=1, default=float))
    charts(res, E_an, E_ca)
    n = res["nominal"]
    print(f"cell {cap:.1f} Ah, water {water_g:.0f} g, headspace {headspace_L*1000:.0f} mL")
    print(f"nominal CE {n['CE']}: gas {n['gas_mL']:.0f} mL/cell/cycle, water {n['water_g']:.3f} g/cycle -> 20% water loss after {n['cycles_to_20pct_water_loss']:.0f} cycles")
    print(f"CE needed for 3000 cycles before 20% water loss: {n['CE_needed_for_3000_cycles']:.5f}")
    print("tafel", {k: round(v, 4) for k, v in res["tafel"].items()})
    print("fault", {k: round(v, 3) for k, v in res["fault"].items()})
    print("ventilation", res["ventilation"])


def charts(res, E_an, E_ca):
    pH = np.linspace(0, 14, 50)
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.fill_between(pH, e_her(pH), e_oer(pH), color=ps.SEQ_BLUE[0], alpha=0.6, lw=0)
    ax.plot(pH, e_her(pH), color=ps.SERIES[0], lw=1.5); ax.plot(pH, e_oer(pH), color=ps.SERIES[7], lw=1.5)
    ax.text(1, e_her(1) - 0.12, "H$_2$ evolution below this line", fontsize=7.5, color=ps.TEXT2)
    ax.text(1, e_oer(1) + 0.05, "O$_2$ evolution above this line", fontsize=7.5, color=ps.TEXT2)
    pHop = GAS["pH"].value
    ax.add_patch(plt.Rectangle((pHop - 0.35, E_an.min()), 0.7, E_an.max() - E_an.min(), color=ps.SERIES[1], lw=0))
    ax.add_patch(plt.Rectangle((pHop + 0.6, E_ca.min()), 0.7, E_ca.max() - E_ca.min(), color=ps.SERIES[2], lw=0))
    ax.text(pHop - 0.5, E_an.min() - 0.08, "NTP anode", fontsize=7.5, ha="right", color=ps.TEXT2)
    ax.text(pHop + 1.5, E_ca.max() - 0.05, "birnessite cathode", fontsize=7.5, color=ps.TEXT2)
    ax.set_xlabel("pH"); ax.set_ylabel("Potential (V vs SHE)"); ax.set_xlim(0, 14); ax.set_ylim(-1.2, 1.6)
    ax.set_title("Water stability window and R1 electrode operating ranges")
    ps.note(ax, "Nernst lines at 25 °C; electrode bars at pH 7", "lower left")
    ps.save(fig, OUT / "s04_water_window",
            "Thermodynamic water window (1.23 V) vs pH, with the R1 anode and cathode potential ranges at pH 7: both ends rely on kinetic overpotential, so side reactions are expected.",
            "[LIT] Nernst equation; electrode ranges [ASSUMPTION] (params MAT)")
    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    ce = [r["CE"] * 100 for r in res["ce_sweep"]]; cyc = [r["cycles_to_20pct_water_loss"] for r in res["ce_sweep"]]
    ax.plot(ce, cyc, color=ps.SERIES[0], marker="o", markeredgecolor=ps.SURFACE, markeredgewidth=1.5)
    ax.axhline(3000, color=ps.DEEMPH, lw=1); ax.text(ce[0], 3150, "3,000-cycle target", fontsize=7.5, color=ps.TEXT2)
    ax.set_yscale("log"); ax.set_xlabel("Coulombic efficiency per cycle (%)"); ax.set_ylabel("Cycles to lose 20 % of cell water")
    ax.set_title("Sealed-cell life is set by side-reaction losses")
    ps.save(fig, OUT / "s04_water_loss_vs_CE",
            "Cycles until a sealed R1 cell loses 20 % of its electrolyte water, as a function of coulombic efficiency (side charge assumed to split water, no recombination).",
            "[CALC] from [ASSUMPTION] CE range 99.0–99.9 % and R1 design (params)")


if __name__ == "__main__":
    main()
