"""Params-consistency checks for the CAD, drawings and part lists (CONCEPT design).

CAD dimensions == params == drawings:
  * exported STEP bounding boxes equal MONOBLOC / CABINET envelopes
  * R0 electrodes are R0["electrode_diameter"] (15 mm) - from the exported STEP and from the model function
  * drawing DXFs carry the overall dimension values and the concept/no-fabrication title-block text
  * no hard clashes between monoblocs and the cabinet / module structure
  * MODULE48["tray_mm"] cannot hold 4 monoblocs (documented params conflict -> strict xfail)

Run:  pytest tests/test_cad_params.py -q      (needs: python cad/make_cad.py && python drawings/make_drawings.py)
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(LAB / "cad"))

from params.design import monobloc  # noqa: E402
from params.mech_params import M48_TRAY_CAD_MM, monobloc_layout, tray_fits_4_monoblocs  # noqa: E402
from params.product_params import CABINET, MODULE48, MONOBLOC, R0  # noqa: E402

CAD_OUT = LAB / "cad" / "out"
DWG_OUT = LAB / "drawings" / "out"


def _size(shape):
    bb = shape.bounding_box()
    return bb.size.X, bb.size.Y, bb.size.Z


def _walk(shape):
    yield shape
    for ch in getattr(shape, "children", ()) or ():
        yield from _walk(ch)


@pytest.fixture(scope="module")
def step():
    from build123d import import_step
    out = {}
    for n in ("r0_test_cell", "r1_monobloc", "r1_module48", "r1_ups_cabinet"):
        p = CAD_OUT / f"{n}.step"
        assert p.exists(), f"missing {p} - run python cad/make_cad.py"
        out[n] = import_step(str(p))
    return out


@pytest.fixture(scope="module")
def mk():
    import make_cad
    return make_cad


# ------------------------------------------------------------------------------------------- envelopes
def test_monobloc_step_bbox_equals_params(step):
    sx, sy, sz = _size(step["r1_monobloc"])
    assert sx == pytest.approx(MONOBLOC["length_mm"], abs=0.5)
    assert sy == pytest.approx(MONOBLOC["width_mm"], abs=0.5)
    assert sz == pytest.approx(MONOBLOC["height_mm"], abs=0.5)


def test_monobloc_model_bbox_equals_params(mk):
    for detail in (True, False):
        lo, hi = mk.build_monobloc(detail).bbox()
        size = [hi[i] - lo[i] for i in range(3)]
        assert size == pytest.approx([MONOBLOC["length_mm"], MONOBLOC["width_mm"], MONOBLOC["height_mm"]], abs=0.5)


def test_cabinet_step_bbox_equals_params(step):
    sx, sy, sz = _size(step["r1_ups_cabinet"])
    assert sx == pytest.approx(CABINET["width_mm"], abs=1.0)
    assert sy == pytest.approx(CABINET["depth_mm"], abs=1.0)
    assert sz == pytest.approx(CABINET["height_mm"], abs=1.0)


def test_cabinet_holds_shelves_x_blocks(mk):
    A = mk.build_cabinet(0.0)
    blocks = {p.sub for p in A.parts if p.sub and "monobloc" in p.sub}
    assert len(blocks) == CABINET["shelves"] * CABINET["monoblocs_per_shelf"]


# ------------------------------------------------------------------------------------------- R0
def test_r0_electrode_diameter_from_step(step):
    hits = [s for s in _walk(step["r0_test_cell"]) if getattr(s, "label", "") and "coating" in s.label.lower()
            and "electrode" in s.label.lower()]
    assert len(hits) == 2, [getattr(s, "label", "") for s in _walk(step["r0_test_cell"])]
    for s in hits:
        sx, sy, _ = _size(s)
        assert sx == pytest.approx(R0["electrode_diameter"].value, abs=0.01)
        assert sy == pytest.approx(15.0, abs=0.01)


def test_r0_electrode_diameter_from_model(mk):
    A = mk.build_r0()
    elec = [p for p in A.solids() if p.group in ("coating", "carbonpaper")]
    assert len(elec) == 4
    for p in elec:
        sx, sy, _ = _size(p.shape)
        assert sx == pytest.approx(15.0, abs=0.01) and sy == pytest.approx(15.0, abs=0.01)


# ------------------------------------------------------------------------------------------- internals
def test_stack_fits_compartment_and_true_repeat_count(mk):
    d, lay = monobloc(), monobloc_layout()
    assert lay["stack_t"] < lay["comp"]
    A = mk.build_monobloc(True)
    cathodes = [p for p in A.parts if p.ptype.startswith("cathode plate")]
    assert len(cathodes) == d["n_cells"] * d["repeats_per_cell"]       # every repeat unit is modelled
    c5 = [p.shape.bounding_box() for p in A.solids() if p.sub == "Cell 5" and p.group in ("cathode", "anode", "separator")]
    thick = max(b.max.X for b in c5) - min(b.min.X for b in c5)
    assert thick == pytest.approx(lay["stack_t"], abs=1e-3)


def test_monobloc_partlist_mass_close_to_design():
    rows = list(csv.DictReader(open(CAD_OUT / "r1_monobloc_partlist.csv")))
    total = float([r for r in rows if r["part"].startswith("TOTAL")][0]["total_mass_kg"])
    assert total == pytest.approx(monobloc()["mass_kg"], rel=0.05)


def _clashes(A, a_pred, b_pred, min_mm3=1.0):
    As = [p for p in A.solids() if a_pred(p)]
    Bs = [p for p in A.solids() if b_pred(p)]
    bad = []
    for a in As:
        ba = a.shape.bounding_box()
        for b in Bs:
            bb = b.shape.bounding_box()
            if (ba.max.X <= bb.min.X or bb.max.X <= ba.min.X or ba.max.Y <= bb.min.Y or bb.max.Y <= ba.min.Y
                    or ba.max.Z <= bb.min.Z or bb.max.Z <= ba.min.Z):
                continue
            v = (a.shape & b.shape).volume
            if v > min_mm3:
                bad.append((a.name, b.name, round(v, 1)))
    return bad


def test_no_block_clashes_in_cabinet(mk):
    A = mk.build_cabinet(0.0)
    structure = ("corner posts", "shelf with supports", "side panel", "rear panel", "front door with louvres",
                 "DC string breaker", "master BMS enclosure", "vertical cable duct (segments)", "roof with vent slots")
    assert _clashes(A, lambda p: p.sub and "monobloc" in p.sub and "Case container" in p.name,
                    lambda p: p.ptype in structure) == []


def test_no_block_clashes_in_module(mk):
    A = mk.build_module48()
    assert _clashes(A, lambda p: p.sub and p.sub.startswith("Monobloc") and "Case container" in p.name,
                    lambda p: p.material in ("galvanised steel", "electronics (potted avg)")) == []


def test_cad_tray_holds_four_monoblocs():
    assert tray_fits_4_monoblocs(M48_TRAY_CAD_MM)


@pytest.mark.xfail(strict=True, reason="PARAMS CONFLICT: MODULE48['tray_mm'] (600x450x280) cannot hold 4 VRLA-size "
                                       "monoblocs; CAD uses M48_TRAY_CAD_MM - params owner to update")
def test_params_tray_holds_four_monoblocs():
    assert tray_fits_4_monoblocs(MODULE48["tray_mm"])


# ------------------------------------------------------------------------------------------- drawings
def _dxf(name):
    import ezdxf
    p = DWG_OUT / f"{name}.dxf"
    assert p.exists(), f"missing {p} - run python drawings/make_drawings.py"
    return ezdxf.readfile(p)


def _dim_values(doc):
    return [round(d.get_measurement(), 3) for d in doc.modelspace().query("DIMENSION")]


def _texts(doc):
    return " | ".join(t.dxf.text if t.dxftype() == "TEXT" else t.text for t in doc.modelspace().query("TEXT MTEXT"))


def test_ga001_has_overall_dimensions():
    vals = _dim_values(_dxf("SB-GA-001"))
    lay = monobloc_layout()
    for v in (MONOBLOC["length_mm"], MONOBLOC["width_mm"], MONOBLOC["height_mm"], MONOBLOC["terminal_spacing_mm"],
              round(lay["pitch"], 3), round(lay["comp"], 3)):
        assert any(abs(x - v) < 0.01 for x in vals), f"{v} not dimensioned in SB-GA-001"


def test_ga002_has_layer_dimensions():
    d = monobloc()
    vals = _dim_values(_dxf("SB-GA-002"))
    for v in (d["plate_w_mm"], d["plate_h_mm"], round(d["compartment_mm"], 3)):
        assert any(abs(x - v) < 0.01 for x in vals), f"{v} not dimensioned in SB-GA-002"


def test_ga003_has_overall_dimensions():
    vals = _dim_values(_dxf("SB-GA-003"))
    for v in (CABINET["width_mm"], CABINET["depth_mm"], CABINET["height_mm"]):
        assert any(abs(x - v) < 0.01 for x in vals), f"{v} not dimensioned in SB-GA-003"


@pytest.mark.parametrize("dwg", ["SB-GA-001", "SB-GA-002", "SB-GA-003"])
def test_title_block_concept_text(dwg):
    t = _texts(_dxf(dwg))
    for s in ("CONCEPT — NOT FOR FABRICATION", "TOLERANCES: CONCEPT", "REV A", "2026-11-02", f"DWG {dwg}", "UNITS mm"):
        assert s in t, f"{s!r} missing from {dwg}"
    for ext in ("pdf", "png"):
        assert (DWG_OUT / f"{dwg}.{ext}").exists()
