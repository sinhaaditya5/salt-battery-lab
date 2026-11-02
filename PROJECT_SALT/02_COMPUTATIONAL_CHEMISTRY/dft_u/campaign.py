#!/usr/bin/env python3
"""S11 - local DFT(+U) campaign for the 'salt-literal' chemistries (Na | NaCl | MCl2 and Na | Cl2).

Why these systems: they are the only rechargeable chemistries in which common salt (NaCl) is itself
the discharged active material (ZEBRA-type Na-MCl2 cells are assembled from NaCl + metal powder;
Na-Cl2 cells cycle NaCl <-> Na + 1/2 Cl2). The campaign tests how well PBE(+U) reproduces their
thermodynamics before any number from it is used for screening.

Engine:  Quantum ESPRESSO 7.6 (conda-forge, osx-arm64), run locally on the Apple M4.
Pseudos: GBRV ultrasoft v1.x (PBE), tools/pseudo/gbrv (provenance: tools/pseudo/gbrv_pbe_v1.5.tar.gz).
Usage:   python campaign.py write <stage>   # writes inputs under runs/<stage>/<job>/
         python campaign.py run <stage> [--lanes 2 --np 4 --nk 1]   (--nk = pw.x k-point pools)
Stages:  conv, relax, mag, dos, bands, defect, neb   (see STAGES below)
Every job folder holds: job.in, job.out, STATUS (DONE/FAILED), wall.txt, cmd.txt.
"""
from __future__ import annotations
import json, os, re, subprocess, sys, time, shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np

LAB = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
QE = LAB / "tools/micromamba/envs/qe/bin"
PSEUDO = LAB / "tools/pseudo/gbrv"
PP = {"Na": ("22.990", "na_pbe_v1.5.uspp.F.UPF"), "Cl": ("35.453", "cl_pbe_v1.4.uspp.F.UPF"),
      "Fe": ("55.845", "fe_pbe_v1.5.uspp.F.UPF"), "Co": ("58.933", "co_pbe_v1.2.uspp.F.UPF"),
      "Ni": ("58.693", "ni_pbe_v1.4.uspp.F.UPF")}
MAG0 = {"Fe": 0.6, "Co": 0.5, "Ni": 0.4}          # starting_magnetization (fraction)
TM = ("Fe", "Co", "Ni")
U_SCAN = (0.0, 2.0, 4.0, 6.0)
ECUT = (50, 400)                                  # production wfc/rho cutoffs, Ry (chosen from conv stage)

# ---------------------------------------------------------------- structures (Angstrom)
# Starting geometries from standard crystallographic data; every production job is vc-relaxed,
# so these only need the right structure type.
def bcc(a):  return np.array([[-a/2, a/2, a/2], [a/2, -a/2, a/2], [a/2, a/2, -a/2]])
def fcc(a):  return np.array([[0, a/2, a/2], [a/2, 0, a/2], [a/2, a/2, 0]])
def hcp(a, c): return np.array([[a, 0, 0], [-a/2, a*np.sqrt(3)/2, 0], [0, 0, c]])

def rhombo_from_hex(a, c):
    """Primitive rhombohedral vectors (obverse) for R-3m given hexagonal a, c."""
    A = np.array([a, 0, 0]); B = np.array([-a/2, a*np.sqrt(3)/2, 0]); C = np.array([0, 0, c])
    return np.array([(2*A + B + C)/3, (-A + B + C)/3, (-A - 2*B + C)/3])

# CdCl2-type MCl2, R-3m, hex a, c, Cl 6c z  (Wyckoff & ICSD-type data; relaxed anyway)
MCL2 = {"Fe": (3.579, 17.536, 0.2576), "Co": (3.544, 17.430, 0.2570), "Ni": (3.543, 17.335, 0.2557)}

def structures():
    S = {}
    S["Na_bcc"] = dict(cell=bcc(4.225), atoms=[("Na", (0, 0, 0))], kind="metal")
    S["NaCl_rs"] = dict(cell=fcc(5.640), atoms=[("Na", (0, 0, 0)), ("Cl", (.5, .5, .5))], kind="ins")
    L = 12.0; d = 1.988
    S["Cl2_box"] = dict(cell=np.diag([L, L + 0.5, L + 1.0]),
                        atoms=[("Cl", (0.5 - d/2/L, 0.5, 0.5)), ("Cl", (0.5 + d/2/L, 0.5, 0.5))], kind="mol")
    S["Fe_bcc"] = dict(cell=bcc(2.866), atoms=[("Fe", (0, 0, 0))], kind="metal")
    S["Ni_fcc"] = dict(cell=fcc(3.524), atoms=[("Ni", (0, 0, 0))], kind="metal")
    S["Co_hcp"] = dict(cell=hcp(2.507, 4.070), atoms=[("Co", (1/3, 2/3, 0.25)), ("Co", (2/3, 1/3, 0.75))], kind="metal")
    for m, (a, c, z) in MCL2.items():
        S[f"{m}Cl2_FM"] = dict(cell=rhombo_from_hex(a, c),
                               atoms=[(m, (0, 0, 0)), ("Cl", (z, z, z)), ("Cl", (-z, -z, -z))], kind="tm")
        # interlayer-AFM supercell: A1=a1-a2, A2=a2-a3, A3=2a3 keeps layers FM, alternates spin by layer
        R = rhombo_from_hex(a, c); T = np.array([[1, -1, 0], [0, 1, -1], [0, 0, 2]])
        cell = T @ R; inv = np.linalg.inv(cell)
        cart = []
        for shift in (np.zeros(3), R[2]):
            cart += [(m + ("1" if not shift.any() else "2"), shift)]
            cart += [("Cl", shift + z*(R[0]+R[1]+R[2])), ("Cl", shift - z*(R[0]+R[1]+R[2]))]
        atoms = [(s, tuple(np.mod(np.array(p) @ inv, 1.0))) for s, p in cart]
        S[f"{m}Cl2_AFM"] = dict(cell=cell, atoms=atoms, kind="tm_afm")
    return S

# ---------------------------------------------------------------- input writer
def kmesh(cell, density):
    """k-mesh from a target linear density (k-points * Angstrom)."""
    rec = np.linalg.norm(np.linalg.inv(cell).T, axis=1)
    return [max(1, int(np.ceil(density * r))) for r in rec]

def write_input(path: Path, name, st, calc="vc-relax", U=0.0, ecut=ECUT, kdens=None, extra_sys="",
                nspin=None, kpts=None, nbnd=None, tot_charge=0, occupations=None, positions=None,
                cell=None, conv_thr=1e-9):
    if kdens is None: kdens = 40.0 if st["kind"] == "metal" else 20.0
    path.mkdir(parents=True, exist_ok=True)
    cell = st["cell"] if cell is None else cell
    atoms = st["atoms"] if positions is None else positions
    species = []
    for s, _ in atoms:
        if s not in species: species.append(s)
    elem = lambda s: re.sub(r"\d", "", s)
    magnetic = any(elem(s) in TM for s in species)
    nspin = nspin or (2 if magnetic else 1)
    lines = ["&control", f"  calculation='{calc}', prefix='{name}', outdir='./tmp',",
             f"  pseudo_dir='{PSEUDO}', tprnfor=.true., tstress=.true.,",
             "  etot_conv_thr=1e-5, forc_conv_thr=1e-4, disk_io='low'", "/",
             "&system", f"  ibrav=0, nat={len(atoms)}, ntyp={len(species)},",
             f"  ecutwfc={ecut[0]}, ecutrho={ecut[1]}, vdw_corr='dft-d3', dftd3_version=4,"]
    occ = occupations or ("smearing" if st["kind"] in ("metal", "tm", "tm_afm") else "fixed")
    if st["kind"] == "mol": occ = "smearing"
    if occ == "smearing":
        lines.append("  occupations='smearing', smearing='mv', degauss=0.01,")
    else:
        lines.append("  occupations='fixed',")
    if nspin == 2:
        lines.append("  nspin=2,")
        for i, s in enumerate(species, 1):
            e = elem(s)
            if e in TM:
                sign = -1 if s.endswith("2") else 1
                lines.append(f"  starting_magnetization({i})={sign*MAG0[e]},")
    if tot_charge: lines.append(f"  tot_charge={tot_charge},")
    if nbnd: lines.append(f"  nbnd={nbnd},")
    if extra_sys: lines.append("  " + extra_sys)
    lines += ["/", "&electrons", f"  conv_thr={conv_thr:.0e}, mixing_beta=0.3, electron_maxstep=200", "/"]
    if calc in ("relax", "vc-relax"): lines += ["&ions", "  ion_dynamics='bfgs'", "/"]
    if calc == "vc-relax": lines += ["&cell", "  cell_dynamics='bfgs', press_conv_thr=0.5" +
                                     (", cell_dofree='ibrav'" if False else ""), "/"]
    lines.append("ATOMIC_SPECIES")
    for s in species:
        m, f = PP[elem(s)]
        lines.append(f"{s} {m} {f}")
    if U > 0 and magnetic:
        lines.append("HUBBARD (ortho-atomic)")
        for s in species:
            if elem(s) in TM: lines.append(f"U {s}-3d {U:.2f}")
    lines.append("CELL_PARAMETERS angstrom")
    lines += ["  " + " ".join(f"{x:.8f}" for x in v) for v in cell]
    lines.append("ATOMIC_POSITIONS crystal")
    lines += [f"{s} " + " ".join(f"{x:.8f}" for x in p) for s, p in atoms]
    if kpts == "gamma":
        lines.append("K_POINTS gamma")
    elif isinstance(kpts, str):
        lines.append(kpts)
    else:
        k = kpts or ([1, 1, 1] if st["kind"] == "mol" else kmesh(cell, kdens))
        lines += ["K_POINTS automatic", f"{k[0]} {k[1]} {k[2]} 0 0 0"]
    (path / "job.in").write_text("\n".join(lines) + "\n")
    (path / "meta.json").write_text(json.dumps(dict(name=name, calc=calc, U=U, ecut=ecut, kdens=kdens,
                                                    kind=st["kind"], nat=len(atoms)), indent=1))

# ---------------------------------------------------------------- parsing
RY = 13.605693122994
def parse(out: Path):
    t = out.read_text(errors="ignore") if out.exists() else ""
    E = [float(x) for x in re.findall(r"^!\s+total energy\s+=\s+(-?\d+\.\d+) Ry", t, re.M)]
    mag = re.findall(r"total magnetization\s+=\s+(-?\d+\.\d+)", t)
    absmag = re.findall(r"absolute magnetization\s+=\s+(-?\d+\.\d+)", t)
    gap = re.findall(r"highest occupied, lowest unoccupied level \(ev\):\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)", t)
    vol = re.findall(r"unit-cell volume\s+=\s+(\d+\.\d+) \(a\.u\.\)\^3", t)
    newvol = re.findall(r"new unit-cell volume =\s+(\d+\.\d+) a\.u\.\^3", t)
    wall = re.findall(r"PWSCF\s+:.*CPU\s+(.+) WALL", t)
    cellp = re.findall(r"CELL_PARAMETERS \(alat=\s*(\d+\.\d+)\)\n(.+)\n(.+)\n(.+)", t)
    fe = re.findall(r"Final (?:enthalpy|energy)\s+=\s+(-?\d+\.\d+) Ry", t)
    return dict(E_Ry=float(fe[-1]) if fe else (E[-1] if E else None), n_scf=len(E), converged_relax="End final coordinates" in t or
                "bfgs converged" in t, job_done="JOB DONE" in t, total_mag=float(mag[-1]) if mag else None,
                abs_mag=float(absmag[-1]) if absmag else None,
                homo_lumo=[float(gap[-1][0]), float(gap[-1][1])] if gap else None,
                vol_bohr3=float(newvol[-1]) if newvol else (float(vol[-1]) if vol else None),
                wall=wall[-1].strip() if wall else None, error=("Error" in t or "%%%%" in t))

def band_gap(out: Path):
    """Spin-resolved gap from the LAST printed band block (SCF k-mesh, so an estimate of the true gap), by electron
    counting: n_up = (N + M)/2, n_dn = (N - M)/2 with M the total moment rounded to an integer (FM insulators).
    Returns dict(gap_eV, vbm_eV, cbm_eV, n_up, n_dn) or None if bands are missing / moment is not integral."""
    t = out.read_text(errors="ignore") if out.exists() else ""
    if "End of self-consistent calculation" not in t: return None
    blk = t.split("End of self-consistent calculation")[-1]
    N = re.findall(r"number of electrons\s+=\s+(\d+\.\d+)", t); M = re.findall(r"total magnetization\s+=\s+(-?\d+\.\d+)", blk)
    if not N or not M: return None
    N = float(N[-1]); Mf = float(M[-1]); Mi = round(Mf)
    if abs(Mf - Mi) > 0.05: return None
    n = {"up": int(round((N + Mi) / 2)), "dn": int(round((N - Mi) / 2))}
    parts = blk.split("SPIN DOWN")
    if len(parts) != 2: return None
    vbm, cbm = -1e9, 1e9
    for spin, txt in zip(("up", "dn"), parts):
        txt = re.split(r"the Fermi energy|highest occupied", txt)[0]
        for b in re.findall(r"bands \(ev\):\s*\n\s*\n(.*?)(?:\n\s*\n|$)", txt, re.S):
            e = [float(x) for x in re.findall(r"-?\d+\.\d+", b)]
            if len(e) <= n[spin]: return None
            vbm = max(vbm, e[n[spin] - 1]); cbm = min(cbm, e[n[spin]])
    return dict(gap_eV=round(cbm - vbm, 3), vbm_eV=round(vbm, 3), cbm_eV=round(cbm, 3), n_up=n["up"], n_dn=n["dn"])

# ---------------------------------------------------------------- runner
def run_job(d: Path, np_=4, exe="pw.x", args=""):
    if (d / "STATUS").exists() and (d / "STATUS").read_text().startswith("DONE"):   # incl. "DONE bfgs-converged"
        return d.name, "SKIP"
    env = dict(os.environ, OMP_NUM_THREADS="1", PATH=f"{QE}:{os.environ['PATH']}")
    cmd = f'"{QE}/mpirun" --oversubscribe -np {np_} "{QE}/{exe}" {args} -in job.in > job.out 2>&1'
    (d / "cmd.txt").write_text(cmd + "\n")
    t0 = time.time()
    r = subprocess.run(cmd, shell=True, cwd=d, env=env)
    dt = time.time() - t0
    txt = (d / "job.out").read_text(errors="ignore")
    ok = r.returncode == 0 and "JOB DONE" in txt
    bfgs_ok = (not ok) and "End final coordinates" in txt      # known QE 7.6 (conda) crash in the optional final SCF
    (d / "wall.txt").write_text(f"{dt:.1f}\n")
    (d / "STATUS").write_text("DONE\n" if ok else ("DONE bfgs-converged; final SCF crashed (QE 7.6 conda bug)\n" if bfgs_ok
                              else f"FAILED rc={r.returncode}\n"))
    ok = ok or bfgs_ok
    shutil.rmtree(d / "tmp", ignore_errors=True) if exe == "pw.x" and "keep" not in d.name else None
    with open(RUNS / "campaign.log", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {d.relative_to(RUNS)} {'DONE' if ok else 'FAILED'} {dt:.1f}s\n")
    return d.name, "DONE" if ok else "FAILED"

def run_stage(stage, lanes=2, np_=4, nk=1):
    lock = RUNS / f".{stage}.lock"
    if lock.exists():
        pid = int(lock.read_text().strip() or 0)
        try:
            os.kill(pid, 0); sys.exit(f"stage {stage} already running (pid {pid})")
        except OSError:
            pass
    lock.write_text(str(os.getpid()))
    jobs = sorted(p.parent for p in (RUNS / stage).glob("*/job.in"))
    with ThreadPoolExecutor(max_workers=lanes) as ex:
        for name, st in ex.map(lambda d: run_job(d, np_, args=f"-nk {nk}" if nk > 1 else ""), jobs):
            print(stage, name, st, flush=True)
    lock.unlink(missing_ok=True)

# ---------------------------------------------------------------- stages
def write_conv():
    S = structures()
    for ec in (30, 35, 40, 45, 50, 60, 70):
        for nm in ("NaCl_rs", "NiCl2_FM"):
            write_input(RUNS / "conv" / f"{nm}_ecut{ec}", nm, S[nm], calc="scf", U=4.0 if "Ni" in nm else 0,
                        ecut=(ec, 8 * ec), kdens=15, conv_thr=1e-8)
    for nm, kds in (("NaCl_rs", (10, 15, 20, 25, 30)), ("NiCl2_FM", (10, 15, 20, 25, 30)),
                    ("Ni_fcc", (20, 30, 40, 50, 60))):
        for kd in kds:
            write_input(RUNS / "conv" / f"{nm}_k{kd}", nm, S[nm], calc="scf", U=4.0 if "Cl2" in nm else 0,
                        ecut=ECUT, kdens=kd, conv_thr=1e-8)

def write_relax():
    S = structures()
    for nm in ("Na_bcc", "NaCl_rs", "Fe_bcc", "Ni_fcc", "Co_hcp"):
        write_input(RUNS / "relax" / nm, nm, S[nm], calc="vc-relax", conv_thr=1e-8)
    write_input(RUNS / "relax" / "Cl2_box", "Cl2_box", S["Cl2_box"], calc="relax")
    for m in TM:
        for U in (0.0, 4.0):     # vc-relax at two U values; U-scan done as fixed-geometry SCF (stage 'uscan')
            write_input(RUNS / "relax" / f"{m}Cl2_FM_U{U:.0f}", f"{m}Cl2", S[f"{m}Cl2_FM"], calc="vc-relax", U=U, kdens=15, conv_thr=1e-7)

def write_uscan():
    """Fixed-geometry SCF at every U on the U=4 eV relaxed cell (and on the U=0 cell for U=0) -> voltage sensitivity to U."""
    for m in TM:
        for geomU in (0.0, 4.0):
            try:
                cell, atoms = relaxed_geometry(RUNS / "relax" / f"{m}Cl2_FM_U{geomU:.0f}")
            except Exception:
                print("skip (relax not converged):", m, geomU); continue
            st = dict(cell=cell, atoms=atoms, kind="tm")
            for U in U_SCAN:
                write_input(RUNS / "uscan" / f"{m}Cl2_geomU{geomU:.0f}_U{U:.0f}", f"{m}Cl2", st, calc="scf", U=U, kdens=20)

def relaxed_geometry(job: Path):
    """Return (cell, atoms) from the final coordinates of a vc-relax output."""
    t = (job / "job.out").read_text()
    if "Begin final coordinates" not in t:
        raise ValueError(f"{job.name}: vc-relax has not converged (no final coordinates)")
    blk = t.split("Begin final coordinates")[-1]
    m = re.search(r"CELL_PARAMETERS \((alat=\s*([\d.]+)|angstrom)\)\n(.+)\n(.+)\n(.+)", blk)
    rows = [list(map(float, m.group(i).split())) for i in (3, 4, 5)]
    cell = np.array(rows) * (float(m.group(2)) * 0.529177210903 if m.group(2) else 1.0)
    pos = re.search(r"ATOMIC_POSITIONS \(crystal\)\n(.*?)\nEnd final", blk, re.S).group(1).strip().splitlines()
    atoms = [(l.split()[0], tuple(map(float, l.split()[1:4]))) for l in pos]
    return cell, atoms

def write_mag():
    """FM vs interlayer-AFM at the FM-relaxed geometry (U = 0 and 4 eV)."""
    S = structures()
    for m in TM:
        for U in (0.0, 4.0):
            src = RUNS / "relax" / f"{m}Cl2_FM_U{U:.0f}"
            try:
                cell, atoms = relaxed_geometry(src)
            except Exception:
                print("skip (relax not converged):", m, U); continue
            R = cell; T = np.array([[1, -1, 0], [0, 1, -1], [0, 0, 2]]); sup = T @ R; inv = np.linalg.inv(sup)
            cart = []
            for k, shift in enumerate((np.zeros(3), R[2])):
                for s, f in atoms:
                    lab = (m + str(k + 1)) if s == m else s
                    cart.append((lab, np.mod((np.array(f) @ R + shift) @ inv, 1.0)))
            st = dict(cell=sup, atoms=cart, kind="tm_afm")
            write_input(RUNS / "mag" / f"{m}Cl2_AFM_U{U:.0f}", f"{m}Cl2afm", st, calc="scf", U=U)
            stf = dict(cell=sup, atoms=[(m if s.startswith(m) else s, p) for s, p in cart], kind="tm")
            write_input(RUNS / "mag" / f"{m}Cl2_FMsup_U{U:.0f}", f"{m}Cl2fms", stf, calc="scf", U=U)

def write_dos():
    """PDOS: SCF on a denser mesh (k 30 A) with 40 bands at the relaxed geometry, kept tmp/ for projwfc.x (projwfc.in)."""
    for m in TM:
        for U in (0.0, 4.0):
            try:
                cell, atoms = relaxed_geometry(RUNS / "relax" / f"{m}Cl2_FM_U{U:.0f}")
            except Exception:
                print("skip (relax not converged):", m, U); continue
            d = RUNS / "dos" / f"{m}Cl2_U{U:.0f}_keep"
            write_input(d, f"{m}Cl2dos", dict(cell=cell, atoms=atoms, kind="tm"), calc="scf", U=U, kdens=30, nbnd=40)
            (d / "projwfc.in").write_text(f"&projwfc\n  prefix='{m}Cl2dos', outdir='./tmp', filpdos='pdos',\n"
                                          "  DeltaE=0.02, degauss=0.01, ngauss=0\n/\n")

if __name__ == "__main__":
    act, stage = sys.argv[1], sys.argv[2]
    lanes = int(sys.argv[sys.argv.index("--lanes") + 1]) if "--lanes" in sys.argv else 2
    np_ = int(sys.argv[sys.argv.index("--np") + 1]) if "--np" in sys.argv else 4
    nk = int(sys.argv[sys.argv.index("--nk") + 1]) if "--nk" in sys.argv else 1   # k-point pools (EC2: 32 cores)
    RUNS.mkdir(exist_ok=True)
    if act == "write":
        {"conv": write_conv, "relax": write_relax, "mag": write_mag, "uscan": write_uscan, "dos": write_dos}[stage]()
        print("written", stage, len(list((RUNS / stage).glob("*/job.in"))))
    elif act == "run":
        run_stage(stage, lanes, np_, nk)
