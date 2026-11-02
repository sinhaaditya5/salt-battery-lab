"""Engineering designs D3-D5 (P1 cell, SM-48T module + thermal, SC-UPS-1), spreadsheet, MATLAB stems, salt renders/diagrams."""
import csv, json
from pathlib import Path
import pytest

LAB = Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
import sys; sys.path.insert(0, str(LAB))
from params.smodule_params import CABINET, MODULE, P1, THERMAL  # noqa: E402
from params.scell_params import OPERATE  # noqa: E402


def test_module_electrical_envelope():
    assert MODULE["V_max"] < 60.0                                   # SELV
    assert MODULE["V_min"] >= 40.0                                  # telecom LVD window
    assert abs(MODULE["kWh"] - MODULE["V_nom"] * MODULE["Ah"] / 1000) < 1e-9
    # the max module current respects the R0 current-density limit (C/1.5 at 60 mAh/cm2)
    assert MODULE["I_max_A"] <= MODULE["parallel"] * OPERATE["I_max_mA_cm2"] * P1["active_cm2"] / 1000 + 1e-9
    assert P1["j_max_mA_cm2"] / P1["qa_mAh_cm2"] < 4.0              # a 15-min (4C) UPS is out of reach: stated in the docs


def test_p1_stack_thickness():
    t = 2 * P1["can_wall_mm"] + P1["anode_gap_mm"] + P1["plate_t_mm"] + P1["cathode_t_mm"] + P1["spring_gap_mm"]
    assert abs(t - P1["thickness_mm"]) < 1e-9 and 6 < t < 12


@pytest.fixture(scope="module")
def s16():
    p = LAB / "sim/s16_module_thermal/out/s16_results.json"
    if not p.exists(): pytest.skip("run sim/s16_module_thermal/thermal.py")
    return json.load(open(p))


def test_thermal_physics(s16):
    g = s16["geometry"]
    assert g["A_inner_m2"] < g["A_mean_m2"] < g["A_outer_m2"]
    sd = s16["standby_design"]
    assert sd["microporous_W"] / sd["evacuated_W"] == pytest.approx(THERMAL["k_microporous_W_mK"] / THERMAL["k_vacuum_panel_W_mK"], rel=1e-2)   # results rounded to 0.1 W
    sw = s16["standby_sweep"]["W"]["evacuated panel, 25 C"]
    assert all(a > b for a, b in zip(sw, sw[1:]))                   # loss falls monotonically with thickness
    assert s16["warmup"]["600 W"]["hours"] >= s16["warmup_ramp_limited_floor_h"]
    assert s16["discharge"]["adiabatic_rise_C"] < 260 - THERMAL["T_op_C"]


@pytest.fixture(scope="module")
def meta():
    p = LAB / "cad/out/smodule/smodule_meta.json"
    if not p.exists(): pytest.skip("run cad/make_smodule.py")
    return json.load(open(p))


def test_module_fits_rack_and_partlist(meta):
    m = meta["sm48t"]
    assert m["ox"] <= 450.0                                         # 19-inch rack opening
    assert m["oz"] <= MODULE["height_mm"] + 1e-6                     # 7U
    rows = list(csv.DictReader(open(LAB / "cad/out/smodule/sm48t_partlist.csv")))
    q = {int(r["item"]): int(r["qty"]) for r in rows}
    assert q[21] == MODULE["cells"] and q[5] == 4                   # 84 beta'' plates, 4 heaters
    assert all(r["material"] and r["tolerance_spec"] for r in rows)
    assert m["Wh_kg"] == pytest.approx(MODULE["kWh"] * 1000 / m["mass_kg"], rel=1e-3)


def test_step_and_drawings_exist(meta):
    for f in ("p1_cell.step", "sm48t_module.step", "sm48t_exploded.step", "sm48t_cutaway.step", "sc_ups1_cabinet.step"):
        assert (LAB / "cad/out/smodule" / f).stat().st_size > 10_000, f
    for d in ("SB-SM-001", "SB-TM-001", "SB-UPS-001"):
        for ext in ("dxf", "pdf", "png"):
            assert (LAB / "drawings/out" / f"{d}.{ext}").exists(), (d, ext)
    st = meta.get("drawings") or json.load(open(LAB / "cad/out/smodule/smodule_meta.json")).get("drawings")
    if st:
        assert all(v["tool"] == "CADCraft" and not v["errors"] for v in st.values())


def test_spreadsheet_verified():
    p = LAB / "PROJECT_SALT/10_ECONOMICS/salt_model_check.json"
    if not p.exists(): pytest.skip("run finance/make_salt_model.py")
    c = json.load(open(p))
    assert c["verified"] and not c["errors"] and c["sheets_exported"] >= 8
    r = c["recalculated"]
    assert r["module_usd_kwh"] > 3 * 10                              # nowhere near USD 3/kWh
    assert r["whkg_levers"][0] < r["whkg_levers"][-1]


def test_matlab_stems():
    d = LAB / "matlab/stem"
    ms = sorted(d.glob("stem_*.m")); pngs = sorted((d / "out").glob("stem_*.png"))
    assert len(ms) >= 5 and len(pngs) == len(ms)
    for m in ms:
        t = m.read_text(); assert "stem(" in t and "print(" in t


def test_salt_diagrams_and_renders():
    for n in ("ds1_cell_electrochemistry", "ds2_module_electrical", "ds3_module_thermal_budget", "ds4_p1_manufacturing_flow", "ds5_gate_ladder"):
        assert (LAB / "diagrams/out" / f"{n}.png").exists(), n
    caps = list((LAB / "renders/out_salt").glob("*_captioned.png"))
    if not caps: pytest.skip("renders not run")
    assert len(caps) >= 6
