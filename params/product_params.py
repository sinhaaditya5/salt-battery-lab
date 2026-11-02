"""Single source of truth for every design number in the Salt Battery lab.

Rules
-----
* CAD, drawings, PCB ratings, simulations, cost model and documents import from here.
  No hand-copied numbers anywhere else.
* Every value is a ``P`` record carrying a claim tag:
  LIT | VENDOR | CALC | SIM | ASSUMPTION | TARGET   (MEASURED is forbidden until lab data exists).
* Ranges are (low, nominal, high). Assumptions always carry a range and a justification.

This file is extended phase by phase. R0 = published reference cell; R1 = our product concept.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Tuple

ALLOWED_TAGS = {"LIT", "VENDOR", "CALC", "SIM", "ASSUMPTION", "TARGET"}


@dataclass(frozen=True)
class P:
    value: float
    unit: str
    tag: str
    source: str
    rng: Optional[Tuple[float, float]] = None  # (low, high) for ASSUMPTION / SIM / TARGET
    note: str = ""

    def __post_init__(self):
        if self.tag not in ALLOWED_TAGS:
            raise ValueError(f"tag {self.tag!r} not allowed (MEASURED is forbidden until lab data exists)")
        if self.tag == "ASSUMPTION" and self.rng is None:
            raise ValueError("ASSUMPTION values must carry a range")

    def __float__(self):
        return float(self.value)

    @property
    def lo(self):
        return self.rng[0] if self.rng else self.value

    @property
    def hi(self):
        return self.rng[1] if self.rng else self.value


SHAN2019 = "Shan et al., Nat. Commun. 10, 4975 (2019), doi:10.1038/s41467-019-12939-3"

# ----------------------------------------------------------------------------------------
# Physical constants
# ----------------------------------------------------------------------------------------
F = 96485.33212        # C/mol
R_GAS = 8.314462618    # J/mol/K
T_REF = 298.15         # K
E_WATER_THERMO = P(1.229, "V", "LIT", "Standard thermodynamic water-splitting potential (25 C)")

# ----------------------------------------------------------------------------------------
# R0 — published reference cell (Shan 2019) as transcribed in the kit
# ----------------------------------------------------------------------------------------
R0 = dict(
    active_mass_per_electrode=P(5.00, "mg", "LIT", SHAN2019 + " Methods; kit 01_R0 spec 5.1"),
    carbon_black_per_electrode=P(1.25, "mg", "LIT", SHAN2019),
    electrode_diameter=P(15.0, "mm", "LIT", SHAN2019 + " (Toray carbon paper, 1.5 cm)"),
    electrolyte_volume=P(150.0, "uL", "LIT", SHAN2019),
    electrolyte_molarity=P(1.0, "mol/L", "LIT", SHAN2019 + " (Na2SO4)"),
    full_cell_window=P(2.5, "V", "LIT", SHAN2019),
    capacity_after_5000=P(83.0, "mAh/g", "LIT", SHAN2019 + " at 1 A/g; electrode-material basis; denominator ambiguous"),
    capacity_10Ag=P(24.0, "mAh/g", "LIT", SHAN2019 + " at 10 A/g (kit spec section 6)"),
    halfcell_capacity_first=P(138.0, "mAh/g", "LIT", SHAN2019 + " half-cell 0.6 A/g, -0.75..1.25 V vs Ag/AgCl, 1st cycle"),
    halfcell_capacity_4th=P(94.0, "mAh/g", "LIT", SHAN2019 + " half-cell, after 4th cycle"),
    d001_pristine=P(7.19, "angstrom", "LIT", SHAN2019 + " XRD, Na0.27MnO2.0.63H2O"),
    d001_insitu_max=P(7.33, "angstrom", "LIT", SHAN2019 + " in-situ XRD extreme state"),
    d001_insitu_min=P(7.02, "angstrom", "LIT", SHAN2019 + " in-situ XRD extreme state"),
    na_per_mn=P(0.27, "-", "LIT", SHAN2019),
    h2o_per_mn=P(0.63, "-", "LIT", SHAN2019 + " TGA"),
)
R0_ELECTRODE_AREA_CM2 = math.pi * (R0["electrode_diameter"].value / 20.0) ** 2           # CALC
R0_LOADING_MG_CM2 = R0["active_mass_per_electrode"].value / R0_ELECTRODE_AREA_CM2       # CALC ~2.83

COMMERCIAL_LOADING = P(20.0, "mg/cm2", "ASSUMPTION", "Typical commercial electrode active loading",
                       rng=(15.0, 25.0), note="Mission brief range for commercial electrodes")

# ----------------------------------------------------------------------------------------
# Atomistic / DFT settings (S5, S6). Literature validation values live in sim/s05_atomistic.
# ----------------------------------------------------------------------------------------
DFT = dict(
    functional="PBE",
    hubbard_U_eV={"Mn": 3.9, "Fe": 5.3},      # Materials Project GGA+U values (Jain et al. 2011); no U on Ti
    hubbard_source="Materials Project GGA+U U values (Mn 3.9 eV, Fe 5.3 eV); projector differences between "
                   "QE 'atomic' and VASP PAW make these approximate",
    pseudopotentials="GBRV ultrasoft v1.2-1.5 (Garrity et al., Comput. Mater. Sci. 81, 446 (2014))",
    ecutwfc_Ry=40.0,           # GBRV design cutoff (40 Ry); reduced from 45 after on-instance timing, 2 Nov 2026
    ecutrho_Ry=240.0,          # 6x for USPP (GBRV recommends 200)
    kspacing_inv_A=0.25,          # Monkhorst-Pack density target (2*pi*0.25 / A^-1 grid)
    smearing="mv", degauss_Ry=0.01,
    magnetic_order="ferromagnetic initial guess (screening simplification)",
)

# ----------------------------------------------------------------------------------------
# EC2 job envelope approved by the founder on 2 Nov 2026
# ----------------------------------------------------------------------------------------
EC2 = dict(
    region="ap-south-1",
    instance_type="c8g.8xlarge",       # Graviton4, 32 physical cores, 64 GiB
    market="spot",
    os="Ubuntu 24.04 LTS (arm64)",
    spend_cap_usd=25.0,
    hard_shutdown_hours=48.0,
    spot_price_seen_usd_h=0.3155,       # describe-spot-price-history, 2 Nov 2026
    ebs_gb=60,
)

# ========================================================================================
# R1 — product concept (Phase 3 decision, 2 Nov 2026; see decisions/DECISIONS.md D-03..D-08)
# Chemistry B: Na-birnessite (Na_xMnO2.yH2O) cathode // carbon-coated NaTi2(PO4)3 anode,
# 1 mol/L Na2SO4 (pH ~7, no perchlorate), sealed O2-free, valve-regulated.
# Format: 12 V "monobloc" — 10 prismatic multi-plate cells in series in one VRLA-sized case,
# so a UPS / telecom integrator can swap it for a 12 V VRLA block.  EVERY value below is an
# input; performance numbers are [TARGET] until a cell is built and measured.
# ========================================================================================
MAT = dict(
    # --- cathode: Na-birnessite -------------------------------------------------------
    cathode_capacity=P(75.0, "mAh/g", "ASSUMPTION", "Practical capacity in a ~1 V window; Shan 2019 half-cell 94 mAh/g after 4 cycles, 83 mAh/g full-cell basis ambiguous",
                       rng=(50.0, 94.0)),
    cathode_avg_potential_SHE=P(0.55, "V vs SHE", "ASSUMPTION", "Mid-window of Shan 2019 half-cell (-0.75..1.25 V vs Ag/AgCl) restricted to the gas-safe region; S5 uMLIP 2.2-3.7 V vs Na brackets it",
                                rng=(0.35, 0.75)),
    cathode_density=P(3.2, "g/cm3", "ASSUMPTION", "Hydrated birnessite crystal density ~3.0-3.6 g/cm3", rng=(3.0, 3.6)),
    # --- anode: NaTi2(PO4)3 / C ----------------------------------------------------------
    anode_capacity=P(115.0, "mAh/g", "ASSUMPTION", "NTP theoretical 133 mAh/g; aqueous reports ~100-110 mAh/g (RSC JMCA 2019 C9TA08829F)", rng=(95.0, 125.0)),
    anode_avg_potential_SHE=P(-0.61, "V vs SHE", "CALC", "-0.807 V vs Ag/AgCl (RSC JMCA 2019) + 0.197 V"),
    anode_density=P(2.95, "g/cm3", "ASSUMPTION", "NASICON NaTi2(PO4)3 crystal density ~2.9-3.0 g/cm3", rng=(2.85, 3.05)),
    # --- electrode formulation (both electrodes, aqueous binder, no NMP, no dry room) ----
    active_fraction=P(0.80, "-", "ASSUMPTION", "80:10:10 active:carbon:binder, common aqueous-electrode recipe", rng=(0.75, 0.88)),
    carbon_fraction=P(0.10, "-", "ASSUMPTION", "conductive carbon", rng=(0.06, 0.12)),
    electrode_porosity=P(0.35, "-", "ASSUMPTION", "calendered aqueous electrode", rng=(0.30, 0.45)),
    np_ratio=P(1.10, "-", "ASSUMPTION", "anode/cathode capacity ratio (anode excess against HER-driven loss)", rng=(1.05, 1.25)),
    # --- electrolyte --------------------------------------------------------------------
    # D-05: 0.5 mol/L, not the paper's 1 mol/L: 1 M Na2SO4 (14.2 g/100 mL) crystallises as Glauber's salt below ~15-20 C
    electrolyte_molarity=P(0.5, "mol/L", "TARGET", "Na2SO4; keeps saturation below ~5 C (decision D-05)", rng=(0.4, 0.6)),
    na2so4_solubility_0C=P(4.76, "g/100 mL", "LIT", "Na2SO4 solubility at 0 C (Wikipedia/CRC anhydrous basis; sources conflict at 20 C: 13.9-19.5)"),
    na2so4_solubility_25C=P(28.1, "g/100 mL", "LIT", "Na2SO4 solubility at 25 C (Wikipedia/CRC)"),
    electrolyte_density=P(1.06, "g/cm3", "ASSUMPTION", "0.5 mol/L Na2SO4(aq) ~1.06 g/cm3", rng=(1.05, 1.07)),
    electrolyte_conductivity=P(4.8, "S/m", "ASSUMPTION", "0.5 mol/L Na2SO4(aq) ~4-5.5 S/m at 25 C", rng=(4.0, 5.5)),
    electrolyte_excess=P(1.10, "-", "ASSUMPTION", "electrolyte volume / pore volume", rng=(1.05, 1.30)),
    # --- inactive parts -----------------------------------------------------------------
    cc_thickness_um=P(25.0, "um", "ASSUMPTION", "carbon-coated 316L stainless foil current collector", rng=(15.0, 50.0)),
    cc_density=P(8.0, "g/cm3", "LIT", "316L stainless steel density"),
    separator_thickness_um=P(150.0, "um", "ASSUMPTION", "nonwoven PP / absorbent glass mat", rng=(100.0, 300.0)),
    separator_areal_mass=P(6.0, "mg/cm2", "ASSUMPTION", "nonwoven separator", rng=(4.0, 10.0)),
    separator_porosity=P(0.60, "-", "ASSUMPTION", "nonwoven", rng=(0.5, 0.75)),
)
R1_CELL_VOLTAGE_NOM = MAT["cathode_avg_potential_SHE"].value - MAT["anode_avg_potential_SHE"].value   # CALC ~1.16 V
R1_CELL_V_MAX = P(1.75, "V", "TARGET", "charge cut-off; kept inside the gas-safe window found in S4")
R1_CELL_V_MIN = P(0.60, "V", "TARGET", "discharge cut-off")

# Design point: cathode areal loading per side and plate geometry (S3 sweeps loading; this is the chosen point)
R1_LOADING = dict(
    cathode_mg_cm2_per_side=P(40.0, "mg/cm2", "TARGET", "design point from S3 loading sweep (UPS 15-min rate retention vs cost)", rng=(20.0, 80.0)),
)

# 12 V monobloc: external envelope copies the common 12 V 100 Ah VRLA block so it fits existing UPS racks
MONOBLOC = dict(
    cells_in_series=10,
    length_mm=330.0, width_mm=173.0, height_mm=220.0,          # common 12 V 100 Ah VRLA footprint [LIT: typical datasheets]
    wall_mm=4.0, partition_mm=2.5, lid_mm=6.0, base_mm=4.0,
    headspace_mm=30.0,                                          # gas space + busbars above plates
    plate_margin_mm=5.0,                                        # electrode edge clearance to wall
    case_material="PP-GF20 (glass-filled polypropylene)", case_density_g_cm3=1.05,
    terminal="M8 female insert", terminal_spacing_mm=250.0,
    vent_valve_open_kPa=P(15.0, "kPa", "TARGET", "one-way pressure-relief valve opening (VRLA valves open ~7-35 kPa); sized in S4", rng=(7.0, 35.0)),
    flame_arrestor="porous PP frit in vent path",
)
VRLA_REF = dict(
    energy_kWh_C10=P(1.2, "kWh", "CALC", "12 V x 100 Ah nominal"),
    mass_kg=P(30.0, "kg", "ASSUMPTION", "typical 12 V 100 Ah VRLA datasheet mass", rng=(28.0, 32.0)),
    fraction_at_15min=P(0.50, "-", "ASSUMPTION", "deliverable energy at a 15-minute UPS rate vs C10 (constant-power tables)", rng=(0.45, 0.60)),
    life_years=P(4.0, "years", "ASSUMPTION", "VRLA float service life in UPS at 25 C", rng=(3.0, 6.0)),
)

# Telecom / small-UPS module and data-centre UPS cabinet
MODULE48 = dict(
    monoblocs=4, nominal_V=48.0,
    dcdc_needed=True,                    # sloping 0.6-1.75 V/cell does not fit a 42-57 V bus without a DC/DC stage
    dcdc_efficiency=P(0.97, "-", "ASSUMPTION", "bidirectional buck-boost", rng=(0.95, 0.98)),
    tray_mm=(600.0, 450.0, 280.0),       # fits a 19-inch / 600 mm deep telecom cabinet shelf
)
CABINET = dict(
    width_mm=600.0, depth_mm=800.0, height_mm=2000.0,
    shelves=8, monoblocs_per_shelf=5,    # 40 monoblocs = one 480 V nominal string
    string_nominal_V=480.0,
)
BMS = dict(
    series_groups_per_board=16,          # one board can read up to 16 series groups (cells or monoblocs)
    cell_v_range=(0.0, 2.5),             # V per measured group (aqueous cell)
    block_v_range=(0.0, 20.0),           # V per monobloc channel
    ntc_channels=8, shunt_A_max=200.0, shunt_mohm=0.25,
    gas_inputs=2,                        # H2 sensor + pressure transducer (aqueous-specific)
    comms=("CAN 2.0B", "RS-485 Modbus RTU"), isolation_kV=2.5,
    supply_V=(9.0, 60.0),
)

# ----------------------------------------------------------------------------------------
# S4 gas / water-window inputs
# ----------------------------------------------------------------------------------------
GAS = dict(
    pH=P(7.0, "-", "ASSUMPTION", "neutral Na2SO4; drifts locally (HER raises pH at anode, OER lowers it at cathode)", rng=(6.0, 9.0)),
    coulombic_eff=P(0.995, "-", "ASSUMPTION", "aqueous Na-ion full cells typically report 98-99.9 % CE; side charge -> gas/water loss",
                    rng=(0.990, 0.999)),
    her_share=P(0.8, "-", "ASSUMPTION", "fraction of side charge that is HER at the anode (rest OER at cathode)", rng=(0.5, 0.95)),
    tafel_HER_mV_dec=P(180.0, "mV/dec", "ASSUMPTION", "sluggish HER on disordered Mn oxide / carbon in neutral sulfate (Shan 2019 qualitative)", rng=(120.0, 250.0)),
    tafel_OER_mV_dec=P(150.0, "mV/dec", "ASSUMPTION", "OER on Mn oxide, neutral pH", rng=(100.0, 250.0)),
    float_V_per_cell=P(1.55, "V", "TARGET", "UPS float voltage per cell (below full-charge 1.75 V to limit gassing)", rng=(1.45, 1.65)),
    overcharge_fault_C=P(0.2, "C", "ASSUMPTION", "charger fault: continuous overcharge current", rng=(0.1, 0.5)),
    h2_limit_fraction=P(0.01, "-", "LIT", "1 % H2 by volume = 25 % of the 4 % LFL, the usual battery-room design limit (IEEE 1635 / NFPA 855 practice; verify edition)"),
    case_burst_kPa=P(60.0, "kPa", "ASSUMPTION", "PP-GF monobloc design burst margin", rng=(40.0, 100.0)),
)
