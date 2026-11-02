#!/usr/bin/env python3
"""Assemble PROJECT_SALT/ from generated artifacts + authored documents, then write the claims ledger, thermodynamic-limits
document, material table, BUILD_STATUS.md and MANIFEST.csv. Idempotent. Never creates empty folders.

Usage: python tools/project_salt/assemble.py
"""
from __future__ import annotations
import csv, hashlib, json, shutil, sys, zipfile
from pathlib import Path

LAB = Path(__file__).resolve().parents[2]; P = LAB / "PROJECT_SALT"
def J(p): return json.load(open(LAB / p))

def cp(src, dst_dir, name=None):
    s = LAB / src
    if not s.exists(): return False
    d = P / dst_dir; d.mkdir(parents=True, exist_ok=True)
    if s.is_dir():
        t = d / (name or s.name)
        shutil.copytree(s, t, dirs_exist_ok=True, ignore=shutil.ignore_patterns("tmp", "__pycache__", "*.save", "*.wfc*", "*.lock"))
    else:
        shutil.copy2(s, d / (name or s.name))
    return True

def copy_artifacts():
    # 01 research
    for f in ("chemistry_candidates.csv", "balanced_reactions.md", "s12_energy_ladder.png", "s12_energy_ladder.svg", "s12_pareto.png", "s12_pareto.svg", "s12_results.json"):
        cp(f"sim/s12_chemistry_matrix/out/{f}", "01_SCIENTIFIC_RESEARCH")
    cp("research/sources_project_salt.csv", "01_SCIENTIFIC_RESEARCH")
    # 02 computational chemistry
    for f in ("campaign.py", "analyze.py"): cp(f"sim/s11_dft_chlorides/{f}", "02_COMPUTATIONAL_CHEMISTRY/dft_u")
    for stage in ("conv", "relax", "uscan", "mag", "dos"):
        src = LAB / "sim/s11_dft_chlorides/runs" / stage
        if not src.exists(): continue
        for job in sorted(src.iterdir()):
            if not job.is_dir(): continue
            dst = P / "02_COMPUTATIONAL_CHEMISTRY/raw_results" / stage / job.name; dst.mkdir(parents=True, exist_ok=True)
            for f in ("job.in", "job.out", "STATUS", "wall.txt", "cmd.txt", "meta.json", "projwfc.in", "projwfc.out"):
                if (job / f).exists(): shutil.copy2(job / f, dst / f)
            for f in job.glob("pdos.pdos_*"): shutil.copy2(f, dst / f.name)
    cp("sim/s11_dft_chlorides/runs/campaign.log", "02_COMPUTATIONAL_CHEMISTRY/raw_results")
    cp("sim/s11_dft_chlorides/runs/ec2_logs", "02_COMPUTATIONAL_CHEMISTRY/raw_results")
    for f in ("ec2_s11.sh", "remote_run.sh", "remote_dos.sh", "pull_loop.sh"): cp(f"sim/s11_dft_chlorides/ec2/{f}", "02_COMPUTATIONAL_CHEMISTRY/dft_u/ec2")
    for f in ("s11_results.json", "s11_voltage_vs_U.png", "s11_voltage_vs_U.svg", "s11_voltage_vs_U.caption.txt",
              "s11_pdos.png", "s11_pdos.svg", "s11_pdos.caption.txt"):
        cp(f"sim/s11_dft_chlorides/out/{f}", "02_COMPUTATIONAL_CHEMISTRY/validation")
    cp("sim/s06_dft_ec2/README.md", "02_COMPUTATIONAL_CHEMISTRY/ec2_runs_previous", "README_s06.md")
    cp("sim/s06_dft_ec2/make_qe_inputs.py", "02_COMPUTATIONAL_CHEMISTRY/ec2_runs_previous")
    cp("sim/s05_atomistic/out/s05_summary.json", "02_COMPUTATIONAL_CHEMISTRY/migration")
    cp("sim/s05_atomistic/out/neb_mace_mp0b3.json", "02_COMPUTATIONAL_CHEMISTRY/migration")
    cp("sim/s05_atomistic/out/s05_barriers.png", "02_COMPUTATIONAL_CHEMISTRY/migration")
    write_structures()
    # 03 electrochemical modelling
    for f in ("s13a_fast_charge.json", "s13a_fast_charge_benchmark.png", "s13a_fast_charge_benchmark.svg", "s13a_fast_charge_benchmark.caption.txt"):
        cp(f"sim/s13_founder_targets/out/{f}", "03_ELECTROCHEMICAL_MODELLING/fast_charging")
    cp("sim/s13_founder_targets/fast_charge_pybamm.py", "03_ELECTROCHEMICAL_MODELLING/fast_charging")
    for f in ("scell_model.py", "out/s14_results.json", "out/s14_scell_curves.png", "out/s14_scell_curves.svg"):
        cp(f"sim/s14_scell_model/{f}", "03_ELECTROCHEMICAL_MODELLING/cell_models")
    cp("sim/s03_r1_cell/out/s03_results.json", "03_ELECTROCHEMICAL_MODELLING/cell_models", "s03_aqueous_r1_results.json")
    cp("sim/s04_gas/out", "03_ELECTROCHEMICAL_MODELLING/gas_generation", "s04_aqueous_gas")
    cp("sim/s08_thermal/out", "03_ELECTROCHEMICAL_MODELLING/thermal_models", "s08_aqueous_thermal")
    cp("sim/s02_pybamm_validation/out", "03_ELECTROCHEMICAL_MODELLING/validation_data", "s02_na_dfn_validation")
    cp("sim/s02_pybamm_validation/README.md", "03_ELECTROCHEMICAL_MODELLING/validation_data", "S02_README.md")
    # 04 CAD
    cp("cad/out/scell", "04_MECHANICAL_CAD", "cell")
    for f in ("SB-SC-001.dxf", "SB-SC-001.pdf", "SB-SC-001.png", "SB-SC-001_paper.png", "SB-SC-001_commands.jsonl"):
        cp(f"drawings/out/{f}", "04_MECHANICAL_CAD/drawings")
    cp("cad/out/scell/scell_r0_exploded.step", "04_MECHANICAL_CAD/assemblies")
    cp("cad/out/scell/scell_r0.step", "04_MECHANICAL_CAD/assemblies")
    for f in ("cad/make_scell.py", "params/scell_params.py", "drawings/make_drawings.py"): cp(f, "04_MECHANICAL_CAD/native_sources")
    # v1.1 product concepts D3-D5 (EC2 build host): P1 cell + SM-48T module, thermal architecture, SC-UPS-1 cabinet
    for f in ("p1_cell.step", "p1_cell_partlist.csv", "sm48t_module.step", "sm48t_exploded.step", "sm48t_cutaway.step", "sm48t_partlist.csv", "smodule_meta.json"):
        cp(f"cad/out/smodule/{f}", "04_MECHANICAL_CAD/module")
    for f in ("sc_ups1_cabinet.step", "sc_ups1_partlist.csv"): cp(f"cad/out/smodule/{f}", "04_MECHANICAL_CAD/enclosure")
    for f in ("s16_results.json", "s16_thermal.png", "s16_thermal.svg", "s16_thermal.caption.txt"): cp(f"sim/s16_module_thermal/out/{f}", "04_MECHANICAL_CAD/thermal_management")
    cp("sim/s16_module_thermal/thermal.py", "04_MECHANICAL_CAD/thermal_management")
    for dwg in ("SB-SM-001", "SB-TM-001", "SB-UPS-001"):
        for ext in ("dxf", "pdf", "png"): cp(f"drawings/out/{dwg}.{ext}", "04_MECHANICAL_CAD/drawings")
    cp("drawings/out/SB-TM-001.pdf", "04_MECHANICAL_CAD/thermal_management")
    for f in ("cad/make_smodule.py", "params/smodule_params.py"): cp(f, "04_MECHANICAL_CAD/native_sources")
    for f in sorted((LAB / "renders/out_salt").glob("*_captioned.png")): cp(str(f.relative_to(LAB)), "04_MECHANICAL_CAD/renders")
    cp("renders/out_salt/sm48t_turntable.mp4", "04_MECHANICAL_CAD/renders"); cp("renders/blender_salt.py", "04_MECHANICAL_CAD/renders")
    for f in sorted((LAB / "diagrams/out").glob("ds*")): cp(str(f.relative_to(LAB)), "01_SCIENTIFIC_RESEARCH/diagrams")
    cp("matlab/stem", "01_SCIENTIFIC_RESEARCH", "matlab_stem")
    for f in ("SaltBattery_Complete_Technical_Record.docx", "SaltBattery_Complete_Technical_Record.pdf", "SaltBattery_Complete_Technical_Deck.pptx",
              "SaltBattery_Complete_Technical_Deck.pdf"):
        cp(f"DELIVERABLES/1_investor_docs/{f}", "12_YC/investor_deck")
    cp("finance/make_salt_model.py", "10_ECONOMICS/bom_cost_model")
    cp("tools/ec2_build", "13_RELEASE", "ec2_build_host")
    # 05 electronics
    sm = "pcb/scell_monitor"
    for f in ("design_scm.py", "scell_monitor.kicad_pro", "scell_monitor.kicad_sch", "scell_monitor_power.kicad_sch", "scell_monitor_mcu.kicad_sch",
              "scell_monitor_sense.kicad_sch", "scell_monitor_io.kicad_sch", "scell_monitor.kicad_dru", "sym-lib-table", "fp-lib-table",
              "scell_monitor.net", "erc.json"):
        cp(f"{sm}/{f}", "05_ELECTRONICS/kicad")
    cp("pcb/lib/scm_pcb.kicad_sym", "05_ELECTRONICS/kicad")
    cp(f"{sm}/fab/scell_monitor-schematic.pdf", "05_ELECTRONICS/schematics")
    for f in ("scell_monitor.kicad_pcb", "drc.json", "build.log", "route_report.json", "fab/scell_monitor-top.png"): cp(f"{sm}/{f}", "05_ELECTRONICS/pcb")
    fab = LAB / sm / "fab"
    for f in fab.glob("*"):
        if f.suffix in (".gbr", ".gtl", ".gbl", ".gts", ".gbs", ".gto", ".gbo", ".gtp", ".gbp", ".gm1", ".g1", ".g2", ".drl", ".gbrjob", ".gta", ".gba") or f.name.endswith("pos.csv"):
            cp(str(f.relative_to(LAB)), "05_ELECTRONICS/gerbers")
    cp(f"{sm}/fab/scell_monitor-bom.csv", "05_ELECTRONICS/bom")
    cp(f"{sm}/firmware", "05_ELECTRONICS", "firmware")
    # 07 parts
    cp("cad/out/scell/scell_r0_partlist.csv", "07_BUILD_MANUAL/parts")
    # 10 economics
    cp("sim/s12_chemistry_matrix/prices.py", "10_ECONOMICS/bom_cost_model")
    cp("sim/s12_chemistry_matrix/matrix.py", "10_ECONOMICS/bom_cost_model")
    for f in ("s13b_targets.json", "s13b_three_dollar.png", "s13b_three_dollar.svg", "s13b_energy_vs_loading.png"):
        cp(f"sim/s13_founder_targets/out/{f}", "10_ECONOMICS/lifetime_cost")
    cp("sim/s13_founder_targets/targets.py", "10_ECONOMICS/lifetime_cost")
    for f in ("out/s15_results.json", "out/s15_factory_and_tornado.png", "out/s15_factory_and_tornado.svg", "factory.py"):
        cp(f"sim/s15_factory/{f}", "10_ECONOMICS/factory_capex")
    cp("sim/s15_factory/out/s15_factory_and_tornado.png", "10_ECONOMICS/sensitivity_analysis")
    # 11 market
    cp("sim/s10_market/out", "11_MARKET/india", "s10_india_market_model")

def write_structures():
    """Relaxed structures (CIF) from the DFT runs, via ASE."""
    sys.path.insert(0, str(LAB / "sim/s11_dft_chlorides"))
    try:
        import campaign as C
        from ase import Atoms
        from ase.io import write
    except Exception:
        return
    d = P / "02_COMPUTATIONAL_CHEMISTRY/structures"
    for job in sorted((LAB / "sim/s11_dft_chlorides/runs/relax").glob("*")):
        try:
            cell, atoms = C.relaxed_geometry(job)
        except Exception:
            continue
        sym = [__import__("re").sub(r"\d", "", s) for s, _ in atoms]
        a = Atoms(symbols=sym, scaled_positions=[p for _, p in atoms], cell=cell, pbc=True)
        d.mkdir(parents=True, exist_ok=True); write(d / f"{job.name}_relaxed.cif", a)

MATERIALS = [  # element, crust ppm, seawater mg/L, role, India/US supply note  (CRC-type standard values, transcribed: [PUBLISHED, verify])
    ("Na", 23600, 10800, "anode ion / NaCl", "unlimited (salt, soda ash)"), ("Cl", 145, 19400, "salt-literal cathodes", "unlimited (salt)"),
    ("Fe", 56300, 0.002, "S03 cathode, NFPP, Fe-air", "abundant; India and US steel industries"), ("Ni", 84, 0.0006, "ZEBRA S01/S02; NMC", "import-dependent in India"),
    ("Al", 82300, 0.002, "NaAlCl4, collectors, beta-alumina", "abundant"), ("Mn", 950, 0.0002, "layered oxides, PW, aqueous", "India has Mn ore"),
    ("S", 350, 904, "Na-S, FeS additive", "refinery by-product"), ("Zn", 70, 0.005, "Zn-ion, Zn-air", "India/US smelters"),
    ("Ti", 5650, 0.001, "NTP anode (aqueous)", "abundant ilmenite (India)"), ("P", 1050, 0.06, "NFPP, NVP", "imported phosphate rock (India)"),
    ("V", 120, 0.0025, "NVPF/NVP", "constrained"), ("Mo", 1.2, 0.01, "S-cell current collector", "small quantities only"),
    ("Li", 20, 0.18, "benchmarks only", "import-dependent"), ("Co", 25, 0.00002, "benchmarks only", "import-dependent"),
    ("Mg", 23300, 1290, "Mg-ion; beta''-alumina dopant", "abundant"), ("Ca", 41500, 412, "Ca-ion; impurity to remove", "abundant")]

def write_materials():
    with open(P / "01_SCIENTIFIC_RESEARCH/material_abundance.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["element", "crust_ppm", "seawater_mg_per_L", "role_in_candidates", "supply_note", "label"])
        for r in MATERIALS: w.writerow(list(r) + ["[PUBLISHED] standard reference values transcribed - verify (CRC Handbook)"])

def write_thermo():
    s12 = J("sim/s12_chemistry_matrix/out/s12_results.json")["results"]
    s11p = LAB / "sim/s11_dft_chlorides/out/s11_results.json"; s11 = json.load(open(s11p)) if s11p.exists() else {}
    L = ["# Thermodynamic and practical limits (generated by tools/project_salt/assemble.py)", "",
         "## 1. Theoretical vs practical specific energy (S12)", "",
         "| ID | Candidate | Theoretical Wh/kg [THEORETICAL] | Cell P50 [P10–P90] [CALCULATED] | Practical/theoretical |", "|---|---|---|---|---|"]
    for r in sorted(s12.values(), key=lambda r: -r["cell_P50"]):
        L.append(f"| {r['id']} | {r['name']} | {r['theoretical_Whkg']:.0f} | {r['cell_P50']:.0f} [{r['cell_P10']:.0f}–{r['cell_P90']:.0f}] | {r['cell_P50']/r['theoretical_Whkg']:.0%} |")
    L += ["", "## 2. Why 360 Wh/kg is out of reach for sodium (cell level)", "",
          "- Practical cells keep only ~25–55 % of the active-pair energy (column above); the best calibrated benchmarks keep ~50 %.",
          "- Na intercalation cathodes deliver ≈3.1–3.3 V × 120–185 mAh/g ≈ 400–600 Wh/kg-CAM vs NMC811 ≈ 3.75 V × 200 mAh/g ≈ 750 Wh/kg-CAM.",
          "  With an anode-free Na metal design (N08) the build-up gives 259 Wh/kg P50 / 292 P90 [CALCULATED]. A 360 Wh/kg Na cell needs a CAM ≥ ~750 Wh/kg",
          "  that also cycles - none is known.",
          "- Conversion chemistries (Na–S 1,271; Na–Cl₂ 1,825; Na–O₂ 1,106 Wh/kg theoretical) have the headroom but lose it to excess Na, electrolyte",
          "  and carbon hosts (P50 125–188 Wh/kg here) and carry cycle-life (Na–S, Na–O₂) or toxicity (Na–Cl₂) problems.",
          "- Aqueous cells are capped by water's 1.23 V thermodynamic window (practical ≤ ~1.9–2.0 V with kinetic overpotentials) - 19–54 Wh/kg here.", "",
          "## 3. DFT+U check of the salt-literal thermodynamics (S11, QE 7.6; Apple M4 + EC2 c8g.8xlarge)", ""]
    if s11.get("voltages"):
        L += ["| Reaction | DFT voltage (V) | Expt from ΔH (V) | Expt from ΔG 298 K (V) | ZEBRA OCV ~300 °C | Note |", "|---|---|---|---|---|---|"]
        for k, v in s11["voltages"].items():
            note = s11.get("formation", {}).get(k, {}).get("note", "")
            L.append(f"| {k} | {v['dft_V']} | {v['exp_dH_V']} | {v['exp_dG_V']} | {v.get('exp_OCV_300C') or '–'} | {note} |")
        L += ["", "Formation enthalpies (eV per formula unit):", "", "| Phase | DFT | Expt | Error |", "|---|---|---|---|"]
        for k, v in s11.get("formation", {}).items(): L.append(f"| {k} | {v['dft_eV']} | {v['exp_eV']} | {v['err_eV']} |")
        if s11.get("uscan"):
            L += ["", "U-scan (fixed geometry; voltage vs Na, V):", "", "| Chloride / geometry | U=0 | U=2 | U=4 | U=6 |", "|---|---|---|---|---|"]
            for k, row in s11["uscan"].items():
                L.append(f"| {k} | " + " | ".join(str(row.get(str(u), row.get(u, {})).get("V", "–")) if isinstance(row.get(str(u), row.get(u)), dict) else "–" for u in (0, 2, 4, 6)) + " |")
        if s11.get("magnetic"):
            L += ["", "Magnetic order (E_AFM − E_FM, meV per formula unit; negative = interlayer AFM ground state):", ""]
            for k, v in s11["magnetic"].items(): L.append(f"- {k}: {v['E_AFM_minus_FM_meV_per_fu']} → {v['ground']}")
        if s11.get("gaps"):
            L += ["", "Band gaps on the SCF k-mesh (eV; electron counting, FM order; 0 = the FM solution is metallic):", "",
                  "| Chloride | U = 0 (relaxed) | U = 4 (relaxed) |", "|---|---|---|"]
            G = s11["gaps"]
            for m in ("Fe", "Co", "Ni"):
                cell = lambda k: ("–" if k not in G else (f"{G[k]['gap_eV']:.2f}" + (" (metallic)" if G[k]["metallic"] else "")))
                L.append(f"| {m}Cl₂ | {cell(f'{m}Cl2_U0_relax')} | {cell(f'{m}Cl2_U4_relax')} |")
            L += ["", "FeCl₂ (Fe²⁺ d⁶) stays metallic in the symmetric 3-atom cell even with U: opening its gap needs orbital-ordering symmetry",
                  "breaking (lower-symmetry cell / occupation control), which was not attempted. Treat its U > 0 numbers with extra caution."]
        if s11.get("platform"):
            n_ec2 = sum(1 for v in s11["platform"].values() if v.startswith("EC2")); n_loc = len(s11["platform"]) - n_ec2
            L += ["", f"Where the {len(s11['platform'])} jobs ran: {n_loc} on the local Apple M4 (osx-arm64), {n_ec2} on EC2 c8g.8xlarge (linux-aarch64),",
                  "same conda-forge QE 7.6 build family, inputs and pseudopotentials (per-job list: `validation/s11_results.json` → `platform`)."]
        L += ["", "Experimental thermochemistry transcribed from standard tables - verify before citing. DFT energies are 0 K; compare with the ΔH column."]
    else:
        L.append("DFT results not yet available when this file was generated - re-run the assembler after `sim/s11_dft_chlorides/analyze.py`.")
    L += ["", "## 4. Five-minute-charge limits", "", "See `03_ELECTROCHEMICAL_MODELLING/fast_charging` and `10_ECONOMICS/lifetime_cost/s13b_targets.json`:",
          "transport-limited loading ≈1.9 mAh/cm² for liquid electrolytes; ≥42 mA/cm² metal plating at 12C vs ~1–10 mA/cm² CCD; molten-salt cell needs > 3.05 V."]
    (P / "01_SCIENTIFIC_RESEARCH/thermodynamic_limits.md").write_text("\n".join(L) + "\n")
    shutil.copy2(LAB / "sim/s12_chemistry_matrix/out/balanced_reactions.md", P / "01_SCIENTIFIC_RESEARCH/balanced_reactions.md")

def write_dft_results():
    """02/dft_u/RESULTS.md: every S11 number, generated from validation/s11_results.json (no hand transcription)."""
    s11p = LAB / "sim/s11_dft_chlorides/out/s11_results.json"
    if not s11p.exists(): return
    r = json.load(open(s11p)); L = ["# S11 results (generated by tools/project_salt/assemble.py from `../validation/s11_results.json`)", "",
        "All values [SIMULATED]: PBE(+U)-D3, QE 7.6, GBRV USPP, 0 K, no zero-point/thermal terms. Experimental references [PUBLISHED] are",
        "transcribed from standard tables (NBS/CRC) - verify before citing.", "",
        "## 1. Conversion voltages, 2 Na + MCl₂ → 2 NaCl + M (V vs Na)", "",
        "| Couple | DFT | Expt (ΔH) | DFT − expt | Expt (ΔG, 298 K) | ZEBRA OCV ~300 °C |", "|---|---|---|---|---|---|"]
    for k, v in r["voltages"].items():
        err = v.get("err_vs_dH_V", round(v["dft_V"] - v["exp_dH_V"], 3))
        L.append(f"| {k} | {v['dft_V']:.3f} | {v['exp_dH_V']:.3f} | {err:+.3f} | {v['exp_dG_V']:.3f} | {v.get('exp_OCV_300C') or '–'} |")
    L += ["", "U4 rows mix a +U chloride with a U = 0 metal (uncorrected); use the U0 rows.", "",
          "## 2. Formation enthalpy (eV per formula unit)", "", "| Phase | DFT | Expt | Error |", "|---|---|---|---|"]
    for k, v in r["formation"].items(): L.append(f"| {k} | {v['dft_eV']:.3f} | {v['exp_eV']:.3f} | {v['err_eV']:+.3f} |")
    L += ["", "## 3. Voltage and gap vs U (fixed geometry)", "", "| Chloride (geometry) | U = 0 | U = 2 | U = 4 | U = 6 |", "|---|---|---|---|---|"]
    for k, row in r["uscan"].items():
        cells = []
        for u in ("0", "2", "4", "6"):
            x = row.get(u)
            cells.append("–" if not x else f"{x['V']:.3f} V, gap {x['gap_eV']:.2f} eV" + (" (metal)" if x.get("metallic") else ""))
        m_, g_ = k.split("_geomU"); L.append(f"| {m_} (relaxed at U = {g_} eV) | " + " | ".join(cells) + " |")
    L += ["", "## 4. Lattice parameters (Å)", "", "| Phase | DFT | Expt | Error |", "|---|---|---|---|"]
    for k, v in r["lattice"].items():
        if "a_hex" in v: L.append(f"| {k} | a {v['a_hex']}, c {v['c_hex']} | a {v['exp'][0]}, c {v['exp'][1]} | a {v['err_a_pct']:+.2f} %, c {v['err_c_pct']:+.2f} % |")
        elif "a_conv" in v: L.append(f"| {k} | a {v['a_conv']} | a {v['exp']} | {v['err_pct']:+.2f} % |")
        else: L.append(f"| {k} | a {v['a']}, c {v['c']} | a {v['exp'][0]}, c {v['exp'][1]} | – |")
    L += ["", "## 5. Interlayer magnetic order (2-formula-unit supercell, same k-mesh for FM and AFM)", "",
          "| Chloride | E(AFM) − E(FM), meV per f.u. | Lower-energy order |", "|---|---|---|"]
    for k, v in r["magnetic"].items(): L.append(f"| {k} | {v['E_AFM_minus_FM_meV_per_fu']:+.2f} | {v['ground']} |")
    if r.get("gaps"):
        L += ["", "## 6. Band gaps (eV, SCF k-mesh, electron counting; 0 = metallic FM solution)", "", "| Run | Gap | Metallic |", "|---|---|---|"]
        for k, v in r["gaps"].items(): L.append(f"| {k} | {v['gap_eV']:.2f} | {'yes' if v['metallic'] else 'no'} |")
    if r.get("pdos"):
        L += ["", "## 7. Character of the top 1 eV of the valence band (PDOS)", "", "| Run | VBM − E_F (eV) | M-3d share | Cl-3p share |", "|---|---|---|---|"]
        for k, v in r["pdos"].items(): L.append(f"| {k} | {v['vbm_minus_EF_eV']:+.2f} | {v['top1eV_M3d_frac']:.2f} | {1 - v['top1eV_M3d_frac']:.2f} |")
    if r.get("convergence"):
        L += ["", "## 8. Convergence (meV/atom relative to the densest setting)", ""]
        for k, v in r["convergence"].items(): L.append(f"- {k}: " + ", ".join(f"{a} {b:+.2f}" for a, b in v.items()))
    if r.get("platform"):
        n_ec2 = sum(1 for v in r["platform"].values() if v.startswith("EC2"))
        L += ["", f"## 9. Where the jobs ran", "", f"{len(r['platform']) - n_ec2} jobs on the local Apple M4, {n_ec2} on EC2 c8g.8xlarge. Per-job list in the JSON (`platform`)."]
    d = P / "02_COMPUTATIONAL_CHEMISTRY/dft_u"; d.mkdir(parents=True, exist_ok=True); (d / "RESULTS.md").write_text("\n".join(L) + "\n")

def claims():
    s12 = J("sim/s12_chemistry_matrix/out/s12_results.json")["results"]; s13 = J("sim/s13_founder_targets/out/s13b_targets.json")
    s14 = J("sim/s14_scell_model/out/s14_results.json"); s15 = J("sim/s15_factory/out/s15_results.json"); fc = J("sim/s13_founder_targets/out/s13a_fast_charge.json")
    rows = []
    def add(claim, label, value, unit, src, used="EXECUTIVE_VERDICT"):
        rows.append([f"PSC-{len(rows)+1:03d}", claim, label, value, unit, src, used])
    add("Founder target: cell specific energy", "[TARGET]", 360, "Wh/kg", "brief §1")
    add("Founder target: range on one charge", "[TARGET]", 1500, "km", "brief §1")
    add("Founder target: charge time", "[TARGET]", 5, "min", "brief §1")
    add("Founder target: manufacturing cost (unit basis unresolved)", "[TARGET]", 3, "USD", "brief §1.1")
    for cid in ("N08", "S04", "N01", "N02", "N03", "S01", "S02", "S03", "N05", "N06", "A01", "A03"):
        r = s12[cid]
        add(f"{cid} {r['name']}: practical cell specific energy P50 (P10-P90 {r['cell_P10']:.0f}-{r['cell_P90']:.0f})", "[CALCULATED]", round(r["cell_P50"]), "Wh/kg", "sim/s12_chemistry_matrix/out/s12_results.json")
        if r.get("mat_cost_P50") is not None:
            add(f"{cid}: cell materials cost P50", "[CALCULATED] from [ASSUMPTION] prices", round(r["mat_cost_P50"]), "USD/kWh", "s12_results.json")
    for cid in ("S01", "S04", "N09", "N10"):
        add(f"{cid}: theoretical specific energy of the balanced reaction", "[THEORETICAL]", s12[cid]["theoretical_Whkg"], "Wh/kg", "balanced_reactions.md")
    for cid in ("B01", "B02", "B03", "B04", "B05", "N01", "S01"):
        r = s12[cid]
        if "calibration_err_pct" in r: add(f"Build-up calibration error vs published cell, {cid}", "[CALCULATED]", r["calibration_err_pct"], "%", "s12_results.json")
    suv = next(x for x in s13["A_vehicle"] if x["vehicle"] == "mid SUV" and x["pack_case"].startswith("founder"))
    add("Mid SUV 1,500 km with 360 Wh/kg cell: usable energy", "[CALCULATED]", suv["usable_kWh"], "kWh", "s13b_targets.json")
    add("Mid SUV 1,500 km: battery mass", "[CALCULATED]", suv["battery_mass_kg"], "kg", "s13b_targets.json")
    add("Mid SUV 1,500 km in 5 min: average charging power", "[CALCULATED]", suv["avg_charge_power_MW"], "MW", "s13b_targets.json")
    add("Mid SUV 1,500 km in 5 min: average C-rate", "[CALCULATED]", suv["avg_C_rate"], "C", "s13b_targets.json")
    add("MCS connector ceiling", "[PUBLISHED]", 3.75, "MW", "PS-033")
    add("Best deployed/claimed passenger-car charging power (CATL Shenxing gen-2)", "[VENDOR CLAIM]", 1.3, "MW", "PS-018")
    add("Transport-limited areal capacity for a 5-min charge (liquid electrolyte)", "[CALCULATED]", s13["B_electrode"]["Qa_max_cell"], "mAh/cm2", "s13b_targets.json")
    for r in fc["li_benchmark"]:
        if r.get("rate") in (1, 4, 10) and "frac_at_5min" in r:
            add(f"Validated Li-ion DFN (Chen2020): fraction charged in 5 min at {r['rate']}C CC-CV", "[SIMULATED]", round(100 * r["frac_at_5min"], 1), "%", "s13a_fast_charge.json", "03/fast_charging")
    for d in fc.get("degradation", []):
        if "fade_pct_per_cycle" in d:
            add(f"OKane2022 Li benchmark: capacity fade per cycle with {d['charge_rate']}C charge (15 cycles)", "[SIMULATED]", round(d["fade_pct_per_cycle"], 4), "%/cycle", "s13a_fast_charge.json", "03/fast_charging")
    fc60 = s14["fast_charge"]["60"]
    add("S-cell: cell voltage needed for a 5-min (12C) charge at 60 mAh/cm2", "[SIMULATED] (unvalidated model)", fc60["cell_V_needed"], "V", "s14_results.json")
    add("Over-charge side reaction onset in Na-MCl2 (NaAlCl4 + Ni)", "[PUBLISHED] (ZEBRA literature)", 3.05, "V", "HAZARD_ANALYSIS H3")
    for r in s13["C_three_dollar"]:
        if r["id"] in ("S03", "S04", "N02", "B02"):
            add(f"{r['id']}: theoretical minimum material cost (reactants at feedstock price)", "[CALCULATED] from [ASSUMPTION]", r["theoretical_min_material_usd_kWh"], "USD/kWh", "s13b_targets.json")
            add(f"{r['id']}: cell cost floor at 1 GWh", "[CALCULATED] from [ASSUMPTION]", r["cell_cost_floor"], "USD/kWh", "s13b_targets.json")
    for s in s15["scenarios"]:
        if s["region"] == "India" and s["MWh_per_yr"] in (100, 1000):
            add(f"{s['line']} cell cost at {s['MWh_per_yr']} MWh/yr, India scenario", "[CALCULATED] from [ASSUMPTION]", s["cell_cost_usd_kWh"], "USD/kWh", "s15_results.json", "08/10")
    add("S03 materials cost in the G4 case (0.5 mm disc, 100 mAh/cm2, $15/kg ceramic)", "[CALCULATED] from [ASSUMPTION]", s15["tornado_S03_materials"]["G4_case_0p5mm_100mAh_15usdkg"], "USD/kWh", "s15_results.json")
    add("Lowest LFP cell price 2025 (stationary)", "[PUBLISHED]", 36, "USD/kWh", "PS-017")
    add("Altech CERENERGY 120 MWh/yr plant capex", "[VENDOR CLAIM]", 156, "EUR million", "PS-032")
    add("ZEBRA cell specific energy (literature range 90-140)", "[PUBLISHED]", 120, "Wh/kg", "PS-010")
    add("Na-FeCl2 at 190 C: capacity at 33.3 mA/cm2", "[PUBLISHED]", 116, "mAh/g", "PS-005")
    add("NFPA 855 threshold quantity, sodium nickel chloride (70 kWh if UL 1973 listed)", "[PUBLISHED]", 20, "kWh", "PS-015")
    add("Number of cells built / measured in this project", "[MEASURED]-type fact: none exist", 0, "cells", "BUILD_STATUS")
    add("Customer interviews conducted", "fact", 0, "interviews", "11_MARKET/customer_interviews")
    s11p = LAB / "sim/s11_dft_chlorides/out/s11_results.json"
    if s11p.exists():
        s11 = json.load(open(s11p))
        for k, v in s11.get("voltages", {}).items():
            add(f"DFT(+U) voltage {k}", "[SIMULATED]", v["dft_V"], "V", "02/validation/s11_results.json", "thermodynamic_limits.md")
    with open(P / "00_START_HERE/CLAIMS_LEDGER.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "claim", "label", "value", "unit", "source_or_evidence", "where_used"]); w.writerows(rows)
    with open(P / "12_YC/evidence_register.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "claim", "label", "value", "unit", "source_or_evidence", "where_used"])
        w.writerows([r for r in rows if "TARGET" not in r[2]])
    return len(rows)

def kit_zip():
    d = P / "13_RELEASE/final_build_kit"; d.mkdir(parents=True, exist_ok=True)
    z = d / "S-cell_R0_build_kit.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for sub in ("04_MECHANICAL_CAD", "05_ELECTRONICS", "06_PROCUREMENT", "07_BUILD_MANUAL", "09_VALIDATION"):
            for f in (P / sub).rglob("*"):
                if f.is_file(): zf.write(f, f.relative_to(P))
        zf.write(P / "00_START_HERE/EXECUTIVE_VERDICT.md", "00_START_HERE/EXECUTIVE_VERDICT.md")

def prune_empty():
    for d in sorted((x for x in P.rglob("*") if x.is_dir()), key=lambda x: -len(x.parts)):
        if not any(d.iterdir()): d.rmdir()

def build_status(nclaims):
    req = ["00_START_HERE", "01_SCIENTIFIC_RESEARCH", "02_COMPUTATIONAL_CHEMISTRY/dft_u", "02_COMPUTATIONAL_CHEMISTRY/bft_u", "02_COMPUTATIONAL_CHEMISTRY/structures",
           "02_COMPUTATIONAL_CHEMISTRY/pseudopotentials", "02_COMPUTATIONAL_CHEMISTRY/molecular_dynamics", "02_COMPUTATIONAL_CHEMISTRY/migration",
           "02_COMPUTATIONAL_CHEMISTRY/validation", "02_COMPUTATIONAL_CHEMISTRY/raw_results", "02_COMPUTATIONAL_CHEMISTRY/convergence_reports",
           "03_ELECTROCHEMICAL_MODELLING/cell_models", "03_ELECTROCHEMICAL_MODELLING/electrolyte_models", "03_ELECTROCHEMICAL_MODELLING/gas_generation",
           "03_ELECTROCHEMICAL_MODELLING/thermal_models", "03_ELECTROCHEMICAL_MODELLING/degradation", "03_ELECTROCHEMICAL_MODELLING/fast_charging",
           "03_ELECTROCHEMICAL_MODELLING/validation_data", "04_MECHANICAL_CAD/cell", "04_MECHANICAL_CAD/electrode", "04_MECHANICAL_CAD/enclosure",
           "04_MECHANICAL_CAD/module", "04_MECHANICAL_CAD/thermal_management", "04_MECHANICAL_CAD/drawings", "04_MECHANICAL_CAD/assemblies",
           "04_MECHANICAL_CAD/native_sources", "05_ELECTRONICS/kicad", "05_ELECTRONICS/schematics", "05_ELECTRONICS/pcb", "05_ELECTRONICS/firmware",
           "05_ELECTRONICS/gerbers", "05_ELECTRONICS/bom", "06_PROCUREMENT", "06_PROCUREMENT/sds", "06_PROCUREMENT/quotations",
           "07_BUILD_MANUAL/safety", "07_BUILD_MANUAL/tools", "07_BUILD_MANUAL/parts", "07_BUILD_MANUAL/numbered_steps", "07_BUILD_MANUAL/assembly_maps",
           "07_BUILD_MANUAL/troubleshooting", "07_BUILD_MANUAL/acceptance_tests", "08_MANUFACTURING/lab_process", "08_MANUFACTURING/pilot_line",
           "08_MANUFACTURING/industrial_line", "08_MANUFACTURING/factory_layout", "08_MANUFACTURING/plc", "08_MANUFACTURING/robotics",
           "08_MANUFACTURING/inspection", "08_MANUFACTURING/quality_control", "09_VALIDATION/protocols", "09_VALIDATION/raw_measurements",
           "09_VALIDATION/cycle_life", "09_VALIDATION/fast_charging", "09_VALIDATION/abuse_testing", "09_VALIDATION/independent_reports",
           "10_ECONOMICS/bom_cost_model", "10_ECONOMICS/manufacturing_cost", "10_ECONOMICS/factory_capex", "10_ECONOMICS/lifetime_cost",
           "10_ECONOMICS/sensitivity_analysis", "11_MARKET/india", "11_MARKET/usa", "11_MARKET/global", "11_MARKET/customer_interviews",
           "11_MARKET/competitor_analysis", "12_YC", "12_YC/investor_deck", "12_YC/technical_data_room", "13_RELEASE/final_build_kit",
           "13_RELEASE/version_history"]
    why = {
        "02_COMPUTATIONAL_CHEMISTRY/molecular_dynamics": "not run this session (AIMD/MLIP-MD of NaAlCl4 melt or Na in beta''-alumina is a next step)",
        "03_ELECTROCHEMICAL_MODELLING/electrolyte_models": "no electrolyte model built (NaAlCl4 conductivity taken from literature ranges in S14)",
        "03_ELECTROCHEMICAL_MODELLING/degradation": "degradation results live in fast_charging/s13a_fast_charge.json (OKane2022 Li benchmark); no Na-MCl2 ageing model",
        "04_MECHANICAL_CAD/electrode": "electrode = cathode granule bed, modelled as item 6 inside cell/",
        "04_MECHANICAL_CAD/enclosure": "no module enclosure designed - gated on R0 results", "04_MECHANICAL_CAD/module": "no module designed - gated on R0",
        "04_MECHANICAL_CAD/thermal_management": "lab cell sits in a furnace; product thermal enclosure not designed",
        "06_PROCUREMENT/sds": "SDS not downloaded; hazard classes listed in master_bom.csv - obtain each SDS from the supplier at order",
        "06_PROCUREMENT/quotations": "no quotations requested or received", "08_MANUFACTURING/factory_layout": "floor areas only (industrial_line); no layout drawn",
        "08_MANUFACTURING/robotics": "covered in plc/AUTOMATION_SPEC.md; no robot cell designed", "08_MANUFACTURING/inspection": "covered in quality_control/QC_PLAN.md",
        "09_VALIDATION/raw_measurements": "no measurements exist", "09_VALIDATION/cycle_life": "protocol only (protocols/TEST_PLAN.md §3)",
        "09_VALIDATION/fast_charging": "protocol only (§4)", "09_VALIDATION/abuse_testing": "protocol only (§5)", "09_VALIDATION/independent_reports": "none exist",
        "10_ECONOMICS/manufacturing_cost": "in factory_capex/s15_results.json", "11_MARKET/usa": "in MARKET_ANALYSIS.md §2", "11_MARKET/global": "in MARKET_ANALYSIS.md §3",
        "02_COMPUTATIONAL_CHEMISTRY/convergence_reports": "convergence table is in validation/s11_results.json -> 'convergence'",
    }
    L = ["# BUILD STATUS (generated by tools/project_salt/assemble.py)", "",
         "Every folder below either holds real files or is listed as intentionally absent with the reason. No placeholders.", "",
         "| Folder (brief §15) | Files | Status |", "|---|---|---|"]
    for r in req:
        d = P / r; n = sum(1 for f in d.rglob("*") if f.is_file()) if d.exists() else 0
        st = "populated" if n else ("ABSENT - " + why.get(r, "not produced"))
        L.append(f"| `{r}` | {n} | {st} |")
    L += ["", f"Claims ledger rows: {nclaims}.", "",
          "## Progress register", "- Done: S11 (DFT+U: relax, U-scan, FM/AFM, PDOS; local M4 + EC2), S12, S13, S13a, S14, S15; CAD + drawing; SCM-1 schematic (ERC 0) + draft layout; firmware core (host tests);",
          "  BOM, build manual, hazard analysis, manufacturing, validation protocols, market, YC delta, release docs.",
          "- Done v1.1 (3 Nov, EC2 build host): D3 P1 cell + SM-48T module, D4 thermal architecture (S16), D5 SC-UPS-1 cabinet - build123d STEP, CADCraft drawings "
          "SB-SM-001/SB-TM-001/SB-UPS-001, Blender renders + turntable; SaltIron_Engineering_Model.xlsx (LibreOffice-verified); 9 MATLAB stem scripts (Octave); "
          "complete technical record (.docx/.pdf) and deck (.pptx/.pdf); Freerouting tried on SCM-1 (did not complete).",
          "- External execution required: everything in 07/09 (partner lab), quotes (06), interviews (11), independent review (13).", "",
          "## Unresolved questions", "1. Does a 0.5 mm beta''-alumina disc survive and conduct with a 100 mAh/cm2 salt-iron cathode (G4)?",
          "2. What does a purpose-built molten-salt line really cost per kWh/yr?", "3. Is there any priced premium for a hot-site, non-flammable battery in India (K4)?",
          "4. What is 'BFT+U'? (ask the founder)", "", "## Failed hypotheses (kept, not deleted)",
          "- Any salt-derived cell at 360 Wh/kg (S12) - fails.", "- 5-minute charging for 1,500 km (S13/S13a/S14) - fails.", "- $3/kWh in any cost reading (S13) - fails.",
          "- Aqueous Na-ion as the best 'salt battery' (earlier track) - dominated in S12.", "",
          "## Next experiments, compute and cost", "| Item | Time | Cost |", "|---|---|---|",
          "| K4 buyer interviews (20) | 4 weeks | ~INR 50k |", "| S-cell R0 campaign G1-G5 | 16-20 weeks | ~INR 12.5 lakh parts [ASSUMPTION] + partner fees |",
          "| DFT on EC2: NaCl vacancy NEB, Na6FeCl8 phase, orbital-ordered FeCl2, band structures | ~2-4 h on c8g.8xlarge spot | ~$2-4 |", "| SCM-1 layout completion + DRC clean | 1-2 engineer-days | - |",
          "| Independent review (3 experts) | 2-4 weeks | quote |", "", "## Reproducibility", "`./run_all.sh --project-salt` rebuilds this folder (see README)."]
    (P / "00_START_HERE/BUILD_STATUS.md").write_text("\n".join(L) + "\n")

def manifest():
    with open(P / "00_START_HERE/MANIFEST.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["path", "bytes", "sha256"])
        for p in sorted(P.rglob("*")):
            if p.is_file() and p.name != "MANIFEST.csv":
                w.writerow([str(p.relative_to(P)), p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()])

if __name__ == "__main__":
    copy_artifacts(); write_materials(); write_thermo(); write_dft_results(); n = claims(); kit_zip(); prune_empty(); build_status(n); manifest()
    print("PROJECT_SALT assembled;", n, "claims;", sum(1 for f in P.rglob('*') if f.is_file()), "files")
