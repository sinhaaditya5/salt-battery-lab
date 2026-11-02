"""S5/S6 analysis: insertion voltages, interlayer spacing, barriers; uMLIP vs literature vs DFT+U.

Writes out/s05_summary.json and charts in out/ (PNG 300 dpi + SVG + caption with claim tags).
Run any time; DFT columns fill in as S6 results arrive in sim/s06_dft_ec2/runs/.
"""
import json, pathlib, sys, warnings
warnings.filterwarnings("ignore")
import numpy as np
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "tools"))
import plotstyle as ps
import matplotlib.pyplot as plt
from pymatgen.core import Structure

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"
REF = json.loads((HERE / "literature_refs.json").read_text())
RY = 13.605693122994
MODELS = {"mace_mp0b3": "MACE-MP-0b3", "mace_mp0": "MACE-MP-0", "chgnet": "CHGNet"}

# reaction: (inserted state, host, ion, n ions per cell, metal reference)
REACTIONS = {
    "LiFePO4": ("LiFePO4", "FePO4_olivine", "Li", 4),
    "LiMn2O4": ("LiMn2O4", "lambda_MnO2", "Li", 2),
    "NaFePO4_olivine": ("NaFePO4_olivine", "FePO4_olivine", "Na", 4),
    "Na3Ti2PO43": ("Na3Ti2PO43", "NaTi2PO43", "Na", 4),
    "Na2MnFeCN6": ("Na2MnFeCN6", "MnFeCN6", "Na", 2),
}
BIRN = {"x 1/9 -> 3/9": ("birnessite_Na3_9", "birnessite_Na1_9", "Na", 2),
        "x 3/9 -> 5/9": ("birnessite_Na5_9", "birnessite_Na3_9", "Na", 2)}


def mlip_energies(model):
    p = OUT / f"relax_{model}.json"
    if not p.exists():
        return {}
    return {k: v["energy_eV"] for k, v in json.loads(p.read_text()).items() if "energy_eV" in v}


def dft_energies():
    """Final total energies (eV) of finished S6 jobs; job dir names are <lane>_[<prio>_]<name>."""
    out, meta = {}, {}
    runs = LAB / "sim/s06_dft_ec2/runs/jobs"
    if not runs.exists():
        return out, meta
    for d in sorted(runs.iterdir()):
        txt0 = (d / "pw.out").read_text(errors="ignore") if (d / "pw.out").exists() else ""
        done = (d / "DONE").exists()
        bfgs_ok = "bfgs converged" in txt0
        if not (done or ((d / "FAILED").exists() and bfgs_ok)):
            continue
        name = d.name.split("_", 1)[1]
        if name[:2] in ("1_", "2_", "3_", "4_"):
            name = name[2:]
        txt = (d / "pw.out").read_text(errors="ignore")
        es = [float(l.split("=")[1].split()[0]) for l in txt.splitlines() if l.strip().startswith("!")]
        if not es:
            continue
        out[name] = es[-1] * RY
        mags = [l for l in txt.splitlines() if "total magnetization" in l]
        if bfgs_ok and "End final coordinates" in txt:
            # use the last BFGS-converged energy (the optional final fresh-basis SCF may be missing/crashed)
            pre = txt.split("End final coordinates")[0]
            es = [float(l.split("=")[1].split()[0]) for l in pre.splitlines() if l.strip().startswith("!")] or es
            out[name] = es[-1] * RY
        meta[name] = {"status": "DONE" if done else "bfgs-converged; final SCF crashed", "n_scf": len(es), "wall_s": (d / "WALL_SECONDS").read_text().strip() if (d / "WALL_SECONDS").exists() else None,
                      "total_mag": mags[-1].split("=")[1].split()[0] if mags else None}
    return out, meta


def voltage(E, ins, host, ion, n):
    metal = "Li_bcc" if ion == "Li" else "Na_bcc"
    if not all(k in E for k in (ins, host, metal)):
        return None
    return -(E[ins] - E[host] - n * E[metal]) / n


def interlayer(model):
    res = {}
    for n in (1, 3, 5):
        p = OUT / f"relaxed_{model}" / f"birnessite_Na{n}_9.json"
        if p.exists():
            s = Structure.from_dict(json.loads(p.read_text()))
            a, b = s.lattice.matrix[0], s.lattice.matrix[1]
            res[n / 9] = float(s.volume / np.linalg.norm(np.cross(a, b)))
    return res


def dft_interlayer():
    res = {}
    runs = LAB / "sim/s06_dft_ec2/runs/jobs"
    from ase.io import read
    for n in (1, 3, 5):
        for d in runs.glob(f"*birnessite_Na{n}_9") if runs.exists() else []:
            if (d / "DONE").exists():
                at = read(str(d / "pw.out"), format="espresso-out", index=-1)
                c = at.cell
                res[n / 9] = float(at.get_volume() / np.linalg.norm(np.cross(c[0], c[1])))
    return res


def main():
    summary = {"label": "[SIM] uMLIP screen (MACE-MP-0b3, MACE-MP-0, CHGNet); DFT+U columns '[SIM] DFT+U PBE+U GBRV, screening settings'",
               "voltages": {}, "birnessite_voltage": {}, "interlayer_A": {}, "barriers_eV": {}, "errors": {}}
    Edft, dmeta = dft_energies()
    summary["dft_jobs_done"] = dmeta
    sources = {m: mlip_energies(m) for m in MODELS}
    sources["dft"] = Edft
    for rx, (ins, host, ion, n) in REACTIONS.items():
        row = {"literature": REF["voltages_V"][rx]}
        for m, E in sources.items():
            v = voltage(E, ins, host, ion, n)
            row[m] = None if v is None else round(v, 3)
        summary["voltages"][rx] = row
    for rx, (ins, host, ion, n) in BIRN.items():
        summary["birnessite_voltage"][rx] = {m: (None if voltage(E, ins, host, ion, n) is None else round(voltage(E, ins, host, ion, n), 3))
                                             for m, E in sources.items()}
    for m in MODELS:
        summary["interlayer_A"][m] = interlayer(m)
    summary["interlayer_A"]["dft"] = dft_interlayer()
    # error statistics vs literature
    for m in list(MODELS) + ["dft"]:
        errs = [summary["voltages"][rx][m] - REF["voltages_V"][rx]["value"]
                for rx in REACTIONS if summary["voltages"][rx].get(m) is not None]
        if errs:
            e = np.array(errs)
            summary["errors"][m] = {"n": len(e), "MAE_V": round(float(np.abs(e).mean()), 3),
                                    "max_abs_V": round(float(np.abs(e).max()), 3), "mean_signed_V": round(float(e.mean()), 3)}
    for m in MODELS:
        p = OUT / f"neb_{m}.json"
        if p.exists():
            summary["barriers_eV"][m] = {k: v.get("barrier_forward_eV") for k, v in json.loads(p.read_text()).items()}
    (OUT / "s05_summary.json").write_text(json.dumps(summary, indent=2))
    charts(summary)
    print(json.dumps({k: summary[k] for k in ("voltages", "errors", "birnessite_voltage", "interlayer_A", "barriers_eV")}, indent=1))


def charts(S):
    # 1) Voltage parity: computed vs literature, one panel per method family
    rxs = list(REACTIONS)
    lit = np.array([REF["voltages_V"][r]["value"] for r in rxs])
    fig, ax = plt.subplots(figsize=(5.6, 4.6))
    lo, hi = 1.0, 5.0
    ax.plot([lo, hi], [lo, hi], color=ps.DEEMPH, lw=1, zorder=1)
    ax.fill_between([lo, hi], [lo - 0.3, hi - 0.3], [lo + 0.3, hi + 0.3], color=ps.GRID, alpha=0.6, lw=0, zorder=0)
    methods = [("mace_mp0b3", "MACE-MP-0b3", "o"), ("chgnet", "CHGNet", "s"), ("mace_mp0", "MACE-MP-0", "^"), ("dft", "DFT+U", "D")]
    for m, lab, mk in methods:
        y = np.array([S["voltages"][r].get(m) if S["voltages"][r].get(m) is not None else np.nan for r in rxs], float)
        if np.all(np.isnan(y)):
            continue
        err = S["errors"].get(m, {})
        ax.scatter(lit, y, s=48, marker=mk, color=ps.ENTITY[lab], edgecolor=ps.SURFACE, linewidth=1.5, zorder=3,
                   label=f"{lab} (MAE {err.get('MAE_V', float('nan')):.2f} V)")
    short = {"LiFePO4": "LiFePO$_4$", "LiMn2O4": "LiMn$_2$O$_4$", "NaFePO4_olivine": "NaFePO$_4$",
             "Na3Ti2PO43": "NaTi$_2$(PO$_4$)$_3$", "Na2MnFeCN6": "Na$_2$MnFe(CN)$_6$"}
    for r, x in zip(rxs, lit):
        ax.annotate(short[r], (x, x), xytext=(6, -12), textcoords="offset points", fontsize=7.5, color=ps.TEXT2)
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.set_xlabel("Literature voltage (V vs alkali metal)")
    ax.set_ylabel("Computed average voltage (V)")
    ax.set_title("Insertion voltage: computed vs literature")
    ax.legend(loc="upper left")
    ps.note(ax, "grey band = ±0.3 V", "lower right")
    ps.save(fig, OUT / "s05_voltage_parity",
            "Average insertion voltages from universal ML potentials (and DFT+U where finished) against literature values for five validation compounds.",
            "[SIM] uMLIP screen, not DFT-verified; [LIT] reference voltages (sim/s05_atomistic/literature_refs.json)")
    # 2) Birnessite interlayer spacing vs Na content, XRD band
    fig, ax = plt.subplots(figsize=(5.6, 3.8))
    d = REF["structure"]["birnessite_d001_A"]
    ax.axhspan(d["range"][0], d["range"][1], color=ps.GRID, lw=0)
    ax.axhline(d["value"], color=ps.DEEMPH, lw=1)
    ax.text(0.585, d["value"] + 0.02, "XRD 7.19 Å (Na$_{0.27}$, pristine)", fontsize=7.5, color=ps.TEXT2, ha="right", va="bottom")
    ax.text(0.585, d["range"][0] + 0.02, "in-situ range 7.02–7.33 Å", fontsize=7.2, color=ps.MUTED, ha="right", va="bottom")
    for (m, lab, mk) in methods:
        src = S["interlayer_A"].get(m, {})
        if not src:
            continue
        xs = sorted(float(k) for k in src)
        ys = [src[k] if k in src else src[str(k)] for k in sorted(src, key=float)]
        ax.plot(xs, ys, marker=mk, color=ps.ENTITY[lab], label=lab, markersize=7, markeredgecolor=ps.SURFACE, markeredgewidth=1.5)
    ax.axvline(0.27, color=ps.DEEMPH, lw=0.8)
    ax.set_xlabel("Na per Mn (x) in Na$_x$MnO$_2$·0.67H$_2$O model")
    ax.set_ylabel("Interlayer spacing (Å)")
    ax.set_title("Birnessite interlayer spacing vs sodium content")
    ax.legend(loc="upper right")
    ps.save(fig, OUT / "s05_birnessite_interlayer",
            "Relaxed interlayer spacing of a 48-atom ordered birnessite model at three Na contents, compared with the reference paper's XRD.",
            "[SIM] uMLIP screen, ordered model of a disordered material; [LIT] Shan et al. 2019 XRD")
    # 3) Barriers
    if S["barriers_eV"]:
        paths = ["LiFePO4_b", "NaFePO4_b", "birnessite_Na", "PBA_Na"]
        labels = ["LiFePO$_4$ [010]", "NaFePO$_4$ [010]", "Birnessite Na hop", "Prussian white Na"]
        fig, ax = plt.subplots(figsize=(6.0, 3.6))
        ms = [m for m in MODELS if m in S["barriers_eV"]]
        w = 0.8 / max(1, len(ms))
        for i, m in enumerate(ms):
            vals = [S["barriers_eV"][m].get(p) or np.nan for p in paths]
            xs = np.arange(len(paths)) + (i - (len(ms) - 1) / 2) * w
            ax.bar(xs, vals, width=min(w * 0.85, 0.22), color=ps.ENTITY[MODELS[m]], label=MODELS[m])
            for x, v in zip(xs, vals):
                if not np.isnan(v):
                    ax.text(x, v + 0.01, f"{v:.2f}", ha="center", va="bottom", fontsize=7, color=ps.TEXT2)
        ax.scatter([0], [REF["barriers_eV"]["LiFePO4_b"]["value"]], marker="_", s=400, color=ps.TEXT, zorder=4, label="Literature (GGA)")
        ax.set_xticks(range(len(paths))); ax.set_xticklabels(labels)
        ax.set_ylabel("Migration barrier (eV)")
        ax.set_title("Alkali-ion migration barriers (climbing-image NEB)")
        ax.legend(loc="upper left")
        ps.save(fig, OUT / "s05_barriers",
                "Climbing-image NEB migration barriers from universal ML potentials; LiFePO4 compared with the GGA literature value.",
                "[SIM] uMLIP screen, not DFT-verified; [LIT] Morgan et al. 2004 (0.27 eV)")


if __name__ == "__main__":
    main()
