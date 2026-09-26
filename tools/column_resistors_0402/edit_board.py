"""v0.4r2 board edits for panel_rp2354_20x20_ir-red_v0p4 (run with KiCad 10's bundled python).
usage: edit_board.py in.kicad_pcb out.kicad_pcb"""
import sys, math, pcbnew
IN, OUT = sys.argv[1], sys.argv[2]
LIB = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty'
NEWFP = 'R_0402_1005Metric'
LCSC_LED = {'LED_T2': 'C6879329', 'LED_T3': 'C2852592'}      # T2 -> IR, T3 -> red (checkerboard)
CLR, HOLE2HOLE, EDGE = 0.135, 0.26, 0.21                    # design targets (JLCPCB: 0.127 / 0.25 / 0.20)

TEMPLATES = [pcbnew.FootprintLoad(LIB, NEWFP) for _ in range(20)]; assert all(TEMPLATES)
board = pcbnew.LoadBoard(IN)
REMOVED = []      # BOARD.Remove hands ownership to Python; deleting the C++ objects corrupts the heap, so keep them
log = []
def V(x, y): return pcbnew.VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))
def F(v): return f"({v.x/1e6:.3f},{v.y/1e6:.3f})"
def field(fp, name):
    for f in fp.GetFields():
        if f.GetName() == name: return f
def segs(): return [t for t in board.GetTracks() if t.GetClass() != 'PCB_VIA']
def vias(): return [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
def near(a, b, tol=1500): return (a - b).EuclideanNorm() < tol
CU = [l for l in board.GetEnabledLayers().CuStack()]
bb = board.GetBoardEdgesBoundingBox(); EDGE_L, EDGE_R, EDGE_T, EDGE_B = bb.GetLeft(), bb.GetRight(), bb.GetTop(), bb.GetBottom()

# ---------- 1. LED bank swap ----------
n = {}
for fp in board.GetFootprints():
    if fp.GetValue() in LCSC_LED:
        field(fp, 'LCSC Part #').SetText(LCSC_LED[fp.GetValue()]); n[fp.GetValue()] = n.get(fp.GetValue(), 0) + 1
log.append(f"LED LCSC swapped: {n}")

# ---------- 2. footprint swap R9-R28 ----------
for i in range(9, 29):
    ref = f'R{i}'; old = board.FindFootprintByReference(ref); new = TEMPLATES[i - 9]
    board.Add(new); new.thisown = False
    new.SetPosition(old.GetPosition())
    if old.IsFlipped(): new.Flip(old.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    new.SetOrientation(old.GetOrientation())
    new.SetReference(ref); new.SetValue(old.GetValue()); new.SetFPID(pcbnew.LIB_ID('Resistor_SMD', NEWFP))
    new.SetPath(old.GetPath()); new.SetSheetname(old.GetSheetname()); new.SetSheetfile(old.GetSheetfile()); new.SetAttributes(old.GetAttributes())
    for f in old.GetFields():
        nf = field(new, f.GetName())
        if nf is not None and f.GetName() not in ('Reference', 'Value', 'Footprint'):
            nf.SetText(f.GetText()); nf.SetVisible(f.IsVisible()); nf.SetLayer(f.GetLayer())
    field(new, 'Reference').SetVisible(False); field(new, 'Value').SetVisible(False)
    oldpads = {p.GetNumber(): p for p in old.Pads() if p.GetNumber()}
    for p in new.Pads():
        if p.GetNumber():
            p.SetNet(oldpads[p.GetNumber()].GetNet())
            d = p.GetPosition() - new.GetPosition(); e = oldpads[p.GetNumber()].GetPosition() - old.GetPosition()
            assert d.x * e.x + d.y * e.y > 0, (ref, p.GetNumber())
    board.Remove(old); old.thisown = False; REMOVED.append(old)
    log.append(f"{ref}: -> {NEWFP} at {F(new.GetPosition())} rot {new.GetOrientationDegrees():.0f} {new.GetLayerName()}")

# ---------- 3. resistor nudges (centre moves) ----------
def move_fp(ref, x, y):
    fp = board.FindFootprintByReference(ref); o = fp.GetPosition(); fp.SetPosition(V(x, y)); log.append(f"  {ref} centre {F(o)} -> ({x:.3f},{y:.3f})")
move_fp('R21', 50.700, 71.25)     # +0.05 north: clears C28.1 (was 0.115) with via D1-A moved north
move_fp('R12', 55.125, 83.16)     # +0.18 north: COL_MCU_02 corridor between pad 1 and U4 pads is only 0.275 wide
move_fp('R15', 50.830, 79.155)    # +0.17 east: board edge at x=50.0 leaves no room west of pad 1 for the D121-A track
move_fp('R22', 50.850, 66.465)    # +0.17 east: same, D261-A track
move_fp('R10', 55.140, 87.560)    # +0.03 south: D1-A then fits between via D61-A and pad 2 (0.137 each side); J3.2 below limits further shift
move_fp('R14', 55.320, 79.145)    # +0.20 east: via COL_MCU_04 cannot move; D101-A now passes between it and pad 1
move_fp('R17', 55.270, 74.965)    # +0.15 east: clears vias D41-A / COL_MCU_09 without moving them
move_fp('R25', 59.440, 66.455)    # -0.15 west: clears via D100-A (no legal spot east of pad 2, U19 pads)
move_fp('R24', 65.080, 62.570)    # -0.15 north: clears COL_MCU_17 diagonal (C74 blocks re-routing it)

# ---------- 4. track edits ----------
def move_vertex(ox, oy, nx, ny):
    o, nv = V(ox, oy), V(nx, ny); cnt = 0
    for s in segs():
        if near(s.GetStart(), o): s.SetStart(nv); cnt += 1
        if near(s.GetEnd(), o): s.SetEnd(nv); cnt += 1
    for v in vias():
        if near(v.GetPosition(), o): v.SetPosition(nv); cnt += 1
    assert cnt, f"no item at ({ox},{oy})"; log.append(f"  vertex ({ox:.3f},{oy:.3f}) -> ({nx:.3f},{ny:.3f}) [{cnt}]")
def split_segment(ax, ay, bx, by, mx, my):
    a, b, m = V(ax, ay), V(bx, by), V(mx, my)
    for s in segs():
        if (near(s.GetStart(), a) and near(s.GetEnd(), b)) or (near(s.GetStart(), b) and near(s.GetEnd(), a)):
            s.SetStart(a); s.SetEnd(m)
            t = pcbnew.PCB_TRACK(board); t.SetStart(m); t.SetEnd(b); t.SetWidth(s.GetWidth()); t.SetLayer(s.GetLayer()); t.SetNet(s.GetNet()); board.Add(t); t.thisown = False
            log.append(f"  split ({ax:.3f},{ay:.3f})-({bx:.3f},{by:.3f}) at ({mx:.3f},{my:.3f})"); return
    raise AssertionError(f"segment ({ax},{ay})-({bx},{by}) not found")
log.append("R10 D1-A"); move_vertex(55.243, 86.425, 55.40, 86.425)
split_segment(55.40, 86.425, 54.413, 87.255, 55.245, 86.58); split_segment(55.245, 86.58, 54.413, 87.255, 54.60, 86.58)
log.append("R12 COL_MCU_02"); split_segment(54.955, 84.096, 59.081, 84.096, 58.987, 84.19); move_vertex(54.955, 84.096, 54.862, 84.19)
log.append("R14 D101-A")
move_vertex(54.724, 79.120, 54.70, 79.144); move_vertex(54.724, 79.749, 54.70, 79.85)
split_segment(54.878, 79.903, 58.900, 79.903, 58.797, 80.00); split_segment(54.878, 79.903, 58.797, 80.00, 55.86, 80.00)
split_segment(54.878, 79.903, 55.86, 80.00, 55.70, 80.16); move_vertex(54.878, 79.903, 55.01, 80.16)
log.append("R16 D141-A"); move_vertex(59.189, 74.948, 59.02, 75.118); move_vertex(59.189, 76.058, 59.02, 76.058)
log.append("R22 D261-A"); split_segment(50.271, 67.078, 50.937, 67.744, 50.815, 67.744); move_vertex(50.271, 67.078, 50.271, 67.20)
log.append("R24 COL_15 stub"); move_vertex(65.080, 62.400, 65.080, 62.25); move_vertex(65.440, 62.400, 65.44, 62.25)
z = 0
for s in segs():
    if near(s.GetStart(), s.GetEnd()): board.Remove(s); s.thisown = False; REMOVED.append(s); z += 1
log.append(f"removed {z} zero-length segments")

# ---------- 5. via placement with an all-layer spot search ----------
def items_near(c, r):
    R = int(r * 1e6); out = []
    for t in board.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            if near(t.GetPosition(), c, R): out.append(t)
        elif near(t.GetStart(), c, R) or near(t.GetEnd(), c, R) or t.GetEffectiveShape(t.GetLayer()).Collide(c, R): out.append(t)
    for f in board.GetFootprints():
        if near(f.GetPosition(), c, R + 4000000):
            for p in f.Pads():
                if near(p.GetPosition(), c, R): out.append(p)
    return out
def on_layer(it, L):
    if it.GetClass() == 'PCB_VIA': return it.GetLayerSet().Contains(L)
    if it.GetClass() == 'PAD': return it.GetLayerSet().Contains(L)
    return it.GetLayer() == L
def min_clear(shape, L, net, items, exclude):
    m = 9e9
    for it in items:
        if it.GetNetCode() == net or not on_layer(it, L): continue
        m = min(m, shape.GetClearance(it.GetEffectiveShape(L)) / 1e6)
    return m
def place_via(cx, cy, px, py, radius, step=0.025):
    c = V(cx, cy); via = [v for v in vias() if near(v.GetPosition(), c)]; assert len(via) == 1, (cx, cy); via = via[0]
    att = [(s, 'S') for s in segs() if near(s.GetStart(), c)] + [(s, 'E') for s in segs() if near(s.GetEnd(), c)]
    exid = set([via.m_Uuid.AsString()] + [s.m_Uuid.AsString() for s, _ in att]); net = via.GetNetCode()
    items = [it for it in items_near(V(px, py), radius + 2.5) if it.m_Uuid.AsString() not in exid]; excl = ()
    drill = via.GetDrillValue() / 1e6
    cands = []
    k = int(radius / step) + 1
    for ix in range(-k, k + 1):
        for iy in range(-k, k + 1):
            x, y = px + ix * step, py + iy * step
            if math.hypot(x - px, y - py) <= radius: cands.append((math.hypot(x - px, y - py), x, y))
    cands.sort()
    orig = via.GetPosition()
    def apply(p):
        via.SetPosition(p)
        for s, e in att: (s.SetStart if e == 'S' else s.SetEnd)(p)
    best = None
    for _, x, y in cands:
        p = V(x, y); apply(p)
        r = via.GetWidth(pcbnew.B_Cu) / 2e6
        if x - r < EDGE_L / 1e6 + EDGE or x + r > EDGE_R / 1e6 - EDGE or y - r < EDGE_T / 1e6 + EDGE or y + r > EDGE_B / 1e6 - EDGE: continue
        ok = True; worst = 9e9
        for L in CU:
            if not via.GetLayerSet().Contains(L): continue
            m = min_clear(via.GetEffectiveShape(L), L, net, items, excl); worst = min(worst, m)
            if m < CLR: ok = False; break
        if not ok: continue
        for it in items:          # hole to hole
            if it.GetClass() == 'PCB_VIA' or (it.GetClass() == 'PAD' and it.GetDrillSizeX() > 0):
                d2 = (it.GetDrillValue() if it.GetClass() == 'PCB_VIA' else it.GetDrillSizeX()) / 1e6
                if (it.GetPosition() - p).EuclideanNorm() / 1e6 - (drill + d2) / 2 < HOLE2HOLE: ok = False; break
        if not ok: continue
        for s, _ in att:
            m = min_clear(s.GetEffectiveShape(s.GetLayer()), s.GetLayer(), net, items, excl); worst = min(worst, m)
            if m < CLR: ok = False; break
        if ok: best = (x, y, worst); break
    if best is None:
        apply(orig); log.append(f"  !! via {via.GetNetname()} {F(orig)}: NO SPOT within {radius} of ({px:.3f},{py:.3f})"); return False
    log.append(f"  via {via.GetNetname():14s} {F(orig)} -> ({best[0]:.3f},{best[1]:.3f})  moved {math.hypot(best[0]-cx,best[1]-cy):.3f}  worst clr {best[2]:.3f}")
    return True
log.append("via placement")
place_via(54.614, 88.221, 54.45, 88.40, 0.6)      # R10 CS3
place_via(55.378, 88.600, 55.40, 88.70, 0.6)      # R10 ROW_08
place_via(51.051, 88.497, 51.15, 88.60, 0.6)      # R11 D1-A
place_via(54.601, 82.843, 54.45, 82.70, 0.6)      # R12 D1-A
place_via(50.525, 80.025, 50.42, 80.25, 0.6)      # R15 D121-A
place_via(54.687, 71.412, 54.55, 70.72, 0.8)      # R20 D41-A
place_via(50.825, 70.200, 50.825, 70.10, 0.5)     # R21 D1-A
place_via(51.100, 65.600, 51.10, 65.45, 0.8)      # R22 D41-A
place_via(54.848, 65.528, 54.75, 65.33, 0.6)      # R26 D21-A
place_via(64.985, 54.540, 64.93, 54.80, 0.8)      # R27 D141-A

# ---------- 6. courtyard overlap report ----------
for i in range(9, 29):
    fp = board.FindFootprintByReference(f'R{i}'); cy = fp.GetCourtyard(pcbnew.B_CrtYd).BBox()
    for f in board.GetFootprints():
        if f is fp or not near(f.GetPosition(), fp.GetPosition(), 4000000): continue
        o = f.GetCourtyard(pcbnew.B_CrtYd).BBox()
        if o.GetWidth() == 0: continue
        ox = min(cy.GetRight(), o.GetRight()) - max(cy.GetLeft(), o.GetLeft()); oy = min(cy.GetBottom(), o.GetBottom()) - max(cy.GetTop(), o.GetTop())
        if ox > 0 and oy > 0 and f.GetReference() != fp.GetReference(): log.append(f"  courtyard overlap R{i}/{f.GetReference()}: {min(ox,oy)/1e6:.3f} mm")

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(OUT, board)
print('\n'.join(log)); print('saved', OUT)
