"""Mechanical parameters that params/product_params.py and params/design.py do not define.

Used by cad/make_cad.py, drawings/make_drawings.py, renders/blender_scene.py and tests/test_cad_params.py.
Every number carries a tag in its comment (ASSUMPTION | TARGET | LIT | CALC | CHOICE) and a one-line
justification. Nothing here is measured. Values that depend on params/product_params.py are derived
from it (CALC) rather than copied.

Coordinate conventions (mm):
  monobloc  origin = centre of the footprint at the base; +X along length, +Y along width, +Z up
  module48  origin = centre of the tray footprint at floor level; +X = tray depth (front at -X)
  cabinet   origin = centre of the footprint at floor level; +X = width, +Y = depth (door at -Y), +Z up
"""
from __future__ import annotations

import math

from params.product_params import CABINET, MAT, MODULE48, MONOBLOC, R0
from params.design import monobloc

# ------------------------------------------------------------------------------------------------
# Material densities used for part-list mass estimates (g/cm3)
# ------------------------------------------------------------------------------------------------
DENSITY = {
    "PP-GF20": MONOBLOC["case_density_g_cm3"],   # from product_params (MONOBLOC case_density_g_cm3)
    "PP": 0.90,            # LIT: polypropylene handbook value 0.90-0.91
    "PP frit (porous)": 0.45,  # ASSUMPTION: sintered PP frit ~50 % porosity (0.40-0.55)
    "EPDM": 1.15,          # ASSUMPTION: filled EPDM compound 1.0-1.3
    "316L stainless": MAT["cc_density"].value,   # from product_params (LIT 8.0)
    "304 stainless": 7.93, # LIT: handbook
    "spring steel (316)": 8.0,  # LIT: stainless spring wire
    "brass (lead-free, Sn-plated)": 8.5,   # LIT: CW511L-type brass 8.4-8.6
    "PTFE": 2.17,          # LIT: handbook 2.14-2.20
    "PEEK": 1.31,          # LIT: handbook 1.30-1.32
    "galvanised steel": 7.85,  # LIT: carbon steel
    "powder-coated steel": 7.85,  # LIT: carbon steel (coating mass ignored)
    "aluminium 6063": 2.70,  # LIT: handbook
    "copper (insulated cable)": 3.6,   # ASSUMPTION: 25 mm2 Cu + PVC/XLPE insulation, averaged over cable section
    "label film": 1.0,     # ASSUMPTION: PET/paper label, mass negligible
    "electronics (potted avg)": 1.6,   # ASSUMPTION: enclosure + PCB + components averaged over box volume (1.2-2.0)
    "electrolyte 0.5 M Na2SO4": MAT["electrolyte_density"].value,  # from product_params (ASSUMPTION 1.06)
    "electrolyte 1 M Na2SO4": 1.12,   # ASSUMPTION: 1 mol/L Na2SO4(aq) ~1.11-1.13 g/cm3 (R0 only)
    "carbon paper": 0.44,  # ASSUMPTION: Toray TGP-H bulk density ~0.44-0.45 g/cm3
    "cellulose filter paper": 0.50,  # ASSUMPTION: Whatman-type filter paper apparent density 0.45-0.55
    "R0 coating": 1.9,     # ASSUMPTION: porous birnessite + carbon black coating, apparent density (1.5-2.3)
}

# ------------------------------------------------------------------------------------------------
# (a) R0 — generic split test-cell fixture (illustrative). Shan 2019 names an MTI EQ-STC split cell with
#     a stainless plate + compression spring; no drawing is published, so EVERY fixture dimension is ASSUMPTION.
# ------------------------------------------------------------------------------------------------
R0_FIXTURE = dict(
    label="generic split-cell fixture (illustrative)",
    plate_od_mm=50.0,        # ASSUMPTION: stainless end-plate diameter; bench split cells are ~40-60 mm across
    plate_t_mm=8.0,          # ASSUMPTION: stiff enough for 3-bolt clamping without dishing
    boss_od_mm=19.6,         # ASSUMPTION: plate boss / piston sliding fit in the 20 mm PTFE bore
    boss_h_mm=4.0,           # ASSUMPTION: boss engagement into the bore
    body_od_mm=50.0,         # ASSUMPTION: PTFE insulating body flush with the plates
    body_bore_mm=20.0,       # ASSUMPTION: > 19 mm separator so the separator lies flat
    bolt_n=3,                # ASSUMPTION: 3 clamp bolts (common split-cell layout)
    bolt_d_mm=5.0,           # ASSUMPTION: M5 clamp bolts
    bolt_pcd_mm=38.0,        # ASSUMPTION: bolt circle between bore and rim
    bolt_len_mm=40.0,        # ASSUMPTION: through both plates + nut
    sleeve_od_mm=7.5,        # ASSUMPTION: PEEK insulating sleeve so the bolts do not short the plates
    spacer_t_mm=1.0,         # ASSUMPTION: "stainless plate" named in Shan 2019 Methods; thickness not given
    spring_od_mm=15.0,       # ASSUMPTION: "compression spring" named in Shan 2019; dimensions not given
    spring_wire_mm=1.2,      # ASSUMPTION
    spring_len_mm=6.0,       # ASSUMPTION: compressed (installed) length
    spring_turns=4.0,        # ASSUMPTION
    piston_h_mm=5.0,         # ASSUMPTION: stainless piston between spring and top-plate boss
    carbon_paper_t_mm=0.19,  # ASSUMPTION: Toray TGP-H-060 thickness; paper gives no grade (range 0.11-0.37)
    separator_d_mm=19.0,     # ASSUMPTION: cellulose filter-paper disc (Whatman, grade not stated), > 15 mm electrodes
    separator_t_mm=0.18,     # ASSUMPTION: Whatman grade-1-like thickness (range 0.15-0.25)
    lead_w_mm=6.0, lead_l_mm=18.0, lead_t_mm=1.0,   # ASSUMPTION: connection tabs on each end plate
)
_r0_area_cm2 = math.pi * (R0["electrode_diameter"].value / 20.0) ** 2
# CALC: R0 coating thickness from published masses (5.00 mg birnessite + 1.25 mg carbon black, 4:1, on 1.5 cm disc),
#       using MAT cathode density and porosity assumptions (binder not stated in Shan 2019 -> ignored)
R0_COATING_UM = ((R0["active_mass_per_electrode"].value / MAT["cathode_density"].value
                  + R0["carbon_black_per_electrode"].value / 1.9) / _r0_area_cm2
                 / (1 - MAT["electrode_porosity"].value) * 10.0)
# CALC: stack height inside the bore -> PTFE body height so the top boss just closes on the piston
R0_STACK_H_MM = (2 * R0_FIXTURE["carbon_paper_t_mm"] + 2 * R0_COATING_UM / 1000 + R0_FIXTURE["separator_t_mm"]
                 + R0_FIXTURE["spacer_t_mm"] + R0_FIXTURE["spring_len_mm"] + R0_FIXTURE["piston_h_mm"])
R0_FIXTURE["body_h_mm"] = round(R0_STACK_H_MM + 2 * R0_FIXTURE["boss_h_mm"], 2)   # CALC

# ------------------------------------------------------------------------------------------------
# (b) R1 12 V monobloc — details below the MONOBLOC envelope (case, plates, straps, terminals, vent)
# ------------------------------------------------------------------------------------------------
VENT_ARRANGEMENT = (  # CHOICE (documented): each cell is its own sealed gas space, so each needs its own one-way valve
    "per-cell one-way EPDM Bunsen valve (x10) in a lid well, venting into a common lid manifold channel "
    "that exits through a single porous-PP flame-arrestor frit and outlet hole"
)
# Why: VRLA practice; partitions are sealed to the lid, so a single common valve would let cells exchange gas and
#      electrolyte vapour; one arrestor at one outlet is cheaper than ten and gives one point to duct H2 away.
MB_MECH = dict(
    case_fillet_mm=4.0,       # ASSUMPTION: vertical-edge radius for a moulded PP-GF case
    tab_w_mm=16.0,            # ASSUMPTION: electrode tab width (uncoated 316L foil, welded bundle)
    tab_h_mm=10.0,            # ASSUMPTION: tab height above the plate top
    tab_y_mm=45.0,            # ASSUMPTION: tab centre offset from the plate centreline (+/-)
    bus_h_mm=6.0,             # ASSUMPTION: plate-group strap (316L) height; 16x6 mm section ~96 mm2 for a ~34 A (1C) cell
    sep_overhang_mm=2.0,      # ASSUMPTION: separator overhang beyond the electrode edge on every side
    term_y_inset_mm=24.0,     # ASSUMPTION: terminal centre inset from the long edge (typical VRLA lid layout)
    term_post_d_mm=16.0,      # ASSUMPTION: terminal post / brass insert outer diameter
    term_bore_d_mm=6.8,       # LIT: ISO M8x1.25 tap-drill diameter (female M8 insert, MONOBLOC terminal)
    term_bore_depth_mm=12.0,  # ASSUMPTION: thread engagement depth for an M8 bolt
    term_top_below_lid_mm=1.0,  # ASSUMPTION: insert face 1 mm below the lid top so the envelope stays 220 mm
    term_well_d_mm=28.0,      # ASSUMPTION: recessed lid well around each terminal (fits an M8 ring lug)
    term_well_depth_mm=3.0,   # ASSUMPTION
    term_link_w_mm=12.0,      # ASSUMPTION: end-cell-to-terminal link width (316L)
    collar_od_mm=24.0,        # ASSUMPTION: red/black polarity collar in the terminal well
    collar_t_mm=1.5,          # ASSUMPTION
    valve_well_od_mm=16.0,    # ASSUMPTION: moulded valve well under the lid (one per cell)
    valve_well_id_mm=11.0,    # ASSUMPTION
    valve_well_depth_mm=12.0, # ASSUMPTION: depth below the lid underside (headspace is MONOBLOC headspace_mm)
    valve_nipple_od_mm=6.0,   # ASSUMPTION: PP nipple carrying the EPDM Bunsen cap
    valve_nipple_id_mm=2.5,   # ASSUMPTION
    valve_cap_od_mm=9.0,      # ASSUMPTION: EPDM cap; opening pressure is MONOBLOC vent_valve_open_kPa [TARGET]
    valve_cap_h_mm=6.5,       # ASSUMPTION
    manifold_w_mm=12.0,       # ASSUMPTION: common vent channel moulded in the lid top
    manifold_depth_mm=4.0,    # ASSUMPTION: 2 mm gas channel + 2 mm cover strip
    cover_t_mm=2.0,           # ASSUMPTION: welded PP cover strip, flush with the lid top
    frit_len_mm=7.0,          # ASSUMPTION: porous PP flame-arrestor block at the channel end (MONOBLOC flame_arrestor)
    outlet_d_mm=3.0,          # ASSUMPTION: single vent outlet hole above the frit
    label_l_mm=190.0,         # ASSUMPTION: lid label recess length
    label_w_mm=54.0,          # ASSUMPTION: lid label recess width
    label_depth_mm=0.6,       # ASSUMPTION: recess depth; label film 0.3 mm
    label_y_mm=45.0,          # ASSUMPTION: label centre offset toward the rear (+Y) half of the lid
)


def monobloc_layout():
    """CALC: derived positions inside the monobloc (all from MONOBLOC, design.monobloc() and MB_MECH)."""
    mb, d = MONOBLOC, monobloc()
    es = d["electrode"]
    n, comp = d["n_cells"], d["compartment_mm"]
    pitch = comp + mb["partition_mm"]
    x0 = -mb["length_mm"] / 2 + mb["wall_mm"] + comp / 2
    cell_x = [x0 + i * pitch for i in range(n)]
    stack_t = d["repeats_per_cell"] * es["repeat_thick_um"] / 1000.0
    z_plate0 = mb["base_mm"] + mb["plate_margin_mm"]
    z_plate1 = z_plate0 + d["plate_h_mm"]
    z_lid0 = mb["height_mm"] - mb["lid_mm"]
    z_tab1 = z_plate1 + MB_MECH["tab_h_mm"]
    z_bus1 = z_tab1 + MB_MECH["bus_h_mm"]
    term_y = -(mb["width_mm"] / 2 - MB_MECH["term_y_inset_mm"])
    term_x = [-mb["terminal_spacing_mm"] / 2, mb["terminal_spacing_mm"] / 2]
    # free electrolyte pooled around the stack: design.monobloc() free_electrolyte_kg spread over the 10 cells
    w_in = mb["width_mm"] - 2 * mb["wall_mm"]
    sep_w = d["plate_w_mm"] + 2 * MB_MECH["sep_overhang_mm"]
    z_sep0 = z_plate0 - MB_MECH["sep_overhang_mm"]
    v_free_mm3 = d["free_electrolyte_kg"] / n / MAT["electrolyte_density"].value * 1e6
    a_full, a_ann = comp * w_in, comp * w_in - stack_t * sep_w
    v_below = a_full * (z_sep0 - mb["base_mm"])
    z_fill = (mb["base_mm"] + v_free_mm3 / a_full) if v_free_mm3 <= v_below else z_sep0 + (v_free_mm3 - v_below) / a_ann
    return dict(n=n, comp=comp, pitch=pitch, cell_x=cell_x, stack_t=stack_t, z_plate0=z_plate0, z_plate1=z_plate1,
                z_lid0=z_lid0, z_tab1=z_tab1, z_bus1=z_bus1, term_y=term_y, term_x=term_x, w_in=w_in, sep_w=sep_w,
                z_sep0=z_sep0, z_fill=z_fill, v_free_mm3=v_free_mm3)


# ------------------------------------------------------------------------------------------------
# (c) 48 V telecom module.
# FINDING: MODULE48["tray_mm"] = (600, 450, 280) cannot hold 4 monoblocs of 330 x 173 x 220 mm in any upright
# arrangement (2x2 needs >= 660 x 346 mm; 4-in-line needs 692 x 330 mm; 600 x 450 holds at most 3).
# The CAD keeps the 450 mm width (fits between 19-inch rails) and the 280 mm height, and derives the length
# from a 2 x 2 block layout. Params owner should update MODULE48["tray_mm"] (module48() volume_L / Wh_per_L
# use it); the tray needs an 800 mm-deep cabinet, not a 600 mm one.
# ------------------------------------------------------------------------------------------------
M48_MECH = dict(
    sheet_t_mm=2.0,           # ASSUMPTION: galvanised-steel tray sheet
    block_gap_mm=6.0,         # ASSUMPTION: gap between monoblocs (assembly + air)
    wall_clear_mm=3.0,        # ASSUMPTION: clearance block-to-tray wall
    side_lip_h_mm=60.0,       # ASSUMPTION: low side/rear lips; blocks restrained by a top hold-down bar
    holddown_w_mm=30.0, holddown_t_mm=4.0,   # ASSUMPTION: steel hold-down bars across the block lids
    bms_box_mm=(180.0, 80.0, 50.0),     # ASSUMPTION: module BMS enclosure (L x W x H); board from pcb/ (BMS dict)
    dcdc_box_mm=(260.0, 80.0, 200.0),   # ASSUMPTION: bidirectional DC/DC box (MODULE48 dcdc_needed=True)
    fuse_box_mm=(90.0, 60.0, 70.0),     # ASSUMPTION: main fuse holder
    cable_d_mm=10.0,          # ASSUMPTION: 25 mm2 insulated power cable outer diameter
    sense_d_mm=3.0,           # ASSUMPTION: BMS sense lead outer diameter
    handle_w_mm=120.0,        # ASSUMPTION: front pull handles
)
_bw = 2 * MONOBLOC["width_mm"] + M48_MECH["block_gap_mm"] + 2 * M48_MECH["sheet_t_mm"] + 2 * M48_MECH["wall_clear_mm"]
M48_TRAY_CAD_MM = (
    2 * MONOBLOC["length_mm"] + M48_MECH["block_gap_mm"] + 2 * M48_MECH["sheet_t_mm"] + 2 * M48_MECH["wall_clear_mm"],  # CALC length
    MODULE48["tray_mm"][1],   # from product_params (width, fits between 19-inch rails)
    MODULE48["tray_mm"][2],   # from product_params (height)
)
M48_BAY_W_MM = M48_TRAY_CAD_MM[1] - _bw     # CALC: side electronics bay width left after the 2 x 2 blocks


def tray_fits_4_monoblocs(tray_mm=MODULE48["tray_mm"]):
    """True if 4 upright monoblocs fit the tray footprint in a 2x2 or 1x4 layout (no clearances)."""
    L, W, _ = tray_mm
    l, w = MONOBLOC["length_mm"], MONOBLOC["width_mm"]
    layouts = [(2 * l, 2 * w), (2 * w, 2 * l), (4 * w, l), (l, 4 * w), (4 * l, w), (w, 4 * l)]
    return any(a <= L and b <= W for a, b in layouts)


# ------------------------------------------------------------------------------------------------
# (d) UPS cabinet (CABINET envelope from product_params)
# ------------------------------------------------------------------------------------------------
CAB_MECH = dict(
    post_mm=30.0,             # ASSUMPTION: 30 x 30 mm corner tubes; 40 mm posts clashed with the 3-wide block row (CAD check)
    panel_t_mm=1.5,           # ASSUMPTION: side / rear / roof sheet
    plinth_h_mm=60.0,         # ASSUMPTION: base frame + bottom air inlet
    roof_h_mm=40.0,           # ASSUMPTION: roof frame with top air outlet slots
    door_t_mm=20.0,           # ASSUMPTION: front door incl. stiffeners (inside the 800 mm depth)
    shelf_t_mm=2.5,           # ASSUMPTION: steel shelf sheet
    shelf_lip_mm=25.0,        # ASSUMPTION: folded shelf edge / support angle
    block_gap_mm=6.0,         # ASSUMPTION: gap between monoblocs on a shelf
    front_clear_mm=35.0,      # ASSUMPTION: door inner face to front block row; clears the 30 mm front posts
    louvre_slot_mm=(140.0, 10.0),  # ASSUMPTION: door louvre slot (w x h)
    louvre_rows=6,            # ASSUMPTION: rows of louvres at door top and bottom (H2 natural ventilation: in low, out high)
    roof_slots=8,             # ASSUMPTION: roof outlet slots
    bms_box_mm=(150.0, 200.0, 120.0),     # ASSUMPTION: master BMS enclosure (W x D x H)
    breaker_mm=(105.0, 100.0, 165.0),     # ASSUMPTION: DC string breaker body (W x D x H), MCCB-style
    duct_mm=60.0,             # ASSUMPTION: vertical cable duct in the free slot of shelves 1-7
    hinge_side=-1,            # CHOICE: door hinged on the -X side
    row_count=3,              # ASSUMPTION: cabinets in the rendered rack row
)
CAB_SHELF_PITCH_MM = (CABINET["height_mm"] - CAB_MECH["plinth_h_mm"] - CAB_MECH["roof_h_mm"]) / CABINET["shelves"]  # CALC
CAB_TERMINAL_CLEAR_MM = CAB_SHELF_PITCH_MM - CAB_MECH["shelf_t_mm"] - MONOBLOC["height_mm"]  # CALC (flagged in README)

# ------------------------------------------------------------------------------------------------
# Render / scene inputs
# ------------------------------------------------------------------------------------------------
SCENE = dict(
    room_mm=(9000.0, 7000.0, 3200.0),   # ASSUMPTION: generic equipment-room size for the installed render
    raised_floor_tile_mm=600.0,         # LIT: common raised-floor tile size
    turntable_seconds=25.0,             # TARGET: 20-30 s turntable (brief)
    turntable_fps=24,                   # TARGET: brief
)

if __name__ == "__main__":
    import json
    lay = monobloc_layout()
    print("R0 coating um", round(R0_COATING_UM, 2), "body_h", R0_FIXTURE["body_h_mm"])
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in lay.items() if k != "cell_x"})
    print("cell_x", [round(x, 3) for x in lay["cell_x"]])
    print("tray CAD", M48_TRAY_CAD_MM, "bay", round(M48_BAY_W_MM, 1), "params tray fits 4:", tray_fits_4_monoblocs())
    print("cabinet shelf pitch", CAB_SHELF_PITCH_MM, "terminal clearance", CAB_TERMINAL_CLEAR_MM)
