"""PyBaMM parameter set for the R1 aqueous cell (Na-birnessite // NaTi2(PO4)3-C, 1 M Na2SO4).

Built on the Chayambuka2022 sodium-ion template (S2) with every R1-specific value from
params/product_params.py (MAT) or an explicit literature range below. Potentials are expressed vs
Na+/Na (= vs SHE + 2.71 V) so the PyBaMM sodium DFN can be reused; only the cell voltage matters.

Known approximations (state them wherever results are used):
* Na2SO4 is a 2:1 salt; the DFN's binary 1:1 concentrated-solution electrolyte is an approximation.
* OCP curves are assumed shapes (sloping birnessite, flat NTP plateau), not measured curves.
* Kinetic/transport values are literature ranges; S2 showed voltages carry >= +/-0.1 V without measured kinetics.
"""
from __future__ import annotations
import math, sys
import numpy as np
import pybamm
sys.path.insert(0, "/Volumes/Aditya ssd/Salt-Battery-Lab")
from params.product_params import MAT, F
from params.design import electrode_stack

SHE_TO_NA = 2.71
RT_F = 8.314 * 298.15 / F

# Literature ranges for transport/kinetics (log-uniform in Monte Carlo)
RANGES = {
    "D_p": (1e-16, 1e-14, 1e-15),      # m2/s birnessite (layered MnO2, nano) — 1e-12..1e-10 cm2/s
    "D_n": (1e-16, 1e-14, 1e-15),      # m2/s carbon-coated NTP
    "r_p": (0.2e-6, 2.0e-6, 0.5e-6),   # m secondary-particle radius
    "r_n": (0.1e-6, 1.0e-6, 0.3e-6),
    "j0_p": (0.5, 20.0, 2.0),          # A/m2 at mid-SOC, 1 M
    "j0_n": (0.5, 20.0, 2.0),
    "kappa": (4.0, 5.5, 4.8),          # S/m, 0.5 M Na2SO4 (D-05)
    "D_e": (0.9e-9, 1.25e-9, 1.1e-9),  # m2/s Na2SO4 salt diffusivity
    "t_plus": (0.36, 0.42, 0.39),      # Na+ transference in Na2SO4
}


def ocp_cathode(sto, Emid=None, span=0.9):
    """Sloping Na-birnessite OCP vs Na+/Na; decreases as Na is inserted (sto up)."""
    Emid = (MAT["cathode_avg_potential_SHE"].value if Emid is None else Emid) + SHE_TO_NA
    return Emid + span * (0.5 - sto) + 0.6 * RT_F * pybamm.log((1 - sto) / sto)


def ocp_anode(sto, E0=None):
    """Flat NTP plateau vs Na+/Na with Nernstian ends; decreases as Na is inserted (sto up)."""
    E0 = (MAT["anode_avg_potential_SHE"].value if E0 is None else E0) + SHE_TO_NA
    return E0 + 0.04 * (0.5 - sto) + 0.5 * RT_F * pybamm.log((1 - sto) / sto)


def cmax(capacity_mAh_g, density, window=0.8):
    vol_cap = capacity_mAh_g * density            # mAh/cm3
    return vol_cap * 3.6 / F * 1e6 / window       # mol/m3 (usable window -> full lattice)


def build(loading_c=None, s=None, cap_c=None, cap_a=None, porosity=None):
    """Return pybamm.ParameterValues for one R1 cell, 1 m2 electrode area (single-sided repeat)."""
    s = {k: v[2] for k, v in RANGES.items()} | (s or {})
    es = electrode_stack(loading_c)
    cap_c = cap_c or MAT["cathode_capacity"].value
    cap_a = cap_a or MAT["anode_capacity"].value
    por = porosity or MAT["electrode_porosity"].value
    af = MAT["active_fraction"].value
    # active-material volume fractions consistent with params.design thickness model
    def eps_s(L_act, rho, t_um):
        return (L_act / rho) * 10.0 / t_um
    eps_p = eps_s(es["cathode_loading"], MAT["cathode_density"].value, es["cathode_thick_um"])
    eps_n = eps_s(es["anode_loading"], MAT["anode_density"].value, es["anode_thick_um"])
    cmp_ = cmax(cap_c, MAT["cathode_density"].value)
    cmn_ = cmax(cap_a, MAT["anode_density"].value)
    pv = pybamm.ParameterValues("Chayambuka2022")
    area = 1.0
    cap_Ah = es["cathode_loading"] * cap_c / 1000.0 * 1e4 / 1000.0 * area   # mAh/cm2 * 1e4 cm2 -> Ah (one side)
    c_e0 = MAT["electrolyte_molarity"].value * 1000.0
    j0p, j0n = s["j0_p"], s["j0_n"]

    def j0_pos(c_e, c_s_surf, c_s_max, T):
        x = c_s_surf / c_s_max
        return j0p * (c_e / c_e0) ** 0.5 * (4 * x * (1 - x)) ** 0.5

    def j0_neg(c_e, c_s_surf, c_s_max, T):
        x = c_s_surf / c_s_max
        return j0n * (c_e / c_e0) ** 0.5 * (4 * x * (1 - x)) ** 0.5

    kap, De = s["kappa"], s["D_e"]
    pv.update({
        "Negative electrode thickness [m]": es["anode_thick_um"] * 1e-6,
        "Positive electrode thickness [m]": es["cathode_thick_um"] * 1e-6,
        "Separator thickness [m]": MAT["separator_thickness_um"].value * 1e-6,
        "Electrode height [m]": 1.0, "Electrode width [m]": area,
        "Nominal cell capacity [A.h]": cap_Ah, "Current function [A]": cap_Ah,
        "Negative electrode porosity": por, "Positive electrode porosity": por,
        "Separator porosity": MAT["separator_porosity"].value,
        "Negative electrode active material volume fraction": eps_n,
        "Positive electrode active material volume fraction": eps_p,
        "Negative particle radius [m]": s["r_n"], "Positive particle radius [m]": s["r_p"],
        "Negative particle diffusivity [m2.s-1]": s["D_n"], "Positive particle diffusivity [m2.s-1]": s["D_p"],
        "Maximum concentration in negative electrode [mol.m-3]": cmn_,
        "Maximum concentration in positive electrode [mol.m-3]": cmp_,
        "Negative electrode OCP [V]": ocp_anode, "Positive electrode OCP [V]": ocp_cathode,
        "Negative electrode exchange-current density [A.m-2]": j0_neg,
        "Positive electrode exchange-current density [A.m-2]": j0_pos,
        "Negative electrode conductivity [S.m-1]": 50.0, "Positive electrode conductivity [S.m-1]": 10.0,
        "Initial concentration in electrolyte [mol.m-3]": c_e0,
        "Electrolyte conductivity [S.m-1]": lambda c_e, T: kap * (c_e / c_e0) ** 0.8,
        "Electrolyte diffusivity [m2.s-1]": lambda c_e, T: De + 0 * c_e,
        "Cation transference number": s["t_plus"],
        "Lower voltage cut-off [V]": 0.60, "Upper voltage cut-off [V]": 1.75,
        "Open-circuit voltage at 0% SOC [V]": 0.60, "Open-circuit voltage at 100% SOC [V]": 1.75,
        # charged state: anode sodiated (high sto), cathode desodiated (low sto); window 0.1..0.9 used
        "Initial concentration in negative electrode [mol.m-3]": 0.9 * cmn_ / MAT["np_ratio"].value * 1.0,
        "Initial concentration in positive electrode [mol.m-3]": 0.1 * cmp_,
        "Contact resistance [Ohm]": 0.0,
    })
    return pv, cap_Ah
