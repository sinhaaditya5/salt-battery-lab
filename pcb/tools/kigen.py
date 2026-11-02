"""kigen -- tiny programmatic KiCad schematic/project generator (Salt-Battery-Lab, concept PCBs).

Python 3.9 compatible, no third-party deps.  A design is a list of parts; every part pin is
assigned a net name (or None = explicit no-connect).  The schematic is written as a root sheet
plus sub-sheets; every pin is connected by a *global label placed exactly on the pin end*,
so ERC sees real connectivity and the PDF stays readable (one symbol = one block of labels).

Library symbols are read from the KiCad bundle (or project libs), flattened if derived
("extends"), and embedded in lib_symbols exactly like eeschema does.
"""
import os, re, uuid, json, math, hashlib

KICAD_SHARE = "/Volumes/Aditya ssd/Applications/KiCad/KiCad.app/Contents/SharedSupport"
if not os.path.isdir(KICAD_SHARE):          # Linux build host (EC2): KiCad PPA install
    KICAD_SHARE = "/usr/share/kicad"
SYM_DIR = os.path.join(KICAD_SHARE, "symbols")
FP_DIR = os.path.join(KICAD_SHARE, "footprints")

# ------------------------------------------------------------------------------------------
# S-expressions
# ------------------------------------------------------------------------------------------
class Q(str):
    """quoted string atom"""


def parse_sexpr(text):
    tok = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')
    stack, cur = [], []
    for m in tok.finditer(text):
        t = m.group(0)
        if t == "(":
            stack.append(cur); cur = []
        elif t == ")":
            done = cur; cur = stack.pop(); cur.append(done)
        elif t[0] == '"':
            cur.append(Q(t[1:-1].replace('\\"', '"').replace("\\\\", "\\").replace("\\n", "\n")))
        else:
            cur.append(t)
    return cur[0]


def _atom(a):
    if isinstance(a, Q):
        return '"' + a.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(a, float):
        s = ("%.4f" % a).rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return str(a)


def dump(node, ind=0):
    if not isinstance(node, list):
        return _atom(node)
    simple = all(not isinstance(x, list) for x in node)
    if simple or (len(node) <= 4 and all(not isinstance(x, list) or all(not isinstance(y, list) for y in x) for x in node) and len(str(node)) < 90):
        return "(" + " ".join(dump(x) for x in node) + ")"
    out = "(" + " ".join(dump(x) for x in node[:1])
    i = 1
    while i < len(node) and not isinstance(node[i], list):
        out += " " + _atom(node[i]); i += 1
    for x in node[i:]:
        out += "\n" + "\t" * (ind + 1) + dump(x, ind + 1)
    return out + "\n" + "\t" * ind + ")"


def find(node, key):
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def findall(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def uid(*seed):
    """deterministic UUID so rebuilds are reproducible"""
    h = hashlib.sha1(("|".join(str(s) for s in seed)).encode()).hexdigest()
    return str(uuid.UUID(h[:32]))


# ------------------------------------------------------------------------------------------
# library symbols
# ------------------------------------------------------------------------------------------
_LIBCACHE = {}
EXTRA_LIBS = {}   # name -> path of project-local .kicad_sym


def _load_lib(lib):
    if lib not in _LIBCACHE:
        path = EXTRA_LIBS.get(lib, os.path.join(SYM_DIR, lib + ".kicad_sym"))
        with open(path, encoding="utf-8") as f:
            _LIBCACHE[lib] = parse_sexpr(f.read())
    return _LIBCACHE[lib]


def _raw_symbol(lib, name):
    root = _load_lib(lib)
    for s in findall(root, "symbol"):
        if s[1] == name:
            return s
    raise KeyError("%s:%s not found" % (lib, name))


def flat_symbol(lib_id):
    """Return a flattened deep copy of the library symbol, renamed 'Lib:Name'."""
    lib, name = lib_id.split(":")
    s = _requote(_raw_symbol(lib, name))
    ext = find(s, "extends")
    if ext:
        parent = flat_symbol(lib + ":" + ext[1])
        child_props = {p[1]: p for p in findall(s, "property")}
        out = [parent[0], Q(name)]
        for x in parent[2:]:
            if isinstance(x, list) and x[0] == "property" and x[1] in child_props:
                out.append(child_props.pop(x[1]))
            elif isinstance(x, list) and x[0] == "symbol":
                sub = list(x)
                sub[1] = Q(re.sub("^" + re.escape(ext[1]) + "_", name + "_", sub[1]))
                out.append(sub)
            else:
                out.append(x)
        # remaining child-only properties go before the first sub-symbol
        idx = next(i for i, x in enumerate(out) if isinstance(x, list) and x[0] == "symbol")
        for p in child_props.values():
            out.insert(idx, p); idx += 1
        s = out
    s[1] = Q(lib_id)
    return s


def _requote(node):
    """deep copy preserving Q atoms"""
    if isinstance(node, list):
        return [_requote(x) for x in node]
    if isinstance(node, Q):
        return Q(str(node))
    return node


class SymInfo:
    def __init__(self, lib_id):
        self.lib_id = lib_id
        self.node = flat_symbol(lib_id)
        name = lib_id.split(":")[1]
        self.props = {p[1]: p[2] for p in findall(self.node, "property")}
        self.pins = []   # dict(number,name,type,x,y,a,len,hidden)
        xs, ys = [], []
        for sub in findall(self.node, "symbol"):
            m = re.match(r".*_(\d+)_(\d+)$", sub[1])
            unit, style = int(m.group(1)), int(m.group(2))
            if style not in (0, 1) or unit not in (0, 1):
                continue
            for g in sub[2:]:
                if not isinstance(g, list):
                    continue
                if g[0] == "pin":
                    at = find(g, "at"); ln = float(find(g, "length")[1])
                    hidden = ("hide" in g) or any(isinstance(x, list) and x[0] == "hide" and x[1] == "yes" for x in g)
                    p = dict(type=g[1], number=str(find(g, "number")[1]), name=str(find(g, "name")[1]),
                             x=float(at[1]), y=float(at[2]), a=int(float(at[3])), len=ln, hidden=hidden)
                    self.pins.append(p)
                    xs.append(p["x"]); ys.append(p["y"])
                elif g[0] in ("rectangle",):
                    for k in ("start", "end"):
                        v = find(g, k); xs.append(float(v[1])); ys.append(float(v[2]))
                elif g[0] in ("polyline",):
                    pts = find(g, "pts")
                    for xy in findall(pts, "xy"):
                        xs.append(float(xy[1])); ys.append(float(xy[2]))
                elif g[0] == "circle":
                    c = find(g, "center"); r = float(find(g, "radius")[1])
                    xs += [float(c[1]) - r, float(c[1]) + r]; ys += [float(c[2]) - r, float(c[2]) + r]
        if not xs:
            xs, ys = [0.0], [0.0]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))   # library coords (y up)

    def pins_by(self, key):
        """map pin number or pin name -> list of pin numbers"""
        if key in [p["number"] for p in self.pins]:
            return [key]
        nums = [p["number"] for p in self.pins if p["name"] == key]
        if not nums:
            raise KeyError("%s has no pin %r" % (self.lib_id, key))
        return nums


_SYMCACHE = {}


def syminfo(lib_id):
    if lib_id not in _SYMCACHE:
        _SYMCACHE[lib_id] = SymInfo(lib_id)
    return _SYMCACHE[lib_id]


# ------------------------------------------------------------------------------------------
# design model
# ------------------------------------------------------------------------------------------
class Part:
    def __init__(self, ref, lib_id, value, footprint, nets, sheet, fields=None, dnp=False):
        self.ref, self.lib_id, self.value, self.footprint = ref, lib_id, value, footprint
        self.nets = nets          # pin number -> net name or None (no connect)
        self.sheet, self.fields, self.dnp = sheet, dict(fields or {}), dnp


class Design:
    def __init__(self, name, title, company="Salt-Battery-Lab (pre-prototype)", rev="A", date="2026-11-02"):
        self.name, self.title, self.company, self.rev, self.date = name, title, company, rev, date
        self.parts, self.sheets, self._count, self._used = [], [], {}, set()
        self.notes = {}           # sheet -> list of text notes
        self.comments = ["CONCEPT \u2013 NOT FOR PRODUCTION", "", "", ""]

    def sheet(self, key, title):
        self.sheets.append((key, title)); self.notes.setdefault(key, [])
        return key

    def next_ref(self, prefix):
        while True:
            self._count[prefix] = self._count.get(prefix, 0) + 1
            ref = "%s%d" % (prefix, self._count[prefix])
            if ref not in self._used:
                return ref

    def add(self, sheet, lib_id, value, pins, footprint=None, ref=None, prefix=None, **fields):
        si = syminfo(lib_id)
        if footprint is None:
            footprint = si.props.get("Footprint", "")
        if ref is None:
            prefix = prefix or str(si.props.get("Reference", "U")).rstrip("?")
            ref = self.next_ref(prefix)
        nets = {}
        for k, v in pins.items():
            for num in si.pins_by(str(k)):
                nets[num] = v
        allnums = sorted(set(p["number"] for p in si.pins))
        missing = [n for n in allnums if n not in nets]
        # pins sharing a location with an assigned pin inherit its net (stacked hidden pins)
        loc = {}
        for p in si.pins:
            loc.setdefault((p["x"], p["y"]), []).append(p["number"])
        for n in list(missing):
            for p in si.pins:
                if p["number"] == n:
                    for other in loc[(p["x"], p["y"])]:
                        if other in nets:
                            nets[n] = nets[other]; missing.remove(n); break
                    break
        for n in missing:
            ptype = [p["type"] for p in si.pins if p["number"] == n][0]
            if ptype in ("no_connect",):
                continue
            raise ValueError("%s (%s): pin %s (%s) unassigned" % (ref, lib_id, n,
                             [p["name"] for p in si.pins if p["number"] == n][0]))
        if ref in self._used:
            raise ValueError("duplicate reference " + ref)
        self._used.add(ref)
        dnp = fields.pop("dnp", False)
        part = Part(ref, lib_id, value, footprint, nets, sheet, fields, dnp)
        self.parts.append(part)
        return part

    def nets(self):
        out = {}
        for p in self.parts:
            for num, n in p.nets.items():
                if n is not None:
                    out.setdefault(n, []).append((p.ref, num))
        return out


# ------------------------------------------------------------------------------------------
# schematic writer
# ------------------------------------------------------------------------------------------
PAPERS = [("A4", 297.0, 210.0), ("A3", 420.0, 297.0), ("A2", 594.0, 420.0), ("A1", 841.0, 594.0)]
G = 1.27


def snap(v):
    return round(v / G) * G


def _font(size=1.27):
    return ["effects", ["font", ["size", size, size]]]


def _label_len(name):
    return 1.0 + 0.95 * len(name) * 1.27 * 0.75 + 2.0


class SheetWriter:
    def __init__(self, design, key, title, page, root_uuid, sheet_uuid, file_uuid):
        self.d, self.key, self.title, self.page = design, key, title, page
        self.root_uuid, self.sheet_uuid, self.file_uuid = root_uuid, sheet_uuid, file_uuid
        self.items, self.libs = [], {}

    def place_parts(self, parts):
        # compute block sizes (symbol bbox + label allowance) and shelf-pack them
        blocks = []
        for p in parts:
            si = syminfo(p.lib_id)
            x0, y0, x1, y1 = si.bbox
            left = right = up = down = 2.54
            for pin in si.pins:
                net = p.nets.get(pin["number"])
                L = _label_len(net) if net else 2.0
                a = pin["a"]
                if a == 0: left = max(left, L + (x0 - pin["x"] if pin["x"] < x0 else 0))
                elif a == 180: right = max(right, L)
                elif a == 90: down = max(down, L)
                elif a == 270: up = max(up, L)
            w = (x1 - x0) + left + right + 6
            h = (y1 - y0) + up + down + 8
            blocks.append((p, w, h, left, up, x0, y1))
        for name, W, H in PAPERS:
            usable_w, usable_h = W - 30, H - 60
            pos, x, y, rowh, ok = [], 15.0, 20.0, 0.0, True
            for b in blocks:
                p, w, h = b[0], b[1], b[2]
                if x + w > 15 + usable_w:
                    x, y, rowh = 15.0, y + rowh, 0.0
                if w > usable_w:
                    ok = False; break
                pos.append((b, x, y)); x += w; rowh = max(rowh, h)
            if ok and y + rowh <= 20 + usable_h:
                break
        self.paper = name
        for (p, w, h, left, up, x0, y1), bx, by in pos:
            ox = snap(bx + left - x0)
            oy = snap(by + up + y1 + 3)
            self.symbol(p, ox, oy)

    def symbol(self, p, ox, oy):
        si = syminfo(p.lib_id)
        self.libs[p.lib_id] = si.node
        x0, y0, x1, y1 = si.bbox
        su = uid(self.d.name, "sym", p.ref)
        props = []
        def prop(k, v, x, y, hide=False, justify=None):
            e = ["effects", ["font", ["size", 1.27, 1.27]]]
            if justify: e.append(["justify", justify])
            if hide: e.append(["hide", "yes"])
            props.append(["property", Q(k), Q(v), ["at", round(x, 2), round(y, 2), 0], e])
        prop("Reference", p.ref, ox + x0, oy - y1 - 1.6, justify="left")
        prop("Value", p.value, ox + x0, oy - y0 + 2.6, justify="left")
        prop("Footprint", p.footprint, ox, oy, hide=True)
        prop("Datasheet", str(si.props.get("Datasheet", "")), ox, oy, hide=True)
        prop("Description", str(si.props.get("Description", "")), ox, oy, hide=True)
        for k, v in p.fields.items():
            prop(k, str(v), ox, oy, hide=True)
        node = ["symbol", ["lib_id", Q(p.lib_id)], ["at", round(ox, 2), round(oy, 2), 0], ["unit", 1],
                ["exclude_from_sim", "no"], ["in_bom", "no" if p.ref.startswith("#") else "yes"],
                ["on_board", "no" if p.ref.startswith("#") else "yes"], ["dnp", "yes" if p.dnp else "no"],
                ["uuid", Q(su)]] + props
        for pin in sorted(set(pp["number"] for pp in si.pins)):
            node.append(["pin", Q(pin), ["uuid", Q(uid(su, "pin", pin))]])
        node.append(["instances", ["project", Q(self.d.name),
                     ["path", Q(self.inst_path()), ["reference", Q(p.ref)], ["unit", 1]]]])
        self.items.append(node)
        # labels / no-connects at pin ends (one per distinct location)
        done = set()
        for pin in si.pins:
            px, py = round(ox + pin["x"], 3), round(oy - pin["y"], 3)
            if (px, py) in done:
                continue
            done.add((px, py))
            net = p.nets.get(pin["number"])
            if net is None:
                if pin["type"] != "no_connect":
                    self.items.append(["no_connect", ["at", px, py], ["uuid", Q(uid(su, "nc", pin["number"]))]])
                continue
            ang = (pin["a"] + 180) % 360
            just = "left" if ang in (0, 90) else "right"
            self.items.append(["global_label", Q(net), ["shape", "passive"], ["at", px, py, ang],
                               ["fields_autoplaced", "yes"],
                               ["effects", ["font", ["size", 1.27, 1.27]], ["justify", just]],
                               ["uuid", Q(uid(su, "lbl", pin["number"]))],
                               ["property", Q("Intersheetrefs"), Q("${INTERSHEET_REFS}"), ["at", px, py, 0],
                                ["effects", ["font", ["size", 1.27, 1.27]], ["hide", "yes"]]]])

    def inst_path(self):
        return "/" + self.root_uuid + ("/" + self.sheet_uuid if self.sheet_uuid else "")

    def text(self, s, x, y, size=1.8):
        self.items.append(["text", Q(s), ["exclude_from_sim", "no"], ["at", x, y, 0],
                           ["effects", ["font", ["size", size, size]], ["justify", "left", "top"]],
                           ["uuid", Q(uid(self.d.name, self.key, "text", s[:40], x, y))]])

    def render(self, extra=None):
        d = self.d
        tb = ["title_block", ["title", Q(d.title + " \u2014 " + self.title)], ["date", Q(d.date)],
              ["rev", Q(d.rev)], ["company", Q(d.company)]]
        for i, c in enumerate(d.comments, 1):
            if c:
                tb.append(["comment", i, Q(c)])
        root = ["kicad_sch", ["version", 20231120], ["generator", Q("eeschema")], ["generator_version", Q("8.0")],
                ["uuid", Q(self.file_uuid)], ["paper", Q(self.paper)], tb,
                ["lib_symbols"] + [self.libs[k] for k in sorted(self.libs)]]
        root += self.items
        if extra:
            root += extra
        return dump(root) + "\n"


def write_schematic(design, outdir):
    """Writes <name>.kicad_sch (root, with sheet symbols + notes) and one sub-sheet per design sheet."""
    os.makedirs(outdir, exist_ok=True)
    root_uuid = uid(design.name, "root")
    sheet_nodes, files = [], []
    for i, (key, title) in enumerate(design.sheets):
        s_uuid = uid(design.name, "sheet", key)
        f_uuid = uid(design.name, "file", key)
        sw = SheetWriter(design, key, title, i + 2, root_uuid, s_uuid, f_uuid)
        sw.place_parts([p for p in design.parts if p.sheet == key])
        y = {"A4": 185, "A3": 262, "A2": 380, "A1": 550}[sw.paper]
        for n in design.notes.get(key, []):
            sw.text(n, 15, y); y += 4.0 * (n.count("\n") + 1) + 2
        fname = "%s_%s.kicad_sch" % (design.name, key)
        with open(os.path.join(outdir, fname), "w", encoding="utf-8") as f:
            f.write(sw.render())
        files.append(fname)
        col, row = i % 4, i // 4
        x, yy = 20 + col * 95, 40 + row * 32
        sheet_nodes.append(["sheet", ["at", x, yy], ["size", 80, 18], ["fields_autoplaced", "yes"],
                            ["stroke", ["width", 0.1524], ["type", "solid"]], ["fill", ["color", 0, 0, 0, 0.0]],
                            ["uuid", Q(s_uuid)],
                            ["property", Q("Sheetname"), Q(title), ["at", x, yy - 0.7, 0],
                             ["effects", ["font", ["size", 1.27, 1.27]], ["justify", "left", "bottom"]]],
                            ["property", Q("Sheetfile"), Q(fname), ["at", x, yy + 18.6, 0],
                             ["effects", ["font", ["size", 1.27, 1.27]], ["justify", "left", "top"]]],
                            ["instances", ["project", Q(design.name), ["path", Q("/" + root_uuid), ["page", Q(str(i + 2))]]]]])
    rw = SheetWriter(design, "root", "Overview", 1, root_uuid, None, root_uuid)
    rw.paper = "A3"
    y = 40 + ((len(design.sheets) + 3) // 4) * 32 + 8
    for n in design.notes.get("root", []):
        rw.text(n, 20, y, size=1.6); y += 3.4 * (n.count("\n") + 1) + 2
    extra = sheet_nodes + [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]]]
    with open(os.path.join(outdir, design.name + ".kicad_sch"), "w", encoding="utf-8") as f:
        f.write(rw.render(extra))
    return files


# ------------------------------------------------------------------------------------------
# project files
# ------------------------------------------------------------------------------------------
def write_lib_tables(design, outdir, extra_sym=None):
    libs = sorted(set(p.lib_id.split(":")[0] for p in design.parts))
    lines = ["(sym_lib_table", "  (version 7)"]
    for l in libs:
        uri = (extra_sym or {}).get(l) or "${KICAD10_SYMBOL_DIR}/" + l + ".kicad_sym"     # portable Mac <-> Linux
        lines.append('  (lib (name "%s")(type "KiCad")(uri "%s")(options "")(descr ""))' % (l, uri))
    lines.append(")")
    with open(os.path.join(outdir, "sym-lib-table"), "w") as f:
        f.write("\n".join(lines) + "\n")
    fps = sorted(set(p.footprint.split(":")[0] for p in design.parts if p.footprint))
    lines = ["(fp_lib_table", "  (version 7)"]
    for l in fps:
        lines.append('  (lib (name "%s")(type "KiCad")(uri "%s")(options "")(descr ""))' % (l, "${KICAD10_FOOTPRINT_DIR}/" + l + ".pretty"))
    lines.append(")")
    with open(os.path.join(outdir, "fp-lib-table"), "w") as f:
        f.write("\n".join(lines) + "\n")


def write_project(design, outdir, netclasses, patterns, rules_extra=None):
    """netclasses: name -> dict(track, clearance, via_d, via_drill); patterns: list of (netclass, pattern)"""
    def nc(name, d):
        return {"name": name, "bus_width": 12, "clearance": d["clearance"], "diff_pair_gap": 0.25,
                "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "microvia_diameter": 0.3,
                "microvia_drill": 0.1, "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": d.get("priority", 0),
                "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": d["track"], "via_diameter": d["via_d"],
                "via_drill": d["via_drill"], "wire_width": 6}
    classes = [nc("Default", netclasses["Default"])] + [nc(k, v) for k, v in netclasses.items() if k != "Default"]
    pro = {
        "board": {"design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.5,
                         "copper_text_size_v": 1.5, "copper_text_thickness": 0.3, "silk_line_width": 0.12,
                         "silk_text_size_h": 0.8, "silk_text_size_v": 0.8, "silk_text_thickness": 0.12},
            "rules": {"min_clearance": 0.2, "min_track_width": 0.2, "min_via_diameter": 0.5, "min_via_annular_width": 0.1,
                      "min_through_hole_diameter": 0.3, "min_hole_to_hole": 0.25, "min_hole_clearance": 0.25,
                      "min_copper_edge_clearance": 0.3, "min_silk_clearance": 0.0, "min_text_height": 0.8,
                      "min_text_thickness": 0.08, "solder_mask_to_copper_clearance": 0.0, "min_microvia_diameter": 0.2,
                      "min_microvia_drill": 0.1, "max_error": 0.005, "allow_blind_buried_vias": False, "allow_microvias": False},
            "track_widths": [0.0, 0.2, 0.3, 0.5, 0.8], "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}],
            "rule_severities": {}}},
        "meta": {"filename": design.name + ".kicad_pro", "version": 3},
        "net_settings": {"classes": classes, "meta": {"version": 4},
                         "netclass_assignments": None,
                         "netclass_patterns": [{"netclass": c, "pattern": p} for c, p in patterns]},
        "schematic": {"drawing": {"default_text_size": 50.0}, "legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [[uid(design.name, "root"), "Root"]] + [[uid(design.name, "sheet", k), t] for k, t in design.sheets],
        "text_variables": {"REV": design.rev, "DATE": design.date},
    }
    if rules_extra:
        pro["board"]["design_settings"]["rule_severities"].update(rules_extra)
    with open(os.path.join(outdir, design.name + ".kicad_pro"), "w") as f:
        json.dump(pro, f, indent=2)


def _retype_pins(node, pin_types):
    """Recursively set the electrical type of pins whose number is in pin_types (e.g. {'13': 'open_collector'})."""
    if not isinstance(node, list):
        return
    if node and node[0] == "pin":
        num = next((str(c[1]).strip('"') for c in node if isinstance(c, list) and c and c[0] == "number"), None)
        if num in pin_types:
            node[1] = pin_types[num]
        return
    for c in node:
        _retype_pins(c, pin_types)


def make_custom_lib(path, entries):
    """entries: list of (new_name, base_lib_id, overrides(dict prop->value)[, pin_types(dict number->type)]). Writes a .kicad_sym.
    pin_types corrects stock-symbol electrical types where the datasheet differs (e.g. open-drain outputs typed as 'output')."""
    syms = []
    for entry in entries:
        new, base, ov = entry[:3]
        node = flat_symbol(base)
        if len(entry) > 3:
            _retype_pins(node, entry[3])
        node[1] = Q(new)
        old = base.split(":")[1]
        for x in node[2:]:
            if isinstance(x, list) and x[0] == "symbol":
                x[1] = Q(re.sub("^" + re.escape(old) + "_", new + "_", x[1]))
            if isinstance(x, list) and x[0] == "property" and x[1] in ov:
                x[2] = Q(ov[x[1]])
        syms.append(node)
    root = ["kicad_symbol_lib", ["version", 20231120], ["generator", Q("kigen")], ["generator_version", Q("8.0")]] + syms
    with open(path, "w", encoding="utf-8") as f:
        f.write(dump(root) + "\n")


# ------------------------------------------------------------------------------------------
# netlist reader (kicad-cli 'kicadsexpr' export)
# ------------------------------------------------------------------------------------------
def read_netlist(path):
    with open(path, encoding="utf-8") as f:
        root = parse_sexpr(f.read())
    comps = {}
    for c in findall(find(root, "components"), "comp"):
        ref = str(find(c, "ref")[1])
        sp = find(c, "sheetpath")
        tst = str(find(sp, "tstamps")[1])
        ts = find(c, "tstamps") or find(c, "tstamp")
        fields = {}
        fl = find(c, "fields")
        if fl:
            for fld in findall(fl, "field"):
                fields[str(find(fld, "name")[1])] = str(fld[2]) if len(fld) > 2 else ""
        comps[ref] = dict(ref=ref, value=str(find(c, "value")[1]),
                          footprint=str(find(c, "footprint")[1]) if find(c, "footprint") else "",
                          path=tst + str(ts[1]), fields=fields)
    nets = {}
    for n in findall(find(root, "nets"), "net"):
        name = str(find(n, "name")[1])
        nets[name] = [(str(find(nd, "ref")[1]), str(find(nd, "pin")[1])) for nd in findall(n, "node")]
    return comps, nets
