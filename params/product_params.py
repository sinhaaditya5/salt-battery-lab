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
