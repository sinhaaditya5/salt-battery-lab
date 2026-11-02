# Test report

Generated 2026-11-02 15:21 by `run_all.sh`.

**pytest: 28 passed, 0 failed, 0 skipped.**

| Suite | Passed | Failed | Skipped |
|---|---|---|---|
| `test_docs_lint` | 3 | 0 | 0 |
| `test_params` | 8 | 0 | 0 |
| `test_sim_models` | 17 | 0 | 0 |

## Model validation gates (scientific, not software)
| Gate | Result |
|---|---|
| S1 kit re-run vs kit expected outputs | 9/9 pass |
| S2 PyBaMM independent validation (MAE ≤ 60 mV) | FAIL (documented; see sim/s02_pybamm_validation/README.md) |
| S2 one-parameter calibrated variant | PASS (calibration, not validation) |

## What the suites cover
- `test_params`: every value tagged; no MEASURED; assumptions ranged; design identities (energy = n·V·Ah, mass balance, fits the envelope).
- `test_sim_models`: Faraday/Nernst conservation, S3 physicality, S5 literature regression, S9 refusal logic and cost sums, spreadsheet = python, S10 ordering, claims ledger completeness.
- `test_docs_lint`: forbidden phrases and claim tag in the same paragraph or table row for every number in the deck, report and one-pager.
- `test_cad_params` / `test_pcb` (if present): CAD bounding boxes = params; ERC/DRC zero errors; PCB ratings = params.
