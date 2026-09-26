"""Text pass on the saved board: for footprints R9-R28 add the LCSC Part # property and drop KiLib_Generator."""
import re, sys
LCSC = {'R_T0': 'C313374', 'R_T3': 'C313374', 'R_T1': 'C5736551', 'R_T2': 'C5736551'}   # 22 Ω Vishay CRCW040222R0FKEDHP / 47 Ω ROHM ESR01MZPF47R0, 0.2 W
s = open(sys.argv[1]).read()
parts = re.split(r'(\n\t\(footprint )', s); out = [parts[0]]; n = 0
for i in range(1, len(parts), 2):
    blk = parts[i + 1]
    ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
    val = re.search(r'\(property "Value" "([^"]*)"', blk).group(1)
    if val in LCSC and re.fullmatch(r'R(9|1\d|2[0-8])', ref):
        assert '"LCSC Part #"' not in blk, ref
        # drop KiLib_Generator property block (balanced parens, starts at line beginning)
        m = re.search(r'\n\t\t\(property "KiLib_Generator"', blk)
        if m:
            j = m.start() + 1; depth = 0; k = j
            while True:
                if blk[k] == '(': depth += 1
                elif blk[k] == ')':
                    depth -= 1
                    if depth == 0: break
                k += 1
            blk = blk[:m.start()] + blk[k + 1:]
        # insert LCSC property after the Description property block
        m = re.search(r'\n\t\t\(property "Description"', blk); j = m.start() + 1; depth = 0; k = j
        while True:
            if blk[k] == '(': depth += 1
            elif blk[k] == ')':
                depth -= 1
                if depth == 0: break
            k += 1
        rot = re.search(r'\n\t\t\(at [-\d.]+ [-\d.]+ ?([-\d.]*)\)', blk).group(1) or '0'
        import uuid
        prop = ('\n\t\t(property "LCSC Part #" "%s"\n\t\t\t(at 0 0 %s)\n\t\t\t(unlocked yes)\n\t\t\t(layer "B.Fab")\n\t\t\t(hide yes)\n\t\t\t(uuid "%s")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t\t(justify mirror)\n\t\t\t)\n\t\t)') % (LCSC[val], rot, uuid.uuid4())
        blk = blk[:k + 1] + prop + blk[k + 1:]; n += 1
    out += [parts[i], blk]
open(sys.argv[1], 'w').write(''.join(out)); print('fix_fields: patched', n, 'footprints')
