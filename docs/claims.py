"""Claims ledger: every number used in investor material is built here from params / simulation
outputs / research/sources.csv, with one tag and an ID. Documents call `C.txt(id)` to print a
value with its tag and ID, which records where it was used; `write_ledger()` writes CLAIMS_LEDGER.csv.

Tags: LIT, VENDOR, CALC, SIM, ASSUMPTION, TARGET. MEASURED is forbidden (no lab data exists).
"""
from __future__ import annotations
import csv, json, pathlib, sys
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
sys.path.insert(0, str(LAB))
from params.product_params import COST, MAT, R0, R0_LOADING_MG_CM2, MONOBLOC

TAGS = {"LIT", "VENDOR", "CALC", "SIM", "ASSUMPTION", "TARGET"}


def j(rel):
    p = LAB / rel
    return json.loads(p.read_text()) if p.exists() else {}


class Ledger:
    def __init__(self):
        self.rows = {}
        self.used = {}

    def add(self, cid, text, tag, value, unit, source, confidence="medium"):
        assert tag in TAGS, (cid, tag)
        self.rows[cid] = dict(id=cid, claim=text, tag=tag, value=value, unit=unit, source=source, confidence=confidence)

    def v(self, cid):
        return self.rows[cid]["value"]

    def txt(self, cid, where="", fmt=None, with_unit=True):
        r = self.rows[cid]
        if where:
            self.used.setdefault(cid, set()).add(where)
        val = r["value"] if fmt is None else fmt.format(r["value"])
        u = f" {r['unit']}" if with_unit and r["unit"] and r["unit"] != "-" else ""
        return f"{val}{u} [{r['tag']}; {cid}]"

    def tag(self, cid, where=""):
        if where:
            self.used.setdefault(cid, set()).add(where)
        return f"[{self.rows[cid]['tag']}; {cid}]"

    def write(self, path=LAB / "CLAIMS_LEDGER.csv"):
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "claim text", "tag", "value", "unit", "source/evidence file", "confidence", "where used"])
            for cid, r in self.rows.items():
                w.writerow([cid, r["claim"], r["tag"], r["value"], r["unit"], r["source"], r["confidence"],
                            "; ".join(sorted(self.used.get(cid, [])))])
        return path


def build() -> Ledger:
    L = Ledger()
    s1 = j("sim/s01_kit_rerun/out/s1_comparison.json"); s2 = j("sim/s02_pybamm_validation/out/s02_validation.json")
    s3 = j("sim/s03_r1_cell/out/s03_results.json"); s4 = j("sim/s04_gas/out/s04_results.json")
    s5 = j("sim/s05_atomistic/out/s05_summary.json"); s7 = j("sim/s07_buildup/out/s07_results.json")
    s8 = j("sim/s08_thermal/out/s08_results.json"); s9 = j("sim/s09_tea/out/s09_results.json")
    s10 = j("sim/s10_market/out/s10_results.json")
    # ---------------- literature / vendor -------------------------------------------------
    L.add("C-001", "Reference cell capacity after 5,000 cycles at 1 A/g (electrode-material basis, denominator ambiguous)", "LIT", 83, "mAh/g", "Shan et al., Nat. Commun. 10, 4975 (2019)", "high")
    L.add("C-002", "Reference electrode loading (5 mg on a 15 mm disc)", "CALC", round(R0_LOADING_MG_CM2, 1), "mg/cm2", "params R0; kit spec 5.1", "high")
    L.add("C-003", "Commercial electrode loading range", "ASSUMPTION", "15-25", "mg/cm2", "mission brief; typical Li-ion electrodes", "medium")
    L.add("C-004", "Thermodynamic water stability window", "LIT", 1.23, "V", "standard thermodynamics", "high")
    L.add("C-005", "Stationary-storage Li-ion pack average price 2025", "LIT", 70, "$/kWh", "BNEF 2025 via energy-storage.news; research/sources.csv SRC-104/105", "high")
    L.add("C-006", "Lowest observed LFP cell price 2025", "LIT", 36, "$/kWh", "BNEF 2025 (snippet) SRC-108", "medium")
    L.add("C-007", "IFC 2024 permit threshold, lithium-ion", "LIT", 20, "kWh", "IFC 2024 Table 1207.1.3 via Clark County guide, SRC-080", "high")
    L.add("C-008", "IFC 2024 permit threshold, 'other battery technologies' (an unlisted aqueous Na chemistry)", "LIT", 3, "kWh", "SRC-081", "high")
    L.add("C-009", "IFC 2024 permit threshold, lead-acid and Zn-MnO2", "LIT", 70, "kWh", "SRC-079, SRC-082", "high")
    L.add("C-010", "NFPA 855-2026 requires a hazard mitigation analysis for essentially all installations and removes the stored-energy table", "LIT", "HMA by default", "", "SRC-085, SRC-086 (MeyerFire)", "medium")
    L.add("C-011", "NFPA 855-2026 exempts lead-acid and aqueous-nickel (not aqueous sodium) from explosion control", "LIT", "exemption list", "", "SRC-088", "medium")
    L.add("C-012", "Fire and Rescue NSW: 240-minute fire-resistance rooms for Li-ion data-centre UPS batteries", "LIT", 240, "min", "SRC-093", "low")
    L.add("C-013", "Aquion Aspen 48S-2.2 module specific energy", "CALC", 18.6, "Wh/kg", "2200 Wh / 118 kg, datasheet SRC-035", "high")
    L.add("C-014", "Aquion Aspen maximum power-to-energy ratio", "CALC", 0.45, "C", "1.0 kW peak / 2.2 kWh, SRC-038", "high")
    L.add("C-015", "Aquion funding raised before 2017 bankruptcy", "LIT", "~200", "$M", "MIT Technology Review 2017; SRC-032", "high")
    L.add("C-016", "Natron Energy (Prussian blue, data-centre backup) shut down", "LIT", "Sep 2025", "", "IEEE Spectrum; SRC-028", "high")
    L.add("C-017", "Peak Energy Series B (non-aqueous sodium-ion)", "VENDOR", 108, "$M", "pv-magazine 2026-10-23; SRC-001", "medium")
    L.add("C-018", "Peak Energy reported orders", "VENDOR", ">1", "$B", "SRC-007", "medium")
    L.add("C-019", "Alsym Na-Series ('NFPP+') cell specific energy claim", "VENDOR", 135, "Wh/kg", "ESS News 2025-10-22; SRC-011", "medium")
    L.add("C-020", "CATL Naxtra sodium-ion cell specific energy", "VENDOR", "~175", "Wh/kg", "electrek 2026-04-22; SRC-021", "medium")
    L.add("C-021", "India VRLA 12 V 100 Ah price per nominal kWh", "CALC", "7,100-7,600", "INR/kWh", "GeM listing SRC-120/121", "low")
    L.add("C-022", "India 48 V LFP pack price per kWh", "CALC", "10,800-21,600", "INR/kWh", "listings SRC-119", "low")
    L.add("C-023", "India data-centre capacity June 2026 -> 2029", "LIT", "1.6 -> 6", "GW", "JLL via press SRC-124", "low")
    L.add("C-024", "India telecom tower installations (Dec 2024)", "LIT", "816,763", "towers", "DoT via Business Standard SRC-134", "low")
    L.add("C-025", "India added BESS capacity H1 2026", "LIT", 8.2, "GWh", "Mercom via ESS News SRC-126", "medium")
    L.add("C-026", "Best aqueous Na-ion full cells at realistic loading use 17 m NaClO4 (an oxidiser)", "LIT", 17, "mol/kg", "Wu et al., Nat Commun 2024; SRC-052/053", "high")
    L.add("C-027", "Na2SO4 solubility at 0 C (anhydrous basis)", "LIT", 4.76, "g/100 mL", "Wikipedia/CRC; params MAT", "medium")
    L.add("C-028", "Alsym Series C (2024)", "LIT", 78, "$M", "energy-storage.news; SRC-018", "medium")
    L.add("C-029", "India UPS battery market (paid-report summaries)", "LIT", "305-401", "$M/yr", "IMARC / TechSci press releases SRC-137/138", "low")
    L.add("C-030", "YC W27 Request for Startups includes 'Data Center Supply Chain'", "LIT", "RFS W27", "", "ycombinator.com/rfs; SRC-146", "high")
    # ---------------- simulations / calculations ------------------------------------------
    if s1:
        L.add("C-101", "Kit software re-run on macOS reproduces the kit's expected outputs", "CALC", f"{s1['n_pass']}/{s1['n_total']}", "checks", "sim/s01_kit_rerun/out/s1_comparison.json", "high")
    if s2:
        maeA = [r["A_as_shipped"]["MAE_mV"] for r in s2["rates"].values()]
        maeD = [r["D_calibrated_k_x2"]["MAE_mV"] for r in s2["rates"].values()]
        L.add("C-102", "PyBaMM sodium-ion DFN (parameters as shipped) voltage error vs published HC//NVPF data, 4 rates", "SIM", f"{min(maeA):.0f}-{max(maeA):.0f}", "mV MAE", "sim/s02_pybamm_validation (fails 60 mV gate)", "high")
        L.add("C-103", "Same model after one-parameter kinetic calibration", "SIM", f"{min(maeD):.0f}-{max(maeD):.0f}", "mV MAE", "sim/s02_pybamm_validation (calibration, not validation)", "high")
    if s3:
        d = s3["mc"][str(s3["design_loading"])]["4.0"]; d60 = s3["mc"]["60.0"]["4.0"]
        L.add("C-104", "R1 capacity retained at a 15-minute (4C) discharge vs C/10, 40 mg/cm2 cathode, median (P10-P90)", "SIM",
              f"{d['p50']*100:.0f}% ({d['p10']*100:.0f}-{d['p90']*100:.0f}%)", "", "sim/s03_r1_cell (PyBaMM DFN, literature ranges, not validated)", "low")
        L.add("C-105", "R1 4C retention at 60 mg/cm2, median", "SIM", f"{d60['p50']*100:.0f}%", "", "sim/s03_r1_cell", "low")
        rt = s3["round_trip"]
        L.add("C-106", "R1 cell electrochemical round-trip efficiency at C/5 / 1C / 4C (excludes side reactions)", "SIM",
              f"{rt['0.2']['round_trip_eff']*100:.0f} / {rt['1.0']['round_trip_eff']*100:.0f} / {rt['4.0']['round_trip_eff']*100:.0f}%", "", "sim/s03_r1_cell", "low")
    if s4:
        L.add("C-107", "Coulombic efficiency a sealed R1 cell needs to reach 3,000 cycles before losing 20% of its water", "CALC",
              f"{s4['nominal']['CE_needed_for_3000_cycles']*100:.2f}%", "", "sim/s04_gas", "medium")
        L.add("C-108", "Cycles to 20% water loss at 99.5% CE", "CALC", f"{s4['nominal']['cycles_to_20pct_water_loss']:.0f}", "cycles", "sim/s04_gas", "medium")
        L.add("C-109", "NTP anode operating potential relative to the H2 line at pH 7", "CALC", "~0.2 V below", "", "sim/s04_gas; params MAT", "medium")
    if s5:
        e = s5["errors"].get("mace_mp0b3", {})
        L.add("C-110", "uMLIP (MACE-MP-0b3) insertion-voltage error vs literature, 5 compounds", "SIM", f"MAE {e.get('MAE_V', float('nan')):.2f}, max {e.get('max_abs_V', float('nan')):.2f}", "V",
              "sim/s05_atomistic (uMLIP screen, not DFT-verified)", "medium")
        il = s5["interlayer_A"].get("chgnet", {})
        k = [x for x in il if abs(float(x) - 1/3) < 0.01]
        if k:
            L.add("C-111", "Birnessite interlayer spacing, ordered Na0.33MnO2.0.67H2O model (CHGNet) vs paper XRD 7.19 A", "SIM", f"{il[k[0]]:.2f}", "angstrom", "sim/s05_atomistic", "medium")
        b = s5["barriers_eV"].get("mace_mp0b3", {})
        if b:
            L.add("C-112", "LiFePO4 [010] Li migration barrier, MACE-MP-0b3 vs GGA literature 0.27 eV", "SIM", f"{b.get('LiFePO4_b', float('nan')):.2f}", "eV", "sim/s05_atomistic", "medium")
            L.add("C-113", "Na hop barrier in the birnessite interlayer model (MACE-MP-0b3)", "SIM", f"{b.get('birnessite_Na', float('nan')):.2f}", "eV", "sim/s05_atomistic", "low")
        dv = s5["voltages"]["LiFePO4"].get("dft")
        if dv:
            L.add("C-114", "DFT+U (QE, GBRV, U_Fe 5.3 eV) LiFePO4 voltage vs 3.45 V literature", "SIM", f"{dv:.2f}", "V", "sim/s06_dft_ec2 + s05 analyze", "medium")
    if s7:
        m = s7["R1_mc"]["monobloc_Wh_kg"]
        L.add("C-115", "R1 12 V block specific energy, bottom-up, median (P10-P90)", "CALC", f"{m['p50']:.1f} ({m['p10']:.1f}-{m['p90']:.1f})", "Wh/kg", "sim/s07_buildup", "medium")
        L.add("C-116", "R1 block energy in a 12 V/100 Ah VRLA envelope (nominal design)", "CALC", f"{s7['R1_nominal']['monobloc_Wh']/1000:.2f}", "kWh", "params/design.py", "medium")
        L.add("C-117", "R1 block energy density", "CALC", f"{s7['R1_nominal']['monobloc_Wh_L']:.0f}", "Wh/L", "params/design.py", "medium")
        L.add("C-118", "R1 UPS cabinet energy (600x800x2000 mm, 40 blocks)", "CALC", f"{s7['R1_nominal']['cabinet_kWh']:.1f}", "kWh", "params/design.py", "medium")
    if s8:
        L.add("C-119", "Max temperature rise of a block during a 15-minute UPS discharge", "SIM", f"{s8['fd2d_ups_15min']['max_dT_K']:.1f}", "K", "sim/s08_thermal", "low")
        L.add("C-120", "Adiabatic rise if all stored energy of a block became heat", "CALC", f"{s8['abuse']['adiabatic_rise_if_all_energy_released_K']:.0f}", "K", "sim/s08_thermal", "medium")
        L.add("C-121", "PP case fire load vs stored electrical energy per block", "CALC", f"{s8['abuse']['case_fire_load_MJ']:.0f} vs {s8['abuse']['stored_electrical_energy_MJ']:.1f}", "MJ", "sim/s08_thermal", "medium")
    if s9:
        L.add("C-122", "R1 block bottom-up manufacturing cost (0.5 GWh/yr plant)", "CALC", f"{s9['monobloc_ups']['cost_per_kWh']:.0f}", "$/kWh", "sim/s09_tea (assumed prices, no quotes)", "low")
        u = s9["ups_tco_per_kWh15"]
        L.add("C-123", "15-year indoor UPS cost per kWh of 15-min backup: R1 / LFP incl. fire protection / VRLA", "CALC", f"{u['R1']:.0f} / {u['LFP']:.0f} / {u['VRLA']:.0f}", "$", "sim/s09_tea", "low")
        t = s9["telecom_lcos"]
        L.add("C-124", "Telecom daily-cycling LCOS: R1 / LFP / VRLA", "CALC", f"{t['R1']:.2f} / {t['LFP']:.2f} / {t['VRLA']:.2f}", "$/kWh", "sim/s09_tea", "low")
        L.add("C-125", "Best-case aqueous design cost (Prussian-white variant, optimistic inputs)", "CALC", "~150", "$/kWh", "sim/s09_tea scenario grid", "low")
    if s10:
        L.add("C-126", "India backup-battery TAM (telecom + data-centre UPS), median", "CALC", f"{s10['TAM_usd_yr']['p50']/1e6:.0f}", "$M/yr", "sim/s10_market", "low")
        L.add("C-127", "SAM where 'allowed indoors' plausibly changes the purchase, median", "CALC", f"{s10['SAM_usd_yr']['p50']/1e6:.0f}", "$M/yr", "sim/s10_market", "low")
        L.add("C-128", "5-year obtainable revenue (SOM), median", "CALC", f"{s10['SOM_usd_yr_after_5y']['p50']/1e6:.1f}", "$M/yr", "sim/s10_market", "low")
    # ---------------- assumptions / targets ------------------------------------------------
    L.add("C-201", "Li-ion indoor fire-protection extra cost used in base case (range 15-200)", "ASSUMPTION", COST["lfp_fire_protection"].value, "$/kWh", "params COST", "low")
    L.add("C-202", "R1 cycle life target", "TARGET", 3000, "cycles", "decisions/IDEA_v2.md", "n/a")
    L.add("C-203", "R1 cost target at first 0.5 GWh line", "TARGET", 150, "$/kWh", "decisions/IDEA_v2.md", "n/a")
    L.add("C-204", "R1 electrolyte: 0.5 M Na2SO4, no perchlorate", "TARGET", 0.5, "mol/L", "params MAT; decision D-05", "n/a")
    L.add("C-205", "First lab experiment cost and duration", "ASSUMPTION", "5-10 k$, 10-12 weeks", "", "founder estimate; no quote", "low")
    L.add("C-206", "Kill gate: cathode capacity at 40 mg/cm2", "TARGET", ">=60", "mAh/g", "decisions/IDEA_v2.md K1", "n/a")
    L.add("C-207", "Kill gate: buyers naming a >=$150/kWh Li-ion indoor premium", "TARGET", ">=3 of 20", "", "decisions/IDEA_v2.md K4", "n/a")
    L.add("C-208", "Use of funds total (YC standard deal)", "LIT", 500, "k$", "ycombinator.com/deal", "high")
    L.add("C-209", "VRLA float service life in UPS duty", "ASSUMPTION", "3-6", "years", "params VRLA_REF; typical datasheets", "low")
    L.add("C-210", "R1 nominal cell voltage (cathode minus anode average potential)", "CALC", round(MAT["cathode_avg_potential_SHE"].value - MAT["anode_avg_potential_SHE"].value, 2), "V", "params MAT", "medium")
    L.add("C-211", "Li-ion fire-protection cost at which R1 breaks even for indoor UPS (base case)", "CALC", 568, "$/kWh", "finance model UPS_TCO (LibreOffice-recalculated)", "low")
    L.add("C-212", "DFT spot instance spend to date (two instances; first reclaimed by AWS)", "CALC", "<2", "$", "sim/s06_dft_ec2 cost watchdog", "high")
    return L


if __name__ == "__main__":
    L = build(); p = L.write(); print(f"{len(L.rows)} claims -> {p}")
