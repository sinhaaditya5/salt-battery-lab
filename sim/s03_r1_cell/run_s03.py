"""S3 — R1 cell electrochemical model (PyBaMM sodium DFN, literature parameter ranges).

Outputs (out/): s03_results.json, discharge curves, rate retention vs loading with Monte Carlo
P10-P90 bands, round-trip energy efficiency. Label: [SIM] PyBaMM DFN, parameters = literature
ranges, NOT validated for this chemistry (S2: voltages carry >= +/-0.1 V without measured kinetics).
"""
import json, pathlib, sys, time, warnings
warnings.filterwarnings("ignore")
from multiprocessing import Pool
import numpy as np
import pybamm
pybamm.set_logging_level("ERROR")
HERE = pathlib.Path(__file__).parent
LAB = HERE.parents[1]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
import r1_parameters as R
from params.product_params import R1_LOADING, MAT, R0_LOADING_MG_CM2

OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
LOADINGS = [round(R0_LOADING_MG_CM2, 2), 10.0, 25.0, 40.0, 60.0, 80.0]
RATES = [0.1, 0.2, 1.0, 4.0]          # C/10 reference, C/5 telecom, 1C, 4C = 15-minute UPS
N_MC = 40
DESIGN = R1_LOADING["cathode_mg_cm2_per_side"].value


def discharge(loading, crate, s=None, extra=None, curve=False):
    pv, cap = R.build(loading, s, **(extra or {}))
    pv["Current function [A]"] = cap * crate
    try:
        sol = pybamm.Simulation(pybamm.sodium_ion.BasicDFN(), parameter_values=pv).solve(
            np.linspace(0, 3600 / crate * 1.4, 400))
        q = sol["Discharge capacity [A.h]"].entries; v = sol["Voltage [V]"].entries
        e = float(np.trapezoid(v, q))
        out = {"Ah": float(q[-1]), "Wh": e, "Vavg": e / q[-1] if q[-1] > 0 else float("nan")}
        if curve:
            out["q"] = q.tolist(); out["v"] = v.tolist()
        return out
    except Exception as ex:
        return {"Ah": float("nan"), "Wh": float("nan"), "Vavg": float("nan"), "err": str(ex)[:120]}


def sample(rng):
    s = {}
    for k, (lo, hi, nom) in R.RANGES.items():
        if k in ("kappa", "D_e", "t_plus"):
            s[k] = float(rng.uniform(lo, hi))
        else:
            s[k] = float(np.exp(rng.uniform(np.log(lo), np.log(hi))))
    extra = {"cap_c": float(rng.uniform(MAT["cathode_capacity"].lo, MAT["cathode_capacity"].hi)),
             "porosity": float(rng.uniform(MAT["electrode_porosity"].lo, MAT["electrode_porosity"].hi))}
    return s, extra


def mc_task(args):
    loading, seed = args
    rng = np.random.default_rng(seed)
    s, extra = sample(rng)
    ref = discharge(loading, 0.1, s, extra)
    row = {"loading": loading, "seed": seed, "s": s, "extra": extra, "ref_Ah": ref["Ah"]}
    for c in RATES[1:]:
        r = discharge(loading, c, s, extra)
        row[f"ret_{c}"] = r["Ah"] / ref["Ah"] if ref["Ah"] == ref["Ah"] else float("nan")
        row[f"Vavg_{c}"] = r["Vavg"]
    return row


def round_trip(loading, crate):
    pv, cap = R.build(loading)
    exp = pybamm.Experiment([f"Discharge at {crate}C until 0.6 V", "Rest for 30 minutes",
                             f"Charge at {crate}C until 1.75 V", "Rest for 30 minutes",
                             f"Discharge at {crate}C until 0.6 V"])
    sol = pybamm.Simulation(pybamm.sodium_ion.BasicDFN(), parameter_values=pv, experiment=exp).solve()
    def energy(step):
        t = step["Time [s]"].entries; i = step["Current [A]"].entries; v = step["Voltage [V]"].entries
        return float(np.trapezoid(np.abs(i) * v, t) / 3600)
    cyc = sol.cycles  # each experiment string is its own cycle in PyBaMM
    e_ch, e_dis = energy(cyc[2].steps[0]), energy(cyc[4].steps[0])
    return {"E_charge_Wh": e_ch, "E_discharge_Wh": e_dis, "round_trip_eff": e_dis / e_ch}


def main():
    t0 = time.time()
    res = {"label": "[SIM] PyBaMM sodium BasicDFN with R1 literature-range parameters; not validated (see S2)",
           "loadings_mg_cm2": LOADINGS, "rates_C": RATES, "design_loading": DESIGN, "nominal": {}, "mc": {}, "round_trip": {}}
    # nominal curves
    for L in LOADINGS:
        res["nominal"][str(L)] = {str(c): discharge(L, c, curve=(L in (DESIGN, LOADINGS[0]))) for c in RATES}
    # Monte Carlo
    tasks = [(L, 1000 + i) for L in LOADINGS for i in range(N_MC)]
    with Pool(5) as p:
        rows = p.map(mc_task, tasks, chunksize=4)
    (OUT / "s03_mc_samples.json").write_text(json.dumps(rows))
    for L in LOADINGS:
        rr = [r for r in rows if r["loading"] == L]
        res["mc"][str(L)] = {}
        for c in RATES[1:]:
            x = np.array([r[f"ret_{c}"] for r in rr], float); x = x[np.isfinite(x)]
            res["mc"][str(L)][str(c)] = {"n": int(len(x)), "p10": float(np.percentile(x, 10)), "p50": float(np.percentile(x, 50)),
                                         "p90": float(np.percentile(x, 90))}
    for c in (0.2, 1.0, 4.0):
        try:
            res["round_trip"][str(c)] = round_trip(DESIGN, c)
        except Exception as ex:
            res["round_trip"][str(c)] = {"error": str(ex)[:200]}
    res["runtime_s"] = round(time.time() - t0, 1)
    (OUT / "s03_results.json").write_text(json.dumps(res, indent=1))
    charts(res)
    d = res["mc"][str(DESIGN)]
    print(f"design {DESIGN} mg/cm2: 4C retention P10/P50/P90 = {d['4.0']['p10']:.2f}/{d['4.0']['p50']:.2f}/{d['4.0']['p90']:.2f}")
    print("round trip", {k: round(v.get('round_trip_eff', float('nan')), 3) for k, v in res["round_trip"].items()})
    print("runtime", res["runtime_s"], "s")


def charts(res):
    import plotstyle as ps
    import matplotlib.pyplot as plt
    # 1) discharge curves at the design loading
    fig, ax = plt.subplots(figsize=(6.0, 3.9))
    nom = res["nominal"][str(DESIGN)]
    labels = {0.1: "C/10", 0.2: "C/5 (telecom)", 1.0: "1C", 4.0: "4C (15-min UPS)"}
    for i, c in enumerate(RATES):
        d = nom[str(c)]
        if "q" in d:
            q = np.array(d["q"]); ax.plot(q / nom["0.1"]["Ah"] * 100, d["v"], color=ps.SERIES[i], label=labels[c])
    ax.set_xlabel("Capacity (% of C/10 capacity)"); ax.set_ylabel("Cell voltage (V)")
    ax.set_title(f"R1 cell discharge at {DESIGN:.0f} mg/cm² cathode loading (simulated)")
    ax.set_xlim(0, 105); ax.set_ylim(0.5, 1.8); ax.legend(loc="lower left")
    ps.note(ax, "PyBaMM DFN, nominal literature parameters", "upper right")
    ps.save(fig, OUT / "s03_discharge_curves",
            "Simulated R1 (Na-birnessite // NaTi2(PO4)3, 1 M Na2SO4) discharge curves at the design loading for four rates.",
            "[SIM] PyBaMM DFN, literature-range parameters, not validated for this chemistry (S2); voltage uncertainty >= ±0.1 V")
    # 2) retention vs loading with MC band
    fig, ax = plt.subplots(figsize=(6.0, 3.9))
    for i, c in enumerate([0.2, 1.0, 4.0]):
        xs = res["loadings_mg_cm2"]
        p10 = [res["mc"][str(L)][str(c)]["p10"] * 100 for L in xs]
        p50 = [res["mc"][str(L)][str(c)]["p50"] * 100 for L in xs]
        p90 = [res["mc"][str(L)][str(c)]["p90"] * 100 for L in xs]
        col = ps.SERIES[[1, 2, 3][i]]
        ax.fill_between(xs, p10, p90, color=col, alpha=0.12, lw=0)
        ax.plot(xs, p50, color=col, marker="o", markeredgecolor=ps.SURFACE, markeredgewidth=1.5, label=labels[c])
    ax.axvline(res["loadings_mg_cm2"][0], color=ps.DEEMPH, lw=1); ax.text(res["loadings_mg_cm2"][0] + 1, 55, "R0 paper\n2.8 mg/cm²", fontsize=7.2, color=ps.TEXT2)
    ax.axvline(DESIGN, color=ps.DEEMPH, lw=1); ax.text(DESIGN + 1, 55, "R1 design\npoint", fontsize=7.2, color=ps.TEXT2)
    ax.set_xlabel("Cathode loading per side (mg/cm²)"); ax.set_ylabel("Capacity retained vs C/10 (%)")
    ax.set_ylim(0, 105); ax.set_title("Rate capability vs electrode loading (Monte Carlo P10–P90)")
    ax.legend(loc="lower left")
    ps.save(fig, OUT / "s03_retention_vs_loading",
            f"Capacity retained at C/5, 1C and 4C relative to C/10 as cathode loading rises from the paper's 2.8 mg/cm² to 80 mg/cm²; bands are P10–P90 of {N_MC} Monte Carlo samples per loading.",
            "[SIM] PyBaMM DFN with literature parameter ranges (diffusivity, particle size, kinetics, conductivity, capacity, porosity); not validated")


if __name__ == "__main__":
    main()
