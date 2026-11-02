"""Params single-source-of-truth tests: tags, ranges, derived-design consistency."""
import math
import pytest
from params import product_params as PP
from params.product_params import P, MAT, COST, MONOBLOC, R0, ALLOWED_TAGS
import params.design as D


def all_P():
    for name in dir(PP):
        obj = getattr(PP, name)
        if isinstance(obj, P):
            yield name, obj
        elif isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, P):
                    yield f"{name}.{k}", v


def test_every_value_tagged_and_no_measured():
    for name, p in all_P():
        assert p.tag in ALLOWED_TAGS, name
        assert p.tag != "MEASURED"


def test_assumptions_have_ordered_ranges():
    for name, p in all_P():
        if p.tag == "ASSUMPTION":
            assert p.rng is not None, name
            assert p.rng[0] <= p.value <= p.rng[1], (name, p.value, p.rng)


def test_measured_tag_rejected():
    with pytest.raises(ValueError):
        P(1.0, "-", "MEASURED", "x")


def test_r0_loading_matches_paper_geometry():
    area = math.pi * 0.75 ** 2
    assert abs(PP.R0_LOADING_MG_CM2 - 5.0 / area) < 1e-9
    assert 2.8 < PP.R0_LOADING_MG_CM2 < 2.9


def test_monobloc_energy_identity():
    mb = D.monobloc()
    assert abs(mb["energy_Wh"] - mb["n_cells"] * mb["v_cell_nom"] * mb["cap_Ah"]) < 1e-6
    assert abs(mb["v_cell_nom"] - (MAT["cathode_avg_potential_SHE"].value - MAT["anode_avg_potential_SHE"].value)) < 1e-9


def test_monobloc_mass_balance_and_fits_envelope():
    mb = D.monobloc()
    parts = mb["stack_kg"] + mb["case_kg"] + mb["hardware_kg"] + mb["free_electrolyte_kg"]
    assert abs(parts - mb["mass_kg"]) < 1e-9
    assert mb["repeats_per_cell"] * mb["electrode"]["repeat_thick_um"] / 1000 <= mb["compartment_mm"]
    assert abs(mb["volume_L"] - MONOBLOC["length_mm"] * MONOBLOC["width_mm"] * MONOBLOC["height_mm"] / 1e6) < 1e-9


def test_loading_monotonic():
    caps = [D.electrode_stack(L)["cap_mAh_cm2"] for L in (2.8, 10, 40, 80)]
    assert caps == sorted(caps)


def test_electrolyte_below_solubility_limit_at_5C():
    # 0.5 M Na2SO4 = 7.1 g/100 mL; solubility rises from 4.76 (0 C) to >=13.9 (20 C): saturation between 0 and ~10 C
    g_per_100mL = MAT["electrolyte_molarity"].value * 142.04 / 10
    assert g_per_100mL < 13.9
    assert MAT["na2so4_solubility_0C"].value < g_per_100mL  # i.e. it would saturate near freezing -> stated 5 C limit
