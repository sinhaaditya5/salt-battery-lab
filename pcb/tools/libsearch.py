"""Search the KiCad bundled symbol libraries for symbol names (dev helper)."""
import re, sys, pathlib
S = pathlib.Path("/Volumes/Aditya ssd/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
pats = sys.argv[1:]
for f in sorted(S.glob("*.kicad_sym")):
    txt = f.read_text(errors="ignore")
    names = re.findall(r'^\t\(symbol "([^"]+)"', txt, re.M)
    for p in pats:
        hits = [n for n in names if re.search(p, n, re.I)]
        if hits:
            print(f"{p:14s} {f.stem}: {', '.join(hits[:12])}")
