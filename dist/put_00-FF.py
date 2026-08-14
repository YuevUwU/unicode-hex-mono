import fontforge

src = fontforge.open("UnicodeHexMono_00000_000FF.otf")
dsts = ["00100_0F35F", "0F360_1DDE1", "108400_10FFFD", "1DDE2_2C843", "2C844_3B2A5", "3B2A6_49D07", "49D08_58769", "5876A_671CB", "671CC_75C2D", "75C2E_8468F", "84690_930F1", "930F2_A1B53", "A1B54_B05B5", "B05B6_BF015", "BF016_CDA77", "CDA78_DC4D9", "DC4DA_EAF3B", "EAF3C_F999D", "F999E_1083FF"]

src.selection.none()

for cp in range(0x100):
    slot = src.findEncodingSlot(cp)
    if slot >= 0 and src[slot].glyphname != ".notdef":
        src.selection.select(("more",), cp)

src.copy()

print("Copied")

for suffix in dsts:
    print(f"Handling nicodeHexMono_{suffix}_renamed.otf")
    dst = fontforge.open(f"UnicodeHexMono_{suffix}_renamed.otf")
    output = f"UnicodeHexMono_{suffix}_renamed_with_00-FF.otf"

    dst.selection.none()

    for cp in range(0x100):
        slot = src.findEncodingSlot(cp)
        if slot >= 0 and src[slot].glyphname != ".notdef":
            dst.createChar(cp, src[slot].glyphname)
            dst.selection.select(("more",), cp)

    dst.paste()
    dst.generate(output)
    print(f"Generated to {output}")
