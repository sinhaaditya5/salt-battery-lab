"""S2 — Validation of the electrochemical model before trusting any aqueous model.

Question: does PyBaMM's sodium-ion DFN (pybamm.sodium_ion.BasicDFN + Chayambuka2022 parameters)
reproduce the published HC//NVPF discharge curves at 1, 5, 10 and 12 A/m2?

Reference data: experimental symbols of Fig. 4a in Chayambuka et al., Electrochim. Acta 404, 139764
(2022), digitised here by colour segmentation of the published raster figure (ref/). The paper's own
P2D model reached mean absolute voltage errors of 19.9 / 34.6 / 32.2 / 48.1 mV (Table 1).

Acceptance (set before running): per-rate mean absolute error (MAE) <= 60 mV and end-of-discharge
capacity within 5 % of the last experimental point, at every rate.
The paper adds a current-collector contact resistance (R_n 2 + R_p 8.5 mOhm m2, Table A1); PyBaMM's
parameter set ships with 0. We run both and report both.
"""
import json, pathlib, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
from PIL import Image
from scipy import ndimage
import pybamm

LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
import plotstyle as ps
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
FIG = HERE / "ref" / "fig4_p6_0_Im7.jpg"
RATES = {1: "#ff00ff", 5: "#22dd22", 10: "#1010cc", 12: "#22ddee"}   # figure colours (magenta, green, blue, cyan)
PAPER_MAE_MV = {1: 19.9, 5: 34.6, 10: 32.2, 12: 48.1}
R_CONTACT = 2e-3 + 8.5e-3   # Ohm m2, Chayambuka 2022 Table A1
AREA = 2.54e-4              # m2 (parameter set: height x width)

# Panel (a) axis calibration in image pixels (x: 0 and 3 mAh ticks; y: 2.0 and 4.0 V ticks)
X0_PX, X3_PX = 152.0, 1208.0
Y2_PX, Y4_PX = 488.0, 136.0
PANEL_A = (slice(100, 500), slice(140, 1225))


def digitise():
    img = np.asarray(Image.open(FIG).convert("RGB")).astype(float)
    sub = img[PANEL_A]
    pts = {}
    for rate, hexc in RATES.items():
        c = np.array([int(hexc[i:i + 2], 16) for i in (1, 3, 5)], float)
        dist = np.sqrt(((sub - c) ** 2).sum(-1))
        mask = dist < 95
        # remove 2-3 px lines, keep ~12 px symbols
        mask = ndimage.binary_opening(mask, structure=np.ones((7, 7)))
        lab, n = ndimage.label(mask)
        cents = ndimage.center_of_mass(mask, lab, range(1, n + 1))
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        xy = []
        for (r, ccol), s in zip(cents, sizes):
            if s < 25:
                continue
            xpx = ccol + PANEL_A[1].start; ypx = r + PANEL_A[0].start
            q = 3.0 * (xpx - X0_PX) / (X3_PX - X0_PX)
            v = 2.0 + 2.0 * (Y2_PX - ypx) / (Y2_PX - Y4_PX)
            if 0.18 < q < 0.35 and 2.85 < v < 3.1:
                continue  # legend line segment, not data
            if 0 <= q <= 3.0 and 2.0 <= v <= 4.3:
                xy.append((q, v))
        pts[rate] = sorted(xy)
    return pts


def simulate(j, k_factor=1.0):
    """k_factor = sqrt(c_e0) restores the paper's Eq. 6 units (c_e un-normalised, k in m^2.5 mol^-1.5 s^-1)."""
    model = pybamm.sodium_ion.BasicDFN()
    pv = pybamm.ParameterValues("Chayambuka2022")
    pv["Current function [A]"] = j * AREA
    if k_factor != 1.0:
        for e in ("Positive", "Negative"):
            f = pv[f"{e} electrode exchange-current density [A.m-2]"]
            pv[f"{e} electrode exchange-current density [A.m-2]"] = (lambda f: (lambda ce, cs, cmax, T: k_factor * f(ce, cs, cmax, T)))(f)
    sim = pybamm.Simulation(model, parameter_values=pv)
    sol = sim.solve([0, 3600 * 1.2 * 3e-3 / (j * AREA)])
    q = sol["Discharge capacity [A.h]"].entries * 1e3   # mAh
    v = sol["Voltage [V]"].entries
    return q, v


def main():
    pts = digitise()
    res = {"model": "pybamm.sodium_ion.BasicDFN + ParameterValues('Chayambuka2022')", "pybamm_version": pybamm.__version__,
           "reference": "Chayambuka et al. 2022 Fig. 4a experimental symbols (digitised)", "rates": {}}
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for i, (j, _) in enumerate(RATES.items()):
        qe = np.array([p[0] for p in pts[j]]); ve = np.array([p[1] for p in pts[j]])
        def mae(qs, vs):
            ok = qe <= qs.max()
            return float(np.mean(np.abs(np.interp(qe[ok], qs, vs) - ve[ok])) * 1e3)
        def trunc(q, v):
            cut = np.argmax(v < 2.0) if np.any(v < 2.0) else len(v)
            return q[:cut], v[:cut]
        q, v = simulate(j)
        qA, vA = trunc(q, v)
        qB, vB = trunc(q, v - R_CONTACT * j)
        qc, vc = simulate(j, k_factor=float(np.sqrt(1000.0)))
        qC, vC = trunc(qc, vc - R_CONTACT * j)
        qd, vd = simulate(j, k_factor=2.0)          # D: one-parameter calibration (k x2, no contact R)
        qD, vD = trunc(qd, vd)
        q_end_exp = float(qe.max())
        r = {"n_points": len(qe), "c_rate": round(j * AREA / 3e-3, 2), "paper_model_MAE_mV": PAPER_MAE_MV[j],
             "q_last_exp_point_mAh": round(q_end_exp, 3)}
        for tag, (qs, vs) in {"A_as_shipped": (qA, vA), "B_plus_contact_R": (qB, vB), "C_units_fix_plus_contact_R": (qC, vC),
                             "D_calibrated_k_x2": (qD, vD)}.items():
            r[tag] = {"MAE_mV": round(mae(qs, vs), 1), "q_end_mAh": round(float(qs.max()), 3),
                      "q_end_err_pct": round(100 * (qs.max() - q_end_exp) / q_end_exp, 2)}
            r[tag]["pass"] = bool(r[tag]["MAE_mV"] <= 60 and abs(r[tag]["q_end_err_pct"]) <= 5)
        col = ps.SERIES[i]
        ax.plot(qD, vD, color=col, lw=2, label=f"{j} A m$^{{-2}}$ ({r['c_rate']:.1f}C)")
        ax.plot(qA, vA, color=col, lw=1, alpha=0.45)
        ax.scatter(qe, ve, s=30, color=col, edgecolor=ps.SURFACE, linewidth=1.2, zorder=3)
        print(f"{j:3d} A/m2  MAE A {r['A_as_shipped']['MAE_mV']:6.1f} | B {r['B_plus_contact_R']['MAE_mV']:6.1f} | "
              f"C {r['C_units_fix_plus_contact_R']['MAE_mV']:6.1f} mV (paper {PAPER_MAE_MV[j]});  q_end C {qC.max():.3f} vs exp {q_end_exp:.3f}")
        res["rates"][str(j)] = r
    for tag in ("A_as_shipped", "B_plus_contact_R", "C_units_fix_plus_contact_R", "D_calibrated_k_x2"):
        res[f"all_pass_{tag}"] = all(r[tag]["pass"] for r in res["rates"].values())
    res["independent_validation_pass"] = res["all_pass_A_as_shipped"]
    res["calibrated_pass"] = res["all_pass_D_calibrated_k_x2"]
    res["verdict"] = ("Independent validation (parameters as shipped) FAILS the pre-set 60 mV voltage criterion at all four rates (MAE 67-121 mV) "
                      "(capacity within 5 % passes at all rates). A one-parameter calibration of the exchange-current scale (x2) "
                      "brings MAE to 42-55 mV at all rates (paper's own model 20-48 mV) - that is calibration on the same data, not "
                      "validation. Consequence for S3: capacity-vs-rate trends usable at +/-5 %; absolute voltages carry >= +/-0.1 V "
                      "uncertainty until kinetics are measured (GITT/EIS) for the real electrodes.")
    res["note_units"] = ("PyBaMM's Chayambuka2022 j0 normalises c_e by c_e0 while keeping k values whose paper units (Eq. 6) are "
                         "m^2.5 mol^-1.5 s^-1 with un-normalised c_e; the x sqrt(1000) correction fits the upper plateau but "
                         "overshoots the lower one, so the shipped k(c) tables likely differ from the paper's final optimised curves.")
    ax.set_xlabel("Discharge capacity (mAh)"); ax.set_ylabel("Cell voltage (V)")
    ax.set_title("PyBaMM sodium-ion DFN vs published HC//NVPF data")
    ax.set_xlim(0, 3); ax.set_ylim(2.0, 4.3)
    ax.legend(loc="lower left", title="thick: PyBaMM calibrated (k x2)  thin: as shipped  dots: experiment", title_fontsize=7)
    ps.note(ax, "Experiment digitised from Chayambuka et al. 2022, Fig. 4a", "upper right")
    ps.save(fig, OUT / "s02_validation_discharge",
            "PyBaMM sodium-ion DFN against digitised experimental HC//NVPF discharge curves: thin lines use parameters as shipped (independent validation: voltage MAE 67-121 mV, fails 60 mV gate); thick lines after a one-parameter kinetic calibration (MAE 42-55 mV).",
            "[SIM] PyBaMM BasicDFN, validated against [LIT] Chayambuka et al. 2022 (MAE per rate in s02_validation.json)")
    (OUT / "s02_validation.json").write_text(json.dumps(res, indent=2))
    print({k: v for k, v in res.items() if k.startswith("all_pass")})


if __name__ == "__main__":
    main()
