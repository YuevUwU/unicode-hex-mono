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