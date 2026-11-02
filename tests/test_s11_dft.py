"""S11 DFT(+U) chloride campaign: parser unit tests + regression gates on the analysed results."""
import json, sys
from pathlib import Path
import pytest

LAB = Path("/Volumes/Aditya ssd/Salt-Battery-Lab"); S11 = LAB / "sim/s11_dft_chlorides"
sys.path.insert(0, str(S11))
import campaign as C  # noqa: E402

RES = S11 / "out/s11_results.json"

FAKE = """
     number of electrons       =         6.00
     End of self-consistent calculation

 ------ SPIN UP ------------


          k = 0.0000 0.0000 0.0000 (  100 PWs)   bands (ev):

    -5.0000  -4.0000  -1.0000   2.0000   3.0000

          k = 0.5000-0.5000 0.0000 (  100 PWs)   bands (ev):

    -5.1000  -3.9000  -0.5000   1.5000   3.5000

 ------ SPIN DOWN ----------


          k = 0.0000 0.0000 0.0000 (  100 PWs)   bands (ev):

    -4.8000  -0.2000   2.5000   3.0000   4.0000

          k = 0.5000-0.5000 0.0000 (  100 PWs)   bands (ev):

    -4.9000   0.1000   2.2000   3.1000   4.2000

     the Fermi energy is     0.5000 ev
     total magnetization       =     2.00 Bohr mag/cell
"""


def test_band_gap_electron_counting(tmp_path):
    # N = 6, M = 2 -> 4 up, 2 down occupied. VBM = max(up[3]=2.0/1.5, dn[1]=-0.2/0.1) = 2.0;
    # CBM = min(up[4]=3.0/3.5, dn[2]=2.5/2.2) = 2.2 -> gap 0.2 eV
    f = tmp_path / "job.out"; f.write_text(FAKE)
    g = C.band_gap(f)
    assert g == dict(gap_eV=0.2, vbm_eV=2.0, cbm_eV=2.2, n_up=4, n_dn=2)


def test_band_gap_rejects_nonintegral_moment(tmp_path):
    f = tmp_path / "job.out"; f.write_text(FAKE.replace("2.00 Bohr", "1.70 Bohr"))
    assert C.band_gap(f) is None


def test_relaxed_geometry_refuses_unconverged(tmp_path):
    (tmp_path / "job.out").write_text("CELL_PARAMETERS (alat= 6.0)\n1 0 0\n0 1 0\n0 0 1\n")
    with pytest.raises(ValueError):
        C.relaxed_geometry(tmp_path)


@pytest.fixture(scope="module")
def res():
    if not RES.exists():
        pytest.skip("run sim/s11_dft_chlorides/analyze.py first")
    return json.load(open(RES))


def test_every_reference_and_chloride_relaxed(res):
    for k, v in res["status"].items():
        assert v.startswith("DONE"), (k, v)
    assert len(res["status"]) == 12


def test_pbe_u0_voltages_track_thermochemistry(res):
    # consistent-functional (U = 0) conversion voltages within 0.35 V of the dH-based experimental value (screening accuracy)
    for m in ("Fe", "Co", "Ni"):
        v = res["voltages"][f"{m}Cl2_U0"]
        assert abs(v["err_vs_dH_V"]) < 0.35, (m, v)
    # and the voltage ordering Fe < Co < Ni matches experiment
    V = [res["voltages"][f"{m}Cl2_U0"]["dft_V"] for m in ("Fe", "Co", "Ni")]
    E = [res["voltages"][f"{m}Cl2_U0"]["exp_dH_V"] for m in ("Fe", "Co", "Ni")]
    assert (V[0] < V[2]) and (E[0] < E[2])


def test_nacl_formation_within_half_ev(res):
    assert abs(res["formation"]["NaCl"]["err_eV"]) < 0.5


def test_uscan_and_magnetic_complete(res):
    assert len(res["uscan"]) == 6 and all(len(r) == 4 for r in res["uscan"].values())
    assert len(res["magnetic"]) == 6
    # interlayer coupling in these van der Waals layered chlorides is weak: |E_AFM - E_FM| < 20 meV/f.u.
    for k, v in res["magnetic"].items():
        assert abs(v["E_AFM_minus_FM_meV_per_fu"]) < 20, (k, v)


def test_every_job_has_a_platform(res):
    assert res["platform"] and all(v.startswith(("EC2", "local")) for v in res["platform"].values())
