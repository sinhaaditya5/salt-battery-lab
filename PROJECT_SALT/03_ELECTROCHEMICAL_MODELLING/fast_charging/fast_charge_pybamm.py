#!/usr/bin/env python3
"""S13a - What does '5-minute charging' do to a real cell? PyBaMM DFN experiments.

Models (PyBaMM 26.10):
  * Chen2020  - LG M50 21700 NMC811|graphite-SiOx, DFN + lumped thermal. Parameterised and validated in
    Chen et al., J. Electrochem. Soc. 167, 080534 (2020). Used as the PHYSICS BENCHMARK, not as a salt cell.
  * OKane2022 - same cell + SEI growth, lithium plating (partially reversible), particle cracking, LAM.
    O'Kane et al., PCCP 24, 7909 (2022). Used to compare degradation per cycle at 1C vs fast charge.
  * Chayambuka2022 - Na-ion HC|NVPF DFN. FAILED our independent validation (S02: 67-121 mV MAE vs 60 mV gate);
    results are labelled TREND ONLY and never used as a performance claim.

Outputs: out/s13a_fast_charge.json, out/s13a_*.png/svg
Indicator of metal plating: eta_pl = phi_s,n - phi_e,n at the negative/separator interface (V vs Li/Li+ or Na/Na+);
eta_pl < 0 means metal deposition is thermodynamically favoured.
"""
from __future__ import annotations
import json, sys, time, warnings
from pathlib import Path
import numpy as np
import pybamm

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent; LAB = HERE.parents[1]; OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
RATES = [1, 2, 4, 6, 8, 10, 12]

def li_cc_charge(rate, h=100.0):
    """Chen2020 DFN, lumped thermal (h=100 W/m2K, active cooling), CC charge from fully discharged to 4.2 V,
    then CV hold at 4.2 V so the full 5-minute window is used."""
    model = pybamm.lithium_ion.DFN(options={"thermal": "lumped"})
    pv = pybamm.ParameterValues("Chen2020")
    pv.update({"Total heat transfer coefficient [W.m-2.K-1]": h}, check_already_exists=False)
    exp = pybamm.Experiment([f"Discharge at C/5 until 2.5 V", "Rest for 1 hour",
                             f"Charge at {rate}C until 4.2 V", "Hold at 4.2 V for 10 minutes"])
    sim = pybamm.Simulation(model, parameter_values=pv, experiment=exp)
    sol = sim.solve(calc_esoh=False)
    cc, cv = sol.cycles[2], sol.cycles[3]
    t_cc = cc["Time [s]"].entries
    tt = np.concatenate([t_cc, cv["Time [s]"].entries]); tt = tt - t_cc[0]
    class _S:  # stitch CC + CV
        def __getitem__(self, k):
            a, b = cc[k].entries, cv[k].entries
            return type("E", (), {"entries": np.concatenate([a, b], axis=-1)})()
    st = _S()
    t = tt
    Q = st["Discharge capacity [A.h]"].entries; Q = -(Q - Q[0])
    keep = t <= 300.0 + 1e-6; t, Q = t[keep], Q[keep]
    phis = st["Negative electrode potential [V]"].entries[-1, :][keep]  # last node of negative electrode (separator side)
    phie = st["Negative electrolyte potential [V]"].entries[-1, :][keep]
    eta = phis - phie
    T = st["X-averaged cell temperature [K]"].entries[keep] - 273.15
    nominal = pv["Nominal cell capacity [A.h]"]
    i5 = np.searchsorted(t, 300.0)
    onset = float(t[np.argmax(eta < 0)]) if (eta < 0).any() else None
    return dict(rate=rate, h_W_m2K=h, t_end_s=float(t[-1]), Q_end_Ah=float(Q[-1]), frac_nominal_end=float(Q[-1] / nominal),
                Q_at_5min_Ah=float(Q[min(i5, len(Q) - 1)]), frac_at_5min=float(Q[min(i5, len(Q) - 1)] / nominal),
                min_eta_plating_V=float(eta.min()), plating_onset_s=onset,
                frac_charged_before_plating=float(Q[np.argmax(eta < 0)] / nominal) if onset is not None else float(Q[-1] / nominal),
                T_max_C=float(T.max()), T_start_C=float(T[0]),
                curve=dict(t=t[::max(1, len(t)//200)].tolist(), V=st["Voltage [V]"].entries[keep][::max(1, len(t)//200)].tolist(),
                           eta=eta[::max(1, len(t)//200)].tolist()))

def li_cc_only(rate, h=100.0):
    """Fallback when the CV hold cannot converge: CC charge to 4.2 V only (records how fast the limit is hit)."""
    model = pybamm.lithium_ion.DFN(options={"thermal": "lumped"})
    pv = pybamm.ParameterValues("Chen2020")
    pv.update({"Total heat transfer coefficient [W.m-2.K-1]": h}, check_already_exists=False)
    exp = pybamm.Experiment([f"Discharge at C/5 until 2.5 V", "Rest for 1 hour", f"Charge at {rate}C until 4.2 V"])
    sol = pybamm.Simulation(model, parameter_values=pv, experiment=exp).solve(calc_esoh=False)
    st = sol.cycles[2]
    t = st["Time [s]"].entries; t = t - t[0]
    Q = st["Discharge capacity [A.h]"].entries; Q = -(Q - Q[0])
    eta = st["Negative electrode potential [V]"].entries[-1, :] - st["Negative electrolyte potential [V]"].entries[-1, :]
    T = st["X-averaged cell temperature [K]"].entries - 273.15
    nominal = pv["Nominal cell capacity [A.h]"]
    onset = float(t[np.argmax(eta < 0)]) if (eta < 0).any() else None
    return dict(rate=rate, h_W_m2K=h, mode="CC only (CV hold failed to converge: cell at 4.2 V within seconds)", t_end_s=float(t[-1]),
                Q_end_Ah=float(Q[-1]), frac_nominal_end=float(Q[-1] / nominal), Q_at_5min_Ah=float(Q[-1]), frac_at_5min=float(Q[-1] / nominal),
                min_eta_plating_V=float(eta.min()), plating_onset_s=onset,
                frac_charged_before_plating=float(Q[np.argmax(eta < 0)] / nominal) if onset is not None else float(Q[-1] / nominal),
                T_max_C=float(T.max()), T_start_C=float(T[0]))

def na_cc_charge(rate):
    """Chayambuka2022 Na-ion BasicDFN (isothermal). TREND ONLY (failed S02 validation)."""
    pv0 = pybamm.ParameterValues("Chayambuka2022"); I1C = pv0["Nominal cell capacity [A.h]"]
    try:
        m0 = pybamm.sodium_ion.BasicDFN(); pv0.update({"Current function [A]": I1C / 10})
        s0 = pybamm.Simulation(m0, parameter_values=pv0).solve([0, 40000])          # C/10 discharge to 2.0 V
        model = pybamm.sodium_ion.BasicDFN(); model.set_initial_conditions_from(s0)
        pv = pybamm.ParameterValues("Chayambuka2022"); pv.update({"Current function [A]": -rate * I1C})
        sol = pybamm.Simulation(model, parameter_values=pv).solve([0, 3600 / rate * 1.2])
    except Exception as e:  # noqa
        return dict(rate=rate, error=str(e)[:200])
    t = sol["Time [s]"].entries
    V = sol["Voltage [V]"].entries
    vmax = pv["Upper voltage cut-off [V]"]
    k = np.argmax(V >= vmax) if (V >= vmax).any() else len(V) - 1
    try:
        phis = sol["Negative electrode potential [V]"].entries[-1, :]; phie = sol["Negative electrolyte potential [V]"].entries[-1, :]
        eta = phis - phie; mineta = float(eta[:k + 1].min())
    except Exception:
        mineta = None
    Q = rate * I1C * t[k] / 3600
    return dict(rate=rate, t_to_Vmax_s=float(t[k]), Q_Ah=float(Q), frac_nominal=float(Q / I1C), min_eta_plating_V=mineta, label="TREND ONLY")

def okane_cycles(charge_rate, n=15):
    """OKane2022 degradation: n cycles of (charge at XC to 4.2 V, CV to C/20 capped) + 1C discharge. Returns LLI & plated Li."""
    model = pybamm.lithium_ion.DFN(options={"SEI": "solvent-diffusion limited", "SEI porosity change": "true",
                                            "lithium plating": "partially reversible", "lithium plating porosity change": "true",
                                            "particle mechanics": ("swelling and cracking", "swelling only"), "SEI on cracks": "true",
                                            "loss of active material": "stress-driven", "thermal": "lumped"})
    pv = pybamm.ParameterValues("OKane2022")
    cyc = [(f"Discharge at C/2 until 2.5 V", "Rest for 5 minutes", f"Charge at {charge_rate}C until 4.2 V", "Hold at 4.2 V until C/5", "Rest for 5 minutes")]
    exp = pybamm.Experiment(cyc * n)
    sim = pybamm.Simulation(model, parameter_values=pv, experiment=exp, solver=pybamm.IDAKLUSolver())
    t0 = time.time(); sol = sim.solve(calc_esoh=False); dt = time.time() - t0
    caps = [c.steps[0]["Discharge capacity [A.h]"].entries[-1] - c.steps[0]["Discharge capacity [A.h]"].entries[0] for c in sol.cycles if c is not None]
    lli = sol["Loss of lithium inventory [%]"].entries if "Loss of lithium inventory [%]" in sol.all_models[0].variables else None
    out = dict(charge_rate=charge_rate, n_cycles=len(caps), discharge_capacity_Ah=[float(x) for x in caps], wall_s=dt)
    try:
        out["LLI_pct_end"] = float(sol["Loss of lithium inventory [%]"].entries[-1])
        out["plated_Li_capacity_Ah_end"] = float(sol["Loss of capacity to negative lithium plating [A.h]"].entries[-1])
        out["SEI_loss_Ah_end"] = float(sol["Loss of capacity to negative SEI [A.h]"].entries[-1])
    except Exception as e:
        out["note"] = f"degradation variables unavailable: {e}"[:200]
    if len(caps) > 2:
        fade = (caps[1] - caps[-1]) / max(1, len(caps) - 2)
        out["fade_Ah_per_cycle"] = float(fade); out["fade_pct_per_cycle"] = float(100 * fade / caps[1])
        out["cycles_to_80pct_linear_extrapolation"] = float(0.2 * caps[1] / fade) if fade > 0 else None
    return out

def main():
    res = dict(li_benchmark=[], na_trend=[], degradation=[], notes=__doc__)
    for r in RATES:
        try: res["li_benchmark"].append(li_cc_charge(r))
        except Exception as e:
            try: res["li_benchmark"].append(li_cc_only(r) | {"cv_error": str(e)[:200]})
            except Exception as e2: res["li_benchmark"].append(dict(rate=r, error=str(e2)[:300]))
        print("Li", r, {k: v for k, v in res["li_benchmark"][-1].items() if k != "curve"}, flush=True)
    for r in RATES:
        res["na_trend"].append(na_cc_charge(r)); print("Na", res["na_trend"][-1], flush=True)
    json.dump(res, open(OUT / "s13a_fast_charge.json", "w"), indent=1)
    if "--no-degradation" not in sys.argv:
        for cr in (1, 3, 6):
            try: res["degradation"].append(okane_cycles(cr)); print("OKane", res["degradation"][-1], flush=True)
            except Exception as e: res["degradation"].append(dict(charge_rate=cr, error=str(e)[:300])); print("OKane", cr, "ERR", e, flush=True)
            json.dump(res, open(OUT / "s13a_fast_charge.json", "w"), indent=1)
    plot(res)

def plot(res):
    sys.path.insert(0, str(LAB / "tools")); import plotstyle as ps; import matplotlib.pyplot as plt
    ps.apply()
    ok = [r for r in res["li_benchmark"] if "error" not in r]
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    ax = axs[0]
    ax.plot([r["rate"] for r in ok], [100 * r["frac_at_5min"] for r in ok], "o-", color=ps.SERIES[0], label="charged in first 5 min (CC to 4.2 V, then CV)")
    ax.plot([r["rate"] for r in ok], [100 * r["frac_charged_before_plating"] for r in ok], "s-", color=ps.SERIES[1], label="charged before plating onset (η_pl < 0)")
    ax.axhline(80, color=ps.STATUS["critical"], ls="--", lw=1.2); ax.text(1, 82, "≈80% in 5 min needed for the founder's case [TARGET]", fontsize=7.5, color=ps.STATUS["critical"])
    ax.set_xlabel("Constant charge rate (C)"); ax.set_ylabel("% of nominal capacity"); ax.set_ylim(0, 105); ax.legend(fontsize=7.5, loc="lower left")
    ax.set_title("LG M50-class Li-ion DFN (Chen2020): charge vs plating")
    ax = axs[1]
    ax.plot([r["rate"] for r in ok], [r["T_max_C"] for r in ok], "o-", color=ps.SERIES[3])
    ax.set_xlabel("Constant charge rate (C)"); ax.set_ylabel("Max lumped cell temperature (°C), h = 100 W/m²K"); ax.set_title("Lumped thermal response")
    ps.save(fig, OUT / "s13a_fast_charge_benchmark", "PyBaMM DFN of a validated Li-ion benchmark cell under constant-current charge 1-12C: fraction charged in 5 min, fraction charged before the plating criterion is crossed, and peak temperature.",
            "[SIMULATED] benchmark Li-ion model (Chen2020); not a salt-battery result")

if __name__ == "__main__":
    if "--plot-only" in sys.argv: plot(json.load(open(OUT / "s13a_fast_charge.json")))
    else: main()
