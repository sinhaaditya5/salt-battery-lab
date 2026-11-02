# S1: Kit re-run
**Question:** Do the kit's own scripts reproduce the kit's expected outputs on macOS, run on an untouched copy?
**Model:** The kit's scripts (cell sizing, cycler analyser, RC model, moonshot arithmetic, cost-model guard), run on `work/kit_rerun/` with the lab venv.
**Validation:** `compare.py` diffs each output against the kit's `*_smoke_test.txt`, `cost_model_expected_block.txt` and the demo output files. **Result:** `out/s1_comparison.json`, 9/9 pass [CALC; C-101].
**Limits:** Software checks only. Every demo input is synthetic, and nothing here is electrochemistry.
Run: `./run.sh`
