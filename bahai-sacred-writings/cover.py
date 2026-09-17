#!/usr/bin/env python3
"""Generate the EPUB cover: gold serif capitals on dark blue linen.

Modelled on the hardcover (Bahá'í World Centre, 2026): plain dark blue cloth
with the title in gold small capitals. For a thumbnail the title is stacked
one word per line and set much larger. No author on the cover; the title
page inside credits both Bahá'u'lláh and 'Abdu'l-Bahá.

Requires ImageMagick 7 (`brew install imagemagick`) and macOS's bundled
Hoefler Text; run with an alternative font path as the first argument if
that font is unavailable.

Usage:  ./cover.py [font-path]        -> build/cover.jpg
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
OUT = BUILD / "cover.jpg"
# Fonts tried (all bundled with macOS, all carry Á and Í), in order of
# preference for this design:
#   Hoefler Text.ttc   - chosen: widest set, boldest colour, most legible
#                        as a thumbnail; closest to the hardcover's feel.
#   Baskerville.ttc    - lighter and more delicate; reads well at full size
#                        but thins out in an icon.
#   Bodoni 72 Smallcaps Book.ttf - true small caps (type the words in
#                        title case, e.g. "Bahá’í"), elegant but high-contrast
#                        hairlines disappear at small sizes.
# ImageMagick takes the first face of a .ttc; pass a .ttf for a specific
# weight. Non-macOS: any serif with Latin Extended coverage, e.g. Libre
# Baskerville or Cormorant Garamond from Google Fonts.
FONT = "/System/Library/Fonts/Supplemental/Hoefler Text.ttc"

W, H = 1600, 2400
BLUE = "#14305e"     # the overlay/softlight passes below lighten this a little
GOLD = "#c9a85a"     # muted foil gold; brighter golds look brassy on blue
WORDS = ["BAHÁ’Í", "SACRED", "WRITINGS"]
POINT = 250          # pointsize; WRITINGS then spans ~85% of the width
GAP = H // 6         # vertical distance between word baselines
RULE = 260           # half-length of the thin rules above and below


def magick(*args):
    subprocess.run(["magick", *args], check=True)


def main():
    font = sys.argv[1] if len(sys.argv) > 1 else FONT
    BUILD.mkdir(exist_ok=True)
    size = f"{W}x{H}"
    linen = BUILD / "linen.png"
    # Two orthogonal streaks of blurred noise, blended, read as woven cloth.
    magick("-size", size, "xc:gray50", "-seed", "7", "+noise", "Gaussian", "-colorspace", "gray",
           "-motion-blur", "0x6+0",
           "(", "-size", size, "xc:gray50", "-seed", "11", "+noise", "Gaussian", "-colorspace", "gray",
           "-motion-blur", "0x6+90", ")",
           "-compose", "blend", "-define", "compose:args=50", "-composite",
           "-contrast-stretch", "2%x2%", str(linen))
    rule_top = H // 2 - GAP - int(POINT * 0.85)
    rule_bot = H // 2 + GAP + int(POINT * 0.85)
    magick("-size", size, f"xc:{BLUE}",
           "(", str(linen), "-alpha", "set", "-channel", "A", "-evaluate", "set", "18%", "+channel", ")",
           "-compose", "overlay", "-composite",
           "(", "-size", size, "radial-gradient:#ffffff-#000000",
           "-alpha", "set", "-channel", "A", "-evaluate", "set", "12%", "+channel", ")",
           "-compose", "softlight", "-composite",
           "-fill", GOLD, "-font", font, "-pointsize", str(POINT), "-kerning", "12", "-gravity", "center",
           "-annotate", f"+0-{GAP}", WORDS[0],
           "-annotate", "+0+0", WORDS[1],
           "-annotate", f"+0+{GAP}", WORDS[2],
           "-stroke", GOLD, "-strokewidth", "3",
           "-draw", f"line {W//2-RULE},{rule_top} {W//2+RULE},{rule_top}",
           "-draw", f"line {W//2-RULE},{rule_bot} {W//2+RULE},{rule_bot}",
           "-quality", "88", str(OUT))
    linen.unlink()
    print("wrote", OUT, OUT.stat().st_size, "bytes")
    return OUT


if __name__ == "__main__":
    main()
