#!/usr/bin/env python3
"""Generate ANSI art text using bbs-ansi-art library.

Block-letter font definitions rendered with CP437 shading characters
and the ArtBuilder fluent API.
"""

import sys
import os

if sys.version_info < (3, 10):
    print(
        f"Error: Python 3.10+ required (you have {sys.version_info.major}.{sys.version_info.minor}).\n"
        f"\n"
        f"Try: /opt/homebrew/bin/python3 {os.path.basename(__file__)} --help",
        file=sys.stderr,
    )
    sys.exit(1)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bbs_ansi_art.create.builder import ArtBuilder
from bbs_ansi_art.render.terminal import TerminalRenderer

# ── Block letter font (5 wide x 6 tall) using CP437 block characters ──
# Characters: █ (full), ▀ (upper half), ▄ (lower half), ░ (light), ▓ (dark)

FONT = {
    'A': [
        " ▄██▄ ",
        "██  ██",
        "██▄▄██",
        "██  ██",
        "██  ██",
    ],
    'B': [
        "███▄  ",
        "██  █ ",
        "████▄ ",
        "██  ██",
        "████▀ ",
    ],
    'C': [
        " ▄███▄",
        "██    ",
        "██    ",
        "██    ",
        " ▀███▀",
    ],
    'D': [
        "███▄  ",
        "██ ▀█ ",
        "██  ██",
        "██ ▄█ ",
        "███▀  ",
    ],
    'E': [
        "██████",
        "██    ",
        "████  ",
        "██    ",
        "██████",
    ],
    'F': [
        "██████",
        "██    ",
        "████  ",
        "██    ",
        "██    ",
    ],
    'G': [
        " ▄███▄",
        "██    ",
        "██ ▄██",
        "██  ██",
        " ▀███▀",
    ],
    'H': [
        "██  ██",
        "██  ██",
        "██████",
        "██  ██",
        "██  ██",
    ],
    'I': [
        "██████",
        "  ██  ",
        "  ██  ",
        "  ██  ",
        "██████",
    ],
    'J': [
        "  ████",
        "    ██",
        "    ██",
        "█▄  ██",
        " ▀██▀ ",
    ],
    'K': [
        "██ ▄█▀",
        "██▀▀  ",
        "███▄  ",
        "██ ▀█▄",
        "██  ▀█",
    ],
    'L': [
        "██    ",
        "██    ",
        "██    ",
        "██    ",
        "██████",
    ],
    'M': [
        "█▄  ▄█",
        "███▄██",
        "██▀█▀█",
        "██ ▀ █",
        "██   █",
    ],
    'N': [
        "██  ██",
        "███ ██",
        "█▀█▄██",
        "██ ███",
        "██  ██",
    ],
    'O': [
        " ▄██▄ ",
        "██  ██",
        "██  ██",
        "██  ██",
        " ▀██▀ ",
    ],
    'P': [
        "████▄ ",
        "██  ██",
        "████▀ ",
        "██    ",
        "██    ",
    ],
    'Q': [
        " ▄██▄ ",
        "██  ██",
        "██  ██",
        "██ ▄██",
        " ▀██▄▀",
    ],
    'R': [
        "████▄ ",
        "██  ██",
        "████▀ ",
        "██ ▀█▄",
        "██  ▀█",
    ],
    'S': [
        " ▄███▄",
        "██    ",
        " ▀██▄ ",
        "    ██",
        "▀███▀ ",
    ],
    'T': [
        "██████",
        "  ██  ",
        "  ██  ",
        "  ██  ",
        "  ██  ",
    ],
    'U': [
        "██  ██",
        "██  ██",
        "██  ██",
        "██  ██",
        " ▀██▀ ",
    ],
    'V': [
        "██  ██",
        "██  ██",
        "██  ██",
        " █▄▄█ ",
        "  ██  ",
    ],
    'W': [
        "█   ██",
        "█ ▄ ██",
        "██▀█▀█",
        "███▀██",
        "█▀  ▀█",
    ],
    'X': [
        "██  ██",
        " █▄▄█ ",
        "  ██  ",
        " █▀▀█ ",
        "██  ██",
    ],
    'Y': [
        "██  ██",
        " █▄▄█ ",
        "  ██  ",
        "  ██  ",
        "  ██  ",
    ],
    'Z': [
        "██████",
        "   ██ ",
        "  ██  ",
        " ██   ",
        "██████",
    ],
    ' ': [
        "   ",
        "   ",
        "   ",
        "   ",
        "   ",
    ],
    '!': [
        " ██",
        " ██",
        " ██",
        "   ",
        " ██",
    ],
    '.': [
        "  ",
        "  ",
        "  ",
        "  ",
        "██",
    ],
    '-': [
        "      ",
        "      ",
        "██████",
        "      ",
        "      ",
    ],
    '0': [
        " ▄██▄ ",
        "██ ▄██",
        "██▀▄██",
        "██▀ ██",
        " ▀██▀ ",
    ],
    '1': [
        " ▄██  ",
        "  ██  ",
        "  ██  ",
        "  ██  ",
        "██████",
    ],
    '2': [
        "▄███▄ ",
        "    ██",
        " ▄██▀ ",
        "██    ",
        "██████",
    ],
    '3': [
        "▄███▄ ",
        "    ██",
        " ▀██▄ ",
        "    ██",
        "▀███▀ ",
    ],
    '4': [
        "██  ██",
        "██  ██",
        "▀█████",
        "    ██",
        "    ██",
    ],
    '5': [
        "██████",
        "██    ",
        "████▄ ",
        "    ██",
        "████▀ ",
    ],
    '6': [
        " ▄███ ",
        "██    ",
        "████▄ ",
        "██  ██",
        " ▀██▀ ",
    ],
    '7': [
        "██████",
        "   ██ ",
        "  ██  ",
        " ██   ",
        " ██   ",
    ],
    '8': [
        " ▄██▄ ",
        "██  ██",
        " ▀██▄ ",
        "██  ██",
        " ▀██▀ ",
    ],
    '9': [
        " ▄██▄ ",
        "██  ██",
        " ▀████",
        "    ██",
        " ███▀ ",
    ],
}

# ── Color schemes ──

SCHEMES = {
    'acid': {
        'colors': [36, 96, 35, 95, 34, 94],  # Cyan/magenta cycle
        'mode': 'per_letter',
    },
    'ice': {
        'colors': [94, 36, 96, 34],  # Blue/cyan cool tones
        'mode': 'per_letter',
    },
    'fire': {
        'colors': [31, 91, 33, 93],  # Red/yellow warm tones
        'mode': 'per_row',
    },
    'neon': {
        'colors': [92, 96, 95, 93],  # Bright green/cyan/magenta/yellow
        'mode': 'per_letter',
    },
    'chrome': {
        'colors': [37, 97, 90, 97, 37],  # White/gray metallic
        'mode': 'per_row',
    },
    'mono': {
        'colors': [97],  # Bright white
        'mode': 'per_letter',
    },
}


def render_text(message: str, scheme_name: str = 'acid', width: int = 80) -> str:
    """Render a message as large ANSI art block text.

    Args:
        message: Text to render (uppercase letters, digits, space, !, ., -)
        scheme_name: Color scheme name from SCHEMES
        width: Canvas width

    Returns:
        ANSI-escaped string ready for terminal display.
    """
    message = message.upper()
    scheme = SCHEMES.get(scheme_name, SCHEMES['acid'])
    colors = scheme['colors']
    color_mode = scheme['mode']

    # Calculate total width needed
    letter_widths = []
    for ch in message:
        glyph = FONT.get(ch)
        if glyph:
            letter_widths.append(len(glyph[0]))
        else:
            letter_widths.append(3)  # fallback space

    total_width = sum(letter_widths) + len(message) - 1  # 1-char gap between letters
    canvas_width = max(width, total_width + 2)

    builder = ArtBuilder(canvas_width)
    num_rows = 5  # font height

    for row in range(num_rows):
        x = 1  # left margin
        for i, ch in enumerate(message):
            glyph = FONT.get(ch)
            if glyph is None:
                glyph = FONT[' ']

            line = glyph[row]

            # Pick color based on mode
            if color_mode == 'per_letter':
                fg_color = colors[i % len(colors)]
            elif color_mode == 'per_row':
                fg_color = colors[row % len(colors)]
            else:
                fg_color = colors[0]

            builder.move_to(x, row).fg(fg_color).bold().text(line)
            x += len(line) + 1  # 1 char gap

    canvas = builder.build()
    renderer = TerminalRenderer()
    return renderer.render(canvas)


def render_text_with_shadow(
    message: str,
    scheme_name: str = 'acid',
    width: int = 80,
) -> str:
    """Render block text with a dark shadow effect."""
    message = message.upper()
    scheme = SCHEMES.get(scheme_name, SCHEMES['acid'])
    colors = scheme['colors']
    color_mode = scheme['mode']

    letter_widths = []
    for ch in message:
        glyph = FONT.get(ch)
        if glyph:
            letter_widths.append(len(glyph[0]))
        else:
            letter_widths.append(3)

    total_width = sum(letter_widths) + len(message) - 1
    canvas_width = max(width, total_width + 4)
    builder = ArtBuilder(canvas_width)
    num_rows = 5

    # Shadow pass (offset +1, +1)
    for row in range(num_rows):
        x = 2  # shadow offset
        for i, ch in enumerate(message):
            glyph = FONT.get(ch, FONT[' '])
            line = glyph[row]
            shadow_line = ''
            for c in line:
                shadow_line += '░' if c != ' ' else ' '
            builder.move_to(x, row + 1).fg(90).bold(False).text(shadow_line)
            x += len(line) + 1

    # Foreground pass
    for row in range(num_rows):
        x = 1
        for i, ch in enumerate(message):
            glyph = FONT.get(ch, FONT[' '])
            line = glyph[row]

            if color_mode == 'per_letter':
                fg_color = colors[i % len(colors)]
            elif color_mode == 'per_row':
                fg_color = colors[row % len(colors)]
            else:
                fg_color = colors[0]

            builder.move_to(x, row).fg(fg_color).bold().text(line)
            x += len(line) + 1

    canvas = builder.build()
    renderer = TerminalRenderer()
    return renderer.render(canvas)


def demo():
    """Show off various text styles."""
    print()
    print(render_text("HELLO", 'acid'))
    print()
    print(render_text_with_shadow("ANSI ART", 'fire'))
    print()
    print(render_text("BBS", 'neon'))
    print()
    print(render_text("1994", 'chrome'))
    print()
    print(render_text_with_shadow("COOL!", 'ice'))
    print()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
        scheme = 'acid'
        # Check for --scheme flag
        if '--scheme' in sys.argv:
            idx = sys.argv.index('--scheme')
            if idx + 1 < len(sys.argv):
                scheme = sys.argv[idx + 1]
                # Remove scheme args from text
                args = [a for a in sys.argv[1:] if a not in ('--scheme', scheme)]
                text = ' '.join(args)
        if '--shadow' in sys.argv:
            text = text.replace('--shadow', '').strip()
            print(render_text_with_shadow(text, scheme))
        else:
            print(render_text(text, scheme))
    else:
        demo()
