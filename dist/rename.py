from fontTools.ttLib import TTFont
from pathlib import Path
import re

FONT_DIR = Path(".")

def set_name(font, name_id, value):
    name_table = font["name"]

    # 刪除現有的所有 name record
    name_table.names = [
        n for n in name_table.names
        if n.nameID != name_id
    ]

    # Windows Unicode
    name_table.setName(
        value,
        name_id,
        3,      # platformID
        1,      # platEncID
        0x409   # English (US)
    )

    # Macintosh
    name_table.setName(
        value,
        name_id,
        1,      # platformID
        0,      # platEncID
        0       # English
    )


def process(path):
    m = re.search(
        r"UnicodeHexMono_([0-9A-F]+)_([0-9A-F]+)\.otf$",
        path.name,
        re.IGNORECASE
    )

    if not m:
        return

    start = m.group(1).upper()
    end = m.group(2).upper()

    base = "UnicodeHexMono"
    psname = f"{base}-{start}-{end}"
    family = psname
    subfamily = "Regular"
    fullname = f"{base} {start}-{end}"

    font = TTFont(path)

    # name 1 = Family
    set_name(font, 1, family)

    # name 2 = Subfamily
    set_name(font, 2, subfamily)

    # name 4 = Full name
    set_name(font, 4, fullname)

    # name 6 = PostScript name
    set_name(font, 6, psname)

    # name 16 = Typographic / Preferred Family
    set_name(font, 16, family)

    # name 17 = Typographic / Preferred Subfamily
    set_name(font, 17, subfamily)

    # name 18 = Compatible Full
    set_name(font, 18, fullname)

    output = path.with_name(
        path.stem + "_renamed.otf"
    )

    font.save(output)

    print(f"{path.name} -> {output.name}")
    print(f"  Family:    {family}")
    print(f"  Subfamily: {subfamily}")
    print(f"  Fullname:  {fullname}")
    print(f"  PS Name:   {psname}")
    print()


for path in sorted(FONT_DIR.glob("UnicodeHexMono_*.otf")):
    process(path)
