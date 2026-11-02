#!/usr/bin/env bash
# Rebuild every v1.1 salt-design artefact on the EC2 build host, in dependency order (no DFT, no full render set).
# Usage (build host): tools/ec2_build/rebuild_salt.sh [--renders shot1,shot2]
set -euo pipefail
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; cd "$LAB"; source tools/env.sh >/dev/null 2>&1
SHOTS="${2:-module_hero,module_cutaway}"
step() { echo "== $(date -u +%T) $*"; }
step thermal;     python sim/s16_module_thermal/thermal.py > /dev/null
step cad;         python cad/make_smodule.py | tail -1
step renders;     python renders/run_salt_renders.py --shots "$SHOTS"
step diagrams;    python diagrams/make_salt_diagrams.py > /dev/null
step stems;       (unset DISPLAY; TMPDIR=/tmp python tools/matlab/make_stem.py --run | grep -E '"engine"|returncode')
step pcb;         pcb/build_scm.sh | tail -3
step xlsx;        python finance/make_salt_model.py | grep -E '"verified"|errors'
step tests;       python -m pytest -q tests/ -p no:cacheprovider --junitxml=tests/junit_ec2.xml | tail -2
step screens;     python tools/ec2_build/make_screens.py | tail -1
step report;      python docs/make_full_report.py
step deck;        python docs/make_full_deck.py
step pdf;         (cd DELIVERABLES/1_investor_docs && for f in SaltBattery_Complete_Technical_Record.docx SaltBattery_Complete_Technical_Deck.pptx; do
                     soffice -env:UserInstallation=file:///tmp/lo_pdf --headless --convert-to pdf "$f" > /dev/null 2>&1; done; ls -la SaltBattery_Complete_*)
step validate;    (cd /work/skill_pptx/office && "$LAB/.venv/bin/python" validate.py "$LAB/DELIVERABLES/1_investor_docs/SaltBattery_Complete_Technical_Deck.pptx" | tail -2)
step qa;          rm -f /work/qa/*.png; mkdir -p /work/qa
                  python tools/ec2_build/contact.py DELIVERABLES/1_investor_docs/SaltBattery_Complete_Technical_Deck.pdf /work/qa/deck 6 2 1.0
                  python tools/ec2_build/contact.py DELIVERABLES/1_investor_docs/SaltBattery_Complete_Technical_Record.pdf /work/qa/rep 8 4 0.6
step done
