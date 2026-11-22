#!/usr/bin/env python3
"""
Converts an indexed 80x192 PNG (<=9 colours) into an Atari BASIC GRAPHICS 10
program, in the spirit of "A tennis player" by Paul Bunn.

Note on GRAPHICS 10: it is a GTIA mode (ANTIC F + GTIA mode 2) and has no
text window option at all, so it already gives the full 80 x 192. There is no
need for "+16" here -- that applies to the ordinary CTIA/ANTIC modes.

CHANGES vs the earlier version
------------------------------
1. Compact encoding: ONE number per run instead of three.
   V = reg*128 + length, with 2000 ADDED to mark the last run of a row.
   length is 1..80 and reg is 0..8, so a mid-row V is 1..1104 and an
   end-of-row V is 2001..3104. All values are positive whole numbers -- no
   minus signs, which Atari BASIC's READ can treat as punctuation (error 8).
   This cuts program size by roughly a third, which matters because the whole
   picture must live in RAM alongside ~7.7K of screen memory.

2. Real diagnostics. If anything goes wrong the program prints the BASIC error
   code (PEEK(195)) and the row it reached, instead of silently looping.

3. X is clamped in the emitted code, so a bad value can never run off the
   right-hand edge of the screen.
"""

import colorsys
import re
from PIL import Image

IN_PNG = "your_image.png"
OUT_BAS = "atari_basic.bas"
OUT_PREVIEW = "final_image.png"

SCREEN_W, SCREEN_H = 80, 192

# ---------------------------------------------------------------------------
# Atari NTSC colour approximation
# ---------------------------------------------------------------------------
HUE_DEGREES = {
    0: None,                                   # grey / no chroma
    1: 40, 2: 20, 3: 25, 4: 355, 5: 300, 6: 265, 7: 250,
    8: 225, 9: 205, 10: 195, 11: 80, 12: 122, 13: 145, 14: 65, 15: 55,
}

def atari_byte_to_rgb(byte_val):
    hue_idx = (byte_val >> 4) & 0x0F
    luma = byte_val & 0x0F
    lightness = 0.03 + (luma / 14.0) * 0.94
    if HUE_DEGREES[hue_idx] is None:
        return (lightness, lightness, lightness)
    return colorsys.hls_to_rgb(HUE_DEGREES[hue_idx] / 360.0, lightness, 0.75)

ATARI_CANDIDATES = []
for _hue in range(16):
    for _luma in range(0, 16, 2):
        _bv = _hue * 16 + _luma
        _r, _g, _b = atari_byte_to_rgb(_bv)
        ATARI_CANDIDATES.append((_bv, int(_r * 255), int(_g * 255), int(_b * 255)))

def closest_atari_byte(rgb):
    r, g, b = rgb
    best_byte, best_dist = 0, float("inf")
    for byte_val, cr, cg, cb in ATARI_CANDIDATES:
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < best_dist:
            best_dist, best_byte = d, byte_val
    return best_byte

HUE_NAMES = {0:"Grey",1:"Rust",2:"Red-orange",3:"Dark orange",4:"Red",5:"Dk lavender",
             6:"Cobalt blue",7:"Ultramarine",8:"Medium blue",9:"Dark blue",10:"Blue-grey",
             11:"Olive green",12:"Medium green",13:"Dark green",14:"Orange-green",15:"Orange"}

# ---------------------------------------------------------------------------
# 1. Load image
# ---------------------------------------------------------------------------
im = Image.open(IN_PNG).convert("P")
W, H = im.size
assert (W, H) == (SCREEN_W, SCREEN_H), f"expected {SCREEN_W}x{SCREEN_H}, got {W}x{H}"
pal = im.getpalette()
pixels = list(im.tobytes())

counts = {}
for p in pixels:
    counts[p] = counts.get(p, 0) + 1
used_indices = sorted(counts.keys(), key=lambda i: -counts[i])
assert len(used_indices) <= 9, f"image has {len(used_indices)} colours, max 9 supported"

reg_of_index = {orig_idx: rank for rank, orig_idx in enumerate(used_indices)}

print(f"{'reg':>3} {'orig RGB':>16} -> {'byte':>5}  hue name        count")
reg_atari_byte = {}
for orig_idx in used_indices:
    rgb = (pal[orig_idx*3], pal[orig_idx*3+1], pal[orig_idx*3+2])
    bv = closest_atari_byte(rgb)
    reg = reg_of_index[orig_idx]
    reg_atari_byte[reg] = bv
    print(f"{reg:>3} {str(rgb):>16} -> {bv:>5}  {HUE_NAMES[(bv>>4)&0xF]:<14} {counts[orig_idx]:>6}")

# ---------------------------------------------------------------------------
# 2. Run-length encode each row
# ---------------------------------------------------------------------------
rows = []
for y in range(H):
    row_pixels = pixels[y*W:(y+1)*W]
    runs = []
    start = 0
    for x in range(1, W + 1):
        if x == W or row_pixels[x] != row_pixels[start]:
            runs.append((x - start, reg_of_index[row_pixels[start]]))
            start = x
    assert sum(r[0] for r in runs) == W, f"row {y} does not sum to {W}"
    rows.append(runs)

# ---------------------------------------------------------------------------
# 3. Emit the BASIC listing
#    V = reg*128 + length ; negative V marks the last run of a row.
# ---------------------------------------------------------------------------
lines = [
    "10 REM * CONVERTED FROM PNG *",
    "20 GRAPHICS 10:TRAP 500",
    f"30 POKE 704,{reg_atari_byte[0]}:POKE 705,{reg_atari_byte.get(1,0)}"
    f":POKE 706,{reg_atari_byte.get(2,0)}",
    f"40 POKE 707,{reg_atari_byte.get(3,0)}:POKE 708,{reg_atari_byte.get(4,0)}"
    f":POKE 709,{reg_atari_byte.get(5,0)}",
    f"50 POKE 710,{reg_atari_byte.get(6,0)}:POKE 711,{reg_atari_byte.get(7,0)}"
    f":POKE 712,{reg_atari_byte.get(8,0)}",
    "60 X=0:G=0",
    "70 READ V:C=0",
    "80 IF V>1500 THEN C=1:V=V-2000",
    "90 B=INT(V/128):A=V-B*128",
    "100 E=X+A-1:IF E>79 THEN E=79",
    "110 COLOR B:PLOT X,G:DRAWTO E,G:X=E+1",
    "120 IF C=1 THEN X=0:G=G+1",
    "130 IF G<192 THEN GOTO 70",
    "140 TRAP 40000:GOTO 140",
    '500 GRAPHICS 0:? "ERR ";PEEK(195);" ROW ";G:STOP',
]

MAX_LINE_CHARS = 100
line_no = 1000
for runs in rows:
    toks = []
    for i, (length, reg) in enumerate(runs):
        v = reg * 128 + length
        toks.append(str(v + 2000 if i == len(runs) - 1 else v))

    chunk, cur = [], len(f"{line_no} DATA ")
    for t in toks:
        if chunk and cur + len(t) + 1 > MAX_LINE_CHARS:
            lines.append(f"{line_no} DATA " + ",".join(chunk))
            line_no += 10
            chunk, cur = [], len(f"{line_no} DATA ")
        chunk.append(t)
        cur += len(t) + 1
    lines.append(f"{line_no} DATA " + ",".join(chunk))
    line_no += 10

out = "\n".join(lines) + "\n"
with open(OUT_BAS, "w") as f:
    f.write(out)

# ---------------------------------------------------------------------------
# 4. Size / memory estimate
# ---------------------------------------------------------------------------
tok = 0
for l in lines:
    m = re.match(r"(\d+) (.*)", l)
    body = m.group(2)
    if body.startswith("DATA "):
        tok += 2 + 1 + 1 + 1 + len(body[5:]) + 1
    else:
        tok += 2 + 1 + len(body) + 2
screen = 40 * 192 + 256
print(f"\nWrote {OUT_BAS}: {len(lines)} lines, {len(out)} source bytes")
print(f"  approx tokenised program : {tok:,} bytes")
print(f"  GR.10 screen + DL        : {screen:,} bytes")
print(f"  approx total RAM needed  : {tok+screen:,} bytes")
print(f"  longest line             : {max(len(l) for l in lines)} chars")

# ---------------------------------------------------------------------------
# 5. Simulate the emitted listing exactly, and render the preview from it
# ---------------------------------------------------------------------------
nums = []
for l in lines:
    m = re.match(r"\d+ DATA (.*)", l)
    if m:
        nums.extend(int(t) for t in m.group(1).split(","))

preview = Image.new("RGB", (W, H))
ppx = preview.load()
x = g = 0
issues = 0
for v in nums:
    c = 0
    if v > 1500:
        c = 1
        v = v - 2000
    b = v // 128
    a = v - b * 128
    if not (0 <= b <= 8) or not (1 <= a <= 80):
        issues += 1
        continue
    e = min(x + a - 1, 79)
    r, gg, bb = atari_byte_to_rgb(reg_atari_byte[b])
    col = (int(r*255), int(gg*255), int(bb*255))
    for xx in range(x, e + 1):
        ppx[xx, g] = col
    x = e + 1
    if c == 1:
        x = 0
        g += 1

print(f"  data values              : {len(nums):,}")
print(f"  simulated rows drawn     : {g} / 192   (bad values: {issues})")
preview.resize((W*6, H*6), Image.NEAREST).save(OUT_PREVIEW)
print(f"Wrote {OUT_PREVIEW}")
