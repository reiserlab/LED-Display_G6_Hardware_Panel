---
title: "Four-color and Red+IR G6 panels: components and order decisions"
tags: [hardware, LED, G6, violet, blue, green, yellow, orange, red, infrared, checkerboard, procurement]
status: pilot order placed (15 four-color, 5 Red+IR panels); assembled-panel qualification pending
---

# Four-color and Red+IR G6 panels

Two new G6 panel variants populate the existing four independently current-limited color banks (`T0`-`T3`) with alternate LEDs. Neither requires LED-net rerouting, a driver-count change, a mapping-table change, or a firmware fork; both still need the normal 400-pixel mapping and polarity test.

This doc records which options were actually chosen, why, and what deviated from the two original recommendation write-ups. The full content of those two write-ups is summarized in the appendix below.

## Four-color panel

**Purpose:** a four-wavelength visible palette (405-410 nm violet, 460-475 nm blue, 516-534 nm green, 586-594 nm yellow-orange) intended to approximate a broader daylight-like spectrum for visual stimulation and optogenetics, with post-production calibration headroom built in via GS16 temporal modulation.

**Components ordered (BOM A, all-Yongyu):**

| Bank | Color | LED | Resistor |
|---|---|---|---|
| `T0` | violet | Yongyu `YY0402PU-NN3S0-T1AR4` | 68 Ω `C138127` (default) |
| `T1` | blue | Yongyu `YY0402BL-NN1S0-T1AR4` | 68 Ω `C138127` |
| `T2` | green | Yongyu `YY0402GR-NN1S0-T1AR4` | 68 Ω `C138127` |
| `T3` | yellow-orange | Yongyu `YY0402YE-NN1S0-T1AR4` | 110 Ω `C295716` |

**Decisions:**

- Chose **BOM A (all-Yongyu)** over BOM B (Yongyu violet + XINGLIGHT hybrid) to keep all four LEDs on one nominal package family, reducing mechanical/assembly risk. The hybrid would have been cheaper but needed its own footprint, polarity, and optical qualification for the XINGLIGHT parts.
- Ordered 3×3,000-piece reels (violet, blue, green) plus 1×5,000-piece reel (yellow-orange, the vendor's minimum order size for that part) via the manufacturer Guangdong Yongyu Optoelectronics, consigned to JLCPCB, without a confirmed violet `Vf` bin (the vendor could only offer unbinned reels at this quantity; for a larger future order they offered to bin the LEDs). The parts arrived on 2026-08-18. The 68 Ω default resistor stands until the first assembled panel is measured; adjust to 82.5 Ω or 56 Ω only from that measurement, per the source doc's bin table.
- Kept the 25 mA nominal / 30 mA sparse-pixel ceiling current target rather than pushing higher current now. Pushing more current and heat-sinking as needed was discussed as an option for a **future** test batch, not this pilot, so as not to consume the full reel before knowing whether the panels are bright enough.
- The violet/blue/green 3,000-piece reels remain the limiting factor (the yellow-orange 5,000-piece reel has spare headroom), giving material for up to ~29 panels. The pilot **assembly order is 15 panels**, placed on 2026-08-26, leaving the rest of the reels for follow-up batches.

## Red+IR checkerboard panel

**Purpose:** a 630 nm red + 850 nm IR checkerboard for combined optogenetic stimulation and camera-based tracking (e.g. FicTrac) illumination that stays outside the flies' visible range.

**Components ordered:**

| Bank | Channel | LED | Resistor |
|---|---|---|---|
| `T0`, `T3` | red | Kingbright `APHHS1005SURCK` | 100 Ω `C77623` |
| `T1`, `T2` | IR | Inolux `IN-S42CTQIR` | 100 Ω `C77623` |

**Decisions:**

- The source doc's recommended IR part, ams OSRAM `SFH 4053B`, had no workable near-term source: about 12 weeks via Mouser (~$650) or up to ~$2,200 with unclear lead time via LCSC. Switched to **Inolux `IN-S42CTQIR`** (via DigiKey), available in about 5 weeks at ~$730, to keep the pilot on schedule.
- The 100 Ω IR current-limit resistor is a calculated value based on the Inolux `IN-S42CTQIR` datasheet, not a doc recommendation (the source doc specified the OSRAM part and a 56 Ω resistor). It predicts that driving the IR LEDs at about 25-30 mA gives similar light intensity to the red channel; this has not yet been bench-verified on an assembled panel.
- The doc recommended building **12 panels** (9 for a 3x3 display + 3 spares/qualification). The actual pilot order is **5 panels**, matching the JLC minimum. This was a deliberate measure-first choice: the main risk identified was insufficient brightness (especially red), so the team preferred to qualify a small batch and decide on resistor/current changes before committing more of the ~3,040-3,050 red/IR LEDs already purchased (material for up to 15 panels).
- As with the four-color panel, higher current with heat-sinking was discussed as a possible follow-up if the pilot proves too dim, not as part of this order.

### Revision v0.4r2 (2026-09-26, PR reiserlab/LED-Display_G6_Hardware_Panel#1)

Two things were found after the pilot order and are corrected in `panel_rp2354_20x20_ir-red_v0p4` v0.4r2:

- **The v0.4r1 BOM as ordered had red on `T0`+`T2` and IR on `T1`+`T3`** (vertical red/IR stripes, even columns red), not the `T0`/`T3` red checkerboard in the table above. v0.4r2 swaps the `T2`/`T3` LCSC fields so red is on `T0`+`T3` and IR on `T1`+`T2` (checkerboard). Firmware channel = bank index: on v0.4r2 red = channels 0 and 3, IR = channels 1 and 2 (`panel_test.py led 0|3`).
- **The 0201 column resistors were over rating.** A column resistor conducts whenever any lit LED of its column is in the active row, i.e. up to 90 % of the frame for a full-field pattern, so it dissipates about 20× the LED's average power; the 100 Ω 0201 parts ran at 128–198 % of their 50 mW rating. v0.4r2 changes R9–R28 to 0402 0.2 W "high-power" parts: red banks 47 Ω (ROHM `ESR01MZPF47R0`, `C5736551`), IR banks 100 Ω (Panasonic `ERJ-PA2F1000X`, `C427235`). Red current about doubles (≈50 mA per LED while its row is active, 28 % of the LED's 185 mA pulse rating); IR is unchanged at ≈33 mA. Resistors run at 57 % / 50 % of rating. Higher-current options (down to 22 Ω red / 47 Ω IR, ≈3× red) were modelled and rejected: they pull ≈1.2 A per panel from 5 V and droop the rail below the drivers' 4.5 V minimum.
- **Panel supply current** for a full-field pattern is 0.9 × the row current (one row is on 45 µs of every 50 µs): ≈0.72 A average per panel at v0.4r2 values (0.80 A pulses), ≈0.53 A on v0.4r1. Earlier notes quoting ≈50 mA multiplied by the per-LED duty and are wrong. 5 V enters through the 4-pin JST SH (≈1 A per contact) and is bussed on one pin per inter-panel header; check the arena's power distribution before daisy-chaining many panels at full field.
- Layout: the 0402 pads needed nine resistors nudged by 0.03–0.20 mm, ten vias moved and six short track re-routes; no driver or other part moved. Details, before/after clearance tables and the DRC report: `panel_rp2354_20x20_ir-red_v0p4/CHANGES-v0p4r2.md` and `production/v0p4r2/`.

## Combined pilot order

15 four-color panels + 5 Red+IR panels, both assembled via JLCPCB from consigned DigiKey Marketplace reels. The $430 order (plus an additional ~$70 fab charge for undersized vias) covers PCB fabrication and assembly only; the LED components were already paid for and consigned separately in the earlier reel orders.

## Open items

- [ ] Measure the assembled four-color panel's violet `Vf` bin and confirm/adjust the 68 Ω resistor (82.5 Ω or 56 Ω per the bin table in Appendix A).
- [ ] Bench-verify the 100 Ω IR current-limit resistor for the Inolux `IN-S42CTQIR` substitution; the value is currently a datasheet calculation only (v0.4r2 keeps 100 Ω, now a 0.2 W 0402 part).
- [ ] v0.4r2 first articles: measure panel 5 V current and driver VDD droop at full field, confirm red on channels 0/3 and IR on 1/2 optically, inspect the tight resistor sites R14/U8, R15/U9, R17/U11, R22/U16 (0.14–0.18 mm body gap).
- [ ] Run the first-panel electrical/optical qualification steps summarized in Appendix A and Appendix B (sparse-pixel and full-row current, rail droop, spectra/photon irradiance at the fly position, red/IR visibility limits).
- [ ] Decide, based on pilot brightness measurements, whether a follow-up batch should push higher current with heat-sinking, using the remaining LEDs from the already-purchased reels.
- [ ] If a larger four-color order is placed later, follow up with Guangdong Yongyu Optoelectronics on their offer to bin the LEDs by `Vf`/wavelength.

## Appendix A: source doc summary, four-color palette

Target palette: 405-410 nm violet, 460-475 nm blue, 516-534 nm green, 586-594 nm yellow-orange centered near 590 nm. The violet LEDs are not true UV, just close to it.

**Bank mapping** (repeating physical cell: row 0 violet/blue, row 1 green/yellow-orange):

| Bank | Physical positions | Color | Resistor identities |
|---|---|---|---|
| `T0` | even row, even column | violet | R9, R13, R17, R21, R25 |
| `T1` | even row, odd column | blue | R10, R14, R18, R22, R26 |
| `T2` | odd row, even column | green | R11, R15, R19, R23, R27 |
| `T3` | odd row, odd column | yellow-orange | R12, R16, R20, R24, R28 |

**Two BOM options were proposed:**

- **BOM A, all-Yongyu:** violet `YY0402PU-NN3S0-T1AR4`, blue `YY0402BL-NN1S0-T1AR4`, green `YY0402GR-NN1S0-T1AR4`, yellow-orange `YY0402YE-NN1S0-T1AR4`. All four share the same nominal 0402 package, 140 degree viewing angle, and polarity convention, which lowers assembly risk. Provisional resistors: 68 Ω (`C138127`) for violet/blue/green, 110 Ω (`C295716`) for yellow-orange. Four 3,000-piece reels cost about $304 and yield up to 30 panels ($10.13/panel in LEDs).
- **BOM B, Yongyu violet + XINGLIGHT hybrid:** same Yongyu violet, but XINGLIGHT `XL-1005UBC`/`XL-1005UGC`/`XL-1005UYC` for blue/green/yellow-orange, which are directly JLC-stocked. Cheaper ($5.06-$7.52/panel depending on route) but the XINGLIGHT parts differ in body size, height, and viewing angle from Yongyu and needed their own footprint, polarity, and optical qualification before use.

**Violet resistor selection** depends on the received `Vf` bin: 82.5 Ω for 2.8-3.0 V, 68 Ω for 3.0-3.3 V, 56 Ω for 3.3-3.6 V. Without a known bin, use 68 Ω as the default and measure the assembled panel before reworking.

**Panel quantity options:** 5 (minimum pilot), 20 (efficient larger build), 28 (practical single-reel maximum), 30 (theoretical maximum consuming the entire reel with no spares). The 3,000-piece Yongyu violet reel is the limiting factor in both BOMs.

**Current target:** 25 mA nominal with a 30 mA sparse-pixel ceiling, justified because G6's Triggered/Gated scanning gives each LED only a fraction of a percent to a few percent electrical duty, well under the LEDs' pulsed ratings. The extra headroom also gives firmware calibration room: the weakest channel limits how bright a daylight-balanced four-channel mix can be, and GS16 can only dim channels down, not brighten them, so hardware headroom must be built in up front. A fully lit row draws about 0.50 A at 25 mA/LED and 0.60 A at the 30 mA ceiling; the pilot must verify rail droop, driver behavior, and resistor pulse tolerance (0201 resistors are rated 50 mW continuous, and pulse power at 25-30 mA can exceed that instantaneously even though average dissipation is low).

**Bring-up and calibration steps:** start at low GS16, measure sparse-pixel and full-row current per channel, reject anything over 30 mA sparse, check rail/waveforms/temperature, verify the 400-pixel mapping and polarity, measure spectra and photon irradiance at the fly position (equal current/mcd/GS16 are not equivalent across colors), and start continuous-mode violet at about half scale since violet has been unusually salient to flies in the past.

## Appendix B: source doc summary, Red+IR checkerboard

**Recommended build (as proposed):** 12 dedicated panels, 9 populating a 3x3 display and 3 held back for electrical/optical qualification, potentially destructive testing, rework, or replacement.

**Bank mapping** (checkerboard: red and IR alternate by row/column parity):

| Bank | Physical parity | LED | Resistor identities | Value |
|---|---|---|---|---|
| `T0` | even, even | red | R9, R13, R17, R21, R25 | 100 Ω |
| `T1` | even, odd | IR | R10, R14, R18, R22, R26 | 56 Ω |
| `T2` | odd, even | IR | R11, R15, R19, R23, R27 | 56 Ω |
| `T3` | odd, odd | red | R12, R16, R20, R24, R28 | 100 Ω |

**Proposed parts:** red = Kingbright `APHHS1005SURCK` (630 nm dominant, 645 nm peak, `Vf` 1.95 V typ/2.5 V max @ 20 mA, JLC-stocked `C2852592`), current-limited to about 26-30 mA with a 100 Ω resistor (`C77623`). IR = ams OSRAM `SFH 4053B` (850 nm centroid, `Vf` 1.50 V typ/1.75 V max @ 70 mA), current-limited to about 53-61 mA with the recommended 56 Ω resistor (`C295809`); 68 Ω (about 45-50 mA) was listed as a more conservative fallback and 51.1 Ω as a qualification-only option. These are instantaneous, row-active currents, not time-averaged ones, and depend on shared row-driver voltage drop. (The actual build substitutes Inolux `IN-S42CTQIR` and a 100 Ω resistor for the IR channel; see the Red+IR checkerboard panel section above.)

**Electrical caveat:** the existing G6 LED rail, row/column drivers, and resistors have not been tested at these proposed currents. A fully lit mixed red/IR row draws about 0.79 A. Instantaneous resistor dissipation at the top of the calculated ranges is about 90 mW (red, 100 Ω) and 208 mW (IR, 56 Ω) against a 50 mW continuous rating for the stock 0201 `RC0201` parts; average multiplexed dissipation is much lower (about 4.5 mW red, 10.4 mW IR at 5% duty), but pulse loading and assembled temperature still need bench verification. A pulse-rated `SR0201` automotive resistor family exists as a possible reliability upgrade if a suitable value can be sourced.

**Panel quantity options:** 5 (JLC minimum, uses about a third of the IR reel), 9 (exactly fills the 3x3 display with no spares), 12 (recommended: 9 display + 3 spare/qualification, leaving about 600 IR LEDs from one 3,000-piece reel), 14 (leaves 200 IR LEDs), 15 (theoretical reel maximum, no spares). Planning cost for 12 panels was about $841 in LEDs (~$58.92/panel placed, ~$70/panel cash cost including spares), before freight, tariffs, consignment, and assembly.

**First-panel qualification steps:** verify MPNs/polarity/land pattern, verify red on `T0`/`T3` and IR on `T1`/`T2`, start at low GS16, test all 400 pixel addresses, measure sparse-pixel and full-row current (do not exceed 30 mA red or 70 mA IR), measure rail/driver/resistor temperature and supply transients, measure red spectral power below 610 nm and IR visible leakage, establish the maximum red level flies do not behaviorally detect, confirm camera/tracking performance at the chosen IR level, and reserve one spare panel for full (including potentially destructive) qualification before releasing the display panels for experiments.
