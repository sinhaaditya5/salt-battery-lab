#!/usr/bin/env python3
"""Summarise Freerouting attempts from its log (runs split where the pass counter restarts) -> pcb/scell_monitor/freeroute_attempts.json"""
import json, re, sys
from pathlib import Path
log = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/freerouting/freerouting.log").read_text(errors="ignore")
runs, cur, last = [], [], 0
for m in re.finditer(r"pass #(\d+) .*?score of ([\d.]+) \((\d+) unrouted\)", log):
    n, score, un = int(m.group(1)), float(m.group(2)), int(m.group(3))
    if n < last and cur: runs.append(cur); cur = []
    cur.append((n, score, un)); last = n
if cur: runs.append(cur)
cfg = ["2 signal layers (F/B), In1 GND + In2 +3V3 planes", "3 signal layers (F/In2/B), In1 GND plane, +3V3 routed"]
out = [dict(config=cfg[i] if i < len(cfg) else "?", passes=len(r), best_unrouted=min(u for *_, u in r), last_unrouted=r[-1][2]) for i, r in enumerate(runs)]
res = dict(tool="Freerouting 2.1.0 (headless, EC2 c7i.8xlarge)", attempts=out,
           decision="neither attempt completed the board; delivered layout uses the in-house router (DRAFT) - placement needs manual rework")
Path("/Volumes/Aditya ssd/Salt-Battery-Lab/pcb/scell_monitor/freeroute_attempts.json").write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
