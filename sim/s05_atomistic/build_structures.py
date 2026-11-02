"""S5 step 1: build every structure used by the uMLIP screen (Mac) and the DFT+U check (EC2).

Sources: Materials Project via its public OPTIMADE endpoint (no API key), or built from
literature-standard prototypes where MP lacks the topotactic phase. Writes CIF + JSON in structures/.
"""
import json, pathlib, urllib.parse, urllib.request
import numpy as np
from pymatgen.core import Structure, Lattice
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
import sys; sys.path.insert(0, "/Volumes/Aditya ssd/Salt-Battery-Lab")
from params.product_params import R0

OUT = pathlib.Path(__file__).parent / "structures"; OUT.mkdir(exist_ok=True)
OPT = "https://optimade.materialsproject.org/v1/structures"
log = {}

def mp_fetch(formula_reduced, max_sites=60, prefer=None):
    q = urllib.parse.urlencode({"filter": f'chemical_formula_reduced="{formula_reduced}"',
                                "response_fields": "lattice_vectors,cartesian_site_positions,species_at_sites,nsites,_mp_stability",
                                "page_limit": 50})
    import requests
    r = requests.get(f"{OPT}?{q}", timeout=90); r.raise_for_status(); d = r.json()
    cands = []
    for x in d["data"]:
        a = x["attributes"]
        if a["nsites"] > max_sites: continue
        st = (a.get("_mp_stability") or {}).get("gga_gga+u") or (a.get("_mp_stability") or {}).get("gga_gga+u_r2scan") or {}
        eh = st.get("energy_above_hull", 9.9)
        cands.append((eh, x["id"], a))
    cands.sort(key=lambda c: c[0])
    if prefer:
        cands = [c for c in cands if c[1] == prefer] or cands
    eh, mid, a = cands[0]
    s = Structure(Lattice(a["lattice_vectors"]), a["species_at_sites"], a["cartesian_site_positions"], coords_are_cartesian=True)
    return s, mid, eh

def save(name, s, src):
    s = s.get_sorted_structure()
    s.to(filename=str(OUT / f"{name}.cif"))
    (OUT / f"{name}.json").write_text(json.dumps(s.as_dict()))
    sg = SpacegroupAnalyzer(s, symprec=0.1).get_space_group_symbol()
    log[name] = {"formula": s.composition.reduced_formula, "nsites": len(s), "spacegroup": sg, "source": src,
                 "volume_A3": round(s.volume, 2)}
    print(f"{name:28s} {s.composition.formula:28s} n={len(s):3d} {sg:10s} {src}")

# --- Validation set ---------------------------------------------------------------------
lfp, mid, eh = mp_fetch("FeLiO4P", 30); save("LiFePO4", lfp, f"MP {mid} (Ehull {eh:.3f})")
fp = lfp.copy(); fp.remove_species(["Li"]); save("FePO4_olivine", fp, f"topotactic: {mid} minus Li")
nfp = lfp.copy(); nfp.replace_species({"Li": "Na"}); nfp.scale_lattice(lfp.volume * 1.10)
save("NaFePO4_olivine", nfp, f"topotactic: {mid} Li->Na, volume +10% (relaxed later)")

lmo, mid, eh = mp_fetch("LiMn2O4", 60)
lmo_p = SpacegroupAnalyzer(lmo, symprec=0.1).get_primitive_standard_structure()
save("LiMn2O4", lmo_p, f"MP {mid} (Ehull {eh:.3f}) primitive")
lam = lmo_p.copy(); lam.remove_species(["Li"]); save("lambda_MnO2", lam, f"topotactic: {mid} minus Li")

ntp, mid, eh = mp_fetch("NaO12P3Ti2", 40, prefer="mp-6761"); save("NaTi2PO43", ntp, f"MP {mid} (Ehull {eh:.3f})")
try:
    n3tp, mid3, eh3 = mp_fetch("Na3O12P3Ti2", 50); save("Na3Ti2PO43", n3tp, f"MP {mid3} (Ehull {eh3:.3f})")
except Exception as e:
    print("Na3Ti2(PO4)3 fetch failed:", e)

try:
    pba, midp, ehp = mp_fetch("C6FeMnN6Na2", 40); src = f"MP {midp} (Ehull {ehp:.3f})"
except Exception:
    # MP has no Na2MnFe(CN)6 entry: cubic Prussian-white prototype (Fm-3m), Fe-C 1.90 A, C-N 1.15 A, Na in 8c
    a = 10.5
    pba = Structure.from_spacegroup("Fm-3m", Lattice.cubic(a), ["Fe", "Mn", "C", "N", "Na"],
                                    [[0, 0, 0], [.5, .5, .5], [1.90 / a, 0, 0], [3.05 / a, 0, 0], [.25, .25, .25]]).get_primitive_structure()
    src = "built: cubic Fm-3m Prussian-white prototype a=10.5 A (MP has no entry); real material is rhombohedral"
save("Na2MnFeCN6", pba, src)
mnfe = pba.copy(); mnfe.remove_species(["Na"]); save("MnFeCN6", mnfe, "topotactic: Na2MnFe(CN)6 minus Na")

# --- Metal references ---------------------------------------------------------------------
save("Li_bcc", Structure(Lattice.cubic(3.44), ["Li", "Li"], [[0, 0, 0], [.5, .5, .5]]).get_primitive_structure(), "bcc a=3.44 A")
save("Na_bcc", Structure(Lattice.cubic(4.23), ["Na", "Na"], [[0, 0, 0], [.5, .5, .5]]).get_primitive_structure(), "bcc a=4.23 A")
save("MnO_rocksalt", Structure.from_spacegroup("Fm-3m", Lattice.cubic(4.445), ["Mn", "O"], [[0, 0, 0], [.5, .5, .5]]).get_primitive_structure(),
     "rocksalt a=4.445 A (mu_Mn reference for vacancy proxy)")

# --- Birnessite model: 3x3 hexagonal delta-MnO2 layer, one layer per cell -----------------------
# Mn-O 1.92 A edge-sharing octahedra (a_hex = 2.85 A), interlayer start = paper d001 7.19 A.
a_hex, c0 = 2.85, R0["d001_pristine"].value
dz = np.sqrt(1.92**2 - (a_hex / np.sqrt(3))**2)
N = 3
lat = Lattice.hexagonal(a_hex * N, c0)
species, frac = [], []
for i in range(N):
    for j in range(N):
        species += ["Mn", "O", "O"]
        frac += [[i / N, j / N, 0.0], [(i + 1/3) / N, (j + 2/3) / N, dz / c0], [(i + 2/3) / N, (j + 1/3) / N, -dz / c0]]
layer = Structure(lat, species, frac)
# interlayer sites in the mid-plane, on a 3x3 grid shifted off the Mn columns
sites = [[(i + 1/3) / N, (j + 2/3) / N, 0.5] for i in range(N) for j in range(N)]
rng = np.random.default_rng(7)
# water order: 6 H2O fixed (0.67 per Mn ~ paper 0.63); Na count varies -> x = 1/9, 3/9, 5/9
NA_SITES = {1: [0], 3: [0, 4, 8], 5: [0, 2, 4, 6, 8]}
def birnessite(n_na, n_w=6):
    s = layer.copy()
    na_idx = NA_SITES[n_na]
    w_idx = [k for k in range(9) if k not in na_idx][:n_w]
    if len(w_idx) < n_w:  # x=5/9 leaves only 4 grid sites; place extra water on a shifted grid
        extra = [[(i + 2/3) / N, (j + 1/3) / N, 0.5] for i in range(N) for j in range(N)]
        w_pos = [sites[k] for k in w_idx] + extra[: n_w - len(w_idx)]
    else:
        w_pos = [sites[k] for k in w_idx]
    for k in na_idx:
        s.append("Na", sites[k])
    for p in w_pos:
        o = lat.get_cartesian_coords(p)
        th = rng.uniform(0, 2 * np.pi)
        h1 = o + 0.9572 * np.array([np.cos(th) * np.sin(0.9119), np.sin(th) * np.sin(0.9119), np.cos(0.9119)])
        h2 = o + 0.9572 * np.array([np.cos(th) * np.sin(0.9119), np.sin(th) * np.sin(0.9119), -np.cos(0.9119)])
        s.append("O", o, coords_are_cartesian=True); s.append("H", h1, coords_are_cartesian=True); s.append("H", h2, coords_are_cartesian=True)
    return s
for n in (1, 3, 5):
    save(f"birnessite_Na{n}_9", birnessite(n), f"built: 3x3 delta-MnO2 layer + {n} Na + 6 H2O, c0={c0} A (paper d001)")
# dry layered MnO2 (no Na, no water) for reference
save("MnO2_layer_dry", layer.copy(), "built: 3x3 delta-MnO2 layer, no interlayer species")

(OUT / "structures_log.json").write_text(json.dumps(log, indent=2))
