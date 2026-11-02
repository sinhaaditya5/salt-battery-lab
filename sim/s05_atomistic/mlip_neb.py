"""S5 step 3: climbing-image NEB migration barriers with uMLIPs (Mac CPU), and DFT static-image export.

Paths
  LiFePO4_b      Li vacancy hop along the 1D olivine channel (validation vs GGA literature 0.27 eV)
  NaFePO4_b      Na analogue (olivine NaFePO4)
  birnessite_Na  Na hop between neighbouring interlayer sites in Na(1/9)MnO2.(2/3)H2O (R0/R1 cathode)
  PBA_Na         Na vacancy hop between 8c cages in cubic Na2MnFe(CN)6 (candidate C cathode)

Usage: python mlip_neb.py <model> [threads]
Label: [SIM] uMLIP screen, not DFT-verified (until S6 static-image DFT confirms).
"""
import json, pathlib, sys, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import torch
from pymatgen.core import Structure
from pymatgen.io.ase import AseAtomsAdaptor
from ase.mep import NEB
from ase.optimize import FIRE
from ase.io import write

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from mlip_relax import get_calc  # noqa: E402

MODEL = sys.argv[1] if len(sys.argv) > 1 else "mace_mp0b3"
torch.set_num_threads(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
if MODEL.startswith("mace"):
    torch.set_default_dtype(torch.float64)
NIMG = 7
OUT = HERE / "out" / f"neb_{MODEL}"; OUT.mkdir(parents=True, exist_ok=True)


def relaxed(name):
    return Structure.from_dict(json.loads((HERE / "out" / f"relaxed_{MODEL}" / f"{name}.json").read_text()))


def relax_fixed(atoms, calc, fmax=0.03, steps=800):
    atoms = atoms.copy(); atoms.calc = calc
    FIRE(atoms, logfile=None).run(fmax=fmax, steps=steps)
    return atoms


def vacancy_hop(s, ion, sc):
    """Supercell, remove one ion, the nearest same-species neighbour hops into the vacancy."""
    s = s.copy(); s.make_supercell(sc)
    idx = [i for i, x in enumerate(s) if x.specie.symbol == ion]
    i0 = idx[0]
    d = [(s.get_distance(i0, j), j) for j in idx if j != i0]
    dmin, j = min(d)
    vac_frac = s[i0].frac_coords
    ini = s.copy(); ini.remove_sites([i0])
    fin = ini.copy()
    jj = j - (1 if j > i0 else 0)
    fin.replace(jj, ion, coords=vac_frac)
    return ini, fin, dmin


def birnessite_hop():
    s = relaxed("birnessite_Na1_9")
    na = [i for i, x in enumerate(s) if x.specie.symbol == "Na"][0]
    # candidate empty interlayer sites: original 3x3 mid-plane grid positions 7 and 8 (see build_structures.py)
    N = 3
    grid = [[(i + 1/3) / N, (j + 2/3) / N, 0.5] for i in range(N) for j in range(N)]
    best = None
    for k in (7, 8):
        target = np.array(grid[k], float)
        target[2] = s[na].frac_coords[2]
        dist = s.lattice.get_distance_and_image(s[na].frac_coords, target)[0]
        if best is None or dist < best[0]:
            best = (dist, target)
    fin = s.copy(); fin.replace(na, "Na", coords=best[1])
    return s.copy(), fin, best[0]


def run_neb(tag, ini, fin, calc, hop):
    a0 = relax_fixed(AseAtomsAdaptor.get_atoms(ini), calc)
    a1 = relax_fixed(AseAtomsAdaptor.get_atoms(fin), calc)
    images = [a0] + [a0.copy() for _ in range(NIMG - 2)] + [a1]
    for im in images:
        im.calc = get_calc(MODEL) if MODEL == "chgnet" else calc
    neb = NEB(images, climb=True, allow_shared_calculator=(MODEL != "chgnet"))
    neb.interpolate(method="idpp", mic=True)
    FIRE(neb, logfile=None).run(fmax=0.05, steps=600)
    E = np.array([im.get_potential_energy() for im in images])
    Ef = E - E[0]
    res = {"path": tag, "hop_distance_A": float(hop), "natoms": len(a0), "energies_rel_eV": Ef.tolist(),
           "barrier_forward_eV": float(Ef.max()), "barrier_backward_eV": float(Ef.max() - Ef[-1]),
           "endpoint_dE_eV": float(Ef[-1])}
    write(str(OUT / f"{tag}_images.extxyz"), images)
    for k, im in enumerate(images):
        AseAtomsAdaptor.get_structure(im).to(filename=str(OUT / f"{tag}_img{k}.cif"))
    print(f"{MODEL} {tag:16s} barrier={res['barrier_forward_eV']:.3f} eV  dE={res['endpoint_dE_eV']:.3f}  hop={hop:.2f} A", flush=True)
    return res


def main():
    calc = get_calc(MODEL)
    results = {}
    jobs = []
    lfp = relaxed("LiFePO4")
    # 2x supercell along the channel direction (the lattice vector closest to the Li-Li nearest-neighbour vector)
    def chan_sc(s, ion):
        idx = [i for i, x in enumerate(s) if x.specie.symbol == ion]
        _, img = s.lattice.get_distance_and_image(s[idx[0]].frac_coords, s[idx[1]].frac_coords)
        dists = [(s.get_distance(idx[0], j), j) for j in idx[1:]]
        d, j = min(dists)
        v = s[j].coords - s[idx[0]].coords
        ax = int(np.argmax([abs(np.dot(v, m)) / np.linalg.norm(m) for m in s.lattice.matrix]))
        sc = [1, 1, 1]; sc[ax] = 2
        return sc
    jobs.append(("LiFePO4_b", *vacancy_hop(lfp, "Li", chan_sc(lfp, "Li"))))
    nfp = relaxed("NaFePO4_olivine")
    jobs.append(("NaFePO4_b", *vacancy_hop(nfp, "Na", chan_sc(nfp, "Na"))))
    jobs.append(("birnessite_Na", *birnessite_hop()))
    pba = relaxed("Na2MnFeCN6")
    jobs.append(("PBA_Na", *vacancy_hop(pba, "Na", [[-1, 1, 1], [1, -1, 1], [1, 1, -1]])))  # conventional cubic cell
    for tag, ini, fin, hop in jobs:
        t0 = time.time()
        try:
            results[tag] = run_neb(tag, ini, fin, calc, hop)
            results[tag]["seconds"] = round(time.time() - t0, 1)
        except Exception as ex:
            results[tag] = {"error": repr(ex)}
            print(f"{MODEL} {tag}: ERROR {ex!r}", flush=True)
    (HERE / "out" / f"neb_{MODEL}.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
