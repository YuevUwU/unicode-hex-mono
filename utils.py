"""
Drawing utilities for UnicodeHexMono font generation.

This module provides low-level drawing primitives for creating glyphs:
- Codepoint validation (excluding surrogates and non-characters)
- Rounded square path generation using Bézier curves
- Thick line drawing for X symbols and dividers
- Hex digit rendering using 3x5 pixel grid patterns

All drawing functions use FontForge's pen API to draw vector paths.
"""

import config

def is_valid_codepoint(cp):
    """Check if codepoint is valid and not in surrogate range."""
    if cp < config.UNICODE_MIN or cp > config.UNICODE_MAX:
        return False
    if config.SURROGATE_START <= cp <= config.SURROGATE_END:
        return False
    # Exclude non-characters: U+FFFE, U+FFFF and U+nFFFE, U+nFFFF for each plane
    # These are permanent non-characters and can cause cmap table errors
    if (cp & 0xFFFF) >= 0xFFFE:  # Check if last 4 hex digits are FFFE or FFFF
        return False
    # Exclude Arabic Presentation Forms-B non-characters (U+FDD0..U+FDEF)
    if 0xFDD0 <= cp <= 0xFDEF:
        return False
    return True


def draw_rounded_square(pen, x, y, size, radius, stroke_width=40):
    """
    Draw a rounded square frame (hollow rounded square).
    
    The frame is constructed from:
      1. An outer rounded square drawn clockwise.
      2. An inner rounded square drawn counter-clockwise.
      
    This creates a real hole in the middle using the non-zero winding rule.
    
    Args:
        pen: FontForge glyph pen
        x, y: Bottom-left corner of the outer square.
        size: Outer square width and height.
        radius: Outer corner radius.
        stroke_width: Thickness of the frame.
    
    The outer contour is clockwise and the inner contour is counter-clockwise.
    """
    
    # ------------------------------------------------------------------
    # Clamp dimensions
    # ------------------------------------------------------------------
    
    r_outer = min(radius, size / 2)
    
    # Inner square
    inner_x = x + stroke_width
    inner_y = y + stroke_width
    inner_size = size - 2 * stroke_width
    
    if inner_size <= 0:
        raise ValueError("stroke_width is too large for the square size")
    
    # Inner radius should follow the outer radius while accounting
    # for the frame thickness.
    r_inner = max(0, r_outer - stroke_width)
    r_inner = min(r_inner, inner_size / 2)
    
    K = 0.448
    
    
    # ==================================================================
    # OUTER CONTOUR
    # Clockwise
    # ==================================================================
    
    pen.moveTo((x + r_outer, y))

    # Bottom edge
    pen.lineTo((x + size - r_outer, y))
    
    # Bottom-right corner
    pen.curveTo(
        (x + size - r_outer * K, y),
        (x + size, y + r_outer * K),
        (x + size, y + r_outer)
    )
    
    # Right edge
    pen.lineTo((x + size, y + size - r_outer))
    
    # Top-right corner
    pen.curveTo(
        (x + size, y + size - r_outer * K),
        (x + size - r_outer * K, y + size),
        (x + size - r_outer, y + size)
    )
    
    # Top edge
    pen.lineTo((x + r_outer, y + size))
    
    # Top-left corner
    pen.curveTo(
        (x + r_outer * K, y + size),
        (x, y + size - r_outer * K),
        (x, y + size - r_outer)
    )
    
    # Left edge
    pen.lineTo((x, y + r_outer))
    
    # Bottom-left corner
    pen.curveTo(
        (x, y + r_outer * K),
        (x + r_outer * K, y),
        (x + r_outer, y)
    )
    
    pen.closePath()
    
    
    # ==================================================================
    # INNER CONTOUR
    # Counter-clockwise
    #
    # This contour becomes a hole.
    # ==================================================================
    
    pen.moveTo((inner_x + r_inner, inner_y))
    
    # Bottom-left corner
    pen.curveTo(
        (inner_x + r_inner * K, inner_y),
        (inner_x, inner_y + r_inner * K),
        (inner_x, inner_y + r_inner)
    )
    
    # Left edge
    pen.lineTo(
        (inner_x, inner_y + inner_size - r_inner)
    )
    
    # Top-left corner
    pen.curveTo(
        (inner_x, inner_y + inner_size - r_inner * K),
        (inner_x + r_inner * K, inner_y + inner_size),
        (inner_x + r_inner, inner_y + inner_size)
    )
    
    # Top edge
    pen.lineTo(
        (inner_x + inner_size - r_inner, inner_y + inner_size)
    )
    
    # Top-right corner
    pen.curveTo(
        (inner_x + inner_size - r_inner * K, inner_y + inner_size),
        (inner_x + inner_size, inner_y + inner_size - r_inner * K),
        (inner_x + inner_size, inner_y + inner_size - r_inner)
    )
    
    # Right edge
    pen.lineTo(
        (inner_x + inner_size, inner_y + r_inner)
    )
    
    # Bottom-right corner
    pen.curveTo(
        (inner_x + inner_size, inner_y + r_inner * K),
        (inner_x + inner_size - r_inner * K, inner_y),
        (inner_x + inner_size - r_inner, inner_y)
    )
    
    # Bottom edge
    pen.lineTo(
        (inner_x + r_inner, inner_y)
    )
    
    pen.closePath()



def draw_thick_line(pen, x1, y1, x2, y2, width):
    """
    Draw a thick line as a filled rectangle rotated along the line direction.
    
    Args:
        pen: FontForge glyph pen
        x1, y1: Starting point coordinates
        x2, y2: Ending point coordinates
        width: Line thickness
    """
    import math
    
    # Calculate angle and length
    dx = x2 - x1
    dy = y2 - y1
    angle = math.atan2(dy, dx)
    
    # Calculate perpendicular offset for line width
    offset_x = -math.sin(angle) * width / 2
    offset_y = math.cos(angle) * width / 2
    
    # Draw rectangle along the line (clockwise)
    pen.moveTo((x1 + offset_x, y1 + offset_y))
    pen.lineTo((x2 + offset_x, y2 + offset_y))
    pen.lineTo((x2 - offset_x, y2 - offset_y))
    pen.lineTo((x1 - offset_x, y1 - offset_y))
    pen.closePath()

def draw_hex_digit(pen, digit, x, y, size):
    """
    Draw a single hexadecimal digit (0-9, A-F) using a 3x5 pixel grid.
    Each digit is defined as a pattern of filled cells in a 3-column by 5-row grid.
    
    Args:
        pen: FontForge glyph pen
        digit: Hex digit character ('0'-'9', 'A'-'F')
        x, y: Bottom-left corner coordinates
        size: Height of the digit
    """
    
    # Digit dimensions - width is 60% of height for 3:5 aspect ratio
    width = size * 0.6
    
    # Define 3x5 grid patterns for each hex digit
    # Grid format: list of (col, row) tuples where col is 0-2 (left to right)
    # and row is 0-4 (bottom to top)
    digit_patterns = {
        '0': [(0,0), (1,0), (2,0), (0,1), (2,1), (0,2), (2,2), (0,3), (2,3), (0,4), (1,4), (2,4)],
        '1': [(1,0), (1,1), (1,2), (1,3), (1,4)],
        '2': [(0,0), (1,0), (2,0), (0,1), (0,2), (1,2), (2,2), (2,3), (0,4), (1,4), (2,4)],
        '3': [(0,0), (1,0), (2,0), (2,1), (0,2), (1,2), (2,2), (2,3), (0,4), (1,4), (2,4)],
        '4': [(0,4), (0,3), (0,2), (1,2), (2,0), (2,1), (2,2), (2,3), (2,4)],
        '5': [(0,0), (1,0), (2,0), (2,1), (0,2), (1,2), (2,2), (0,3), (0,4), (1,4), (2,4)],
        '6': [(0,0), (1,0), (2,0), (0,1), (2,1), (0,2), (1,2), (2,2), (0,3), (0,4), (1,4), (2,4)],
        '7': [(2,0), (2,1), (2,2), (2,3), (0,4), (1,4), (2,4)],
        '8': [(0,0), (1,0), (2,0), (0,1), (2,1), (0,2), (1,2), (2,2), (0,3), (2,3), (0,4), (1,4), (2,4)],
        '9': [(0,0), (1,0), (2,0), (2,1), (0,2), (1,2), (2,2), (0,3), (2,3), (0,4), (1,4), (2,4)],
        'A': [(0,0), (2,0), (0,1), (2,1), (0,2), (1,2), (2,2), (0,3), (2,3), (0,4), (1,4), (2,4)],
        'B': [(0,0), (1,0), (0,1), (2,1), (0,2), (1,2), (0,3), (2,3), (0,4), (1,4)],
        'C': [(0,0), (1,0), (2,0), (0,1), (0,2), (0,3), (0,4), (1,4), (2,4)],
        'D': [(0,0), (1,0), (0,1), (2,1), (0,2), (2,2), (0,3), (2,3), (0,4), (1,4)],
        'E': [(0,0), (1,0), (2,0), (0,1), (0,2), (1,2), (2,2), (0,3), (0,4), (1,4), (2,4)],
        'F': [(0,0), (0,1), (0,2), (1,2), (2,2), (0,3), (0,4), (1,4), (2,4)],
    }
    
    # Get the pattern for this digit
    digit = digit.upper()
    pattern = digit_patterns.get(digit, [])
    
    # Calculate cell dimensions for solid appearance
    cell_height = size / 5  # 5 rows
    cell_width = width / 3  # 3 columns
    
    # Helper to draw a filled rectangle
    def draw_rect(x1, y1, x2, y2):
        pen.moveTo((x1, y1))
        pen.lineTo((x2, y1))
        pen.lineTo((x2, y2))
        pen.lineTo((x1, y2))
        pen.closePath()
    
    # Draw each cell in the pattern
    for col, row in pattern:
        # Calculate cell position
        cell_x = x + col * cell_width
        cell_y = y + row * cell_height
        
        # Draw the cell
        draw_rect(cell_x, cell_y, cell_x + cell_width, cell_y + cell_height)
