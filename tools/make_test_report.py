"""Write DELIVERABLES/9_data/TEST_REPORT.md from pytest junit XML + S1/S2 validation outputs."""
import datetime, json, pathlib, sys, xml.etree.ElementTree as ET
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
x = ET.parse(sys.argv[1]).getroot()
suites = {}
for tc in x.iter("testcase"):
    f = tc.get("classname", "").split(".")[-1] or tc.get("file", "")
    st = "failed" if tc.find("failure") is not None or tc.find("error") is not None else ("skipped" if tc.find("skipped") is not None else "passed")
    suites.setdefault(f, {"passed": 0, "failed": 0, "skipped": 0, "fails": []})[st] += 1
    if st == "failed":
        suites[f]["fails"].append(tc.get("name"))
tot = {k: sum(s[k] for s in suites.values()) for k in ("passed", "failed", "skipped")}
s1 = json.loads((LAB / "sim/s01_kit_rerun/out/s1_comparison.json").read_text())
s2 = json.loads((LAB / "sim/s02_pybamm_validation/out/s02_validation.json").read_text())
L = [f"# Test report\n\nGenerated {datetime.datetime.now():%Y-%m-%d %H:%M} by `run_all.sh`.\n",
     f"**pytest: {tot['passed']} passed, {tot['failed']} failed, {tot['skipped']} skipped.**\n",
     "| Suite | Passed | Failed | Skipped |", "|---|---|---|---|"]
for k, s in sorted(suites.items()):
    L.append(f"| `{k}` | {s['passed']} | {s['failed']} | {s['skipped']} |")
L += ["", "## Model validation gates (scientific, not software)", "| Gate | Result |", "|---|---|",
      f"| S1 kit re-run vs kit expected outputs | {s1['n_pass']}/{s1['n_total']} pass |",
      f"| S2 PyBaMM independent validation (MAE ≤ 60 mV) | {'PASS' if s2['independent_validation_pass'] else 'FAIL (documented; see sim/s02_pybamm_validation/README.md)'} |",
      f"| S2 one-parameter calibrated variant | {'PASS' if s2['calibrated_pass'] else 'FAIL'} (calibration, not validation) |",
      "", "## What the suites cover",
      "- `test_params`: every value tagged; no MEASURED; assumptions ranged; design identities (energy = n·V·Ah, mass balance, fits the envelope).",
      "- `test_sim_models`: Faraday/Nernst conservation, S3 physicality, S5 literature regression, S9 refusal logic and cost sums, spreadsheet = python, S10 ordering, claims ledger completeness.",
      "- `test_docs_lint`: forbidden phrases and claim tag in the same paragraph or table row for every number in the deck, report and one-pager.",
      "- `test_cad_params` / `test_pcb` (if present): CAD bounding boxes = params; ERC/DRC zero errors; PCB ratings = params."]
if tot["failed"]:
    L += ["", "## Failures"] + [f"- `{k}`: {', '.join(s['fails'])}" for k, s in suites.items() if s["fails"]]
out = LAB / "DELIVERABLES/9_data/TEST_REPORT.md"; out.write_text("\n".join(L) + "\n"); print(out, tot)
