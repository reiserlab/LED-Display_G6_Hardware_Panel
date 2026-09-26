# Column resistors 0201 → 0402 (v0.4r2 layout change)

Scripts used to produce `panel_rp2354_20x20_ir-red_v0p4` v0.4r2. They run with KiCad 10's bundled
Python (`/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`)
because they use `pcbnew`. All edits are made through the pcbnew API and verified by re-parsing; a
load/save round trip of these boards is byte-identical, so diffs contain only the intended changes.

| script | what it does |
|---|---|
| `clearance.py board.kicad_pcb asis\|hypo0402 [--dump]` | For R9–R28, nearest foreign-net copper (other footprints' B.Cu pads, B.Cu tracks, vias) to each pad, in mm. `hypo0402` measures a library `R_0402_1005Metric` dropped at each resistor's centre/rotation without any other change. |
| `edit_board.py in.kicad_pcb out.kicad_pcb` | LED bank LCSC swap (T2→IR, T3→red), R9–R28 footprint swap to `Resistor_SMD:R_0402_1005Metric` (same centre/rotation/side, nets, path, fields), nine resistor nudges, track re-routes, and via re-placement by an all-layer spot search (clearance ≥0.135 mm to foreign copper on every layer, hole-to-hole ≥0.26 mm, board edge ≥0.21 mm). Refills zones and saves. |
| `fix_fields.py out.kicad_pcb` | Text pass on the saved board: adds the `LCSC Part #` field to the 20 new footprints and drops the library's `KiLib_Generator` field (creating fields through SWIG corrupts the heap, see below). |

Then: `kicad-cli pcb drc --severity-all` with a copy of the `.kicad_pro` whose netclass/min clearance is set
to 0.127 mm, and the Fabrication Toolkit CLI for `production/`.

## Applying to the other two variants

`panel_rp2354_20x20_four-color_v0p4` and `panel_rp2354_20x20_v0p3` have the identical layout (557
footprints, same coordinates), so sections 2–5 of `edit_board.py` apply unchanged. Disable section 1 (the
LED LCSC swap is IR-red specific) and set the resistor LCSC codes in `fix_fields.py` (`LCSC`) to the 0.2 W
0402 parts wanted for that variant (green: 160 Ω, four-color: 68/68/68/110 Ω).

## pcbnew scripting pitfalls found (KiCad 10.0.1)

- `FOOTPRINT.GetField(name)` returns an *owning* wrapper: when the Python variable is rebound the C++ field is
  deleted and the heap is corrupted (symptom: later calls return bare `SwigPyObject`s). Iterate `GetFields()`.
- `BOARD.Remove(item)` hands ownership to Python; let the item be garbage-collected and the same happens.
  Keep removed items in a list and set `thisown = False`.
- `FOOTPRINT.Flip()` segfaults on a footprint that is not yet on a board; `board.Add()` first.
- `PCB_VIA.GetWidth()` needs a layer argument (`GetWidth(pcbnew.B_Cu)`).
- Python's stdout is lost on a segfault; run with `python3 -u`.
