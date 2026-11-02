"""Compare S1 re-run outputs against the kit's own expected files. Writes out/s1_comparison.json."""
import json, pathlib, filecmp
LAB = pathlib.Path("/Volumes/Aditya ssd/Salt-Battery-Lab")
SRC = LAB / "00_source_kit/Salt_Battery_R0_Reference_Cell_Kit_v1"
OUT = LAB / "sim/s01_kit_rerun/out"
def norm(t): return [l.rstrip() for l in t.replace("\r", "").strip().splitlines()]
checks = []
def text_check(name, got, exp):
    g, e = norm((OUT / got).read_text()), norm((SRC / exp).read_text())
    checks.append({"check": name, "pass": g == e, "got_lines": len(g), "expected_lines": len(e),
                   "first_diff": next((f"{a!r} != {b!r}" for a, b in zip(g, e) if a != b), None)})
text_check("calculator stdout == calculator_smoke_test.txt", "calculator.txt", "simulation/calculator_smoke_test.txt")
text_check("analyser stdout == analyzer_smoke_test.txt", "analyzer.txt", "simulation/analyzer_smoke_test.txt")
text_check("RC stdout == rc_smoke_test.txt", "rc.txt", "simulation/rc_smoke_test.txt")
text_check("cost guard output == cost_model_expected_block.txt", "cost_guard.txt", "economics/cost_model_expected_block.txt")
checks.append({"check": "cost guard exits non-zero", "pass": (OUT / "cost_guard_exit.txt").read_text().strip() != "0"})
for got, exp in [("analyzer_summary.json", "simulation/demo_analysis_output/summary.json"),
                 ("analyzer_cycle_summary.csv", "simulation/demo_analysis_output/cycle_summary.csv"),
                 ("rc_output.csv", "simulation/rc_demo_synthetic_output.csv")]:
    a, b = (OUT / got).read_text().replace("\r", ""), (SRC / exp).read_text().replace("\r", "")
    if got.endswith(".json"):
        ja, jb = json.loads(a), json.loads(b)
        ja.pop("input_file", None); jb.pop("input_file", None)
        ok = ja == jb
    else:
        ok = a.strip() == b.strip()
    checks.append({"check": f"{got} == kit {exp}", "pass": ok})
m = (OUT / "moonshot.txt").read_text()
checks.append({"check": "moonshot arithmetic ran", "pass": "kWh" in m or "kW" in m})
res = {"n_pass": sum(c["pass"] for c in checks), "n_total": len(checks), "checks": checks}
(OUT / "s1_comparison.json").write_text(json.dumps(res, indent=2))
for c in checks: print(("PASS " if c["pass"] else "FAIL ") + c["check"] + ("" if c["pass"] else f"  {c.get('first_diff')}"))
print(f"S1: {res['n_pass']}/{res['n_total']} checks pass")
