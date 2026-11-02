#!/usr/bin/env python3
"""S14 - Chemistry-specific 0-D electrochemical-thermal model of the S-cell (Na | beta''-alumina | NaAlCl4 | Fe/Ni-NaCl).

NOT a lithium-ion model. Physics (standard ZEBRA description, e.g. Sudworth & Galloway; Coetzer patents PS-008/PS-009):
  * Two-phase conversion plateaus: Fe/FeCl2 (E0 ~2.35 V) then Ni/NiCl2 (E0 ~2.58 V) for the 10 mol% Ni share.
    The Na6FeCl8 intermediate seen in some Fe cells is NOT modelled (known gap).
  * Resistance = beta''-alumina (Arrhenius) + cathode reaction-front term (ionic path through NaAlCl4 in the pores grows
    with depth of discharge; the front starts at the ceramic and moves into the bed) + lumped charge transfer.
  * Heat = I^2 R (+ small entropic term ignored); thermal balance not needed in a furnace-held lab cell, reported as W/cm2.
Inputs are literature-range [ASSUMPTION]s; the model is UNVALIDATED until the R0 campaign (gates G1/G2) produces data.
Outputs: out/s14_results.json, out/s14_*.png/svg
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent; LAB = HERE.parents[1]; OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
from params.scell_params import CELL, OPERATE, RECIPE, cathode_charge  # noqa: E402

K_B = 8.617e-5
P = dict(sigma_base_300C=(0.10, 0.20, 0.30), Ea_base_eV=0.17,      # S/cm at 300 C; polycrystalline beta'' range [ASSUMPTION]
         sigma_melt_200C=(0.20, 0.30, 0.40), eps_melt=0.40, brugg=1.5,  # NaAlCl4 [ASSUMPTION]
         R_ct_ohm_cm2=(0.3, 0.6, 1.0), E_Fe=2.35, E_Ni=2.58, ni_cap_frac=RECIPE["Ni_mol_frac_of_metal"])

def asr(T_C, t_mm, qa, dod, sig_base300=0.20, sig_melt=0.30, rct=0.6):
    T = T_C + 273.15
    sb = sig_base300 * math.exp(-P["Ea_base_eV"] / K_B * (1 / T - 1 / 573.15))
    r_base = (t_mm / 10) / sb
    L = cathode_charge(qa)["cathode_thickness_mm"] / 10                     # cm
    r_cath = dod * L / (sig_melt * P["eps_melt"] ** P["brugg"])
    return r_base + r_cath + rct, r_base, r_cath

def ocv(soc):
    """soc = fraction of capacity charged. Ni plateau occupies the top ni_cap_frac of charge."""
    return P["E_Ni"] if soc > 1 - P["ni_cap_frac"] else P["E_Fe"]

def run(mode, j_mA_cm2, qa, T_C=190.0, t_mm=1.0, **kw):
    """Galvanostatic discharge (from full) or charge (from empty) to the voltage limit. Returns curve + metrics."""
    dt_frac = 0.002; out = []
    soc = 1.0 if mode == "dis" else 0.0
    q = 0.0; E = 0.0; heat = 0.0
    while True:
        dod = 1 - soc
        R, rb, rc = asr(T_C, t_mm, qa, dod if mode == "dis" else dod, **kw)  # front position follows reacted fraction
        eta = j_mA_cm2 / 1000 * R
        V = ocv(soc) - eta if mode == "dis" else ocv(min(soc + 1e-9, 1)) + eta
        if mode == "dis" and (V < OPERATE["V_discharge_min"] or soc <= 0): break
        if mode == "chg" and (V > OPERATE["V_charge_max"] or soc >= 1): break
        out.append((q, V, R))
        dq = dt_frac * qa; q += dq; E += V * dq; heat += eta * dq
        soc += -dt_frac if mode == "dis" else dt_frac
    return dict(mode=mode, j=j_mA_cm2, qa=qa, T_C=T_C, t_mm=t_mm, cap_mAh_cm2=q, utilisation=q / qa, Wh_cm2=E / 1000,
                heat_frac=heat / max(E, 1e-9), C_rate=j_mA_cm2 / qa, curve=out[::5])

def main():
    res = dict(params=P, runs=[], fast_charge={}, notes=__doc__)
    for qa in (30, 60, 100):
        for j in OPERATE["I_test_mA_cm2"]:
            for mode in ("dis", "chg"):
                r = run(mode, j, qa); r.pop("curve") if qa != 60 else None; res["runs"].append(r)
    # round-trip efficiency at 10 mA/cm2, 60 mAh/cm2
    d = run("dis", 10, 60); c = run("chg", 10, 60); res["RTE_60_10"] = d["Wh_cm2"] / max(c["Wh_cm2"], 1e-9)
    # 5-minute charge: 12C at 60 mAh/cm2 -> 720 mA/cm2
    for qa in (30, 60, 100):
        R0, rb, rc = asr(190, 1.0, qa, 0.5)
        j12 = 12 * qa
        res["fast_charge"][str(qa)] = dict(j_required_mA_cm2=j12, overpotential_V=round(j12 / 1000 * R0, 2),
                                           cell_V_needed=round(P["E_Fe"] + j12 / 1000 * R0, 2), overcharge_reaction_V=3.05,
                                           max_C_within_0p4V=round(0.4 / R0 * 1000 / qa, 2), ASR_mid_ohm_cm2=round(R0, 2))
    # sensitivity of ASR (50% DoD, 60 mAh/cm2) to temperature and disc thickness
    res["asr_map"] = {f"{T}C_{t}mm": round(asr(T, t, 60, 0.5)[0], 2) for T in (190, 230, 270, 300) for t in (0.5, 1.0, 1.5)}
    json.dump(res, open(OUT / "s14_results.json", "w"), indent=1, default=float)
    import plotstyle as ps; import matplotlib.pyplot as plt
    ps.apply(); fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    for i, j in enumerate(OPERATE["I_test_mA_cm2"]):
        for mode, ls in (("dis", "-"), ("chg", "--")):
            r = run(mode, j, 60); cv = np.array(r["curve"])
            axs[0].plot(cv[:, 0], cv[:, 1], ls, color=ps.SERIES[i], label=f"{j} mA/cm² ({r['C_rate']:.2f}C) {mode}")
    axs[0].axhline(OPERATE["V_charge_max"], color=ps.TEXT2, lw=0.8, ls=":"); axs[0].axhline(OPERATE["V_discharge_min"], color=ps.TEXT2, lw=0.8, ls=":")
    axs[0].set_xlabel("Capacity (mAh/cm²), 60 mAh/cm² cathode, 190 °C, 1.0 mm disc"); axs[0].set_ylabel("Cell voltage (V)"); axs[0].legend(fontsize=6.5)
    axs[0].set_title("S-cell model: discharge (—) / charge (--)")
    qs = [30, 60, 100]; caps = {j: [run("dis", j, q)["utilisation"] * 100 for q in qs] for j in OPERATE["I_test_mA_cm2"]}
    for i, j in enumerate(caps): axs[1].plot(qs, caps[j], "o-", color=ps.SERIES[i], label=f"{j} mA/cm²")
    axs[1].set_xlabel("Areal capacity (mAh/cm²)"); axs[1].set_ylabel("Utilisation to 1.8 V (%)"); axs[1].legend(fontsize=7)
    axs[1].set_title("Gate G2 needs ≥80% at 60 mAh/cm², 10 mA/cm²")
    axs[1].set_ylim(0, 108); axs[1].ticklabel_format(axis="y", useOffset=False); axs[1].axhline(80, color=ps.TEXT2, lw=0.8, ls=":")
    axs[1].text(65, 40, "Model predicts 100 % everywhere:\nonly an ohmic reaction-front loss,\nno transport / NaCl-morphology limit.\nIt CANNOT test G2 — only R0 can.",
                ha="center", va="center", fontsize=7.5, color=ps.TEXT2, bbox=dict(fc="white", ec=ps.GRID))
    ps.save(fig, OUT / "s14_scell_curves", "Chemistry-specific 0-D model of the salt-iron planar cell: voltage curves and utilisation vs loading and current density.",
            "[SIMULATED] unvalidated model with [ASSUMPTION] literature-range parameters")
    for k, v in res["fast_charge"].items(): print("5-min charge @", k, "mAh/cm2:", v)
    print("RTE 60/10:", round(res["RTE_60_10"], 3)); print("ASR map:", res["asr_map"])
    for r in res["runs"]:
        if r["qa"] == 60: print(r["mode"], r["j"], "util", round(r["utilisation"], 3), "C", round(r["C_rate"], 2))

if __name__ == "__main__":
    main()
