#!/usr/bin/env python3
"""Assemble the co-founder delivery pack (copies only; sources are never modified)."""
import glob, hashlib, os, re, shutil, sys
from pathlib import Path

LAB = Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
PACK = LAB / "SEND_TO_COFOUNDER" / "SaltBattery_Pack_2026-11-03"

SKIP_NAMES = {".DS_Store", "__pycache__"}
SKIP_RE = re.compile(r"(^~.*\.lck$|\.pyc$|\.kicad_prl$|_commands\.jsonl$)")
missing = []


def cp(src, dst_dir, name=None):
    src = LAB / src
    if not src.exists():
        missing.append(str(src)); return
    d = PACK / dst_dir
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, d / (name or src.name))


def cpg(pattern, dst_dir, exclude=None):
    hits = sorted(glob.glob(str(LAB / pattern)))
    if not hits:
        missing.append(pattern)
    for h in hits:
        n = os.path.basename(h)
        if n in SKIP_NAMES or SKIP_RE.search(n) or (exclude and re.search(exclude, n)):
            continue
        if os.path.isfile(h):
            cp(os.path.relpath(h, LAB), dst_dir)


def cptree(src, dst_dir, skip_dirs=()):
    s = LAB / src
    if not s.exists():
        missing.append(str(s)); return
    for root, dirs, files in os.walk(s):
        rel = Path(root).relative_to(s)
        dirs[:] = [x for x in dirs if x not in SKIP_NAMES and str(rel / x) not in skip_dirs]
        for f in files:
            if f in SKIP_NAMES or SKIP_RE.search(f):
                continue
            cp(Path(src) / rel / f, Path(dst_dir) / rel)


if PACK.exists():
    shutil.rmtree(PACK)
PACK.mkdir(parents=True)

# 01 verdict & decisions
D = "01_Start_Here_Verdict_and_Decisions"
cp("DELIVERABLES/STARTUP_DECISION_MEMO.md", D)
for f in ["EXECUTIVE_VERDICT.md", "BUILD_STATUS.md", "TECHNICAL_GLOSSARY.md"]:
    cp(f"PROJECT_SALT/00_START_HERE/{f}", D)
cp("PROJECT_SALT/13_RELEASE/known_limitations.md", D)
cp("PROJECT_SALT/13_RELEASE/independent_review.md", D)
cp("PROJECT_SALT/13_RELEASE/version_history/CHANGELOG.md", D)
cp("CLAIMS_LEDGER.csv", D, "CLAIMS_LEDGER_aqueous_UPS_track.csv")
cp("PROJECT_SALT/00_START_HERE/CLAIMS_LEDGER.csv", D, "CLAIMS_LEDGER_project_salt_track.csv")
cpg("decisions/*", f"{D}/decision_log")

# 02 decks & reports
D = "02_Pitch_Deck_and_Reports"
for f in ["SaltBattery_Complete_Technical_Deck.pptx", "SaltBattery_Complete_Technical_Deck.pdf",
          "SaltBattery_Complete_Technical_Record.docx", "SaltBattery_Complete_Technical_Record.pdf"]:
    cp(f"DELIVERABLES/1_investor_docs/{f}", f"{D}/A_LATEST_complete_record_3Nov")
for f in ["SaltBattery_Investor_Deck.pptx", "SaltBattery_Investor_Deck.pdf",
          "SaltBattery_Technical_and_Business_Report.docx", "SaltBattery_Technical_and_Business_Report.pdf",
          "SaltBattery_OnePager.docx", "SaltBattery_OnePager.pdf"]:
    cp(f"DELIVERABLES/1_investor_docs/{f}", f"{D}/B_first_pitch_aqueous_UPS_2Nov")
cp("PROJECT_SALT/12_YC/investor_deck/DECK_ERRATA.md", f"{D}/B_first_pitch_aqueous_UPS_2Nov",
   "READ_FIRST_Deck_Errata.md")

# 03 YC
D = "03_YC_Application"
cp("DELIVERABLES/0_YC_APPLICATION/YC_W27_answers.md", D, "YC_W27_answers_v3.md")
cp("PROJECT_SALT/12_YC/application.md", D, "YC_W27_answers_v4_changes_on_top_of_v3.md")
cp("DELIVERABLES/0_YC_APPLICATION/YC_SUBMIT_CHECKLIST.md", D)
cp("DELIVERABLES/0_YC_APPLICATION/YC_founder_video_script.md", D)
cp("PROJECT_SALT/12_YC/founder_video.md", D, "YC_founder_video_v4_notes.md")
cp("PROJECT_SALT/12_YC/company_thesis.md", D)
cp("PROJECT_SALT/12_YC/evidence_register.csv", D)
cp("PROJECT_SALT/12_YC/technical_data_room/DATA_ROOM_INDEX.md", D, "Technical_Data_Room_Index.md")

# 04 spreadsheets & BOMs
D = "04_Spreadsheets_and_BOMs"
cp("PROJECT_SALT/10_ECONOMICS/SaltIron_Engineering_Model.xlsx", D)
cp("DELIVERABLES/1_investor_docs/SaltBattery_Financial_Model.xlsx", D)
cpg("PROJECT_SALT/06_PROCUREMENT/*.csv", f"{D}/procurement_BOMs")
cpg("cad/out/smodule/*_partlist.csv", f"{D}/part_lists_salt_iron")
cp("cad/out/scell/scell_r0_partlist.csv", f"{D}/part_lists_salt_iron")
cpg("cad/out/r*_partlist.csv", f"{D}/part_lists_aqueous_UPS")
cp("pcb/scell_monitor/fab/scell_monitor-bom.csv", f"{D}/electronics_BOM")

# 05 3D CAD
D = "05_3D_CAD_Engineering_Designs"
S = f"{D}/A_salt_iron_designs_LATEST"
cptree("PROJECT_SALT/04_MECHANICAL_CAD", S, skip_dirs=("renders", "drawings"))
for p in ["p1_cell", "sm48t_module", "sc_ups1_cabinet"]:
    cptree(f"cad/out/stl/{p}", f"{S}/stl_per_part/{p}")
A = f"{D}/B_aqueous_UPS_designs_first_pitch"
for p in ["r0_test_cell", "r1_cell", "r1_monobloc", "r1_module48", "r1_ups_cabinet"]:
    for ext in ["step", "stl", "glb"]:
        cp(f"cad/out/{p}.{ext}", A)
    cp(f"cad/out/{p}_partlist.csv", A)
cp("cad/out/cad_meta.json", A)
cpg("renders/out/previews/*.png", f"{A}/previews")

# 06 drawings
D = "06_Engineering_Drawings_CADCraft"
for dwg in ["SB-SC-001", "SB-SM-001", "SB-TM-001", "SB-UPS-001"]:
    for ext in ["pdf", "dxf", "png"]:
        cp(f"drawings/out/{dwg}.{ext}", f"{D}/A_salt_iron_LATEST")
for dwg in ["SB-GA-001", "SB-GA-002", "SB-GA-003"]:
    for ext in ["pdf", "dxf", "png"]:
        cp(f"drawings/out/{dwg}.{ext}", f"{D}/B_aqueous_UPS_first_pitch")

# 07 renders & video
D = "07_Blender_Renders_and_Video"
cpg("renders/out_salt/*.png", f"{D}/A_salt_iron_renders_LATEST", exclude=r"^test_")
cp("renders/out_salt/sm48t_turntable.mp4", f"{D}/A_salt_iron_renders_LATEST", "SM-48T_module_turntable.mp4")
cpg("renders/out/*.png", f"{D}/B_aqueous_UPS_renders_first_pitch")
cp("video/out/SaltBattery_explainer.mp4", f"{D}/C_explainer_video")
cp("video/out/SaltBattery_explainer.srt", f"{D}/C_explainer_video")

# 08 PCB / KiCad
D = "08_PCB_KiCad"
K = f"{D}/A_SCM-1_salt_cell_test_monitor_LATEST"
for pat in ["*.kicad_pro", "*.kicad_sch", "*.kicad_pcb", "*.kicad_dru", "*.net", "sym-lib-table", "fp-lib-table"]:
    cpg(f"pcb/scell_monitor/{pat}", f"{K}/kicad_project")
cp("pcb/lib/scm_pcb.kicad_sym", f"{K}/kicad_project/lib")
cptree("pcb/scell_monitor/fab", f"{K}/fabrication_outputs_DRAFT_review_only")
for f in ["erc.json", "drc.json", "route_report.json", "freeroute_attempts.json"]:
    cp(f"pcb/scell_monitor/{f}", f"{K}/check_reports")
cptree("pcb/scell_monitor/firmware", f"{K}/firmware")
cp("PROJECT_SALT/05_ELECTRONICS/README.md", K)
B = f"{D}/B_BMS_monitor_first_pitch_DRAFT"
for pat in ["*.kicad_pro", "*.kicad_sch", "*.kicad_pcb", "*.kicad_dru", "*.net", "sym-lib-table", "fp-lib-table"]:
    cpg(f"pcb/bms_monitor/{pat}", f"{B}/kicad_project")
cp("pcb/lib/salt_pcb.kicad_sym", f"{B}/kicad_project/lib")
cp("pcb/bms_monitor/route_report.json", f"{B}/check_reports")

# 09 charts & simulations
D = "09_Charts_and_Simulations"
for s in ["s11_dft_chlorides", "s12_chemistry_matrix", "s13_founder_targets", "s14_scell_model", "s15_factory", "s16_module_thermal"]:
    for ext in ["png", "svg", "caption.txt", "json"]:
        cpg(f"sim/{s}/out/*.{ext}", f"{D}/A_salt_iron_track_s11-s16/{s}")
cpg("DELIVERABLES/7_simulation_charts/*", f"{D}/B_aqueous_UPS_track_s02-s10")
cpg("DELIVERABLES/9_data/*.json", f"{D}/B_aqueous_UPS_track_s02-s10/result_data")
cp("DELIVERABLES/9_data/TEST_REPORT.md", D, "TEST_REPORT_aqueous_track.md")
cpg("matlab/stem/*.m", f"{D}/C_MATLAB_stem_plots/scripts")
cp("matlab/stem/stem_manifest.json", f"{D}/C_MATLAB_stem_plots")
cpg("matlab/stem/out/*.png", f"{D}/C_MATLAB_stem_plots")

# 10 diagrams
D = "10_Diagrams"
cpg("diagrams/out/ds*", f"{D}/A_salt_iron_ds1-ds5")
cpg("diagrams/out/d[0-9]_*", f"{D}/B_aqueous_UPS_d1-d9")

# 11 technical package (Project Salt deep-dive docs not already above)
D = "11_Technical_Package_Project_Salt"
for sub in ["01_SCIENTIFIC_RESEARCH", "03_ELECTROCHEMICAL_MODELLING", "06_PROCUREMENT", "07_BUILD_MANUAL",
            "08_MANUFACTURING", "09_VALIDATION", "10_ECONOMICS", "11_MARKET"]:
    cptree(f"PROJECT_SALT/{sub}", f"{D}/{sub}")
cptree("PROJECT_SALT/02_COMPUTATIONAL_CHEMISTRY", f"{D}/02_COMPUTATIONAL_CHEMISTRY", skip_dirs=("raw_results",))
cp("PROJECT_SALT/13_RELEASE/final_build_kit/S-cell_R0_build_kit.zip", f"{D}/13_R0_test_cell_build_kit")

# 12 research & data room
D = "12_Research_and_Data_Room"
for f in ["sources.csv", "sources_project_salt.csv", "RESEARCH_NOTES.md", "COMPETITORS.csv", "GRANTS_AND_FUNDING.md"]:
    cp(f"research/{f}", D)
cptree("research/papers", f"{D}/papers")
cptree("research/datasheets", f"{D}/datasheets")
for f in ["Data_Room_Index.md", "OUTREACH_PACK.md"]:
    cp(f"DELIVERABLES/10_data_room/{f}", D)

# 13 screenshots
D = "13_Screenshots"
for sub in sorted(os.listdir(LAB / "DELIVERABLES/11_screenshots")):
    p = LAB / "DELIVERABLES/11_screenshots" / sub
    if p.is_dir() and any(x for x in os.listdir(p) if x != ".DS_Store"):
        cptree(f"DELIVERABLES/11_screenshots/{sub}", f"{D}/{sub}")

# --- make the KiCad library tables portable (the copies only) ---
KICAD_APP = "/Volumes/Aditya ssd/Applications/KiCad/KiCad.app/Contents/SharedSupport"
for t in PACK.rglob("*-lib-table"):
    txt = t.read_text()
    txt = txt.replace(f"{KICAD_APP}/symbols/", "${KICAD10_SYMBOL_DIR}/")
    txt = txt.replace(f"{KICAD_APP}/footprints/", "${KICAD10_FOOTPRINT_DIR}/")
    txt = txt.replace(f"{LAB}/pcb/lib/", "${KIPRJMOD}/lib/")
    t.write_text(txt)

# README (source kept in tools/) and checksum list
shutil.copy2(LAB / "tools/cofounder_pack_README.md", PACK / "README_START_HERE.md")
import csv
rows = []
for root, dirs, files in os.walk(PACK):
    dirs.sort()
    for f in sorted(files):
        fp = Path(root) / f
        if f in SKIP_NAMES or f == "FILE_LIST.csv":
            continue
        rows.append((str(fp.relative_to(PACK)), fp.stat().st_size, hashlib.sha256(fp.read_bytes()).hexdigest()))
with open(PACK / "FILE_LIST.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["path", "bytes", "sha256"]); w.writerows(rows)
# zip: cd SEND_TO_COFOUNDER && zip -r -X -q SaltBattery_Pack_2026-11-03.zip SaltBattery_Pack_2026-11-03 -x '*.DS_Store'

if missing:
    print("MISSING:", *missing, sep="\n  ")
    sys.exit(1)
print("ok")
