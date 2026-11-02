"""Build a routed .kicad_pcb from a kicad-cli netlist + board design module.  Runs in KiCad's Python (pcbnew).

usage: <kicad python> pcbbuild.py <board_dir> <design_module> <netlist.net> <out.kicad_pcb>
"""
import importlib, json, math, os, sys, time
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kigen as K  # noqa: E402
from router import Router  # noqa: E402

FP_DIR = K.FP_DIR
OX, OY = 20.0, 20.0          # board origin on the KiCad page (mm)
mm = pcbnew.FromMM
tomm = pcbnew.ToMM


def V(x, y):
    return pcbnew.VECTOR2I(mm(x + OX), mm(y + OY))


def rect_poly(rects):
    ps = pcbnew.SHAPE_POLY_SET()
    for (x0, y0, x1, y1) in rects:
        ps.NewOutline()
        for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ps.Append(mm(x + OX), mm(y + OY))
    ps.Simplify() if hasattr(ps, "Simplify") else None
    return ps


def poly_sub(a, b):
    try:
        a.BooleanSubtract(b)
    except TypeError:
        a.BooleanSubtract(b, pcbnew.SHAPE_POLY_SET.PM_FAST)
    return a


def poly_and(a, b):
    try:
        a.BooleanIntersection(b)
    except TypeError:
        a.BooleanIntersection(b, pcbnew.SHAPE_POLY_SET.PM_FAST)
    return a


def grow(rects, d):
    return [(x0 - d, y0 - d, x1 + d, y1 + d) for (x0, y0, x1, y1) in rects]


class Builder:
    def __init__(self, board_dir, modname, netfile):
        sys.path.insert(0, board_dir)
        self.D = importlib.import_module(modname)
        self.comps, self.nets = K.read_netlist(netfile)
        self.pin_net = {}
        for n, nodes in self.nets.items():
            for ref, pin in nodes:
                self.pin_net[(ref, pin)] = n
        self.board = pcbnew.CreateEmptyBoard()
        self.board.SetCopperLayerCount(4)
        self.W, self.H = self.D.BOARD_W, self.D.BOARD_H
        self.fps = {}
        self.log = []

    # ------------------------------------------------------------------ setup
    def setup(self):
        b = self.board
        tb = b.GetTitleBlock()
        tb.SetTitle(getattr(self.D, "TITLE", self.D.NAME)); tb.SetRevision("A"); tb.SetDate("2026-11-02")
        tb.SetCompany("Salt-Battery-Lab (pre-prototype)"); tb.SetComment(0, "CONCEPT – NOT FOR PRODUCTION")
        ds = b.GetDesignSettings()
        ds.m_MinClearance = mm(0.2); ds.m_TrackMinWidth = mm(0.2); ds.m_ViasMinSize = mm(0.5)
        ds.m_MinThroughDrill = mm(0.3); ds.m_HoleToHoleMin = mm(0.25); ds.m_CopperEdgeClearance = mm(0.3)
        for (a, c) in (((0, 0), (self.W, 0)), ((self.W, 0), (self.W, self.H)), ((self.W, self.H), (0, self.H)), ((0, self.H), (0, 0))):
            s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
            s.SetStart(V(*a)); s.SetEnd(V(*c)); s.SetWidth(mm(0.1)); b.Add(s)
        self.netinfo = {}
        for n in sorted(self.nets):
            ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); self.netinfo[n] = ni

    def load_footprints(self):
        for ref in sorted(self.comps):
            c = self.comps[ref]
            if not c["footprint"]:
                continue
            lib, name = c["footprint"].split(":")
            fp = pcbnew.FootprintLoad(os.path.join(FP_DIR, lib + ".pretty"), name)
            fp.SetFPID(pcbnew.LIB_ID(lib, name))
            fp.SetReference(ref); fp.SetValue(c["value"])
            fp.SetPath(pcbnew.KIID_PATH(c["path"]))
            for fld in ("MPN", "Manufacturer"):
                if fld in c["fields"] and hasattr(fp, "SetField"):
                    try:
                        fp.SetField(fld, c["fields"][fld])
                    except Exception:
                        pass
            for t in (fp.Reference(), fp.Value()):
                t.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); t.SetTextThickness(mm(0.12))
            fp.Value().SetVisible(False)
            self.board.Add(fp)
            for pad in fp.Pads():
                n = self.pin_net.get((ref, pad.GetNumber()))
                if n:
                    pad.SetNet(self.netinfo[n])
            self.fps[ref] = fp

    def place(self, ref, x, y, rot, side="F"):
        fp = self.fps[ref]
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)
        if side == "B" and not fp.IsFlipped():
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT if hasattr(pcbnew, "FLIP_DIRECTION_LEFT_RIGHT") else False)

    def courtyard(self, fp, pad=0.15):
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False, False)
        return (tomm(bb.GetLeft()) - OX - pad, tomm(bb.GetTop()) - OY - pad, tomm(bb.GetRight()) - OX + pad, tomm(bb.GetBottom()) - OY + pad)

    # ------------------------------------------------------------------ placement
    def placement(self):
        fixed = self.D.fixed_placement()
        for ref, (x, y, rot, side) in fixed.items():
            if ref in self.fps:
                self.place(ref, x, y, rot, side)
        self.placed = set(r for r in fixed if r in self.fps)
        self.occ = [self.courtyard(self.fps[r]) for r in self.placed] + list(getattr(self.D, "RESERVED", []))
        self.router_for_masks()
        plane_nets = set(self.D.PLANES)
        order = [r for r in self.comps_in_design_order() if r in self.fps and r not in self.placed]
        last_ic = None
        anchors = {}
        for r in self.comps_in_design_order():
            if r[0] == "U" or r[0] == "J" or r.startswith("SW"):
                last_ic = r
            anchors[r] = last_ic
        for ref in order:
            self.auto_place(ref, plane_nets, anchors.get(ref))
        self.log.append("placed %d fixed + %d auto" % (len(fixed), len(order)))

    def comps_in_design_order(self):
        d = self.D.build() if not hasattr(self, "_design") else self._design
        self._design = d
        return [p.ref for p in d.parts if not p.ref.startswith("#")]

    def router_for_masks(self):
        r = Router(self.W, self.H, g=0.25)
        regs = self.D.regions()
        for dom, rects in regs.items():
            r.set_domain(dom, rects)
        r.prepare_masks(self.lv_exclusions())
        self.mask_router = r

    def lv_exclusions(self):
        regs, gap = self.D.regions(), self.D.DOMAIN_GAP
        out = []
        for dom, rects in regs.items():
            kind = self.D.domain_kind(dom)
            out.append((rects, gap[(kind, "LV")] if (kind, "LV") in gap else gap[("LV", kind)]))
        return out

    def pads_ok(self, fp):
        r = self.mask_router
        for pad in fp.Pads():
            n = pad.GetNetname()
            dom = self.D.net_domain(n) if n and not n.startswith("unconnected") else None
            bb = pad.GetBoundingBox()
            x0, y0, x1, y1 = tomm(bb.GetLeft()) - OX, tomm(bb.GetTop()) - OY, tomm(bb.GetRight()) - OX, tomm(bb.GetBottom()) - OY
            # an unconnected pad belongs to no domain: accept it inside any domain's mask
            masks = [v for k, v in r.dmask.items() if k[1] == 0] if dom is None else [r.dmask[(dom, 0)]]
            for (px, py) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1), ((x0 + x1) / 2, (y0 + y1) / 2)):
                ix, iy = int(round(px / r.g)), int(round(py / r.g))
                if not (0 <= ix < r.nx and 0 <= iy < r.ny) or not any(m[iy * r.nx + ix] for m in masks):
                    return False
        return True

    def overlaps(self, box):
        x0, y0, x1, y1 = box
        if x0 < 0.2 or y0 < 0.2 or x1 > self.W - 0.2 or y1 > self.H - 0.2:
            return True
        for (a0, b0, a1, b1) in self.occ:
            if x0 < a1 and x1 > a0 and y0 < b1 and y1 > b0:
                return True
        return False

    def net_target(self, net, exclude_ref):
        pts = []
        for ref, pin in self.nets.get(net, []):
            if ref != exclude_ref and ref in self.placed:
                for pad in self.fps[ref].Pads():
                    if pad.GetNumber() == pin:
                        p = pad.GetPosition(); pts.append((tomm(p.x) - OX, tomm(p.y) - OY))
        return pts

    def auto_place(self, ref, plane_nets, anchor):
        fp = self.fps[ref]
        sig = {}
        for pad in fp.Pads():
            n = pad.GetNetname()
            if n and n not in plane_nets and not n.startswith("unconnected") and len(self.nets.get(n, [])) <= 24:
                pts = self.net_target(n, ref)
                if pts:
                    sig.setdefault(pad.GetNumber(), []).extend(pts)
        allpts = [p for v in sig.values() for p in v]
        if allpts:
            tx = sum(p[0] for p in allpts) / len(allpts); ty = sum(p[1] for p in allpts) / len(allpts)
        elif anchor and anchor in self.placed:
            # decoupling-type part: near the anchor IC's pins on the same plane nets
            pts = []
            for pad in fp.Pads():
                n = pad.GetNetname()
                for apad in self.fps[anchor].Pads():
                    if apad.GetNetname() == n and n not in ("GND",):
                        p = apad.GetPosition(); pts.append((tomm(p.x) - OX, tomm(p.y) - OY))
            if not pts:
                p = self.fps[anchor].GetPosition(); pts = [(tomm(p.x) - OX, tomm(p.y) - OY)]
            tx = sum(p[0] for p in pts) / len(pts); ty = sum(p[1] for p in pts) / len(pts)
        else:
            tx, ty = self.W * 0.6, self.H / 2
        best = None
        for rot in (0, 90, 180, 270):
            self.place(ref, tx, ty, rot)
            cost = 0.0
            for pad in fp.Pads():
                pts = sig.get(pad.GetNumber())
                if pts:
                    p = pad.GetPosition(); px, py = tomm(p.x) - OX, tomm(p.y) - OY
                    cost += min(math.hypot(px - a, py - b) for a, b in pts)
            if best is None or cost < best[0] - 1e-6:
                best = (cost, rot)
        rot = best[1]
        step = 0.5
        for rad in range(0, 80):
            cands = []
            for i in range(-rad, rad + 1):
                for j in (-rad, rad) if abs(i) != rad else range(-rad, rad + 1):
                    cands.append((math.hypot(i, j), i, j))
            cands.sort()
            for _, i, j in cands:
                x, y = round((tx + i * step) / 0.25) * 0.25, round((ty + j * step) / 0.25) * 0.25
                self.place(ref, x, y, rot)
                box = self.courtyard(fp)
                if self.overlaps(box):
                    continue
                if not self.pads_ok(fp):
                    continue
                self.placed.add(ref); self.occ.append(box)
                return
        raise RuntimeError("could not place " + ref)

    # ------------------------------------------------------------------ routing
    def route(self):
        D = self.D
        r = Router(self.W, self.H, g=0.25)
        regs = D.regions()
        for dom, rects in regs.items():
            r.set_domain(dom, rects)
        r.prepare_masks(self.lv_exclusions())
        for ref, fp in self.fps.items():
            for pad in fp.Pads():
                attr = pad.GetAttribute()
                p = pad.GetPosition(); cx, cy = tomm(p.x) - OX, tomm(p.y) - OY
                if attr == pcbnew.PAD_ATTRIB_NPTH:
                    r.add_hole(cx, cy, tomm(pad.GetDrillSize().x) / 2 + 0.25)
                    continue
                layers = tuple(L for L, lid in ((0, pcbnew.F_Cu), (1, pcbnew.B_Cu)) if pad.IsOnLayer(lid))
                if not layers:
                    continue
                bb = pad.GetBoundingBox()
                rect = (tomm(bb.GetLeft()) - OX, tomm(bb.GetTop()) - OY, tomm(bb.GetRight()) - OX, tomm(bb.GetBottom()) - OY)
                n = pad.GetNetname()
                if not n or n.startswith("unconnected"):
                    n = "__nc_%s_%s" % (ref, pad.GetNumber())
                r.add_pad(n, layers, rect, (cx, cy), attr == pcbnew.PAD_ATTRIB_SMD, ref + "." + pad.GetNumber())
        r.build()
        # plane masks (where a fan-out via may land)
        plane_masks = {}
        lvpoly_rects = None
        for net, (layer, spec) in D.PLANES.items():
            if spec == "LV":
                m = r.dmask[("LV", 0)]
                m2 = bytearray(m)
                r.subtract_rects(m2, [], 0)
                comps = [self._shrink_mask(r, m2, 0.6)]
            elif isinstance(spec, str):
                comps = [r.mask_from_rects(regs[spec], 0.8)]
            else:
                comps = []
                for rect in spec:
                    mk = r.mask_from_rects([rect], 0.8)
                    lv = r.dmask[("LV", 0)]
                    comps.append(bytearray(a & b for a, b in zip(mk, self._shrink_mask(r, lv, 0.6))))
            plane_masks[net] = comps
        widths = dict(D.POWER_NETS)
        t0 = time.time()

        def order_key(name, L):
            pri = 0 if name in D.PLANES else (1 if name in widths else 2)
            return (pri, L)
        failed = r.route_all(widths, D.net_domain, plane_masks, order_key=order_key)
        self.log.append("routing %.1fs: %d tracks, %d vias, %d failed" % (time.time() - t0, len(r.tracks), len(r.vias), len(failed)))
        for f in failed[:60]:
            self.log.append("  UNROUTED %s %s -> %s" % f)
        self.failed = failed
        b = self.board
        for t in r.tracks:
            name = r.netname[t["net"]]
            if name.startswith("__nc"):
                continue
            tr = pcbnew.PCB_TRACK(b)
            tr.SetStart(V(t["x0"], t["y0"])); tr.SetEnd(V(t["x1"], t["y1"])); tr.SetWidth(mm(t["w"]))
            tr.SetLayer(pcbnew.F_Cu if t["layer"] == 0 else pcbnew.B_Cu); tr.SetNet(self.netinfo[name]); b.Add(tr)
        seen = set()
        for v in r.vias:
            key = (round(v["x"], 3), round(v["y"], 3))
            if key in seen:
                continue
            seen.add(key)
            via = pcbnew.PCB_VIA(b)
            via.SetPosition(V(v["x"], v["y"])); via.SetWidth(mm(r.via_d)); via.SetDrill(mm(r.via_drill))
            via.SetNet(self.netinfo[r.netname[v["net"]]]); b.Add(via)
        self.router = r

    def _shrink_mask(self, r, m, d):
        """erode a mask by d mm (square structuring element)"""
        k = int(math.ceil(d / r.g)); nx, ny = r.nx, r.ny
        out = bytearray(m)
        rows = [m[iy * nx:(iy + 1) * nx] for iy in range(ny)]
        # horizontal erosion
        h = []
        for row in rows:
            rr = bytearray(nx)
            run = 0
            pre = [0] * (nx + 1)
            for i in range(nx):
                pre[i + 1] = pre[i] + row[i]
            for i in range(nx):
                a, b2 = max(0, i - k), min(nx, i + k + 1)
                rr[i] = 1 if (pre[b2] - pre[a]) == (b2 - a) and (i - k >= 0 and i + k < nx) else 0
            h.append(rr)
        for ix in range(nx):
            col = [h[iy][ix] for iy in range(ny)]
            pre = [0] * (ny + 1)
            for i in range(ny):
                pre[i + 1] = pre[i] + col[i]
            for iy in range(ny):
                a, b2 = max(0, iy - k), min(ny, iy + k + 1)
                out[iy * nx + ix] = 1 if (pre[b2] - pre[a]) == (b2 - a) and (iy - k >= 0 and iy + k < ny) else 0
        return out

    # ------------------------------------------------------------------ zones + text
    def zones(self):
        D, b = self.D, self.board
        regs, gap = D.regions(), D.DOMAIN_GAP
        board_in = [(0.5, 0.5, self.W - 0.5, self.H - 0.5)]

        def lv_poly():
            ps = rect_poly(board_in)
            for rects, g in self.lv_exclusions():
                poly_sub(ps, rect_poly(grow(rects, g)))
            return ps
        for net, (layer, spec) in D.PLANES.items():
            if spec == "LV":
                ps = lv_poly()
            elif isinstance(spec, str):
                ps = rect_poly(grow(regs[spec], -0.3))
            else:
                ps = poly_and(rect_poly(spec), lv_poly())
            lid = {"In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu, "F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}[layer]
            for k in range(ps.OutlineCount()):
                z = pcbnew.ZONE(b)
                z.SetLayer(lid)
                z.SetNet(self.netinfo[net])
                zo = z.Outline()
                zo.NewOutline()
                ch = ps.Outline(k)
                for i in range(ch.PointCount()):
                    pt = ch.CPoint(i); zo.Append(pt.x, pt.y)
                for h in range(ps.HoleCount(k)):
                    hc = ps.Hole(k, h); zo.NewHole()
                    for i in range(hc.PointCount()):
                        pt = hc.CPoint(i); zo.Append(pt.x, pt.y, 0, 0)
                z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
                z.SetMinThickness(mm(0.25))
                try:
                    z.SetLocalClearance(mm(0.3))
                except Exception:
                    z.SetLocalClearance(pcbnew.OptionalInt(mm(0.3)) if hasattr(pcbnew, "OptionalInt") else mm(0.3))
                z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
                z.SetZoneName("%s_%s_%d" % (net, layer, k))
                b.Add(z)
        # NOTE: pcbnew.ZONE_FILLER segfaults without a wxApp in KiCad 10 standalone Python;
        # zones are filled by `kicad-cli pcb drc --refill-zones --save-board` in build_pcb.sh instead.

    def text(self, s, x, y, size, layer=pcbnew.F_SilkS, mirror=False, bold=True):
        t = pcbnew.PCB_TEXT(self.board)
        t.SetText(s); t.SetPosition(V(x, y)); t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(size * 0.15))
        if mirror:
            t.SetMirrored(True)
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        self.board.Add(t)

    def save(self, out):
        pcbnew.SaveBoard(out, self.board)


def main():
    board_dir, modname, netfile, out = sys.argv[1:5]
    pro = os.path.join(board_dir, os.path.splitext(os.path.basename(out))[0] + ".kicad_pro")
    pro_txt = open(pro).read() if os.path.exists(pro) else None
    B = Builder(os.path.abspath(board_dir), modname, netfile)
    def st(m):
        print("[pcbbuild] " + m, flush=True)
    st("setup"); B.setup(); st("footprints"); B.load_footprints(); st("placement"); B.placement()
    if os.environ.get("SCM_ROUTER") == "freerouting":      # routed afterwards by tools/freeroute.py (Freerouting, headless)
        st("route skipped (freerouting)"); B.failed = []; B.router = type("R", (), {"tracks": [], "vias": []})()
    else:
        st("route"); B.route()
    st("texts")
    lmap = {"F.SilkS": pcbnew.F_SilkS, "B.SilkS": pcbnew.B_SilkS}
    for (s, x, y, size, layer, mirror) in B.D.silk_texts():
        B.text(s, x, y, size, layer=lmap[layer], mirror=mirror)
    st("zones"); B.zones()
    st("save"); B.save(out)
    if pro_txt is not None:
        with open(pro, "w") as f:
            f.write(pro_txt)
    rep = dict(log=B.log, failed=B.failed, tracks=len(B.router.tracks), vias=len(B.router.vias), footprints=len(B.fps))
    with open(os.path.join(board_dir, "route_report.json"), "w") as f:
        json.dump(rep, f, indent=1)
    print("\n".join(B.log))


if __name__ == "__main__":
    main()
