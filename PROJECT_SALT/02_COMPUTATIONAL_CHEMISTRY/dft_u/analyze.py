#!/usr/bin/env python3
"""S11 analysis: convergence, lattice parameters, moments, formation enthalpies, conversion voltages and U sensitivity.

Experimental references (298 K, NBS/CRC standard tables; values transcribed - VERIFY against CRC Handbook before citing):
  dfH  NaCl -411.15, FeCl2 -341.79, CoCl2 -312.5, NiCl2 -305.33 kJ/mol
  dfG  NaCl -384.14, FeCl2 -302.35, CoCl2 -269.8, NiCl2 -259.03 kJ/mol
DFT total energies are 0 K, no zero-point/thermal terms, so they are compared with the dH-based voltage; the dG-based value
and the ~300 C ZEBRA OCVs (Ni 2.58 V, Fe 2.35 V) are shown for context.  Output: out/s11_results.json + charts.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent; LAB = HERE.parents[1]; RUNS = HERE / "runs"; OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(LAB / "tools"))
import campaign as C  # noqa: E402
RY = 13.605693122994; KJ = 96.485                       # eV per Ry; kJ/mol per eV
EXP_H = dict(NaCl=-411.15, FeCl2=-341.79, CoCl2=-312.5, NiCl2=-305.33)
EXP_G = dict(NaCl=-384.14, FeCl2=-302.35, CoCl2=-269.8, NiCl2=-259.03)
EXP_OCV_300C = dict(Ni=2.58, Fe=2.35)
EXP_LAT = dict(Na_bcc=4.225, NaCl_rs=5.640, Fe_bcc=2.866, Ni_fcc=3.524, Co_hcp=(2.507, 4.070),
               FeCl2=(3.579, 17.536), CoCl2=(3.544, 17.43), NiCl2=(3.543, 17.335))
NAT = dict(Na_bcc=1, NaCl_rs=1, Fe_bcc=1, Ni_fcc=1, Co_hcp=2, Cl2_box=1)   # formula units per cell

def E_fu(job, nfu=1):
    p = C.parse(RUNS / job / "job.out")
    return None if p["E_Ry"] is None else p["E_Ry"] * RY / nfu, p

def lattice(job):
    try:
        cell, atoms = C.relaxed_geometry(RUNS / job)
    except Exception:
        return None
    return cell

def hex_ac(cell):
    a = np.linalg.norm(cell[0] - cell[1]); c = np.linalg.norm(cell[0] + cell[1] + cell[2]); return a, c

def exp_voltage(m, which="H"):
    T = EXP_H if which == "H" else EXP_G
    return -(2 * T["NaCl"] - T[f"{m}Cl2"]) / (2 * KJ)

def main():
    res = dict(convergence={}, lattice={}, moments={}, formation={}, voltages={}, uscan={}, magnetic={}, gaps={}, pdos={},
               status={}, platform={})
    # ---- convergence
    for nm, nat in (("NaCl_rs", 2), ("NiCl2_FM", 3), ("Ni_fcc", 1)):
        rows = {}
        for d in sorted((RUNS / "conv").glob(nm + "_*")):
            p = C.parse(d / "job.out")
            if p["E_Ry"] is not None: rows[d.name.split("_")[-1]] = p["E_Ry"] * RY / nat * 1000   # meV/atom
        if rows:
            ref_e = rows.get("ecut70"); ref_k = rows.get("k60" if nm == "Ni_fcc" else "k30")
            res["convergence"][nm] = {k: round(v - (ref_e if k.startswith("ecut") else ref_k), 2) for k, v in rows.items()
                                      if (ref_e if k.startswith("ecut") else ref_k) is not None}
    # ---- reference phases
    E = {}
    for job, nfu in (("Na_bcc", 1), ("NaCl_rs", 1), ("Fe_bcc", 1), ("Ni_fcc", 1), ("Co_hcp", 2), ("Cl2_box", 1)):
        e, p = E_fu(f"relax/{job}", nfu); E[job] = e
        res["status"][job] = (RUNS / "relax" / job / "STATUS").read_text().strip() if (RUNS / "relax" / job / "STATUS").exists() else "pending"
        cell = lattice(f"relax/{job}")
        if cell is not None and job in EXP_LAT:
            if job == "Co_hcp":
                a, c = np.linalg.norm(cell[0]), np.linalg.norm(cell[2]); res["lattice"][job] = dict(a=round(a, 3), c=round(c, 3), exp=EXP_LAT[job])
            else:
                vol = abs(np.linalg.det(cell)); a = (vol * (2 if job.endswith("bcc") else 4)) ** (1 / 3)
                res["lattice"][job] = dict(a_conv=round(a, 3), exp=EXP_LAT[job], err_pct=round(100 * (a / EXP_LAT[job] - 1), 2))
        if p.get("abs_mag") is not None: res["moments"][job] = p["total_mag"]
    # ---- chlorides (relaxed at U0, U4)
    for m in ("Fe", "Co", "Ni"):
        for U in (0, 4):
            job = f"relax/{m}Cl2_FM_U{U}"
            e, p = E_fu(job, 1); E[f"{m}Cl2_U{U}"] = e
            res["status"][f"{m}Cl2_U{U}"] = (RUNS / job / "STATUS").read_text().strip() if (RUNS / job / "STATUS").exists() else "pending"
            cell = lattice(job)
            if cell is not None:
                a, c = hex_ac(cell); ea, ec = EXP_LAT[f"{m}Cl2"]
                res["lattice"][f"{m}Cl2_U{U}"] = dict(a_hex=round(a, 3), c_hex=round(c, 3), exp=[ea, ec], err_a_pct=round(100 * (a / ea - 1), 2), err_c_pct=round(100 * (c / ec - 1), 2))
            if p.get("total_mag") is not None: res["moments"][f"{m}Cl2_U{U}"] = p["total_mag"]
    # ---- formation enthalpies and voltages (U consistent with metals only at U=0)
    if all(E.get(k) is not None for k in ("Na_bcc", "NaCl_rs", "Cl2_box")):
        dHf = E["NaCl_rs"] - E["Na_bcc"] - 0.5 * E["Cl2_box"]
        res["formation"]["NaCl"] = dict(dft_eV=round(dHf, 3), exp_eV=round(EXP_H["NaCl"] / KJ, 3), err_eV=round(dHf - EXP_H["NaCl"] / KJ, 3))
        res["voltages"]["Na+1/2Cl2"] = dict(dft_V=round(-dHf, 3), exp_dH_V=round(-EXP_H["NaCl"] / KJ, 3), exp_dG_V=round(-EXP_G["NaCl"] / KJ, 3))
    for m, met in (("Fe", "Fe_bcc"), ("Co", "Co_hcp"), ("Ni", "Ni_fcc")):
        for U in (0, 4):
            k = f"{m}Cl2_U{U}"
            if all(E.get(x) is not None for x in (k, met, "Na_bcc", "NaCl_rs", "Cl2_box")):
                dHf = E[k] - E[met] - E["Cl2_box"]
                V = -(2 * E["NaCl_rs"] + E[met] - E[k] - 2 * E["Na_bcc"]) / 2
                res["formation"][k] = dict(dft_eV=round(dHf, 3), exp_eV=round(EXP_H[f"{m}Cl2"] / KJ, 3), err_eV=round(dHf - EXP_H[f"{m}Cl2"] / KJ, 3),
                                           note="U>0 chloride vs U=0 metal: mixed-functional energy, not corrected" if U else "consistent PBE")
                res["voltages"][k] = dict(dft_V=round(V, 3), exp_dH_V=round(exp_voltage(m, "H"), 3), exp_dG_V=round(exp_voltage(m, "G"), 3),
                                          exp_OCV_300C=EXP_OCV_300C.get(m), err_vs_dH_V=round(V - exp_voltage(m, "H"), 3))
    # ---- U scan (fixed geometry)
    for m, met in (("Fe", "Fe_bcc"), ("Co", "Co_hcp"), ("Ni", "Ni_fcc")):
        for g in (0, 4):
            row = {}
            for U in (0, 2, 4, 6):
                e, p = E_fu(f"uscan/{m}Cl2_geomU{g}_U{U}", 1)
                if e is not None and all(E.get(x) is not None for x in (met, "Na_bcc", "NaCl_rs")):
                    gp = C.band_gap(RUNS / f"uscan/{m}Cl2_geomU{g}_U{U}" / "job.out")
                    row[U] = dict(V=round(-(2 * E["NaCl_rs"] + E[met] - e - 2 * E["Na_bcc"]) / 2, 3), mag=p.get("total_mag"),
                                  gap_eV=None if gp is None else max(0.0, gp["gap_eV"]), metallic=None if gp is None else gp["gap_eV"] <= 0)
            if row: res["uscan"][f"{m}Cl2_geomU{g}"] = row
    # ---- magnetic order
    for m in ("Fe", "Co", "Ni"):
        for U in (0, 4):
            ea, _ = E_fu(f"mag/{m}Cl2_AFM_U{U}", 2); ef, _ = E_fu(f"mag/{m}Cl2_FMsup_U{U}", 2)
            if ea is not None and ef is not None:
                res["magnetic"][f"{m}Cl2_U{U}"] = dict(E_AFM_minus_FM_meV_per_fu=round(1000 * (ea - ef), 2), ground=("AFM (interlayer)" if ea < ef else "FM"))
    # ---- band gaps on the SCF k-mesh (electron counting; <=0 means the FM solution is metallic)
    for m in ("Fe", "Co", "Ni"):
        for U in (0, 4):
            for tag, job in (("relax", f"relax/{m}Cl2_FM_U{U}"), ("dos_k30", f"dos/{m}Cl2_U{U}_keep")):
                g = C.band_gap(RUNS / job / "job.out")
                if g: res["gaps"][f"{m}Cl2_U{U}_{tag}"] = dict(gap_eV=max(0.0, g["gap_eV"]), metallic=g["gap_eV"] <= 0, raw_eV=g["gap_eV"])
    res["pdos"] = pdos_summary()
    # ---- where each job ran (local Apple M4 vs EC2 c8g.8xlarge, same QE 7.6 conda-forge build family)
    for cmd in sorted(RUNS.glob("*/*/cmd.txt")):
        res["platform"][str(cmd.parent.relative_to(RUNS))] = "EC2 c8g.8xlarge (linux-aarch64)" if "/work/lab" in cmd.read_text() else "local Apple M4 (osx-arm64)"
    json.dump(res, open(OUT / "s11_results.json", "w"), indent=1, default=str)
    print(json.dumps({k: res[k] for k in ("status", "formation", "voltages", "magnetic", "gaps")}, indent=1, default=str))
    plot(res); plot_pdos()

def plot(res):
    if not res["uscan"]: return
    import plotstyle as ps; import matplotlib.pyplot as plt
    ps.apply(); fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for i, m in enumerate(("Fe", "Co", "Ni")):
        row = res["uscan"].get(f"{m}Cl2_geomU4") or res["uscan"].get(f"{m}Cl2_geomU0")
        if not row: continue
        Us = sorted(int(u) for u in row); ax.plot(Us, [row[u]["V"] if u in row else row[str(u)]["V"] for u in Us], "o-", color=ps.SERIES[i], label=f"{m}Cl₂ + 2Na (DFT+U)")
        ax.axhline(exp_voltage(m, "H"), color=ps.SERIES[i], ls="--", lw=1)
    ax.set_xlabel("Hubbard U on M-3d (eV); metal reference always U = 0"); ax.set_ylabel("Voltage vs Na (V)")
    ax.set_title("Conversion voltage 2Na + MCl₂ → 2NaCl + M: sensitivity to U")
    from matplotlib.lines import Line2D
    h, _ = ax.get_legend_handles_labels()
    h.append(Line2D([], [], color=ps.TEXT2, ls="--", lw=1, label="dashed: experimental ΔH voltage (same colour)"))
    ax.legend(handles=h, fontsize=7.5, loc="upper left")
    ps.save(fig, OUT / "s11_voltage_vs_U", "DFT(+U) conversion voltages of Na-MCl2 couples versus Hubbard U, against experimental enthalpy-based voltages.",
            "[SIMULATED] PBE(+U)-D3, QE 7.6, GBRV USPP; experimental [PUBLISHED] thermochemistry (transcribed, verify)")

def _read_pdos(d, elem, l):
    """Sum spin-up / spin-down PDOS over every pdos_atm file of element `elem` and channel `l` ('d' or 'p')."""
    files = sorted(d.glob(f"pdos.pdos_atm#*({elem})_wfc#*({l})"))
    if not files: return None
    E = up = dn = None
    for f in files:
        a = np.loadtxt(f)
        if E is None: E, up, dn = a[:, 0], a[:, 1].copy(), a[:, 2].copy()
        else: up += a[:, 1]; dn += a[:, 2]
    return E, up, dn

def _fermi(d):
    import re as _re
    t = (d / "job.out").read_text(errors="ignore") if (d / "job.out").exists() else ""
    f = _re.findall(r"the Fermi energy is\s+(-?\d+\.\d+) ev", t); return float(f[-1]) if f else None

def pdos_summary():
    out = {}
    for d in sorted((RUNS / "dos").glob("*_keep")) if (RUNS / "dos").exists() else []:
        m = d.name[:2]; ef = _fermi(d); dd = _read_pdos(d, m, "d"); pp = _read_pdos(d, "Cl", "p")
        if ef is None or dd is None or pp is None: continue
        E = dd[0] - ef; tot = dd[1] + dd[2] + pp[1] + pp[2]
        occ = np.where((E <= 0.0) & (tot > 0.05 * tot.max()))[0]   # highest occupied state with real weight (E_F of an
        vbm = float(E[occ.max()]) if occ.size else 0.0             # insulator sits mid-gap under smearing)
        win = (E > vbm - 1.0) & (E <= vbm)                         # top 1 eV of the valence band
        wd = np.trapezoid(dd[1][win] + dd[2][win], E[win]); wp = np.trapezoid(pp[1][win] + pp[2][win], E[win])
        out[d.name.replace("_keep", "")] = dict(E_F_eV=ef, vbm_minus_EF_eV=round(vbm, 2), top1eV_M3d_frac=round(float(wd / (wd + wp)), 3),
                                                note="share of M-3d vs Cl-3p projected states in the top 1 eV of the valence band")
    return out

def plot_pdos():
    dirs = [RUNS / "dos" / f"{m}Cl2_U4_keep" for m in ("Fe", "Co", "Ni")]
    dirs = [d for d in dirs if (d / "projwfc.out").exists() and _fermi(d) is not None]
    if not dirs: return
    import plotstyle as ps; import matplotlib.pyplot as plt
    ps.apply(); fig, axes = plt.subplots(len(dirs), 1, figsize=(7.2, 2.3 * len(dirs)), sharex=True, squeeze=False)
    for ax, d in zip(axes[:, 0], dirs):
        m = d.name[:2]; ef = _fermi(d)
        for (el, l), col, lab in (((m, "d"), ps.SERIES[0], f"{m} 3d"), (("Cl", "p"), ps.SERIES[1], "Cl 3p")):
            r = _read_pdos(d, el, l)
            if r is None: continue
            ax.plot(r[0] - ef, r[1], color=col, lw=1.1, label=lab); ax.plot(r[0] - ef, -r[2], color=col, lw=1.1)
        ax.axvline(0, color=ps.MUTED, lw=0.8, ls="--"); ax.axhline(0, color=ps.GRID, lw=0.8)
        ax.set_ylabel("PDOS (states/eV)\n↑ up / ↓ down"); ax.set_xlim(-8, 6)
        ax.text(0.01, 0.92, f"{m}Cl₂, U = 4 eV", transform=ax.transAxes, fontsize=8.5, color=ps.TEXT, va="top")
        ax.legend(fontsize=7.5, loc="upper right")
    axes[-1, 0].set_xlabel("E − E_F (eV)")
    axes[0, 0].set_title("Spin-resolved projected DOS of the FM chlorides (PBE+U-D3, k 30 Å)")
    ps.save(fig, OUT / "s11_pdos", "Projected density of states (metal 3d, Cl 3p) of FeCl2, CoCl2 and NiCl2 at U = 4 eV. For the insulators "
            "(CoCl2, NiCl2) E_F falls inside the gap; FeCl2 has a minority-spin Fe-3d state at E_F (metallic in the symmetric cell).",
            "[SIMULATED] PBE+U-D3, QE 7.6 projwfc.x, GBRV USPP; FM order, R-3m 3-atom cell")

if __name__ == "__main__":
    main()
