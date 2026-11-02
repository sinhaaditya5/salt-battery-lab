"""Blender scene for the salt-iron designs (S-cell R0, P1 cell, SM-48T module, SC-UPS-1 cabinet).

  "$BLENDER" -b --factory-startup -P renders/blender_salt.py -- <shot> [--samples N] [--res WxH] [--out PATH] [--frames N]

Geometry is imported from the build123d exports (one STL per material group), never modelled here, so every render
shows the CAD as designed (Blender = visualisation only, brief section 7.1). Shots:
  r0_hero, r0_exploded            S-cell R0 lab test cell (cad/out/scell/stl/<item>_<mat>.stl)
  p1_exploded                     P1 planar product cell, layers separated
  module_hero, module_cutaway, module_exploded, module_turntable
  cabinet_closed, cabinet_open
Cycles on CPU (all cores) + OpenImageDenoise. Units: CAD mm -> Blender m.
"""
import math, sys
from pathlib import Path
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SHOT = argv[0] if argv else "module_hero"
opt = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
SAMPLES = int(opt("--samples", 96)); RES = tuple(int(v) for v in opt("--res", "1600x1000").split("x"))
FRAMES = int(opt("--frames", 96)); EXPO = float(opt("--expo", 0.5))      # light-level multiplier
LAB = Path(__file__).resolve().parents[1]; STL = LAB / "cad" / "out" / "stl"; OUT = Path(opt("--out", str(LAB / "renders" / "out_salt" / f"{SHOT}.png")))
MM = 0.001

MATS = {   # group -> principled settings
    "beta": dict(color=(0.93, 0.89, 0.78), rough=0.35, sss=0.15), "beta_alumina": dict(color=(0.93, 0.89, 0.78), rough=0.35, sss=0.15),
    "alpha": dict(color=(0.97, 0.97, 0.95), rough=0.45), "alpha_alumina": dict(color=(0.97, 0.97, 0.95), rough=0.45),
    "glass": dict(color=(0.55, 0.75, 0.85), rough=0.05, transmission=0.8),
    "nickel": dict(color=(0.70, 0.68, 0.63), metallic=1.0, rough=0.28), "Ni201": dict(color=(0.70, 0.68, 0.63), metallic=1.0, rough=0.28),
    "stainless": dict(color=(0.76, 0.77, 0.79), metallic=1.0, rough=0.25), "SS316L": dict(color=(0.76, 0.77, 0.79), metallic=1.0, rough=0.25),
    "SS316L_mesh": dict(color=(0.60, 0.61, 0.63), metallic=1.0, rough=0.55), "stainless_dark": dict(color=(0.55, 0.56, 0.58), metallic=1.0, rough=0.4),
    "Mo": dict(color=(0.62, 0.63, 0.66), metallic=1.0, rough=0.35), "steel_8.8": dict(color=(0.45, 0.45, 0.47), metallic=1.0, rough=0.35),
    "graphite_foil": dict(color=(0.08, 0.08, 0.085), metallic=0.3, rough=0.5), "cathode_bed": dict(color=(0.16, 0.12, 0.10), rough=0.95),
    "mica": dict(color=(0.78, 0.62, 0.36), rough=0.35, transmission=0.15), "heater": dict(color=(0.55, 0.33, 0.12), rough=0.5),
    "busbar": dict(color=(0.86, 0.84, 0.80), metallic=1.0, rough=0.2), "insulation": dict(color=(0.86, 0.87, 0.86), rough=0.9),
    "case": dict(color=(0.20, 0.22, 0.24), rough=0.55, coat=0.1), "panel": dict(color=(0.04, 0.04, 0.045), metallic=0.4, rough=0.35),
    "pcb": dict(color=(0.05, 0.30, 0.15), rough=0.4), "black": dict(color=(0.03, 0.03, 0.035), rough=0.45),
    "red": dict(color=(0.72, 0.06, 0.05), rough=0.4), "fuse": dict(color=(0.92, 0.92, 0.88), rough=0.6),
    "handle": dict(color=(0.75, 0.76, 0.78), metallic=1.0, rough=0.3), "accent": dict(color=(0.90, 0.42, 0.08), rough=0.4),
    "led": dict(color=(0.1, 0.9, 0.3), emission=(0.1, 1.0, 0.35), strength=6.0),
    "cab_paint": dict(color=(0.80, 0.81, 0.80), rough=0.5), "cab_frame": dict(color=(0.04, 0.04, 0.045), rough=0.5),
    "cab_door": dict(color=(0.12, 0.13, 0.14), metallic=0.5, rough=0.45), "glass_hmi": dict(color=(0.02, 0.03, 0.05), rough=0.05, coat=1.0),
}
MATS["glass"] = dict(MATS["glass"])


def principled(name, color=(0.5, 0.5, 0.5), metallic=0.0, rough=0.4, transmission=0.0, coat=0.0, sss=0.0, emission=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Metallic"].default_value = metallic; b.inputs["Roughness"].default_value = rough
    if transmission: b.inputs["Transmission Weight"].default_value = transmission
    if coat: b.inputs["Coat Weight"].default_value = coat
    if sss: b.inputs["Subsurface Weight"].default_value = sss
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1); b.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*color, 1)
    return m


_MC = {}
def mat(g):
    if g not in _MC: _MC[g] = principled("M_" + g, **MATS.get(g, dict(color=(0.5, 0.5, 0.5))))
    return _MC[g]


def import_stl(f, group, offset=(0, 0, 0)):
    bpy.ops.wm.stl_import(filepath=str(f), global_scale=MM, forward_axis="Y", up_axis="Z")
    o = bpy.context.selected_objects[0]; o.name = f.stem
    try:
        bpy.context.view_layer.objects.active = o; bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30))
    except Exception:
        pass
    o.data.materials.append(mat(group)); o.location = Vector(offset) * MM; o.select_set(False)
    return o


def import_groups(asm, variant, offsets=None):
    objs = []
    for f in sorted((STL / asm / variant).glob("*.stl")):
        objs.append(import_stl(f, f.stem, (offsets or {}).get(f.stem, (0, 0, 0))))
    return objs


def import_scell(exploded=False):
    off = {1: 0, 2: 0, 3: 0, 4: 12, 5: 30, 6: 18, 7: 22, 8: 25, 9: 30, 10: 30, 11: -12, 12: -30, 13: -20, 14: 45, 15: 38, 16: 50}  # = make_scell
    objs = []
    for f in sorted((LAB / "cad" / "out" / "scell" / "stl").glob("*.stl")):
        item = int(f.stem.split("_")[0]); grp = f.stem.split("_", 1)[1]
        objs.append(import_stl(f, grp, (0, 0, off[item] if exploded else 0)))
    return objs


def bbox(objs):
    lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    bpy.context.view_layer.update()
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi


def stage(objs, view_dir, tight=1.0):
    lo, hi = bbox(objs); c = (lo + hi) / 2; r = (hi - lo).length / 2
    sc = bpy.context.scene
    # floor
    bpy.ops.mesh.primitive_plane_add(size=60 * r, location=(c.x, c.y, lo.z - 0.0005)); fl = bpy.context.active_object
    fl.data.materials.append(principled("M_floor", color=(0.80, 0.81, 0.82), rough=0.55))
    # world
    w = sc.world or bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.88, 0.89, 0.91, 1); bg.inputs["Strength"].default_value = 0.30 * EXPO
    # lights (scaled to the object)
    for name, d, e, s in (("key", (-2.0, -2.6, 3.0), 110 * EXPO, 2.2), ("fill", (3.0, -1.6, 1.4), 35 * EXPO, 3.0), ("rim", (0.5, 3.2, 2.6), 70 * EXPO, 2.0)):
        L = bpy.data.lights.new(name, "AREA"); L.energy = e * (r / 0.35) ** 2; L.size = s * r
        lo_ = bpy.data.objects.new(name, L); sc.collection.objects.link(lo_); lo_.location = c + Vector(d) * r
        tc = lo_.constraints.new("TRACK_TO"); tgt = bpy.data.objects.new(name + "_t", None); sc.collection.objects.link(tgt); tgt.location = c; tc.target = tgt
    # camera
    cam = bpy.data.cameras.new("cam"); cam.lens = 50; co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
    fov_v = 2 * math.atan((36 * RES[1] / RES[0] / 2) / 50)
    dist = r / math.sin(fov_v / 2) * 0.92 * tight
    co.location = c + Vector(view_dir).normalized() * dist
    tgt = bpy.data.objects.new("cam_t", None); sc.collection.objects.link(tgt); tgt.location = c
    tc = co.constraints.new("TRACK_TO"); tc.target = tgt
    cam.clip_end = dist * 10; cam.clip_start = dist / 1000
    return c, r


def setup_render(samples, res):
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
    sc.cycles.samples = samples; sc.cycles.use_adaptive_sampling = True; sc.cycles.use_denoising = True
    try: sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception: pass
    sc.cycles.max_bounces = 8; sc.cycles.transmission_bounces = 8
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"; sc.view_settings.view_transform = "AgX"


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    setup_render(SAMPLES, RES)
    s = SHOT
    if s == "r0_hero":       objs = import_scell(False); vd, tight = (1.0, -1.4, 0.9), 1.0
    elif s == "r0_exploded": objs = import_scell(True); vd, tight = (1.2, -1.5, 0.55), 1.0
    elif s == "p1_exploded":
        objs = import_groups("p1_cell", "full", {"stainless": (0, 0, 0), "beta": (0, 0, 28), "alpha": (0, 0, 28), "nickel": (0, 0, 56)}); vd, tight = (1.0, -1.3, 0.85), 1.0
    elif s in ("module_hero", "module_turntable"): objs = import_groups("sm48t_module", "full"); vd, tight = (-1.0, -1.5, 0.75), 1.0
    elif s == "module_cutaway": objs = import_groups("sm48t_module", "cutaway"); vd, tight = (1.35, -1.05, 0.8), 0.95
    elif s == "module_exploded": objs = import_groups("sm48t_module", "exploded"); vd, tight = (-1.1, -1.5, 0.7), 1.0
    elif s == "cabinet_closed": objs = import_groups("sc_ups1_cabinet", "closed"); vd, tight = (-0.9, -1.6, 0.45), 1.0
    elif s == "cabinet_open": objs = import_groups("sc_ups1_cabinet", "open"); vd, tight = (1.0, -1.7, 0.4), 1.0
    else: raise SystemExit("unknown shot " + s)
    c, r = stage(objs, vd, tight)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    if s.endswith("turntable"):
        piv = bpy.data.objects.new("pivot", None); sc.collection.objects.link(piv); piv.location = c
        for o in objs:
            o.parent = piv; o.matrix_parent_inverse = piv.matrix_world.inverted()
        sc.frame_start, sc.frame_end = 1, FRAMES
        bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"     # constant angular speed (Blender 5 layered actions)
        piv.rotation_euler = (0, 0, 0); piv.keyframe_insert("rotation_euler", frame=1)
        piv.rotation_euler = (0, 0, 2 * math.pi * (FRAMES - 1) / FRAMES); piv.keyframe_insert("rotation_euler", frame=FRAMES)
        sc.render.filepath = str(OUT.parent / (OUT.stem + "_frames") / "f_")
        bpy.ops.render.render(animation=True)
    else:
        sc.render.filepath = str(OUT); bpy.ops.render.render(write_still=True)
    print("RENDERED", s, OUT)


main()
