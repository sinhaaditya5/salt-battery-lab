"""After the 2 Nov 06:25 UTC spot interruption: build jobs/ for instance 2.
Interrupted relaxations restart from the last geometry in the pulled pw.out; never-started jobs are copied;
finished/BFGS-converged jobs are kept in runs_i1/ and not re-run."""
import pathlib, shutil, sys, json
import re, numpy as np
from pymatgen.core import Structure, Lattice
BOHR = 0.529177210903


def last_geometry(path):
    """Last CELL_PARAMETERS + ATOMIC_POSITIONS printed by pw.x (vc-relax/relax), as a pymatgen Structure."""
    L = path.read_text(errors="ignore").splitlines()
    ci = [i for i, l in enumerate(L) if l.startswith("CELL_PARAMETERS")]
    pi = [i for i, l in enumerate(L) if l.startswith("ATOMIC_POSITIONS")]
    nsteps = len(pi)
    c = L[ci[-1]]
    cell = np.array([[float(x) for x in L[ci[-1] + k].split()] for k in (1, 2, 3)])
    if "alat" in c:
        alat = float(re.search(r"alat=\s*([0-9.]+)", c).group(1)) * BOHR
        cell = cell * alat
    elif "bohr" in c:
        cell = cell * BOHR
    sp, xyz = [], []
    for l in L[pi[-1] + 1:]:
        f = l.split()
        if len(f) < 4 or not re.match(r"^[A-Z][a-z]?$", f[0]):
            break
        sp.append(f[0]); xyz.append([float(v) for v in f[1:4]])
    assert "angstrom" in L[pi[-1]], L[pi[-1]]
    return Structure(Lattice(cell), sp, xyz, coords_are_cartesian=True), nsteps
from pymatgen.io.ase import AseAtomsAdaptor
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import make_qe_inputs as M
HERE = pathlib.Path(__file__).parent


def main():
    OLD_RUNS, OLD_JOBS, NEW = HERE / "runs_i1" / "jobs", HERE / "jobs_i1", HERE / "jobs"
    NEW.mkdir(exist_ok=True)
    M.JOBS = NEW
    restart = {  # dir name in old run -> (job name, kwargs, lane prefix)
        "C_1_birnessite_Na3_9": ("birnessite_Na3_9_r2", dict(vdw="grimme-d3", kpts=[2, 2, 1]), "C_1"),
        "D_1_birnessite_Na5_9": ("birnessite_Na5_9_r2", dict(vdw="grimme-d3", kpts=[2, 2, 1]), "D_1"),
        "A_Na3Ti2PO43": ("Na3Ti2PO43_r2", dict(kspacing=0.45), "A_1"),
        "B_NaTi2PO43": ("NaTi2PO43_r2", dict(kspacing=0.45), "B_1"),
    }
    log = {}
    for old, (name, kw, lane) in restart.items():
        s, nsteps = last_geometry(OLD_RUNS / old / "pw.out")
        meta = M.write_pw(name, s, lane=lane.split("_")[0], note=f"restart from ionic step {nsteps} of {old} (spot interruption)", **kw)
        src = NEW / f"{lane.split('_')[0]}_{name}"; dst = NEW / f"{lane}_{name}"
        src.rename(dst); log[old] = str(dst.name)
    for d in OLD_RUNS.iterdir():
        if d.name in restart or (d / "pw.out").exists():
            continue                       # finished / converged / restarted above
        shutil.copytree(OLD_JOBS / d.name, NEW / d.name)
        for f in ("RUNNING", "DONE", "FAILED"):
            (NEW / d.name / f).unlink(missing_ok=True)
        (NEW / d.name / "READY").write_text("")
        log[d.name] = "resubmitted"
    (HERE / "restart_log.json").write_text(json.dumps(log, indent=1))
    print(len(list(NEW.iterdir())), "jobs for instance 2"); print(json.dumps(log, indent=0)[:600])


if __name__ == "__main__":
    main()
