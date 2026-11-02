"""S-cell R0: salt-assembled planar Na | beta''-alumina | NaAlCl4 | (Fe,Ni)Cl2 LAB TEST CELL - parametric CAD + drawing.

CONCEPT - NOT FOR FABRICATION until the qualification tests named in the part list (QT-xx) pass.
All dimensions from params/scell_params.py (CELL, cathode_charge). build123d / OpenCascade for 3D, CADCraft for 2D.

Outputs (cad/out/scell/):
  scell_r0.step / .stl / .glb             assembled, named solids (z = 0 at the anode face of the beta'' disc)
  scell_r0_exploded.step                  exploded along z for the assembly map
  stl/<part>.stl                          one mesh per part (non-critical visual / jig use only)
  scell_r0_partlist.csv                   item, part, material spec, qty, mass, tolerance, qualification test, BOM link
  scell_meta.json                         z-stack, masses, cathode-thickness check
Drawing (drawings/out/): SB-SC-001.{dxf,pdf,png}  section A-A 2:1, plan view, item table, loading table, notes.

Usage: python cad/make_scell.py [--no-drawing] [--qa 60]
"""
from __future__ import annotations
import csv, json, math, sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "drawings"))
from build123d import Align, Color, Compound, Cylinder, Location, Pos, export_gltf, export_step, export_stl  # noqa: E402
from params.scell_params import CELL, LOADINGS_mAh_cm2, OPERATE, cathode_charge  # noqa: E402

OUT = LAB / "cad" / "out" / "scell"; (OUT / "stl").mkdir(parents=True, exist_ok=True)
BOT = (Align.CENTER, Align.CENTER, Align.MIN)
DENS = {"beta_alumina": 3.26, "alpha_alumina": 3.95, "glass": 2.5, "Ni201": 8.89, "SS316L": 7.99, "Mo": 10.22, "graphite_foil": 1.1,
        "mica": 2.8, "steel_8.8": 7.85, "cathode_bed": 2.4, "SS316L_mesh": 2.0}

def cyl(r, z0, z1):
    return Cylinder(r, z1 - z0, align=BOT).moved(Location((0, 0, z0)))

def tube(ro, ri, z0, z1):
    return cyl(ro, z0, z1) - cyl(ri, z0 - 0.01, z1 + 0.01)

def build(qa=60.0):
    c = CELL; t = c["disc_t_mm"]; ch = cathode_charge(qa)
    P = []  # (item, name, shape, material, qty, tol, qt, bom, colour)
    def add(item, name, shape, mat, tol, qt, bom, col, qty=1):
        P.append(dict(item=item, name=name, shape=shape, mat=mat, qty=qty, tol=tol, qt=qt, bom=bom, col=col))
    # ---- ceramic core: disc in alpha ring counterbore, glass seal ring
    add(1, "beta''-alumina electrolyte disc", cyl(c["disc_d_mm"] / 2, 0, t), "beta_alumina",
        f"OD {c['disc_d_mm']} +0/-0.1; t {t} +/-0.05; flatness 0.02; both faces lapped", "QT-01 conductivity, QT-02 He leak", "PS-M-01", (0.95, 0.93, 0.85))
    ring = tube(c["ring_od_mm"] / 2, c["ring_id_mm"] / 2, t - c["ring_t_mm"], t) - cyl(c["ring_cbore_d_mm"] / 2, 0, t + 0.01)
    add(2, "alpha-alumina insulating ring (counterbored)", ring, "alpha_alumina",
        f"OD {c['ring_od_mm']} +/-0.1; ID {c['ring_id_mm']} +/-0.1; c'bore {c['ring_cbore_d_mm']} +0.05/0 x {t} deep; faces flat 0.02",
        "QT-02 He leak (after seal)", "PS-M-02", (0.98, 0.98, 0.97))
    add(3, "glass seal (disc-to-ring)", tube(c["ring_cbore_d_mm"] / 2, c["disc_d_mm"] / 2, 0, t), "glass",
        "fillet fills radial gap 0.2; CTE-matched sealing glass", "QT-02 He leak, QT-03 20 thermal cycles", "PS-M-03", (0.55, 0.75, 0.80))
    z_top = t
    # ---- cathode side (positive, top)
    g = c["gasket_t_mm"]
    add(4, "cathode-side gasket (graphite foil)", tube(c["ring_od_mm"] / 2, c["ring_id_mm"] / 2 + 0.5, z_top, z_top + g), "graphite_foil",
        f"t {g} before compression; OD/ID +/-0.2", "QT-04 NaAlCl4 compatibility 500 h at 260 C", "PS-M-04", (0.15, 0.15, 0.15))
    z0 = z_top + g
    cup_h = c["flange_t_mm"] + c["cath_cup_depth_mm"] - c["flange_t_mm"] + 3.0
    cath = (cyl(c["flange_od_mm"] / 2, z0, z0 + c["flange_t_mm"]) + cyl((c["active_d_mm"] / 2 + c["cup_wall_mm"]), z0, z0 + c["cath_cup_depth_mm"] + 3.0)) \
        - cyl(c["active_d_mm"] / 2, z0 - 0.01, z0 + c["cath_cup_depth_mm"])
    for k in range(c["bolt_n"]):
        a = 2 * math.pi * k / c["bolt_n"]
        cath = cath - Cylinder(3.1, 40).moved(Location((c["bolt_pcd_mm"] / 2 * math.cos(a), c["bolt_pcd_mm"] / 2 * math.sin(a), z0)))
    cath = cath - Cylinder(c["fill_tube_od_mm"] / 2 + 0.05, 20).moved(Location((-6, 0, z0 + c["cath_cup_depth_mm"])))
    cath = cath - Cylinder(c["tc_well_od_mm"] / 2 + 0.05, 20).moved(Location((6, 0, z0 + c["cath_cup_depth_mm"])))
    add(5, "cathode housing / + terminal (Ni 201)", cath, "Ni201",
        "ISO 2768-mK; sealing face flat 0.02, Ra 0.8; bolt holes 6.2 for insulating sleeves", "QT-04 compatibility; QT-05 Ni chloridisation check", "PS-M-05", (0.62, 0.64, 0.60))
    bed_t = ch["cathode_thickness_mm"]
    add(6, f"cathode granule bed NaCl+Fe+Ni+additives, NaAlCl4-infiltrated ({qa:.0f} mAh/cm2)", cyl(c["active_d_mm"] / 2 - 0.05, z_top, z_top + bed_t),
        "cathode_bed", f"{ch['granules_g']:.2f} g granules + {ch['NaAlCl4_g']:.2f} g NaAlCl4; thickness {bed_t:.2f} mm (calc)", "QT-06 granule moisture <100 ppm",
        "PS-C-01..09", (0.25, 0.20, 0.18))
    add(7, "cathode current collector mesh (Mo)", cyl(c["active_d_mm"] / 2 - 0.1, z_top + bed_t, z_top + bed_t + c["mesh_t_mm"]), "Mo",
        "Mo mesh disc, dia 23.8; welded to Mo wave spring", "QT-04", "PS-M-06", (0.55, 0.55, 0.58))
    add(8, "Mo wave spring (cathode compression)", tube(c["active_d_mm"] / 2 - 2, c["active_d_mm"] / 2 - 3, z_top + bed_t + c["mesh_t_mm"], z0 + c["cath_cup_depth_mm"]),
        "Mo", "free height >= gap + 0.5 mm; load 20-40 N", "QT-04", "PS-M-07", (0.55, 0.55, 0.58))
    tube_len = 25.0
    add(9, "fill tube (Ni 201, crimp + weld after infiltration)", tube(c["fill_tube_od_mm"] / 2, c["fill_tube_id_mm"] / 2, z0 + c["cath_cup_depth_mm"], z0 + c["cath_cup_depth_mm"] + tube_len).moved(Location((-6, 0, 0))),
        "Ni201", "1/8 in OD x 0.024 in wall", "QT-02", "PS-M-08", (0.62, 0.64, 0.60))
    add(10, "thermocouple well (Ni 201, closed end)", cyl(c["tc_well_od_mm"] / 2, z0 + 1.0, z0 + c["cath_cup_depth_mm"] + 15).moved(Location((6, 0, 0))),
        "Ni201", "closed-end 1/8 in tube, tip 1 mm above Mo spring", "-", "PS-M-08", (0.62, 0.64, 0.60))
    # ---- anode side (negative, bottom)
    zb = t - c["ring_t_mm"]
    add(11, "anode-side gasket (graphite foil)", tube(c["ring_od_mm"] / 2, c["ring_id_mm"] / 2 + 0.5, zb - g, zb), "graphite_foil",
        f"t {g}", "QT-07 Na compatibility 500 h at 260 C", "PS-M-04", (0.15, 0.15, 0.15))
    za = zb - g
    an = (cyl(c["flange_od_mm"] / 2, za - c["flange_t_mm"], za) + cyl((c["active_d_mm"] / 2 + c["cup_wall_mm"]), za - c["anode_cup_depth_mm"] - 3.0, za)) \
        - cyl(c["active_d_mm"] / 2, za - c["anode_cup_depth_mm"], za + 0.01)
    for k in range(c["bolt_n"]):
        a = 2 * math.pi * k / c["bolt_n"]
        an = an - Cylinder(2.25, 40).moved(Location((c["bolt_pcd_mm"] / 2 * math.cos(a), c["bolt_pcd_mm"] / 2 * math.sin(a), za)))
    add(12, "anode housing / - terminal (SS 316L)", an, "SS316L", "ISO 2768-mK; sealing face flat 0.02, Ra 0.8; M4 clearance 4.5", "QT-07", "PS-M-09", (0.72, 0.74, 0.77))
    add(13, "anode wick: SS 316L mesh roll + 0.1 mm shim (Na wetting path)", cyl(c["active_d_mm"] / 2 - 1.5, za - c["anode_cup_depth_mm"], 0.0), "SS316L_mesh",
        "compressed 0.3 mm against disc anode face", "QT-07", "PS-M-10", (0.70, 0.70, 0.72))
    # ---- fasteners + insulation
    zt, zbb = z0 + c["flange_t_mm"], za - c["flange_t_mm"]
    for k in range(c["bolt_n"]):
        a = 2 * math.pi * k / c["bolt_n"]; x, y = c["bolt_pcd_mm"] / 2 * math.cos(a), c["bolt_pcd_mm"] / 2 * math.sin(a)
        add(14, "bolt M4x30 ISO 4762 A4-70 (with nut, Belleville stack)", Cylinder(2.0, zt - zbb + 8, align=BOT).moved(Location((x, y, zbb - 4))),
            "SS316L", "torque 1.2 N.m at RT; re-check after first heat-up", "-", "PS-M-11", (0.45, 0.45, 0.47))
        add(15, "insulating sleeve (alpha-alumina, OD 6 / ID 4.2)", tube(3.0, 2.1, z0, zt).moved(Location((x, y, 0))), "alpha_alumina",
            "length = flange t", "QT-08 insulation > 10 MOhm at 260 C", "PS-M-12", (0.98, 0.98, 0.97))
        add(16, "mica washer (insulating, under bolt head)", tube(4.5, 2.1, zt, zt + 0.3).moved(Location((x, y, 0))), "mica", "t 0.3", "QT-08", "PS-M-13", (0.85, 0.80, 0.65))
    return P, ch, dict(z_disc=(0, t), z_cath_flange=(z0, z0 + c["flange_t_mm"]), z_anode_flange=(za - c["flange_t_mm"], za), cathode_thickness_mm=bed_t,
                       cath_gap_mm=c["cath_cup_depth_mm"] - (t + bed_t + c["mesh_t_mm"] - z0) if False else z0 + c["cath_cup_depth_mm"] - (z_top + bed_t + c["mesh_t_mm"]))

def export(P, ch, meta, qa):
    shapes = []
    for p in P:
        s = p["shape"]; s.label = f"{p['item']:02d} {p['name']}"; s.color = Color(*p["col"]); shapes.append(s)
    asm = Compound(children=shapes, label="S-cell R0 assembly")
    export_step(asm, str(OUT / "scell_r0.step")); export_stl(Compound(shapes), str(OUT / "scell_r0.stl"), tolerance=0.02, angular_tolerance=0.2)
    try:
        export_gltf(asm, str(OUT / "scell_r0.glb"), binary=True)
    except Exception as e:  # noqa
        print("glb export skipped:", e)
    # exploded: spread along z by item order on each side of the disc
    off = {1: 0, 2: 0, 3: 0, 4: 12, 5: 30, 6: 18, 7: 22, 8: 25, 9: 30, 10: 30, 11: -12, 12: -30, 13: -20, 14: 45, 15: 38, 16: 50}
    ex = []
    for p in P:
        s = p["shape"].moved(Location((0, 0, off[p["item"]]))); s.label = f"{p['item']:02d} {p['name']}"; s.color = Color(*p["col"]); ex.append(s)
    export_step(Compound(children=ex, label="S-cell R0 exploded"), str(OUT / "scell_r0_exploded.step"))
    seen = set(); rows = []
    for p in P:
        key = p["item"]
        vol = p["shape"].volume / 1000.0   # cm3
        m = vol * DENS[p["mat"]]
        if key not in seen:
            export_stl(p["shape"], str(OUT / "stl" / f"{key:02d}_{p['mat']}.stl"), tolerance=0.02, angular_tolerance=0.2)
            qty = sum(1 for q in P if q["item"] == key)
            rows.append(dict(item=key, part=p["name"], material=p["mat"], qty=qty, unit_mass_g=round(m, 3), total_mass_g=round(m * qty, 2),
                             tolerance_spec=p["tol"], qualification_test=p["qt"], bom_item=p["bom"]))
            seen.add(key)
    with open(OUT / "scell_r0_partlist.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    total = sum(r["total_mass_g"] for r in rows)
    meta |= dict(qa_mAh_cm2=qa, cathode_charge={k: round(v, 4) for k, v in ch.items()}, total_mass_g=round(total, 1),
                 energy_Wh=round(ch["Q_mAh"] / 1000 * 2.2, 3), lab_cell_Wh_per_kg=round(ch["Q_mAh"] / 1000 * 2.2 / total * 1000, 2),
                 note="Lab fixture: heavy metal housings dominate mass; Wh/kg here is NOT a cell-design metric [CALCULATED]")
    (OUT / "scell_meta.json").write_text(json.dumps(meta, indent=1, default=float))
    return rows, meta

def drawing(rows, meta, qa):
    import make_drawings as MD
    c = CELL; S = 0.5                       # 2:1 enlargement (model mm per paper mm)
    sh = MD.Sheet("SB-SC-001", "S-CELL R0 PLANAR TEST CELL", S, "2:1")
    sh.dimstyle("SB", 1.0)
    X0, Z0 = 80.0, 132.0                     # section origin on sheet (model mm)
    def R(r0, r1, z0, z1, hatch=None, lay="OUTLINE"):
        for sgn in (1, -1):
            a, b = sorted((X0 + sgn * r0, X0 + sgn * r1)); sh.rect((a, Z0 + z0), (b, Z0 + z1), lay, hatch=hatch, hs=0.25)
    t = c["disc_t_mm"]; g = c["gasket_t_mm"]; z0 = t + g; za = t - c["ring_t_mm"] - g; bed = meta["cathode_thickness_mm"]
    R(0, c["disc_d_mm"] / 2, 0, t, "ANSI37")                                                       # 1 disc (full width)
    R(c["ring_cbore_d_mm"] / 2, c["ring_od_mm"] / 2, 0, t, "ANSI31"); R(c["ring_id_mm"] / 2, c["ring_od_mm"] / 2, t - c["ring_t_mm"], 0, "ANSI31")  # 2 ring
    R(c["disc_d_mm"] / 2, c["ring_cbore_d_mm"] / 2, 0, t)                                            # 3 glass
    R(c["ring_id_mm"] / 2 + 0.5, c["ring_od_mm"] / 2, t, t + g, "SOLID"); R(c["ring_id_mm"] / 2 + 0.5, c["ring_od_mm"] / 2, za, za + g, "SOLID")  # 4/11 gaskets
    R(c["active_d_mm"] / 2, c["flange_od_mm"] / 2, z0, z0 + c["flange_t_mm"], "ANSI32")              # 5 flange
    R(c["active_d_mm"] / 2, (c["active_d_mm"] / 2 + c["cup_wall_mm"]), z0 + c["flange_t_mm"], z0 + c["cath_cup_depth_mm"], "ANSI32")
    R(0, (c["active_d_mm"] / 2 + c["cup_wall_mm"]), z0 + c["cath_cup_depth_mm"], z0 + c["cath_cup_depth_mm"] + 3.0, "ANSI32")
    R(0, c["active_d_mm"] / 2 - 0.05, t, t + bed, "AR-SAND")                                         # 6 bed
    R(0, c["active_d_mm"] / 2 - 0.1, t + bed, t + bed + c["mesh_t_mm"])                               # 7 mesh
    R(c["active_d_mm"] / 2, c["flange_od_mm"] / 2, za - c["flange_t_mm"], za, "ANSI33")              # 12 anode flange
    R(c["active_d_mm"] / 2, (c["active_d_mm"] / 2 + c["cup_wall_mm"]), za - c["anode_cup_depth_mm"], za - c["flange_t_mm"], "ANSI33")
    R(0, (c["active_d_mm"] / 2 + c["cup_wall_mm"]), za - c["anode_cup_depth_mm"] - 3.0, za - c["anode_cup_depth_mm"], "ANSI33")
    R(0, c["active_d_mm"] / 2 - 1.5, za - c["anode_cup_depth_mm"], 0, None, "THIN")                 # 13 wick
    for sgn in (1, -1):                                                                              # 14 bolts (centreline + outline)
        xb = X0 + sgn * c["bolt_pcd_mm"] / 2
        sh.line([(xb, Z0 + za - c["flange_t_mm"] - 4), (xb, Z0 + z0 + c["flange_t_mm"] + 4)], "CENTER")
        sh.rect((xb - 2, Z0 + za - c["flange_t_mm"] - 3.2), (xb + 2, Z0 + z0 + c["flange_t_mm"] + 3), "PHANTOM")
    sh.line([(X0, Z0 - 25), (X0, Z0 + 35)], "CENTER")
    # dimensions
    sh.dim((X0 - c["flange_od_mm"] / 2, Z0 - 22), (X0 + c["flange_od_mm"] / 2, Z0 - 22), (X0, Z0 - 28), f"%%c{c['flange_od_mm']:.0f}")
    sh.dim((X0 - c["active_d_mm"] / 2, Z0 + t), (X0 + c["active_d_mm"] / 2, Z0 + t), (X0, Z0 + 27), f"%%c{c['active_d_mm']:.0f} ACTIVE")
    sh.dim((X0 - c["disc_d_mm"] / 2, Z0), (X0 + c["disc_d_mm"] / 2, Z0), (X0, Z0 - 12), f"%%c{c['disc_d_mm']:.0f}")
    sh.dim((X0 + 36, Z0), (X0 + 36, Z0 + t), (X0 + 40, Z0 + t / 2), f"{t:.1f}")
    sh.dim((X0 - 36, Z0 + t), (X0 - 36, Z0 + t + bed), (X0 - 42, Z0 + t + bed / 2), f"{bed:.2f} @ {qa:.0f} mAh/cm2")
    # balloons
    tgt = {1: (X0 + 5, Z0 + t / 2), 2: (X0 + 19, Z0 - 1.5), 3: (X0 + 15.1, Z0 + 0.5), 4: (X0 + 18, Z0 + t + g / 2), 5: (X0 + 25, Z0 + z0 + 2.5),
           6: (X0 - 5, Z0 + t + bed / 2), 7: (X0 - 8, Z0 + t + bed + 0.15), 11: (X0 - 18, Z0 + za + g / 2), 12: (X0 - 25, Z0 + za - 2.5),
           13: (X0 + 4, Z0 + za - 3), 14: (X0 + c["bolt_pcd_mm"] / 2, Z0 + z0 + c["flange_t_mm"] + 2)}
    pos = {1: (X0 + 52, Z0 + 4), 2: (X0 + 52, Z0 - 6), 3: (X0 + 44, Z0 + 14), 4: (X0 + 44, Z0 + 22), 5: (X0 + 38, Z0 + 30), 6: (X0 - 46, Z0 + 18),
           7: (X0 - 38, Z0 + 27), 11: (X0 - 46, Z0 - 10), 12: (X0 - 44, Z0 - 18), 13: (X0 + 18, Z0 - 20), 14: (X0 + 44, Z0 + 38)}
    for k, p in pos.items():
        sh.balloon(k, tgt[k], p)
    sh.text((X0 - 40, Z0 + 46), "SECTION A-A  (2:1)   z = 0 AT ANODE FACE OF ITEM 1", 4.0)
    # plan view
    PX, PZ = 200.0, 140.0
    sh.circle((PX, PZ), c["flange_od_mm"] / 2); sh.circle((PX, PZ), c["active_d_mm"] / 2, "HIDDEN"); sh.circle((PX, PZ), c["bolt_pcd_mm"] / 2, "CENTER")
    for k in range(c["bolt_n"]):
        a = 2 * math.pi * k / c["bolt_n"]; sh.circle((PX + c["bolt_pcd_mm"] / 2 * math.cos(a), PZ + c["bolt_pcd_mm"] / 2 * math.sin(a)), 3.1)
    sh.circle((PX - 6, PZ), c["fill_tube_od_mm"] / 2); sh.circle((PX + 6, PZ), c["tc_well_od_mm"] / 2)
    sh.line([(PX - 36, PZ), (PX + 36, PZ)], "CENTER"); sh.text((PX - 34, PZ + 2), "A", 4.0); sh.text((PX + 32, PZ + 2), "A", 4.0)
    sh.text((PX - 30, PZ + 36), f"PLAN (2:1)  {c['bolt_n']}x {c['bolt_size']} ON PCD {c['bolt_pcd_mm']:.0f}; FILL TUBE (L), TC WELL (R)", 3.0)
    # item table
    tab = [["ITEM", "PART", "MATERIAL", "QTY", "QUALIFICATION"]] + [[r["item"], r["part"][:46], r["material"], r["qty"], r["qualification_test"][:30]] for r in rows]
    sh.table(10.0, 84.0, [12, 92, 30, 10, 58], tab, h=2.2, row_h=4.6, title="ITEM LIST (BOM link: scell_r0_partlist.csv / PROJECT_SALT/06_PROCUREMENT)")
    lt = [["mAh/cm2", "NaCl g", "Fe g", "Ni g", "granules g", "NaAlCl4 g", "bed mm"]]
    for q in LOADINGS_mAh_cm2:
        d = cathode_charge(q); lt.append([q, f"{d['NaCl_g']:.3f}", f"{d['Fe_g']:.3f}", f"{d['Ni_g']:.3f}", f"{d['granules_g']:.3f}", f"{d['NaAlCl4_g']:.3f}", f"{d['cathode_thickness_mm']:.2f}"])
    sh.table(160.0, 95.0, [18, 16, 14, 14, 20, 20, 16], lt, h=2.2, row_h=4.6, title="CATHODE CHARGE PER CELL (params/scell_params.py)")
    sh.notes(10.0, 37.0, [
        "NOTES", "1. ASSEMBLE DISCHARGED (NaCl + Fe) IN Ar GLOVEBOX, H2O/O2 < 1 ppm. NO SODIUM METAL IS HANDLED AT ASSEMBLY.",
        "2. GENERAL TOLERANCES ISO 2768-mK. SEALING FACES (ITEMS 2,5,12) FLATNESS 0.02, Ra 0.8.",
        f"3. OPERATE {OPERATE['T_range_C'][0]:.0f}-{OPERATE['T_range_C'][1]:.0f} C; HEAT/COOL <= {OPERATE['T_ramp_C_per_min']:.0f} C/min; HW TRIP {OPERATE['T_trip_C']:.0f} C.",
        f"4. CELL LIMITS {OPERATE['V_discharge_min']}-{OPERATE['V_charge_max']} V; TRIPS {OPERATE['V_trip_low']}/{OPERATE['V_trip_high']} V (SIDE REACTIONS 1.58/3.05 V).",
        "5. GASKET/SEAL MATERIALS ARE CANDIDATES - QT-02/03/04/07/08 MUST PASS BEFORE ANY CHARGED CELL.",
        "6. ITEMS 1-3 SUPPLIED AS A GLASS-SEALED SUB-ASSEMBLY OR SEALED AT PARTNER LAB (QUOTE REQUIRED).",
    ], h=2.2, step=4.0)
    sh.frame("SOURCE: params/scell_params.py, cad/make_scell.py")
    ok, rc, errs = MD.run_cadcraft(sh)
    tool = "CADCraft"
    if not ok:
        ok, rc, errs = MD.run_cadcraft(sh)
    if not ok:
        MD.fallback_ezdxf(sh); tool = "ezdxf+matplotlib (fallback)"
    MD.paper_png(sh)
    return tool, errs

if __name__ == "__main__":
    qa = float(sys.argv[sys.argv.index("--qa") + 1]) if "--qa" in sys.argv else 60.0
    P, ch, meta = build(qa)
    rows, meta = export(P, ch, meta, qa)
    print(json.dumps({k: meta[k] for k in ("total_mass_g", "energy_Wh", "cathode_thickness_mm", "cath_gap_mm")}, default=float))
    if "--no-drawing" not in sys.argv:
        print("drawing:", drawing(rows, meta, qa))
