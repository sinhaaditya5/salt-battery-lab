"""Autoroute a placed board with Freerouting (headless) and import the result.  Runs in KiCad's Python (pcbnew).

usage: <kicad python> freeroute.py <board.kicad_pcb> <board_dir> <design_module> [max_passes]

1. LoadBoard (pulls net classes/patterns from the .kicad_pro, so Power = 0.5 mm etc. reach the DSN)
2. inner copper layers -> POWER type (planes only; Freerouting keeps signals on F/B.Cu)
3. isolation keepouts: rule areas (no tracks, no vias) on the DOMAIN_GAP strip around every isolated region
4. ExportSpecctraDSN -> java -jar $FREEROUTING_JAR -de .dsn -do .ses (no GUI) -> ImportSpecctraSES -> save
Writes freeroute_report.json (passes, wall time, track/via counts, Freerouting log tail).
"""
import importlib, json, os, subprocess, sys, time
import pcbnew

mm = pcbnew.FromMM
OX, OY = 20.0, 20.0          # same board origin as pcbbuild.py


def rule_area(board, x0, y0, x1, y1, name):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    try:
        z.SetDoNotAllowZoneFills(False)
    except AttributeError:
        z.SetDoNotAllowCopperPour(False)
    z.SetLayerSet(pcbnew.LSET.AllCuMask())
    o = z.Outline(); o.NewOutline()
    for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(mm(x + OX), mm(y + OY))
    z.SetZoneName(name)
    board.Add(z)


def main():
    pcb, board_dir, modname = sys.argv[1:4]
    passes = int(sys.argv[4]) if len(sys.argv) > 4 else 60
    sys.path.insert(0, os.path.abspath(board_dir))
    D = importlib.import_module(modname)
    board = pcbnew.LoadBoard(pcb)
    inner_signal = os.environ.get("FR_INNER_SIGNAL") == "1"      # In1 = GND plane; In2 becomes a routing layer (+3V3 as traces)
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_SIGNAL if inner_signal else pcbnew.LT_POWER)
    if inner_signal:
        for z in list(board.Zones()):
            if not z.GetIsRuleArea() and z.GetLayer() == pcbnew.In2_Cu:
                board.Remove(z)
    W, H = D.BOARD_W, D.BOARD_H
    for dom, rects in D.regions().items():
        kind = D.domain_kind(dom)
        gap = D.DOMAIN_GAP.get((kind, "LV")) or D.DOMAIN_GAP.get(("LV", kind))
        for k, (x0, y0, x1, y1) in enumerate(rects):
            if x1 < W - 0.5: rule_area(board, x1, max(0, y0 - gap), min(W, x1 + gap), min(H, y1 + gap), f"ISO_GAP_{dom}_{k}_R")
            if y1 < H - 0.5: rule_area(board, max(0, x0 - gap), y1, min(W, x1 + gap), min(H, y1 + gap), f"ISO_GAP_{dom}_{k}_B")
            if x0 > 0.5: rule_area(board, max(0, x0 - gap), max(0, y0 - gap), x0, min(H, y1 + gap), f"ISO_GAP_{dom}_{k}_L")
            if y0 > 0.5: rule_area(board, max(0, x0 - gap), max(0, y0 - gap), min(W, x1 + gap), y0, f"ISO_GAP_{dom}_{k}_T")
    base = os.path.splitext(pcb)[0]
    dsn, ses = base + ".dsn", base + ".ses"
    ok = pcbnew.ExportSpecctraDSN(board, dsn)
    jar = os.environ.get("FREEROUTING_JAR", "/opt/freerouting/freerouting.jar")
    t0 = time.time()
    cmd = ["java", "-Djava.awt.headless=true", "-jar", jar, "-de", dsn, "-do", ses, "-mp", str(passes), "--gui.enabled=false"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    wall = time.time() - t0
    rep = dict(inner_signal=inner_signal, dsn_export=bool(ok), cmd=" ".join(cmd), returncode=r.returncode, wall_s=round(wall, 1),
               log_tail=(r.stdout + r.stderr)[-3000:], ses_exists=os.path.exists(ses))
    if os.path.exists(ses):
        rep["ses_import"] = bool(pcbnew.ImportSpecctraSES(board, ses))
        rep["tracks"] = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_TRACK")
        rep["vias"] = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA")
        pcbnew.SaveBoard(pcb, board)
    with open(os.path.join(board_dir, "freeroute_report.json"), "w") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "log_tail"}))
    sys.exit(0 if rep.get("ses_import") else 1)


if __name__ == "__main__":
    main()
