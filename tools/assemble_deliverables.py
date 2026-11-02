"""Copy generated outputs into DELIVERABLES/ and write the data-room index. Idempotent."""
import glob, json, pathlib, shutil, datetime
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
D = LAB / "DELIVERABLES"


def cp(pattern, dest, rename=None):
    dest = D / dest; dest.mkdir(parents=True, exist_ok=True); n = 0
    for f in sorted(glob.glob(str(LAB / pattern))):
        f = pathlib.Path(f)
        if f.is_file():
            name = rename(f) if rename else f.name
            shutil.copy2(f, dest / name); n += 1
    return n


def main():
    counts = {}
    counts["7_simulation_charts"] = sum(cp(f"sim/{s}/out/*.{e}", "7_simulation_charts", lambda f: f"{f.parents[1].name}__{f.name}")
                                        for s in ("s02_pybamm_validation", "s03_r1_cell", "s04_gas", "s05_atomistic", "s07_buildup", "s08_thermal", "s09_tea", "s10_market")
                                        for e in ("png", "svg", "caption.txt"))
    counts["8_diagrams"] = cp("diagrams/out/*", "8_diagrams")
    counts["9_data"] = sum(cp(p, "9_data", lambda f: f"{f.parents[1].name}__{f.name}") for p in
                           ("sim/s01_kit_rerun/out/s1_comparison.json", "sim/s02_pybamm_validation/out/s02_validation.json", "sim/s03_r1_cell/out/s03_results.json",
                            "sim/s04_gas/out/s04_results.json", "sim/s05_atomistic/out/s05_summary.json", "sim/s07_buildup/out/s07_results.json",
                            "sim/s08_thermal/out/s08_results.json", "sim/s09_tea/out/s09_results.json", "sim/s10_market/out/s10_results.json"))
    cp("CLAIMS_LEDGER.csv", "9_data"); cp("CLAIMS_LEDGER.csv", "10_data_room")
    for p in ("decisions/IDEA_v2.md", "decisions/DECISIONS.md", "decisions/RED_TEAM.md", "decisions/chemistry_matrix.csv",
              "research/sources.csv", "research/RESEARCH_NOTES.md", "research/COMPETITORS.csv", "DELIVERABLES/STARTUP_DECISION_MEMO.md",
              "DELIVERABLES/9_data/TEST_REPORT.md"):
        cp(p, "10_data_room")
    for p in ("DELIVERABLES/1_investor_docs/*",):
        cp(p, "10_data_room/investor_docs")
    cp("renders/out/*.png", "6_prototype_images"); cp("renders/out/*.mp4", "2_video")
    cp("cad/out/*.step", "3_cad_3d"); cp("cad/out/*.stl", "3_cad_3d"); cp("cad/out/*.glb", "3_cad_3d"); cp("cad/out/*partlist*.csv", "3_cad_3d")
    cp("drawings/out/*", "4_engineering_drawings")
    # index
    groups = [("0_YC_APPLICATION", "YC W27 answers (v2), founder video script, submit checklist"),
              ("1_investor_docs", "Investor deck (.pptx/.pdf), technical & business report (.docx/.pdf), one-pager (.pdf), financial model (.xlsx, live formulas)"),
              ("2_video", "Turntable / explainer video if rendered"), ("3_cad_3d", "STEP/STL/GLB of R0 test cell, R1 block, 48 V tray, UPS cabinet + part lists"),
              ("4_engineering_drawings", "CADCraft drawings (DXF/PDF/PNG), concept, not for fabrication"), ("5_pcb", "KiCad BMS/monitor board (+ cycler): schematics, layout, ERC/DRC, Gerbers, BOM, 3D renders"),
              ("6_prototype_images", "Blender concept renders, plain + annotated"), ("7_simulation_charts", "All simulation charts (PNG 300 dpi + SVG + tagged captions)"),
              ("8_diagrams", "Architecture, process flow, capex, validation ladder, safety, positioning, unit economics, roadmap, use of funds"),
              ("9_data", "Simulation result JSONs, claims ledger, TEST_REPORT.md"), ("10_data_room", "This index, decision documents, research sources, grants list, outreach pack"),
              ("11_screenshots", "Console snapshots and images captured while running tests, simulations, Blender, KiCad, DFT and document QA")]
    lines = [f"# Data room index\n\nGenerated {datetime.datetime.now():%Y-%m-%d %H:%M}. Pre-prototype: everything is simulation, calculation or literature; every number resolves in CLAIMS_LEDGER.csv.\n",
             "## Read in this order\n1. `STARTUP_DECISION_MEMO.md`: verdict, riskiest assumption, cheapest experiment, first 90 days\n2. `investor_docs/SaltBattery_OnePager.pdf`, then the deck and report\n3. `IDEA_v2.md`, `DECISIONS.md`, `RED_TEAM.md`\n4. `CLAIMS_LEDGER.csv` and `research/sources.csv` (in this folder as `sources.csv`)\n5. `TEST_REPORT.md`\n",
             "## Folders\n| Folder | Contents | Files |\n|---|---|---|"]
    for g, desc in groups:
        n = len([p for p in (D / g).rglob("*") if p.is_file()]) if (D / g).exists() else 0
        lines.append(f"| `{g}/` | {desc} | {n} |")
    lines.append("\n## Files in this folder\n" + "\n".join(f"- `{p.relative_to(D / '10_data_room')}`" for p in sorted((D / "10_data_room").rglob("*")) if p.is_file()))
    (D / "10_data_room" / "Data_Room_Index.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
