"""S5 step 2: relax every structure with universal ML interatomic potentials (Mac CPU).

Usage: python mlip_relax.py <model>   with model in {mace_mp0b3, mace_mp0, chgnet}
Writes out/relax_<model>.json (energies, volumes, lattice) and relaxed CIFs in out/relaxed_<model>/.
Label for all results: [SIM] uMLIP screen, not DFT-verified.
"""
import json, pathlib, sys, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import torch
from pymatgen.core import Structure
from pymatgen.io.ase import AseAtomsAdaptor
from ase.filters import FrechetCellFilter
from ase.optimize import FIRE, BFGS

HERE = pathlib.Path(__file__).parent
LAB = HERE.parents[1]
MODEL = sys.argv[1] if len(sys.argv) > 1 else "mace_mp0b3"
torch.set_num_threads(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
if MODEL.startswith("mace"): torch.set_default_dtype(torch.float64)


def get_calc(model):
    if model.startswith("mace"):
        from mace.calculators import mace_mp
        path = {"mace_mp0b3": "mace-mp-0b3-medium.model", "mace_mp0": "mace-mp-0-medium.model"}[model]
        return mace_mp(model=str(LAB / "tools/models" / path), device="cpu", default_dtype="float64")
    if model == "chgnet":
        from chgnet.model.dynamics import CHGNetCalculator
        return CHGNetCalculator(use_device="cpu", check_cuda_mem=False)
    raise ValueError(model)


def relax(atoms, calc, fmax=0.03, steps=600, cell=True):
    atoms = atoms.copy(); atoms.calc = calc
    target = FrechetCellFilter(atoms) if cell else atoms
    opt = FIRE(target, logfile=None)
    opt.run(fmax=fmax, steps=steps)
    return atoms, opt.nsteps


def main():
    calc = get_calc(MODEL)
    sdir = HERE / "structures"
    outdir = HERE / "out" / f"relaxed_{MODEL}"; outdir.mkdir(parents=True, exist_ok=True)
    res = {}
    names = sorted(p.stem for p in sdir.glob("*.json") if p.stem != "structures_log")
    for name in names:
        s = Structure.from_dict(json.loads((sdir / f"{name}.json").read_text()))
        atoms = AseAtomsAdaptor.get_atoms(s)
        t0 = time.time()
        try:
            r, n = relax(atoms, calc)
            e = float(r.get_potential_energy())
            fmax = float(np.abs(r.get_forces()).max())
            rs = AseAtomsAdaptor.get_structure(r)
            rs.to(filename=str(outdir / f"{name}.cif"))
            (outdir / f"{name}.json").write_text(json.dumps(rs.as_dict(), default=float))
            res[name] = {"energy_eV": e, "natoms": len(r), "steps": n, "fmax_final": fmax,
                         "volume_A3": float(r.get_volume()), "cell_lengths": [float(x) for x in r.cell.lengths()],
                         "cell_angles": [float(x) for x in r.cell.angles()], "formula": rs.composition.formula,
                         "seconds": round(time.time() - t0, 1)}
            print(f"{MODEL} {name:24s} E={e:12.4f} eV  steps={n:4d}  fmax={fmax:.3f}  V={r.get_volume():8.2f}  {time.time()-t0:6.1f}s", flush=True)
        except Exception as ex:  # record, never hide
            res[name] = {"error": repr(ex)}
            print(f"{MODEL} {name}: ERROR {ex!r}", flush=True)
    (HERE / "out" / f"relax_{MODEL}.json").write_text(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
