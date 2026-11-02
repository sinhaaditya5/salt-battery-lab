#!/usr/bin/env python3
"""R0 prototype cost model. Requires real quotes, yields and test results.

Costs are reported per prototype cell, nominal kWh and lifetime delivered kWh.
This is not a factory-scale forecast; add module, BMS, enclosure, certification,
factory CAPEX, depreciation, logistics and working capital for commercial COGS.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

REQUIRED = [
    "accepted_active_powder_yield_g_per_batch", "precursor_chemicals_cost_inr_per_batch",
    "powder_processing_cost_inr_per_batch", "characterization_cost_inr_per_batch",
    "cell_assembly_labour_cost_inr_per_batch", "batch_cells_planned",
    "carbon_black_cost_inr_per_g", "carbon_paper_disc_cost_inr", "separator_disc_cost_inr",
    "electrolyte_cost_inr_per_ml", "test_fixture_cost_inr", "fixture_reuse_cycles",
    "other_components_cost_inr_per_cell", "assembly_labour_cost_inr_per_cell",
    "scrap_fraction", "measured_discharge_energy_Wh_per_cell", "measured_cycles_to_end_of_life",
    "measured_average_depth_of_discharge_fraction", "measured_round_trip_energy_efficiency_fraction"
]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("inputs_json", type=Path)
    p.add_argument("--electrolyte-ml-per-cell", type=float, default=0.150)
    p.add_argument("--electrodes-per-cell", type=int, default=2)
    args = p.parse_args()
    d = json.loads(args.inputs_json.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if d.get(k) is None]
    if missing:
        raise SystemExit("Cost model not run: enter actual values for: " + ", ".join(missing))
    vals = {k: float(d[k]) for k in REQUIRED}
    if not 0 <= vals["scrap_fraction"] < 1:
        raise SystemExit("scrap_fraction must be [0,1)")
    for k, v in vals.items():
        if k != "scrap_fraction" and v < 0:
            raise SystemExit(f"{k} cannot be negative")
    if vals["batch_cells_planned"] <= 0 or vals["fixture_reuse_cycles"] <= 0:
        raise SystemExit("batch_cells_planned and fixture_reuse_cycles must be positive")
    if vals["accepted_active_powder_yield_g_per_batch"] <= 0:
        raise SystemExit("accepted_active_powder_yield_g_per_batch must be positive")
    if vals["measured_discharge_energy_Wh_per_cell"] <= 0 or vals["measured_cycles_to_end_of_life"] <= 0:
        raise SystemExit("Measured cell energy and cycles to end-of-life must be positive")
    if not 0 <= vals["measured_average_depth_of_discharge_fraction"] <= 1:
        raise SystemExit("Depth of discharge must lie in [0,1]")
    if not 0 <= vals["measured_round_trip_energy_efficiency_fraction"] <= 1:
        raise SystemExit("Round-trip energy efficiency must lie in [0,1]")

    good_cells = vals["batch_cells_planned"] * (1 - vals["scrap_fraction"])
    powder_cost_g = (vals["precursor_chemicals_cost_inr_per_batch"] +
                     vals["powder_processing_cost_inr_per_batch"] +
                     vals["characterization_cost_inr_per_batch"]) / vals["accepted_active_powder_yield_g_per_batch"]
    active_cost = powder_cost_g * float(d["active_material_g_per_cell_both_electrodes"])
    batch_conversion_per_cell = vals["cell_assembly_labour_cost_inr_per_batch"] / good_cells
    carbon_cost = float(d["carbon_black_g_per_cell"]) * vals["carbon_black_cost_inr_per_g"]
    collector_cost = args.electrodes_per_cell * vals["carbon_paper_disc_cost_inr"]
    separator_cost = vals["separator_disc_cost_inr"]
    electrolyte_cost = args.electrolyte_ml_per_cell * vals["electrolyte_cost_inr_per_ml"]
    fixture_cost = vals["test_fixture_cost_inr"] / vals["fixture_reuse_cycles"]
    assembly_cost = vals["other_components_cost_inr_per_cell"] + vals["assembly_labour_cost_inr_per_cell"]
    cell_cost = active_cost + batch_conversion_per_cell + carbon_cost + collector_cost + separator_cost + electrolyte_cost + fixture_cost + assembly_cost

    usable_energy_kwh = vals["measured_discharge_energy_Wh_per_cell"] / 1000.0
    nominal_cost_per_kwh = cell_cost / usable_energy_kwh
    lifetime_throughput_kwh = (usable_energy_kwh * vals["measured_cycles_to_end_of_life"] *
                               vals["measured_average_depth_of_discharge_fraction"] *
                               vals["measured_round_trip_energy_efficiency_fraction"])
    lifetime_cost_per_kwh = cell_cost / lifetime_throughput_kwh if lifetime_throughput_kwh > 0 else math.inf

    print("R0 COST MODEL — BASED ON USER-ENTERED ACTUALS")
    for name, value in [
        ("Active powder cost allocated per cell", active_cost),
        ("Batch conversion/assembly labour per cell", batch_conversion_per_cell),
        ("Carbon black per cell", carbon_cost),
        ("Carbon-paper collectors per cell", collector_cost),
        ("Separator per cell", separator_cost),
        ("Electrolyte per cell", electrolyte_cost),
        ("Reusable test fixture amortisation per cell", fixture_cost),
        ("Other components + cell assembly labour", assembly_cost),
        ("Prototype cell estimated cost", cell_cost),
        ("Cost per measured nominal kWh", nominal_cost_per_kwh),
        ("Lifetime-delivered energy per cell (kWh)", lifetime_throughput_kwh),
        ("Cost per lifetime-delivered kWh", lifetime_cost_per_kwh),
    ]:
        print(f"{name:55s} INR {value:,.2f}")
    print("\nNOT factory COGS: excludes factory CAPEX/depreciation, BMS, module/pack enclosure, thermal controls, certification, logistics, warranty and tax.")

if __name__ == "__main__":
    main()
