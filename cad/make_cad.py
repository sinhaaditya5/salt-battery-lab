"""Salt Battery R0 / R1 parametric CAD (build123d / OpenCascade).  CONCEPT - NOT FOR FABRICATION.

Every dimension comes from params/product_params.py, params/design.py and params/mech_params.py.

Assemblies                        STEP / STL / GLB name
  (a) R0 lab test cell             r0_test_cell      generic split-cell fixture (illustrative), 15 mm electrodes
  (b) R1 12 V monobloc             r1_monobloc       10 cells, full electrode stacks (all repeat units modelled)
      R1 single cell (one comp.)   r1_cell           one plate group + straps, for the cell detail
  (c) 48 V telecom module          r1_module48       4 monoblocs (exterior-only model) + BMS + DC/DC + fuse + cabling
  (d) UPS cabinet                  r1_ups_cabinet    8 shelves x 5 monoblocs (exterior-only model), master BMS, breaker

Outputs (cad/out/):
  <asm>.step  <asm>.stl  <asm>.glb      labelled, coloured assembly (named solids, nested sub-assemblies)
  <asm>_partlist.csv                    part, material, qty, unit mass, total mass, mass basis
  stl/<asm>/<variant>/<group>.stl       per-render-material meshes for Blender (variants: full, cut, exploded, open)
  cad_meta.json                         bounding boxes, variants, colours, callout anchors (mm) for renders/tests

Usage:  python cad/make_cad.py [--only r0,monobloc,cell,module,cabinet] [--no-glb]
"""
from __future__ import annotations

import csv
import json
import math
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))

from build123d import (Align, Axis, Box, Circle, Color, Compound, Cylinder, Helix, Location, Plane, Pos, Rot,  # noqa: E402
                       Solid, Sphere, Torus, export_gltf, export_step, export_stl, fillet, sweep)

from params.design import electrode_stack, monobloc  # noqa: E402
from params.mech_params import (CAB_MECH, CAB_SHELF_PITCH_MM, DENSITY, M48_MECH, M48_TRAY_CAD_MM, MB_MECH,  # noqa: E402
                                R0_COATING_UM, R0_FIXTURE, SCENE, VENT_ARRANGEMENT, monobloc_layout)
from params.product_params import BMS, CABINET, MAT, MODULE48, MONOBLOC, R0  # noqa: E402

OUT = LAB / "cad" / "out"
BOT = (Align.CENTER, Align.CENTER, Align.MIN)

# render-material groups -> RGB (also used as STEP colours)
GROUP_COLOR = {
    "case": (0.36, 0.40, 0.45), "lid": (0.30, 0.33, 0.37), "vent": (0.10, 0.42, 0.68), "epdm": (0.04, 0.04, 0.04),
    "frit": (0.93, 0.93, 0.89), "steel": (0.72, 0.74, 0.77), "terminal": (0.83, 0.82, 0.78),
    "red": (0.72, 0.08, 0.07), "black": (0.04, 0.04, 0.045), "label": (0.95, 0.95, 0.93),
    "cathode": (0.09, 0.07, 0.06), "anode": (0.24, 0.25, 0.27), "separator": (0.90, 0.93, 0.97),
    "electrolyte": (0.35, 0.62, 0.95),
    "tray": (0.62, 0.64, 0.66), "enclosure": (0.17, 0.18, 0.20), "cable_red": (0.70, 0.07, 0.06),
    "cable_black": (0.05, 0.05, 0.05), "sense": (0.90, 0.72, 0.18), "handle": (0.10, 0.10, 0.11),
    "cab_paint": (0.17, 0.19, 0.22), "cab_shelf": (0.70, 0.72, 0.74), "duct": (0.32, 0.33, 0.35),
    "breaker": (0.07, 0.07, 0.08), "accent": (0.90, 0.45, 0.10),
    "r0_steel": (0.75, 0.76, 0.78), "ptfe": (0.95, 0.95, 0.92), "peek": (0.74, 0.60, 0.40),
    "carbonpaper": (0.07, 0.07, 0.08), "coating": (0.16, 0.10, 0.07), "cellulose": (0.98, 0.97, 0.93),
    "spring": (0.62, 0.64, 0.68),
}


# ================================================================================================ helpers
def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=BOT)


def cyl(r, z0, z1, x=0.0, y=0.0):
    return Pos(x, y, z0) * Cylinder(r, z1 - z0, align=BOT)


def tube(ro, ri, z0, z1, x=0.0, y=0.0):
    return cyl(ro, z0, z1, x, y) - cyl(ri, z0 - 0.01, z1 + 0.01, x, y)


def rod(p0, p1, r):
    """Cylinder between two 3D points."""
    import numpy as np
    a, b = np.array(p0, float), np.array(p1, float)
    d = b - a
    h = float(np.linalg.norm(d))
    return Solid.make_cylinder(r, h, Plane(origin=tuple(a), z_dir=tuple(d / h)))


def cable(points, r):
    """Cable as cylinders between waypoints + spheres at the joints (robust, no sweep)."""
    s = None
    for p0, p1 in zip(points[:-1], points[1:]):
        seg = rod(p0, p1, r)
        s = seg if s is None else s + seg
    for p in points[1:-1]:
        s = s + Pos(*p) * Sphere(r)
    return s


@dataclass
class Part:
    name: str
    ptype: str           # part-list row key
    material: str        # DENSITY key (or descriptive)
    group: str           # render group
    shape: object        # build123d shape or None (part-list-only row)
    explode: str = "base"
    sub: str | None = None
    cut: bool = True     # cut in the cutaway variant
    mass_kg: float | None = None
    basis: str = "CAD volume x density"
    meta: dict = field(default_factory=dict)

    def mass(self):
        if self.mass_kg is not None:
            return self.mass_kg
        if self.shape is None:
            return 0.0
        return self.shape.volume / 1000.0 * DENSITY[self.material] / 1000.0   # mm3 -> cm3 -> g -> kg


class Asm:
    def __init__(self, key, title):
        self.key, self.title, self.parts, self.anchors, self.notes, self.extra = key, title, [], {}, [], {}

    def add(self, *a, **k):
        p = Part(*a, **k)
        self.parts.append(p)
        return p

    def solids(self):
        return [p for p in self.parts if p.shape is not None]

    def bbox(self, parts=None):
        lo, hi = [1e18] * 3, [-1e18] * 3
        for p in parts or self.solids():
            bb = p.shape.bounding_box()
            lo = [min(lo[0], bb.min.X), min(lo[1], bb.min.Y), min(lo[2], bb.min.Z)]
            hi = [max(hi[0], bb.max.X), max(hi[1], bb.max.Y), max(hi[2], bb.max.Z)]
        return lo, hi


# ================================================================================================ (b) R1 monobloc
def build_monobloc(detail: bool = True) -> Asm:
    """R1 12 V monobloc. detail=False -> exterior only (case, lid, vent cover, terminals, label)."""
    mb, d, lay, mm = MONOBLOC, monobloc(), monobloc_layout(), MB_MECH
    es = d["electrode"]
    L, W, H = mb["length_mm"], mb["width_mm"], mb["height_mm"]
    wall, pt, base = mb["wall_mm"], mb["partition_mm"], mb["base_mm"]
    n, comp, st = lay["n"], lay["comp"], lay["stack_t"]
    zl0, zt1, zb1 = lay["z_lid0"], lay["z_tab1"], lay["z_bus1"]
    cx = lay["cell_x"]
    ty, tw = mm["tab_y_mm"], mm["tab_w_mm"]
    A = Asm("r1_monobloc" if detail else "r1_monobloc_ext",
            f"R1 12 V monobloc ({n} cells, {d['energy_Wh']/1000:.2f} kWh TARGET) - CONCEPT NOT FOR FABRICATION")

    # ---- intercell connectors and terminal links first (they also cut holes in the partitions)
    conns, links = [], {}
    for i in range(n - 1):
        y = ty if i % 2 == 0 else -ty            # anode of cell i -> cathode of cell i+1 on the same side
        conns.append((i, box(cx[i] + st / 2, cx[i + 1] - st / 2, y - tw / 2, y + tw / 2, zt1, zb1)))
    lw, pd, tyy = mm["term_link_w_mm"], mm["term_post_d_mm"], lay["term_y"]
    for sgn, ci, txx in ((+1, 0, lay["term_x"][0]), (-1, n - 1, lay["term_x"][1])):
        # +: cell 0 cathode bus (-Y side); -: cell n-1 anode bus (-Y side, n-1 odd)
        xe = cx[ci] + sgn * st / 2                # bus end facing the terminal
        a = box(min(xe, xe - sgn * lw), max(xe, xe - sgn * lw), tyy - lw / 2, -ty - tw / 2, zt1, zb1)
        b = box(min(xe, txx + sgn * pd / 2), max(xe, txx + sgn * pd / 2), tyy - lw / 2, tyy + lw / 2, zt1, zb1)
        links["+" if sgn > 0 else "-"] = (a + b, txx)

    # ---- case container with moulded partitions
    outer = fillet(box(-L / 2, L / 2, -W / 2, W / 2, 0, zl0).edges().filter_by(Axis.Z), mm["case_fillet_mm"])
    shell = outer - box(-L / 2 + wall, L / 2 - wall, -W / 2 + wall, W / 2 - wall, base, zl0 + 1)
    for i in range(n - 1):
        xp = cx[i] + comp / 2
        shell = shell + box(xp, xp + pt, -W / 2 + wall, W / 2 - wall, base, zl0)
    for _, c in conns:
        shell = shell - c
    for lk, _ in links.values():
        shell = shell - lk
    A.add("Case container, PP-GF20, 10 compartments + 9 partitions", "case container (moulded with partitions)",
          "PP-GF20", "case", shell, explode="case")

    # ---- lid with valve wells, vent manifold groove, terminal wells, label recess
    mw, mdep, ct = mm["manifold_w_mm"], mm["manifold_depth_mm"], mm["cover_t_mm"]
    xg0, xg1 = cx[0] - mm["valve_well_od_mm"] / 2, L / 2 - wall
    zw0 = zl0 - mm["valve_well_depth_mm"]
    lid = fillet(box(-L / 2, L / 2, -W / 2, W / 2, zl0, H).edges().filter_by(Axis.Z), mm["case_fillet_mm"])
    for x in cx:
        lid = lid + tube(mm["valve_well_od_mm"] / 2, mm["valve_well_id_mm"] / 2, zw0 + 1.5, zl0 + 0.5, x, 0)
        lid = lid + (cyl(mm["valve_well_od_mm"] / 2, zw0, zw0 + 1.5, x, 0) - cyl(mm["valve_nipple_id_mm"] / 2, zw0 - 1, zw0 + 2, x, 0))
        lid = lid - cyl(mm["valve_well_id_mm"] / 2, zl0 - 0.5, H - mdep + 0.01, x, 0)
    lid = lid - box(xg0, xg1, -mw / 2, mw / 2, H - mdep, H + 1)
    for txx in lay["term_x"]:
        lid = lid - cyl(mm["term_well_d_mm"] / 2, H - mm["term_well_depth_mm"], H + 1, txx, tyy)
        lid = lid - cyl(pd / 2, zl0 - 1, H + 1, txx, tyy)
    ll, lwid, ly, ldep = mm["label_l_mm"], mm["label_w_mm"], mm["label_y_mm"], mm["label_depth_mm"]
    lid = lid - box(-ll / 2, ll / 2, ly - lwid / 2, ly + lwid / 2, H - ldep, H + 1)
    A.add("Lid, PP-GF20, with 10 valve wells, vent manifold groove, terminal wells, label recess",
          "lid (moulded, incl. valve wells)", "PP-GF20", "lid", lid, explode="lid")
    A.add("Lid label (blank film in recess)", "lid label", "label film", "label",
          box(-ll / 2 + 0.5, ll / 2 - 0.5, ly - lwid / 2 + 0.5, ly + lwid / 2 - 0.5, H - ldep, H - ldep + 0.3), explode="lid")

    # ---- common vent manifold cover + flame arrestor
    xo = xg1 - mm["frit_len_mm"] / 2
    cover = box(xg0, xg1, -mw / 2, mw / 2, H - ct, H) - cyl(mm["outlet_d_mm"] / 2, H - ct - 1, H + 1, xo, 0)
    A.add("Vent manifold cover strip (PP, welded) with outlet hole", "vent manifold cover", "PP", "vent", cover, explode="cover")
    A.add("Flame arrestor, porous PP frit (MONOBLOC flame_arrestor)", "flame arrestor frit", "PP frit (porous)", "frit",
          box(xg1 - mm["frit_len_mm"], xg1, -mw / 2, mw / 2, H - mdep, H - ct), explode="cover")

    # ---- per-cell one-way valves (nipple + EPDM Bunsen cap)
    zn0, zn1 = zw0 + 1.5, zl0 - 4.0
    for i, x in enumerate(cx):
        A.add(f"Valve nipple, cell {i+1} (PP)", "valve nipple", "PP", "vent",
              tube(mm["valve_nipple_od_mm"] / 2, mm["valve_nipple_id_mm"] / 2, zn0, zn1, x, 0), explode="valve", sub="Vent valves")
        cap = cyl(mm["valve_cap_od_mm"] / 2, zn1 - mm["valve_cap_h_mm"] + 1.5, zn1 + 1.5, x, 0) - \
            cyl(mm["valve_nipple_od_mm"] / 2, zn1 - mm["valve_cap_h_mm"] + 1.4, zn1, x, 0)
        A.add(f"One-way valve cap, cell {i+1} (EPDM Bunsen, opens {mb['vent_valve_open_kPa'].value:.0f} kPa TARGET)",
              "one-way valve cap (EPDM)", "EPDM", "epdm", cap, explode="valve", sub="Vent valves")

    # ---- terminals: post (M8 female insert) + polarity collar + link to end cell
    for pol, (lk, txx) in links.items():
        post = cyl(pd / 2, zb1, H - mm["term_top_below_lid_mm"], txx, tyy) - \
            cyl(mm["term_bore_d_mm"] / 2, H - mm["term_top_below_lid_mm"] - mm["term_bore_depth_mm"], H + 1, txx, tyy)
        A.add(f"Terminal {pol}: M8 female insert post (lead-free brass, Sn-plated)", "terminal post M8 female insert",
              "brass (lead-free, Sn-plated)", "terminal", post, explode="stack", cut=False, sub="Terminals")
        A.add(f"Terminal {pol}: polarity collar ({'red' if pol == '+' else 'black'} PP)", "terminal polarity collar", "PP",
              "red" if pol == "+" else "black",
              tube(mm["collar_od_mm"] / 2, pd / 2, H - mm["term_well_depth_mm"], H - mm["term_well_depth_mm"] + mm["collar_t_mm"], txx, tyy),
              explode="lid", sub="Terminals")
        if detail:
            A.add(f"Terminal {pol} link to end cell (316L)", "terminal link (316L)", "316L stainless", "steel", lk,
                  explode="stack", cut=False, sub="Terminals")
    A.anchors.update({
        "terminal_pos": [lay["term_x"][0], tyy, H], "terminal_neg": [lay["term_x"][1], tyy, H],
        "vent_outlet": [xo, 0.0, H], "lid_label": [0.0, ly, H], "case_side": [0.0, -W / 2, H * 0.45],
        "lid_edge": [-L / 2 + 30, -W / 2 + 10, H], "valve_cell5": [cx[4], 0.0, zn1], "manifold": [cx[6], 0.0, H - ct - 1],
        "frit": [xg1 - mm["frit_len_mm"] / 2, 0.0, H - mdep + 1],
    })
    if not detail:
        return A

    # ---- cells: full electrode stacks (every repeat unit), separators, tabs, plate-group straps
    tc2 = (2 * es["cathode_thick_um"] + MAT["cc_thickness_um"].value) / 1000.0
    ta2 = (2 * es["anode_thick_um"] + MAT["cc_thickness_um"].value) / 1000.0
    sep = MAT["separator_thickness_um"].value / 1000.0
    pw, ph = d["plate_w_mm"], d["plate_h_mm"]
    area = d["plate_area_cm2"]
    af = MAT["active_fraction"].value
    cc_kg_cm2 = MAT["cc_thickness_um"].value * 1e-4 * MAT["cc_density"].value * 1e-3
    m_cath = area * (2 * es["cathode_loading"] / af * 1e-6 + cc_kg_cm2)
    m_anod = area * (2 * es["anode_loading"] / af * 1e-6 + cc_kg_cm2)
    m_sep = area * MAT["separator_areal_mass"].value * 1e-6
    m_tab = tw * mm["tab_h_mm"] * MAT["cc_thickness_um"].value / 1000.0 / 1000.0 * MAT["cc_density"].value / 1000.0
    z0, z1 = lay["z_plate0"], lay["z_plate1"]
    sw, zs0 = lay["sep_w"], lay["z_sep0"]
    nrep = d["repeats_per_cell"]
    for i, x in enumerate(cx):
        sub = f"Cell {i+1}"
        yc, ya = (-ty, ty) if i % 2 == 0 else (ty, -ty)
        xs = x - st / 2
        k = 0
        for r in range(nrep):
            for kind, t in (("cathode", tc2), ("sep", sep), ("anode", ta2), ("sep", sep)):
                meta = dict(cell=i, rep=r, layer=k, x0=xs)
                if kind == "sep":
                    A.add(f"{sub} separator {2*r + (k % 4 == 3) + 1}", "separator (nonwoven PP / AGM)",
                          "separator", "separator", box(xs, xs + t, -sw / 2, sw / 2, zs0, z1 + MB_MECH["sep_overhang_mm"]),
                          explode="stack", sub=sub, mass_kg=m_sep, basis="MAT separator_areal_mass x plate area", meta=meta)
                else:
                    yt = yc if kind == "cathode" else ya
                    nm = "cathode plate (Na-birnessite, 2-side coated 316L)" if kind == "cathode" else \
                        "anode plate (NaTi2(PO4)3/C, 2-side coated 316L)"
                    A.add(f"{sub} {kind} plate {r+1}", nm, kind, kind, box(xs, xs + t, -pw / 2, pw / 2, z0, z1),
                          explode="stack", sub=sub, mass_kg=m_cath if kind == "cathode" else m_anod,
                          basis="design.electrode_stack loading / active fraction + cc", meta=meta)
                    A.add(f"{sub} {kind} tab {r+1}", "electrode tab (uncoated 316L foil; drawn at plate thickness)",
                          "316L stainless", "steel", box(xs, xs + t, yt - tw / 2, yt + tw / 2, z1, zt1), explode="stack",
                          sub=sub, cut=False, mass_kg=m_tab, basis="tab area x cc thickness x density", meta=meta)
                xs += t
                k += 1
        for kind, yb in (("cathode", yc), ("anode", ya)):
            A.add(f"{sub} {kind} plate-group strap (316L)", "plate-group strap (316L)", "316L stainless", "steel",
                  box(x - st / 2, x + st / 2, yb - tw / 2, yb + tw / 2, zt1, zb1), explode="stack", sub=sub, cut=False,
                  meta=dict(cell=i))
        # free electrolyte pooled around the stack (pores are saturated, see part list)
        g = 0.05   # render gap so the fluid surface never coincides with a wall or plate face
        el = box(x - comp / 2 + g, x + comp / 2 - g, -lay["w_in"] / 2 + g, lay["w_in"] / 2 - g, base + g, lay["z_fill"]) - \
            box(x - st / 2 - g, x + st / 2 + g, -sw / 2 - g, sw / 2 + g, zs0 - g, lay["z_fill"] + 1)
        A.add(f"{sub} free electrolyte, {MAT['electrolyte_molarity'].value} M Na2SO4 (fluid volume)",
              "free electrolyte 0.5 M Na2SO4 (fluid volume)", "electrolyte 0.5 M Na2SO4", "electrolyte", el,
              explode="electrolyte", sub=sub, meta=dict(cell=i))
    for i, c in conns:
        A.add(f"Intercell connector cell {i+1}->{i+2} (316L, through-partition weld)", "intercell connector (316L)",
              "316L stainless", "steel", c, explode="stack", cut=False, sub="Intercell connectors")
    # pore electrolyte: part-list-only row (it is inside the plate/separator solids)
    pore_kg = es["electrolyte_mg_cm2"] * area * nrep * n * 1e-6
    A.add("Electrolyte held in electrode + separator pores", "electrolyte in pores (not a separate solid)",
          "electrolyte 0.5 M Na2SO4", "electrolyte", None, mass_kg=pore_kg / n, basis="design.electrode_stack electrolyte_mg_cm2",
          meta=dict(qty=n))
    A.anchors.update({
        "plates_cell5": [cx[4], -pw / 2, (z0 + z1) / 2], "electrolyte_cell5": [cx[4], -lay["w_in"] / 2, (base + lay["z_fill"]) / 2],
        "strap": [cx[3], ty, zb1], "headspace": [cx[5], -40.0, (z1 + zl0) / 2], "partition": [cx[4] + comp / 2, -W / 2 + wall, 120.0],
        "separator_cell5": [cx[4], -sw / 2, z0 + 20],
    })
    A.notes.append(f"Vent: {VENT_ARRANGEMENT}")
    A.notes.append(f"Free-electrolyte level {lay['z_fill']:.1f} mm (from design.monobloc free_electrolyte_kg); pores saturated.")
    return A


def build_cell() -> Asm:
    """One R1 cell (compartment 5): plate group, straps, electrolyte - for the cell detail."""
    full = build_monobloc(True)
    A = Asm("r1_cell", "R1 cell (one of 10 in the monobloc) - CONCEPT NOT FOR FABRICATION")
    for p in full.parts:
        if p.sub == "Cell 5" and p.shape is not None:
            A.parts.append(Part(p.name, p.ptype, p.material, p.group, p.shape, "base", None, True, p.mass_kg, p.basis, p.meta))
    return A


# ================================================================================================ (a) R0 test cell
def build_r0() -> Asm:
    f = R0_FIXTURE
    A = Asm("r0_test_cell", f"R0 symmetric aqueous test cell in a {f['label']} - CONCEPT NOT FOR FABRICATION")
    rp, tp, bo, bh = f["plate_od_mm"] / 2, f["plate_t_mm"], f["boss_od_mm"] / 2, f["boss_h_mm"]
    de = R0["electrode_diameter"].value
    cp, coat, sept = f["carbon_paper_t_mm"], R0_COATING_UM / 1000.0, f["separator_t_mm"]
    bolts = [(f["bolt_pcd_mm"] / 2 * math.cos(math.radians(90 + 120 * k)), f["bolt_pcd_mm"] / 2 * math.sin(math.radians(90 + 120 * k)))
             for k in range(f["bolt_n"])]
    body_top = tp + f["body_h_mm"]

    def holes(s, z0, z1):
        for bx, by in bolts:
            s = s - cyl(f["sleeve_od_mm"] / 2, z0 - 1, z1 + 1, bx, by)
        return s

    bottom = holes(cyl(rp, 0, tp) + cyl(bo, tp, tp + bh), 0, tp)
    A.add("Bottom end plate with boss (304 stainless)", "end plate with boss (304 SS)", "304 stainless", "r0_steel", bottom, explode="b0")
    A.add("Bottom lead tab (304 stainless)", "lead tab (304 SS)", "304 stainless", "r0_steel",
          box(rp - 2, rp + f["lead_l_mm"], -f["lead_w_mm"] / 2, f["lead_w_mm"] / 2, 0, f["lead_t_mm"]), explode="b0")
    body = holes(tube(f["body_od_mm"] / 2, f["body_bore_mm"] / 2, tp, body_top), tp, body_top)
    A.add("Insulating body (PTFE), bore 20 mm", "insulating body (PTFE)", "PTFE", "ptfe", body, explode="body")
    z = tp + bh
    layers = [("Carbon-paper collector 1 (Toray, E-Tek)", "carbon-paper current collector", "carbon paper", "carbonpaper", de, cp),
              ("Electrode 1 coating: Na0.27MnO2 + carbon black (4:1), 5.00 mg active", "electrode coating (birnessite + CB)", "R0 coating", "coating", de, coat),
              ("Separator: cellulose filter paper (Whatman)", "separator (cellulose filter paper)", "cellulose filter paper", "cellulose", f["separator_d_mm"], sept),
              ("Electrode 2 coating: Na0.27MnO2 + carbon black (4:1), 5.00 mg active", "electrode coating (birnessite + CB)", "R0 coating", "coating", de, coat),
              ("Carbon-paper collector 2 (Toray, E-Tek)", "carbon-paper current collector", "carbon paper", "carbonpaper", de, cp)]
    for k, (nm, pt_, mat, grp, dia, t) in enumerate(layers):
        mass = (R0["active_mass_per_electrode"].value + R0["carbon_black_per_electrode"].value) * 1e-6 if grp == "coating" else None
        A.add(nm, pt_, mat, grp, cyl(dia / 2, z, z + t), explode=f"s{k}", mass_kg=mass,
              basis="Shan 2019 masses (LIT)" if mass else "CAD volume x density", meta=dict(z0=z, z1=z + t))
        if k == 1:
            A.anchors["electrode_1"] = [de / 2, 0.0, z + t]
        if k == 2:
            A.anchors["separator"] = [f["separator_d_mm"] / 2, 0.0, z + t / 2]
        z += t
    A.add("Spacer disc (304 stainless; the stainless plate of Shan 2019)", "spacer disc (304 SS)", "304 stainless", "r0_steel",
          cyl(bo, z, z + f["spacer_t_mm"]), explode="s5")
    z += f["spacer_t_mm"]
    wire, slen, turns, sod = f["spring_wire_mm"], f["spring_len_mm"], f["spring_turns"], f["spring_od_mm"]
    try:
        hx = Helix(pitch=(slen - wire) / turns, height=slen - wire, radius=(sod - wire) / 2)
        spring = sweep(Plane(hx @ 0, z_dir=hx % 0) * Circle(wire / 2), path=hx)
        spring = Pos(0, 0, z + wire / 2) * spring
        if spring.volume <= 0:
            raise ValueError("empty sweep")
    except Exception as exc:  # fallback: stacked tori
        print("spring sweep failed, using tori:", exc)
        spring = None
        for k in range(int(turns) + 1):
            t_ = Pos(0, 0, z + wire / 2 + k * (slen - wire) / turns) * Torus((sod - wire) / 2, wire / 2)
            spring = t_ if spring is None else spring + t_
    A.add("Compression spring (316 stainless)", "compression spring", "spring steel (316)", "spring", spring, explode="s6")
    z += slen
    A.add("Piston (304 stainless)", "piston (304 SS)", "304 stainless", "r0_steel", cyl(bo, z, z + f["piston_h_mm"]), explode="s7")
    z += f["piston_h_mm"]
    top = holes(cyl(rp, body_top, body_top + tp) + cyl(bo, body_top - bh, body_top), body_top, body_top + tp)
    A.add("Top end plate with boss (304 stainless)", "end plate with boss (304 SS)", "304 stainless", "r0_steel", top, explode="t0")
    A.add("Top lead tab (304 stainless)", "lead tab (304 SS)", "304 stainless", "r0_steel",
          box(-rp - f["lead_l_mm"], -rp + 2, -f["lead_w_mm"] / 2, f["lead_w_mm"] / 2, body_top + tp - f["lead_t_mm"], body_top + tp), explode="t0")
    zt = body_top + tp
    for k, (bx, by) in enumerate(bolts):
        A.add(f"Insulating sleeve {k+1} (PEEK)", "insulating bolt sleeve (PEEK)", "PEEK", "peek",
              tube(f["sleeve_od_mm"] / 2, f["bolt_d_mm"] / 2, 0, zt, bx, by), explode="bolt")
        A.add(f"Clamp bolt {k+1} M5 (304 stainless) + head", "clamp bolt M5 + nut", "304 stainless", "r0_steel",
              cyl(f["bolt_d_mm"] / 2, -5, zt, bx, by) + cyl(4.25, zt, zt + 4, bx, by) + cyl(4.6, -5, 0, bx, by),
              explode="bolt")
    vol_uL = R0["electrolyte_volume"].value
    A.add(f"Electrolyte {vol_uL:.0f} uL, {R0['electrolyte_molarity'].value:.0f} M Na2SO4 (wets the stack; not a solid)",
          "electrolyte 150 uL 1 M Na2SO4 (not modelled)", "electrolyte 1 M Na2SO4", "electrolyte", None,
          mass_kg=vol_uL * 1e-3 * DENSITY["electrolyte 1 M Na2SO4"] / 1000.0, basis="R0 electrolyte_volume x density")
    A.anchors.update({"top_plate": [0.0, rp, zt], "body": [-f["body_od_mm"] / 2, 0.0, tp + f["body_h_mm"] / 2],
                      "spring": [sod / 2, 0.0, z - f["piston_h_mm"] - slen / 2], "bolt": [bolts[0][0], bolts[0][1], zt + 4]})
    A.notes.append(f"Fixture is a {f['label']}; Shan 2019 used an MTI EQ-STC split cell (no published drawing).")
    return A


# ================================================================================================ placement helpers
def place(shape, x=0.0, y=0.0, z=0.0, rz=0.0):
    return Pos(x, y, z) * (Rot(0, 0, rz) * shape if rz else shape)


def xform_pt(p, x=0.0, y=0.0, z=0.0, rz=0.0):
    c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    return [x + c * p[0] - s * p[1], y + s * p[0] + c * p[1], z + p[2]]


def add_block(A, ext: Asm, idx, x, y, z, rz, sub):
    """Place an exterior-only monobloc into an assembly."""
    for p in ext.parts:
        A.add(f"{sub}: {p.name}", "monobloc 12 V (exterior model; mass from design.monobloc)", p.material, p.group,
              place(p.shape, x, y, z, rz), explode="block", sub=sub, mass_kg=0.0, basis="counted in monobloc row")
    return {k: xform_pt(v, x, y, z, rz) for k, v in ext.anchors.items()}


# ================================================================================================ (c) 48 V module
def build_module48() -> Asm:
    m, mbd = M48_MECH, monobloc()
    Lt, Wt, Ht = M48_TRAY_CAD_MM
    t, gap, clr = m["sheet_t_mm"], m["block_gap_mm"], m["wall_clear_mm"]
    A = Asm("r1_module48", f"R1 48 V telecom module ({MODULE48['monoblocs']} x 12 V monobloc) - CONCEPT NOT FOR FABRICATION")
    A.notes.append(f"Tray {Lt:.0f} x {Wt:.0f} x {Ht:.0f} mm (CAD): MODULE48 tray_mm {MODULE48['tray_mm']} cannot hold 4 monoblocs.")
    ext = build_monobloc(detail=False)
    lb, wb = MONOBLOC["length_mm"], MONOBLOC["width_mm"]
    # tray
    tray = box(-Lt / 2, Lt / 2, -Wt / 2, Wt / 2, 0, t)
    tray = tray + box(Lt / 2 - t, Lt / 2, -Wt / 2, Wt / 2, t, m["side_lip_h_mm"])
    for sy in (-1, 1):
        y0 = sy * Wt / 2 - (t if sy > 0 else 0)
        tray = tray + box(-Lt / 2 + t, Lt / 2 - t, y0, y0 + t, t, m["side_lip_h_mm"])
    yb0 = -Wt / 2 + t + clr
    ydiv = yb0 + 2 * wb + gap + clr
    tray = tray + box(-Lt / 2 + t, Lt / 2 - t, ydiv, ydiv + t, t, m["side_lip_h_mm"])
    A.add("Tray, galvanised steel (base, rear and side lips, bay divider)", "tray (galvanised steel)", "galvanised steel", "tray", tray)
    front = box(-Lt / 2, -Lt / 2 + t, -Wt / 2, Wt / 2, 0, Ht)
    yc_bay = (ydiv + t + Wt / 2 - t) / 2
    for zc in (Ht * 0.35, Ht * 0.6):   # output connector holes
        front = front - Pos(-Lt / 2, yc_bay, zc) * Rot(0, 90, 0) * Cylinder(9, 10)
    A.add("Front panel, galvanised steel", "front panel (galvanised steel)", "galvanised steel", "tray", front)
    for sy in (-1, 1):
        yh = sy * Wt * 0.28
        h = box(-Lt / 2 - 35, -Lt / 2 - 27, yh - m["handle_w_mm"] / 2, yh + m["handle_w_mm"] / 2, Ht * 0.45, Ht * 0.55) + \
            box(-Lt / 2 - 35, -Lt / 2, yh - m["handle_w_mm"] / 2, yh - m["handle_w_mm"] / 2 + 10, Ht * 0.45, Ht * 0.55) + \
            box(-Lt / 2 - 35, -Lt / 2, yh + m["handle_w_mm"] / 2 - 10, yh + m["handle_w_mm"] / 2, Ht * 0.45, Ht * 0.55)
        A.add(f"Front pull handle {'L' if sy < 0 else 'R'}", "front pull handle", "aluminium 6063", "handle", h)
    # blocks 2 x 2 (rear row rotated 180 deg so all terminals face the cable runs)
    xs = [-(lb + gap) / 2, (lb + gap) / 2]
    ys = [yb0 + wb / 2, yb0 + wb * 1.5 + gap]
    pos = [(xs[0], ys[0], 0), (xs[1], ys[0], 0), (xs[1], ys[1], 180), (xs[0], ys[1], 180)]
    anc = []
    A.extra["blocks"] = [[[x, y], rz] for x, y, rz in pos]
    for k, (x, y, rz) in enumerate(pos):
        anc.append(add_block(A, ext, k, x, y, t, rz, f"Monobloc {k+1}"))
    A.add("Monobloc 12 V (R1)", "monobloc 12 V (R1, full mass from design.monobloc)", "-", "case", None,
          mass_kg=mbd["mass_kg"], basis="design.monobloc() mass_kg (CALC)", meta=dict(qty=MODULE48["monoblocs"]))
    zl = t + MONOBLOC["height_mm"]
    # hold-down bars
    for xb in (xs[0] - 80, xs[0] + 80, xs[1] - 80, xs[1] + 80):
        hw, ht_ = m["holddown_w_mm"] / 2, m["holddown_t_mm"]
        hb = box(xb - hw, xb + hw, -Wt / 2 - 3, ydiv + t + 3, zl, zl + ht_)              # bar over the lids
        hb = hb + box(xb - hw, xb + hw, -Wt / 2 - 3, -Wt / 2, 0, zl)                       # strap outside the side lip
        hb = hb + box(xb - hw, xb + hw, ydiv + t, ydiv + t + 3, t, zl)                      # strap on the bay side of the divider
        A.add("Hold-down bar + 2 straps (steel)", "hold-down bar + straps", "galvanised steel", "tray", hb)
    # electronics bay: fuse, DC/DC, BMS
    bayx0 = -Lt / 2 + t + 8
    fl, fw, fh = m["fuse_box_mm"]
    dl, dw, dh = m["dcdc_box_mm"]
    bl, bw_, bh = m["bms_box_mm"]
    fuse = box(bayx0, bayx0 + fl, yc_bay - fw / 2, yc_bay + fw / 2, t, t + fh)
    dcx0 = bayx0 + fl + 15
    dcdc = box(dcx0, dcx0 + dl, yc_bay - dw / 2, yc_bay + dw / 2, t, t + dh)
    for k in range(9):   # cooling fins on the top
        xf = dcx0 + 15 + k * (dl - 30) / 8
        dcdc = dcdc + box(xf - 1.5, xf + 1.5, yc_bay - dw / 2 + 5, yc_bay + dw / 2 - 5, t + dh, t + dh + 12)
    bmx0 = dcx0 + dl + 15
    bms = box(bmx0, bmx0 + bl, yc_bay - bw_ / 2, yc_bay + bw_ / 2, t, t + bh)
    A.add("Main fuse holder + fuse", "main fuse (holder + link)", "electronics (potted avg)", "enclosure", fuse)
    A.add(f"Bidirectional DC/DC converter box (eff. {MODULE48['dcdc_efficiency'].value:.2f} ASSUMPTION)",
          "DC/DC converter box", "electronics (potted avg)", "enclosure", dcdc)
    A.add(f"Module BMS enclosure ({BMS['series_groups_per_board']}-ch monitor board, {BMS['comms'][0]})",
          "module BMS enclosure + board", "electronics (potted avg)", "enclosure", bms)
    for k, zc in enumerate((Ht * 0.35, Ht * 0.6)):
        A.add(f"DC output connector {'+' if k else '-'}", "DC output connector", "PP", "cable_red" if k else "cable_black",
              Pos(-Lt / 2 - 12, yc_bay, zc) * Rot(0, 90, 0) * Cylinder(8, 24))
    # power cabling (series string) + leads to fuse / DC/DC
    rc = m["cable_d_mm"] / 2
    zc = zl + rc + 1
    tp = [(a["terminal_pos"], a["terminal_neg"]) for a in anc]

    def up(p, dz=rc + 1):
        return (p[0], p[1], p[2] + dz)
    runs = [
        ("Series cable B1- to B2+", [up(tp[0][1]), up(tp[1][0])], "cable_black"),
        ("Series cable B2- to B3+", [up(tp[1][1]), (tp[1][1][0], tp[1][1][1], zc + 12), (tp[2][0][0], tp[2][0][1], zc + 12), up(tp[2][0])], "cable_black"),
        ("Series cable B3- to B4+", [up(tp[2][1]), up(tp[3][0])], "cable_black"),
        ("Module + lead to fuse", [up(tp[0][0]), (tp[0][0][0] - 25, tp[0][0][1], zc + 6), (tp[0][0][0] - 25, yc_bay - 10, zc + 6),
                                   (bayx0 + fl / 2, yc_bay - 10, zc + 6), (bayx0 + fl / 2, yc_bay - 10, t + fh)], "cable_red"),
        ("Module - lead to DC/DC", [up(tp[3][1]), (tp[3][1][0] + 30, tp[3][1][1], zc + 18), (dcx0 + 40, yc_bay, zc + 18),
                                    (dcx0 + 40, yc_bay, t + dh + 12)], "cable_black"),
        ("Fuse to DC/DC", [(bayx0 + fl, yc_bay + 10, t + fh * 0.6), (dcx0, yc_bay + 10, t + fh * 0.6)], "cable_red"),
        ("DC/DC to output +", [(dcx0, yc_bay - 20, t + Ht * 0.6), (-Lt / 2 + t, yc_bay, Ht * 0.6)], "cable_red"),
        ("DC/DC to output -", [(dcx0, yc_bay - 20, t + Ht * 0.3), (-Lt / 2 + t, yc_bay, Ht * 0.35)], "cable_black"),
    ]
    for nm, pts, grp in runs:
        A.add(nm, "power cable 25 mm2 (insulated Cu)", "copper (insulated cable)", grp, cable(pts, rc), sub="Cabling")
    rs = m["sense_d_mm"] / 2
    for k, (pp, pn) in enumerate(tp):
        pts = [(pp[0], pp[1] + (14 if k < 2 else -14), zl + 2 * rc + 4), (pp[0], ydiv - 6, zl + 2 * rc + 4),
               (bmx0 + 20 + 30 * k, ydiv - 6, zl + 2 * rc + 4), (bmx0 + 20 + 30 * k, yc_bay, t + bh)]
        A.add(f"BMS sense lead block {k+1}", "BMS sense / NTC lead", "copper (insulated cable)", "sense", cable(pts, rs), sub="Cabling")
    A.anchors.update({"tray": [Lt / 2 - 60, -Wt / 2, m["side_lip_h_mm"] * 0.6], "dcdc": [dcx0 + dl / 2, yc_bay, t + dh + 12],
                      "bms": [bmx0 + bl / 2, yc_bay, t + bh], "fuse": [bayx0 + fl / 2, yc_bay, t + fh],
                      "block1": anc[0]["case_side"], "block2_vent": anc[1]["vent_outlet"], "series_cable": list(up(tp[0][1])),
                      "output": [-Lt / 2 - 24, yc_bay, Ht * 0.6], "label3": anc[2]["lid_label"]})
    return A


# ================================================================================================ (d) UPS cabinet
def build_cabinet(door_open_deg: float = 0.0) -> Asm:
    c, cm = CABINET, CAB_MECH
    Wc, Dc, Hc = c["width_mm"], c["depth_mm"], c["height_mm"]
    pm, pt, dt = cm["post_mm"], cm["panel_t_mm"], cm["door_t_mm"]
    A = Asm("r1_ups_cabinet", f"R1 UPS battery cabinet ({c['shelves']} x {c['monoblocs_per_shelf']} monoblocs, "
            f"{c['string_nominal_V']:.0f} V string) - CONCEPT NOT FOR FABRICATION")
    yf = -Dc / 2 + dt                       # inner face of door / front of frame
    ext = build_monobloc(detail=False)
    # frame
    posts = None
    for sx in (-1, 1):
        for y0 in (yf, Dc / 2 - pm):
            x0 = sx * Wc / 2 - (pm if sx > 0 else 0)
            p = box(x0, x0 + pm, y0, y0 + pm, 0, Hc) - box(x0 + 2, x0 + pm - 2, y0 + 2, y0 + pm - 2, -1, Hc + 1)   # 2 mm wall tube
            posts = p if posts is None else posts + p
    A.add("Corner posts 4x (folded steel)", "corner posts", "powder-coated steel", "cab_paint", posts)
    ph, rh = cm["plinth_h_mm"], cm["roof_h_mm"]
    plinth = box(-Wc / 2 + pm, Wc / 2 - pm, yf, Dc / 2, 0, ph) - box(-Wc / 2 + pm + 2, Wc / 2 - pm - 2, yf + 2, Dc / 2 - 2, -1, ph + 1)
    A.add("Plinth / base frame", "plinth base frame", "powder-coated steel", "cab_paint", plinth)
    for sx in (-1, 1):
        A.add(f"Side panel {'L' if sx < 0 else 'R'}", "side panel", "powder-coated steel", "cab_paint",
              box(sx * Wc / 2 - (pt if sx > 0 else 0), sx * Wc / 2 + (0 if sx > 0 else pt), yf + pm, Dc / 2 - pm, ph, Hc - rh))
    A.add("Rear panel", "rear panel", "powder-coated steel", "cab_paint", box(-Wc / 2 + pm, Wc / 2 - pm, Dc / 2 - pt, Dc / 2, ph, Hc - rh))
    roof = box(-Wc / 2, Wc / 2, yf, Dc / 2, Hc - rh, Hc) - box(-Wc / 2 + 2, Wc / 2 - 2, yf + 2, Dc / 2 - 2, Hc - rh - 1, Hc - pt)
    for k in range(cm["roof_slots"]):        # H2 outlet slots over the rear plenum
        yy = 0.10 * Dc + k * (0.36 * Dc) / (cm["roof_slots"] - 1)
        roof = roof - box(-Wc / 2 + pm + 30, Wc / 2 - pm - 30, yy - 6, yy + 6, Hc - pt - 1, Hc + 1)
    A.add("Roof with ventilation slots (H2 outlet, high)", "roof with vent slots", "powder-coated steel", "cab_paint", roof)
    # door with louvres (low inlet, high outlet), flush handle, hinges
    sw_, sh_ = cm["louvre_slot_mm"]
    door = box(-Wc / 2, Wc / 2, -Dc / 2, yf, 0, Hc) - box(-Wc / 2 + 25, Wc / 2 - 25, -Dc / 2 + pt, yf + 1, 25, Hc - 25)
    louvres = []
    for band, z0 in (("low", 110.0), ("high", Hc - 110.0 - (cm["louvre_rows"] - 1) * 24)):
        for r in range(cm["louvre_rows"]):
            for col in (-1, 0, 1):
                louvres.append(box(col * (sw_ + 30) - sw_ / 2, col * (sw_ + 30) + sw_ / 2, -Dc / 2 - 1, -Dc / 2 + pt + 1,
                                   z0 + r * 24, z0 + r * 24 + sh_))
    for lv in louvres:
        door = door - lv
    hx, hz = Wc / 2 - 60, Hc * 0.52
    door = door - box(hx - 18, hx + 18, -Dc / 2 - 1, -Dc / 2 + 12, hz - 80, hz + 80)
    handle = box(hx - 10, hx + 10, -Dc / 2 + 2, -Dc / 2 + 12, hz - 70, hz + 70)
    hinge_x, hinge_y = -Wc / 2 + 6, -Dc / 2 + dt / 2
    hinges = None
    for zh in (250.0, Hc / 2, Hc - 250.0):
        hh = cyl(5, zh - 40, zh + 40, hinge_x, hinge_y)
        hinges = hh if hinges is None else hinges + hh
    plate = box(-80, 80, -Dc / 2 - 0.0, -Dc / 2 + 0.8, Hc - 380, Hc - 320)   # blank rating-plate area (no marks)
    door_parts = [("Front door with louvres top + bottom (H2 natural ventilation)", "front door with louvres", "powder-coated steel", "cab_paint", door),
                  ("Door flush swing handle", "door handle (flush)", "aluminium 6063", "handle", handle),
                  ("Door hinges 3x", "door hinges", "304 stainless", "steel", hinges),
                  ("Blank rating plate (to be defined)", "rating plate (blank)", "aluminium 6063", "label", plate)]
    for nm, pt_, mat, grp, s in door_parts:
        if door_open_deg:
            s = Pos(hinge_x, hinge_y, 0) * Rot(0, 0, -door_open_deg) * Pos(-hinge_x, -hinge_y, 0) * s
        A.add(nm, pt_, mat, grp, s, explode="door")
    # shelves + blocks
    lb, wb, gap = MONOBLOC["length_mm"], MONOBLOC["width_mm"], cm["block_gap_mm"]
    pitch = CAB_SHELF_PITCH_MM
    xcols = [-(wb + gap), 0.0, wb + gap]
    yfr = yf + cm["front_clear_mm"]
    yrows = [yfr + lb / 2, yfr + lb * 1.5 + gap]
    sx0, sx1 = -Wc / 2 + pm, Wc / 2 - pm
    sy0, sy1 = yf + pm, yrows[1] + lb / 2 + 4
    nblk = 0
    shelf_anc = {}
    rc = M48_MECH["cable_d_mm"] / 2
    for s in range(c["shelves"]):
        zs = ph + s * pitch
        shelf = box(sx0, sx1, sy0 - 10, sy1, zs, zs + cm["shelf_t_mm"]) + \
            box(sx0, sx1, sy0 - 10, sy0 - 10 + cm["shelf_t_mm"], zs - cm["shelf_lip_mm"], zs)
        for sxx in (-1, 1):
            shelf = shelf + box(sxx * (Wc / 2 - pt) - (12 if sxx > 0 else 0), sxx * (Wc / 2 - pt) + (0 if sxx > 0 else 12),
                                sy0, sy1, zs - cm["shelf_lip_mm"], zs)
        A.add(f"Shelf {s+1} (steel, with front lip + side supports)", "shelf with supports", "galvanised steel", "cab_shelf", shelf,
              sub="Shelves")
        zb = zs + cm["shelf_t_mm"]
        slots = [(xcols[0], yrows[0]), (xcols[1], yrows[0]), (xcols[0], yrows[1]), (xcols[1], yrows[1]), (xcols[2], yrows[1])]
        ancs = []
        for k, (x, y) in enumerate(slots[:c["monoblocs_per_shelf"]]):
            ancs.append(add_block(A, ext, nblk, x, y, zb, 90.0, f"Shelf {s+1} monobloc {k+1}"))
            nblk += 1
        # inter-block jumpers on this shelf (series)
        order = [0, 1, 3, 4, 2]
        for a_, b_ in zip(order[:-1], order[1:]):
            p0, p1 = ancs[a_]["terminal_neg"], ancs[b_]["terminal_pos"]
            zj = zb + MONOBLOC["height_mm"] + rc + 0.5
            A.add(f"Shelf {s+1} jumper {a_+1}-{b_+1}", "inter-block jumper cable", "copper (insulated cable)", "cable_black",
                  cable([(p0[0], p0[1], zj), (p0[0], (p0[1] + p1[1]) / 2, zj), (p1[0], (p0[1] + p1[1]) / 2, zj), (p1[0], p1[1], zj)], rc),
                  sub="Cabling")
        xd, yd = xcols[2], yrows[0]
        if s < c["shelves"] - 1:
            A.add(f"Cable duct segment shelf {s+1}", "vertical cable duct (segments)", "PP", "duct",
                  box(xd - cm["duct_mm"] / 2, xd + cm["duct_mm"] / 2, yd - cm["duct_mm"] / 2, yd + cm["duct_mm"] / 2, zb, zs + pitch),
                  sub="Cabling")
        else:
            bw_, bd_, bh_ = cm["bms_box_mm"]
            kw, kd, kh = cm["breaker_mm"]
            brk = box(xd - kw / 2, xd + kw / 2, yfr, yfr + kd, zb, zb + kh)
            hdl = box(xd - 8, xd + 8, yfr - 14, yfr, zb + kh * 0.45, zb + kh * 0.62)
            bmsb = box(xd - bw_ / 2, xd + bw_ / 2, yfr + kd + 15, yfr + kd + 15 + bd_, zb, zb + bh_)
            A.add("DC string breaker (MCCB-style, 2-pole)", "DC string breaker", "electronics (potted avg)", "breaker", brk)
            A.add("DC string breaker handle", "breaker handle", "PP", "accent", hdl)
            A.add(f"Master BMS enclosure ({BMS['comms'][0]} / {BMS['comms'][1]}, H2 + pressure inputs)",
                  "master BMS enclosure", "electronics (potted avg)", "enclosure", bmsb)
            shelf_anc["breaker"] = [xd, yfr - 14, zb + kh * 0.55]
            shelf_anc["master_bms"] = [xd - bw_ / 2, yfr + kd + 15 + bd_ / 2, zb + bh_]
        if s == 0:
            shelf_anc["block_bottom"] = ancs[0]["case_side"]
        if s == 3:
            shelf_anc["block_mid_terminal"] = ancs[1]["terminal_pos"]
            shelf_anc["shelf4"] = [xcols[0], sy0 - 10, zs]
        if s == 5:
            shelf_anc["vent_block"] = ancs[1]["vent_outlet"]
    A.add("Monobloc 12 V (R1)", "monobloc 12 V (R1, full mass from design.monobloc)", "-", "case", None,
          mass_kg=monobloc()["mass_kg"], basis="design.monobloc() mass_kg (CALC)", meta=dict(qty=nblk))
    A.anchors.update(shelf_anc)
    A.anchors.update({"louvre_low": [0.0, -Dc / 2, 160.0], "louvre_high": [0.0, -Dc / 2, Hc - 160.0], "roof_slots": [0.0, 0.25 * Dc, Hc],
                      "door_handle": [hx, -Dc / 2, hz], "plenum": [0.0, sy1 + 30, Hc * 0.5]})
    A.notes.append(f"Shelf pitch {pitch:.1f} mm leaves {pitch - cm['shelf_t_mm'] - MONOBLOC['height_mm']:.1f} mm above block lids.")
    return A


# ================================================================================================ variants + export
def cut_monobloc_shape(p: Part, regions):
    """Remove the cutaway regions from a part (bbox-tested so untouched parts are not booleaned)."""
    if not p.cut:
        return p.shape
    s = p.shape
    for R in regions:
        rb, sb = R.bounding_box(), s.bounding_box()
        if sb.max.X < rb.min.X or sb.min.X > rb.max.X or sb.max.Y < rb.min.Y or sb.min.Y > rb.max.Y or \
                sb.max.Z < rb.min.Z or sb.min.Z > rb.max.Z:
            continue
        s = s - R
        if s is None or s.volume < 1e-3:
            return None
    return s


def monobloc_variants(A: Asm):
    lay, mb = monobloc_layout(), MONOBLOC
    W, H = mb["width_mm"], mb["height_mm"]
    xc0 = lay["cell_x"][1] + lay["comp"] / 2 + mb["partition_mm"] / 2       # mid-partition between cells 2 and 3
    regions = [box(xc0, 200, -W, -lay["w_in"] / 2 + 0.02, -1, H + 1),        # front wall off (cells 3-10)
               box(xc0, 200, -W, 0, lay["z_plate1"] + 2, H + 1)]             # front half of headspace / lid / vent
    full, cut, expl = defaultdict(list), defaultdict(list), defaultdict(list)
    off = {"case": (0, 0, 0), "stack": (0, 0, 150), "lid": (0, 0, 330), "valve": (0, 0, 300), "cover": (0, 0, 380)}
    nfan = 4                                                                  # fan out the first 4 repeat units of cell 1
    for p in A.solids():
        if p.group != "electrolyte":
            full[p.group].append(p.shape)
        cs = cut_monobloc_shape(p, regions)
        if cs is not None:
            cut[p.group].append(cs)
        if p.explode == "electrolyte":
            continue
        dx, dy, dz = off.get(p.explode, (0, 0, 0))
        if p.meta.get("cell") == 0 and p.explode == "stack":
            dx -= 150
            lyr = p.meta.get("layer")
            if lyr is not None and lyr < 4 * nfan:
                dx -= (4 * nfan - lyr) * 6.0
        expl[p.group].append(Pos(dx, dy, dz) * p.shape)
    return {"full": full, "cut": cut, "exploded": expl}, {"cut_x0": xc0}


def r0_variants(A: Asm):
    full, cut, expl = defaultdict(list), defaultdict(list), defaultdict(list)
    zoff = {"b0": 0, "body": 25, "s0": 45, "s1": 52, "s2": 60, "s3": 68, "s4": 75, "s5": 84, "s6": 94, "s7": 108, "t0": 125, "bolt": 150}
    R = box(-100, 0, -100, 0, -50, 100)
    for p in A.solids():
        full[p.group].append(p.shape)
        s = p.shape - R
        if s is not None and s.volume > 1e-4:
            cut[p.group].append(s)
        expl[p.group].append(Pos(0, 0, zoff.get(p.explode, 0)) * p.shape)
    return {"full": full, "cut": cut, "exploded": expl}, {"explode_z": zoff}


def simple_variants(A: Asm, name="full"):
    g = defaultdict(list)
    for p in A.solids():
        g[p.group].append(p.shape)
    return {name: g}, {}


def step_tree(A: Asm):
    subs, loose = defaultdict(list), []
    for p in A.solids():
        s = p.shape
        if s is None:
            continue
        s = Pos(0, 0, 0) * s          # fresh wrapper so a shape is only parented once
        s.label = p.name
        s.color = Color(*GROUP_COLOR[p.group])
        (subs[p.sub] if p.sub else loose).append(s)
    children = loose + [Compound(label=k, children=v) for k, v in subs.items()]
    return Compound(label=A.title, children=children)


def write_partlist(A: Asm, path: Path):
    rows = defaultdict(lambda: dict(qty=0, mass=0.0, material="", basis=""))
    order = []
    for p in A.parts:
        if p.basis == "counted in monobloc row":
            continue
        r = rows[p.ptype]
        if p.ptype not in order:
            order.append(p.ptype)
        q = p.meta.get("qty", 1)
        r["qty"] += q
        r["mass"] += p.mass() * q
        r["material"] = p.material
        r["basis"] = p.basis
    total = sum(r["mass"] for r in rows.values())
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["part", "material", "qty", "unit_mass_kg", "total_mass_kg", "mass_basis"])
        for k in order:
            r = rows[k]
            w.writerow([k, r["material"], r["qty"], f"{r['mass']/r['qty']:.4g}", f"{r['mass']:.4g}", r["basis"]])
        w.writerow(["TOTAL (estimate, CONCEPT)", "", sum(r["qty"] for r in rows.values()), "", f"{total:.3f}", "sum of rows"])
        if A.key == "r1_monobloc":
            w.writerow(["design.monobloc() mass_kg for comparison", "", "", "", f"{monobloc()['mass_kg']:.3f}", "params/design.py (CALC)"])
    return total


def export_asm(A: Asm, variants: dict, glb=True, tol=0.05, ang=0.25):
    t0 = time.time()
    top = step_tree(A)
    export_step(top, str(OUT / f"{A.key}.step"))
    export_stl(Compound([p.shape for p in A.solids()]), str(OUT / f"{A.key}.stl"), tolerance=tol, angular_tolerance=ang)
    glb_ok = False
    if glb:
        try:
            glb_ok = bool(export_gltf(top, str(OUT / f"{A.key}.glb"), binary=True, linear_deflection=tol * 2, angular_deflection=ang * 2))
        except Exception as exc:
            print(f"  GLB export failed for {A.key}: {exc}")
    for vname, groups in variants.items():
        d = OUT / "stl" / A.key / vname
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.stl"):
            old.unlink()
        for g, shapes in groups.items():
            shapes = [s for s in shapes if s is not None]
            if shapes:
                export_stl(Compound(shapes), str(d / f"{g}.stl"), tolerance=tol, angular_tolerance=ang)
    mass = write_partlist(A, OUT / f"{A.key}_partlist.csv")
    lo, hi = A.bbox()
    print(f"  {A.key}: {len(A.solids())} solids, bbox {[round(hi[i]-lo[i], 2) for i in range(3)]} mm, "
          f"mass est {mass:.2f} kg, glb={glb_ok}, {time.time()-t0:.1f} s")
    return dict(title=A.title, solids=len(A.solids()), bbox_min=lo, bbox_max=hi, size=[hi[i] - lo[i] for i in range(3)],
                mass_est_kg=mass, glb=glb_ok, variants=list(variants), anchors=A.anchors, notes=A.notes, extra=A.extra)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    only = set(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else {"r0", "monobloc", "cell", "module", "cabinet"}
    glb = "--no-glb" not in argv
    OUT.mkdir(parents=True, exist_ok=True)
    meta_path = OUT / "cad_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta["group_colors"] = GROUP_COLOR
    d = monobloc()
    meta["labels"] = {   # lid label text, generated from params (rendered in Blender)
        "line1": f"R1  {MONOBLOC['cells_in_series']}-CELL AQUEOUS Na-ION  12 V BLOCK",
        "line2": f"{d['v_nom']:.1f} V nom  |  {d['energy_Wh']/1000:.2f} kWh [TARGET]  |  {MAT['electrolyte_molarity'].value} M Na2SO4 (water-based)",
        "line3": "CONCEPT PROTOTYPE - NOT FOR SALE",
        "side": ["R1 AQUEOUS SODIUM-ION 12 V", f"{d['n_cells']} cells in series | {d['v_nom']:.1f} V nom | {d['energy_Wh']/1000:.2f} kWh [TARGET]",
                 f"water-based {MAT['electrolyte_molarity'].value} M Na2SO4 electrolyte", "no lead | no lithium | concept"],
    }
    meta["mech"] = {"tab_y_mm": MB_MECH["tab_y_mm"], "m48_sheet_t": M48_MECH["sheet_t_mm"]}
    meta["scene"] = {"tile_m": SCENE["raised_floor_tile_mm"] / 1000.0}
    t0 = time.time()
    if "r0" in only:
        A = build_r0()
        v, extra = r0_variants(A)
        meta["r0_test_cell"] = export_asm(A, v, glb, tol=0.01, ang=0.2) | extra
    if "monobloc" in only:
        A = build_monobloc(True)
        v, extra = monobloc_variants(A)
        meta["r1_monobloc"] = export_asm(A, v, glb, tol=0.05) | extra | {"layout": monobloc_layout()}
    if "cell" in only:
        A = build_cell()
        v, extra = simple_variants(A)
        meta["r1_cell"] = export_asm(A, v, glb, tol=0.05)
    if "module" in only:
        A = build_module48()
        v, extra = simple_variants(A)
        meta["r1_module48"] = export_asm(A, v, glb, tol=0.2, ang=0.3) | {"tray_cad_mm": list(M48_TRAY_CAD_MM)}
        meta["module_blocks"] = A.extra["blocks"]
    if "cabinet" in only:
        A = build_cabinet(0.0)
        v, _ = simple_variants(A, "closed")
        Ao = build_cabinet(105.0)
        v.update(simple_variants(Ao, "open")[0])
        meta["r1_ups_cabinet"] = export_asm(A, v, glb, tol=0.5, ang=0.35) | {"shelf_pitch_mm": CAB_SHELF_PITCH_MM}
    meta_path.write_text(json.dumps(meta, indent=1, default=float))
    print(f"CAD done in {time.time()-t0:.1f} s -> {OUT}")


if __name__ == "__main__":
    main()
