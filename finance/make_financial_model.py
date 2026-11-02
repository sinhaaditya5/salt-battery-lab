"""SaltBattery_Financial_Model.xlsx — live-formula model. Inputs (Assumptions sheet) come from
params/product_params.py COST + params/design.py; every input row carries its claim tag and, where
used in investor material, the CLAIMS_LEDGER id. All other sheets are formulas over those inputs.
"""
import pathlib, sys
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB))
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from params.product_params import COST, MAT, P, MODULE48, CABINET, VRLA_REF
import params.design as D
import json

OUT = LAB / "DELIVERABLES" / "1_investor_docs" / "SaltBattery_Financial_Model.xlsx"
HDR = Font(bold=True, color="FFFFFF"); HFILL = PatternFill("solid", fgColor="2A78D6")
INFILL = PatternFill("solid", fgColor="EEF4FC"); NOTE = Font(italic=True, color="52514E", size=9)
thin = Side(style="thin", color="E6E5E1")


def header(ws, row, cols):
    for i, c in enumerate(cols, 1):
        cell = ws.cell(row=row, column=i, value=c); cell.font = HDR; cell.fill = HFILL
        cell.alignment = Alignment(wrap_text=True, vertical="center")


def main():
    wb = Workbook()
    # ---------------- Assumptions ----------------
    A = wb.active; A.title = "Assumptions"
    A["A1"] = "Salt Battery — financial model inputs (blue cells are inputs; change them, everything else recalculates)"; A["A1"].font = Font(bold=True, size=12)
    A["A2"] = "Every value is tagged. No supplier quotations exist; ASSUMPTION values carry low/high ranges. Not investment advice."; A["A2"].font = NOTE
    header(A, 4, ["Key", "Description", "Base", "Low", "High", "Unit", "Tag", "Source / claim id"])
    mb = D.monobloc(); mbt = D.monobloc(80.0)
    es = mb["electrode"]
    A_rows = []
    claim_map = {"lfp_pack": "C-005", "lfp_fire_protection": "C-201"}
    for k, x in COST.items():
        if isinstance(x, P):
            A_rows.append((k, x.source[:90], x.value, x.lo, x.hi, x.unit, x.tag, claim_map.get(k, "params COST")))
    s3 = json.loads((LAB / "sim/s03_r1_cell/out/s03_results.json").read_text())
    f15 = s3["mc"]["40.0"]["4.0"]["p50"] * s3["nominal"]["40.0"]["4.0"]["Vavg"] / s3["nominal"]["40.0"]["0.1"]["Vavg"]
    A_rows += [
        ("block_kWh", "R1 12 V block energy at design point (C/10)", mb["energy_Wh"] / 1000, None, None, "kWh", "CALC", "C-116 params/design.py"),
        ("block_kg", "R1 block mass", mb["mass_kg"], None, None, "kg", "CALC", "params/design.py"),
        ("f15", "Fraction of C/10 energy delivered at 15-min rate (S3 median)", f15, None, None, "-", "SIM", "C-104"),
        ("blocks_per_cabinet", "Blocks per UPS cabinet", CABINET["shelves"] * CABINET["monoblocs_per_shelf"], None, None, "-", "TARGET", "params CABINET"),
        ("cabinet_floor_m2", "Cabinet footprint 0.6 x 0.8 m", 0.48, None, None, "m2", "TARGET", "params CABINET"),
        ("materials_per_block", "Bottom-up materials per block before yield (S9)", None, None, None, "$", "CALC", "C-122 sim/s09_tea"),
        ("vrla_life", "VRLA float life", VRLA_REF["life_years"].value, VRLA_REF["life_years"].lo, VRLA_REF["life_years"].hi, "years", "ASSUMPTION", "params VRLA_REF"),
    ]
    s9 = json.loads((LAB / "sim/s09_tea/out/s09_results.json").read_text())
    names = {}
    for i, r in enumerate(A_rows, start=5):
        k = r[0]
        if k == "materials_per_block":
            r = (k, r[1], sum(s9["monobloc_ups"]["materials_breakdown"].values()), None, None, r[5], r[6], r[7])
        for c, v in enumerate(r, 1):
            cell = A.cell(row=i, column=c, value=v)
            if c == 3:
                cell.fill = INFILL
        names[k] = f"Assumptions!$C${i}"
    for col, w in zip("ABCDEFGH", (24, 70, 12, 10, 10, 14, 12, 26)):
        A.column_dimensions[col].width = w
    n = names  # shorthand
    # ---------------- Unit cost ----------------
    U = wb.create_sheet("Unit_Cost")
    U["A1"] = "R1 12 V block — unit cost and price (formulas)"; U["A1"].font = Font(bold=True, size=12)
    rows = [
        ("Materials per block (after yield)", f"={n['materials_per_block']}/{n['yield_']}"),
        ("Labour per block", f"={n['labour']}"),
        ("Process energy per block", f"={n['energy_kwh_per_kwh']}*{n['block_kWh']}*{n['electricity']}"),
        ("Depreciation per block", f"={n['capex_per_GWh']}*{n['plant_GWh']}/{n['depreciation_years']}/({n['plant_GWh']}*1000000*{n['utilisation']})*{n['block_kWh']}"),
        ("Cash cost per block", "=B3+B4+B5"),
        ("Overhead", f"=B7*{n['overhead_frac']}"),
        ("Total cost per block", "=B7+B8+B6"),
        ("Cost per kWh", f"=B9/{n['block_kWh']}"),
        ("Selling price per block", f"=B9/(1-{n['gross_margin']})"),
        ("Price per kWh", f"=B11/{n['block_kWh']}"),
        ("LFP stationary pack price per kWh [LIT; C-005]", f"={n['lfp_pack']}"),
        ("R1 price / LFP pack price (x)", "=B12/B13"),
    ]
    for i, (lab, f) in enumerate(rows, start=3):
        U.cell(row=i, column=1, value=lab); U.cell(row=i, column=2, value=f).number_format = "#,##0.00"
    U.column_dimensions["A"].width = 50; U.column_dimensions["B"].width = 16
    U["A17"] = "Check vs S9 python model: cost per kWh = " + f"{s9['monobloc_ups']['cost_per_kWh']:.1f}"; U["A17"].font = NOTE
    # ---------------- UPS TCO ----------------
    T = wb.create_sheet("UPS_TCO")
    T["A1"] = "15-year cost per kWh of 15-minute UPS backup (formulas)"; T["A1"].font = Font(bold=True, size=12)
    trows = [
        ("Discount rate", f"={n['discount_rate']}"),
        ("R1 cabinet price per kWh-15min", f"=(Unit_Cost!B9*{n['blocks_per_cabinet']}+{n['cabinet_frame']})/(1-{n['gross_margin']})/({n['blocks_per_cabinet']}*{n['block_kWh']}*{n['f15']})"),
        ("R1 floor cost per kWh-15min", f"={n['floor_cost']}*{n['cabinet_floor_m2']}*{n['clearance_factor']}/({n['blocks_per_cabinet']}*{n['block_kWh']}*{n['f15']})"),
        ("R1 replacement (one, at float life, discounted)", f"=IF({n['r1_float_life_years']}<{n['horizon_years']},B4/(1+B3)^{n['r1_float_life_years']},0)"),
        ("R1 15-yr total", "=B4+B5+B6"),
        ("LFP cabinet installed", f"={n['lfp_ups_cabinet_installed']}"),
        ("LFP fire protection [ASSUMPTION; C-201]", f"={n['lfp_fire_protection']}"),
        ("LFP floor", f"={n['floor_cost']}/{n['lfp_footprint']}"),
        ("LFP replacement", f"=IF({n['lfp_life_years']}<{n['horizon_years']},B8/(1+B3)^{n['lfp_life_years']},0)"),
        ("LFP 15-yr total", "=B8+B9+B10+B11"),
        ("VRLA first install per kWh-15min", f"={n['vrla_installed']}/{n['vrla_15min_fraction']}"),
        ("VRLA replacements (discounted)", f"=B13*(1/(1+B3)^{n['vrla_life']}+IF(2*{n['vrla_life']}<{n['horizon_years']},1/(1+B3)^(2*{n['vrla_life']}),0)+IF(3*{n['vrla_life']}<{n['horizon_years']},1/(1+B3)^(3*{n['vrla_life']}),0))"),
        ("VRLA floor", f"={n['floor_cost']}/({n['vrla_footprint']}*{n['vrla_15min_fraction']})"),
        ("VRLA 15-yr total", "=B13+B14+B15"),
        ("R1 minus LFP (negative = R1 cheaper)", "=B7-B12"),
        ("Li-ion fire-protection cost that would make R1 break even", "=B9+B17"),
    ]
    for i, (lab, f) in enumerate(trows, start=3):
        T.cell(row=i, column=1, value=lab); T.cell(row=i, column=2, value=f).number_format = "#,##0.00"
    T.column_dimensions["A"].width = 58; T.column_dimensions["B"].width = 16
    T["A21"] = (f"Check vs S9 python: R1 {s9['ups_tco_per_kWh15']['R1']:.0f}, LFP {s9['ups_tco_per_kWh15']['LFP']:.0f}, VRLA {s9['ups_tco_per_kWh15']['VRLA']:.0f} "
                "(python VRLA uses the same replacement rule; small differences from rounding)"); T["A21"].font = NOTE
    # ---------------- 5-year plan (only if gates pass) ----------------
    Pn = wb.create_sheet("Plan_5yr")
    Pn["A1"] = "Illustrative 5-year plan IF all week-12 gates pass (scenario, not a forecast)"; Pn["A1"].font = Font(bold=True, size=12)
    header(Pn, 3, ["Line", "Y1", "Y2", "Y3", "Y4", "Y5", "Tag"])
    lines = [("Volume shipped (MWh)", [0, 0.5, 5, 30, 120], "TARGET"),
             ("Price per kWh ($)", ["=Unit_Cost!$B$12*1.6", "=Unit_Cost!$B$12*1.4", "=Unit_Cost!$B$12*1.2", "=Unit_Cost!$B$12*1.1", "=Unit_Cost!$B$12"], "CALC (pilot premium declining to scale price)"),
             ("Cost per kWh ($)", ["=Unit_Cost!$B$10*2.5", "=Unit_Cost!$B$10*2.0", "=Unit_Cost!$B$10*1.5", "=Unit_Cost!$B$10*1.2", "=Unit_Cost!$B$10"], "CALC (sub-scale penalty)"),
             ("Revenue ($k)", None, "CALC"), ("COGS ($k)", None, "CALC"), ("Gross profit ($k)", None, "CALC"),
             ("Team & opex ($k)", [450, 1200, 2500, 4500, 7000], "ASSUMPTION"),
             ("Testing & certification ($k)", [60, 250, 400, 300, 300], "ASSUMPTION"),
             ("Capex ($k)", [100, 2000, 8000, 0, 20000], "ASSUMPTION (pilot, demo, plant)"),
             ("Free cash flow ($k)", None, "CALC"), ("Cumulative cash need ($k)", None, "CALC")]
    for i, (lab, vals, tag) in enumerate(lines, start=4):
        Pn.cell(row=i, column=1, value=lab); Pn.cell(row=i, column=7, value=tag)
        for j in range(5):
            col = get_column_letter(j + 2)
            if vals is not None:
                Pn.cell(row=i, column=j + 2, value=vals[j])
            elif lab.startswith("Revenue"):
                Pn.cell(row=i, column=j + 2, value=f"={col}4*{col}5")
            elif lab.startswith("COGS"):
                Pn.cell(row=i, column=j + 2, value=f"={col}4*{col}6")
            elif lab.startswith("Gross"):
                Pn.cell(row=i, column=j + 2, value=f"={col}7-{col}8")
            elif lab.startswith("Free"):
                Pn.cell(row=i, column=j + 2, value=f"={col}9-{col}10-{col}11-{col}12")
            elif lab.startswith("Cumulative"):
                Pn.cell(row=i, column=j + 2, value=f"=MIN(0,{col}13)" if j == 0 else f"={get_column_letter(j+1)}14+{col}13")
            Pn.cell(row=i, column=j + 2).number_format = "#,##0"
    Pn.column_dimensions["A"].width = 30; Pn.column_dimensions["G"].width = 40
    Pn["A16"] = "Reading: even at target volumes the cell business needs tens of $M of capital before gross profit covers opex — the reason the memo says no-go until K1–K6 pass."; Pn["A16"].font = NOTE
    # ---------------- Use of funds ----------------
    F = wb.create_sheet("Use_of_Funds")
    F["A1"] = "Use of a $500k YC-standard investment [LIT; C-208] over 18 months (plan)"; F["A1"].font = Font(bold=True, size=12)
    header(F, 3, ["Item", "$k", "Share", "Conditional on gate"])
    uf = [("Partner-lab work: synthesis, characterisation, cells", 110, "K4"), ("Electrochemist co-founder / staff (12 mo)", 120, "K4"),
          ("Fire & safety testing (UL 9540A cell/unit, gas)", 90, "K1-K3"), ("Equipment: cycler channels, gas/pressure rig", 50, "K4"),
          ("BMS + monobloc prototypes", 40, "K1-K3"), ("Customer pilots, travel, HMA/code consultant", 40, "none"), ("Founder runway + contingency", 50, "none")]
    for i, (a, b, g) in enumerate(uf, start=4):
        F.cell(row=i, column=1, value=a); F.cell(row=i, column=2, value=b); F.cell(row=i, column=3, value=f"=B{i}/SUM($B$4:$B$10)").number_format = "0%"
        F.cell(row=i, column=4, value=g)
    F.cell(row=11, column=1, value="Total"); F.cell(row=11, column=2, value="=SUM(B4:B10)")
    F.column_dimensions["A"].width = 52; F.column_dimensions["D"].width = 20
    # ---------------- Claims ----------------
    C = wb.create_sheet("Claims_Ledger")
    import csv
    for i, row in enumerate(csv.reader(open(LAB / "CLAIMS_LEDGER.csv")), start=1):
        for jx, v in enumerate(row, 1):
            C.cell(row=i, column=jx, value=v)
    for col, w in zip("ABCDEFGH", (8, 70, 11, 22, 12, 50, 10, 30)):
        C.column_dimensions[col].width = w
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
