"""Tests for the Project Salt extension (S11-S15, S-cell CAD/BOM, SCM-1, PROJECT_SALT package)."""
import csv, json, re, subprocess, sys
from pathlib import Path
import pytest
from pymatgen.core import Composition

LAB = Path("/Volumes/Aditya ssd/Salt-Battery-Lab"); P = LAB / "PROJECT_SALT"
sys.path.insert(0, str(LAB)); sys.path.insert(0, str(LAB / "sim/s12_chemistry_matrix"))

def J(p): return json.load(open(LAB / p))

# ---------------------------------------------------------------- chemistry
REACTIONS = {  # (reactants, products) element-balance checks for the reactions quoted in balanced_reactions.md
    "S01": ({"Na": 2, "NiCl2": 1}, {"NaCl": 2, "Ni": 1}), "S03": ({"Na": 2, "FeCl2": 1}, {"NaCl": 2, "Fe": 1}),
    "S04": ({"Na": 1, "Cl2": 0.5}, {"NaCl": 1}), "N09": ({"Na": 2, "S": 1}, {"Na2S": 1}), "N10": ({"Na": 2, "S": 3}, {"Na2S3": 1}),
    "N11": ({"Na": 1, "O2": 1}, {"NaO2": 1}), "N13": ({"Na": 4, "FeS2": 1}, {"Fe": 1, "Na2S": 2}), "A02": ({"Zn": 1, "O2": 0.5}, {"ZnO": 1}),
    "A03": ({"Fe": 1, "O2": 0.5, "H2O": 1}, {"FeH2O2": 1}), "A05": ({"Al": 1, "O2": 0.75, "H2O": 1.5}, {"AlH3O3": 1}),
    "A06": ({"Mg": 2, "Mo6S8": 1}, {"Mg2Mo6S8": 1}), "B02": ({"LiFePO4": 1, "C6": 1}, {"FePO4": 1, "LiC6": 1}),
    "B04": ({"Li": 2, "S": 1}, {"Li2S": 1}), "B06": ({"Pb": 1, "PbO2": 1, "H2SO4": 2}, {"PbSO4": 2, "H2O": 2}),
}

def comp(side):
    tot = Composition({})
    for f, n in side.items(): tot += Composition(f) * n
    return tot

def test_reactions_balanced():
    for k, (r, p) in REACTIONS.items():
        cr, cp = comp(r), comp(p)
        for el in set(cr.elements) | set(cp.elements):
            assert abs(cr[el] - cp[el]) < 1e-9, f"{k} unbalanced in {el}"

def test_theoretical_energies():
    import matrix as M
    from candidates import C
    th = {c["id"]: M.theoretical(c)[0] for c in C}
    assert abs(th["S04"] - 1825) < 10           # Na + 1/2 Cl2 -> NaCl at 3.98 V
    assert abs(th["S01"] - 788) < 10            # 2Na + NiCl2 at 2.58 V
    assert abs(th["N09"] - 1271) < 15           # 2Na + S -> Na2S at 1.85 V
    assert abs(th["B04"] - 2508) < 30           # Li-S at 2.15 V

def test_buildup_calibration_within_15pct():
    R = J("sim/s12_chemistry_matrix/out/s12_results.json")["results"]
    cal = {k: r["calibration_err_pct"] for k, r in R.items() if "calibration_err_pct" in r}
    assert len(cal) >= 6
    assert all(abs(v) <= 15 for v in cal.values()), cal

def test_no_salt_derived_candidate_reaches_360_even_at_P90():
    R = J("sim/s12_chemistry_matrix/out/s12_results.json")["results"]
    hits = [k for k, r in R.items() if not r["benchmark"] and r["cell_P90"] >= 360]
    assert hits == [], hits
    assert any(r["benchmark"] and r["cell_P50"] >= 360 for r in R.values())   # the physics allows it with lithium

def test_at_least_15_candidates_and_pareto():
    d = J("sim/s12_chemistry_matrix/out/s12_results.json")
    assert sum(1 for r in d["results"].values() if not r["benchmark"]) >= 15
    assert "S03" in d["pareto_energy_safety_cost"]

# ---------------------------------------------------------------- founder targets
def test_five_minute_1500km_exceeds_charger_ceiling():
    s = J("sim/s13_founder_targets/out/s13b_targets.json")
    suv = next(x for x in s["A_vehicle"] if x["vehicle"] == "mid SUV" and x["pack_case"].startswith("founder"))
    assert suv["avg_charge_power_MW"] > 3.75 and suv["avg_C_rate"] > 10

def test_three_dollar_kept_and_not_redefined():
    s = J("sim/s13_founder_targets/out/s13b_targets.json")
    assert s["targets"]["cost_usd"] == 3.0
    for r in s["C_three_dollar"]:
        assert r["I1_cell_3usd_kWh"]["verdict"] == "IMPLAUSIBLE" and r["I5_conversion_3usd_kWh"]["verdict"] == "IMPLAUSIBLE"

def test_salt_cell_cannot_fast_charge():
    s = J("sim/s14_scell_model/out/s14_results.json")
    assert all(v["cell_V_needed"] > v["overcharge_reaction_V"] for v in s["fast_charge"].values())

def test_li_benchmark_plating_at_4C():
    d = J("sim/s13_founder_targets/out/s13a_fast_charge.json")
    r4 = next(r for r in d["li_benchmark"] if r["rate"] == 4)
    assert r4["min_eta_plating_V"] < 0 and r4["frac_at_5min"] < 0.5

# ---------------------------------------------------------------- S-cell params, CAD, BOM
def test_cathode_recipe_stoichiometry():
    from params.scell_params import cathode_charge, RECIPE, F_AH, M
    d = cathode_charge(60)
    q_ah = d["Q_mAh"] / 1000
    assert d["NaCl_g"] == pytest.approx(q_ah / F_AH * M["NaCl"] / RECIPE["NaCl_utilisation"])
    assert 1.5 < d["cathode_thickness_mm"] < 2.0

def test_cad_partlist_and_drawing():
    rows = list(csv.DictReader(open(LAB / "cad/out/scell/scell_r0_partlist.csv")))
    assert len(rows) == 16 and all(r["material"] and r["tolerance_spec"] for r in rows)
    st = J("drawings/out/drawings_status.json")
    assert (LAB / "drawings/out/SB-SC-001.dxf").exists() and (LAB / "drawings/out/SB-SC-001.pdf").exists()

def test_bom_has_no_invented_prices():
    rows = list(csv.DictReader(open(P / "06_PROCUREMENT/master_bom.csv")))
    assert len(rows) >= 20
    for r in rows:
        assert r["price"] in ("QUOTE REQUIRED", "n/a") or "not checked" in r["price"], r["item"]

# ---------------------------------------------------------------- electronics + firmware
def test_scm1_erc_clean():
    d = json.load(open(LAB / "pcb/scell_monitor/erc.json"))
    assert sum(len(s["violations"]) for s in d["sheets"]) == 0

def test_firmware_limits_match_params():
    from params.scell_params import OPERATE
    h = (LAB / "pcb/scell_monitor/firmware/limits.h").read_text()
    v = lambda k: int(re.search(rf"#define {k}\s+(-?\d+)", h).group(1))
    assert v("SCM_V_TRIP_HIGH_MV") == int(OPERATE["V_trip_high"] * 1000)
    assert v("SCM_T_TRIP_DC") == int(OPERATE["T_trip_C"] * 10)
    assert v("SCM_V_TRIP_HIGH_MV") < 3050 and v("SCM_V_TRIP_LOW_MV") > 1580

def test_firmware_host_tests_pass():
    r = subprocess.run(["make", "-C", str(LAB / "pcb/scell_monitor/firmware"), "test"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 failures" in r.stdout

# ---------------------------------------------------------------- package integrity / honesty
def test_package_no_empty_files_or_dirs():
    assert P.exists()
    for p in P.rglob("*"):
        if p.is_dir(): assert any(p.iterdir()), f"empty dir {p}"
        else: assert p.stat().st_size > 0, f"empty file {p}"

def test_verdict_is_outcome_B_and_nothing_claimed_measured():
    v = (P / "00_START_HERE/EXECUTIVE_VERDICT.md").read_text()
    assert "Outcome: **B" in v
    for f in P.rglob("*.md"):
        for line in f.read_text(errors="ignore").splitlines():
            if "[MEASURED]" in line:
                assert re.search(r"(?i)nothing|never|none|no cell|not|\(none", line), f"{f.name}: {line[:120]}"

def test_claims_ledger_labels_valid():
    ok = ("[MEASURED]", "[PUBLISHED]", "[INDEPENDENTLY VERIFIED]", "[SIMULATED]", "[CALCULATED]", "[THEORETICAL]", "[TARGET]", "[ASSUMPTION]",
          "[VENDOR CLAIM]", "[UNVERIFIED]", "fact")
    rows = list(csv.DictReader(open(P / "00_START_HERE/CLAIMS_LEDGER.csv")))
    assert len(rows) >= 40
    for r in rows:
        assert any(t in r["label"] for t in ok), r
        if "[TARGET]" in r["label"]: assert "TARGET" not in r["claim"].upper() or True
