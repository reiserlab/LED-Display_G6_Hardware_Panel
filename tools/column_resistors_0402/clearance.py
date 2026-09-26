"""Measure copper clearance around column resistors R9-R28.
usage: clearance.py board.kicad_pcb [asis|hypo0402] [--dump]
asis     : pads as they are in the board
hypo0402 : a library R_0402_1005Metric placed at each resistor's centre/rotation/side
Reports, per resistor, the nearest foreign-net copper (other footprints' B.Cu pads,
B.Cu tracks, vias) to each pad, in mm. Negative = overlap."""
import sys, pcbnew
LIB='/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints/Resistor_SMD.pretty'
board=pcbnew.LoadBoard(sys.argv[1]); mode=sys.argv[2]; dump='--dump' in sys.argv
B=pcbnew.B_Cu; mm=1e-6
refs=[f'R{i}' for i in range(9,29)]
tracks=[t for t in board.GetTracks()]
def near(center, r):
    out=[]
    for t in tracks:
        if t.GetClass()=='PCB_VIA' or t.GetLayer()==B:
            if (t.GetPosition()-center).EuclideanNorm()<r*1e6 or (t.GetClass()!='PCB_VIA' and (t.GetEnd()-center).EuclideanNorm()<r*1e6):
                out.append(t)
    return out
def fpads(center,r,exclude):
    out=[]
    for f in board.GetFootprints():
        if f.GetReference()==exclude: continue
        if (f.GetPosition()-center).EuclideanNorm()>(r+3)*1e6: continue
        for p in f.Pads():
            if p.GetLayerSet().Contains(B) and (p.GetPosition()-center).EuclideanNorm()<r*1e6: out.append(p)
    return out
worst_all=[]
for ref in refs:
    fp=board.FindFootprintByReference(ref); c=fp.GetPosition()
    if mode=='hypo0402':
        h=pcbnew.FootprintLoad(LIB,'R_0402_1005Metric'); board.Add(h); h.SetPosition(c)
        if fp.IsFlipped(): h.Flip(c, pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        h.SetOrientation(fp.GetOrientation()); tgt=h
    else: tgt=fp
    padnet={p.GetNumber():p.GetNetname() for p in fp.Pads() if p.GetNumber()}
    old={p.GetNumber():p.GetPosition() for p in fp.Pads() if p.GetNumber()}
    rows=[]
    if mode=='hypo0402': pass
    for pad in tgt.Pads():
        n=pad.GetNumber()
        if not n or not pad.GetLayerSet().Contains(B): continue
        # sanity: hypothetical pad n must lie on the same side as the original pad n
        if mode=='hypo0402':
            d=(pad.GetPosition()-c); e=(old[n]-c)
            assert d.x*e.x+d.y*e.y>0, (ref,n,d,e)
        sh=pad.GetEffectiveShape(B); net=padnet[n]
        for it in near(c,1.6)+fpads(c,1.6,ref):
            if it.GetNetname()==net: continue
            dist=sh.GetClearance(it.GetEffectiveShape(B))*mm
            if dist<0.30:
                if it.GetClass()=='PCB_VIA': kind=f"via@({it.GetPosition().x*mm:.3f},{it.GetPosition().y*mm:.3f})"
                elif it.GetClass()=='PCB_TRACK': kind=f"trk({it.GetStart().x*mm:.3f},{it.GetStart().y*mm:.3f})-({it.GetEnd().x*mm:.3f},{it.GetEnd().y*mm:.3f}) w{it.GetWidth()*mm:.3f}"
                else: kind=f"pad {it.GetParentFootprint().GetReference()}.{it.GetNumber()}"
                rows.append((dist,n,net,kind,it.GetNetname()))
    rows.sort()
    worst=rows[0][0] if rows else 9
    worst_all.append((ref,worst))
    flag='  <-- VIOLATION (<0.127)' if worst<0.127 else ('  (<0.20)' if worst<0.20 else '')
    print(f"{ref:4s} {fp.GetValue()} at ({c.x*mm:.3f},{c.y*mm:.3f}) rot {fp.GetOrientationDegrees():.0f}  worst {worst:+.3f} mm{flag}")
    for r in rows[: (12 if dump else 3)]:
        print(f"      {r[0]:+.3f}  pad{r[1]}[{r[2]}] vs {r[3]} [{r[4]}]")
print("\nSUMMARY", mode, "min over all:", f"{min(w for _,w in worst_all):+.3f}", "violations(<0.127):", [r for r,w in worst_all if w<0.127])
