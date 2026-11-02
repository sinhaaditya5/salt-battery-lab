"""S6: write Quantum ESPRESSO (pw.x 7.6, conda-forge linux-aarch64 build; Ubuntu 24.04 apt QE 6.7 aborts with a fortify buffer-overflow) inputs from uMLIP-relaxed structures.

Each job is a folder jobs/<lane>_<name>/ with pw.in and a JOB file (metadata). The EC2 queue runner
executes them. All results are labelled "[SIM] DFT+U (PBE+U, GBRV USPP), screening settings".

Usage: python make_qe_inputs.py [batch]   batch in {relax, neb}  (default relax)
"""
import json, math, pathlib, sys
import numpy as np
from pymatgen.core import Structure
sys.path.insert(0, "/Volumes/Aditya ssd/Salt-Battery-Lab")
from params.product_params import DFT

HERE = pathlib.Path(__file__).parent
S5 = HERE.parent / "s05_atomistic"
JOBS = HERE / "jobs"; JOBS.mkdir(exist_ok=True)
PSEUDO = {
    "Li": "li_pbe_v1.4.uspp.F.UPF", "Na": "na_pbe_v1.5.uspp.F.UPF", "Mn": "mn_pbe_v1.5.uspp.F.UPF",
    "Fe": "fe_pbe_v1.5.uspp.F.UPF", "Ti": "ti_pbe_v1.4.uspp.F.UPF", "P": "p_pbe_v1.5.uspp.F.UPF",
    "O": "o_pbe_v1.2.uspp.F.UPF", "H": "h_pbe_v1.4.uspp.F.UPF", "C": "c_pbe_v1.2.uspp.F.UPF",
    "N": "n_pbe_v1.2.uspp.F.UPF",
}
MASS = {"Li": 6.94, "Na": 22.99, "Mn": 54.938, "Fe": 55.845, "Ti": 47.867, "P": 30.974, "O": 15.999,
        "H": 1.008, "C": 12.011, "N": 14.007}


def kgrid(s, spacing):
    rec = s.lattice.reciprocal_lattice.abc  # |b_i| including 2*pi (VASP KSPACING convention)
    return [max(1, math.ceil(b / spacing)) for b in rec]


def species_list(s, split_fe_mn_pba=False):
    """Return ordered species labels. In Prussian-blue analogues Fe(C-bonded, low spin) and Mn(N-bonded,
    high spin) need distinct starting magnetisation; labels are already element-unique there."""
    seen = []
    for site in s:
        e = site.specie.symbol
        if e not in seen:
            seen.append(e)
    return seen


def write_pw(name, s, calc="vc-relax", spin=True, hubbard=True, kspacing=0.35, vdw=None, magmom=None,
             cell_dofree="all", lane="A", note="", extra_system=None, kpts=None):
    d = JOBS / f"{lane}_{name}"; d.mkdir(exist_ok=True)
    sp = species_list(s)
    k = kpts or kgrid(s, kspacing)
    magmom = magmom or {"Mn": 0.6, "Fe": 0.8, "Ti": 0.1}
    lines = ["&CONTROL", f"  calculation = '{calc}'", f"  prefix = '{name}'", "  outdir = './tmp'",
             "  pseudo_dir = '/work/pseudo'", "  tprnfor = .true.", "  tstress = .true.",
             "  forc_conv_thr = 1.0d-3", "  etot_conv_thr = 1.0d-4", "  nstep = 150", "  disk_io = 'low'",
             "  max_seconds = 160000", "/", "&SYSTEM", "  ibrav = 0", f"  nat = {len(s)}", f"  ntyp = {len(sp)}",
             f"  ecutwfc = {DFT['ecutwfc_Ry']}", f"  ecutrho = {DFT['ecutrho_Ry']}",
             "  occupations = 'smearing'", f"  smearing = '{DFT['smearing']}'", f"  degauss = {DFT['degauss_Ry']}"]
    if spin:
        lines.append("  nspin = 2")
        for i, e in enumerate(sp, 1):
            lines.append(f"  starting_magnetization({i}) = {magmom.get(e, 0.0)}")
    # QE >= 7.1 syntax: Hubbard parameters go in the HUBBARD card (written after K_POINTS)
    hub_card = []
    if hubbard and any(e in DFT["hubbard_U_eV"] for e in sp):
        hub_card = ["HUBBARD {atomic}"] + [f"  U {e}-3d {DFT['hubbard_U_eV'][e]}" for e in sp if e in DFT["hubbard_U_eV"]]
    if vdw:
        lines.append(f"  vdw_corr = '{vdw}'")
    for kk, vv in (extra_system or {}).items():
        lines.append(f"  {kk} = {vv}")
    lines += ["/", "&ELECTRONS", "  conv_thr = 1.0d-7", "  mixing_beta = 0.3", "  electron_maxstep = 250",
              "  mixing_mode = 'local-TF'" if len(s) > 30 else "  mixing_mode = 'plain'", "/"]
    if calc in ("relax", "vc-relax"):
        lines += ["&IONS", "  ion_dynamics = 'bfgs'", "/"]
    if calc == "vc-relax":
        lines += ["&CELL", "  cell_dynamics = 'bfgs'", "  press_conv_thr = 0.5", f"  cell_dofree = '{cell_dofree}'", "/"]
    lines.append("ATOMIC_SPECIES")
    for e in sp:
        lines.append(f"  {e} {MASS[e]} {PSEUDO[e]}")
    lines.append("CELL_PARAMETERS angstrom")
    for v in s.lattice.matrix:
        lines.append("  " + " ".join(f"{x:14.8f}" for x in v))
    lines.append("ATOMIC_POSITIONS angstrom")
    for site in s:
        lines.append(f"  {site.specie.symbol} " + " ".join(f"{x:14.8f}" for x in site.coords))
    lines.append("K_POINTS automatic")
    lines.append("  " + " ".join(map(str, k)) + " 0 0 0")
    lines += hub_card
    (d / "pw.in").write_text("\n".join(lines) + "\n")
    meta = {"name": name, "calc": calc, "natoms": len(s), "formula": s.composition.formula, "kpts": k,
            "spin": spin, "hubbard": hubbard, "vdw": vdw, "lane": lane, "note": note}
    (d / "JOB.json").write_text(json.dumps(meta, indent=2))
    (d / "READY").write_text("")
    return meta


def load(name, model="mace_mp0b3"):
    p = S5 / "out" / f"relaxed_{model}" / f"{name}.json"
    if not p.exists():
        p = S5 / "structures" / f"{name}.json"
    return Structure.from_dict(json.loads(p.read_text()))


def relax_batch():
    metas = []
    # --- metal references (no spin, no U, dense k) ---
    for m in ("Li_bcc", "Na_bcc"):
        metas.append(write_pw(m, load(m), spin=False, hubbard=False, kspacing=0.12, lane="A",
                              note="alkali metal reference for voltages"))
    # --- validation set: PBE+U, no dispersion (consistent with MP-style voltage benchmarks) ---
    val = ["lambda_MnO2", "LiMn2O4", "FePO4_olivine", "LiFePO4", "NaFePO4_olivine", "NaTi2PO43", "Na3Ti2PO43"]
    for i, n in enumerate(val):
        metas.append(write_pw(n, load(n), lane="AB"[i % 2], kspacing=0.45, note="validation voltage end member"))
    # Prussian-white analogue: Fe(II) low-spin (C-bonded) -> start 0; Mn(II) high-spin (N-bonded) -> start 0.8
    for n in ("MnFeCN6", "Na2MnFeCN6"):
        metas.append(write_pw(n, load(n), lane="B", magmom={"Mn": 0.8, "Fe": 0.0}, kspacing=0.45,
                              note="candidate-C cathode end member (cubic prototype)"))
    # --- birnessite (R0/R1 cathode): PBE+U+D3 vc-relax, interlayer spacing vs XRD + voltage ---
    for n, lane in (("birnessite_Na3_9", "C"), ("birnessite_Na5_9", "D"), ("birnessite_Na1_9", "C")):
        metas.append(write_pw(n, load(n), vdw="grimme-d3", kpts=[2, 2, 1], lane=lane,
                              note="birnessite interlayer + voltage (PBE+U+D3)"))
    # --- Mn-dissolution proxy: Mn-vacancy energy at fixed uMLIP cell, pristine vs defect ---
    for n in ("birnessite_Na3_9",):
        s = load(n)
        metas.append(write_pw(n + "_fixcell", s, calc="relax", vdw="grimme-d3", kpts=[2, 2, 1], lane="D",
                              note="pristine at fixed uMLIP cell (vacancy reference)"))
        sv = s.copy()
        mn_idx = [i for i, site in enumerate(sv) if site.specie.symbol == "Mn"]
        sv.remove_sites([mn_idx[0]])
        metas.append(write_pw(n + "_VMn", sv, calc="relax", vdw="grimme-d3", kpts=[2, 2, 1], lane="D",
                              note="Mn vacancy at fixed uMLIP cell (dissolution proxy)"))
    (HERE / "jobs_manifest_relax.json").write_text(json.dumps(metas, indent=2))
    print(f"wrote {len(metas)} jobs")
    for m in metas:
        print(f"  {m['lane']:2s} {m['name']:28s} {m['calc']:9s} n={m['natoms']:3d} k={m['kpts']} vdw={m['vdw']}")




def neb_batch(model="mace_mp0b3"):
    """Static DFT+U SCF on every uMLIP NEB image -> DFT energy profile along the uMLIP path."""
    metas = []
    nd = S5 / "out" / f"neb_{model}"
    for tag, lane, vdw in (("LiFePO4_b", "A", None), ("NaFePO4_b", "B", None), ("birnessite_Na", "C", "grimme-d3")):
        for k in range(7):
            p = nd / f"{tag}_img{k}.cif"
            if not p.exists():
                continue
            s = Structure.from_file(str(p))
            kw = dict(calc="scf", vdw=vdw, lane=lane, note=f"static DFT+U on {model} NEB image {k} of {tag}")
            if tag.startswith("birn"):
                kw["kpts"] = [2, 2, 1]
            else:
                kw["kspacing"] = 0.45
            metas.append(write_pw(f"neb_{tag}_img{k}", s, **kw))
    (HERE / "jobs_manifest_neb.json").write_text(json.dumps(metas, indent=2))
    print(f"wrote {len(metas)} NEB image jobs")


if __name__ == "__main__":
    batch = sys.argv[1] if len(sys.argv) > 1 else "relax"
    {"relax": relax_batch, "neb": neb_batch}[batch]()
