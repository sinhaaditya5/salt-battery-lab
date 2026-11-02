#!/usr/bin/env bash
# S1 — macOS equivalent of the kit's scripts/run_software_checks.ps1, run on a writable copy in work/.
set -euo pipefail
LAB="/Volumes/Aditya ssd/Salt-Battery-Lab"; source "$LAB/tools/env.sh"
SRC="$LAB/00_source_kit/Salt_Battery_R0_Reference_Cell_Kit_v1"; W="$LAB/work/kit_rerun"; OUT="$LAB/sim/s01_kit_rerun/out"
rm -rf "$W"; mkdir -p "$W" "$OUT"; cp -R "$SRC/." "$W/"; chmod -R u+w "$W"; cd "$W"
PY="$LAB/.venv/bin/python"
echo "1/5 syntax";   "$PY" -m py_compile simulation/*.py economics/*.py
echo "2/5 calculator"; "$PY" simulation/cell_sizing_calculator.py --cells 3 > "$OUT/calculator.txt"
echo "3/5 analyser"; rm -rf simulation/demo_analysis_output
"$PY" simulation/analyze_cycler_csv.py simulation/demo_synthetic_data.csv --positive-active-mg 5 --negative-active-mg 5 --out-dir simulation/demo_analysis_output > "$OUT/analyzer.txt"
echo "4/5 RC model"; "$PY" simulation/equivalent_circuit_model.py simulation/rc_model_demo_synthetic_parameters.json simulation/current_profile_demo_synthetic.csv --output simulation/rc_demo_synthetic_output.csv > "$OUT/rc.txt"
echo "5/5 moonshot"; "$PY" simulation/moonshot_requirements.py --range-km 1500 --charge-minutes 5 --consumption-low 15 --consumption-high 20 --cell-whkg 875 > "$OUT/moonshot.txt"
echo "cost guard"; set +e; "$PY" economics/cost_model.py economics/cost_inputs_template.json > "$OUT/cost_guard.txt" 2>&1; CE=$?; set -e
echo "$CE" > "$OUT/cost_guard_exit.txt"
cp simulation/demo_analysis_output/summary.json "$OUT/analyzer_summary.json"; cp simulation/demo_analysis_output/cycle_summary.csv "$OUT/analyzer_cycle_summary.csv"
cp simulation/rc_demo_synthetic_output.csv "$OUT/rc_output.csv"
"$PY" "$LAB/sim/s01_kit_rerun/compare.py"
