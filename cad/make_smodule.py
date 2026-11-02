"""Engineering designs D3-D5 (concept): P1 planar salt-iron cell, SM-48T 48 V module with its thermal-management
architecture, and the SC-UPS-1 cabinet - parametric build123d CAD + CADCraft drawings.

CONCEPT - NOT FOR FABRICATION. Every dimension comes from params/smodule_params.py (all [ASSUMPTION]) and the thermal
envelope from sim/s16_module_thermal (run it first). Material choices are candidates; seal/material compatibility at
190-260 C in NaAlCl4 is NOT established (qualification tests QT-xx in the part lists).

Coordinates (mm): x = rack width (0 = centre), y = depth (front panel face y = 0, +y into the rack), z = up (0 = module floor).

Outputs  cad/out/smodule/
  p1_cell.step                         P1 product cell (named solids)
  sm48t_module.step, sm48t_exploded.step, sm48t_cutaway.step
  sc_ups1_cabinet.step                 cabinet with 3 simplified modules
  sm48t_partlist.csv, sc_ups1_partlist.csv, p1_cell_partlist.csv   item, part, material spec, qty, mass, tolerance, QT, BOM
  smodule_meta.json                    key dimensions, masses, energy, Wh/kg, Wh/L
         cad/out/stl/<assembly>/<variant>/<render-group>.stl      (Blender: renders/blender_salt.py)
Drawings drawings/out/SB-SM-001 (module GA), SB-TM-001 (thermal wall section + budget), SB-UPS-001 (cabinet GA)

Usage: python cad/make_smodule.py [--no-drawing] [--no-step]
"""
from __future__ import annotations
import csv, json, math, sys
from collections import defaultdict
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "drawings"))
from build123d import Align, Axis, Box, Color, Compound, Cylinder, Location, export_step, export_stl  # noqa: E402
from params.smodule_params import CABINET as CB, MODULE as M, P1, THERMAL as TH  # noqa: E402

OUT = LAB / "cad" / "out" / "smodule"; OUT.mkdir(parents=True, exist_ok=True)
STL = LAB / "cad" / "out" / "stl"
MIN3 = (Align.MIN, Align.MIN, Align.MIN)

# material key -> (specification, density g/cm3, render group)
MAT = {
    "beta":    ("beta''-alumina plate, Li/Mg-stabilised, >=98 % dense, both faces lapped", 3.26, "beta"),
    "alpha":   ("alpha-alumina 99.5 %, glass-sealed frame/feedthrough", 3.95, "alpha"),
    "ni201":   ("Ni 201 sheet 0.5 mm, deep drawn (cathode can / + tab)", 8.89, "nickel"),
    "ss316":   ("SS 316L sheet 0.5 mm, deep drawn (anode can / - tab)", 7.99, "stainless"),
    "mica":    ("phlogopite mica sheet 2 mm (cell spacer, 250 C rated)", 2.8, "mica"),
    "heater":  ("mica-insulated plate heater 150 W, 48 V DC, 260 C max", 3.0, "heater"),
    "cu_ni":   ("C110 copper bar, Ni-plated 10 um", 8.94, "busbar"),
    "ss304":   ("SS 304 1.0 mm welded inner can", 7.93, "stainless_dark"),
    "insul":   ("evacuated SS double-wall panel, microporous silica core, k_eff 0.005 W/m.K [ASSUMPTION]", 0.30, "insulation"),
    "steel":   ("DC01 steel 1.2 mm, zinc + powder coat RAL 7016", 7.85, "case"),
    "panel":   ("AL 5052-H32 3 mm front panel, anodised black", 2.68, "panel"),
    "pcb":     ("FR-4 1.6 mm, BMS-48T (SCM-1 derived) [concept]", 1.85, "pcb"),
    "relay":   ("150 A 60 V DC contactor, sealed", 2.0, "black"),
    "fuse":    ("125 A 80 V DC fuse, bolt-down", 3.0, "fuse"),
    "conn_r":  ("panel power connector, 120 A, red (+)", 2.0, "red"),
    "conn_k":  ("panel power connector, 120 A, black (-)", 2.0, "black"),
    "rj45":    ("RJ45 CAN/RS-485 jack", 2.0, "black"),
    "switch":  ("DC isolator 160 A, rotary", 2.0, "accent"),
    "led":     ("status light-pipe", 1.2, "led"),
    "handle":  ("AL handle, anodised", 2.7, "handle"),
    "fan":     ("80 mm 48 V fan + motorised damper (cooling bypass)", 1.5, "black"),
    "rail":    ("telescopic slide rail, zinc steel", 7.85, "stainless"),
    "cab":     ("steel 1.5 mm, powder coat RAL 7035", 7.85, "cab_paint"),
    "cabframe": ("steel 40x40 frame section, powder coat RAL 9005", 7.85, "cab_frame"),
    "door":    ("perforated steel door 1.5 mm, 63 % open area", 7.85, "cab_door"),
    "glass":   ("controller HMI glass", 2.5, "glass"),
    "cable_r": ("35 mm2 DC cable, red", 4.0, "red"),
    "cable_k": ("35 mm2 DC cable, black", 4.0, "black"),
    "breaker": ("DC MCCB 160 A 2-pole", 2.0, "black"),
    "plinth":  ("steel plinth 100 mm, RAL 9005", 7.85, "cab_frame"),
}


def box(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0, align=MIN3).moved(Location((x0, y0, z0)))


def shell(x0, x1, y0, y1, z0, z1, t):
    return box(x0, x1, y0, y1, z0, z1) - box(x0 + t, x1 - t, y0 + t, y1 - t, z0 + t, z1 - t)


def cyl(r, h, axis, c):
    rot = {"x": (0, 90, 0), "y": (90, 0, 0), "z": (0, 0, 0)}[axis]
    return Cylinder(r, h, rotation=rot).moved(Location(c))


class Asm:
    def __init__(self, name):
        self.name, self.parts = name, []

    def add(self, item, name, shape, mat, tol="ISO 2768-mK", qt="-", bom="-", role="part"):
        self.parts.append(dict(item=item, name=name, shape=shape, mat=mat, tol=tol, qt=qt, bom=bom, role=role))

    def shapes(self, pred=lambda p: True, xform=None):
        out = []
        for p in self.parts:
            if pred(p):
                s = xform(p) if xform else p["shape"]
                if s is None: continue
                s.label = f"{p['item']:03d} {p['name']}"; out.append(s)
        return out

    def step(self, path, xform=None):
        export_step(Compound(children=self.shapes(xform=xform), label=self.name), str(path))

    def stl_groups(self, variant, xform=None):
        d = STL / self.name / variant; d.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*.stl"): f.unlink()
        groups = defaultdict(list)
        for p in self.parts:
            s = xform(p) if xform else p["shape"]
            if s is not None and s.volume > 1e-6:
                groups[MAT[p["mat"]][2]].append(s)
        for g, ss in groups.items():
            export_stl(Compound(ss), str(d / f"{g}.stl"), tolerance=0.05, angular_tolerance=0.3)
        return sorted(groups)

    def partlist(self, path):
        agg = {}
        for p in self.parts:
            k = p["item"]; m = p["shape"].volume / 1000 * MAT[p["mat"]][1]
            if k not in agg:
                agg[k] = dict(item=k, part=p["name"], material=MAT[p["mat"]][0], qty=0, unit_mass_g=round(m, 2), total_mass_g=0.0,
                              tolerance_spec=p["tol"], qualification_test=p["qt"], bom_item=p["bom"])
            agg[k]["qty"] += 1; agg[k]["total_mass_g"] = round(agg[k]["total_mass_g"] + m, 1)
        rows = [agg[k] for k in sorted(agg)]
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        return rows


# ================================================================= P1 cell (z = 0 at anode-can floor)
def p1_cell(a: Asm | None, x, y, z, k=0, item0=1):
    """Adds one P1 cell to assembly a at (x, y, z) (cell centre in x/y). Returns z of the top face."""
    o = P1["outer_mm"] / 2; pl = P1["plate_mm"] / 2; w = P1["can_wall_mm"]
    za = P1["can_wall_mm"] + P1["anode_gap_mm"]; zp = za + P1["plate_t_mm"]; zt = P1["thickness_mm"]
    parts = [
        (item0, "P1 anode can (Na reservoir + SS wick), SS 316L", box(-o, o, -o, o, 0, za) - box(-o + w, o - w, -o + w, o - w, w, za + 0.01), "ss316",
         "drawn can, flange flat 0.05", "QT-07 Na compat.", "PM-01"),
        (item0 + 1, "P1 beta''-alumina plate 150 x 150 x 1.0", box(-pl, pl, -pl, pl, za, zp), "beta", "150 +0/-0.2; t 1.0 +/-0.05; flat 0.05",
         "QT-01, QT-02, G5 (scale-up)", "PM-02"),
        (item0 + 2, "P1 alpha-alumina seal frame (glass-sealed to plate)", box(-o, o, -o, o, za, zp) - box(-pl, pl, -pl, pl, za - 0.01, zp + 0.01), "alpha",
         "frame flat 0.03", "QT-02, QT-03", "PM-03"),
        (item0 + 3, "P1 cathode can (granule bed + Mo collector), Ni 201", box(-o, o, -o, o, zp, zt) - box(-o + w, o - w, -o + w, o - w, zp - 0.01, zt - w), "ni201",
         "drawn can, flange flat 0.05", "QT-04, QT-05", "PM-04"),
        (item0 + 4, "P1 + tab (Ni 201)", box(-o - 5, -o, 8, 8 + P1["tab_w_mm"], zt - 2.5, zt - 1.5), "ni201", "-", "-", "PM-04"),
        (item0 + 5, "P1 - tab (SS 316L)", box(-o - 5, -o, -8 - P1["tab_w_mm"], -8, 1.0, 2.0), "ss316", "-", "-", "PM-01"),
    ]
    if a is not None:
        for it, nm, s, mt, tol, qt, bom in parts:
            a.add(it, nm, s.moved(Location((x, y, z))), mt, tol, qt, bom, role="cell")
    return parts


# ================================================================= SM-48T module
def module_geom():
    g = json.load(open(LAB / "sim/s16_module_thermal/out/s16_results.json"))["geometry"]
    ix, iy, iz = g["inner_mm"]; ox, oy, oz = g["hotbox_outer_mm"]
    bay = M["front_bay_mm"]; yc = bay + oy / 2; zc = oz / 2
    return dict(ix=ix, iy=iy, iz=iz, ox=ox, oy=oy, oz=oz, bay=bay, yc=yc, zc=zc, depth=bay + oy + 52.0,
                col=P1["outer_mm"] / 2 + M["stack_gap_mm"] / 2, z0=zc - iz / 2 + 5.0, stack_h=g["stack_h_mm"])


def sm48t(full_cells=True) -> tuple[Asm, dict]:
    a = Asm("sm48t_module"); G = module_geom(); W = G["ox"] / 2; D = G["depth"]; H = G["oz"]
    t_in, t_ins, t_out = M["inner_wall_mm"], M["insulation_mm"], M["outer_wall_mm"]
    # outer case (whole module) + bulkheads
    a.add(1, "outer case (steel, powder coat)", shell(-W, W, 0, D, 0, H, t_out), "steel", "sheet-metal ISO 2768-m", "-", "PM-10", "shell")
    a.add(2, "bay/hot-box bulkhead", box(-W + t_out, W - t_out, G["bay"], G["bay"] + t_out, t_out, H - t_out), "steel", "-", "-", "PM-10", "shell")
    a.add(2, "hot-box/rear bulkhead", box(-W + t_out, W - t_out, G["bay"] + G["oy"] - t_out, G["bay"] + G["oy"], t_out, H - t_out), "steel", "-", "-", "PM-10", "shell")
    # D4 thermal architecture: evacuated insulation shell, inner can, heaters, cooling bypass
    hx, hy, hz = G["ix"] / 2 + t_in, G["iy"] / 2 + t_in, G["iz"] / 2 + t_in
    a.add(3, f"evacuated insulation shell {t_ins:.0f} mm (D4)", box(-hx - t_ins, hx + t_ins, G["yc"] - hy - t_ins, G["yc"] + hy + t_ins, G["zc"] - hz - t_ins, G["zc"] + hz + t_ins)
          - box(-hx, hx, G["yc"] - hy, G["yc"] + hy, G["zc"] - hz, G["zc"] + hz), "insul", "panel joints <= 2 mm, overlapped", "QT-20 standby loss <= 25 W at 25 C", "PM-11", "shell")
    a.add(4, "inner hot can SS 304 (welded, He-tight)", shell(-hx, hx, G["yc"] - hy, G["yc"] + hy, G["zc"] - hz, G["zc"] + hz, t_in), "ss304",
          "weld leak <1e-6 mbar.L/s", "QT-21 He leak", "PM-12", "shell")
    for k, (x0, x1, y0, y1) in enumerate(((-G["ix"] / 2, -G["ix"] / 2 + 2, G["yc"] - 160, G["yc"] + 160), (G["ix"] / 2 - 2, G["ix"] / 2, G["yc"] - 160, G["yc"] + 160),
                                          (-160, 160, G["yc"] - G["iy"] / 2, G["yc"] - G["iy"] / 2 + 2), (-160, 160, G["yc"] + G["iy"] / 2 - 2, G["yc"] + G["iy"] / 2))):
        a.add(5, "mica plate heater 150 W (D4)", box(x0, x1, y0, y1, G["zc"] - 95, G["zc"] + 95), "heater", "-", "QT-22 heater 1000 h at 260 C", "PM-13", "internal")
    yr = G["bay"] + G["oy"]
    a.add(6, "cooling-bypass duct (rear, through insulation) (D4)", shell(-40, 40, G["yc"] + hy, yr + 2, H - 95, H - 50, 1.0), "ss304", "-", "QT-23 damper leak", "PM-14", "internal")
    a.add(6, "cooling-bypass duct, intake (D4)", shell(-40, 40, G["yc"] + hy, yr + 2, 50, 95, 1.0), "ss304", "-", "QT-23", "PM-14", "internal")
    a.add(7, "rear fan 80 mm + motorised damper (D4)", cyl(40, 25, "y", (0, yr + 14, H - 72.5)) - cyl(36, 26, "y", (0, yr + 14, H - 72.5)), "fan", "-", "-", "PM-15", "internal")
    a.add(7, "rear fan hub", cyl(16, 20, "y", (0, yr + 14, H - 72.5)), "fan", "-", "-", "PM-15", "internal")
    # cells: 4 columns x 21 cells, mica spacers, series straps
    n = 0
    for cx in (-G["col"], G["col"]):
        for cy in (G["yc"] - G["col"], G["yc"] + G["col"]):
            for k in range(M["series"]):
                z = G["z0"] + k * (P1["thickness_mm"] + M["stack_pitch_mm"])
                if full_cells or k in (0, M["series"] - 1):
                    p1_cell(a, cx, cy, z, k, item0=20); n += 1
                if k < M["series"] - 1:
                    o = P1["outer_mm"] / 2
                    a.add(30, "mica spacer 2 mm", box(cx - o, cx + o, cy - o, cy + o, z + P1["thickness_mm"], z + P1["thickness_mm"] + M["stack_pitch_mm"]), "mica",
                          "-", "-", "PM-05", "cell")
                    sx = cx - o - 5 if cx < 0 else cx + o
                    a.add(31, "series strap Ni 201 0.5 mm", box(sx if cx < 0 else sx, sx + 5, cy - 12, cy + 12, z + 1.5, z + P1["thickness_mm"] + M["stack_pitch_mm"] + 6.5),
                          "ni201", "resistance-welded", "QT-24 weld pull", "PM-06", "cell")
    # busbars (+ top, - bottom) and front feedthroughs
    ztop = G["z0"] + M["series"] * (P1["thickness_mm"] + M["stack_pitch_mm"]) + 1
    a.add(40, "+ busbar (Cu, Ni-plated) 30 x 5", box(-G["col"] - 20, G["col"] + 20, G["yc"] - 15, G["yc"] + 15, ztop, ztop + 5), "cu_ni", "-", "-", "PM-07", "internal")
    a.add(40, "+ busbar riser to feedthrough", box(-15, 15, G["yc"] - hy + 2, G["yc"] - 15, ztop, ztop + 5), "cu_ni", "-", "-", "PM-07", "internal")
    a.add(41, "- busbar (Cu, Ni-plated) 30 x 5", box(-G["col"] - 20, G["col"] + 20, G["yc"] - 15, G["yc"] + 15, G["z0"] - 4.5, G["z0"] - 0.5), "cu_ni", "-", "-", "PM-07", "internal")
    a.add(41, "- busbar riser to feedthrough", box(-15, 15, G["yc"] - hy + 2, G["yc"] - 15, G["z0"] - 4.5, G["z0"] - 0.5), "cu_ni", "-", "-", "PM-07", "internal")
    for zz in (ztop + 2.5, G["z0"] - 2.5):
        a.add(42, "ceramic power feedthrough (alpha-alumina, brazed)", cyl(9, G["yc"] - hy - G["bay"] + 4, "y", (0, (G["yc"] - hy + G["bay"]) / 2, zz)), "alpha",
              "He leak <1e-8", "QT-25 feedthrough thermal cycling", "PM-08", "internal")
    # front panel (19-inch, 7U) + cold-bay electronics
    PW, PH = M["rack_width_mm"] / 2, M["height_mm"]
    pnl = box(-PW, PW, -3, 0, 0, PH)
    for xs in (-PW + 7.9, PW - 7.9):
        for zs in (22.2, PH / 2, PH - 22.2):
            pnl = pnl - box(xs - 3.25, xs + 3.25, -4, 1, zs - 5, zs + 5)
    a.add(50, "front panel 19 in 7U (AL 5052, black)", pnl, "panel", "EIA-310 hole pattern", "-", "PM-20", "front")
    for xh in (-PW + 30, PW - 30):
        a.add(51, "front handle", box(xh - 8, xh + 8, -38, -3, 70, 80) + box(xh - 8, xh + 8, -38, -3, PH - 80, PH - 70) + box(xh - 8, xh + 8, -38, -28, 70, PH - 70),
              "handle", "-", "-", "PM-21", "front")
    a.add(52, "power connector + (120 A)", cyl(13, 30, "y", (-150, -15, 90)), "conn_r", "-", "-", "PM-22", "front")
    a.add(53, "power connector - (120 A)", cyl(13, 30, "y", (-150, -15, 50)), "conn_k", "-", "-", "PM-22", "front")
    a.add(54, "DC isolator 160 A (rotary)", box(80, 140, -12, 0, 40, 100) + cyl(12, 18, "y", (110, -18, 70)), "switch", "-", "-", "PM-23", "front")
    for k in range(2):
        a.add(55, "RJ45 CAN / RS-485", box(-60 + 22 * k, -42 + 22 * k, -6, 2, 220, 236), "rj45", "-", "-", "PM-24", "front")
    for k in range(4):
        a.add(56, "status LED (light pipe)", cyl(3, 6, "y", (40 + 16 * k, -4, 250)), "led", "-", "-", "PM-25", "front")
    a.add(57, "BMS-48T board (cold bay)", box(-190, 190, 18, 20, 150, 270), "pcb", "-", "QT-26 HIL test", "PM-26", "bay")
    a.add(58, "main contactor 150 A", box(-120, -60, 25, 65, 20, 110), "relay", "-", "-", "PM-27", "bay")
    a.add(59, "main fuse 125 A", cyl(11, 70, "x", (10, 45, 40)), "fuse", "-", "-", "PM-28", "bay")
    for xs in (-W - 6, W):
        a.add(60, "slide rail", box(xs, xs + 6, 20, D - 10, 40, 75), "rail", "-", "-", "PM-29", "shell")
    meta = dict(G, cells_modelled=n, ztop=ztop, panel_w=2 * PW, panel_h=PH)
    return a, meta


# ================================================================= SC-UPS-1 cabinet
def module_shell_parts(a: Asm, z_off, label):
    """Simplified SM-48T for the cabinet: case, panel, handles, connectors, isolator (no internals)."""
    G = module_geom(); W = G["ox"] / 2; D = G["depth"]; PW, PH = M["rack_width_mm"] / 2, M["height_mm"]
    y_off = 40.0
    mv = lambda s: s.moved(Location((0, y_off, z_off)))
    a.add(10, f"SM-48T module ({label})", mv(box(-W, W, 0, D, 0, G["oz"])), "steel", "-", "-", "SM-48T", "module")
    a.add(11, f"SM-48T front panel ({label})", mv(box(-PW, PW, -3, 0, 0, PH)), "panel", "-", "-", "SM-48T", "module")
    for xh in (-PW + 30, PW - 30):
        a.add(12, "module handle", mv(box(xh - 8, xh + 8, -38, -3, 70, 80) + box(xh - 8, xh + 8, -38, -3, PH - 80, PH - 70) + box(xh - 8, xh + 8, -38, -28, 70, PH - 70)), "handle", "-", "-", "SM-48T", "module")
    a.add(13, "module + connector", mv(cyl(13, 30, "y", (-150, -15, 90))), "conn_r", "-", "-", "SM-48T", "module")
    a.add(13, "module - connector", mv(cyl(13, 30, "y", (-150, -15, 50))), "conn_k", "-", "-", "SM-48T", "module")
    a.add(14, "module isolator", mv(box(80, 140, -12, 0, 40, 100) + cyl(12, 18, "y", (110, -18, 70))), "switch", "-", "-", "SM-48T", "module")
    for k in range(4):
        a.add(15, "module LED", mv(cyl(3, 6, "y", (40 + 16 * k, -4, 250))), "led", "-", "-", "SM-48T", "module")


def cabinet(door_open=False) -> tuple[Asm, dict]:
    a = Asm("sc_ups1_cabinet"); X = CB["width_mm"] / 2; Y = CB["depth_mm"]; Z = CB["height_mm"]; P = CB["plinth_mm"]; f = CB["frame_mm"]; t = CB["panel_mm"]
    a.add(1, "plinth 100 mm", shell(-X, X, 0, Y, 0, P, 3.0), "plinth", "-", "-", "PC-01")
    for xs in (-X, X - f):
        for ys in (0, Y - f):
            a.add(2, "frame post 40 x 40", box(xs, xs + f, ys, ys + f, P, Z), "cabframe", "-", "-", "PC-02")
    for zs in (P, Z - f):
        a.add(3, "frame rail (front/rear)", box(-X, X, 0, f, zs, zs + f), "cabframe", "-", "-", "PC-02")
        a.add(3, "frame rail (front/rear)", box(-X, X, Y - f, Y, zs, zs + f), "cabframe", "-", "-", "PC-02")
    a.add(4, "side panel L", box(-X - t, -X, f, Y - f, P, Z), "cab", "-", "-", "PC-03")
    a.add(4, "side panel R", box(X, X + t, f, Y - f, P, Z), "cab", "-", "-", "PC-03")
    a.add(5, "rear panel (louvred)", box(-X + f, X - f, Y - t, Y, P, Z), "cab", "-", "-", "PC-03")
    a.add(6, "roof with vent", box(-X, X, 0, Y, Z, Z + t) - box(-150, 150, 200, 600, Z - 1, Z + t + 1), "cab", "-", "-", "PC-04")
    a.add(6, "roof vent grille", box(-150, 150, 200, 600, Z, Z + t * 0.6), "door", "-", "-", "PC-04")
    rx = M["rack_width_mm"] / 2 - 7.9
    for xs in (-rx - 8, rx - 8):
        for ys in (30.0, 40.0 + 620.0):
            a.add(7, "19-in mounting rail (EIA-310)", box(xs, xs + 16, ys, ys + 2.5, P + 20, Z - f - 10), "rail", "-", "-", "PC-05")
    u = M["u_mm"]; z = P + 40.0
    a.add(8, "vent panel 1U", box(-M["rack_width_mm"] / 2, M["rack_width_mm"] / 2, 37, 40, z, z + u - 0.8), "door", "-", "-", "PC-06"); z += u
    zmods = []
    for k in range(CB["modules"]):
        module_shell_parts(a, z, f"#{k + 1}"); zmods.append(z); z += M["rack_u"] * u
    a.add(20, "controller 2U (HMI, CAN master, SNMP)", box(-M["rack_width_mm"] / 2, M["rack_width_mm"] / 2, 37, 400, z, z + 2 * u - 0.8), "steel", "-", "-", "PC-10")
    a.add(21, "controller HMI glass", box(-120, 40, 34, 37, z + 12, z + 76), "glass", "-", "-", "PC-10"); zc = z; z += 2 * u
    a.add(22, "DC breaker panel 2U", box(-M["rack_width_mm"] / 2, M["rack_width_mm"] / 2, 37, 200, z, z + 2 * u - 0.8), "steel", "-", "-", "PC-11")
    for k in range(4):
        a.add(23, "DC MCCB 160 A 2P", box(-170 + 90 * k, -110 + 90 * k, 22, 37, z + 10, z + 78), "breaker", "-", "-", "PC-11")
    zb = z; z += 2 * u
    for k, zm in enumerate(zmods):
        a.add(30, "DC cable + (35 mm2)", box(215, 227, 10, 22, zm + 90, zb + 40), "cable_r", "-", "-", "PC-12")
        a.add(31, "DC cable - (35 mm2)", box(229, 241, 10, 22, zm + 50, zb + 40), "cable_k", "-", "-", "PC-12")
    a.add(32, "earth bar", box(-200, 200, Y - 60, Y - 50, P + 30, P + 45), "cu_ni", "-", "-", "PC-13")
    # door (hinge at x = -X, y = 0); open variant swings out
    dr = box(-X, X, -22, 0, P, Z) - box(-X + 50, X - 50, -23, 1, P + 50, Z - 50)
    dp = box(-X + 50, X - 50, -12, -10.5, P + 50, Z - 50)
    hd = box(X - 45, X - 30, -45, -22, P + 600, P + 760)
    if door_open:
        ax = Axis((-X, 0, 0), (0, 0, 1))
        dr, dp, hd = dr.rotate(ax, -CB["door_open_deg"]), dp.rotate(ax, -CB["door_open_deg"]), hd.rotate(ax, -CB["door_open_deg"])
    a.add(40, "door frame", dr, "cab", "-", "-", "PC-14"); a.add(41, "door perforated sheet", dp, "door", "-", "-", "PC-14")
    a.add(42, "door handle", hd, "handle", "-", "-", "PC-14")
    return a, dict(z_modules=zmods, z_controller=zc, z_breakers=zb, z_top_used=z, X=X, Y=Y, Z=Z)


# ================================================================= variants
def cut_half(p):
    """Cutaway: shells and front parts lose their x > 0 half; cells and internals stay whole."""
    if p["role"] in ("shell", "front", "bay") or p["item"] in (5, 6):      # heaters/ducts on the cut side would hide the cell stacks
        r = p["shape"] & box(-1000, 0, -500, 1500, -500, 1500)
        return r if r.volume > 1e-3 else None
    return p["shape"]


def exploded(p):
    off = {"shell": (0, 0, 0), "front": (0, -160, 0), "bay": (0, -90, 0), "internal": (0, 0, 0), "cell": (0, 0, 0)}
    it = p["item"]
    if it == 1: return p["shape"].moved(Location((0, 0, 420)))
    if it == 3: return p["shape"].moved(Location((0, 0, 270)))
    if it == 4: return p["shape"].moved(Location((0, 0, 140)))
    if it == 2: return p["shape"].moved(Location((0, 0, 420)))
    if it in (60,): return p["shape"].moved(Location((0, 0, 420)))
    return p["shape"].moved(Location(off[p["role"]]))


# ================================================================= drawings
def drawings(meta, cab_meta, th):
    import make_drawings as MD
    G = meta; W = G["ox"] / 2; D = G["depth"]; H = G["oz"]; PW, PH = M["rack_width_mm"] / 2, M["height_mm"]
    status = {}
    # ---------------- SB-SM-001 module GA, 1:4
    S = 4.0; sh = MD.Sheet("SB-SM-001", "SM-48T 48 V SALT-IRON MODULE - GA", S, "1:4"); sh.dimstyle("SB", 1.0, dec=0)
    FX, FZ = 520.0, 900.0                                    # front view origin (x centre, z = 0)
    sh.rect((FX - PW, FZ), (FX + PW, FZ + PH))
    for xs in (-PW + 7.9, PW - 7.9):
        for zs in (22.2, PH / 2, PH - 22.2): sh.rect((FX + xs - 3.25, FZ + zs - 5), (FX + xs + 3.25, FZ + zs + 5), "THIN")
    sh.circle((FX - 150, FZ + 90), 13); sh.circle((FX - 150, FZ + 50), 13); sh.rect((FX + 80, FZ + 40), (FX + 140, FZ + 100)); sh.circle((FX + 110, FZ + 70), 12)
    for xh in (-PW + 30, PW - 30): sh.rect((FX + xh - 8, FZ + 70), (FX + xh + 8, FZ + PH - 70), "THIN")
    sh.rect((FX - 60, FZ + 220), (FX - 20, FZ + 236), "THIN")
    sh.dim((FX - PW, FZ - 30), (FX + PW, FZ - 30), (FX, FZ - 70), f"{2 * PW:.1f} (19 IN)")
    sh.dim((FX - PW - 30, FZ), (FX - PW - 30, FZ + PH), (FX - PW - 80, FZ + PH / 2), f"{PH:.1f} (7U)")
    sh.text((FX - PW, FZ + PH + 40), "FRONT VIEW", 4.0)
    for k, tg, at in ((52, (FX - 150, FZ + 90), (FX - 300, FZ + 400)), (53, (FX - 150, FZ + 50), (FX - 360, FZ + 360)), (54, (FX + 110, FZ + 70), (FX + 300, FZ + 400)),
                      (50, (FX + 200, FZ + PH - 30), (FX + 330, FZ + 480)), (55, (FX - 40, FZ + 228), (FX - 120, FZ + 450))):
        sh.balloon(k, tg, at)
    # side section A-A (y horizontal, z vertical)
    SX, SZ = 1050.0, 900.0
    sh.rect((SX, SZ), (SX + D, SZ + H))
    sh.rect((SX - 3, SZ), (SX, SZ + PH), "OUTLINE")
    ins0, ins1 = G["yc"] - G["iy"] / 2 - 1 - M["insulation_mm"], G["yc"] + G["iy"] / 2 + 1 + M["insulation_mm"]
    zi0, zi1 = G["zc"] - G["iz"] / 2 - 1 - M["insulation_mm"], G["zc"] + G["iz"] / 2 + 1 + M["insulation_mm"]
    sh.rect((SX + ins0, SZ + zi0), (SX + ins1, SZ + zi1), "OUTLINE", hatch="ANSI37", hs=4.0)
    sh.rect((SX + G["yc"] - G["iy"] / 2 - 1, SZ + G["zc"] - G["iz"] / 2 - 1), (SX + G["yc"] + G["iy"] / 2 + 1, SZ + G["zc"] + G["iz"] / 2 + 1), "OUTLINE", hatch="SOLID")
    sh.rect((SX + G["yc"] - G["iy"] / 2, SZ + G["zc"] - G["iz"] / 2), (SX + G["yc"] + G["iy"] / 2, SZ + G["zc"] + G["iz"] / 2), "OUTLINE")
    sh.rect((SX + G["yc"] - G["iy"] / 2 + 0.01, SZ + G["zc"] - G["iz"] / 2 + 0.01), (SX + G["yc"] + G["iy"] / 2 - 0.01, SZ + G["zc"] + G["iz"] / 2 - 0.01), "THIN", hatch="ANSI37", hs=1.5)
    for cy in (G["yc"] - G["col"], G["yc"] + G["col"]):
        o = P1["outer_mm"] / 2
        sh.rect((SX + cy - o, SZ + G["z0"]), (SX + cy + o, SZ + G["z0"] + G["stack_h"]), "OUTLINE", hatch="ANSI31", hs=3.0)
    sh.rect((SX + G["bay"], SZ + 1.2), (SX + G["bay"] + 1.2, SZ + H - 1.2), "THIN")
    sh.rect((SX + 18, SZ + 150), (SX + 20, SZ + 270), "THIN"); sh.text((SX + 24, SZ + 280), "BMS", 2.5)
    sh.dim((SX, SZ - 30), (SX + D, SZ - 30), (SX + D / 2, SZ - 70), f"{D:.0f}")
    sh.dim((SX, SZ - 100), (SX + G["bay"], SZ - 100), (SX + G["bay"] / 2 + 60, SZ - 135), f"{G['bay']:.0f} COLD BAY")
    sh.dim((SX + ins0, SZ + H + 30), (SX + ins0 + M["insulation_mm"], SZ + H + 30), (SX + ins0 + 120, SZ + H + 65), f"{M['insulation_mm']:.0f} INSUL.")
    sh.dim((SX + D + 30, SZ + G["z0"]), (SX + D + 30, SZ + G["z0"] + G["stack_h"]), (SX + D + 80, SZ + G["z0"] + G["stack_h"] / 2), f"{G['stack_h']:.0f} (21 CELLS)")
    for k, tg, at in ((57, (SX + 19, SZ + 200), (SX + 10, SZ + H + 150)), (3, (SX + ins0 + 20, SZ + zi1 - 20), (SX + 130, SZ + H + 150)),
                      (4, (SX + G["yc"] - G["iy"] / 2, SZ + G["zc"] + 60), (SX + 250, SZ + H + 150)),
                      (20, (SX + G["yc"] - G["col"], SZ + G["z0"] + 100), (SX + 370, SZ + H + 150)), (6, (SX + D - 40, SZ + H - 72), (SX + D + 90, SZ + H + 110))):
        sh.balloon(k, tg, at)
    sh.text((SX, SZ - 210), "SECTION A-A (THROUGH COLUMN CENTRES)", 4.0)
    # item table + spec block
    rows = [["ITEM", "PART", "QTY", "MATERIAL / SPEC"]]
    for r in meta["partlist"][:22]:
        rows.append([r["item"], r["part"][:44], r["qty"], r["material"][:70]])
    sh.table(60.0, 720.0, [12, 86, 12, 140], rows, h=2.0, row_h=4.2, title="ITEM LIST (cad/out/smodule/sm48t_partlist.csv)")
    spec = [["PARAMETER", "VALUE"], ["CONFIG", f"{M['series']}S{M['parallel']}P = {M['cells']} P1 CELLS"], ["V NOM / MAX / MIN", f"{M['V_nom']:.1f} / {M['V_max']:.2f} / {M['V_min']:.1f} V"],
            ["CAPACITY / ENERGY", f"{M['Ah']:.1f} Ah / {M['kWh']:.2f} kWh"], ["MAX CONT. POWER", f"{M['P_max_kW']:.2f} kW (C/1.7)"],
            ["OPERATING T", f"{TH['T_op_C']:.0f} C (180-260)"], ["STANDBY LOSS", f"{th['standby_design']['evacuated_W']:.0f} W @ 25 C"],
            ["MASS (CALC.)", f"{meta['mass_kg']:.1f} kg"], ["Wh/kg / Wh/L", f"{meta['Wh_kg']:.0f} / {meta['Wh_L']:.0f}"]]
    sh.table(1150.0, 720.0, [42, 70], spec, h=2.2, row_h=4.6, title="RATING [CALCULATED FROM ASSUMPTIONS]")
    sh.notes(60.0, 260.0, ["NOTES", "1. CONCEPT. P1 CELL (150 MM PLATE) NOT YET MADE; R0 GATES G1-G5 MUST PASS FIRST.",
                           "2. HOT BOX 190 C; COLD BAY < 60 C. ONLY ITEMS 40-42 CROSS THE INSULATION.",
                           "3. 21S: 57.75 V MAX < 60 V SELV. 15-MIN UPS NOT POSSIBLE (40 MA/CM2 LIMIT = C/1.5).",
                           "4. HEATERS 4 X 150 W ON INDEPENDENT 270 C THERMAL CUT-OUTS (HW, NOT FIRMWARE).",
                           "5. COOLING BYPASS (ITEMS 6-7) OPENS ONLY ABOVE 260 C OR ON BMS FAULT."], h=2.2, step=4.2)
    sh.frame("SOURCE: params/smodule_params.py, cad/make_smodule.py")
    status["SB-SM-001"] = run_sheet(MD, sh)
    # ---------------- SB-TM-001 thermal wall section 1:1 + budget
    S = 1.0; sh = MD.Sheet("SB-TM-001", "SM-48T THERMAL ARCHITECTURE (D4)", S, "1:1"); sh.dimstyle("SB", 1.0, dec=1)
    X0, Z0 = 60.0, 200.0
    layers = [("CELL STACK (P1 CELLS + MICA)", 30.0, "ANSI31"), ("GAP / HEATER 150 W", 10.0, None), ("INNER CAN SS304 1.0", 1.0, "SOLID"),
              ("EVACUATED PANEL 40 (k_eff 0.005)", M["insulation_mm"], "ANSI37"), ("OUTER CASE 1.2", 1.2, "SOLID")]
    x = X0
    for name, w, hp in layers:
        sh.rect((x, Z0), (x + w, Z0 + 120), "OUTLINE", hatch=hp, hs=0.6)
        i = layers.index((name, w, hp))
        sh.leader((x + w / 2, Z0 + 118), (x + w / 2 + 4, Z0 + 140 + 12 * (len(layers) - 1 - i)), name, 2.4)
        x += w
    sh.text((X0, Z0 - 12), "HOT 190 C", 3.0); sh.text((x - 20, Z0 - 12), "AMBIENT 25-45 C", 3.0)
    for zz in (Z0 + 30, Z0 + 60, Z0 + 90): sh.flow([(X0 + 20, zz), (x + 25, zz)])
    sh.dim((X0 + 41, Z0 - 25), (X0 + 41 + M["insulation_mm"], Z0 - 25), (X0 + 61, Z0 - 35), f"{M['insulation_mm']:.0f}")
    sd = th["standby_design"]; wu = th["warmup"]; ds = th["discharge"]
    tb = [["THERMAL BUDGET (S16)", "VALUE"], ["STANDBY, EVACUATED 40 MM", f"{sd['evacuated_W']} W ({sd['evacuated_kWh_day']} kWh/day)"],
          ["  AS SHARE OF STORED ENERGY", f"{100 * sd['evacuated_frac_of_capacity_per_day']:.1f} %/day"], ["STANDBY, MICROPOROUS 40 MM", f"{sd['microporous_W']} W"],
          ["ANNUAL KEEP-WARM", f"{sd['evacuated_kWh_yr']} kWh = USD {sd['evacuated_usd_yr']}"], ["SELF-HEAT IF GRID LOST", f"{sd['self_sustain_hours_if_grid_lost']} h"],
          ["WARM-UP, 600 W HEATERS", f"{wu['600 W']['hours']} h (RAMP FLOOR {th['warmup_ramp_limited_floor_h']} h)"],
          ["DISCHARGE HEAT AT MAX POWER", f"{ds['heat_W']} W vs {ds['standby_loss_W']} W LOSS"], ["ADIABATIC RISE, FULL DISCHARGE", f"{ds['adiabatic_rise_C']} K (WINDOW 70 K)"],
          ["HOT-BOX HEAT CAPACITY", f"{th['heat_capacity_kJ_K']} kJ/K"]]
    sh.table(300.0, 330.0, [62, 80], tb, h=2.2, row_h=5.0, title="FROM sim/s16_module_thermal/out/s16_results.json [CALCULATED]")
    sh.notes(60.0, 120.0, ["CONTROL ARCHITECTURE", "1. 4 HEATER ZONES, PID ON 4 THERMOCOUPLES; HW CUT-OUT 270 C PER ZONE (BIMETAL, NOT FIRMWARE).",
                           "2. RAMP <= 2 C/MIN BOTH WAYS (CERAMIC + GLASS SEAL); FREEZE/THAW CYCLES COUNTED BY BMS.",
                           "3. BYPASS DAMPER NORMALLY CLOSED; OPENS > 260 C OR BMS FAULT; FAN 20 CFM.",
                           "4. COLD BAY (BMS, CONTACTOR) KEPT < 60 C BY BULKHEAD + 1 W/K PASSIVE VENTING.",
                           "5. VALUES ARE MODEL OUTPUTS FROM ASSUMED k AND cp - QT-20 MUST MEASURE STANDBY LOSS."], h=2.2, step=4.6)
    sh.frame("SOURCE: sim/s16_module_thermal/thermal.py, params/smodule_params.py")
    status["SB-TM-001"] = run_sheet(MD, sh)
    # ---------------- SB-UPS-001 cabinet GA 1:10
    S = 10.0; sh = MD.Sheet("SB-UPS-001", "SC-UPS-1 SALT-IRON BACKUP CABINET - GA", S, "1:10"); sh.dimstyle("SB", 1.0, dec=0)
    C = cab_meta; X = C["X"]; Y = C["Y"]; Z = C["Z"]; FX, FZ = 1050.0, 900.0
    sh.rect((FX - X, FZ), (FX + X, FZ + CB["plinth_mm"]), "OUTLINE", hatch="ANSI31", hs=10)
    sh.rect((FX - X, FZ + CB["plinth_mm"]), (FX + X, FZ + Z))
    for zm in C["z_modules"]:
        sh.rect((FX - PW, FZ + zm), (FX + PW, FZ + zm + PH)); sh.text((FX - 60, FZ + zm + PH / 2), "SM-48T", 3.0)
    sh.rect((FX - PW, FZ + C["z_controller"]), (FX + PW, FZ + C["z_controller"] + 2 * M["u_mm"])); sh.text((FX - 90, FZ + C["z_controller"] + 30), "CONTROLLER 2U", 2.5)
    sh.rect((FX - PW, FZ + C["z_breakers"]), (FX + PW, FZ + C["z_breakers"] + 2 * M["u_mm"])); sh.text((FX - 90, FZ + C["z_breakers"] + 30), "DC BREAKERS 2U", 2.5)
    sh.dim((FX - X, FZ - 60), (FX + X, FZ - 60), (FX, FZ - 160), f"{CB['width_mm']:.0f}")
    sh.dim((FX - X - 60, FZ), (FX - X - 60, FZ + Z), (FX - X - 200, FZ + Z / 2), f"{CB['height_mm']:.0f}")
    sh.text((FX - X, FZ + Z + 80), "FRONT VIEW (DOOR REMOVED)", 4.0)
    SX = 1750.0
    sh.rect((SX, FZ), (SX + Y, FZ + CB["plinth_mm"]), "OUTLINE", hatch="ANSI31", hs=10); sh.rect((SX, FZ + CB["plinth_mm"]), (SX + Y, FZ + Z))
    for zm in C["z_modules"]:
        sh.rect((SX + 40, FZ + zm), (SX + 40 + G["depth"], FZ + zm + G["oz"]), "HIDDEN")
    sh.rect((SX - 22, FZ + CB["plinth_mm"]), (SX, FZ + Z), "THIN")
    sh.dim((SX, FZ - 60), (SX + Y, FZ - 60), (SX + Y / 2, FZ - 160), f"{CB['depth_mm']:.0f}")
    sh.text((SX, FZ + Z + 80), "SIDE VIEW (PANEL REMOVED)", 4.0)
    spec = [["PARAMETER", "VALUE"], ["MODULES", f"{CB['modules']} x SM-48T ({M['kWh']:.2f} kWh)"], ["ENERGY", f"{CB['kWh']:.1f} kWh @ {M['V_nom']:.0f} V"],
            ["CONT. POWER", f"{CB['modules'] * M['P_max_kW']:.1f} kW (>= 1.7 h)"], ["KEEP-WARM", f"{CB['modules'] * th['standby_design']['evacuated_W']:.0f} W"],
            ["FOOTPRINT", f"{CB['width_mm']:.0f} x {CB['depth_mm']:.0f} mm"], ["SERVICE", "FRONT: MODULES ON SLIDE RAILS; REAR: CABLE + EARTH"]]
    sh.table(3200.0, 3900.0, [34, 90], spec, h=2.4, row_h=5.2, title="CABINET RATING [CALCULATED FROM ASSUMPTIONS]")
    sh.notes(3200.0, 3250.0, ["NOTES", "1. CONCEPT. FLOOR-STANDING, M12 ANCHORS (4) THROUGH PLINTH; LEVELLING FEET.",
                             "2. SERVICE ACCESS FRONT (DOOR 100 DEG); MODULES 33 KG EACH - 2-PERSON LIFT / LIFT TABLE.",
                             "3. NO FLAMMABLE ELECTROLYTE; FIRE BEHAVIOUR OF A HOT MODULE NOT TESTED (UL 9540A PLANNED).",
                             "4. MODULES ARE 190 C INTERNALLY; OUTER CASE TOUCH-SAFE (< 45 C) BY DESIGN - VERIFY QT-20."], h=2.4, step=5.0)
    sh.frame("SOURCE: params/smodule_params.py (CABINET), cad/make_smodule.py")
    status["SB-UPS-001"] = run_sheet(MD, sh)
    return status


def run_sheet(MD, sh):
    ok, rc, errs = MD.run_cadcraft(sh); tool = "CADCraft"
    if not ok:
        ok, rc, errs = MD.run_cadcraft(sh)
    if not ok:
        MD.fallback_ezdxf(sh); tool = "ezdxf+matplotlib (fallback)"
    MD.paper_png(sh)
    return dict(tool=tool, commands=len(sh.cmds), errors=errs[:5])


# ================================================================= main
def main(argv):
    th = json.load(open(LAB / "sim/s16_module_thermal/out/s16_results.json"))
    meta = {}
    # P1 cell alone
    c = Asm("p1_cell"); p1_cell(c, 0, 0, 0)
    c.stl_groups("full"); rows_c = c.partlist(OUT / "p1_cell_partlist.csv")
    cell_g = sum(r["total_mass_g"] for r in rows_c) + P1["granules_g"] + P1["NaAlCl4_g"]
    meta["p1"] = dict(Ah=round(P1["Ah"], 2), Wh=round(P1["Wh"], 2), thickness_mm=round(P1["thickness_mm"], 2), outer_mm=P1["outer_mm"],
                      hardware_g=round(sum(r["total_mass_g"] for r in rows_c), 1), mass_g=round(cell_g, 1), Wh_kg=round(P1["Wh"] / cell_g * 1000, 1),
                      Wh_L=round(P1["Wh"] / ((P1["outer_mm"] / 10) ** 2 * P1["thickness_mm"] / 10) * 1000, 1))
    # module
    a, g = sm48t(full_cells=True)
    groups = a.stl_groups("full"); a.stl_groups("cutaway", xform=cut_half); a.stl_groups("exploded", xform=exploded)
    rows = a.partlist(OUT / "sm48t_partlist.csv")
    hw_kg = sum(r["total_mass_g"] for r in rows) / 1000
    cath_kg = M["cells"] * (P1["granules_g"] + P1["NaAlCl4_g"]) / 1000
    mass = hw_kg + cath_kg
    vol_L = M["rack_width_mm"] * g["depth"] * M["height_mm"] / 1e6
    meta["sm48t"] = dict(g, partlist=None, render_groups=groups, hardware_kg=round(hw_kg, 2), cathode_kg=round(cath_kg, 2), mass_kg=round(mass, 2),
                         kWh=round(M["kWh"], 3), Wh_kg=round(M["kWh"] * 1000 / mass, 1), Wh_L=round(M["kWh"] * 1000 / vol_L, 1), envelope_L=round(vol_L, 1))
    # cabinet
    cab, cm = cabinet(door_open=False); cab.stl_groups("closed")
    cab_o, _ = cabinet(door_open=True); cab_o.stl_groups("open")
    rows_cab = cab.partlist(OUT / "sc_ups1_partlist.csv")
    meta["cabinet"] = dict(cm, kWh=round(CB["kWh"], 2), modules=CB["modules"])
    if "--no-step" not in argv:
        c.step(OUT / "p1_cell.step"); a.step(OUT / "sm48t_module.step"); a.step(OUT / "sm48t_exploded.step", xform=exploded)
        a.step(OUT / "sm48t_cutaway.step", xform=cut_half); cab.step(OUT / "sc_ups1_cabinet.step")
    if "--no-drawing" not in argv:
        dmeta = dict(g, partlist=rows, mass_kg=mass, Wh_kg=meta["sm48t"]["Wh_kg"], Wh_L=meta["sm48t"]["Wh_L"])
        meta["drawings"] = drawings(dmeta, cm, th)
    (OUT / "smodule_meta.json").write_text(json.dumps(meta, indent=1, default=float))
    print(json.dumps({k: v for k, v in meta.items() if k != "drawings"}, indent=1, default=float)[:3000])
    print("drawings:", json.dumps(meta.get("drawings"), default=str))


if __name__ == "__main__":
    main(sys.argv[1:])
