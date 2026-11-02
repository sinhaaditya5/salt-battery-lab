"""Add labelled callouts (leader lines) to the Blender renders, using the projected 3D anchors.

Pattern reused from PARC-Delta prototype/renders/annotate.py. Every number in a callout is generated from
params/ (product_params, design, mech_params) - nothing is typed in by hand.

  python renders/annotate.py [shot ...]     -> renders/out/<shot>_annotated.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
from params.design import cabinet, module48, monobloc  # noqa: E402
from params.mech_params import (CAB_SHELF_PITCH_MM, CAB_TERMINAL_CLEAR_MM, M48_TRAY_CAD_MM,  # noqa: E402
                                R0_FIXTURE, monobloc_layout)
from params.product_params import BMS, CABINET, MAT, MODULE48, MONOBLOC, R0  # noqa: E402

OUT = HERE / "out"
FONT_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_R = "/System/Library/Fonts/Supplemental/Arial.ttf"
FOOTER = ("CONCEPT RENDER - not a photograph of hardware  |  geometry from the build123d CAD driven by params/  |  "
          "Blender 5.0 Cycles  |  2026-11-02")


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def texts():
    d, lay = monobloc(), monobloc_layout()
    es = d["electrode"]
    mb = MONOBLOC
    E = d["energy_Wh"] / 1000
    M = MAT["electrolyte_molarity"].value
    vent = mb["vent_valve_open_kPa"].value
    m48, cab = module48(), cabinet()
    nblk = CABINET["shelves"] * CABINET["monoblocs_per_shelf"]
    Lt, Wt, Ht = M48_TRAY_CAD_MM
    return {
        "hero": ("R1 12 V aqueous sodium-ion monobloc",
                 f"{d['n_cells']} cells in series  ·  {d['v_nom']:.1f} V nom  ·  {E:.2f} kWh [TARGET]  ·  {d['mass_kg']:.1f} kg [CALC]  ·  "
                 f"water-based electrolyte ({M} M Na2SO4)",
                 {"lid_label": f"12 V block, {E:.2f} kWh [TARGET]",
                  "terminal_pos": f"M8 female terminal (+), {mb['terminal_spacing_mm']:.0f} mm pitch",
                  "terminal_neg": "M8 female terminal (–)",
                  "vent_outlet": f"one-way vent + flame arrestor (opens {vent:.0f} kPa [TARGET])",
                  "manifold": f"common vent manifold over {d['n_cells']} per-cell valves",
                  "case_side": f"PP-GF V-0 case [TARGET], {mb['length_mm']:.0f} × {mb['width_mm']:.0f} × {mb['height_mm']:.0f} mm (VRLA size)"}),
        "exploded": ("R1 monobloc — exploded view",
                     f"plates {d['plate_w_mm']:.0f} × {d['plate_h_mm']:.0f} mm  ·  {d['repeats_per_cell']} repeat units per cell  ·  "
                     f"stack {lay['stack_t']:.1f} mm in a {d['compartment_mm']:.1f} mm compartment  ·  all values from params/",
                     {"lid_label": "PP-GF lid with label recess + terminal wells",
                      "vent_outlet": "vent manifold cover + porous-PP flame arrestor",
                      "valve_cell5": f"{d['n_cells']} × one-way EPDM valve (opens {vent:.0f} kPa [TARGET])",
                      "strap": "316L plate-group straps + intercell connectors",
                      "terminal_pos": "M8 terminal posts on end-cell links",
                      "fan": f"repeat unit {es['repeat_thick_um']/1000:.2f} mm: cathode | separator | anode | separator",
                      "case_side": f"PP-GF case: {d['n_cells']} compartments, {mb['partition_mm']} mm partitions"}),
        "cutaway": ("Inside the R1 monobloc — cutaway",
                    f"front wall and front half of the lid removed (cells 3–10)  ·  orange line = gas vent path (illustrative)  ·  "
                    f"free-electrolyte level from design.monobloc()",
                    {"electrolyte_cell5": f"water-based electrolyte, {M} M Na2SO4 (free reservoir; pores saturated)",
                     "plates_cell5": "Na-birnessite cathode / NaTi2(PO4)3-C anode plates",
                     "separator_cell5": f"separator {MAT['separator_thickness_um'].value:.0f} µm, cathode {es['cathode_thick_um']:.0f} µm/side",
                     "valve": f"one-way valve per cell (opens {vent:.0f} kPa [TARGET])",
                     "frit": "porous-PP flame arrestor",
                     "vent_out": "single vent outlet",
                     "headspace": f"{mb['headspace_mm']:.0f} mm gas headspace + straps",
                     "manifold": "common vent manifold in the lid",
                     "terminal_neg": "M8 terminal post on end-cell link"}),
        "module": ("48 V telecom module — 4 × R1 monobloc",
                   f"{m48['energy_Wh']/1000:.2f} kWh after DC/DC [CALC]  ·  {m48['mass_kg']:.0f} kg [CALC]  ·  "
                   f"tray {Lt:.0f} × {Wt:.0f} × {Ht:.0f} mm (MODULE48 tray_mm too small for 4 blocks - see README)",
                   {"block1": f"{MODULE48['monoblocs']} × 12 V monobloc in series ({MODULE48['monoblocs'] * d['v_nom']:.1f} V nom)",
                    "dcdc": f"bidirectional DC/DC to the 48 V bus (eff. {MODULE48['dcdc_efficiency'].value:.2f} [ASSUMPTION])",
                    "bms": f"module BMS: {BMS['series_groups_per_board']}-ch V sense, NTC, shunt, H2 + pressure inputs",
                    "fuse": "main fuse",
                    "series_cable": "25 mm² series links",
                    "output": f"{MODULE48['nominal_V']:.0f} V DC output",
                    "tray": "galvanised steel tray with hold-down bars",
                    "block2_vent": "one vent outlet per block"}),
        "row": ("R1 UPS battery cabinet in a rack row",
                f"{CABINET['width_mm']:.0f} × {CABINET['depth_mm']:.0f} × {CABINET['height_mm']:.0f} mm  ·  {nblk} × 12 V monobloc  ·  "
                f"{cab['energy_kWh']:.1f} kWh [CALC]  ·  {cab['mass_kg']:.0f} kg [CALC]",
                {"louvre_high": "H2 outlet louvres (high)",
                 "louvre_low": "air inlet louvres (low)",
                 "roof_slots": "roof vent slots over rear plenum",
                 "breaker": "DC string breaker",
                 "master_bms": f"master BMS ({BMS['comms'][0]} / {BMS['comms'][1].split()[0]})",
                 "block_mid_terminal": f"{CABINET['shelves']} shelves × {CABINET['monoblocs_per_shelf']} blocks, {cab['string_V']:.0f} V string [CALC]",
                 "shelf4": f"shelf pitch {CAB_SHELF_PITCH_MM:.1f} mm: only {CAB_TERMINAL_CLEAR_MM:.0f} mm above lids",
                 "rack": "generic IT racks (illustrative)"}),
        "room": ("Installed concept — UPS battery row in an equipment room",
                 f"generic, unbranded scene  ·  4 cabinets × {nblk} blocks  ·  water-based {M} M Na2SO4 electrolyte  ·  "
                 "hydrogen handled by cabinet ventilation",
                 {"string": f"R1 UPS battery cabinets, {cab['string_V']:.0f} V string each [CALC]",
                  "louvre_low": "natural ventilation: low inlet, high outlet",
                  "ups": "UPS power frame (generic)",
                  "racks": "IT racks (generic, illustrative)",
                  "roof": "roof vent slots"}),
        "r0": ("R0 reference cell — Shan et al. 2019 symmetric aqueous cell",
               f"two Ø{R0['electrode_diameter'].value:.0f} mm electrodes, {R0['electrolyte_volume'].value:.0f} µL "
               f"{R0['electrolyte_molarity'].value:.0f} M Na2SO4  ·  {R0_FIXTURE['label']}, not the MTI EQ-STC drawing",
               {"electrode_1": f"Ø{R0['electrode_diameter'].value:.0f} mm electrode: {R0['active_mass_per_electrode'].value:.2f} mg "
                               f"Na0.27MnO2 + {R0['carbon_black_per_electrode'].value:.2f} mg CB on carbon paper [LIT]",
                "separator": "cellulose filter-paper separator [LIT]",
                "spring": "compression spring + stainless spacer [LIT; dims ASSUMPTION]",
                "body": "PTFE insulating body (illustrative)",
                "top_plate": "stainless end plates (illustrative)",
                "bolt": "insulated clamp bolts (illustrative)"}),
    }


def annotate(view: str, title: str, subtitle: str, labels: dict) -> Path:
    img = Image.open(OUT / f"{view}.png").convert("RGBA")
    W, H = img.size
    anchors = json.loads((OUT / f"anchors_{view}.json").read_text())
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    fl = font(FONT_B, int(H * 0.0185))
    ft, fs = font(FONT_B, int(H * 0.036)), font(FONT_R, int(H * 0.0195))
    band = int(H * 0.14)
    for y in range(band):
        a = int(205 * (1 - y / band) ** 0.8)
        d.line([(0, y), (W, y)], fill=(10, 14, 24, a))
    d.text((int(W * 0.025), int(H * 0.028)), title, font=ft, fill=(255, 255, 255, 255))
    d.text((int(W * 0.025), int(H * 0.080)), subtitle, font=fs, fill=(200, 210, 228, 255))
    pts = [(labels[n], x, y) for n, (x, y, z) in anchors.items() if n in labels and 0 < x < W and 0 < y < H and z > 0]
    left = sorted([p for p in pts if p[1] < W * 0.5], key=lambda p: p[2])
    right = sorted([p for p in pts if p[1] >= W * 0.5], key=lambda p: p[2])
    pad, box_h = int(H * 0.010), int(H * 0.038)
    for side, group in (("L", left), ("R", right)):
        if not group:
            continue
        y_lo, y_hi = H * 0.18, H * 0.92
        slots = [min(max(ay, y_lo), y_hi) for _, _, ay in group]
        gap = box_h + pad
        for i in range(1, len(slots)):
            slots[i] = max(slots[i], slots[i - 1] + gap)
        overflow = slots[-1] - y_hi
        if overflow > 0:
            slots = [s - overflow for s in slots]
            for i in range(len(slots) - 2, -1, -1):
                slots[i] = min(slots[i], slots[i + 1] - gap)
        for (name, ax, ay), sy in zip(group, slots):
            tw = d.textlength(name, font=fl)
            bw = tw + 2 * pad
            bx = int(W * 0.018) if side == "L" else int(W * 0.982 - bw)
            by = int(sy - box_h / 2)
            lx = bx + bw if side == "L" else bx
            d.line([(lx, sy), (ax, ay)], fill=(255, 196, 120, 240), width=max(2, H // 540))
            r = max(5, H // 200)
            d.ellipse([ax - r, ay - r, ax + r, ay + r], fill=(255, 150, 60, 255), outline=(255, 255, 255, 255), width=2)
            d.rounded_rectangle([bx, by, bx + bw, by + box_h], radius=int(box_h * 0.25),
                                fill=(12, 18, 32, 220), outline=(255, 170, 90, 255), width=2)
            d.text((bx + pad, by + (box_h - fl.size) / 2 - 2), name, font=fl, fill=(255, 255, 255, 255))
    ff = font(FONT_R, int(H * 0.015))
    d.rectangle([0, int(H * 0.962), W, H], fill=(10, 14, 24, 170))
    d.text((int(W * 0.025), int(H * 0.968)), FOOTER, font=ff, fill=(190, 198, 212, 255))
    out = OUT / f"{view}_annotated.png"
    Image.alpha_composite(img, overlay).convert("RGB").save(out)
    return out


if __name__ == "__main__":
    T = texts()
    views = sys.argv[1:] or [v for v in T if (OUT / f"{v}.png").exists()]
    for v in views:
        print(annotate(v, *T[v]))
