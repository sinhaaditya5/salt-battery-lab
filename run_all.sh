#!/usr/bin/env bash
# Rebuild the whole Salt Battery package from source.
#   ./run_all.sh          full rebuild (incl. uMLIP relax + NEB ~1 h, Blender renders)
#   ./run_all.sh --fast   reuse uMLIP outputs and existing renders; rebuild everything else (~15 min)
# EC2/DFT is never launched here (it costs money): S6 results are only re-analysed from sim/s06_dft_ec2/runs*/.
set -euo pipefail
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; cd "$LAB"; source tools/env.sh
FAST=0; [ "${1:-}" = "--fast" ] && FAST=1
TS=$(date +%Y%m%dT%H%M); SHOT="$LAB/DELIVERABLES/11_screenshots"; LOG="$LAB/work/run_all_logs"; mkdir -p "$LOG"
step() { echo "== $1"; }
snap() { python tools/snap.py "$1" "$SHOT/$2/${TS}_$3.png" --title "$4" >/dev/null || true; }

step "S1 kit re-run";            ./sim/s01_kit_rerun/run.sh > "$LOG/s1.txt" 2>&1; snap "$LOG/s1.txt" 01_simulations S1 "S1 kit re-run"
step "S2 PyBaMM validation";     (cd sim/s02_pybamm_validation && python run_s02.py) > "$LOG/s2.txt" 2>&1; snap "$LOG/s2.txt" 01_simulations S2 "S2 validation"
step "S3 R1 cell DFN + MC";      (cd sim/s03_r1_cell && python run_s03.py) > "$LOG/s3.txt" 2>&1; snap "$LOG/s3.txt" 01_simulations S3 "S3 R1 cell"
step "S4 gas";                   python sim/s04_gas/run_s04.py > "$LOG/s4.txt" 2>&1; snap "$LOG/s4.txt" 01_simulations S4 "S4 gas"
if [ $FAST -eq 0 ]; then
  step "S5 structures + uMLIP (long)"
  (cd sim/s05_atomistic && python build_structures.py && python mlip_relax.py mace_mp0b3 4 && python mlip_relax.py chgnet 3 && python mlip_relax.py mace_mp0 4 && python mlip_neb.py mace_mp0b3 5) > "$LOG/s5.txt" 2>&1
  snap "$LOG/s5.txt" 01_simulations S5 "S5 uMLIP"
fi
step "S5/S6 analysis";           python sim/s05_atomistic/analyze.py > "$LOG/s5a.txt" 2>&1 || true
step "S7 build-up";              python sim/s07_buildup/run_s07.py > "$LOG/s7.txt" 2>&1; snap "$LOG/s7.txt" 01_simulations S7 "S7 build-up"
step "S8 thermal";               python sim/s08_thermal/run_s08.py > "$LOG/s8.txt" 2>&1; snap "$LOG/s8.txt" 01_simulations S8 "S8 thermal"
step "S9 TEA";                   python sim/s09_tea/run_s09.py > "$LOG/s9.txt" 2>&1; snap "$LOG/s9.txt" 01_simulations S9 "S9 TEA"
step "S10 market";               python sim/s10_market/run_s10.py > "$LOG/s10.txt" 2>&1; snap "$LOG/s10.txt" 01_simulations S10 "S10 market"
step "S11 DFT+U analysis (QE runs: sim/s11_dft_chlorides/campaign.py, not re-run here)"; python sim/s11_dft_chlorides/analyze.py > "$LOG/s11.txt" 2>&1 || true
step "S12 chemistry matrix";      python sim/s12_chemistry_matrix/matrix.py > "$LOG/s12.txt" 2>&1; snap "$LOG/s12.txt" 01_simulations S12 "S12 chemistry matrix"
step "S13 founder targets";       python sim/s13_founder_targets/targets.py > "$LOG/s13.txt" 2>&1; snap "$LOG/s13.txt" 01_simulations S13 "S13 founder targets"
if [ $FAST -eq 0 ]; then step "S13a PyBaMM fast charge + degradation (long)"; python sim/s13_founder_targets/fast_charge_pybamm.py > "$LOG/s13a.txt" 2>&1; fi
step "S14 salt-cell model";       python sim/s14_scell_model/scell_model.py > "$LOG/s14.txt" 2>&1
step "S15 factory scenarios";     python sim/s15_factory/factory.py > "$LOG/s15.txt" 2>&1
step "S-cell CAD + drawing";      python cad/make_scell.py > "$LOG/scell_cad.txt" 2>&1
step "SCM-1 PCB (draft) + firmware tests"; pcb/build_scm.sh > "$LOG/scm_pcb.txt" 2>&1 || echo "SCM-1 build reported errors"; make -C pcb/scell_monitor/firmware test > "$LOG/fw.txt" 2>&1 || echo "firmware tests FAILED"
step "procurement + assembly map"; python tools/project_salt/make_procurement.py > "$LOG/proc.txt" 2>&1; python tools/project_salt/render_exploded.py >> "$LOG/proc.txt" 2>&1
step "PROJECT_SALT assemble";     python tools/project_salt/assemble.py > "$LOG/project_salt.txt" 2>&1
step "diagrams";                 python diagrams/make_diagrams.py > "$LOG/diagrams.txt" 2>&1
step "financial model";          python finance/make_financial_model.py > "$LOG/fin.txt" 2>&1
rm -rf work/xlsx_check/recalced; "$SOFFICE" $LO_PROFILE --headless --convert-to pdf --outdir work/xlsx_check/recalced DELIVERABLES/1_investor_docs/SaltBattery_Financial_Model.xlsx > /dev/null 2>&1 || true
if [ -x cad/build_all_mech.sh ]; then step "CAD / drawings / renders"
  if [ $FAST -eq 1 ]; then cad/build_all_mech.sh --no-render > "$LOG/mech.txt" 2>&1 || echo "mech build reported errors (see $LOG/mech.txt)"; else cad/build_all_mech.sh > "$LOG/mech.txt" 2>&1 || echo "mech build reported errors"; fi
  snap "$LOG/mech.txt" 05_cad_drawings mech "CAD + drawings build"; fi
if [ -x pcb/build_pcb.sh ]; then step "PCB (ERC/DRC/Gerbers)"; pcb/build_pcb.sh > "$LOG/pcb.txt" 2>&1 || echo "PCB build reported errors"; snap "$LOG/pcb.txt" 04_pcb pcb "KiCad build: ERC/DRC"; fi
step "claims + documents";       python docs/claims.py > /dev/null; python docs/make_deck.py > "$LOG/docs.txt" 2>&1; python docs/make_report.py >> "$LOG/docs.txt" 2>&1
step "PDF export";               "$SOFFICE" $LO_PROFILE --headless --convert-to pdf --outdir DELIVERABLES/1_investor_docs DELIVERABLES/1_investor_docs/SaltBattery_Investor_Deck.pptx DELIVERABLES/1_investor_docs/SaltBattery_Technical_and_Business_Report.docx DELIVERABLES/1_investor_docs/SaltBattery_OnePager.docx > /dev/null 2>&1
python - <<'PY'
import pypdfium2 as pdfium, pathlib
d = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab/DELIVERABLES"); out = d / "11_screenshots/07_documents_qa"; out.mkdir(parents=True, exist_ok=True)
for name in ("SaltBattery_Investor_Deck", "SaltBattery_Technical_and_Business_Report", "SaltBattery_OnePager"):
    pdf = pdfium.PdfDocument(str(d / "1_investor_docs" / f"{name}.pdf"))
    for i in range(len(pdf)):
        pdf[i].render(scale=1.0).to_pil().save(out / f"{name}_p{i+1:02d}.png")
PY
step "video";                    python video/make_video.py > "$LOG/video.txt" 2>&1 || echo "video step failed"
mkdir -p DELIVERABLES/2_video; cp video/out/SaltBattery_explainer.* DELIVERABLES/2_video/ 2>/dev/null || true
step "lint";                     python docs/lint.py DELIVERABLES/1_investor_docs/*.pptx DELIVERABLES/1_investor_docs/*.docx > "$LOG/lint.txt" 2>&1 || true; snap "$LOG/lint.txt" 07_documents_qa lint "claims linter"
step "tests";                    python -m pytest tests -q --junitxml=work/junit.xml > "$LOG/pytest.txt" 2>&1 || true
python tools/make_test_report.py work/junit.xml > /dev/null; snap "$LOG/pytest.txt" 02_tests pytest "pytest tests/"
step "assemble + zip";           python tools/assemble_deliverables.py > /dev/null
rm -f DELIVERABLES.zip; (cd "$LAB" && zip -qr DELIVERABLES.zip DELIVERABLES -x "*.DS_Store")
tail -3 "$LOG/pytest.txt"; ls -la DELIVERABLES.zip
