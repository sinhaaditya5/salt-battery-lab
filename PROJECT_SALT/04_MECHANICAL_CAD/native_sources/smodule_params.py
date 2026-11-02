"""Single source of truth for the salt-iron PRODUCT concepts (engineering designs D3-D5, 3 Nov 2026):

  D3  P1 planar product cell + SM-48T 48 V telecom/edge backup module (7U, 19-inch)
  D4  SM-48T thermal-management architecture (hot box, heaters, insulation, cooling bypass)  -> sim/s16_module_thermal
  D5  SC-UPS-1 floor cabinet (3 x SM-48T, controller, DC breaker, service access, mounting)

CONCEPT ONLY. Nothing here has been built or measured. The P1 cell scales the S-cell R0 stack (params/scell_params.py)
from a 30 mm disc to a 150 mm square plate; whether a 150 mm, 1.0 mm beta''-alumina plate can be made, sealed and
survive thermal cycling is unknown (gate G5 is on a 30 mm disc). Every number is [ASSUMPTION] unless tagged otherwise.

Why telecom/edge (2-8 h) and NOT a 15-minute data-centre UPS: the R0 operating limit is 40 mA/cm2 [ASSUMPTION, OPERATE];
at 60 mAh/cm2 that is C/1.5, i.e. >= 1.5 h discharge. A 15-minute UPS needs 4C = 240 mA/cm2 - 6x the limit [CALCULATED].
"""
from math import pi
from params.scell_params import CELL as R0, OPERATE, cathode_charge

# ---------------------------------------------------------------- P1 planar product cell [ASSUMPTION]
P1 = dict(
    name="P1 planar salt-iron cell (concept)",
    plate_mm=150.0, plate_t_mm=1.0,                 # square beta''-alumina plate (R0: 30 mm disc, 1.0 mm)
    active_mm=140.0,                                # square active window
    frame_w_mm=8.0, frame_t_mm=4.0,                 # alpha-alumina seal frame (R0: ring)
    can_wall_mm=0.5,                                # Ni 201 (cathode) / SS 316L (anode) drawn sheet cans
    anode_gap_mm=3.0,                               # Na reservoir + SS wick
    spring_gap_mm=1.3,                              # Mo collector + wave spring
    qa_mAh_cm2=60.0,                                # areal capacity (R0 gate G2 loading)
    V_nom=2.30, V_max=OPERATE["V_charge_max"], V_min=2.00,   # 2.00 V/cell product cut-off (R0 test limit 1.80 V)
    j_max_mA_cm2=OPERATE["I_max_mA_cm2"],
    tab_w_mm=20.0, tab_t_mm=1.0, tab_l_mm=12.0,
)
P1["outer_mm"] = P1["plate_mm"] + 2 * (P1["frame_w_mm"] - 3.0) + 2 * P1["can_wall_mm"]        # 161 mm square
P1["active_cm2"] = (P1["active_mm"] / 10) ** 2                                               # 196 cm2
_ch = cathode_charge(P1["qa_mAh_cm2"])                                                        # per R0 cell (4.52 cm2)
P1["cathode_t_mm"] = _ch["cathode_thickness_mm"]                                              # same per-area thickness
P1["thickness_mm"] = (2 * P1["can_wall_mm"] + P1["anode_gap_mm"] + P1["plate_t_mm"] + P1["cathode_t_mm"] + P1["spring_gap_mm"])
P1["Ah"] = P1["qa_mAh_cm2"] * P1["active_cm2"] / 1000.0
P1["Wh"] = P1["Ah"] * P1["V_nom"]
P1["I_max_A"] = P1["j_max_mA_cm2"] * P1["active_cm2"] / 1000.0
_scale = P1["active_cm2"] / R0["active_area_cm2"]
P1["granules_g"] = _ch["granules_g"] * _scale
P1["NaAlCl4_g"] = _ch["NaAlCl4_g"] * _scale

# ---------------------------------------------------------------- D3 SM-48T module [ASSUMPTION]
MODULE = dict(
    name="SM-48T 48 V salt-iron telecom/edge backup module (concept)",
    series=21, parallel=4,                           # 21S: 57.8 V max (SELV < 60 V), 48.3 V nominal, 42.0 V cut-off
    stacks=4, stack_pitch_mm=2.0,                    # one 21-cell column per parallel string; 2 mm mica/heater-sheet spacer
    stack_gap_mm=12.0,                               # between columns (busbars, sense wiring)
    inner_wall_mm=1.0,                               # SS 304 inner hot can
    insulation_mm=40.0,                              # evacuated double-wall panel with microporous core (k_eff below)
    outer_wall_mm=1.2,                               # powder-coated steel outer case
    front_bay_mm=70.0,                               # cold electronics bay (BMS, contactor, fuse, connectors)
    rack_width_mm=482.6, rack_u=7, u_mm=44.45,       # 19-inch, 7U
    depth_mm=620.0,
    heater_W=600.0,                                  # 4 x 150 W mica plate heaters (one per column wall)
    fan_cfm=20.0,                                    # cooling-bypass fan (abuse / fast discharge only)
    fuse_A=125, contactor_A=150,
)
MODULE["cells"] = MODULE["series"] * MODULE["parallel"]
MODULE["V_nom"] = MODULE["series"] * P1["V_nom"]
MODULE["V_max"] = MODULE["series"] * P1["V_max"]
MODULE["V_min"] = MODULE["series"] * P1["V_min"]
MODULE["Ah"] = MODULE["parallel"] * P1["Ah"]
MODULE["kWh"] = MODULE["V_nom"] * MODULE["Ah"] / 1000.0
MODULE["I_max_A"] = MODULE["parallel"] * P1["I_max_A"]
MODULE["P_max_kW"] = MODULE["I_max_A"] * MODULE["V_min"] / 1000.0
MODULE["height_mm"] = MODULE["rack_u"] * MODULE["u_mm"] - 0.8

# ---------------------------------------------------------------- D4 thermal [ASSUMPTION unless tagged]
THERMAL = dict(
    T_op_C=OPERATE["T_set_C"], T_amb_C=(25.0, 45.0),          # indoor shelter; Indian telecom shelters reach 45 C
    k_microporous_W_mK=0.025,                                 # microporous silica board at ~200 C mean [ASSUMPTION; vendor range 0.02-0.03]
    k_vacuum_panel_W_mK=0.005,                                # evacuated SS double wall + microporous core [ASSUMPTION; ZEBRA-type]
    bridge_factor=1.30,                                       # +30 % for feedthroughs, busbars, supports [ASSUMPTION]
    cp_cell_J_gK=0.75, cp_steel_J_gK=0.50,                   # lumped heat capacities [ASSUMPTION]
    melt_latent_J_g=150.0, melt_T_C=157.0,                    # NaAlCl4 fusion [ASSUMPTION; literature order of magnitude, verify]
    ramp_C_min=OPERATE["T_ramp_C_per_min"],
    heat_frac_at_jmax=0.04,                                   # heat / energy at 40 mA/cm2 (S14 model trend) [SIMULATED, approx]
    grid_price_usd_kWh=0.10,
)

# ---------------------------------------------------------------- D5 SC-UPS-1 cabinet [ASSUMPTION]
CABINET = dict(
    name="SC-UPS-1 salt-iron backup cabinet (concept)",
    modules=3, width_mm=600.0, depth_mm=800.0, height_mm=1400.0, rack_u=26,
    plinth_mm=100.0, frame_mm=40.0, panel_mm=1.5,
    controller_u=2, breaker_u=2, vent_u=1,
    door_open_deg=100.0,
)
CABINET["kWh"] = CABINET["modules"] * MODULE["kWh"]

if __name__ == "__main__":
    import json
    print(json.dumps(dict(P1={k: (round(v, 3) if isinstance(v, float) else v) for k, v in P1.items()},
                          MODULE={k: (round(v, 3) if isinstance(v, float) else v) for k, v in MODULE.items()},
                          CABINET_kWh=round(CABINET["kWh"], 2)), indent=1))
