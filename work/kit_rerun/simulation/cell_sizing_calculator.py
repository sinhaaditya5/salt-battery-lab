#!/usr/bin/env python3
"""Transparent arithmetic for the published Na0.27MnO2 R0 reference.

This calculator estimates reagent quantities from published stoichiometry and
reported electrode loading. It does NOT predict electrochemical performance,
yield, purity, or safety. All precursor yields are theoretical upper bounds.
"""
from __future__ import annotations
import argparse

MW = {
    "MnCl2_4H2O": 197.91,  # g/mol
    "Mn3O4": 228.81,      # g/mol
    "NaOH": 39.997,       # g/mol
    "Na2SO4": 142.04,     # g/mol
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mncl2-g", type=float, default=0.700,
                   help="MnCl2·4H2O input to precursor synthesis, grams (paper: 0.700)")
    p.add_argument("--mn3o4-mg", type=float, default=100.0,
                   help="Mn3O4 mass in one Na-insertion batch, mg (paper: 100)")
    p.add_argument("--naoh-ratio", type=float, default=4.0,
                   help="NaOH:Mn3O4 molar ratio for Na-birnessite synthesis (screen 0.5,1,1.5,2,4)")
    p.add_argument("--cells", type=int, default=3,
                   help="Number of symmetric cells to plan for")
    p.add_argument("--active-mg-per-electrode", type=float, default=5.0)
    p.add_argument("--carbon-ratio", type=float, default=4.0,
                   help="Active-material:carbon-black mass ratio (paper: 4:1)")
    p.add_argument("--electrolyte-molarity", type=float, default=1.0)
    p.add_argument("--electrolyte-ul-per-cell", type=float, default=150.0)
    args = p.parse_args()

    if min(args.mncl2_g, args.mn3o4_mg, args.naoh_ratio, args.cells,
           args.active_mg_per_electrode, args.carbon_ratio,
           args.electrolyte_molarity, args.electrolyte_ul_per_cell) <= 0:
        p.error("All inputs must be positive.")

    mn_mol = args.mncl2_g / MW["MnCl2_4H2O"]
    theoretical_mn3o4_g = (mn_mol / 3.0) * MW["Mn3O4"]
    precursor_naoh_solution_ml = 0.167 * 50.0
    precursor_naoh_g = precursor_naoh_solution_ml * 0.123

    mn3o4_g = args.mn3o4_mg / 1000.0
    naoh_mol = args.naoh_ratio * (mn3o4_g / MW["Mn3O4"])
    naoh_g = naoh_mol * MW["NaOH"]

    active_per_cell_mg = 2 * args.active_mg_per_electrode
    carbon_per_electrode_mg = args.active_mg_per_electrode / args.carbon_ratio
    carbon_per_cell_mg = 2 * carbon_per_electrode_mg
    electrolyte_l_per_cell = args.electrolyte_ul_per_cell * 1e-6
    na2so4_g_per_l = args.electrolyte_molarity * MW["Na2SO4"]
    na2so4_g_per_cell = na2so4_g_per_l * electrolyte_l_per_cell

    print("R0 REFERENCE CELL — QUANTITY CALCULATOR")
    print("This is arithmetic only; not a yield or performance prediction.\n")
    print(f"MnCl2·4H2O input:                  {args.mncl2_g:.4f} g")
    print(f"Theoretical maximum Mn3O4:         {theoretical_mn3o4_g:.4f} g")
    print(f"Reported precursor NaOH solution:  {precursor_naoh_solution_ml:.3f} mL")
    print(f"NaOH mass in that solution:        {precursor_naoh_g:.4f} g (calculated)")
    print()
    print(f"Na-insertion batch Mn3O4:          {args.mn3o4_mg:.2f} mg")
    print(f"NaOH:Mn3O4 molar ratio:            {args.naoh_ratio:g}:1")
    print(f"NaOH for this batch:               {naoh_g * 1000:.2f} mg (calculated)")
    print()
    print(f"Cell count:                        {args.cells}")
    print(f"Active material per cell:          {active_per_cell_mg:.2f} mg total across both electrodes")
    print(f"Carbon black per cell:             {carbon_per_cell_mg:.2f} mg total across both electrodes")
    print(f"Total active material for cells:   {active_per_cell_mg * args.cells:.2f} mg")
    print(f"Total carbon black for cells:      {carbon_per_cell_mg * args.cells:.2f} mg")
    print(f"Na2SO4 per cell:                   {na2so4_g_per_cell * 1000:.3f} mg contained in electrolyte")
    print(f"Electrolyte volume for cells:      {args.electrolyte_ul_per_cell * args.cells:.1f} µL")
    print(f"Na2SO4 for cells only:             {na2so4_g_per_cell * args.cells:.4f} g")
    print(f"Na2SO4 for 100 mL stock:           {na2so4_g_per_l * 0.1:.4f} g")
    print("\nImportant: reported paper does not specify the full-cell slurry solvent/solids fraction or all separator/fixture dimensions.")
    print("Do not treat these quantities as an order-ready kit until the facility closes those method gaps.")
    print("Never substitute NaCl/table salt for Na2SO4.")

if __name__ == "__main__":
    main()
