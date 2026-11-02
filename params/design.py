"""Derived R1 geometry, mass, volume and energy, from params/product_params.py only.

Every downstream tool (S3, S7, S9, CAD, drawings, PCB ratings, docs) calls these functions,
so a change to an input propagates everywhere. Results are [CALC] from [ASSUMPTION]/[TARGET] inputs.
"""
from __future__ import annotations
import math
from params.product_params import MAT, R1_LOADING, MONOBLOC, R1_CELL_VOLTAGE_NOM, MODULE48, CABINET


def _v(x, key="value"):
    return x.value if hasattr(x, "value") else x


def electrode_stack(loading_c=None, mat=None):
    """Return per-repeat-unit data for one cathode/anode pair (double-sided electrodes)."""
    m = {k: _v(v) for k, v in (mat or MAT).items()}
    Lc = loading_c if loading_c is not None else R1_LOADING["cathode_mg_cm2_per_side"].value
    qc, qa = m["cathode_capacity"], m["anode_capacity"]
    La = Lc * qc * m["np_ratio"] / qa                      # anode active loading per side (mg/cm2)
    af, por = m["active_fraction"], m["electrode_porosity"]
    # electrode coating thickness per side: solid volume / (1-porosity); carbon+binder ~1.9 g/cm3
    def thick_um(L_act, rho_act):
        mass_total = L_act / af                            # mg/cm2
        v_act = L_act / rho_act; v_inert = (mass_total - L_act) / 1.9
        return (v_act + v_inert) / (1 - por) * 10.0        # mg/cm2 / (g/cm3) = 1e-3 cm = 10 um
    tc, ta = thick_um(Lc, m["cathode_density"]), thick_um(La, m["anode_density"])
    cc = m["cc_thickness_um"]; sep = m["separator_thickness_um"]
    # repeat unit = cathode(2 sides)+cc + anode(2 sides)+cc + 2 separators
    t_rep = 2 * tc + cc + 2 * ta + cc + 2 * sep           # um
    pore_v = (2 * tc + 2 * ta) * 1e-4 * por + 2 * sep * 1e-4 * m["separator_porosity"]   # cm3 per cm2 of plate
    elyte_mass = pore_v * m["electrolyte_excess"] * m["electrolyte_density"] * 1e3        # mg/cm2
    mass = (2 * Lc / af + 2 * La / af + 2 * cc * 1e-4 * m["cc_density"] * 1e3
            + 2 * m["separator_areal_mass"] + elyte_mass)                                 # mg per cm2 plate area
    cap_mAh_cm2 = 2 * Lc * qc / 1000.0                                                     # per cm2 of plate (both sides)
    return dict(cathode_loading=Lc, anode_loading=La, cathode_thick_um=tc, anode_thick_um=ta,
                repeat_thick_um=t_rep, repeat_mass_mg_cm2=mass, cap_mAh_cm2=cap_mAh_cm2,
                electrolyte_mg_cm2=elyte_mass)


def monobloc(loading_c=None, mat=None):
    mb = MONOBLOC
    n = mb["cells_in_series"]
    L_int = mb["length_mm"] - 2 * mb["wall_mm"] - (n - 1) * mb["partition_mm"]
    comp = L_int / n                                        # cell compartment depth (mm)
    plate_w = mb["width_mm"] - 2 * mb["wall_mm"] - 2 * mb["plate_margin_mm"]
    plate_h = mb["height_mm"] - mb["base_mm"] - mb["lid_mm"] - mb["headspace_mm"] - mb["plate_margin_mm"]
    area_cm2 = plate_w * plate_h / 100.0
    es = electrode_stack(loading_c, mat)
    usable = comp - 2.0                                      # 1 mm clearance each side
    n_rep = max(1, int(usable * 1000 // es["repeat_thick_um"]))
    cap_Ah = n_rep * area_cm2 * es["cap_mAh_cm2"] / 1000.0
    m = {k: _v(v) for k, v in (mat or MAT).items()}
    v_cell = m["cathode_avg_potential_SHE"] - m["anode_avg_potential_SHE"]
    energy_Wh = n * v_cell * cap_Ah
    stack_mass_kg = n * n_rep * area_cm2 * es["repeat_mass_mg_cm2"] / 1e6
    # case: walls+partitions+lid+base, PP-GF density
    L, W, H = mb["length_mm"], mb["width_mm"], mb["height_mm"]
    shell_cm3 = (L * W * H - (L - 2 * mb["wall_mm"]) * (W - 2 * mb["wall_mm"]) * (H - mb["base_mm"] - mb["lid_mm"])) / 1000.0
    part_cm3 = (n - 1) * mb["partition_mm"] * (W - 2 * mb["wall_mm"]) * (H - mb["base_mm"] - mb["lid_mm"]) / 1000.0
    case_kg = (shell_cm3 + part_cm3) * mb["case_density_g_cm3"] / 1000.0
    # free electrolyte reservoir in headspace region is zero (valve-regulated, starved); busbars/terminals/valve
    hardware_kg = 0.35 + n * 0.04
    # electrolyte that fills compartment volume not occupied by plates (flooded margin), 30 % of free volume
    comp_free_cm3 = n * (comp * (W - 2 * mb["wall_mm"]) * (plate_h + mb["plate_margin_mm"]) / 1000.0
                         - n_rep * es["repeat_thick_um"] * 1e-4 * area_cm2)
    free_elyte_kg = max(0.0, comp_free_cm3) * 0.30 * m["electrolyte_density"] / 1000.0
    total_kg = stack_mass_kg + case_kg + hardware_kg + free_elyte_kg
    vol_L = L * W * H / 1e6
    return dict(n_cells=n, compartment_mm=comp, plate_w_mm=plate_w, plate_h_mm=plate_h, plate_area_cm2=area_cm2,
                repeats_per_cell=n_rep, cap_Ah=cap_Ah, v_cell_nom=v_cell, v_nom=n * v_cell, energy_Wh=energy_Wh,
                stack_kg=stack_mass_kg, case_kg=case_kg, hardware_kg=hardware_kg, free_electrolyte_kg=free_elyte_kg,
                mass_kg=total_kg, volume_L=vol_L, Wh_per_kg=energy_Wh / total_kg, Wh_per_L=energy_Wh / vol_L,
                cell_Wh_per_kg_stack_only=energy_Wh / stack_mass_kg, electrode=es)


def module48(loading_c=None):
    mb = monobloc(loading_c)
    n = MODULE48["monoblocs"]
    tray_kg, bms_dcdc_kg = 6.0, 2.5
    e = n * mb["energy_Wh"] * MODULE48["dcdc_efficiency"].value
    mass = n * mb["mass_kg"] + tray_kg + bms_dcdc_kg
    L, W, H = MODULE48["tray_mm"]
    return dict(energy_Wh=e, mass_kg=mass, volume_L=L * W * H / 1e6, Wh_per_kg=e / mass, Wh_per_L=e / (L * W * H / 1e6))


def cabinet(loading_c=None):
    mb = monobloc(loading_c)
    n = CABINET["shelves"] * CABINET["monoblocs_per_shelf"]
    frame_kg, bms_kg = 140.0, 8.0
    e = n * mb["energy_Wh"]
    mass = n * mb["mass_kg"] + frame_kg + bms_kg
    vol = CABINET["width_mm"] * CABINET["depth_mm"] * CABINET["height_mm"] / 1e6
    return dict(monoblocs=n, energy_kWh=e / 1000, mass_kg=mass, volume_L=vol, Wh_per_kg=e / mass, Wh_per_L=e / vol,
                string_V=n * mb["v_nom"])


if __name__ == "__main__":
    import json
    out = monobloc()
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in out.items() if k != "electrode"}, indent=1))
    print(json.dumps({k: round(v, 2) for k, v in out["electrode"].items()}, indent=1))
    print("module48", {k: round(v, 2) for k, v in module48().items()})
    print("cabinet", {k: round(v, 2) for k, v in cabinet().items()})
