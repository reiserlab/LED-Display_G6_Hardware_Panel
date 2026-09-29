# IR-red panel v0.4r2 — change notes

Baseline: `production/v0p4r1` (board rev v0.4.1, 2026-08-26). Specification: `panel/bench/hw-column-resistor-analysis.md`
and `panel/bench/hw-irred-v0p4r2-bom-changes.md` in `LED-Display_G6_Firmware_Panel`. Goals: red/IR checkerboard,
more red output for CsChrimson, column resistors inside their power rating. MCU, PSRAM, drivers, connectors,
LED footprints and all other parts are unchanged.

## 1. Checkerboard (BOM only)

| bank | v0.4r1 | v0.4r2 | LCSC |
|---|---|---|---|
| LED_T0 | red | red | C2852592 (Kingbright APHHS1005SURCK) |
| LED_T1 | IR | IR | C6879329 (Inolux IN-S42CTQIR) |
| LED_T2 | red | **IR** | C6879329 |
| LED_T3 | IR | **red** | C2852592 |

Changed the `LCSC Part #` field on the 200 `LED_T2`/`LED_T3` symbols in `panel_led.kicad_sch` and on their PCB
footprints. No net or layout change. The bottom silkscreen legend was updated to match (`0|3: APHHS1005SURCK`,
`1|2: IN-S42CTQIR`, `R: 47|100Ω`; was `0|2`, `1|3`, `R: 100Ω ±1%`). **Firmware:** red = channels 0 and 3 (`sch_col % 4 ∈ {0,3}`), IR = channels 1
and 2; `panel_test.py led 0|3` drives red (was `0|2` on v0.4r1).

## 2. Column resistors R9–R28

Footprint `Resistor_SMD:R_0201_0603Metric` → `Resistor_SMD:R_0402_1005Metric` (pads 0.54 × 0.64 mm at ±0.51 mm),
bottom side, same rotation. Schematic values stay symbolic (`R_T0`…`R_T3`); the part is in the LCSC field. The bottom
silkscreen legend reads `R: 47|100Ω`.

Values (final, 2026-09-26): a **conservative design around 0.7 A per panel**. The spec's 33 Ω / 56 Ω pair had no
56 Ω stock; a 22 Ω / 47 Ω "maximum current" variant was evaluated and rejected because it draws ≈1.2 A per panel and
droops the 5 V rail below the drivers' 4.5 V minimum (see the Codex cross-review notes in the PR). All parts 0.2 W
"high-power" 0402, ±1 %, in stock at JLCPCB/LCSC:

| bank (refs) | colour | value | part in BOM | LCSC | stock 2026-09-26 |
|---|---|---|---|---|---|
| R_T0 (R9, R13, R17, R21, R25), R_T3 (R12, R16, R20, R24, R28) | red | 47 Ω 1 % 0.2 W | ROHM ESR01MZPF47R0 | **C5736551** | 20 000 (alt. Yageo SR0402FR-7T47RL C854484, 3 869) |
| R_T1 (R10, R14, R18, R22, R26), R_T2 (R11, R15, R19, R23, R27) | IR | 100 Ω 1 % 0.2 W | Panasonic ERJ-PA2F1000X | **C427235** | 38 693 (alt. Vishay CRCW0402100RFKEDHP C844502, 4 754) |

Operating points from the analysis-doc model (5 V, 1.3 Ω source, 0.55 Ω sink shared by the row, red V_F = 1.79 V +
8 Ω·I, IR V_F = 1.34 V + 3 Ω·I, checkerboard so every row has 10 red + 10 IR), full-field at duty 255:

| | red 47 Ω | IR 100 Ω |
|---|---|---|
| own colour only: I, resistor power (1.3 Ω source model; with the datasheet's 5 Ω pull-up, see below: 49 / 32 mA) | 52 mA, 114 mW (57 %) | 33 mA, 100 mW (50 %) |
| red + IR all on: I | 49 mA | 31 mA |
| vs v0.4r1 (100 Ω 0201) | ×2.0 current | ×1.0 (unchanged), resistor now at 50 % instead of 198 % |
| LED rating used | 28 % of the 185 mA pulse rating; 30 mA DC | 47 % of 70 mA DC; 500 mA pulse |

Row current all-on 0.80 A → row-sink drop 0.44 V (red falls ≈6 % when the IR bank is also lit); 5 V droop ≈0.40 V
over the 45 µs pulse with the existing 18 × 10 µF, i.e. a 5.0 V rail stays at ≈4.6 V, above the UCC27517's 4.5 V
minimum recommended VDD. The red resistor is insensitive to the LED V-I extrapolation at this current (≤64 % of
rating even with a 4 Ω dynamic resistance).

**Supply current:** one row is on for 45 of every 50 µs, so the panel's 5 V current is 0.9 × the row current:
≈**0.72 A average** (0.80 A pulses, ≈0.76 A RMS) for a full-field red+IR pattern at duty 255; ≈0.47 A red-only,
≈0.30 A IR-only; v0.4r1 was ≈0.53 A all-on. The "≈50 mA" in the analysis doc multiplied the row current by the
per-LED duty and is wrong by ×20; the JST SH 5 V entry (≈1 A/contact) and the single 5 V pin per inter-panel header
still deserve a check for multi-panel arenas.

Alternatives at the same ≈0.72 A budget: 68 Ω / 68 Ω (red ×1.5, IR ×1.5, 46 % / 68 %). Higher-output options that were
modelled: 33/100 Ω (0.84 A, red ×2.5), 27/100 Ω (0.92 A, red ×2.9), 22/47 Ω (1.22 A, red ×3.3, IR ×2.0 — rejected).
Standard 1/16 W 0402 parts must not be substituted. Not in stock at any brand on 2026-09-26: 18, 24, 30, 39, 43, 51,
56, 62 Ω (0.2 W 0402 ±1 %).

### Driver current (UCC27517) — added 2026-09-28 after review

The UCC27517 output is rated 0.3 A continuous and 4 A only for 0.5 µs pulses (absolute maxima); a 45 µs row pulse is
in neither column of that table, so the question is what physically limits the part. It is a MOSFET output stage with
no pulse-specific mechanism: the limit is I²·R heating of the output FET (junction ≤150 °C; R_θJA 217.6 °C/W for the
SOT-23-5) and, for DC, metallisation. Two corrections to the circuit model used above:

- **Column drivers source through the P-MOS pull-up: R_OH = 5 Ω typ / 11 Ω max at 4.5 V** (datasheet §9.3.5: the
  N-MOS boost that gives the 4 A peak is on only during the switching edge). The analysis doc's 1.3 Ω "1.4 × R_OL"
  applies to that edge, not to a 45 µs pulse.
- **Row drivers sink through the N-MOS: R_OL = 0.6 Ω typ / 1.2 Ω max at 4.5 V**, 0.43 → 0.78 Ω from −40 to 140 °C.

| v0.4r2, 47 Ω / 100 Ω, all 20 LEDs of the row on | typ (5 Ω / 0.6 Ω) | datasheet max (11 Ω / 1.2 Ω) |
|---|---|---|
| LED current red / IR | 46 / 30 mA | 37 / 26 mA |
| row pulse (45 µs of 50 µs) | 0.76 A | 0.63 A |
| row driver: RMS / average current | 0.16 A / 34 mA | 0.13 A / 28 mA |
| row driver: average power → junction rise | 15 mW → +3.4 °C | 21 mW → +4.6 °C |
| row driver: energy per pulse → transient rise | 15 µJ → ≈1 °C | 21 µJ → ≈1–2 °C |
| column driver (its LED lit in every row, 90 %) | 9.5 mW → +2 °C | 14 mW → +3 °C |
| **stalled scan** (one row held on, all columns on) | **0.34 W → +75 °C** | **0.47 W → +103 °C** |

For comparison the rated 0.5 µs, 4 A pulse deposits ≈5 µJ; our pulse deposits 3–4× that energy but at 1/50 the power
over 90× the time, and heat diffuses ≈60 µm in silicon in 45 µs, so the transient rise stays at a degree or two.
v0.3 (160 Ω green, 0.33 A rows) dissipates 3 mW per row driver, v0.4r1 (100 Ω) 8.5 mW; the rejected 22/47 Ω point
would have been 41–47 mW (+9–10 °C) — still fine in scanning, but 0.9–1.0 W (+200 °C) if a row stalled.

**Conclusion:** during scanning the drivers are not a heat source at any revision (RMS 0.16 A < 0.3 A, average 34 mA,
junction +3–5 °C). Shortening the row pulse does not help: for the same light the peak current rises in proportion and
I²·t heating gets worse. The exposure is a **held-on row**: at v0.4r2 currents the row driver reaches 100–130 °C
junction in a 25 °C room and exceeds 140 °C at 40 °C ambient; the LEDs (red 46 mA DC vs 30 mA rating) and, on v0.4r1,
the 0201 resistors (78–110 mW vs 50 mW) also overload. The firmware bounds this: the row PIO state machine turns the row
off after its own delay count regardless of the CPU (`display_scan_twopio.cpp`), and a 2 ms per-row completion timeout
fails dark. Worth adding: a hard cap on the PIO delay count (≤100 µs) and the RP2350 hardware watchdog so a CPU hang
reboots into all-off.

## 3. Layout

Copper-to-copper distance from each resistor's pads to the nearest foreign-net copper on B.Cu (other footprints'
pads, tracks, vias), measured with the pcbnew shape API, mm. "—" = nothing within 0.30 mm. JLCPCB minimum 0.127.

| ref | 0201 as built (v0.4r1) | 0402 dropped in place, nothing else changed | v0.4r2 |
|---|---|---|---|
| R9 | 0.143 | 0.179 | 0.179 |
| R10 | 0.156 | **0 (D1-A track through pad 2; via CS3 0.034; via ROW_08 0.118)** | 0.136 |
| R11 | — | **0.096 (via D1-A)** | 0.135 |
| R12 | 0.143 | **0 (COL_MCU_02 tracks under pad 1; via D1-A 0.029)** | 0.137 |
| R13 | — | 0.283 | 0.283 |
| R14 | 0.133 | **0 (own pad-2 net D101-A runs past pad 1)** | 0.152 |
| R15 | 0.127 | **0 (own pad-2 net D121-A track and via)** | 0.154 |
| R16 | 0.127 | **0.007 (own pad-2 net D141-A track)** | 0.176 |
| R17 | 0.144 | **0.013 (via D41-A; via COL_MCU_09 0.082)** | 0.137 |
| R18 | 0.236 | 0.272 | 0.272 |
| R19 | — | 0.248 | 0.248 |
| R20 | 0.162 | **0 (via D41-A)** | 0.182 |
| R21 | — | **0.115 (pad C28.1)** | 0.165 |
| R22 | 0.146 | **0 (own net D261-A track; via D41-A 0.012)** | 0.144 |
| R23 | — | 0.293 | 0.293 |
| R24 | — | **0.113 (COL_MCU_17 track)** | 0.219 |
| R25 | 0.188 | **0.062 (via D100-A)** | 0.212 |
| R26 | 0.223 | **0 (via D21-A)** | 0.137 |
| R27 | 0.132 | **0 (via D141-A)** | 0.156 |
| R28 | — | 0.193 | 0.193 |

Differences from the spec: the exact-geometry check found **14** conflicting sites, not 10 — R14, R15, R16 (the
resistor's own anode-net track passes pad 1 on its way to a via) and R21 (pad-to-pad to C28.1 is 0.115, not 0.14)
were listed as clear. The 0402 pad is 0.64 mm *across* the resistor axis and 0.54 mm along it, which also matters
for the corridors below.

Four corridors are too narrow for a 0.127 mm track with 0.127 mm on both sides, so a via or track move alone could
not fix them: under R12 pad 1 to U4's pad row (0.275 mm), under R14 pad 1 to U6's pad row (0.273 mm), west of R15
and R22 to the board edge at x = 50.0 (edge clearance 0.2 mm), and between via D61-A and R10 pad 2 (0.371 mm; that
via is pinned by an In2 CS2 track at 0.127 mm). Also via D100-A (R25) has no legal spot east of pad 2 (U19 pads),
and vias D41-A/COL_MCU_09 (R17) none within 0.6 mm on all layers. These were solved by nudging the resistor
centres; no driver, connector, capacitor or other part moved.

Resistor centre nudges (KiCad coordinates, +y is down):

| ref | Δ (mm) | new centre | reason |
|---|---|---|---|
| R10 | +0.03 y | 55.140, 87.560 | D1-A track now fits between via D61-A and pad 2 at 0.137/0.137; J3.2 below limits further movement |
| R12 | −0.18 y | 55.125, 83.160 | COL_MCU_02 horizontal moved to y = 84.19: 0.187 to pad 1, 0.142 to U4 pads |
| R14 | +0.20 x | 55.320, 79.145 | D101-A now passes between via COL_MCU_04 and pad 1, then under pad 1 at y = 80.16 and above U6's pads at y = 80.00 |
| R15 | +0.17 x | 50.830, 79.155 | D121-A track keeps its original x = 50.269 (0.207 from the edge), 0.19 from pad 1 |
| R17 | +0.15 x | 55.270, 74.965 | clears vias D41-A (0.163) and COL_MCU_09 (0.232) without moving them |
| R21 | −0.05 y | 50.700, 71.250 | 0.165 to C28.1; via D1-A moved 0.10 north |
| R22 | +0.17 x | 50.850, 66.465 | D261-A track keeps x = 50.271; its bend lowered to y = 67.20 |
| R24 | −0.15 y | 65.080, 62.570 | COL_MCU_17 diagonal clears pad 2 by 0.22 (re-routing it collides with C74) |
| R25 | −0.15 x | 59.440, 66.455 | via D100-A stays; 0.212 to pad 2 |

Via moves (found by an all-layer search: ≥0.135 mm to foreign copper on every layer, hole-to-hole ≥0.26 mm,
≥0.21 mm to the board edge, attached segments re-pointed and checked):

| net | from | to | moved (mm) |
|---|---|---|---|
| /panel_header/CS3 | 54.614, 88.221 | 54.450, 88.350 | 0.21 |
| /drivers/ROW_08 | 55.378, 88.600 | 55.400, 88.700 | 0.10 |
| Net-(D1-A) (R11) | 51.051, 88.497 | 51.200, 88.400 | 0.18 |
| Net-(D1-A) (R12) | 54.601, 82.843 | 54.525, 82.950 | 0.13 |
| Net-(D121-A) | 50.525, 80.025 | 50.395, 80.200 | 0.22 |
| Net-(D41-A) (R20) | 54.687, 71.412 | 54.575, 70.795 | 0.63 |
| Net-(D1-A) (R21) | 50.825, 70.200 | 50.825, 70.100 | 0.10 |
| Net-(D41-A) (R22) | 51.100, 65.600 | 50.400, 65.450 | 0.72 |
| Net-(D21-A) | 54.848, 65.528 | 54.650, 65.455 | 0.21 |
| Net-(D141-A) | 64.985, 54.540 | 64.480, 54.525 | 0.51 |

Track edits: R10 D1-A (jog to y = 86.58 between via D61-A and pad 2), R12 COL_MCU_02 (horizontal 84.096 → 84.19
with a 45° jog back at x ≈ 59.0), R14 D101-A (west leg x = 54.724 → 54.70, then y = 80.16 under pad 1 and y = 80.00
above U6), R16 D141-A (west leg x = 59.189 → 59.02), R22 D261-A (bend y = 67.078 → 67.20), R24 COL_15 stub
(y = 62.40 → 62.25 so it stays inside the moved pad). 15 pre-existing zero-length track stubs were removed. Zones
refilled.

## 4. DRC

`kicad-cli 10.0.1 pcb drc --severity-all` with clearance 0.127 mm (netclass and board minimum; other constraints as
in the project: hole-to-hole 0.25, edge 0.2, hole clearance 0.2). Report: `production/v0p4r2/drc_jlcpcb_0p127.rpt`.

| | v0.4r1 (baseline) | v0.4r2 |
|---|---|---|
| clearance errors | 68 — all 0.1245–0.1263 mm, the board's 0.125 mm netclass, none near R9–R28 | **68, the same items** |
| unconnected items | 0 | 0 |
| courtyard overlaps | 0 | **19** — the 0402 courtyard (0.15 mm margin) overlaps the neighbouring SOT-23-5 courtyard by 0.10–0.14 mm at 17 sites, 0.28 mm at R15/U9 and R22/U16, and C28's at R21 (0.23). No copper involved; JLCPCB does not check courtyards. Shrinking the resistor courtyard margin to 0.05 mm would clear most of them if a clean report is wanted. |
| silk warnings | 17 | 20 — three new "silk clipped by mask" (J3 and U12 outlines over R9/R10/R21 pad 1); cosmetic |
| schematic parity | — | 0 (BOM, designators and netlist regenerate from the schematic without differences) |

At the project's own rules (0.125 mm) the copper DRC is clean apart from the courtyard overlaps.

## 5. Not done

- **Bulk capacitance (spec change 4, optional):** no room. With courtyards padded by 0.15 mm and tracks by
  0.2 mm there is no free bottom-side area for a 1206 or 0805 within 4 mm of any column driver U3–U22; the only
  1206-sized free area on the bottom side is at ≈(76.7, 64.0), 8 mm from U22, fitting one part. Adding 2–4 ×
  22–47 µF therefore needs parts moved and is left for a layout revision; expect ≈0.68 V droop on the 45 µs
  all-on pulse at the rejected 22/47 Ω point; ≈0.40 V at the chosen 47/100 Ω.
- **Other variants:** the layout part of this change (`tools/column_resistors_0402/`) applies unchanged to
  `panel_rp2354_20x20_four-color_v0p4` and `panel_rp2354_20x20_v0p3` (identical layouts). Not applied here; see the
  PR discussion.

## 6. Production files

`production/v0p4r2/` was generated with Fabrication Toolkit 5.3.1 (`-t -f -nI -nB`, i.e. the options in
`fabrication-toolkit-options.json`): `G6_RIRI_45mm_RP2354_v0.4.2.zip`, `bom.csv`, `positions.csv`, `designators.csv`,
`netlist.ipc`. Versus v0p4r1: BOM rows for LED_T2/LED_T3 and the four resistor banks changed; `positions.csv` differs
only in the nine nudged resistors; `designators.csv` is identical.
