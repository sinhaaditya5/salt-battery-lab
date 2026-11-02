"""Material price ranges for S12/S13 (USD per kg unless noted), triangular (low, mode, high).

Label: [ASSUMPTION] for every row unless a source ID is given. These are deliberately wide.
They are order-of-magnitude bulk prices for battery-grade materials in 2025-26, not quotes.
The sensitivity analysis in S13 shows which of them actually move a conclusion.
"""
PRICE = {
    # salt-literal chemistries
    "NaCl_battery": (0.3, 0.6, 1.5),        # dried, sieved, low-Mg/Ca/SO4 NaCl (industrial salt itself ~0.04-0.10/kg)
    "NaCl_industrial": (0.03, 0.06, 0.12),
    "Ni_powder": (18, 25, 35),              # filamentary Ni (LME Ni ~15/kg + powder premium)
    "Fe_powder": (1.5, 2.5, 5),
    "zebra_additives": (5, 10, 20),         # FeS, NaF, Al, NaI
    "NaAlCl4": (1.5, 2.5, 4),               # NaCl + anhydrous AlCl3
    "beta_alumina": (15, 60, 200),          # finished ceramic part: ~15 at mass scale (technical-ceramic analogue) to 200 at pilot; dominant ZEBRA cost driver
    "Ni_rod": (20, 25, 32),
    "porous_carbon_NaCl": (8, 20, 45),
    "SOCl2_AlCl3": (3, 6, 10),
    "Na_metal": (3, 4, 6),
    "sulfur": (0.1, 0.2, 0.4),
    "graphite_felt": (20, 40, 80),
    # Na-ion
    "Na_layered_oxide": (6, 9, 14), "NFPP": (3.5, 5, 7), "Prussian_white": (4, 6, 10), "NVPF": (12, 18, 30), "NVP": (10, 15, 25),
    "hard_carbon": (5, 8, 15), "NaPF6_carbonate": (5, 8, 12), "birnessite": (2, 3, 5), "NTP": (5, 8, 15), "aqueous_salt": (0.2, 0.4, 1.0),
    "NASICON": (30, 80, 300), "sulfide_SE": (50, 200, 1000), "S_carbon": (1.5, 3, 6), "glyme_NaTFSI": (10, 20, 40), "organic_cam": (5, 15, 40),
    "FeS2": (0.5, 1, 3),
    # other
    "MnO2": (1.5, 2.5, 4), "Zn": (2.5, 3, 4), "KOH_aq": (0.5, 1, 2), "graphite": (1, 3, 6), "chloroaluminate_IL": (10, 30, 80), "Al_metal": (2.5, 3, 4),
    "Mo6S8": (30, 60, 120), "Mg_metal": (3, 4, 6), "Ca_metal": (5, 10, 20), "air_electrode": (20, 50, 120),
    # Li benchmarks
    "NMC811": (18, 24, 32), "LFP": (4, 5, 7), "LiPF6_carbonate": (4, 6, 10), "Li_metal": (40, 80, 150), "Si_C": (15, 30, 60),
    # common
    "electrode_inactive": (8, 12, 20), "Al_foil": (4, 5, 7), "Cu_foil": (10, 12, 15), "SS_foil": (5, 8, 12), "Ni_foil": (25, 35, 50),
    "pouch": (10, 15, 25), "prismatic_can": (5, 8, 12), "cyl_can": (4, 6, 9), "PP_case": (2, 3, 5), "steel_case": (3, 5, 8),
}
# Separator priced per m2 (USD/m2)
SEP_PRICE_M2 = {"PE_sep": (0.3, 0.5, 1.0), "nonwoven": (0.2, 0.4, 0.8), "glass_fibre": (1.0, 3.0, 6.0)}
