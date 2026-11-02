"""Salt Battery engineering drawings, generated headless in CADCraft (cadcraft-cli) from params/.

  SB-GA-001  R1 12 V monobloc - general arrangement (front / top / side views, section A-A, detail B vent)  A2 1:2
  SB-GA-002  R1 cell / electrode stack detail (plate, cell section, repeat-unit layers 50:1, layer table)     A2 1:1
  SB-GA-003  R1 UPS cabinet arrangement (front, door removed, side section with airflow, plan section)       A2 1:10

Pattern reused from PARC-Delta prototype/drawings/make_ga_drawing.py (read-only reference): geometry is drawn in
true millimetres in model space, the A2 sheet frame is drawn at (paper mm x scale), DIMSCALE = scale, and the PDF is
plotted at that scale. Outputs drawings/out/<DWG>.{dxf,pdf,png} + <DWG>_paper.png (white sheet rasterised from the PDF).
If CADCraft fails twice for a sheet, the same command list is replayed into ezdxf (DXF) + matplotlib (PDF/PNG).

Usage: python drawings/make_drawings.py [SB-GA-001 SB-GA-002 SB-GA-003]
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
from params.design import cabinet, electrode_stack, monobloc  # noqa: E402
from params.mech_params import (CAB_MECH, CAB_SHELF_PITCH_MM, CAB_TERMINAL_CLEAR_MM, MB_MECH, VENT_ARRANGEMENT,  # noqa: E402
                                monobloc_layout)
from params.product_params import BMS, CABINET, GAS, MAT, MONOBLOC, R1_LOADING  # noqa: E402

OUT = HERE / "out"
OUT.mkdir(parents=True, exist_ok=True)
CADCRAFT = os.environ.get("CADCRAFT", "/Volumes/Aditya ssd/PARC-Delta-Lab/tools/cadcraft/target/release/cadcraft-cli")
DATE = "2026-11-02"
A2 = (594.0, 420.0)
LAYERS = (("OUTLINE", 7, "Continuous", 0.5), ("THIN", 7, "Continuous", 0.18), ("HIDDEN", 8, "HIDDEN", 0.25),
          ("CENTER", 1, "CENTER", 0.18), ("PHANTOM", 6, "PHANTOM", 0.25), ("HATCH", 8, "Continuous", 0.13),
          ("DIM", 5, "Continuous", 0.18), ("TEXT", 7, "Continuous", 0.25), ("BALLOON", 3, "Continuous", 0.25),
          ("BORDER", 7, "Continuous", 0.7), ("FLOW", 4, "Continuous", 0.35))


def f1(x, n=1):
    s = f"{x:.{n}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


class Sheet:
    """Collects CADCraft JSON commands for one drawing (model space in mm, sheet frame at A2 x S)."""

    def __init__(self, dwg, title, S, scale_txt):
        self.dwg, self.title, self.S, self.scale_txt = dwg, title, S, scale_txt
        self.cmds: list[str] = []
        self.cmd("linetype", load="*")
        for name, col, lt, lw in LAYERS:
            self.cmd("layer.new", name=name, color=col, linetype=lt, lineweight=lw)
        self.cmd("ltscale", scale=0.6 * S)
        self.dimstyle("SB", 1.0)
        self.W, self.H = A2[0] * S, A2[1] * S

    # ---------------------------------------------------------------- primitives
    def cmd(self, cid, **p):
        self.cmds.append(f"{cid} {json.dumps(p)}")

    def layer(self, n):
        self.cmd("layer.current", name=n)

    def dimstyle(self, name, factor, dec=2):
        """factor = drawing-to-true scale of the view (e.g. 4 for a 4x enlarged detail); DIMLFAC = 1/factor."""
        self.cmd("dimstyle", name=name, current=True, DIMSCALE=self.S, DIMTXT=2.5, DIMASZ=2.2, DIMEXO=1.0, DIMEXE=1.5,
                 DIMGAP=0.8, DIMDEC=dec, DIMLFAC=1.0 / factor)

    def rect(self, p1, p2, lay="OUTLINE", hatch=None, hs=1.0, ang=0.0, fillet=None):
        self.layer(lay)
        kw = dict(p1=[round(p1[0], 3), round(p1[1], 3)], p2=[round(p2[0], 3), round(p2[1], 3)])
        if fillet:
            kw["fillet"] = fillet
        self.cmd("rectang", **kw)
        if hatch:
            self.layer("HATCH")
            self.cmd("hatch", handles=["{last}"], pattern=hatch, scale=hs, angle=ang)

    def line(self, pts, lay="OUTLINE", closed=False):
        self.layer(lay)
        self.cmd("line", points=[[round(x, 3), round(y, 3)] for x, y in pts], **({"closed": True} if closed else {}))

    def circle(self, c, r, lay="OUTLINE"):
        self.layer(lay)
        self.cmd("circle", center=[round(c[0], 3), round(c[1], 3)], radius=round(r, 3))

    def text(self, at, s, h=3.0, j="L", lay="TEXT", rot=0.0):
        self.layer(lay)
        self.cmd("text", at=[round(at[0], 3), round(at[1], 3)], text=s, height=h * self.S, justify=j, rotation=rot)

    def dim(self, p1, p2, at, text=None, style="SB"):
        self.cmd("dimstyle", name=style, current=True)
        self.layer("DIM")
        kw = dict(p1=[round(p1[0], 3), round(p1[1], 3)], p2=[round(p2[0], 3), round(p2[1], 3)], at=[round(at[0], 3), round(at[1], 3)])
        if text:
            kw["text"] = text
        if abs(p1[0] - p2[0]) < 1e-6:
            kw["rotation"] = 90
        elif abs(p1[1] - p2[1]) < 1e-6:
            kw["rotation"] = 0
        self.cmd("dimlinear", **kw)

    def arrow(self, tip, frm, size=2.2):
        dx, dy = tip[0] - frm[0], tip[1] - frm[1]
        d = math.hypot(dx, dy) or 1.0
        ux, uy = dx / d, dy / d
        a = size * self.S
        b = [tip[0] - ux * a - uy * a * 0.35, tip[1] - uy * a + ux * a * 0.35]
        c = [tip[0] - ux * a + uy * a * 0.35, tip[1] - uy * a - ux * a * 0.35]
        self.cmd("solid", points=[[round(tip[0], 3), round(tip[1], 3)], [round(b[0], 3), round(b[1], 3)], [round(c[0], 3), round(c[1], 3)]])

    def leader(self, target, elbow, s, h=2.6, lay="TEXT"):
        """Note with a leader: arrow at target, line to elbow, short shoulder, text."""
        self.layer(lay)
        right = elbow[0] >= target[0]
        sh = [elbow[0] + (4 if right else -4) * self.S, elbow[1]]
        self.cmd("line", points=[[round(v, 3) for v in target], [round(v, 3) for v in elbow], [round(v, 3) for v in sh]])
        self.arrow(target, elbow, 1.8)
        self.text([sh[0] + (1 if right else -1) * self.S, sh[1]], s, h, "ML" if right else "MR", lay)

    def flow(self, pts):
        self.line(pts, "FLOW")
        self.layer("FLOW")
        self.arrow(pts[-1], pts[-2], 3.0)

    def balloon(self, n, target, at):
        r = 4.0 * self.S
        self.layer("BALLOON")
        dx, dy = target[0] - at[0], target[1] - at[1]
        d = math.hypot(dx, dy) or 1.0
        self.cmd("line", points=[[at[0] + dx / d * r, at[1] + dy / d * r], [round(target[0], 3), round(target[1], 3)]])
        self.cmd("circle", center=[round(at[0], 3), round(at[1], 3)], radius=r)
        self.cmd("circle", center=[round(target[0], 3), round(target[1], 3)], radius=0.6 * self.S)
        self.text(at, str(n), 3.2, "MC", "BALLOON")

    def table(self, x0, ytop, widths, rows, h=2.4, row_h=5.2, title=None):
        S = self.S
        if title:
            self.text([x0, ytop + 2.5 * S], title, 3.0)
        self.layer("THIN")
        tw = sum(widths) * S
        for i in range(len(rows) + 1):
            y = ytop - i * row_h * S
            self.cmd("line", points=[[x0, y], [x0 + tw, y]])
        xx = x0
        for w in widths + [0]:
            self.cmd("line", points=[[xx, ytop], [xx, ytop - len(rows) * row_h * S]])
            xx += w * S
        for i, row in enumerate(rows):
            y = ytop - (i + 0.5) * row_h * S
            xx = x0
            for w, cell in zip(widths, row):
                self.text([xx + 1.2 * S, y], str(cell), h, "ML")
                xx += w * S

    def notes(self, x0, ytop, lines, h=2.4, step=4.4):
        for k, ln in enumerate(lines):
            self.text([x0, ytop - k * step * self.S], ln, 3.0 if k == 0 else h)

    def frame(self, src_note):
        S, W, H = self.S, self.W, self.H
        self.layer("BORDER")
        self.cmd("rectang", p1=[0, 0], p2=[W, H])
        self.cmd("rectang", p1=[10 * S, 10 * S], p2=[W - 10 * S, H - 10 * S])
        x0, x1, y0, y1 = W - 200 * S, W - 10 * S, 10 * S, 72 * S
        self.cmd("rectang", p1=[x0, y0], p2=[x1, y1])
        for y in (24 * S, 36 * S, 48 * S, 60 * S):
            self.cmd("line", points=[[x0, y], [x1, y]])
        self.cmd("line", points=[[x0 + 120 * S, y0], [x0 + 120 * S, 48 * S]])
        tx = x0 + 3 * S
        self.text([tx, 66 * S], f"SALT-BATTERY-LAB  |  {self.title}", 3.4)
        self.text([tx, 54 * S], "CONCEPT — NOT FOR FABRICATION", 3.6)
        self.text([tx, 42 * S], f"DWG {self.dwg}     REV A     SHEET 1/1", 3.0)
        self.text([tx, 30 * S], f"SCALE {self.scale_txt} (A2)  UNITS mm  {DATE}", 2.5)
        self.text([tx, 16 * S], "TOLERANCES: CONCEPT   PROJECTION: 1ST ANGLE", 2.5)
        rx = x0 + 123 * S
        self.text([rx, 42 * S], "CAD: CADCraft (headless CLI)", 2.2)
        self.text([rx, 30 * S], "3D: build123d / OpenCascade", 2.2)
        self.text([rx, 16 * S], src_note, 2.0)
        # first-angle projection symbol
        cx, cy = x0 + 110 * S, 42 * S
        self.layer("THIN")
        self.cmd("circle", center=[cx + 5 * S, cy], radius=2.5 * S)
        self.cmd("circle", center=[cx + 5 * S, cy], radius=1.2 * S)
        self.cmd("line", points=[[cx - 6 * S, cy - 2.5 * S], [cx - 6 * S, cy + 2.5 * S], [cx, cy + 1.5 * S], [cx, cy - 1.5 * S]], closed=True)


# ===================================================================================================== SB-GA-001
def ga001() -> Sheet:
    mb, d, lay, mm = MONOBLOC, monobloc(), monobloc_layout(), MB_MECH
    L, W, H = mb["length_mm"], mb["width_mm"], mb["height_mm"]
    wall, pt, base, lid = mb["wall_mm"], mb["partition_mm"], mb["base_mm"], mb["lid_mm"]
    cx, comp, st, pitch = lay["cell_x"], lay["comp"], lay["stack_t"], lay["pitch"]
    z0, z1, zl0, zf = lay["z_plate0"], lay["z_plate1"], lay["z_lid0"], lay["z_fill"]
    xg0, xg1 = cx[0] - mm["valve_well_od_mm"] / 2, L / 2 - wall
    xo = xg1 - mm["frit_len_mm"] / 2
    tx, ty = lay["term_x"], lay["term_y"]
    sh = Sheet("SB-GA-001", "R1 12 V MONOBLOC - GENERAL ARRANGEMENT", 2.0, "1:2")
    S = sh.S
    FX, FZ, SX, TY, AX = 90.0, 520.0, 520.0, 250.0, 760.0

    def F(x, z):
        return [FX + x + L / 2, FZ + z]

    def T(x, y):
        return [FX + x + L / 2, TY + y + W / 2]

    def Sd(y, z):
        return [SX + (W / 2 - y), FZ + z]

    def A(x, z):
        return [AX + x + L / 2, FZ + z]

    xp = [cx[i] + comp / 2 for i in range(len(cx) - 1)]     # partition left faces
    # ---------------------------------------------------------------- FRONT VIEW
    sh.rect(F(-L / 2, 0), F(L / 2, zl0))
    sh.rect(F(-L / 2, zl0), F(L / 2, H))
    for x in xp:
        sh.line([F(x, base), F(x, zl0)], "HIDDEN")
        sh.line([F(x + pt, base), F(x + pt, zl0)], "HIDDEN")
    sh.line([F(-L / 2 + wall, base), F(L / 2 - wall, base)], "HIDDEN")
    for x in tx:
        sh.rect(F(x - mm["term_post_d_mm"] / 2, lay["z_bus1"]), F(x + mm["term_post_d_mm"] / 2, H - mm["term_top_below_lid_mm"]), "HIDDEN")
        sh.line([F(x, H + 6), F(x, lay["z_bus1"] - 6)], "CENTER")
    sh.text(F(-L / 2, H + 26), "FRONT VIEW", 3.5)
    sh.dim(F(-L / 2, 0), F(L / 2, 0), F(0, -24))
    sh.dim(F(-L / 2, 0), F(-L / 2, H), F(-L / 2 - 20, H / 2))
    sh.dim(F(L / 2, zl0), F(L / 2, H), F(L / 2 + 14, zl0 + 3), text=f"{f1(lid)} LID")
    sh.dim(F(tx[0], H), F(tx[1], H), F(0, H + 12), text=f"{f1(mb['terminal_spacing_mm'])} TERMINAL PITCH")
    # ---------------------------------------------------------------- SIDE VIEW (from left, placed right - first angle)
    sh.rect(Sd(W / 2, 0), Sd(-W / 2, zl0))
    sh.rect(Sd(W / 2, zl0), Sd(-W / 2, H))
    sh.rect(Sd(ty + mm["term_post_d_mm"] / 2, lay["z_bus1"]), Sd(ty - mm["term_post_d_mm"] / 2, H - 1), "HIDDEN")
    sh.rect(Sd(mm["valve_well_od_mm"] / 2, zl0 - mm["valve_well_depth_mm"]), Sd(-mm["valve_well_od_mm"] / 2, zl0), "HIDDEN")
    sh.rect(Sd(mm["manifold_w_mm"] / 2, H - mm["manifold_depth_mm"]), Sd(-mm["manifold_w_mm"] / 2, H), "HIDDEN")
    sh.line([Sd(W / 2 - wall, base), Sd(-W / 2 + wall, base)], "HIDDEN")
    sh.text(Sd(W / 2, H + 26), "SIDE VIEW (FROM LEFT)", 3.5)
    sh.dim(Sd(W / 2, 0), Sd(-W / 2, 0), Sd(0, -24))
    sh.dim(Sd(-W / 2, 0), Sd(-W / 2, H), Sd(-W / 2 - 18, H / 2))
    sh.dim(Sd(-W / 2, H), Sd(ty, H), Sd((ty - W / 2) / 2, H + 12))
    # ---------------------------------------------------------------- TOP VIEW
    sh.rect(T(-L / 2, -W / 2), T(L / 2, W / 2), fillet=mm["case_fillet_mm"])
    for x, pol in zip(tx, ("+", "–")):
        sh.circle(T(x, ty), mm["term_well_d_mm"] / 2)
        sh.circle(T(x, ty), mm["collar_od_mm"] / 2, "THIN")
        sh.circle(T(x, ty), mm["term_post_d_mm"] / 2)
        sh.circle(T(x, ty), mm["term_bore_d_mm"] / 2)
        sh.line([T(x - 18, ty), T(x + 18, ty)], "CENTER")
        sh.line([T(x, ty - 18), T(x, ty + 18)], "CENTER")
        sh.text(T(x + (22 if pol == "+" else -22), ty + 8), pol, 5.0, "MC")
    sh.rect(T(xg0, -mm["manifold_w_mm"] / 2), T(xg1, mm["manifold_w_mm"] / 2))
    sh.circle(T(xo, 0), mm["outlet_d_mm"] / 2)
    for x in cx:
        sh.circle(T(x, 0), mm["valve_well_id_mm"] / 2, "HIDDEN")
    sh.rect(T(xg1 - mm["frit_len_mm"], -mm["manifold_w_mm"] / 2 + 1), T(xg1, mm["manifold_w_mm"] / 2 - 1), "HIDDEN")
    ll, lw_, ly = mm["label_l_mm"], mm["label_w_mm"], mm["label_y_mm"]
    sh.rect(T(-ll / 2, ly - lw_ / 2), T(ll / 2, ly + lw_ / 2), "THIN")
    sh.text(T(0, ly), "LABEL RECESS 0.6 DEEP", 2.6, "MC")
    # section plane A-A
    sh.line([T(-L / 2 - 14, 0), T(-L / 2 - 3, 0)], "CENTER")
    sh.line([T(L / 2 + 3, 0), T(L / 2 + 14, 0)], "CENTER")
    for sx in (-1, 1):
        xx = sx * (L / 2 + 10)
        sh.layer("OUTLINE")
        sh.cmd("line", points=[T(xx, 0), T(xx, 9)])
        sh.arrow(T(xx, 11), T(xx, 0), 2.5)
        sh.text(T(xx, 17), "A", 4.0, "MC")
    sh.text(T(-L / 2, W / 2 + 32), "TOP VIEW", 3.5)
    sh.dim(T(-L / 2, -W / 2), T(-L / 2, W / 2), T(-L / 2 - 20, 0))
    sh.dim(T(L / 2, -W / 2), T(tx[1], ty), T(L / 2 + 14, -W / 2 + 5))
    sh.dim(T(cx[3], 0), T(cx[4], 0), T((cx[3] + cx[4]) / 2, -18), text=f"{f1(pitch, 2)} CELL PITCH")
    sh.dim(T(xg1 - 30, -mm["manifold_w_mm"] / 2), T(xg1 - 30, mm["manifold_w_mm"] / 2), T(xg1 - 12, 22))
    sh.dim(T(-ll / 2, ly + lw_ / 2), T(ll / 2, ly + lw_ / 2), T(0, W / 2 + 10))
    sh.leader(T(tx[0], ty - 14), T(tx[0] + 40, -W / 2 - 16), f"M8 FEMALE INSERT IN Ø{f1(mm['term_well_d_mm'])} WELL", 2.4)
    sh.leader(T(xo, 0), T(L / 2 + 8, W / 2 + 14), f"VENT OUTLET Ø{f1(mm['outlet_d_mm'])}", 2.4)
    # ---------------------------------------------------------------- SECTION A-A (Y = 0)
    hs = 0.35

    def ahatch(x0, x1, za, zb, pat="ANSI31", sc=hs, ang=0.0, lay="OUTLINE"):
        sh.rect(A(x0, za), A(x1, zb), lay, hatch=pat, hs=sc, ang=ang)

    ahatch(-L / 2, L / 2, 0, base)
    ahatch(-L / 2, -L / 2 + wall, base, zl0)
    ahatch(L / 2 - wall, L / 2, base, zl0)
    for x in xp:
        ahatch(x, x + pt, base, zl0)
    for x in cx:
        sh.rect(A(x - st / 2, z0), A(x + st / 2, z1), hatch="ANSI37", hs=0.25)
    # lid in section: full outside the groove, 2 mm floor under the channel with valve holes
    rid = mm["valve_well_id_mm"] / 2
    ahatch(-L / 2, xg0, zl0, H)
    ahatch(xg1, L / 2, zl0, H)
    edges = [xg0] + [v for x in cx for v in (x - rid, x + rid)] + [xg1]
    for a_, b_ in zip(edges[0::2], edges[1::2]):
        ahatch(a_, b_, zl0, H - mm["manifold_depth_mm"])
    ro = mm["outlet_d_mm"] / 2
    ahatch(xg0, xo - ro, H - mm["cover_t_mm"], H, ang=90)
    ahatch(xo + ro, xg1, H - mm["cover_t_mm"], H, ang=90)
    sh.rect(A(xg1 - mm["frit_len_mm"], H - mm["manifold_depth_mm"]), A(xg1, H - mm["cover_t_mm"]), hatch="ANSI37", hs=0.08)
    zw0 = zl0 - mm["valve_well_depth_mm"]
    for x in cx:
        wo, wi, no, ni, co = (mm["valve_well_od_mm"] / 2, rid, mm["valve_nipple_od_mm"] / 2, mm["valve_nipple_id_mm"] / 2,
                              mm["valve_cap_od_mm"] / 2)
        for sgn in (-1, 1):
            ahatch(x + sgn * wi, x + sgn * wo, zw0 + 1.5, zl0)
            ahatch(x + sgn * ni, x + sgn * wo, zw0, zw0 + 1.5)
            ahatch(x + sgn * ni, x + sgn * no, zw0 + 1.5, zl0 - 4)
            sh.rect(A(min(x + sgn * no, x + sgn * co), zl0 - 4 - mm["valve_cap_h_mm"] + 1.5),
                    A(max(x + sgn * no, x + sgn * co), zl0 - 4), hatch="SOLID")
        sh.rect(A(x - co, zl0 - 4), A(x + co, zl0 - 2.5), hatch="SOLID")
    sh.line([A(-L / 2 + wall, zf), A(L / 2 - wall, zf)], "PHANTOM")
    sh.line([A(-L / 2 - 8, z1), A(-L / 2, z1)], "THIN")
    sh.text(A(-L / 2, H + 26), "SECTION A-A (THROUGH CELL CENTRES, Y = 0)", 3.5)
    sh.dim(A(-L / 2, 0), A(-L / 2, H), A(-L / 2 - 24, H / 2))
    sh.dim(A(L / 2, z0), A(L / 2, z1), A(L / 2 + 16, (z0 + z1) / 2), text=f"{f1(d['plate_h_mm'])} PLATE")
    sh.dim(A(-L / 2, z1), A(-L / 2, zl0), A(-L / 2 - 10, (z1 + zl0) / 2), text=f"{f1(mb['headspace_mm'])}")
    sh.text(A(-L / 2 - 4, zl0 + 14), "HEADSPACE", 2.2, "MR")
    sh.dim(A(L / 2, base), A(L / 2, z0), A(L / 2 + 30, (base + z0) / 2))
    sh.dim(A(cx[0] - comp / 2, -2), A(cx[0] + comp / 2, -2), A(cx[0], -16), text=f"{f1(comp, 2)}")
    sh.dim(A(cx[2] - st / 2, -2), A(cx[2] + st / 2, -2), A(cx[2], -16), text=f"{f1(st, 2)} STACK")
    sh.dim(A(cx[5], z1 - 30), A(cx[6], z1 - 30), A((cx[5] + cx[6]) / 2, -30), text=f"{f1(pitch, 2)} PITCH")
    sh.dim(A(xp[7], 120), A(xp[7] + pt, 120), A(xp[7] + 30, -16))
    sh.dim(A(-L / 2, zf), A(-L / 2, base), A(-L / 2 - 10, (zf + base) / 2), text=f"{f1(zf - base)}")
    sh.text(A(-L / 2 - 4, zf + 8), "FREE ELECTROLYTE LEVEL", 2.0, "MR")
    # balloons + parts list
    items = [
        (1, "CASE CONTAINER, PP-GF20, 10 COMPARTMENTS + 9 PARTITIONS", "PP-GF20", "1", A(-L / 2 + 2, 90), A(-L / 2 + 22, 175)),
        (2, "LID WITH 10 VALVE WELLS, MANIFOLD GROOVE, TERMINAL WELLS", "PP-GF20", "1", A(-150, H - 1), A(-110, H + 12)),
        (3, "VENT MANIFOLD COVER STRIP (WELDED)", "PP", "1", A(60, H - 1), A(30, H + 12)),
        (4, "FLAME ARRESTOR, POROUS PP FRIT", "PP FRIT", "1", A(xg1 - 3, H - 3), A(145, H + 12)),
        (5, f"ONE-WAY VALVE CAP, EPDM BUNSEN, OPENS {f1(mb['vent_valve_open_kPa'].value)} kPa [TARGET]", "EPDM", "10",
         A(cx[4], zl0 - 3), A(cx[4] + 6, H + 12)),
        (6, "VALVE NIPPLE", "PP", "10", A(cx[3] - 2, zl0 - 9), A(cx[3] - 10, H + 12)),
        (7, f"ELECTRODE STACK, {d['repeats_per_cell']} REPEAT UNITS (SEE SB-GA-002)", "-", "10", A(cx[6], 120), A(cx[6] + 10, 150)),
        (8, f"FREE ELECTROLYTE {MAT['electrolyte_molarity'].value} M Na2SO4 (WATER-BASED)", "-", "10", A(cx[8] + 14.2, 30), A(cx[8] - 6, 80)),
        (9, "TERMINAL POST, M8 FEMALE INSERT, Sn-PLATED BRASS", "BRASS", "2", F(tx[1], 210), F(tx[1] - 30, 245)),
        (10, "PLATE-GROUP STRAPS + INTERCELL CONNECTORS", "316L", "20 + 9", F(cx[5], 197), F(cx[5] - 20, 245)),
        (11, "POLARITY COLLAR (RED +, BLACK -)", "PP", "2", T(tx[0] + 11, ty), T(tx[0] + 46, ty + 38)),
        (12, "LABEL (IN 0.6 RECESS)", "FILM", "1", T(-60, ly), T(-120, ly + 50)),
    ]
    for n, _, _, _, tgt, at in items:
        sh.balloon(n, tgt, at)
    sh.table(800, 480, [9, 112, 22, 15], [("NO", "DESCRIPTION", "MATERIAL", "QTY")] + [(str(i[0]), i[1], i[2], i[3]) for i in items],
             h=2.1, row_h=5.0, title="PARTS LIST")
    # ---------------------------------------------------------------- DETAIL B (2:1 = 4x the sheet scale): vent valve + manifold + arrestor
    k = 4.0
    xd0, zd0 = cx[8] - 14.0, zl0 - mm["valve_well_depth_mm"] - 3.0
    BX, BZ = 470.0, 252.0

    def B(x, z):
        return [BX + (x - xd0) * k, BZ + (z - zd0) * k]

    def bh(x0, x1, za, zb, pat="ANSI31", sc=1.0, ang=0.0):
        sh.rect(B(x0, za), B(x1, zb), hatch=pat, hs=sc, ang=ang)

    bh(L / 2 - wall, L / 2, zd0, zl0)
    bh(xp[8], xp[8] + pt, zd0, zl0)
    edges_b = [xd0, cx[8] - rid, cx[8] + rid, cx[9] - rid, cx[9] + rid, xg1]
    for a_, b_ in zip(edges_b[0::2], edges_b[1::2]):
        bh(a_, b_, zl0, H - mm["manifold_depth_mm"])
    bh(xg1, L / 2, zl0, H)
    bh(xd0, xo - ro, H - mm["cover_t_mm"], H, ang=90)
    bh(xo + ro, xg1, H - mm["cover_t_mm"], H, ang=90)
    sh.rect(B(xg1 - mm["frit_len_mm"], H - mm["manifold_depth_mm"]), B(xg1, H - mm["cover_t_mm"]), hatch="ANSI37", hs=0.3)
    for x in (cx[8], cx[9]):
        for sgn in (-1, 1):
            bh(x + sgn * wi, x + sgn * wo, zw0 + 1.5, zl0)
            bh(x + sgn * ni, x + sgn * wo, zw0, zw0 + 1.5)
            bh(x + sgn * ni, x + sgn * no, zw0 + 1.5, zl0 - 4)
            sh.rect(B(min(x + sgn * no, x + sgn * co), zl0 - 4 - mm["valve_cap_h_mm"] + 1.5),
                    B(max(x + sgn * no, x + sgn * co), zl0 - 4), hatch="SOLID")
        sh.rect(B(x - co, zl0 - 4), B(x + co, zl0 - 2.5), hatch="SOLID")
        sh.line([B(x, zd0), B(x, H + 2)], "CENTER")
    zc = H - (mm["manifold_depth_mm"] + mm["cover_t_mm"]) / 2
    sh.flow([B(cx[9] + 0.6, zd0 + 0.5), B(cx[9] + 0.6, zl0 - 2.0), B(cx[9] + 2.5, zc), B(xg1 - mm["frit_len_mm"] - 0.5, zc)])
    sh.flow([B(xo, H - mm["cover_t_mm"]), B(xo, H + 6)])
    sh.text(B(xd0, H + 12), "DETAIL B - VENT VALVE, MANIFOLD, FLAME ARRESTOR (SCALE 2:1)", 3.2)
    sh.dimstyle("SBx4", k, dec=1)
    sh.dim(B(cx[8] - wo, zw0), B(cx[8] + wo, zw0), B(cx[8], zw0 - 2.5), style="SBx4", text="Ø<>")
    sh.dim(B(cx[8] - co, zl0 - 4 - mm["valve_cap_h_mm"] + 1.5), B(cx[8] + co, zl0 - 4 - mm["valve_cap_h_mm"] + 1.5),
           B(cx[8], zw0 - 6.0), style="SBx4", text="Ø<> CAP")
    sh.dim(B(xp[8] + pt, zw0), B(xp[8] + pt, zl0), B(xp[8] + pt + 2.5, (zw0 + zl0) / 2), style="SBx4")
    sh.dim(B(L / 2, zl0), B(L / 2, H), B(L / 2 + 3, zl0 + 3), style="SBx4")
    sh.dim(B(xg1 - mm["frit_len_mm"], H), B(xg1, H), B(xg1 - 3.5, H + 4.5), style="SBx4")
    sh.dim(B(xd0 + 1, H - mm["manifold_depth_mm"]), B(xd0 + 1, H - mm["cover_t_mm"]), B(xd0 - 2.5, zc), style="SBx4")
    sh.leader(B(cx[9] - co, zl0 - 5), B(cx[9] - 7.5, zd0 - 4.5), f"EPDM BUNSEN CAP: ONE-WAY, OPENS {f1(mb['vent_valve_open_kPa'].value)} kPa [TARGET]", 2.2)
    sh.leader(B(cx[8] + no - 0.5, zw0 + 3), B(cx[8] + 8, zd0 - 9.5), "PP NIPPLE ON MOULDED VALVE WELL (1 PER CELL)", 2.2)
    sh.leader(B(xg1 - 3, H - 3), B(xg1 + 7, H - 9), "POROUS PP FRIT = FLAME ARRESTOR", 2.2)
    sh.leader(B(cx[9] - 10, zc), B(cx[9] - 14, H + 6), "COMMON MANIFOLD CHANNEL UNDER WELDED COVER", 2.2)
    sh.text(B(xg1 + 2, H + 8), "VENT OUT", 2.2, "ML", "FLOW")
    # ---------------------------------------------------------------- notes
    e = d["electrode"]
    sh.notes(30, 205, [
        "NOTES",
        "1. CONCEPT — NOT FOR FABRICATION. ALL DIMENSIONS IN mm. TOLERANCES: CONCEPT (NONE SPECIFIED). FIRST-ANGLE PROJECTION.",
        f"2. ENVELOPE {f1(L)} x {f1(W)} x {f1(H)} = COMMON 12 V / 100 Ah VRLA BLOCK (params MONOBLOC). TERMINAL FACES 1 mm BELOW LID.",
        f"3. {d['n_cells']} CELLS IN SERIES; COMPARTMENT {f1(comp, 2)}, PITCH {f1(pitch, 2)}; PARTITIONS {f1(pt)} MOULDED WITH CASE, SEALED TO LID.",
        f"4. EACH CELL: {d['repeats_per_cell']} REPEAT UNITS x {f1(e['repeat_thick_um'] / 1000, 3)} = {f1(st, 2)} STACK; PLATES {f1(d['plate_w_mm'])} x {f1(d['plate_h_mm'])} (SB-GA-002).",
        f"5. VENT: ONE-WAY EPDM VALVE PER CELL (OPENS {f1(mb['vent_valve_open_kPa'].value)} kPa [TARGET]) -> COMMON LID MANIFOLD -> ONE POROUS-PP",
        f"    FLAME ARRESTOR + Ø{f1(mm['outlet_d_mm'])} OUTLET. CHOICE DOCUMENTED IN params/mech_params.py (VENT_ARRANGEMENT).",
        f"6. ELECTROLYTE {MAT['electrolyte_molarity'].value} M Na2SO4 (WATER-BASED); PORES SATURATED; FREE LEVEL {f1(zf - base)} ABOVE FLOOR [CALC, design.monobloc].",
        f"7. 12 V BLOCK {d['energy_Wh'] / 1000:.2f} kWh [TARGET], {d['v_nom']:.1f} V NOM, MASS {d['mass_kg']:.1f} kg [CALC]. PERFORMANCE NOT DEMONSTRATED.",
        "8. GENERATED BY drawings/make_drawings.py FROM params/product_params.py, params/design.py, params/mech_params.py.",
    ], h=2.3, step=4.2)
    sh.frame("SOURCE: params/*.py")
    return sh


# ===================================================================================================== SB-GA-002
def ga002() -> Sheet:
    d, lay, mm = monobloc(), monobloc_layout(), MB_MECH
    es = electrode_stack()
    mb = MONOBLOC
    sh = Sheet("SB-GA-002", "R1 CELL / ELECTRODE STACK DETAIL", 1.0, "1:1 + 50:1")
    pw, ph = d["plate_w_mm"], d["plate_h_mm"]
    tw, th, tyo, ov = mm["tab_w_mm"], mm["tab_h_mm"], mm["tab_y_mm"], mm["sep_overhang_mm"]
    # ---------------------------------------------------------------- (a) electrode plate elevation, 1:1
    PX, PZ = 45.0 + pw / 2, 172.0

    def P(y, z):
        return [PX + y, PZ + z]
    sh.rect(P(-pw / 2, 0), P(pw / 2, ph))
    sh.rect(P(-tyo - tw / 2, ph), P(-tyo + tw / 2, ph + th))
    sh.rect(P(tyo - tw / 2, ph), P(tyo + tw / 2, ph + th), "PHANTOM")
    sh.rect(P(-pw / 2 - ov, -ov), P(pw / 2 + ov, ph + ov), "PHANTOM")
    sh.line([P(0, -8), P(0, ph + th + 8)], "CENTER")
    sh.text(P(-pw / 2, ph + th + 18), "VIEW 1 - ELECTRODE PLATE (CATHODE SHOWN), 1:1", 3.2)
    sh.text(P(0, ph / 2 + 10), "COATED BOTH SIDES", 3.0, "MC")
    sh.text(P(0, ph / 2 - 2), f"{d['plate_area_cm2']:.2f} cm² PER FACE [CALC]", 2.6, "MC")
    sh.text(P(0, ph / 2 - 12), f"CATHODE {es['cathode_loading']:.0f} mg/cm² PER SIDE [TARGET]", 2.4, "MC")
    sh.dim(P(-pw / 2, 0), P(pw / 2, 0), P(0, -14))
    sh.dim(P(pw / 2, 0), P(pw / 2, ph), P(pw / 2 + 14, ph / 2))
    sh.dim(P(-tyo - tw / 2, ph + th), P(-tyo + tw / 2, ph + th), P(-tyo, ph + th + 7))
    sh.dim(P(-tyo + tw / 2, ph), P(-tyo + tw / 2, ph + th), P(-tyo + tw / 2 + 8, ph + th / 2))
    sh.dim(P(-tyo, ph + th), P(0, ph + th), P(-tyo / 2, ph + th + 12))
    sh.dim(P(-pw / 2 - ov, -ov), P(-pw / 2, -ov), P(-pw / 2 - 6, -22))
    sh.text(P(-tyo - tw / 2 - 2, ph + th / 2), "CATHODE TAB (BARE 316L)", 2.0, "MR")
    sh.text(P(tyo, ph + th + 4), "ANODE TAB (NEXT PLATE)", 2.0, "BC")
    sh.text(P(0, 14), f"PHANTOM: SEPARATOR OUTLINE, +{f1(ov)} ALL ROUND", 2.2, "MC")
    # ---------------------------------------------------------------- (b) cell section through tabs (Y = +tab_y), 1:1
    comp, st, pt = lay["comp"], lay["stack_t"], mb["partition_mm"]
    CX, CZ = 262.0, 165.0
    base, z0, z1, zl0, zt1, zb1, zf = mb["base_mm"], lay["z_plate0"], lay["z_plate1"], lay["z_lid0"], lay["z_tab1"], lay["z_bus1"], lay["z_fill"]

    def C(x, z):
        return [CX + x, CZ + z]
    for sgn in (-1, 1):
        x0_ = sgn * comp / 2
        sh.rect(C(x0_, base), C(x0_ + sgn * pt, zl0), hatch="ANSI31", hs=0.3)
    sh.rect(C(-comp / 2 - pt, 0), C(comp / 2 + pt, base), hatch="ANSI31", hs=0.3)
    sh.rect(C(-comp / 2 - pt, zl0), C(comp / 2 + pt, mb["height_mm"]), hatch="ANSI31", hs=0.3)
    sh.rect(C(-st / 2, z0), C(st / 2, z1), hatch="ANSI37", hs=0.2)
    sh.rect(C(-st / 2, z1), C(st / 2, zt1), "THIN")
    for k_ in range(0, d["repeats_per_cell"], 2):
        xx = -st / 2 + (k_ + 0.5) * st / d["repeats_per_cell"]
        sh.line([C(xx, z1), C(xx, zt1)], "THIN")
    sh.rect(C(-st / 2, zt1), C(st / 2, zb1), hatch="ANSI31", hs=0.15, ang=90)
    sh.line([C(-comp / 2, zf), C(comp / 2, zf)], "PHANTOM")
    sh.text(C(-comp / 2 - 30, mb["height_mm"] + 18), "VIEW 2 - CELL SECTION AT TABS, 1:1", 3.2)
    sh.dim(C(-comp / 2, base + 1), C(comp / 2, base + 1), C(0, -14))
    sh.dim(C(-st / 2, z1), C(st / 2, z1), C(0, mb["height_mm"] + 8))
    sh.dim(C(comp / 2 + pt, z0), C(comp / 2 + pt, z1), C(comp / 2 + 16, (z0 + z1) / 2))
    sh.dim(C(comp / 2 + pt, z1), C(comp / 2 + pt, zl0), C(comp / 2 + 16, (z1 + zl0) / 2))
    sh.dim(C(comp / 2 + pt, base), C(comp / 2 + pt, z0), C(comp / 2 + 28, base - 4))
    sh.dim(C(-st / 2, z1), C(-st / 2, zt1), C(-comp / 2 - 12, (z1 + zt1) / 2))
    sh.dim(C(-st / 2, zt1), C(-st / 2, zb1), C(-comp / 2 - 24, (zt1 + zb1) / 2 + 4))
    sh.dim(C(-comp / 2, zf), C(-comp / 2, base), C(-comp / 2 - 12, (zf + base) / 2))
    sh.leader(C(st / 2 - 2, (zt1 + zb1) / 2), C(comp / 2 + 30, zb1 + 14), "PLATE-GROUP STRAP (316L)", 2.2)
    sh.leader(C(0, 100), C(comp / 2 + 30, 128), f"STACK: {d['repeats_per_cell']} REPEAT UNITS", 2.2)
    sh.leader(C(comp / 2 - 0.6, zf - 4), C(comp / 2 + 30, zf + 22), "FREE ELECTROLYTE LEVEL [CALC]", 2.2)
    # ---------------------------------------------------------------- (c) repeat-unit layers, 50:1
    k = 50.0
    tc, ta, cc, sep = es["cathode_thick_um"], es["anode_thick_um"], MAT["cc_thickness_um"].value, MAT["separator_thickness_um"].value
    layers = [("CATHODE COATING", tc, "ANSI37", 0.4), ("316L FOIL", cc, "SOLID", 1), ("CATHODE COATING", tc, "ANSI37", 0.4),
              ("SEPARATOR", sep, "ANSI33", 0.5), ("ANODE COATING", ta, "ANSI31", 0.5), ("316L FOIL", cc, "SOLID", 1),
              ("ANODE COATING", ta, "ANSI31", 0.5), ("SEPARATOR", sep, "ANSI33", 0.5)]
    RX, RZ, RH = 382.0, 262.0, 62.0
    sh.dimstyle("SBum", k / 1000.0, dec=0)      # dimension text in um
    x = RX
    for name, t_um, pat, sc in layers:
        w = t_um / 1000.0 * k
        sh.rect([x, RZ], [x + w, RZ + RH], hatch=pat, hs=sc)
        x += w
    sh.line([[RX - 3, RZ + RH], [x + 3, RZ + RH]], "THIN")
    sh.line([[RX - 3, RZ], [x + 3, RZ]], "THIN")
    sh.text([RX, RZ + RH + 46], "DETAIL C - REPEAT UNIT, 50:1 (DIMENSIONS IN µm)", 3.2)
    x = RX
    for i, (name, t_um, _, _) in enumerate(layers):
        w = t_um / 1000.0 * k
        if w > 3:
            sh.dim([x, RZ + RH], [x + w, RZ + RH], [x + w / 2, RZ + RH + 8 + (i % 2) * 7], style="SBum")
        else:
            sh.dim([x, RZ + RH], [x + w, RZ + RH], [x + w / 2, RZ + RH + 22], style="SBum")
        x += w
    sh.dim([RX, RZ + RH], [x, RZ + RH], [(RX + x) / 2, RZ + RH + 32], style="SBum", text="<> REPEAT UNIT")
    xr = x + 8
    x = RX
    elbow_y = {0: RZ - 34, 1: RZ - 26, 3: RZ - 18, 4: RZ - 10}
    for i, (name, t_um, _, _) in enumerate(layers):
        w = t_um / 1000.0 * k
        if i in elbow_y:
            ye = elbow_y[i]
            sh.line([[x + w / 2, RZ + 3], [x + w / 2, ye], [xr, ye]], "TEXT")
            sh.layer("TEXT")
            sh.arrow([x + w / 2, RZ + 3], [x + w / 2, ye], 1.6)
            sh.text([xr + 1.5, ye], name + (" (x2 PER UNIT)" if i != 1 else " CURRENT COLLECTOR (x2)"), 2.2, "ML")
        x += w
    # ---------------------------------------------------------------- (d) layer table from design.electrode_stack()
    rows = [("LAYER (PER REPEAT UNIT)", "µm", "BASIS / TAG"),
            ("cathode coating x2 (Na-birnessite 80:10:10)", f1(tc), f"{es['cathode_loading']:.0f} mg/cm2/side [TARGET]"),
            ("anode coating x2 (NaTi2(PO4)3/C)", f1(ta), f"{es['anode_loading']:.1f} mg/cm2/side, N/P {MAT['np_ratio'].value} [CALC]"),
            ("current collector x2 (C-coated 316L)", f1(cc), "[ASSUMPTION]"),
            ("separator x2 (nonwoven PP / AGM)", f1(sep), "[ASSUMPTION]"),
            ("REPEAT UNIT", f1(es["repeat_thick_um"]), "[CALC]"),
            (f"repeats per cell / stack", f"{d['repeats_per_cell']} / {f1(lay['stack_t'], 2)} mm", f"in {f1(comp, 2)} mm compartment [CALC]"),
            ("porosity / electrolyte in pores", f"{MAT['electrode_porosity'].value}", f"{es['electrolyte_mg_cm2']:.1f} mg/cm2 [CALC]"),
            ("areal capacity / cell capacity", f"{es['cap_mAh_cm2']:.1f} mAh/cm2", f"{d['cap_Ah']:.1f} Ah [CALC]")]
    sh.table(322, 182, [86, 30, 70], rows, h=2.2, row_h=5.6, title="REPEAT UNIT - FROM params/design.py electrode_stack()")
    sh.notes(20, 120, [
        "NOTES",
        "1. CONCEPT — NOT FOR FABRICATION. DIMENSIONS mm (DETAIL C IN µm). TOLERANCES: CONCEPT (NONE SPECIFIED).",
        "2. LAYER THICKNESSES ARE CALCULATED FROM LOADING, DENSITY AND POROSITY",
        "    ASSUMPTIONS IN params/product_params.py (MAT); NOT MEASURED.",
        "3. STACK ORDER: CATHODE | SEPARATOR | ANODE | SEPARATOR, REPEATED;",
        "    CATHODE TABS ONE SIDE, ANODE TABS OTHER SIDE, ALTERNATING CELL TO CELL",
        "    SO INTERCELL CONNECTORS RUN STRAIGHT THROUGH THE PARTITIONS.",
        f"4. ELECTROLYTE {MAT['electrolyte_molarity'].value} M Na2SO4, WATER-BASED; NO DRY ROOM, NO NMP (AQUEOUS BINDER).",
        "5. TABS DRAWN AT PLATE THICKNESS FOR CLARITY; REAL TABS ARE THE BARE 25 µm FOIL, WELDED IN A BUNDLE.",
    ], h=2.2, step=4.0)
    sh.frame("SOURCE: params/design.py")
    return sh


# ===================================================================================================== SB-GA-003
def ga003() -> Sheet:
    c, cm, mb = CABINET, CAB_MECH, MONOBLOC
    Wc, Dc, Hc = c["width_mm"], c["depth_mm"], c["height_mm"]
    pm, ptk, dt, ph, rh = cm["post_mm"], cm["panel_t_mm"], cm["door_t_mm"], cm["plinth_h_mm"], cm["roof_h_mm"]
    lb, wb, hb, gap = mb["length_mm"], mb["width_mm"], mb["height_mm"], cm["block_gap_mm"]
    pitch = CAB_SHELF_PITCH_MM
    sh = Sheet("SB-GA-003", "R1 UPS BATTERY CABINET - ARRANGEMENT", 10.0, "1:10")
    S = sh.S
    xcols = [-(wb + gap), 0.0, wb + gap]
    yf = -Dc / 2 + dt
    yfr = yf + cm["front_clear_mm"]
    yrows = [yfr + lb / 2, yfr + lb * 1.5 + gap]
    zs = [ph + s * pitch for s in range(c["shelves"])]
    zb = [z + cm["shelf_t_mm"] for z in zs]
    BASE = 1250.0
    # ---------------------------------------------------------------- (a) front, door closed
    FX = 1050.0

    def F(x, z):
        return [FX + x, BASE + z]
    sh.rect(F(-Wc / 2, 0), F(Wc / 2, Hc))
    sh.rect(F(-Wc / 2 + 25, 25), F(Wc / 2 - 25, Hc - 25), "THIN")
    swl, shl = cm["louvre_slot_mm"]
    for z0 in (110.0, Hc - 110.0 - (cm["louvre_rows"] - 1) * 24):
        for r in range(cm["louvre_rows"]):
            for col in (-1, 0, 1):
                sh.rect(F(col * (swl + 30) - swl / 2, z0 + r * 24), F(col * (swl + 30) + swl / 2, z0 + r * 24 + shl))
    hx, hz = Wc / 2 - 60, Hc * 0.52
    sh.rect(F(hx - 18, hz - 80), F(hx + 18, hz + 80))
    sh.rect(F(hx - 10, hz - 70), F(hx + 10, hz + 70), "THIN")
    for zh in (250.0, Hc / 2, Hc - 250.0):
        sh.rect(F(-Wc / 2 - 6, zh - 40), F(-Wc / 2, zh + 40))
    sh.rect(F(-80, Hc - 380), F(80, Hc - 320), "THIN")
    sh.text(F(0, Hc - 350), "RATING PLATE (TBD)", 2.0, "MC")
    sh.text(F(-Wc / 2, Hc + 120), "VIEW 1 - FRONT, DOOR CLOSED", 3.5)
    sh.dim(F(-Wc / 2, 0), F(Wc / 2, 0), F(0, -120))
    sh.dim(F(-Wc / 2, 0), F(-Wc / 2, Hc), F(-Wc / 2 - 150, Hc / 2))
    sh.leader(F(-swl - 30, Hc - 160), F(-Wc / 2 - 60, Hc + 40), "H2 OUTLET LOUVRES (HIGH)", 2.4)
    sh.leader(F(-swl - 30, 160), F(-Wc / 2 - 60, -60), "AIR INLET LOUVRES (LOW)", 2.4)
    # ---------------------------------------------------------------- (b) front, door removed
    GX = 2100.0

    def G(x, z):
        return [GX + x, BASE + z]
    sh.rect(G(-Wc / 2, 0), G(Wc / 2, Hc))
    for sx in (-1, 1):
        sh.rect(G(sx * Wc / 2, 0), G(sx * (Wc / 2 - pm), Hc), "THIN")
    sh.rect(G(-Wc / 2 + pm, 0), G(Wc / 2 - pm, ph), hatch="ANSI31", hs=8)
    sh.rect(G(-Wc / 2 + pm, Hc - rh), G(Wc / 2 - pm, Hc), hatch="ANSI31", hs=8)
    for s in range(c["shelves"]):
        sh.rect(G(-Wc / 2 + pm, zs[s] - cm["shelf_lip_mm"]), G(Wc / 2 - pm, zb[s]), "OUTLINE")
        for x in xcols[:2]:
            sh.rect(G(x - wb / 2, zb[s]), G(x + wb / 2, zb[s] + hb))
            sh.line([G(x - wb / 2, zb[s] + hb - mb["lid_mm"]), G(x + wb / 2, zb[s] + hb - mb["lid_mm"])], "THIN")
        if s < c["shelves"] - 1:
            sh.rect(G(xcols[2] - cm["duct_mm"] / 2, zb[s]), G(xcols[2] + cm["duct_mm"] / 2, zs[s] + pitch - cm["shelf_lip_mm"]), "THIN")
            sh.rect(G(xcols[2] - wb / 2, zb[s]), G(xcols[2] + wb / 2, zb[s] + hb), "HIDDEN")
        else:
            kw, kd, kh = cm["breaker_mm"]
            sh.rect(G(xcols[2] - kw / 2, zb[s]), G(xcols[2] + kw / 2, zb[s] + kh))
            sh.rect(G(xcols[2] - 8, zb[s] + kh * 0.45), G(xcols[2] + 8, zb[s] + kh * 0.62), hatch="SOLID")
    sh.text(G(-Wc / 2, Hc + 120), "VIEW 2 - FRONT, DOOR REMOVED", 3.5)
    sh.dim(G(Wc / 2, zs[2]), G(Wc / 2, zs[3]), G(Wc / 2 + 140, (zs[2] + zs[3]) / 2), text=f"{f1(pitch, 1)} SHELF PITCH")
    s7 = c["shelves"] - 2
    sh.dim(G(xcols[0] - 40, zb[s7] + hb), G(xcols[0] - 40, zs[s7 + 1]), G(-Wc / 2 - 110, zb[s7] + hb + 40),
           text="<> CLEAR")
    sh.dim(G(Wc / 2, 0), G(Wc / 2, ph), G(Wc / 2 + 140, ph / 2 - 60))
    sh.dim(G(Wc / 2, Hc - rh), G(Wc / 2, Hc), G(Wc / 2 + 140, Hc + 40))
    sh.dim(G(xcols[0] - wb / 2, zb[0]), G(xcols[0] + wb / 2, zb[0]), G(xcols[0], zb[0] - 70))
    sh.dim(G(xcols[0] + wb / 2, zb[0] + 60), G(xcols[1] - wb / 2, zb[0] + 60), G(xcols[0] + wb / 2 + 3, zb[0] - 70))
    sh.leader(G(xcols[2] + 30, zb[7] + 100), G(Wc / 2 + 60, zb[7] - 40), "DC BREAKER + BMS", 2.2)
    sh.leader(G(xcols[2], zb[4] + 100), G(Wc / 2 + 60, zb[5] + 30), "VERTICAL CABLE DUCT", 2.2)
    sh.leader(G(xcols[1], zb[1] + 100), G(Wc / 2 + 60, zb[1] + 60), "12 V MONOBLOC", 2.2)
    # ---------------------------------------------------------------- (c) side section B-B at X = 0 with airflow
    SX = 3300.0

    def Sv(y, z):
        return [SX + y, BASE + z]
    sh.rect(Sv(-Dc / 2, 0), Sv(-Dc / 2 + dt, Hc), hatch="ANSI31", hs=8)
    sh.rect(Sv(Dc / 2 - ptk, ph), Sv(Dc / 2, Hc - rh), hatch="SOLID")
    sh.rect(Sv(yf, Hc - rh), Sv(Dc / 2, Hc))
    sh.rect(Sv(yf, 0), Sv(Dc / 2, ph))
    sh.rect(Sv(yf, 0), Sv(yf + pm, Hc), "THIN")
    sh.rect(Sv(Dc / 2 - pm, 0), Sv(Dc / 2, Hc), "THIN")
    sy0, sy1 = yf + pm - 10, yrows[1] + lb / 2 + 4
    for s in range(c["shelves"]):
        sh.rect(Sv(sy0, zs[s]), Sv(sy1, zb[s]), hatch="SOLID")
        sh.rect(Sv(sy0, zs[s] - cm["shelf_lip_mm"]), Sv(sy0 + cm["shelf_t_mm"], zs[s]), hatch="SOLID")
        for y in yrows:
            sh.rect(Sv(y - lb / 2, zb[s]), Sv(y + lb / 2, zb[s] + hb))
            sh.line([Sv(y - lb / 2, zb[s]), Sv(y + lb / 2, zb[s] + hb)], "THIN")
            sh.line([Sv(y - lb / 2, zb[s] + hb), Sv(y + lb / 2, zb[s])], "THIN")
    ygap = yf + 12                                    # front gap between door and blocks
    yplen = (yrows[1] + lb / 2 + Dc / 2 - ptk) / 2     # rear plenum centre line
    sh.flow([Sv(-Dc / 2 - 160, 170), Sv(ygap, 170), Sv(ygap, zb[0] + hb + 7)])
    for s in (0, 3, 6):                               # H2 + air over the block lids (clearance to shelf above) to the plenum
        zz = zb[s] + hb + 7
        sh.flow([Sv(ygap, zz), Sv(yplen - 15, zz)])
    sh.flow([Sv(yplen, zb[0] + hb), Sv(yplen, Hc - rh - 30), Sv(yplen, Hc + 150)])
    sh.flow([Sv(ygap, Hc - 300), Sv(ygap, Hc - 160), Sv(-Dc / 2 - 160, Hc - 160)])
    sh.text(Sv(-Dc / 2, Hc + 120), "SECTION B-B (X = 0) - VENTILATION PATH", 3.5)
    sh.dim(Sv(-Dc / 2, 0), Sv(Dc / 2, 0), Sv(0, -120))
    sh.dim(Sv(-Dc / 2, Hc), Sv(-Dc / 2 + dt, Hc), Sv(-Dc / 2 - 60, Hc + 40))
    sh.dim(Sv(yf, zb[0] + hb + 4), Sv(yfr, zb[0] + hb + 4), Sv(yf - 30, zb[0] + hb + 140))
    sh.dim(Sv(yrows[0] - lb / 2, zb[1]), Sv(yrows[0] + lb / 2, zb[1]), Sv(yrows[0], zb[1] - 60))
    sh.dim(Sv(yrows[0] + lb / 2, zb[2]), Sv(yrows[1] - lb / 2, zb[2]), Sv(yrows[0] + lb / 2 + 2, zb[2] - 60))
    sh.dim(Sv(yrows[1] + lb / 2, Hc - 200), Sv(Dc / 2 - ptk, Hc - 200), Sv(Dc / 2 + 40, Hc - 330), text="<> PLENUM")
    sh.leader(Sv(yplen, Hc * 0.72), Sv(Dc / 2 + 80, Hc * 0.75), "REAR PLENUM (AIR + H2 RISE)", 2.2)
    sh.leader(Sv(yplen + 10, Hc - 5), Sv(Dc / 2 + 80, Hc + 60), "ROOF SLOTS (OUT)", 2.2)
    sh.leader(Sv(ygap + 60, zb[3] + hb + 7), Sv(Dc / 2 + 80, Hc * 0.55), f"{f1(CAB_TERMINAL_CLEAR_MM)} mm OVER LIDS TO PLENUM", 2.2)
    # ---------------------------------------------------------------- (d) plan section C-C on shelf 1
    PX, PY = 4850.0, 2750.0

    def Pp(x, y):
        return [PX + x, PY + y]
    sh.rect(Pp(-Wc / 2, -Dc / 2), Pp(Wc / 2, Dc / 2))
    sh.rect(Pp(-Wc / 2, -Dc / 2), Pp(Wc / 2, yf), hatch="ANSI31", hs=8)
    for sx in (-1, 1):
        for y0 in (yf, Dc / 2 - pm):
            sh.rect(Pp(sx * Wc / 2, y0), Pp(sx * (Wc / 2 - pm), y0 + pm), hatch="SOLID")
    a = MB_MECH
    for i, y in enumerate(yrows):
        for j, x in enumerate(xcols):
            if i == 0 and j == 2:
                sh.rect(Pp(x - cm["duct_mm"] / 2, y - lb / 2 + 20), Pp(x + cm["duct_mm"] / 2, y - lb / 2 + 20 + cm["duct_mm"]), "THIN")
                sh.text(Pp(x, y), "DUCT /", 2.2, "MC")
                sh.text(Pp(x, y - 60), "BMS SLOT", 2.2, "MC")
                continue
            sh.rect(Pp(x - wb / 2, y - lb / 2), Pp(x + wb / 2, y + lb / 2))
            for txx in (-mb["terminal_spacing_mm"] / 2, mb["terminal_spacing_mm"] / 2):    # block rotated +90 deg
                lx, lyy = txx, -(mb["width_mm"] / 2 - a["term_y_inset_mm"])
                sh.circle(Pp(x - lyy, y + lx), a["term_post_d_mm"] / 2, "THIN")
    sh.text(Pp(-Wc / 2, Dc / 2 + 120), "SECTION C-C (PLAN ON SHELF 1)", 3.5)
    sh.dim(Pp(-Wc / 2, -Dc / 2), Pp(Wc / 2, -Dc / 2), Pp(0, -Dc / 2 - 110))
    sh.dim(Pp(Wc / 2, -Dc / 2), Pp(Wc / 2, Dc / 2), Pp(Wc / 2 + 110, 0))
    sh.dim(Pp(xcols[0] - wb / 2, yrows[1] + lb / 2), Pp(xcols[0] + wb / 2, yrows[1] + lb / 2), Pp(xcols[0], Dc / 2 + 50))
    sh.dim(Pp(Wc / 2, yrows[0] - lb / 2), Pp(Wc / 2, yrows[0] + lb / 2), Pp(Wc / 2 + 230, yrows[0]))
    sh.text(Pp(0, -Dc / 2 + 6), "DOOR", 2.2, "BC")
    # ---------------------------------------------------------------- parts list + notes
    cab = cabinet()
    nblk = c["shelves"] * c["monoblocs_per_shelf"]
    items = [(1, "CABINET FRAME: POSTS, PLINTH, SLOTTED ROOF, SIDE + REAR PANELS", "STEEL, POWDER-COATED", "1"),
             (2, "FRONT DOOR WITH LOW + HIGH LOUVRES, FLUSH HANDLE, 3 HINGES", "STEEL, POWDER-COATED", "1"),
             (3, "SHELF WITH FRONT LIP + SIDE SUPPORTS", "GALVANISED STEEL", str(c["shelves"])),
             (4, "R1 12 V MONOBLOC (SB-GA-001)", "PP-GF20 CASE", str(nblk)),
             (5, f"MASTER BMS ({BMS['comms'][0]} / {BMS['comms'][1]}; H2 + PRESSURE INPUTS)", "-", "1"),
             (6, "DC STRING BREAKER (MCCB-STYLE)", "-", "1"),
             (7, "VERTICAL CABLE DUCT SEGMENT", "PP", str(c["shelves"] - 1)),
             (8, "INTER-BLOCK JUMPER, 25 mm2", "Cu, INSULATED", str((c["monoblocs_per_shelf"] - 1) * c["shelves"]))]
    sh.table(3950, 1950, [9, 118, 40, 11], [("NO", "DESCRIPTION", "MATERIAL", "QTY")] + [(str(i[0]), i[1], i[2], i[3]) for i in items],
             h=2.1, row_h=5.0, title="PARTS LIST")
    sh.notes(300, 1000, [
        "NOTES",
        "1. CONCEPT — NOT FOR FABRICATION. ALL DIMENSIONS IN mm. TOLERANCES: CONCEPT (NONE SPECIFIED). FIRST-ANGLE PROJECTION.",
        f"2. CABINET {f1(Wc)} x {f1(Dc)} x {f1(Hc)} (params CABINET); {c['shelves']} SHELVES x {c['monoblocs_per_shelf']} MONOBLOCS = {nblk} IN SERIES,"
        f" {cab['string_V']:.0f} V NOM [CALC] (CABINET string_nominal_V {c['string_nominal_V']:.0f} V).",
        f"3. OPEN ISSUE: SHELF PITCH {f1(pitch, 1)} LEAVES ONLY {f1(CAB_TERMINAL_CLEAR_MM)} mm ABOVE THE BLOCK LIDS FOR LUGS + CABLES;"
        " CONSIDER 7 SHELVES OR A TALLER FRAME.",
        f"4. HYDROGEN: NATURAL VENTILATION - LOW DOOR INLET, REAR PLENUM, HIGH DOOR LOUVRES + ROOF SLOTS. DESIGN LIMIT"
        f" {GAS['h2_limit_fraction'].value * 100:.0f} % H2 BY VOLUME [LIT];",
        "    VENT AREA TO BE SIZED FROM THE S4 GAS RATES BEFORE ANY BUILD.",
        "5. MASTER BMS + DC STRING BREAKER IN THE TOP-SHELF FRONT-RIGHT SLOT; CABLE DUCT IN THE SAME SLOT ON SHELVES 1-7.",
        f"6. ENERGY {cab['energy_kWh']:.1f} kWh [CALC]; MASS {cab['mass_kg']:.0f} kg [CALC, design.cabinet] -> FLOOR LOAD"
        f" ~{cab['mass_kg'] / (Wc * Dc / 1e6):.0f} kg/m2 OVER THE FOOTPRINT (CHECK SITE).",
        "7. MONOBLOCS SHOWN AS ENVELOPES; GENERATED BY drawings/make_drawings.py FROM params/*.py.",
    ], h=2.3, step=4.4)
    sh.frame("SOURCE: params/*.py")
    return sh


# ===================================================================================================== run
def run_cadcraft(sh: Sheet):
    dxf, png, pdf = OUT / f"{sh.dwg}.dxf", OUT / f"{sh.dwg}.png", OUT / f"{sh.dwg}.pdf"
    args = [CADCRAFT, "run", "--metric"]
    for c in sh.cmds:
        args += ["--cmd", c]
    args += ["--cmd", "exportpdf " + json.dumps({"path": str(pdf), "paper": "A2", "scale": f"1:{f1(sh.S)}", "landscape": True}),
             "--save", str(dxf), "--export", str(png)]
    (OUT / f"{sh.dwg}_commands.jsonl").write_text("\n".join(sh.cmds))
    res = subprocess.run(args, capture_output=True, text=True)
    errs = [ln for ln in (res.stderr + res.stdout).splitlines() if "error" in ln.lower()]
    ok = res.returncode == 0 and dxf.exists() and pdf.exists() and png.exists()
    return ok, res.returncode, errs


def fallback_ezdxf(sh: Sheet):
    """Replay the command list into ezdxf and plot with matplotlib (used only if CADCraft fails twice)."""
    import ezdxf
    from ezdxf.addons.drawing import matplotlib as mpl_draw
    doc = ezdxf.new("R2018", setup=True)
    msp = doc.modelspace()
    cur = "0"
    for c in sh.cmds:
        cid, js = c.split(" ", 1)
        p = json.loads(js)
        if cid == "layer.new" and p["name"] not in doc.layers:
            doc.layers.add(p["name"], color=p.get("color", 7))
        elif cid == "layer.current":
            cur = p["name"]
        elif cid == "rectang":
            (x0, y0), (x1, y1) = p["p1"], p["p2"]
            msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": cur})
        elif cid == "line":
            msp.add_lwpolyline(p["points"], close=p.get("closed", False), dxfattribs={"layer": cur})
        elif cid == "circle":
            msp.add_circle(p["center"], p["radius"], dxfattribs={"layer": cur})
        elif cid == "text":
            msp.add_text(p["text"], height=p["height"], dxfattribs={"layer": cur}).set_placement(p["at"])
        elif cid == "dimlinear":
            (x0, y0), (x1, y1), (ax, ay) = p["p1"], p["p2"], p["at"]
            ang = 90 if abs(x1 - x0) < abs(y1 - y0) else 0
            dim = msp.add_linear_dim(base=(ax, ay), p1=(x0, y0), p2=(x1, y1), angle=ang, dimstyle="EZDXF",
                                     override={"dimtxt": 2.5 * sh.S, "dimasz": 2.2 * sh.S})
            dim.render()
    dxf = OUT / f"{sh.dwg}.dxf"
    doc.saveas(dxf)
    mpl_draw.qsave(msp, str(OUT / f"{sh.dwg}.png"), bg="#FFFFFF", dpi=150)
    mpl_draw.qsave(msp, str(OUT / f"{sh.dwg}.pdf"), bg="#FFFFFF")


def paper_png(sh: Sheet):
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return None
    pdf = pdfium.PdfDocument(str(OUT / f"{sh.dwg}.pdf"))
    img = pdf[0].render(scale=200 / 72).to_pil().convert("RGB")
    out = OUT / f"{sh.dwg}_paper.png"
    img.save(out)
    return out


def main(argv):
    which = argv or ["SB-GA-001", "SB-GA-002", "SB-GA-003"]
    builders = {"SB-GA-001": ga001, "SB-GA-002": ga002, "SB-GA-003": ga003}
    status = {}
    for dwg in which:
        sh = builders[dwg]()
        ok, rc, errs = run_cadcraft(sh)
        tool = "CADCraft"
        if not ok:
            print(f"{dwg}: CADCraft attempt 1 failed (exit {rc}) {errs[:3]} - retrying")
            ok, rc, errs = run_cadcraft(sh)
        if not ok:
            print(f"{dwg}: CADCraft failed twice - falling back to ezdxf + matplotlib")
            fallback_ezdxf(sh)
            tool = "ezdxf+matplotlib (fallback)"
        pp = paper_png(sh)
        status[dwg] = dict(tool=tool, commands=len(sh.cmds), errors=errs[:10], paper_png=str(pp) if pp else None)
        print(f"{dwg}: {tool}, {len(sh.cmds)} commands, errors: {len(errs)} {errs[:3]}")
    (OUT / "drawings_status.json").write_text(json.dumps(status, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
