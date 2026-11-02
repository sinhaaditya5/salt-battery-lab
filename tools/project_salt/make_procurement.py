#!/usr/bin/env python3
"""Generate PROJECT_SALT/06_PROCUREMENT/*.csv for the S-cell R0 campaign from params/scell_params.py.

Campaign (16 ceramic sub-assemblies): 4 seal-qualification dummies (QT-02/03), 3 cells x 30 mAh/cm2 (replication, G1),
3 x 60 and 3 x 100 mAh/cm2 with 1.0 mm discs (G2), 3 x 100 mAh/cm2 with 0.5 mm discs (G4). Chemical quantities include a
x3 process allowance (drying losses, granulation fines, failed batches) [ASSUMPTION].

Rules followed (brief §8.1): no invented catalogue numbers or prices. 'catalogue' says VERIFY where it was not checked online
in this session; 'price' says QUOTE REQUIRED unless a published price was seen. A separate budget column is an [ASSUMPTION]
for planning only and is labelled as such.
"""
import csv, sys
from pathlib import Path
LAB = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(LAB))
from params.scell_params import CELL, cathode_charge  # noqa: E402
OUT = LAB / "PROJECT_SALT" / "06_PROCUREMENT"; OUT.mkdir(parents=True, exist_ok=True)

CELLS = {30: 3, 60: 3, 100: 6}; DUMMIES = 4; ALLOW = 3.0
tot = {k: 0.0 for k in ("NaCl_g", "Fe_g", "Ni_g", "FeS_g", "NaF_g", "NaI_g", "Al_g", "AlCl3_for_melt_g", "NaCl_for_melt_g")}
for qa, n in CELLS.items():
    ch = cathode_charge(qa)
    for k in tot: tot[k] += ch[k] * n
q = {k: round(v * ALLOW, 1) for k, v in tot.items()}
n_sub = sum(CELLS.values()) + DUMMIES

# id, component, identity, CAS, grade, qty, unit, step, india supplier, us supplier, catalogue, price, alternative, hazard (GHS), budget_inr [ASSUMPTION]
ROWS = [
 ("PS-C-01", "Sodium chloride (cathode + melt)", "NaCl", "7647-14-5", ">=99.9 %, anhydrous, low Ca/Mg/K/SO4 (<50-100 ppm)", round(q["NaCl_g"] + q["NaCl_for_melt_g"] + 50, 0), "g", "B-02, B-04",
  "Merck Life Science (Sigma-Aldrich), India", "MilliporeSigma (Sigma-Aldrich), USA", "VERIFY (trace-metals-basis grade)", "QUOTE REQUIRED", "Thermo Fisher (Alfa Aesar) Puratronic", "Not classified", 8000),
 ("PS-C-02", "Iron powder", "Fe", "7439-89-6", ">=99.5 %, 3-10 um, low O (H2-reduced)", round(q["Fe_g"] + 20, 0), "g", "B-03",
  "Merck / Thermo Fisher India", "MilliporeSigma; Thermo Fisher; American Elements", "VERIFY", "QUOTE REQUIRED", "Carbonyl iron powder (BASF CIP) if O spec met", "Flam. Sol. 1 if fine powder; store under Ar", 6000),
 ("PS-C-03", "Nickel powder (10 mol% of metal)", "Ni", "7440-02-0", ">=99.7 %, filamentary (Type-255-like) or <10 um", round(q["Ni_g"] + 10, 0), "g", "B-03",
  "Merck / Thermo Fisher India", "MilliporeSigma; Vale/Novamet distributors", "VERIFY", "QUOTE REQUIRED", "Ni nanopowder (higher O)", "Carc. 2, Skin Sens. 1, STOT RE 1 - handle in glovebox", 6000),
 ("PS-C-04", "Iron(II) sulfide (S additive)", "FeS", "1317-37-9", ">=99.9 % metals basis, powder", max(5, round(q["FeS_g"], 0)), "g", "B-03",
  "Thermo Fisher India; TCI India", "Thermo Fisher (Alfa Aesar); Strem/Ascensus", "VERIFY", "QUOTE REQUIRED", "elemental S + Fe in situ (patent check: PS-007)", "Releases H2S with acid", 4000),
 ("PS-C-05", "Sodium fluoride", "NaF", "7681-49-4", ">=99.99 % trace metals", 10, "g", "B-03", "Merck India", "MilliporeSigma", "VERIFY", "QUOTE REQUIRED", "-", "Acute Tox. 3 (oral)", 3000),
 ("PS-C-06", "Sodium iodide", "NaI", "7681-82-5", ">=99.99 %, anhydrous", 10, "g", "B-03", "Merck India", "MilliporeSigma", "VERIFY", "QUOTE REQUIRED", "omit in first replication if unavailable", "Eye/skin irritant", 3000),
 ("PS-C-07", "Aluminium powder (priming Na source)", "Al", "7429-90-5", ">=99.5 %, -325 mesh", 10, "g", "B-03", "Merck / Thermo Fisher India", "MilliporeSigma; Thermo Fisher",
  "VERIFY", "QUOTE REQUIRED", "-", "Flam. Sol. 1; water-reactive (H2)", 3000),
 ("PS-C-08", "Aluminium chloride, anhydrous (for NaAlCl4)", "AlCl3", "7446-70-0", ">=99.99 % (sublimed), sealed ampoules/bottles under Ar", round(q["AlCl3_for_melt_g"] + 50, 0), "g", "B-04",
  "Merck India; Thermo Fisher India", "MilliporeSigma; Thermo Fisher", "VERIFY", "QUOTE REQUIRED", "Pre-made NaAlCl4 (quote)", "Skin Corr. 1B; reacts violently with water -> HCl", 12000),
 ("PS-C-09", "Sodium tetrachloroaluminate (made in-house from C-01 + C-08)", "NaAlCl4", "7784-16-9", "melt-filtered, Al-treated", round(q["AlCl3_for_melt_g"] * 1.44, 1), "g", "B-04, D-06",
  "made in lab (step B-04)", "made in lab (step B-04)", "n/a", "n/a", "commercial NaAlCl4 (rare; quote)", "Skin Corr.; HCl on hydrolysis", 0),
 ("PS-M-01", f"beta''-alumina disc, OD {CELL['disc_d_mm']} mm, t 1.0 mm (12) and 0.5 mm (4)", "Na2O-(Li2O/MgO)-stabilised beta''-Al2O3", "1302-74-5 (Na beta-alumina)",
  "sigma >= 0.1 S/cm at 300 C; density >= 98 %; lapped faces", n_sub, "pcs", "C-01",
  "ARCI Hyderabad NBA programme (enquire; PS-031 unverified)", "Ionotec Ltd (UK) - enquire; MSE Supplies powder PS-035 + partner sintering", "QUOTE REQUIRED", "QUOTE REQUIRED",
  "Sinter from powder at partner lab (adds 4-6 weeks)", "Dust: STOT RE (alumina); no special hazard as sintered part", 400000),
 ("PS-M-02", "alpha-alumina insulating ring, OD 42 / ID 26 / t 4 mm, counterbore 30.4 x disc t", "Al2O3 >= 99.5 %", "1344-28-1", "ground faces flat 0.02", n_sub, "pcs", "C-01",
  "Technical-ceramic machinists (quote): e.g. Bangalore/Pune ceramic shops", "CoorsTek; Ceramco; McMaster-Carr blanks + machining", "custom drawing SB-SC-001 item 2", "QUOTE REQUIRED", "Zirconia-toughened alumina", "None", 160000),
 ("PS-M-03", "Sealing glass (beta''-to-alpha alumina), CTE-matched ~7-8 ppm/K", "aluminoborosilicate sealing glass (frit/paste)", "-", "chloroaluminate-resistant; seal T 900-1050 C", 50, "g", "C-02",
  "quote via SCHOTT India / partner lab stock", "SCHOTT; Ferro/Vibrantz sealing glasses", "VERIFY grade with supplier", "QUOTE REQUIRED", "Partner lab's qualified seal glass", "Dust irritant", 30000),
 ("PS-M-04", "Graphite foil gasket, 0.5 mm, punched OD 42 / ID 27", "flexible graphite, >=98 % C, low S/Cl", "7782-42-5", "nuclear/high-purity grade", 2 * n_sub + 8, "pcs", "D-03, D-08",
  "Gasket makers (quote)", "McMaster-Carr flexible graphite sheet; Mersen", "VERIFY", "QUOTE REQUIRED", "Alternative candidates for QT-04/07: Al2O3 felt + mica", "None", 15000),
 ("PS-M-05", "Cathode housing, Ni 201, machined per SB-SC-001 item 5", "Ni 201 (UNS N02201)", "-", "ISO 2768-mK; sealing face flat 0.02 Ra 0.8", n_sub - DUMMIES, "pcs", "D-03",
  "Precision machinists (quote)", "Machined from McMaster-Carr Ni 200/201 bar (quote)", "custom", "QUOTE REQUIRED", "Mo-lined SS 316L (if QT-05 shows Ni loss)", "None", 240000),
 ("PS-M-06", "Mo mesh disc 23.8 mm (cathode current collector)", "Mo >= 99.9 %", "7439-98-7", "40-60 mesh", n_sub, "pcs", "D-05", "Goodfellow India / Alfa Aesar India", "Goodfellow; Thermo Fisher",
  "VERIFY", "QUOTE REQUIRED", "Ni mesh (with Ni-plateau caveat)", "None", 30000),
 ("PS-M-07", "Mo wave spring / Mo foil spring", "Mo", "7439-98-7", "free height >= gap + 0.5 mm", n_sub, "pcs", "D-05", "custom (quote)", "custom (quote) / Smalley-type wave springs in Mo on request",
  "custom", "QUOTE REQUIRED", "Ni felt compression pad", "None", 30000),
 ("PS-M-08", "Ni 201 tube 1/8 in OD x 0.024 in wall (fill tube, TC well)", "Ni 201", "-", "seamless", 2, "m", "D-02", "Swagelok/Hylok India distributors", "McMaster-Carr; Swagelok", "VERIFY", "QUOTE REQUIRED", "-", "None", 15000),
 ("PS-M-09", "Anode housing, SS 316L, machined per SB-SC-001 item 12", "SS 316L", "-", "ISO 2768-mK", n_sub - DUMMIES, "pcs", "D-03", "Precision machinists (quote)", "Machined (quote)", "custom", "QUOTE REQUIRED", "-", "None", 120000),
 ("PS-M-10", "SS 316L mesh 100 mesh + 0.1 mm shim (anode wick)", "SS 316L", "-", "-", 0.1, "m2", "D-04", "Wire-mesh suppliers (quote)", "McMaster-Carr", "VERIFY", "QUOTE REQUIRED", "Ni mesh", "None", 5000),
 ("PS-M-11", "Bolts M4x30 ISO 4762 A4-70 + nuts + Belleville washers", "SS 316", "-", "A4-70", 6 * n_sub, "sets", "D-08", "Local fastener suppliers", "McMaster-Carr", "VERIFY", "published (McMaster) - not checked", "-", "None", 8000),
 ("PS-M-12", "alpha-alumina sleeve OD 6 / ID 4.2 x 5 mm", "Al2O3 99.5 %", "1344-28-1", "-", 6 * n_sub, "pcs", "D-08", "Ceramic tube suppliers (quote)", "McMaster-Carr alumina tube + cut", "VERIFY", "QUOTE REQUIRED", "Mica tube", "None", 10000),
 ("PS-M-13", "Mica washers 0.3 mm, ID 4.2 / OD 9", "muscovite/phlogopite", "12001-26-2", "-", 6 * n_sub, "pcs", "D-08", "Local electrical insulation suppliers", "McMaster-Carr", "VERIFY", "QUOTE REQUIRED", "-", "None", 3000),
 ("PS-E-01", "Type-K thermocouple, mineral-insulated, UNGROUNDED junction, 1.5 mm Inconel sheath, 300 mm", "-", "-", "Class 1 (IEC 60584)", 4 * 4, "pcs", "E-02",
  "Tempsens Instruments (India) - quote", "Omega Engineering; Watlow", "VERIFY", "QUOTE REQUIRED", "-", "None", 40000),
 ("PS-E-02", "SCM-1 monitor PCB assembled (pcb/scell_monitor)", "see fab/scell_monitor-bom.csv", "-", "after layout is finished and DRC-clean", 2, "pcs", "E-01",
  "PCB assembly houses in India (quote)", "JLCPCB/PCBWay/MacroFab (quote)", "fab files", "QUOTE REQUIRED", "Lab DAQ + standalone over-temperature controller", "None", 60000),
 ("PS-E-03", "Zero-cross SSR (DC control, 25 A) + bimetal cut-out 300 C + E-stop with aux NC", "-", "-", "-", 2, "sets", "E-04", "Industrial electrical distributors", "Grainger; McMaster-Carr", "VERIFY",
  "QUOTE REQUIRED", "-", "None", 15000),
 ("PS-G-01", "Argon 5.0 (glovebox purge, furnace)", "Ar", "7440-37-1", ">=99.999 %", 4, "cylinders (47 L)", "A-03", "Linde India / Air Liquide India / INOX Air Products", "Airgas; Linde", "n/a",
  "QUOTE REQUIRED", "-", "Compressed gas; asphyxiant", 20000),
]
cols = ["item", "component", "chemical_or_material_identity", "CAS", "grade_spec", "quantity", "unit", "build_step", "india_supplier", "usa_supplier",
        "catalogue_number", "price", "alternative", "hazard_GHS", "budget_INR_[ASSUMPTION]"]
with open(OUT / "master_bom.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(cols); w.writerows(ROWS)
for region, idx in (("india", 8), ("usa", 9)):
    with open(OUT / f"{region}_suppliers.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["item", "component", "supplier", "catalogue_number", "price", "verification"])
        for r in ROWS:
            w.writerow([r[0], r[1], r[idx], r[10], r[11], "named supplier exists; product/SKU/price NOT verified online this session" if "VERIFY" in r[10] or "QUOTE" in r[11] else "n/a"])
EQUIP = [  # tier, item, critical spec, qty, owner (buy vs partner), price source, alternative
 ("lab", "Ar glovebox with purifier, H2O/O2 < 1 ppm, with heated well/antechamber", "integrated well furnace to 300 C or feed-through to adjacent furnace", 1, "PARTNER LAB (do not buy)", "QUOTE REQUIRED", "Sealed-transfer to furnace in a dry room"),
 ("lab", "Battery cycler / potentiostat with EIS, 4+ channels, +/-1 A, 5 V", "EIS 10 mHz-100 kHz on >=1 channel; aux T input", 1, "PARTNER LAB", "QUOTE REQUIRED", "Neware BTS4000 (cycling) + borrowed EIS"),
 ("lab", "Programmable box/tube furnace, 25-350 C, +/-1 C, inert atmosphere, ramp <=2 C/min", "independent over-temperature controller", 2, "PARTNER LAB or buy", "QUOTE REQUIRED", "Lab oven + Ar purge box (only with QT-08 passed)"),
 ("lab", "Glass-sealing furnace to 1100 C, controlled atmosphere", "for C-02 disc-to-ring seal", 1, "PARTNER LAB / ceramic vendor", "QUOTE REQUIRED", "Buy pre-sealed sub-assemblies"),
 ("lab", "Helium leak detector, <=1e-9 mbar.L/s", "QT-02", 1, "PARTNER / service", "QUOTE REQUIRED", "Pressure-decay test (lower sensitivity)"),
 ("lab", "Planetary ball mill, ZrO2 jars, glovebox-compatible", "B-03 mixing", 1, "PARTNER LAB", "QUOTE REQUIRED", "Agate mortar for <5 g batches"),
 ("lab", "Hydraulic press 10 t + 13/25 mm dies; sieve set 125-425 um", "granulation B-05", 1, "PARTNER LAB", "QUOTE REQUIRED", "-"),
 ("lab", "Vacuum oven 250 C", "salt drying B-02", 1, "PARTNER LAB", "QUOTE REQUIRED", "-"),
 ("lab", "Karl Fischer coulometric titrator", "QT-06 moisture", 1, "PARTNER LAB", "QUOTE REQUIRED", "-"),
 ("lab", "Torque screwdriver 0.5-3 N.m; crimp tool for 1/8 in tube; micro-TIG or laser weld service", "D-08, D-10", 1, "buy small tools", "QUOTE REQUIRED", "-"),
 ("lab", "HCl gas detector (fixed + personal), Class D extinguisher, dry sand, face shield, Nitrile/Neoprene gloves", "safety", 1, "BUY", "QUOTE REQUIRED", "-"),
 ("lab", "Characterisation access: XRD, SEM-EDS, ICP-OES, impedance", "QT-01, failure analysis", 1, "PARTNER LAB", "per-sample fees (quote)", "-"),
 ("pilot", "Beta''-alumina forming + sintering (isostatic press or tape cast, 1600 C kiln)", "only if make-vs-buy favours make", 1, "DEFER until G4 passes", "QUOTE REQUIRED", "Buy discs from ceramic supplier"),
 ("pilot", "Dry room (dew point <= -40 C) 30-50 m2 with granulator, cell assembly, TIG/laser welding cells", "Stage B", 1, "DEFER", "QUOTE REQUIRED", "-"),
 ("pilot", "Formation racks with heated enclosures (190-300 C), 50-100 channels", "Stage B", 1, "DEFER", "QUOTE REQUIRED", "-"),
 ("industrial", "See 08_MANUFACTURING/industrial_line and 10_ECONOMICS/factory_capex (scenario model, not a plan)", "-", 0, "DEFER", "model", "-"),
]
with open(OUT / "equipment_bom.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["tier", "item", "critical_spec", "qty", "acquire_how", "price_source", "alternative"]); w.writerows(EQUIP)
print("procurement written:", n_sub, "sub-assemblies;", {k: q[k] for k in ("NaCl_g", "Fe_g", "Ni_g", "AlCl3_for_melt_g")})
print("budget (ASSUMPTION) INR:", sum(r[14] for r in ROWS))
