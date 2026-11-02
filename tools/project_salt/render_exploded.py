#!/usr/bin/env python3
"""Render the S-cell R0 exploded assembly map (isometric, numbered callouts) from cad/out/scell/stl/*.stl.
Output: PROJECT_SALT/07_BUILD_MANUAL/assembly_maps/scell_r0_exploded.{png,svg}. Pure matplotlib (painter's algorithm)."""
import re, struct, sys
from pathlib import Path
import numpy as np
LAB = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(LAB / "tools"))
import plotstyle as ps  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

STL = LAB / "cad/out/scell/stl"; OUT = LAB / "PROJECT_SALT/07_BUILD_MANUAL/assembly_maps"; OUT.mkdir(parents=True, exist_ok=True)
OFF = {1: 0, 2: 0, 3: 0, 4: 14, 5: 44, 6: 22, 7: 28, 8: 33, 9: 44, 10: 44, 11: -14, 12: -42, 13: -26, 14: 62, 15: 52, 16: 70}
COL = {"beta_alumina": "#f2ead2", "alpha_alumina": "#fbfbf7", "glass": "#8cc0cc", "graphite_foil": "#2b2b2b", "Ni201": "#9ea39a",
       "cathode_bed": "#4a3b33", "Mo": "#8a8c94", "SS316L": "#b8bcc4", "SS316L_mesh": "#b3b3b8", "mica": "#d9cca6"}
NAMES = {1: "β''-alumina disc", 2: "α-alumina ring", 3: "glass seal", 4: "gasket (cathode)", 5: "cathode housing (+)", 6: "salt-iron granule bed",
         7: "Mo mesh", 8: "Mo spring", 11: "gasket (anode)", 12: "anode housing (−)", 13: "anode wick", 14: "M4 bolts ×6", 15: "sleeves ×6", 16: "mica ×6"}

def read_stl(p):
    b = p.read_bytes()
    if b[:5] == b"solid" and b"facet" in b[:400]:
        v = np.array(re.findall(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", b), dtype=float); return v.reshape(-1, 3, 3)
    n = struct.unpack("<I", b[80:84])[0]
    a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return a["v"].reshape(-1, 3, 3).astype(float)

def main():
    ps.apply()
    th, ph = np.radians(35), np.radians(-30)
    R = np.array([[np.cos(ph), -np.sin(ph), 0], [np.sin(ph) * np.sin(th), np.cos(ph) * np.sin(th), np.cos(th)],
                  [np.sin(ph) * np.cos(th), np.cos(ph) * np.cos(th), -np.sin(th)]])
    polys, cols, depth, anchors = [], [], [], {}
    light = np.array([0.3, -0.4, 0.85]); light /= np.linalg.norm(light)
    for f in sorted(STL.glob("*.stl")):
        item = int(f.stem.split("_")[0]); mat = f.stem.split("_", 1)[1]
        tri = read_stl(f).copy(); tri[:, :, 2] += OFF.get(item, 0)
        if item in (14, 15, 16):   # one bolt instance -> show the others shifted round the PCD
            pass
        p = tri @ R.T
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); nn = np.linalg.norm(nrm, axis=1); nrm = nrm / np.maximum(nn[:, None], 1e-9)
        shade = 0.55 + 0.45 * np.clip(nrm @ light, 0, 1)
        base = np.array([int(COL.get(mat, "#999999")[i:i + 2], 16) / 255 for i in (1, 3, 5)])
        for k in range(len(p)):
            polys.append(p[k, :, :2]); cols.append(np.clip(base * shade[k], 0, 1)); depth.append(p[k, :, 2].mean())
        c = tri.reshape(-1, 3); top = c[c[:, 0].argmax()]
        anchors[item] = (top @ R.T)[:2]
    order = np.argsort(depth)[::-1]
    fig, ax = plt.subplots(figsize=(8.5, 9.5))
    ax.add_collection(PolyCollection([polys[i] for i in order], facecolors=[cols[i] for i in order], edgecolors="none"))
    allp = np.vstack(polys); ax.set_xlim(allp[:, 0].min() - 5, allp[:, 0].max() + 60); ax.set_ylim(allp[:, 1].min() - 5, allp[:, 1].max() + 5)
    labs = sorted(((y, item, x) for item, (x, y) in anchors.items() if item in NAMES), reverse=True)
    gap = 0.03 * (allp[:, 1].max() - allp[:, 1].min()); ly_prev = None
    for y, item, x in labs:                      # top-down; push labels apart so none overlap
        ly = y if ly_prev is None or ly_prev - y >= gap else ly_prev - gap
        ly_prev = ly
        ax.annotate(f"{item}  {NAMES[item]}", (x, y), xytext=(allp[:, 0].max() + 12, ly), fontsize=8, va="center", color=ps.TEXT,
                    arrowprops=dict(arrowstyle="-", color=ps.TEXT2, lw=0.6))
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("S-cell R0 — exploded assembly map (z-stack; balloon numbers = SB-SC-001 items)")
    ps.save(fig, OUT / "scell_r0_exploded", "Exploded isometric view of the S-cell R0 test cell rendered from the build123d STL exports.",
            "[CAD] concept geometry from params/scell_params.py")
    print("rendered", len(polys), "triangles")

if __name__ == "__main__":
    main()
