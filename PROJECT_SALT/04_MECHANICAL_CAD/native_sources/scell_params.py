"""Single source of truth for the S-cell R0: a salt-assembled planar Na | beta''-alumina | NaAlCl4 | (Fe,Ni)Cl2 lab test cell.

Purpose (decision-relevant, not a product): falsify the cost lever found in S12 - beta''-alumina dominates cell cost, and
its mass per kWh scales as thickness / areal capacity. R0 measures capacity, ASR, coulombic efficiency and fade at
30 / 60 / 100 mAh/cm2 with a 1.0 mm (and later 0.5 mm) disc, first replicating the published 190 C Na-FeCl2 result (PS-005).

Every number is [ASSUMPTION] (design choice) unless a source ID is given. Consumers: cad/make_scell.py, pcb/scell_monitor
(firmware limits), PROJECT_SALT procurement BOM and build manual (tools/project_salt/*.py), tests/test_project_salt.py.
"""
from math import pi

F_AH = 26.801                       # Ah/mol e-
M = dict(NaCl=58.443, Fe=55.845, Ni=58.693, FeS=87.91, NaF=41.988, Al=26.982, NaI=149.894, AlCl3=133.34, NaAlCl4=191.78)

CELL = dict(
    name="S-cell R0 (salt-iron planar test cell)",
    disc_d_mm=30.0, disc_t_mm=1.0, disc_t_options_mm=(0.5, 1.0),       # beta''-alumina disc [ASSUMPTION; supplier-dependent]
    active_d_mm=24.0,                                                 # cathode/anode window
    ring_od_mm=42.0, ring_id_mm=26.0, ring_t_mm=4.0, ring_cbore_d_mm=30.4, ring_cbore_depth_mm=0.8,   # alpha-alumina ring
    glass_seal_t_mm=0.15,
    cup_od_mm=42.0, cup_wall_mm=3.0, cath_cup_depth_mm=6.0, anode_cup_depth_mm=6.0,
    flange_t_mm=5.0, bolt_n=6, bolt_size="M4", bolt_pcd_mm=50.0, flange_od_mm=60.0,
    mesh_t_mm=0.3, spring_free_mm=2.5, shim_t_mm=0.1,
    fill_tube_od_mm=3.18, fill_tube_id_mm=2.0, tc_well_od_mm=3.18,
    gasket_t_mm=0.5,
)
CELL["active_area_cm2"] = pi * (CELL["active_d_mm"] / 20) ** 2        # 4.52 cm2

# Cathode recipe per mAh/cm2 of areal capacity (discharged-state assembly) [ASSUMPTION; ZEBRA/PNNL practice, PS-005, PS-007]
RECIPE = dict(
    NaCl_utilisation=0.80,           # fraction of NaCl cycled
    Fe_excess=2.2,                   # total Fe / stoichiometric Fe for delivered capacity
    Ni_mol_frac_of_metal=0.10,       # 10 mol% Ni additive (PS-005)
    FeS_wt_frac=0.03, NaF_wt_frac=0.01, NaI_wt_frac=0.01, Al_wt_frac=0.02,   # additives (S, halide, priming Al)
    melt_vol_frac_of_bed=0.40,       # NaAlCl4 fills granule-bed porosity
    granule_bed_density=1.9,         # g/cm3 tapped granule bed (before melt) [ASSUMPTION]
    melt_density=1.65,               # g/cm3 NaAlCl4 at ~200 C [ASSUMPTION; literature ~1.6-1.7]
)
LOADINGS_mAh_cm2 = (30, 60, 100)

def cathode_charge(qa_mAh_cm2: float):
    """Grams of each cathode ingredient for one S-cell at areal capacity qa (mAh/cm2)."""
    A = CELL["active_area_cm2"]; Q_Ah = qa_mAh_cm2 * A / 1000.0
    r = RECIPE
    nacl = Q_Ah / F_AH * M["NaCl"] / r["NaCl_utilisation"]
    metal_mol = Q_Ah / F_AH / 2 * r["Fe_excess"]
    ni = metal_mol * r["Ni_mol_frac_of_metal"] * M["Ni"]; fe = metal_mol * (1 - r["Ni_mol_frac_of_metal"]) * M["Fe"]
    base = nacl + fe + ni
    adds = {k: base * r[f"{k}_wt_frac"] for k in ("FeS", "NaF", "NaI", "Al")}
    bed = base + sum(adds.values())
    bed_vol = bed / r["granule_bed_density"]
    melt = bed_vol * r["melt_vol_frac_of_bed"] * r["melt_density"]
    thick_mm = bed_vol / A * 10
    return dict(Q_mAh=Q_Ah * 1000, NaCl_g=nacl, Fe_g=fe, Ni_g=ni, **{f"{k}_g": v for k, v in adds.items()},
                granules_g=bed, NaAlCl4_g=melt, cathode_thickness_mm=thick_mm,
                AlCl3_for_melt_g=melt * M["AlCl3"] / M["NaAlCl4"], NaCl_for_melt_g=melt * M["NaCl"] / M["NaAlCl4"])

# Operating window [ASSUMPTION grounded in PUBLISHED ZEBRA chemistry; overcharge 3.05 V / overdischarge 1.58 V reactions]
OPERATE = dict(
    T_set_C=190.0, T_range_C=(180.0, 260.0), T_warn_C=270.0, T_trip_C=290.0,       # hardware trip independent of MCU
    T_ramp_C_per_min=2.0,                                                          # protect ceramic and glass seal
    V_charge_max=2.75, V_discharge_min=1.80, V_trip_high=2.95, V_trip_low=1.65,    # trips sit inside 3.05 V / 1.58 V side reactions
    I_max_mA_cm2=40.0, I_test_mA_cm2=(5.0, 10.0, 20.0, 33.3),
    formation=dict(first_charge_mA_cm2=2.0, cycles=3),
    cell_series_max=4,                                                             # SCM-1 board handles up to 4 cells in series
)
# Acceptance / kill criteria for the R0 campaign [TARGET]
GATES = dict(
    G1_replication="Fe-rich cathode delivers >=100 mAh/g(cathode) at 10 mA/cm2, 190 C (PS-005 reports 116 mAh/g at 33.3 mA/cm2)",
    G2_loading="At 60 mAh/cm2: >=80% NaCl utilisation at 10 mA/cm2 and ASR <=4 ohm.cm2 over 0-80% DoD",
    G3_CE="Coulombic efficiency >=99.9% (mean, cycles 10-100) - required for >=3000-cycle life",
    G4_cost_lever="beta''-alumina mass <= 1.0 kg/kWh at the passing loading (disc t / areal capacity) -> ceramic <= $60/kWh at $60/kg",
    G5_seal="Zero leak (He leak rate <1e-8 mbar.L/s) after 20 thermal cycles 25<->190 C",
)
