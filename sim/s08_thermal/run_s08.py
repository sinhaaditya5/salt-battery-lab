"""S8 — Thermal and abuse model for the R1 monobloc and UPS cabinet.

1. Lumped monobloc model at 0.25C, 1C, 2C and the 4C (15-minute) UPS discharge: heat from S3 overpotential.
2. 2-D finite-difference cross-section of one monobloc (length x height, 10 cells, partitions, walls)
   with natural convection, 15-minute UPS discharge and continuous 1C cycling.
3. Abuse energy balance: stored electrical energy vs water's sensible + latent heat sink; the Li-ion
   runaway chain step by step and what replaces each step in an aqueous cell.
4. Remaining hazards register (gas, leakage, Mn2+, freezing/crystallisation, plastic case fire load).
Label: [CALC]/[SIM] from [ASSUMPTION] inputs; no abuse test has been done.
"""
import json, pathlib, sys
import numpy as np
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
from params.product_params import MONOBLOC, MAT
from params.design import monobloc
import plotstyle as ps
import matplotlib.pyplot as plt

OUT = pathlib.Path(__file__).parent / "out"; OUT.mkdir(exist_ok=True)
CP = {"water_electrolyte": 3.9, "active_oxide": 0.75, "carbon_binder": 1.0, "steel": 0.5, "pp_case": 1.9}   # J/g/K [LIT handbook typical]
H_CONV = 6.0           # W/m2/K natural convection + radiation, enclosed rack [ASSUMPTION 4-10]
LATENT_WATER = 2257.0  # J/g [LIT]
PP_HEAT_OF_COMBUSTION = 44.0  # MJ/kg polypropylene [LIT]


def s3_overpotential(crate):
    """Average (OCV-ish C/10 voltage minus voltage at rate) from S3 nominal at the design loading."""
    p = LAB / "sim/s03_r1_cell/out/s03_results.json"
    if p.exists():
        r = json.loads(p.read_text()); key = str(r["design_loading"])
        nom = r["nominal"][key]
        v_ref = nom["0.1"]["Vavg"]
        rates = sorted(float(k) for k in nom)
        vv = [nom[str(k) if str(k) in nom else repr(k)]["Vavg"] for k in rates]
        return float(v_ref - np.interp(crate, rates, vv))
    return 0.05 * crate          # fallback: 50 mV per C (flagged in output)


def lumped():
    mb = monobloc(); es = mb["electrode"]
    n_cells = mb["n_cells"]
    # heat capacity by component (J/K)
    stack_area = mb["repeats_per_cell"] * mb["plate_area_cm2"] * n_cells       # cm2 of repeat units
    elyte_g = es["electrolyte_mg_cm2"] * stack_area / 1000 + mb["free_electrolyte_kg"] * 1000
    active_g = 2 * (es["cathode_loading"] + es["anode_loading"]) * stack_area / 1000
    inert_g = active_g / MAT["active_fraction"].value - active_g
    steel_g = 2 * MAT["cc_thickness_um"].value * 1e-4 * MAT["cc_density"].value * stack_area
    C = (elyte_g * CP["water_electrolyte"] + active_g * CP["active_oxide"] + inert_g * CP["carbon_binder"]
         + steel_g * CP["steel"] + mb["case_kg"] * 1000 * CP["pp_case"])
    L, W, H = MONOBLOC["length_mm"] / 1000, MONOBLOC["width_mm"] / 1000, MONOBLOC["height_mm"] / 1000
    area = 2 * (L * W + L * H + W * H) * 0.6            # ~60 % exposed when racked side by side
    rows = []
    for c in (0.25, 1.0, 2.0, 4.0):
        I = c * mb["cap_Ah"]; dv = s3_overpotential(c) * n_cells
        q = I * dv                                        # W per monobloc
        t_dis = 3600 / c
        dT_adiabatic = q * t_dis / C
        tau = C / (H_CONV * area)
        dT_15min_or_full = q / (H_CONV * area) * (1 - np.exp(-t_dis / tau))
        rows.append({"C_rate": c, "current_A": I, "heat_W": q, "discharge_s": t_dis, "dT_adiabatic_K": dT_adiabatic,
                     "dT_with_convection_K": dT_15min_or_full, "steady_state_cycling_dT_K": q / (H_CONV * area)})
    return {"heat_capacity_J_K": C, "electrolyte_g": elyte_g, "exposed_area_m2": area, "tau_s": C / (H_CONV * area),
            "overpotential_source": "S3 nominal" if (LAB / "sim/s03_r1_cell/out/s03_results.json").exists() else "fallback 50 mV/C",
            "rates": rows}


def fd2d(q_total_W, t_end_s, nx=66, nz=44):
    """2-D transient conduction in a monobloc cross-section (x along 330 mm, z up 220 mm)."""
    L, H = MONOBLOC["length_mm"] / 1000, MONOBLOC["height_mm"] / 1000
    W = MONOBLOC["width_mm"] / 1000
    dx, dz = L / nx, H / nz
    x = (np.arange(nx) + 0.5) * dx; z = (np.arange(nz) + 0.5) * dz
    X, Z = np.meshgrid(x, z, indexing="ij")
    # materials: stack region (anisotropic: cross-plane k low, in-plane higher), walls/partitions PP, headspace gas
    k_stack_x, k_stack_z, k_pp, k_gas = 0.9, 3.0, 0.22, 0.03      # W/m/K [ASSUMPTION]
    rho_cp_stack, rho_cp_pp, rho_cp_gas = 2.6e6, 1.9e6, 1.2e3      # J/m3/K
    wall = MONOBLOC["wall_mm"] / 1000; part = MONOBLOC["partition_mm"] / 1000
    comp = (L - 2 * wall - 9 * part) / 10
    top_of_plates = H - MONOBLOC["lid_mm"] / 1000 - MONOBLOC["headspace_mm"] / 1000
    is_pp = (X < wall) | (X > L - wall) | (Z < MONOBLOC["base_mm"] / 1000) | (Z > H - MONOBLOC["lid_mm"] / 1000)
    for i in range(1, 10):
        x0 = wall + i * comp + (i - 1) * part
        is_pp |= (X >= x0) & (X < x0 + part)
    is_gas = (~is_pp) & (Z > top_of_plates)
    is_stack = (~is_pp) & (~is_gas)
    kx = np.where(is_stack, k_stack_x, np.where(is_pp, k_pp, k_gas))
    kz = np.where(is_stack, k_stack_z, np.where(is_pp, k_pp, k_gas))
    rc = np.where(is_stack, rho_cp_stack, np.where(is_pp, rho_cp_pp, rho_cp_gas))
    qv = np.where(is_stack, q_total_W / (is_stack.sum() * dx * dz * W), 0.0)    # W/m3
    T = np.zeros((nx, nz))
    dt = 0.2 * min(dx, dz) ** 2 * rc.min() / max(kx.max(), kz.max())
    dt = min(dt, 0.5)
    nsteps = int(t_end_s / dt)
    hist = []
    for n in range(nsteps):
        Tp = np.pad(T, 1, mode="edge")
        # convective boundaries: apply via ghost cells T_ghost = T - (h dx / k) T  (ambient 0)
        Tp[0, 1:-1] = T[0] * (1 - H_CONV * dx / k_pp); Tp[-1, 1:-1] = T[-1] * (1 - H_CONV * dx / k_pp)
        Tp[1:-1, 0] = T[:, 0] * (1 - H_CONV * dz / k_pp); Tp[1:-1, -1] = T[:, -1] * (1 - H_CONV * dz / k_pp)
        lap = (kx * (Tp[2:, 1:-1] - 2 * T + Tp[:-2, 1:-1]) / dx ** 2 + kz * (Tp[1:-1, 2:] - 2 * T + Tp[1:-1, :-2]) / dz ** 2)
        T = T + dt * (lap + qv) / rc
        if n % max(1, nsteps // 60) == 0:
            hist.append((n * dt, float(T.max()), float(T[is_stack].mean())))
    return T, X, Z, hist, is_stack


def abuse(mb):
    E_J = mb["energy_Wh"] * 3600
    elyte_g = mb["electrode"]["electrolyte_mg_cm2"] * mb["repeats_per_cell"] * mb["plate_area_cm2"] * mb["n_cells"] / 1000 + mb["free_electrolyte_kg"] * 1000
    water_g = elyte_g * 0.93
    C = lumped()["heat_capacity_J_K"]
    return {"stored_electrical_energy_MJ": E_J / 1e6,
            "adiabatic_rise_if_all_energy_released_K": E_J / C,
            "water_g": water_g,
            "heat_to_reach_100C_from_25C_MJ": C * 75 / 1e6,
            "latent_heat_of_all_water_MJ": water_g * LATENT_WATER / 1e6,
            "fraction_water_boiled_if_all_energy_released_after_100C": max(0.0, (E_J - C * 75) / (water_g * LATENT_WATER)),
            "case_fire_load_MJ": mb["case_kg"] * PP_HEAT_OF_COMBUSTION,
            "case_fire_load_vs_stored_energy": mb["case_kg"] * PP_HEAT_OF_COMBUSTION / (E_J / 1e6),
            "note": "The polypropylene case is combustible in an external fire; specify flame-retardant (UL 94 V-0) PP."}


RUNAWAY_CHAIN = [
    ("SEI decomposition (~80-120 C)", "No SEI in an aqueous Na2SO4 cell", "removed"),
    ("Anode-electrolyte reaction, exothermic", "NTP is an oxide; no lithiated graphite + organic solvent", "removed"),
    ("Separator melt -> internal short (~130-165 C)", "Water boils at ~101 C first and clamps temperature while liquid remains", "mitigated (internal shorts still possible from dendrite-free mechanical damage)"),
    ("Cathode O2 release (NMC ~200 C; LFP much higher)", "MnO2-type oxides lose O2 only at ~500 C+, endothermically", "removed in the credible range"),
    ("Electrolyte combustion (flammable carbonates)", "Electrolyte is water + Na2SO4: non-combustible", "removed"),
    ("Remaining: hydrogen from side reactions or overcharge", "H2 is flammable (LFL 4 %); needs vent + ventilation (S4)", "REMAINS"),
    ("Remaining: plastic case + binder/carbon in an external fire", "Case fire load is larger than the stored electrical energy", "REMAINS"),
    ("Remaining: electrolyte leakage (conductive, Mn2+ traces)", "Short-circuit path on busbars/floor; wastewater handling", "REMAINS"),
    ("Remaining: Mn2+ dissolution / capacity fade", "Performance, not fire, hazard; water-quality limits on disposal", "REMAINS"),
    ("Remaining: freezing / salt crystallisation", "0.5 M Na2SO4 saturates near 5 C; water freezes below ~ -2 C", "REMAINS (operating limit)"),
]


def main():
    mb = monobloc()
    lm = lumped()
    ups = [r for r in lm["rates"] if r["C_rate"] == 4.0][0]
    T, X, Z, hist, is_stack = fd2d(ups["heat_W"], 900.0)
    T1, X1, Z1, hist1, _ = fd2d([r for r in lm["rates"] if r["C_rate"] == 1.0][0]["heat_W"], 3 * 3600.0, nx=44, nz=30)
    res = {"label": "[SIM] lumped + 2-D conduction model; [CALC] abuse energy balance; inputs [ASSUMPTION]",
           "lumped": lm, "fd2d_ups_15min": {"max_dT_K": float(T.max()), "mean_stack_dT_K": float(T[is_stack].mean())},
           "fd2d_1C_3h": {"max_dT_K": float(T1.max())}, "abuse": abuse(mb),
           "runaway_chain": [{"li_ion_step": a, "aqueous_R1": b, "status": c} for a, b, c in RUNAWAY_CHAIN]}
    (OUT / "s08_results.json").write_text(json.dumps(res, indent=1, default=float))
    # chart: 2-D field at end of 15-minute UPS discharge
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    im = ax.pcolormesh(X * 1000, Z * 1000, T, cmap=plt.matplotlib.colors.LinearSegmentedColormap.from_list("b", ps.SEQ_BLUE), shading="auto")
    cb = fig.colorbar(im, ax=ax, label="Temperature rise (K)")
    cb.outline.set_visible(False)
    ax.set_xlabel("Along monobloc length (mm, 10 cells)"); ax.set_ylabel("Height (mm)")
    ax.set_title(f"Monobloc after a 15-minute UPS discharge: max rise {T.max():.1f} K")
    ax.set_aspect("equal"); ax.grid(False)
    ps.save(fig, OUT / "s08_monobloc_ups_temperature",
            "Simulated temperature rise across a 12 V R1 monobloc cross-section at the end of a 15-minute (4C) UPS discharge, natural convection in a rack.",
            "[SIM] 2-D finite-difference conduction; heat from S3 overpotential [SIM]; thermal properties [ASSUMPTION]")
    # chart: abuse energy budget
    ab = res["abuse"]
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    labels = ["Stored electrical\nenergy", "Heat to reach\n100 °C", "Boil all\nelectrolyte water", "PP case\nfire load"]
    vals = [ab["stored_electrical_energy_MJ"], ab["heat_to_reach_100C_from_25C_MJ"], ab["latent_heat_of_all_water_MJ"], ab["case_fire_load_MJ"]]
    cols = [ps.SERIES[1], ps.SERIES[0], ps.SERIES[0], ps.SERIES[7]]
    ax.barh(labels, vals, color=cols, height=0.5)
    for i, v in enumerate(vals):
        ax.text(v + 1.5, i, f"{v:.1f} MJ", va="center", fontsize=8, color=ps.TEXT2)
    ax.invert_yaxis(); ax.set_xlabel("Energy per 12 V monobloc (MJ)")
    ax.set_title("Abuse energy budget: water is a heat sink, the case is the fuel")
    ax.set_xlim(0, max(vals) * 1.25)
    ps.save(fig, OUT / "s08_abuse_energy_budget",
            "Energy balance for one R1 monobloc: even if all stored electrical energy became heat, the water's sensible and latent heat absorb it; the plastic case is the main combustible.",
            "[CALC] handbook heat capacities, latent heat and PP heat of combustion [LIT]; design masses [CALC]")
    print(json.dumps({"UPS_4C": {k: round(v, 2) for k, v in ups.items()}, "fd2d_ups_maxdT": round(T.max(), 2),
                      "fd2d_1C_3h_maxdT": round(T1.max(), 2), "abuse": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in ab.items()}}, indent=1))


if __name__ == "__main__":
    main()
