"""Small grid-based A* PCB router (pure Python, no deps) -- Salt-Battery-Lab concept boards.

Why: the Freerouting binary could not be executed in this environment (blocked), so the boards are
routed with this deliberately simple router.  It routes on two signal layers (F.Cu/B.Cu) with
through vias, keeps exact copper-to-copper clearance (checked again by KiCad DRC), restricts every
net to its isolation-domain region, and drops "fan-out" vias into inner-layer planes for plane nets.

Geometry is in mm, board-relative (0,0 = top-left).  Layers: 0 = F.Cu, 1 = B.Cu.
"""
import heapq, math
from array import array

SQ2 = math.sqrt(2.0)
DIRS = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, SQ2), (1, -1, SQ2), (-1, 1, SQ2), (-1, -1, SQ2)]


def seg_dist(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    if L2 <= 1e-12:
        return math.hypot(px - x0, py - y0)
    t = ((px - x0) * dx + (py - y0) * dy) / L2
    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def seg_seg_dist(a, b):
    (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = a, b
    return min(seg_dist(ax0, ay0, bx0, by0, bx1, by1), seg_dist(ax1, ay1, bx0, by0, bx1, by1),
               seg_dist(bx0, by0, ax0, ay0, ax1, ay1), seg_dist(bx1, by1, ax0, ay0, ax1, ay1))


class Router:
    def __init__(self, W, H, g=0.25, clearance=0.2, margin=0.04, widths=(0.2, 0.4, 0.6, 0.8), via_d=0.6, via_drill=0.3,
                 edge_clear=0.35, via_cost=6.0, log=print):
        self.W, self.H, self.g = W, H, g
        self.nx, self.ny = int(round(W / g)) + 1, int(round(H / g)) + 1
        self.N = self.nx * self.ny
        self.c, self.m, self.widths = clearance, margin, list(widths)
        self.via_d, self.via_drill, self.edge = via_d, via_drill, edge_clear
        self.via_cost, self.log = via_cost, log
        self.netid, self.netname = {}, [None]
        self.pads = []          # dict(net, layers, rect, center, smd, ref)
        self.holes = []         # (x, y, r) npth
        self.tracks = []        # dict(net, layer, x0,y0,x1,y1, w)
        self.vias = []          # dict(net, x, y)
        self.dom_rects = {}     # domain -> list of rects allowed
        self.net_dom = {}
        self.plane = {}         # net -> list of rect lists (each = one plane polygon component)
        self.reset_grids()

    # ------------------------------------------------------------------ grids
    def reset_grids(self):
        N = self.N
        self.own = [[array("i", bytes(4 * N)) for _ in range(2)] for _ in self.widths]
        self.vown = [array("i", bytes(4 * N)) for _ in range(2)]
        self.nopadvia = bytearray(N)

    def nid(self, net):
        if net not in self.netid:
            self.netid[net] = len(self.netname); self.netname.append(net)
        return self.netid[net]

    def cell_range(self, x0, y0, x1, y1, halo):
        g = self.g
        ix0 = max(0, int(math.floor((x0 - halo) / g))); ix1 = min(self.nx - 1, int(math.ceil((x1 + halo) / g)))
        iy0 = max(0, int(math.floor((y0 - halo) / g))); iy1 = min(self.ny - 1, int(math.ceil((y1 + halo) / g)))
        return ix0, ix1, iy0, iy1

    def _mark(self, arr, net, dist_fn, bbox, halo):
        g, nx = self.g, self.nx
        ix0, ix1, iy0, iy1 = self.cell_range(bbox[0], bbox[1], bbox[2], bbox[3], halo)
        for iy in range(iy0, iy1 + 1):
            py = iy * g; base = iy * nx
            for ix in range(ix0, ix1 + 1):
                if dist_fn(ix * g, py) < halo:
                    i = base + ix; v = arr[i]
                    if v == 0:
                        arr[i] = net
                    elif v != net:
                        arr[i] = -1

    def mark_shape(self, net, layers, kind, geo):
        """kind: rect(x0,y0,x1,y1) | seg(x0,y0,x1,y1,hw) | circ(x,y,r); net=-1 -> hard obstacle for all"""
        if kind == "rect":
            x0, y0, x1, y1 = geo
            def dist(px, py):
                dx = x0 - px if px < x0 else (px - x1 if px > x1 else 0.0)
                dy = y0 - py if py < y0 else (py - y1 if py > y1 else 0.0)
                return math.sqrt(dx * dx + dy * dy)
            bbox = geo
        elif kind == "seg":
            x0, y0, x1, y1, hw = geo
            def dist(px, py):
                return seg_dist(px, py, x0, y0, x1, y1) - hw
            bbox = (min(x0, x1) - hw, min(y0, y1) - hw, max(x0, x1) + hw, max(y0, y1) + hw)
        else:
            cx, cy, r = geo
            def dist(px, py):
                return math.hypot(px - cx, py - cy) - r
            bbox = (cx - r, cy - r, cx + r, cy + r)
        for L in layers:
            for wi, w in enumerate(self.widths):
                self._mark(self.own[wi][L], net, dist, bbox, self.c + w / 2 + self.m)
            self._mark(self.vown[L], net, dist, bbox, self.c + self.via_d / 2 + self.m)

    # ------------------------------------------------------------------ inputs
    def add_pad(self, net, layers, rect, center, smd, ref=""):
        n = self.nid(net) if net else -1
        self.pads.append(dict(net=n, layers=layers, rect=rect, center=center, smd=smd, ref=ref))

    def add_hole(self, x, y, r):
        self.holes.append((x, y, r))

    def set_domain(self, dom, rects_allowed):
        self.dom_rects[dom] = rects_allowed

    def build(self):
        """(re)mark everything: pads, holes, existing tracks/vias, domain masks"""
        self.reset_grids()
        for p in self.pads:
            self.mark_shape(p["net"], p["layers"], "rect", p["rect"])
            if p["smd"]:
                x0, y0, x1, y1 = p["rect"]; h = self.via_d / 2 + 0.05
                ix0, ix1, iy0, iy1 = self.cell_range(x0, y0, x1, y1, h)
                for iy in range(iy0, iy1 + 1):
                    for ix in range(ix0, ix1 + 1):
                        self.nopadvia[iy * self.nx + ix] = 1
        for (x, y, r) in self.holes:
            self.mark_shape(-1, (0, 1), "circ", (x, y, r))
            ix0, ix1, iy0, iy1 = self.cell_range(x - r, y - r, x + r, y + r, self.via_d / 2 + 0.3)
            for iy in range(iy0, iy1 + 1):
                for ix in range(ix0, ix1 + 1):
                    if math.hypot(ix * self.g - x, iy * self.g - y) < r + self.via_d / 2 + 0.3:
                        self.nopadvia[iy * self.nx + ix] = 1
        for t in self.tracks:
            self.mark_shape(t["net"], (t["layer"],), "seg", (t["x0"], t["y0"], t["x1"], t["y1"], t["w"] / 2))
        for v in self.vias:
            self.mark_shape(v["net"], (0, 1), "circ", (v["x"], v["y"], self.via_d / 2))

    def mask_from_rects(self, rects, shrink):
        m = bytearray(self.N); g = self.g
        for (x0, y0, x1, y1) in rects:
            x0, y0, x1, y1 = x0 + shrink, y0 + shrink, x1 - shrink, y1 - shrink
            if x1 < x0 or y1 < y0:
                continue
            ix0, ix1 = int(math.ceil(x0 / g - 1e-9)), int(math.floor(x1 / g + 1e-9))
            iy0, iy1 = int(math.ceil(y0 / g - 1e-9)), int(math.floor(y1 / g + 1e-9))
            ix0, iy0 = max(ix0, 0), max(iy0, 0); ix1, iy1 = min(ix1, self.nx - 1), min(iy1, self.ny - 1)
            for iy in range(iy0, iy1 + 1):
                b = iy * self.nx
                m[b + ix0: b + ix1 + 1] = b"\x01" * (ix1 - ix0 + 1)
        return m

    def subtract_rects(self, m, rects, grow):
        g = self.g
        for (x0, y0, x1, y1) in rects:
            x0, y0, x1, y1 = x0 - grow, y0 - grow, x1 + grow, y1 + grow
            ix0, ix1 = max(0, int(math.floor(x0 / g))), min(self.nx - 1, int(math.ceil(x1 / g)))
            iy0, iy1 = max(0, int(math.floor(y0 / g))), min(self.ny - 1, int(math.ceil(y1 / g)))
            for iy in range(iy0, iy1 + 1):
                b = iy * self.nx
                m[b + ix0: b + ix1 + 1] = bytes(ix1 - ix0 + 1)
        return m

    def prepare_masks(self, lv_exclusions):
        """domain masks per track width (copper must stay inside the domain region & board edge)."""
        self.dmask, self.dvmask = {}, {}
        board = [(0.0, 0.0, self.W, self.H)]
        for dom in list(self.dom_rects) + ["LV"]:
            for wi, w in enumerate(self.widths):
                if dom == "LV":
                    m = self.mask_from_rects(board, self.edge + w / 2)
                    for rects, gap in lv_exclusions:
                        self.subtract_rects(m, rects, gap + w / 2)
                else:
                    m = self.mask_from_rects(self.dom_rects[dom], w / 2)
                    bm = self.mask_from_rects(board, self.edge + w / 2)
                    m = bytearray(a & b for a, b in zip(m, bm))
                self.dmask[(dom, wi)] = m
            if dom == "LV":
                m = self.mask_from_rects(board, self.edge + self.via_d / 2)
                for rects, gap in lv_exclusions:
                    self.subtract_rects(m, rects, gap + self.via_d / 2)
            else:
                m = self.mask_from_rects(self.dom_rects[dom], self.via_d / 2)
            self.dvmask[dom] = m

    # ------------------------------------------------------------------ search
    def pad_cells(self, p):
        """grid nodes safely inside the pad copper (away from rounded ends/corners)"""
        x0, y0, x1, y1 = p["rect"]; cx, cy = p["center"]
        hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
        r = min(hx, hy); ax, ay = hx - 0.67 * r, hy - 0.67 * r
        g, nx = self.g, self.nx
        cells = []
        for iy in range(int(math.ceil((cy - ay) / g - 1e-9)), int(math.floor((cy + ay) / g + 1e-9)) + 1):
            for ix in range(int(math.ceil((cx - ax) / g - 1e-9)), int(math.floor((cx + ax) / g + 1e-9)) + 1):
                if 0 <= ix < nx and 0 <= iy < self.ny:
                    cells.append(iy * nx + ix)
        if not cells:   # tiny / off-grid pad: nearest nodes that are still inside the pad rectangle
            cand = []
            for iy in range(int(math.floor(y0 / g)), int(math.ceil(y1 / g)) + 1):
                for ix in range(int(math.floor(x0 / g)), int(math.ceil(x1 / g)) + 1):
                    px, py = ix * g, iy * g
                    if x0 + 0.05 <= px <= x1 - 0.05 and y0 + 0.05 <= py <= y1 - 0.05:
                        cand.append((math.hypot(px - cx, py - cy), iy * nx + ix))
            cand.sort()
            cells = [c for _, c in cand[:2]]
        if not cells:
            cells = [int(round(cy / g)) * nx + int(round(cx / g))]
        return cells

    def astar(self, net, wi, dom, sources, goal_set, goal_pred, target, max_expand=250000, soft=None):
        own = self.own[wi]; dm = self.dmask[(dom, wi)]; vm = self.dvmask[dom]
        vown = self.vown; npv = self.nopadvia
        nx, N = self.nx, self.N
        tx, ty = target

        def ok(L, i):
            o = own[L][i]
            return (o == 0 or o == net) and dm[i]

        def via_ok(i):
            a, b = vown[0][i], vown[1][i]
            return (a == 0 or a == net) and (b == 0 or b == net) and vm[i] and not npv[i]

        def h(i):
            ix, iy = i % nx, i // nx
            dx, dy = abs(ix - tx), abs(iy - ty)
            return (dx + dy) + (SQ2 - 2) * min(dx, dy)

        openh, gsc, came = [], {}, {}
        cnt = 0
        for (L, i) in sources:
            if not (dm[i] and (own[L][i] in (0, net))):
                continue
            node = L * N + i
            gsc[node] = 0.0; came[node] = None
            heapq.heappush(openh, (h(i), cnt, node)); cnt += 1
        exp = 0
        while openh:
            f, _, node = heapq.heappop(openh)
            L, i = divmod(node, N)
            gc = gsc[node]
            if f - h(i) > gc + 1e-9:
                continue
            if (goal_set is not None and node in goal_set) or (goal_pred is not None and goal_pred(L, i)):
                path = []
                while node is not None:
                    path.append(node); node = came[node]
                return path[::-1]
            exp += 1
            if exp > max_expand:
                return None
            ix, iy = i % nx, i // nx
            for dx, dy, cst in DIRS:
                jx, jy = ix + dx, iy + dy
                if jx < 0 or jy < 0 or jx >= nx or jy >= self.ny:
                    continue
                j = jy * nx + jx
                if not ok(L, j):
                    continue
                if dx and dy and not (ok(L, iy * nx + jx) and ok(L, jy * nx + ix)):
                    continue
                nn = L * N + j; ng = gc + cst + (0.02 if L == 1 else 0.0)
                if ng < gsc.get(nn, 1e18):
                    gsc[nn] = ng; came[nn] = node
                    heapq.heappush(openh, (ng + h(j), cnt, nn)); cnt += 1
            if via_ok(i):
                L2 = 1 - L
                if ok(L2, i):
                    nn = L2 * N + i; ng = gc + self.via_cost
                    if ng < gsc.get(nn, 1e18):
                        gsc[nn] = ng; came[nn] = node
                        heapq.heappush(openh, (ng + h(i), cnt, nn)); cnt += 1
        return None

    # ------------------------------------------------------------------ path -> copper
    def commit(self, net, w, path, start_stub=None, end_stub=None):
        N, nx, g = self.N, self.nx, self.g
        pts = [(n // N, (n % N) % nx * g, (n % N) // nx * g) for n in path]
        new_t, new_v = [], []
        # vias where layer changes
        for a, b in zip(pts, pts[1:]):
            if a[0] != b[0]:
                new_v.append(dict(net=net, x=a[1], y=a[2]))
        # split per layer into runs, then merge collinear points
        runs, cur = [], [pts[0]]
        for p in pts[1:]:
            if p[0] != cur[-1][0]:
                runs.append(cur); cur = [p]
            else:
                cur.append(p)
        runs.append(cur)
        for run in runs:
            L = run[0][0]
            xy = [(p[1], p[2]) for p in run]
            if run is runs[0] and start_stub:
                xy = [start_stub] + xy
            if run is runs[-1] and end_stub:
                xy = xy + [end_stub]
            simp = [xy[0]]
            for k in range(1, len(xy) - 1):
                ax, ay = simp[-1]; bx, by = xy[k]; cx, cy = xy[k + 1]
                if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 1e-9:
                    simp.append(xy[k])
            if len(xy) > 1:
                simp.append(xy[-1])
            for (x0, y0), (x1, y1) in zip(simp, simp[1:]):
                if abs(x0 - x1) + abs(y0 - y1) > 1e-6:
                    new_t.append(dict(net=net, layer=L, x0=x0, y0=y0, x1=x1, y1=y1, w=w))
        for t in new_t:
            self.tracks.append(t)
            self.mark_shape(net, (t["layer"],), "seg", (t["x0"], t["y0"], t["x1"], t["y1"], w / 2))
        for v in new_v:
            self.vias.append(v)
            self.mark_shape(net, (0, 1), "circ", (v["x"], v["y"], self.via_d / 2))
        return new_t, new_v

    # ------------------------------------------------------------------ net routing
    def width_index(self, w):
        for i, ww in enumerate(self.widths):
            if ww >= w - 1e-9:
                return i
        return len(self.widths) - 1

    def route_all(self, net_width, net_domain, plane_masks, order_key=None, max_expand=250000):
        """net_width: name->mm; plane_masks: name -> list of (mask bytearray) components."""
        pads_by_net = {}
        for idx, p in enumerate(self.pads):
            if p["net"] > 0:
                pads_by_net.setdefault(p["net"], []).append(idx)
        self.failed, self.comp_of = [], {}
        nets = sorted(pads_by_net, key=lambda n: self._mst_len(pads_by_net[n]))
        if order_key:
            nets = sorted(nets, key=lambda n: order_key(self.netname[n], self._mst_len(pads_by_net[n])))
        for n in nets:
            name = self.netname[n]
            self.route_net(n, pads_by_net[n], net_width.get(name, 0.2), net_domain(name), plane_masks.get(name), max_expand)
        return self.failed

    def _mst_len(self, idxs):
        pts = [self.pads[i]["center"] for i in idxs]
        if len(pts) < 2:
            return 0.0
        inside, tot = {0}, 0.0
        best = {j: math.hypot(pts[0][0] - pts[j][0], pts[0][1] - pts[j][1]) for j in range(1, len(pts))}
        while best:
            j = min(best, key=best.get); tot += best.pop(j); inside.add(j)
            for k in best:
                best[k] = min(best[k], math.hypot(pts[j][0] - pts[k][0], pts[j][1] - pts[k][1]))
        return tot

    def route_net(self, n, idxs, w, dom, planes, max_expand):
        N, g, nx = self.N, self.g, self.nx
        wi = self.width_index(w)
        comps = [[i] for i in idxs]           # each comp: list of pad indices
        comp_cells = [set() for _ in comps]   # encoded nodes with copper of that comp
        for ci, c in enumerate(comps):
            p = self.pads[c[0]]
            for L in p["layers"]:
                for cell in self.pad_cells(p):
                    comp_cells[ci].add(L * N + cell)
        # plane fan-out: SMD pads drop a via into the plane polygon that contains them
        if planes:
            plane_comp = {}
            for ci, c in enumerate(comps):
                p = self.pads[c[0]]
                cx, cy = p["center"]; ic = int(round(cy / g)) * nx + int(round(cx / g))
                for pk, pm in enumerate(planes):
                    if not p["smd"] and pm[ic]:
                        plane_comp.setdefault(pk, []).append(ci); break
                    if p["smd"]:
                        def pred(L, i, pm=pm):
                            a, b = self.vown[0][i], self.vown[1][i]
                            return pm[i] and (a == 0 or a == n) and (b == 0 or b == n) and not self.nopadvia[i] \
                                and self.dvmask[dom][i]
                        srcs = [(L, cell) for L in p["layers"] for cell in self.pad_cells(p)]
                        path = self.astar(n, 0, dom, srcs, None, pred, (cx / g, cy / g), max_expand=4000)
                        if path is not None and len(path) <= 40:
                            t, v = self.commit(n, self.widths[0], path, start_stub=p["center"])
                            L_end, i_end = divmod(path[-1], N)
                            if L_end == 0 or True:
                                vx, vy = (i_end % nx) * g, (i_end // nx) * g
                                if not any(abs(vv["x"] - vx) < 1e-6 and abs(vv["y"] - vy) < 1e-6 for vv in self.vias):
                                    self.vias.append(dict(net=n, x=vx, y=vy))
                                    self.mark_shape(n, (0, 1), "circ", (vx, vy, self.via_d / 2))
                            for node in path:
                                comp_cells[ci].add(node)
                            comp_cells[ci].add((1 - path[-1] // N) * N + path[-1] % N)
                            plane_comp.setdefault(pk, []).append(ci)
                            break
            # merge comps per plane
            for pk, cis in plane_comp.items():
                base = cis[0]
                for ci in cis[1:]:
                    comps[base] += comps[ci]; comp_cells[base] |= comp_cells[ci]; comps[ci] = []; comp_cells[ci] = set()
            keep = [i for i, c in enumerate(comps) if c]
            comps = [comps[i] for i in keep]; comp_cells = [comp_cells[i] for i in keep]
        if len(comps) <= 1:
            return
        # Prim over components, starting with the biggest
        start = max(range(len(comps)), key=lambda i: len(comps[i]))
        tree_pads, tree_cells = list(comps[start]), set(comp_cells[start])
        todo = [i for i in range(len(comps)) if i != start]
        while todo:
            def cdist(ci):
                return min(math.hypot(self.pads[a]["center"][0] - self.pads[b]["center"][0],
                                      self.pads[a]["center"][1] - self.pads[b]["center"][1])
                           for a in comps[ci] for b in tree_pads)
            todo.sort(key=cdist)
            ci = todo.pop(0)
            # source: pad of comp nearest to tree; target heuristic: nearest tree pad
            best = min(((a, b) for a in comps[ci] for b in tree_pads),
                       key=lambda ab: math.hypot(self.pads[ab[0]]["center"][0] - self.pads[ab[1]]["center"][0],
                                                 self.pads[ab[0]]["center"][1] - self.pads[ab[1]]["center"][1]))
            sp, tp = self.pads[best[0]], self.pads[best[1]]
            srcs = [(nd // N, nd % N) for nd in comp_cells[ci]]
            ok = False
            for wtry in ([wi, 0] if wi else [0]):
                path = self.astar(n, wtry, dom, srcs, tree_cells, None, (tp["center"][0] / g, tp["center"][1] / g), max_expand)
                if path is None:
                    continue
                first = path[0]; last = path[-1]
                s_stub = self._stub_for(first, comps[ci]); e_stub = self._stub_for(last, tree_pads)
                self.commit(n, self.widths[wtry], path, start_stub=s_stub, end_stub=e_stub)
                for node in path:
                    tree_cells.add(node)
                tree_cells |= comp_cells[ci]; tree_pads += comps[ci]
                ok = True
                break
            if not ok:
                self.failed.append((self.netname[n], sp["ref"], tp["ref"]))
                tree_cells |= comp_cells[ci]; tree_pads += comps[ci]   # keep going (reported as unrouted)

    def _stub_for(self, node, pad_idxs):
        N, nx, g = self.N, self.nx, self.g
        L, i = divmod(node, N)
        px, py = (i % nx) * g, (i // nx) * g
        for pi in pad_idxs:
            p = self.pads[pi]
            x0, y0, x1, y1 = p["rect"]
            if L in p["layers"] and x0 - 1e-6 <= px <= x1 + 1e-6 and y0 - 1e-6 <= py <= y1 + 1e-6:
                if abs(px - p["center"][0]) + abs(py - p["center"][1]) > 1e-6:
                    return p["center"]
                return None
        return None
