"""
Font generation engine for UnicodeHexMono.

This module orchestrates the multi-file font generation process:
- Collects valid Unicode codepoints
- Separates ASCII (U+0000-U+00FF) into dedicated file for performance
- Splits whole unicode codepoints into chunks (32768 glyphs per file)
- Creates FontForge font objects with proper metadata
- Generates individual glyphs for each codepoint
- Validates and exports OTF font files

The multi-file approach is necessary because OpenType fonts have a hard limit
of 65,535 glyphs per file, while Unicode has over 1 million codepoints.
"""

from collections.abc import Iterable
from functools import cache
from math import ceil
import os
from pathlib import Path

import fontforge
import config
import utils
import glyphs

# ============================================================================
# Font Object Creation
# ============================================================================

def create_font_object():
    """Create and configure a new FontForge font object with proper metadata."""
    font = fontforge.font()
    
    # Set font metadata
    font.fontname = config.FONT_NAME
    font.familyname = config.FONT_FAMILY
    font.fullname = config.FONT_FULLNAME
    font.version = config.FONT_VERSION
    font.copyright = config.FONT_COPYRIGHT
    font.weight = config.FONT_STYLE
    
    # Set encoding to UnicodeFull
    font.encoding = "UnicodeFull"
    
    # Set font metrics
    font.em = config.EM_SIZE
    font.ascent = config.ASCENT
    font.descent = config.DESCENT
    
    # Set OS/2 table properties (required for proper font rendering)
    font.os2_vendor = "PFNT"  # 4-character vendor ID
    font.os2_version = 4
    font.os2_winascent = config.ASCENT
    font.os2_windescent = config.DESCENT
    font.os2_typoascent = config.ASCENT
    font.os2_typodescent = -config.DESCENT
    font.os2_typolinegap = 0
    font.os2_panose = (2, 11, 6, 9, 3, 0, 0, 2, 0, 4)  # Monospaced
    
    # Set PostScript name (required for macOS)
    font.appendSFNTName('English (US)', 'PostScriptName', config.FONT_NAME)
    font.appendSFNTName('English (US)', 'Family', config.FONT_FAMILY)
    font.appendSFNTName('English (US)', 'Fullname', config.FONT_FULLNAME)
    font.appendSFNTName('English (US)', 'Preferred Family', config.FONT_FAMILY)
    font.appendSFNTName('English (US)', 'Compatible Full', config.FONT_FULLNAME)
    
    return font


# ============================================================================
# Multi-File Font Generation
# ============================================================================

def generate_multi_file(
    wanted_range: Iterable[int] | None = None,
    dry_run: bool = False,
    generate_ascii: bool = True,
    generate_woff: bool = False,
):
    """Generate multiple font files to cover the full Unicode range.
    
    Strategy:
    - File 1 (Optional): ASCII & Extended ASCII (U+0000-U+00FF) - 256 glyphs
    - Files 2+: Whole codepoints in 32,768-glyph chunks with ASCII
    """
    
    print("\nMode: Multi-file generation")
    print(f"Glyphs per file (non-ASCII): {config.GLYPHS_PER_FILE}")
    print(f"Unicode range: U+{config.UNICODE_MIN:05X} - U+{config.UNICODE_MAX:05X}")
    
    # Ensure dist directory exists
    os.makedirs('dist', exist_ok=True)
    
    # Collect all valid codepoints
    print("\nCollecting valid codepoints...")
    all_codepoints: list[int | None] = []
    total_valid_codepoints = 0
    
    if wanted_range is None:
        wanted_range = range(config.UNICODE_MIN, config.UNICODE_MAX + 1)
    for cp in wanted_range:
        if utils.is_valid_codepoint(cp):
            all_codepoints.append(cp)
            total_valid_codepoints += 1
        else:
            all_codepoints.append(None)

    print(f"Total valid codepoints: {total_valid_codepoints:,}")
    ascii_codepoints = list(get_ascii_codepoints())
    print(f"\nASCII & Extended ASCII (U+0000-U+00FF, for compatibility): {len(ascii_codepoints):,} glyphs")
    print(f"Whole codepoints: {len(all_codepoints):,} glyphs")
    
    # Calculate total number of files
    num_whole_files = ceil(
        len(all_codepoints) / config.GLYPHS_PER_FILE
    )
    total_files = num_whole_files  # 1 ASCII file + whole unicode files
    if generate_woff:
        total_files *= 2
    if generate_ascii:
        total_files += 1
        if generate_woff:
            total_files += 1
    
    print(f"\nWill generate {total_files} font files:")
    if generate_ascii:
        print(f"  - 1 ASCII file (U+0000-U+00FF)")
    print(f"  - {num_whole_files} files for whole Unicode")
    
    font_files = []
    
    # ========================================================================
    # STEP 1: Generate ASCII & Extended ASCII file (U+0000-U+00FF)
    # ========================================================================
    if generate_ascii:
        print(f"\n{'=' * 70}")
        print(f"File {len(font_files)+1}/{total_files}: ASCII & Extended ASCII")
        generated_files = generate_ascii_subset(dry_run=dry_run, generate_woff=generate_woff)
        font_files += generated_files
    
    # ========================================================================
    # STEP 2: Generate whole unicode files in 32768 chunks
    # ========================================================================
    for file_idx in range(num_whole_files):
        start_idx = file_idx * config.GLYPHS_PER_FILE
        end_idx = min(start_idx + config.GLYPHS_PER_FILE, len(all_codepoints))
        chunk = [cp for cp in all_codepoints[start_idx:end_idx] if cp is not None]
        
        if not chunk:
            continue
        
        min_cp = chunk[0]
        max_cp = chunk[-1]

        total_glyphs = set(chunk+ascii_codepoints)
        
        print(f"\n{'=' * 70}")
        print(f"File {len(font_files)+1}/{total_files}: U+{min_cp:05X} - U+{max_cp:05X}")
        print(f"Glyphs in this file: {len(total_glyphs):,}")
        print(f"{'=' * 70}")

        generated_files = generate_with_range(total_glyphs, cp_min_max=(min_cp, max_cp), dry_run=dry_run, generate_woff=generate_woff)
        font_files += generated_files
        
    
    # Summary
    print("\n" + "=" * 70)
    print("SUCCESS!")
    print(f"Generated {len(font_files)} font files:")
    for f in font_files:
        print(f"  - {f}")
    print(f"Total codepoints covered: {total_valid_codepoints:,}")
    print(f"Formats: OTF (OpenType){" + WOFF2 (Web optimized)" if generate_woff else ""}")
    print("=" * 70)


def generate_with_range(
    codepoints: Iterable[int],
    *,
    path_stem: str | Path | None = None,
    cp_min_max: tuple[int, int] | None = None,
    dry_run: bool = False,
    generate_woff: bool = False
) -> list[str]:
    match (path_stem, cp_min_max):
        case (None, None):  # Leave it undefined for now
            raise ValueError("One of path_stem and cp_min_max should be provided")
        case (path_stem, None):
            output_stem = Path(path_stem)
        case (None, cp_min_max):
            min_cp, max_cp = cp_min_max
            output_stem = Path(f"dist/UnicodeHexMono_{min_cp:05X}_{max_cp:05X}")
        case _:
            raise ValueError("Do not provide both path_stem and cp_min_max")
    
    # Ensure dist directory exists
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    
    font_files = []
    
    # Create font
    font = create_font_object()
    
    # Generate glyphs for this chunk
    print("Generating glyphs...")
    for _, cp in enumerate(codepoints):
        glyphs.create_glyph(font, cp)
        # if (i + 1) % 1000 == 0:
        #     print(f"  {i + 1:,} / {len(chunk)+len(ascii_codepoints):,} glyphs generated...")
    
    # Add .notdef glyph
    print("Creating .notdef glyph...")
    glyphs.create_notdef_glyph(font)
    
    # Validate glyphs
    print("Validating glyphs...")
    glyphs.validate_font_glyphs(font)
    
    # Generate OTF filename
    output_path_otf = output_stem.with_suffix(".otf").as_posix()
    print(f"\nGenerating {output_path_otf}...")
    
    # Generate OTF with proper flags
    if not dry_run:
        font.generate(output_path_otf, flags=('opentype', 'omit-instructions', 'dummy-dsig'))  # Performance Bottleneck
    font_files.append(output_path_otf)
    
    print(f"✓ Generated: {output_path_otf}")
    print(f"  Total glyphs in file: {sum(1 for _ in font.glyphs())}")
    
    # Generate WOFF2 using fonttools
    if generate_woff:
        output_path_woff2 = output_stem.with_suffix(".woff2").as_posix()
        print(f"\nGenerating {output_path_woff2}...")
        print("  Converting OTF to WOFF2 using fonttools...")
        try:
            if not dry_run:
                from fontTools.ttLib import TTFont
                otf_font = TTFont(output_path_otf)
                otf_font.flavor = 'woff2'
                otf_font.save(output_path_woff2)
            font_files.append(output_path_woff2)
            print(f"✓ Generated: {output_path_woff2}")
            print(f"  Format: WOFF2 (optimized for web)")
        except ImportError:
            print("⚠ fonttools not installed - skipping WOFF2 generation")
            print("  Install with: pip3 install --break-system-packages fonttools brotli")
    
    font.close()

    return font_files


@cache
def get_ascii_codepoints():
    ascii_range_end = 0x00FF
    return tuple(filter(lambda cp: utils.is_valid_codepoint(cp), range(ascii_range_end+1)))


def generate_ascii_subset(dry_run: bool = False, generate_woff: bool = False) -> list[str]:
    # Separate ASCII range (U+0000-U+00FF) from the rest
    ascii_codepoints = get_ascii_codepoints()
    
    print(f"\nASCII & Extended ASCII (U+0000-U+00FF): {len(ascii_codepoints):,} glyphs")
    print(f"U+{ascii_codepoints[0]:05X} - U+{ascii_codepoints[-1]:05X}")
    print(f"Glyphs in this file: {len(ascii_codepoints):,}")
    print(f"{'=' * 70}")

    min_cp = ascii_codepoints[0]
    max_cp = ascii_codepoints[-1]
    generated_files = generate_with_range(ascii_codepoints, cp_min_max=(min_cp, max_cp), dry_run=dry_run, generate_woff=generate_woff)
    return generated_files
