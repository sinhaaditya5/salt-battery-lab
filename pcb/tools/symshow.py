"""Print pins/footprint of KiCad library symbols (dev helper). usage: symshow.py Lib:Name ..."""
import re, sys, pathlib
S = pathlib.Path("/Volumes/Aditya ssd/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
def block(txt, name):
    i = txt.find(f'\n\t(symbol "{name}"')
    if i < 0: return None
    j = txt.find('\n\t(symbol "', i + 5)
    return txt[i: j if j > 0 else len(txt)]
for arg in sys.argv[1:]:
    lib, name = arg.split(":")
    txt = (S / f"{lib}.kicad_sym").read_text()
    b = block(txt, name)
    ext = re.search(r'\(extends "([^"]+)"\)', b)
    fp = re.search(r'\(property "Footprint" "([^"]*)"', b).group(1)
    print(f"===== {arg}  extends={ext.group(1) if ext else None} fp={fp}")
    if ext: b = block(txt, ext.group(1))
    for m in re.finditer(r'\(symbol "[^"]+_(\d+)_(\d+)"', b):
        pass
    pins = re.findall(r'\(pin (\w+) (\w+)\s+\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s+\(length [\d.]+\)\s*(\(hide yes\)|hide)?\s*\(name "([^"]*)"[\s\S]*?\(number "([^"]*)"', b)
    out = [f"{p[7]}:{p[6]}[{p[0][:5]}{',H' if p[5] else ''}]" for p in pins]
    units = sorted(set(re.findall(r'\(symbol "[^"]+_(\d+)_\d+"', b)))
    print(f"  units={units} npins={len(pins)}")
    print("  " + "  ".join(out))
