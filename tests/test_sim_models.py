"""Unit, conservation and regression tests for S1-S10."""
import json, math, pathlib, importlib, sys
import numpy as np
import pytest
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
J = lambda rel: json.loads((LAB / rel).read_text())


# ---------------- S1 ----------------
def test_s1_kit_rerun_all_pass():
    r = J("sim/s01_kit_rerun/out/s1_comparison.json")
    assert r["n_pass"] == r["n_total"] == 9


# ---------------- S2 ----------------
def test_s2_validation_recorded_honestly():
    r = J("sim/s02_pybamm_validation/out/s02_validation.json")
    assert r["independent_validation_pass"] is False          # documented failure, must not silently flip
    assert r["calibrated_pass"] is True
    for v in r["rates"].values():
        assert abs(v["A_as_shipped"]["q_end_err_pct"]) < 5     # capacity within 5 % at every rate
        assert v["D_calibrated_k_x2"]["MAE_mV"] <= 60


def test_s2_digitiser_regression():
    sys.path.insert(0, str(LAB / "sim/s02_pybamm_validation"))
    import run_s02
    pts = run_s02.digitise()
    assert set(pts) == {1, 5, 10, 12}
    assert all(len(v) >= 10 for v in pts.values())
    # 0.1C curve starts near 4.1 V (paper Fig. 4a)
    q, v = zip(*pts[1])
    assert 4.0 < v[0] < 4.2


# ---------------- S3 ----------------
def test_s3_retention_physical():
    r = J("sim/s03_r1_cell/out/s03_results.json")
    for L, d in r["mc"].items():
        for c in ("0.2", "1.0", "4.0"):
            assert 0 <= d[c]["p10"] <= d[c]["p50"] <= d[c]["p90"] <= 1.05
        assert d["0.2"]["p50"] >= d["1.0"]["p50"] >= d["4.0"]["p50"]          # higher rate -> less capacity
    p50_4c = [r["mc"][str(L) if str(L) in r["mc"] else repr(L)]["4.0"]["p50"] for L in r["loadings_mg_cm2"]]
    assert p50_4c[0] >= p50_4c[-1]                                            # thicker -> worse at 4C


def test_s3_round_trip_bounded():
    rt = J("sim/s03_r1_cell/out/s03_results.json")["round_trip"]
    effs = [rt[c]["round_trip_eff"] for c in ("0.2", "1.0", "4.0")]
    assert all(0.5 < e <= 1.0 for e in effs) and effs[0] >= effs[1] >= effs[2]


# ---------------- S4 ----------------
def test_s4_faraday_conservation():
    sys.path.insert(0, str(LAB / "sim/s04_gas"))
    import run_s04
    b = run_s04.ce_budget(0.99, 1.0, 10.0)       # 1 % of 10 Ah = 0.1 Ah side charge, all HER
    n_e = 0.1 * 3600 / 96485.33212
    assert math.isclose(b["H2_mL"], n_e / 2 * 22.414 * 1000, rel_tol=1e-9)
    assert math.isclose(b["water_g"], n_e * 18.015, rel_tol=1e-9)
    b2 = run_s04.ce_budget(0.99, 0.0, 10.0)      # all OER: O2 = n_e/4, water = n_e/2
    assert math.isclose(b2["O2_mL"], n_e / 4 * 22.414 * 1000, rel_tol=1e-9)


def test_s4_nernst_window():
    sys.path.insert(0, str(LAB / "sim/s04_gas"))
    import run_s04
    for pH in (0, 7, 14):
        assert math.isclose(run_s04.e_oer(pH) - run_s04.e_her(pH), 1.229, abs_tol=1e-9)


def test_s4_ce_requirement_consistent():
    r = J("sim/s04_gas/out/s04_results.json")
    assert 0.998 < r["nominal"]["CE_needed_for_3000_cycles"] < 0.9995
    cyc = [x["cycles_to_20pct_water_loss"] for x in r["ce_sweep"]]
    assert cyc == sorted(cyc)


# ---------------- S5 ----------------
def test_s5_literature_regression():
    s = J("sim/s05_atomistic/out/s05_summary.json")
    assert abs(s["voltages"]["LiFePO4"]["mace_mp0b3"] - 3.45) < 0.15      # uMLIP reproduces LiFePO4 within 0.15 V
    assert abs(s["voltages"]["LiMn2O4"]["mace_mp0b3"] - 4.10) < 0.15
    assert s["errors"]["mace_mp0b3"]["max_abs_V"] > 0.5                   # and we report the large NTP/PBA failures
    il = {round(float(k), 3): v for k, v in s["interlayer_A"]["chgnet"].items()}
    assert abs(il[0.333] - 7.19) < 0.3                                    # vs paper XRD


def test_s5_voltage_formula():
    sys.path.insert(0, str(LAB / "sim/s05_atomistic"))
    import analyze
    E = {"A": -10.0, "H": -6.0, "Na_bcc": -1.0}
    assert math.isclose(analyze.voltage(E, "A", "H", "Na", 2), -(-10 + 6 + 2) / 2)


# ---------------- S7 / S9 ----------------
def test_s7_bounds_and_aquion_class():
    r = J("sim/s07_buildup/out/s07_results.json")
    m = r["R1_mc"]["monobloc_Wh_kg"]
    assert m["p10"] < m["p50"] < m["p90"]
    assert 10 < m["p50"] < 40


def test_s9_refusal_logic():
    sys.path.insert(0, str(LAB / "sim/s09_tea"))
    import run_s09
    from params.product_params import COST
    saved = COST.pop("ntp")
    try:
        run_s09.REQUIRED = run_s09.REQUIRED  # REQUIRED captured at import includes 'ntp'
        with pytest.raises(SystemExit):
            run_s09.check_inputs()
    finally:
        COST["ntp"] = saved


def test_s9_cost_components_sum():
    r = J("sim/s09_tea/out/s09_results.json")["monobloc_ups"]
    total = r["materials_after_yield"] + r["labour"] + r["energy"] + r["overhead"] + r["depreciation"]
    assert math.isclose(total, r["cost"], rel_tol=1e-9)
    assert math.isclose(r["cost"] / r["kWh"], r["cost_per_kWh"], rel_tol=1e-9)


def test_s9_spreadsheet_matches_python():
    pdf = LAB / "work/xlsx_check/recalced/SaltBattery_Financial_Model.pdf"
    if not pdf.exists():
        pytest.skip("LibreOffice recalculation not run")
    from pypdf import PdfReader
    t = "\n".join(p.extract_text() for p in PdfReader(str(pdf)).pages)
    r = J("sim/s09_tea/out/s09_results.json")
    line = [l for l in t.splitlines() if l.startswith("Cost per kWh ")][0]
    assert abs(float(line.split()[-1].replace(",", "")) - r["monobloc_ups"]["cost_per_kWh"]) < 0.5


# ---------------- S8 / S10 ----------------
def test_s8_energy_balance():
    r = J("sim/s08_thermal/out/s08_results.json")["abuse"]
    assert r["adiabatic_rise_if_all_energy_released_K"] < 75     # never reaches boiling from 25 C
    assert r["case_fire_load_MJ"] > r["stored_electrical_energy_MJ"]


def test_s10_ordering():
    r = J("sim/s10_market/out/s10_results.json")
    assert r["SOM_usd_yr_after_5y"]["p50"] < r["SAM_usd_yr"]["p50"] < r["TAM_usd_yr"]["p50"]
    # cross-check against paid-report UPS battery market (305-401 M$): same order of magnitude
    assert 100e6 < r["TAM_usd_yr"]["p50"] < 1500e6


# ---------------- claims ledger ----------------
def test_claims_ledger_complete():
    import csv
    rows = list(csv.DictReader(open(LAB / "CLAIMS_LEDGER.csv")))
    assert len(rows) >= 50
    tags = {"LIT", "VENDOR", "CALC", "SIM", "ASSUMPTION", "TARGET"}
    for r in rows:
        assert r["tag"] in tags and r["tag"] != "MEASURED"
        assert r["source/evidence file"].strip()
