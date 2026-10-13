"""
Unlike OTF, Windows appears to accept TTF files containing only glyphs outside the BMP.
When converting the borderless version (the original), the glyphs are rendered as solid black squares.
It remains unclear whether the same behavior occurs with the bordered version.
In any case, this is no longer a concern, as the OTF issue has been resolved.
To make matters worse, the conversion also introduces UPM compatibility issues and reduces Bézier curve degrees.
See the notes in `put_00-FF.py` for details.
"""

import sys
import fontforge
from pathlib import Path

# Usage: & "/path/to/ffpython.exe" .\to_ttf.py  (Get-ChildItem *_renamed.otf).FullName
for src in sys.argv[1:]:
    src = Path(src)
    dst = src.with_suffix(".ttf")

    print(f"{src.name} -> {dst.name}")

    font = fontforge.open(str(src))
    font.generate(str(dst))
    font.close()