# Test report (interim, 2026-11-02 11:45 IST)

| Suite | Result |
|---|---|
| S1 kit re-run vs kit expected outputs | 9/9 pass |
| tests/test_params.py + tests/test_sim_models.py | 25 passed, 0 failed |
| S2 PyBaMM independent validation (60 mV gate) | **FAIL (documented)**: 67–121 mV MAE; calibrated variant passes (42–54 mV) |
| tests/test_docs_lint.py (forbidden phrases, claim IDs) | NOT RUN: deck, report and one-pager not generated yet |
| tests/test_cad_params.py, tests/test_pcb.py | Pending (CAD/PCB helpers stopped at usage limit; check those folders) |

Console snapshots: DELIVERABLES/11_screenshots/
