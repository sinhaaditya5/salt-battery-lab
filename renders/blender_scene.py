"""Salt Battery R1 concept renders in Blender 5.0 (Cycles, Metal GPU).  Run headless:

  "$BLENDER" -b --factory-startup -P renders/blender_scene.py -- <shot> [--samples N] [--res WxH] [--out PATH]

shots: hero | exploded | cutaway | module | row | room | r0 | turntable | preview <asm> <variant>
Reads the tessellated CAD from cad/out/stl/<asm>/<variant>/<group>.stl and anchors from cad/out/cad_meta.json
(all positions come from the build123d model, i.e. from params/). Writes renders/out/<shot>.png and
renders/out/anchors_<shot>.json (2D callout anchors for renders/annotate.py).
Pattern reused from PARC-Delta prototype/renders/blender_scene.py (read-only reference).
"""
import json
import math
import sys
import time
from pathlib import Path

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
STL = LAB / "cad" / "out" / "stl"
META = json.loads((LAB / "cad" / "out" / "cad_meta.json").read_text())
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["hero"]
SHOT = argv[0]
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 96
RES = tuple(int(v) for v in (argv[argv.index("--res") + 1] if "--res" in argv else "1920x1080").split("x"))
OUTPATH = Path(argv[argv.index("--out") + 1]) if "--out" in argv else OUT / f"{SHOT}.png"
MM = 0.001
LIGHT_GAIN = float(argv[argv.index("--gain") + 1]) if "--gain" in argv else 0.7

# ------------------------------------------------------------------------------------------ materials
MATS = {
    "case": dict(color=(0.085, 0.10, 0.12), rough=0.5, coat=0.1),
    "lid": dict(color=(0.06, 0.07, 0.085), rough=0.45, coat=0.1),
    "vent": dict(color=(0.02, 0.22, 0.50), rough=0.45),
    "epdm": dict(color=(0.03, 0.03, 0.03), rough=0.75),
    "frit": dict(color=(0.93, 0.93, 0.89), rough=0.95),
    "steel": dict(color=(0.74, 0.75, 0.77), metallic=1.0, rough=0.28),
    "terminal": dict(color=(0.86, 0.85, 0.80), metallic=1.0, rough=0.22),
    "red": dict(color=(0.72, 0.06, 0.05), rough=0.4),
    "black": dict(color=(0.03, 0.03, 0.035), rough=0.4),
    "label": dict(color=(0.93, 0.93, 0.90), rough=0.55),
    "cathode": dict(color=(0.06, 0.045, 0.04), rough=0.9),
    "anode": dict(color=(0.20, 0.21, 0.23), rough=0.85),
    "separator": dict(color=(0.78, 0.86, 0.95), rough=0.35, transmission=0.25),
    "electrolyte": dict(liquid=True),
    "tray": dict(color=(0.62, 0.64, 0.66), metallic=0.85, rough=0.42),
    "enclosure": dict(color=(0.15, 0.16, 0.18), rough=0.5),
    "cable_red": dict(color=(0.68, 0.06, 0.05), rough=0.5),
    "cable_black": dict(color=(0.03, 0.03, 0.03), rough=0.5),
    "sense": dict(color=(0.90, 0.70, 0.15), rough=0.5),
    "handle": dict(color=(0.08, 0.08, 0.09), rough=0.4),
    "cab_paint": dict(color=(0.40, 0.41, 0.41), rough=0.5),
    "cab_shelf": dict(color=(0.66, 0.68, 0.70), metallic=0.8, rough=0.45),
    "duct": dict(color=(0.32, 0.33, 0.35), rough=0.6),
    "breaker": dict(color=(0.06, 0.06, 0.07), rough=0.45),
    "accent": dict(color=(0.90, 0.42, 0.08), rough=0.4),
    "r0_steel": dict(color=(0.78, 0.79, 0.81), metallic=1.0, rough=0.18),
    "ptfe": dict(color=(0.95, 0.95, 0.92), rough=0.6),
    "peek": dict(color=(0.74, 0.58, 0.36), rough=0.45),
    "carbonpaper": dict(color=(0.05, 0.05, 0.055), rough=0.85),
    "coating": dict(color=(0.13, 0.08, 0.05), rough=0.9),
    "cellulose": dict(color=(0.97, 0.96, 0.92), rough=0.9),
    "spring": dict(color=(0.65, 0.67, 0.70), metallic=1.0, rough=0.3),
}
_MCACHE = {}


def principled(name, color=(0.5, 0.5, 0.5), metallic=0.0, rough=0.4, transmission=0.0, emission=None, strength=0.0,
               coat=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if transmission:
        b.inputs["Transmission Weight"].default_value = transmission
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.35
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1)
        b.inputs["Emission Strength"].default_value = strength
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*color, 1)          # Workbench preview colour
    return m


def liquid(name="M_electrolyte"):
    """Water-based electrolyte: clear refractive surface + blue volume absorption."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.80, 0.92, 1.0, 1)
    b.inputs["Roughness"].default_value = 0.03
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.335
    va = nt.nodes.new("ShaderNodeVolumeAbsorption")
    va.inputs["Color"].default_value = (0.10, 0.45, 1.0, 1)
    va.inputs["Density"].default_value = 140.0
    nt.links.new(va.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    m.diffuse_color = (0.35, 0.62, 0.95, 0.6)
    return m


def glow(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (*color, 1)
    return m


def mat(group):
    if group not in _MCACHE:
        spec = MATS.get(group, dict(color=(0.5, 0.5, 0.5)))
        _MCACHE[group] = liquid() if spec.get("liquid") else principled(f"M_{group}", **spec)
    return _MCACHE[group]


# ------------------------------------------------------------------------------------------ import
def import_variant(asm, variant, loc=(0, 0, 0), rz=0.0, tag=None, smooth=True):
    objs = []
    for f in sorted((STL / asm / variant).glob("*.stl")):
        bpy.ops.wm.stl_import(filepath=str(f), global_scale=MM, forward_axis="Y", up_axis="Z")
        o = bpy.context.selected_objects[0]
        o.name = f"{tag or asm}_{variant}_{f.stem}"
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bm.to_mesh(o.data)
        bm.free()
        bpy.context.view_layer.objects.active = o
        o.select_set(True)
        if smooth:
            try:
                bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30))
            except Exception:
                pass
        o.data.materials.append(mat(f.stem))
        o.select_set(False)
        o.location = loc
        o.rotation_euler = (0, 0, math.radians(rz))
        objs.append(o)
    return objs


def instance(objs, loc, rz=0.0, suffix="i"):
    out = []
    for o in objs:
        c = o.copy()
        c.name = o.name + suffix
        c.location = loc
        c.rotation_euler = (0, 0, math.radians(rz))
        bpy.context.collection.objects.link(c)
        out.append(c)
    return out


def add_box(name, size, loc, material, rz=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=(0, 0, math.radians(rz)))
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(material)
    return o


def text_obj(body, loc, size, material, rz=0.0, align="CENTER"):
    cd = bpy.data.curves.new("txt_" + body[:10], type="FONT")
    cd.body = body
    cd.size = size
    cd.align_x = align
    cd.align_y = "CENTER"
    o = bpy.data.objects.new("txt_" + body[:10], cd)
    o.location = loc
    o.rotation_euler = (0, 0, math.radians(rz))
    o.data.materials.append(material)
    bpy.context.collection.objects.link(o)
    return o


def lid_marks(origin=(0, 0, 0), rz=0.0, dz=0.0, full=True, side=True, side_dz0=False):
    """Label text + polarity marks on a monobloc lid (positions from the CAD anchors)."""
    a = META["r1_monobloc"]["anchors"]
    ink, white = principled("M_ink", (0.05, 0.06, 0.08), rough=0.6), principled("M_white", (0.92, 0.92, 0.9), rough=0.5)
    c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))

    def P(p, z_extra=0.0):
        x, y = p[0] * MM, p[1] * MM
        return (origin[0] + c * x - s * y, origin[1] + s * x + c * y, origin[2] + (p[2] + z_extra) * MM + dz * MM)
    lx, ly, lz = a["lid_label"]
    lab = META["labels"]
    if full:
        text_obj(lab["line1"], P((lx, ly + 11, lz - 0.25)), 0.0078, ink, rz)
        text_obj(lab["line2"], P((lx, ly - 1, lz - 0.25)), 0.0047, ink, rz)
        text_obj(lab["line3"], P((lx, ly - 12, lz - 0.25)), 0.0050, ink, rz)
    if full and side:
        film = principled("M_sidefilm", (0.88, 0.89, 0.87), rough=0.5)
        W2 = a["case_side"][1]
        P0 = P
        P = (lambda p, z_extra=0.0: P0(p, z_extra - dz)) if side_dz0 else P0
        add_box("side_label", (0.185, 0.0006, 0.066), P((0.0, W2 - 0.3, 150.0)), film, rz)
        for k, ln in enumerate(lab["side"]):
            t = text_obj(ln, P((0.0, W2 - 0.7, 169 - k * 12.5)), 0.0056 if k else 0.0088, ink, rz)
            t.rotation_euler = (math.radians(90), 0, math.radians(rz))
    for key, sym in (("terminal_pos", "+"), ("terminal_neg", "–")):
        tx, ty, tz = a[key]
        text_obj(sym, P((tx + (24 if key == "terminal_pos" else -24), ty + 2, tz + 0.05)), 0.016, white, rz)


# ------------------------------------------------------------------------------------------ world / lights / camera
def studio(floor_color=(0.45, 0.46, 0.48), strength=0.22, size=40.0):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexGradient")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, math.radians(-90), 0)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(coord.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], sky.inputs["Vector"])
    nt.links.new(sky.outputs["Fac"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = (0.30, 0.31, 0.33, 1)
    ramp.color_ramp.elements[1].color = (0.80, 0.82, 0.85, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    f = bpy.context.active_object
    f.name = "floor"
    f.data.materials.append(principled("M_floor", floor_color, rough=0.35))


def area(name, loc, target, size, energy, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.size, ld.energy, ld.color = size, energy, color
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    bpy.context.collection.objects.link(o)
    d = Vector(target) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


def studio_lights(scale=1.0, center=(0, 0, 0.1)):
    s = scale
    k = LIGHT_GAIN
    area("key", (-1.4 * s, -1.6 * s, 1.9 * s), center, 1.6 * s, 60 * k * s * s, (1.0, 0.96, 0.91))
    area("fill", (1.8 * s, -1.2 * s, 0.9 * s), center, 2.0 * s, 18 * k * s * s, (0.85, 0.90, 1.0))
    area("rim", (0.6 * s, 1.9 * s, 1.4 * s), center, 1.6 * s, 60 * k * s * s, (0.80, 0.88, 1.0))
    area("top", (0, 0, 2.6 * s), center, 2.5 * s, 25 * k * s * s)


def camera(loc, target, lens=50, name="cam"):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.01
    cam = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(cam)
    cam.location = loc
    tgt = bpy.data.objects.new(name + "_target", None)
    tgt.location = target
    bpy.context.collection.objects.link(tgt)
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    bpy.context.scene.camera = cam
    return cam, tgt


def setup_render(samples, res, engine="CYCLES"):
    sc = bpy.context.scene
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    if engine == "CYCLES":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        try:
            prefs.compute_device_type = "METAL"
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            sc.cycles.device = "GPU"
        except Exception as exc:
            print("GPU setup failed, CPU render:", exc)
        sc.cycles.samples = samples
        sc.cycles.use_adaptive_sampling = True
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 10
        sc.cycles.transmission_bounces = 10
        sc.cycles.volume_bounces = 2
        sc.cycles.transparent_max_bounces = 16
        sc.render.use_persistent_data = True
    else:
        sh = sc.display.shading
        sh.light = "STUDIO"
        sh.color_type = "MATERIAL"
        sh.show_shadows = True
        sh.show_cavity = True
        sh.cavity_type = "BOTH"
        sh.show_object_outline = True
        sc.display.render_aa = "8"


def anchors(cam, points: dict, tag):
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    out = {}
    for name, p in points.items():
        co = world_to_camera_view(sc, cam, Vector(p))
        out[name] = [co.x * sc.render.resolution_x, (1 - co.y) * sc.render.resolution_y, co.z]
    (OUT / f"anchors_{tag}.json").write_text(json.dumps(out, indent=1))


def A(asm, key, off=(0, 0, 0), origin=(0, 0, 0), rz=0.0):
    """CAD anchor (mm, assembly frame) + offset (mm) -> world (m), with assembly placement origin (m) / rz."""
    p = META[asm]["anchors"][key]
    x, y, z = p[0] + off[0], p[1] + off[1], p[2] + off[2]
    c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
    return (origin[0] + (c * x - s * y) * MM, origin[1] + (s * x + c * y) * MM, origin[2] + z * MM)


def vent_path():
    """Glowing arrowed path: cell headspace -> valve -> lid manifold -> flame-arrestor frit -> outlet."""
    lay = META["r1_monobloc"]["layout"]
    a = META["r1_monobloc"]["anchors"]
    x = lay["cell_x"][6]
    xo = a["vent_outlet"][0]
    y = 2.2
    H = 220.0
    pts = [(x, y, lay["z_bus1"] - 4), (x, 0.6, 203.0), (x, 0.6, 210.5), (x, y, 214.5), (x, y, 217.0), (xo - 2, y, 217.0),
           (xo, y, 219.0), (xo, y, H + 22)]
    m = glow("M_ventpath", (1.0, 0.45, 0.08), 10.0)
    cd = bpy.data.curves.new("ventpath", "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = 0.9 * MM
    cd.bevel_resolution = 2
    sp = cd.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p[0] * MM, p[1] * MM, p[2] * MM, 1)
    o = bpy.data.objects.new("ventpath", cd)
    o.data.materials.append(m)
    bpy.context.collection.objects.link(o)
    for p0, p1 in [(pts[2], pts[4]), ((x + 40, y, 217.0), (x + 70, y, 217.0)), (pts[6], pts[7])]:
        d = (Vector(p1) - Vector(p0)).normalized()
        bpy.ops.mesh.primitive_cone_add(radius1=1.6 * MM, depth=4 * MM, location=Vector(p1) * MM)
        cone = bpy.context.active_object
        cone.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        cone.data.materials.append(m)
    return pts


# ------------------------------------------------------------------------------------------ generic room props
def generic_rack(name, loc, rz=0.0, w=0.6, d=1.07, h=2.0):
    """Unbranded server rack: dark body, perforated door (procedural), a few status LEDs."""
    body = principled("M_rackbody", (0.025, 0.026, 0.03), metallic=0.4, rough=0.45)
    if "M_perf" not in bpy.data.materials:
        m = bpy.data.materials.new("M_perf")
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        br = nt.nodes.new("ShaderNodeTexBrick")
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
        br.inputs["Scale"].default_value = 160.0
        br.inputs["Mortar Size"].default_value = 0.012
        br.inputs["Color1"].default_value = (0.004, 0.004, 0.005, 1)
        br.inputs["Color2"].default_value = (0.006, 0.006, 0.007, 1)
        br.inputs["Mortar"].default_value = (0.07, 0.075, 0.08, 1)
        nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Metallic"].default_value = 0.5
        b.inputs["Roughness"].default_value = 0.4
        m.diffuse_color = (0.03, 0.03, 0.035, 1)
    perf = bpy.data.materials["M_perf"]
    c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))

    def W(x, y, z):
        return (loc[0] + c * x - s * y, loc[1] + s * x + c * y, loc[2] + z)
    add_box(name, (w, d, h), W(0, 0, h / 2), body, rz)
    add_box(name + "_door", (w - 0.04, 0.012, h - 0.12), W(0, -d / 2 - 0.006, h / 2), perf, rz)
    led = glow("M_led", (0.15, 1.0, 0.45), 18.0)
    for k in range(6):
        add_box(name + f"_led{k}", (0.012, 0.004, 0.004), W(-w / 2 + 0.08, -d / 2 - 0.014, 0.45 + k * 0.23), led, rz)


def raised_floor(size=(12, 10)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    f = bpy.context.active_object
    f.name = "raised_floor"
    f.scale = (size[0], size[1], 1)
    m = bpy.data.materials.new("M_tiles")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    br = nt.nodes.new("ShaderNodeTexBrick")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    br.offset = 0.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = META["scene"]["tile_m"]
    br.inputs["Row Height"].default_value = META["scene"]["tile_m"]
    br.inputs["Mortar Size"].default_value = 0.004
    br.inputs["Color1"].default_value = (0.30, 0.31, 0.32, 1)
    br.inputs["Color2"].default_value = (0.27, 0.28, 0.29, 1)
    br.inputs["Mortar"].default_value = (0.12, 0.12, 0.13, 1)
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.3
    f.data.materials.append(m)


def room_shell(dims=(9.0, 7.0, 3.2), center=(0, 1.0)):
    wall = principled("M_wall", (0.42, 0.43, 0.45), rough=0.8)
    L, D, H = dims
    cx, cy = center
    add_box("wall_back", (L, 0.1, H), (cx, cy + D / 2, H / 2), wall)
    add_box("wall_left", (0.1, D, H), (cx - L / 2, cy, H / 2), wall)
    add_box("wall_right", (0.1, D, H), (cx + L / 2, cy, H / 2), wall)
    add_box("ceiling", (L, D, 0.05), (cx, cy, H), principled("M_ceiling", (0.8, 0.8, 0.8), rough=0.9))
    lamp = glow("M_lamp", (1.0, 0.97, 0.92), 2.5)
    for i in range(-3, 4):
        for j in (-1, 1):
            add_box(f"lamp_{i}_{j}", (1.2, 0.08, 0.02), (cx + i * 1.3, cy + j * 1.6, H - 0.03), lamp)
    tray = principled("M_cabletray", (0.55, 0.56, 0.58), metallic=0.8, rough=0.4)
    for yy in (0.1, -2.6):        # overhead cable ladders above the rows
        for side in (-0.15, 0.15):
            add_box(f"ladder_{yy}_{side}", (L * 0.9, 0.006, 0.08), (cx, yy + side, 2.55), tray)
        for k in range(36):
            add_box(f"rung_{yy}_{k}", (0.02, 0.3, 0.01), (cx - L * 0.45 + k * L * 0.9 / 35, yy, 2.52), tray)
    for k in range(5):
        lv = Vector((cx - 3.5 + k * 1.75, cy, H - 0.05))
        ld = bpy.data.lights.new(f"ceil_{k}", "AREA")
        ld.size, ld.energy = 2.0, 30.0 * LIGHT_GAIN
        o = bpy.data.objects.new(f"ceil_{k}", ld)
        o.location = lv
        bpy.context.collection.objects.link(o)


def generic_ups_frame(loc, w=1.2, d=0.85, h=2.0):
    """Generic UPS power frame next to the battery row (illustrative, unbranded)."""
    add_box("ups_frame", (w, d, h), (loc[0], loc[1], h / 2), principled("M_ups", (0.70, 0.71, 0.70), rough=0.5))
    add_box("ups_screen", (0.22, 0.01, 0.14), (loc[0] - w * 0.25, loc[1] - d / 2 - 0.004, 1.45),
            glow("M_screen", (0.25, 0.55, 0.85), 2.5))
    for k in range(3):
        add_box(f"ups_seam{k}", (0.004, 0.01, h - 0.1), (loc[0] - w / 2 + (k + 1) * w / 4, loc[1] - d / 2 - 0.004, h / 2),
                principled("M_seam", (0.35, 0.36, 0.37), rough=0.6))


# ------------------------------------------------------------------------------------------ shots
def render_still(cam, pts, tag):
    anchors(cam, pts, tag)
    bpy.context.scene.render.filepath = str(OUTPATH)
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"RENDER {tag}: {time.time()-t0:.1f} s -> {OUTPATH}")


def shot_hero():
    import_variant("r1_monobloc", "full")
    lid_marks()
    studio()
    studio_lights(0.6)
    cam, _ = camera((-0.52, -0.72, 0.62), (0.0, 0.0, 0.085), lens=52)
    a = "r1_monobloc"
    pts = {k: A(a, k) for k in ("terminal_pos", "terminal_neg", "vent_outlet", "lid_label", "case_side", "manifold")}
    return cam, pts


def shot_exploded():
    import_variant("r1_monobloc", "exploded")
    lid_marks(dz=330.0, side_dz0=True)
    studio()
    studio_lights(0.8, (0, 0, 0.3))
    cam, _ = camera((-0.72, -1.28, 0.90), (-0.07, 0.0, 0.31), lens=45)
    a, lay = "r1_monobloc", META["r1_monobloc"]["layout"]
    pts = {"lid_label": A(a, "lid_label", (0, 0, 330)), "vent_outlet": A(a, "vent_outlet", (0, 0, 380)),
           "valve_cell5": A(a, "valve_cell5", (0, 0, 300)), "strap": A(a, "strap", (0, 0, 150)),
           "case_side": A(a, "case_side"), "partition": A(a, "partition", (0, 0, 60)),
           "fan": ((lay["cell_x"][0] - 150 - 70) * MM, -60 * MM, 250 * MM),
           "terminal_pos": A(a, "terminal_pos", (0, 0, 150 - 20))}
    return cam, pts


def shot_cutaway():
    import_variant("r1_monobloc", "cut")
    lid_marks(full=False)
    studio()
    studio_lights(0.6)
    vent_path()
    cam, _ = camera((0.24, -0.70, 0.50), (0.03, 0.0, 0.11), lens=46)
    a, lay = "r1_monobloc", META["r1_monobloc"]["layout"]
    x6 = lay["cell_x"][6]
    pts = {"electrolyte_cell5": A(a, "electrolyte_cell5", (0, 3, -10)), "plates_cell5": A(a, "plates_cell5", (0, 2, 30)),
           "separator_cell5": A(a, "separator_cell5", (30, 0, 60)), "valve": (x6 * MM, 0.0, 207 * MM),
           "frit": A(a, "frit"), "vent_out": A(a, "vent_outlet", (0, 0, 20)), "strap": A(a, "strap", (60, -2 * META["mech"]["tab_y_mm"], 0)),
           "headspace": A(a, "headspace", (30, 0, 0)), "manifold": A(a, "manifold", (20, 0, 0)),
           "terminal_neg": A(a, "terminal_neg", (0, 0, -15))}
    return cam, pts


def shot_module():
    import_variant("r1_module48", "full")
    a = "r1_module48"
    t = META["mech"]["m48_sheet_t"]
    for k, (org, rz) in enumerate(META["module_blocks"]):
        lid_marks(origin=(org[0] * MM, org[1] * MM, t * MM), rz=rz, side=False)
    studio()
    studio_lights(1.2, (0, 0, 0.15))
    cam, _ = camera((-1.10, -1.25, 0.95), (0.02, 0.02, 0.10), lens=45)
    pts = {k: A(a, k) for k in ("tray", "dcdc", "bms", "fuse", "block1", "block2_vent", "series_cable", "output", "label3")}
    return cam, pts


def cabinet_row(n=3, open_idx=1, x0=0.0, y0=0.0, with_racks=True, rack_n=2):
    W = META["r1_ups_cabinet"]["size"][0] * MM
    D = META["r1_ups_cabinet"]["size"][1] * MM
    closed = import_variant("r1_ups_cabinet", "closed", (x0, y0, 0), tag="cab0", smooth=False)
    opened = import_variant("r1_ups_cabinet", "open", (x0 + open_idx * W, y0, 0), tag="cabO", smooth=False) if open_idx is not None else []
    for k in range(1, n):
        if k == open_idx:
            continue
        instance(closed, (x0 + k * W, y0, 0), suffix=f"_{k}")
    if open_idx == 0:
        for o in closed:
            o.hide_render = True
    if with_racks:
        for k in range(rack_n):
            generic_rack(f"rackL{k}", (x0 - (k + 1) * 0.6, y0 + (1.07 - D) / 2, 0))
            generic_rack(f"rackR{k}", (x0 + (n + k) * W, y0 + (1.07 - D) / 2, 0))
    return W, D


def shot_row():
    W, D = cabinet_row(3, 1)
    raised_floor()
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.57, 0.6, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12
    add_box("backwall", (12, 0.1, 3.2), (0.6, 2.2, 1.6), principled("M_wall", (0.42, 0.43, 0.45), rough=0.8))
    area("key", (-1.6, -3.2, 2.9), (0.6, 0, 1.0), 3.0, 160 * LIGHT_GAIN, (1.0, 0.97, 0.92))
    area("fill", (3.2, -2.6, 1.6), (0.6, 0, 1.0), 3.0, 50 * LIGHT_GAIN, (0.86, 0.9, 1.0))
    area("top", (0.6, -0.6, 3.1), (0.6, 0, 0.0), 4.0, 80 * LIGHT_GAIN)
    cam, _ = camera((-0.75, -4.05, 1.62), (0.65, -0.1, 1.0), lens=32)
    a = "r1_ups_cabinet"
    o1 = (W, 0.0, 0.0)
    pts = {"louvre_high": A(a, "louvre_high", origin=(2 * W, 0, 0)), "louvre_low": A(a, "louvre_low", origin=(2 * W, 0, 0)),
           "roof_slots": A(a, "roof_slots", origin=(0, 0, 0)), "breaker": A(a, "breaker", origin=o1),
           "master_bms": A(a, "master_bms", origin=o1), "block_mid_terminal": A(a, "block_mid_terminal", origin=o1),
           "shelf4": A(a, "shelf4", origin=o1), "rack": (-0.6, -0.4 - 0.135, 1.5)}
    return cam, pts


def shot_room():
    """Generic equipment room: R1 battery row + generic UPS frame on one side of the aisle, server racks opposite."""
    raised_floor((14, 12))
    room_shell((9.0, 7.0, 3.2), (0.3, -0.9))
    W, D = cabinet_row(4, None, x0=0.0, y0=0.0, with_racks=False)
    generic_ups_frame((4 * W - 0.3 + 0.6, 0.0 - 0.025), w=1.2)
    for k in range(9):            # server-rack row across the aisle, fronts facing the battery row
        generic_rack(f"rowB{k}", (-2.6 + k * 0.6, -2.55, 0), rz=180)
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.52, 0.55, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.08
    area("aisle", (0.5, -1.3, 2.9), (0.5, -1.3, 0.0), 3.5, 110 * LIGHT_GAIN, (1.0, 0.97, 0.93))
    cam, _ = camera((-2.3, -1.40, 1.62), (1.5, -0.45, 0.98), lens=20)
    a = "r1_ups_cabinet"
    pts = {"string": A(a, "louvre_high", origin=(1 * W, 0, 0)), "louvre_low": A(a, "louvre_low", origin=(0, 0, 0)),
           "ups": (4 * W - 0.3 + 0.6 - 0.3, -0.45, 1.45), "racks": (-1.1, -2.55 + 0.55, 1.3), "roof": A(a, "roof_slots", origin=(2 * W, 0, 0))}
    return cam, pts


def shot_r0():
    import_variant("r0_test_cell", "exploded", smooth=True)
    studio(floor_color=(0.66, 0.67, 0.69))
    studio_lights(0.25, (0, 0, 0.06))
    cam, _ = camera((-0.28, -0.55, 0.33), (0.004, 0.0, 0.095), lens=60)
    a, ez = "r0_test_cell", META["r0_test_cell"]["explode_z"]
    pts = {"electrode_1": A(a, "electrode_1", (0, 0, ez["s1"])), "separator": A(a, "separator", (0, 0, ez["s2"])),
           "spring": A(a, "spring", (0, 0, ez["s6"])), "body": A(a, "body", (0, 0, ez["body"])),
           "top_plate": A(a, "top_plate", (0, 0, ez["t0"])), "bolt": A(a, "bolt", (0, 0, ez["bolt"]))}
    return cam, pts


def shot_turntable():
    import_variant("r1_monobloc", "full")
    lid_marks()
    studio()
    studio_lights(0.6)
    sc = bpy.context.scene
    frames = int(argv[argv.index("--frames") + 1]) if "--frames" in argv else 300
    cam, tgt = camera((0, 0, 0), (0.0, 0.0, 0.10), lens=50)
    piv = bpy.data.objects.new("pivot", None)
    piv.location = (0, 0, 0)
    bpy.context.collection.objects.link(piv)
    cam.parent = piv
    cam.location = Vector((-0.57, -0.78, 0.45))
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    piv.rotation_euler = (0, 0, 0)
    piv.keyframe_insert("rotation_euler", frame=1)
    piv.rotation_euler = (0, 0, math.radians(360))
    piv.keyframe_insert("rotation_euler", frame=frames + 1)
    setup_render(SAMPLES, RES)
    sc.frame_start, sc.frame_end = 1, frames
    d = OUT / "turntable"
    d.mkdir(exist_ok=True)
    for old in d.glob("f_*.png"):
        old.unlink()
    sc.render.filepath = str(d / "f_")
    sc.render.image_settings.file_format = "PNG"
    t0 = time.time()
    bpy.ops.render.render(animation=True)
    print(f"RENDER turntable {frames} frames: {time.time()-t0:.1f} s")


def shot_preview(asm, variant):
    """Fast Workbench preview of a CAD variant (for screenshots / visual checks)."""
    objs = import_variant(asm, variant, smooth=False)
    lo = Vector((1e9, 1e9, 1e9))
    hi = -lo
    for o in objs:
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    c = (lo + hi) / 2
    r = (hi - lo).length
    cam, _ = camera(c + Vector((-0.55, -0.85, 0.50)) * r * 1.55, c, lens=40)
    w = bpy.data.worlds.new("World")
    w.color = (0.80, 0.82, 0.85)
    bpy.context.scene.world = w
    setup_render(1, RES, engine="BLENDER_WORKBENCH")
    bpy.context.scene.render.filepath = str(OUTPATH)
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", asm, variant, "->", OUTPATH)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if SHOT == "preview":
        shot_preview(argv[1], argv[2])
        return
    if SHOT == "turntable":
        shot_turntable()
        return
    cam, pts = {"hero": shot_hero, "exploded": shot_exploded, "cutaway": shot_cutaway, "module": shot_module,
                "row": shot_row, "room": shot_room, "r0": shot_r0}[SHOT]()
    if "--blend" in argv:
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"{SHOT}.blend"))
    setup_render(SAMPLES, RES)
    render_still(cam, pts, SHOT)


main()
