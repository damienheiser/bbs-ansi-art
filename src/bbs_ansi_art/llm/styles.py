"""Predefined art styles for LLM generation.

Each StylePreset provides both human-readable descriptions and quantitative
guidance derived from analyzing real BBS-era ANSI artwork.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StylePreset:
    """A named style with description and quantitative guidance."""

    name: str
    description: str
    guidance: str
    example_prompt: str
    # Quantitative lettering guidance
    primary_chars: str = "█▄▀░▒▓"
    char_weights: str = ""
    color_palette: tuple[str, ...] = ()
    letter_height: int = 5
    shading_direction: str = "left-to-right"
    spacing: int = 1
    lettering_guidance: str = ""
    # Group affinity for corpus matching
    group_affinities: tuple[str, ...] = ()


# Registry of built-in styles
STYLES: dict[str, StylePreset] = {
    "acid": StylePreset(
        name="ACiD Style",
        description="Classic ACiD Productions aesthetic from the 1990s",
        guidance="""Use shading blocks (░▒▓█), bold vibrant colors,
high contrast, dramatic shadows. Layer shading from light to dark.
Use the full CP437 character set including box drawing characters.
Prefer cyan, magenta, and white for highlights.""",
        example_prompt="In the style of ACiD Productions circa 1994-1996",
        primary_chars="█▄▀▒▓░▐▌",
        char_weights="█:35% ▄▀:25% ▒▓:20% ░:10% ▐▌:10%",
        color_palette=(
            "bright_cyan", "bright_white", "cyan",
            "bright_magenta", "white", "bright_black",
        ),
        letter_height=6,
        shading_direction="left-to-right",
        spacing=1,
        lettering_guidance="""Letters should feel heavy and dramatic. Use ▓▒░ gradients
fading from bright to dark across each letter stroke. Vertical strokes use full blocks █,
curves and diagonals use half-blocks ▄▀. Drop shadow: 1 cell right, 1 cell down in
bright_black. Color transitions flow from bright_cyan through cyan to bright_magenta
across the word. Bold is ON for all bright colors.""",
        group_affinities=("acid", "acdu"),
    ),

    "ice": StylePreset(
        name="iCE Style",
        description="iCE Advertisements aesthetic - clean and professional",
        guidance="""Clean lines, vibrant colors, detailed shading,
professional appearance. Use smooth gradients with block characters.
Emphasize readability and visual impact. Often blue/cyan themed.""",
        example_prompt="In the style of iCE Advertisements",
        primary_chars="█▄▀▓▒░▐▌",
        char_weights="█:30% ▄▀:30% ▓▒:20% ░:10% ▐▌:10%",
        color_palette=(
            "bright_blue", "bright_cyan", "bright_white",
            "blue", "cyan", "white",
        ),
        letter_height=5,
        shading_direction="top-to-bottom",
        spacing=1,
        lettering_guidance="""Letters are clean and polished with smooth contours.
Use ▄▀ half-blocks extensively for rounded edges. Shading gradient runs top-to-bottom
within each letter: bright_white at top, through bright_blue to blue at base.
Minimal decoration outside the letterforms. Professional, readable, impactful.
Avoid clutter — let the letter shapes breathe.""",
        group_affinities=("ice",),
    ),

    "blocky": StylePreset(
        name="Blocky/Oldschool",
        description="Simple block characters, minimal shading",
        guidance="""Use primarily █ full blocks and solid colors.
Bold, simple shapes without complex shading. High contrast.
Reminiscent of early BBS art before detailed shading techniques.""",
        example_prompt="Oldschool blocky ANSI style with minimal shading",
        primary_chars="█▄▀",
        char_weights="█:60% ▄▀:30% other:10%",
        color_palette=(
            "bright_white", "bright_cyan", "bright_red",
            "bright_yellow", "white",
        ),
        letter_height=5,
        shading_direction="none",
        spacing=1,
        lettering_guidance="""Letters are built from solid █ blocks only — thick and chunky.
Curves use ▄▀ half-blocks sparingly. Single bright color per letter or cycling colors
across the word. No gradients, no shading. Maximum readability. Think toilet/figlet
but with ANSI color. Each letter stands alone clearly.""",
        group_affinities=(),
    ),

    "ascii": StylePreset(
        name="Pure ASCII",
        description="Traditional ASCII art using only printable ASCII",
        guidance="""Use only printable ASCII characters (32-126).
No extended CP437 characters. Create form through character density
and careful selection of glyphs like @#$%&*+=- etc.""",
        example_prompt="Traditional ASCII art style, no extended characters",
        primary_chars="#@$%&*=+-/\\|",
        char_weights="#:20% @:15% =:15% -:10% other:40%",
        color_palette=(
            "bright_white", "white", "bright_black",
        ),
        letter_height=5,
        shading_direction="none",
        spacing=1,
        lettering_guidance="""Letters are built from ASCII characters only — no box drawing,
no block elements. Use # and @ for dense fills, / \\ for diagonals, - and = for
horizontal strokes, | for vertical. Colors are secondary — the character shapes
define the letters. Keep it clean and legible.""",
        group_affinities=(),
    ),

    "amiga": StylePreset(
        name="Amiga Style",
        description="Amiga demoscene inspired aesthetic",
        guidance="""Colorful, playful, with smooth curves suggested by
careful block placement. Often features gradients and a more
European demoscene sensibility. Use creative Unicode if allowed.""",
        example_prompt="Amiga demoscene inspired ANSI art",
        primary_chars="█▄▀░▒▓▐▌",
        char_weights="█:25% ▄▀:35% ▓▒░:25% ▐▌:15%",
        color_palette=(
            "bright_white", "bright_yellow", "bright_green",
            "bright_cyan", "bright_magenta", "yellow",
        ),
        letter_height=6,
        shading_direction="left-to-right",
        spacing=1,
        lettering_guidance="""Letters are colorful and flowing with smooth curves achieved
through dense half-block ▄▀ usage. Color rainbow cycles across the word —
each letter a different bright color. Gentle ░▒▓ shading creates depth.
Playful and energetic. Think demoscene cracktros — vibrant, dynamic.""",
        group_affinities=("blend",),
    ),

    "dark": StylePreset(
        name="Dark/Gothic",
        description="Dark, moody, gothic aesthetic",
        guidance="""Dark background, limited bright colors. Use deep
reds, purples, and grays. Heavy use of shadow blocks (░▒).
Atmospheric and brooding. Skulls, flames, and dark imagery.""",
        example_prompt="Dark gothic ANSI art with moody atmosphere",
        primary_chars="█▓▒░▄▀",
        char_weights="▓▒░:40% █:25% ▄▀:25% other:10%",
        color_palette=(
            "red", "bright_red", "bright_black",
            "magenta", "white", "bright_magenta",
        ),
        letter_height=6,
        shading_direction="top-to-bottom",
        spacing=1,
        lettering_guidance="""Letters emerge from darkness. Heavy use of ░▒▓ shading
with letters barely brighter than the shadows around them. Primary color: red and
bright_red for the letter cores, ▓▒░ in bright_black for the surrounding darkness.
Letters can have subtle highlights in bright_red at their peaks.
Atmospheric — the text should look like it glows dimly in a dark room.""",
        group_affinities=("dark", "avenge"),
    ),

    "neon": StylePreset(
        name="Neon/Cyberpunk",
        description="Bright neon colors on dark background",
        guidance="""High contrast neon colors: bright cyan, magenta,
yellow, green on black. Cyberpunk aesthetic with tech imagery.
Glowing effects suggested by color gradients.""",
        example_prompt="Neon cyberpunk style with glowing effects",
        primary_chars="█▄▀░▒▓",
        char_weights="█:30% ▄▀:25% ░▒▓:30% other:15%",
        color_palette=(
            "bright_cyan", "bright_magenta", "bright_green",
            "bright_yellow", "cyan", "magenta",
        ),
        letter_height=5,
        shading_direction="none",
        spacing=2,
        lettering_guidance="""Letters GLOW. Core of each letter is bright_white, surrounded
by the neon color (bright_cyan or bright_magenta), then ░ in the dim version of that
color as a glow halo. Each letter alternates between bright_cyan and bright_magenta.
Black background is essential — the contrast creates the neon effect.
Clean, sharp letter shapes. Futuristic and electric.""",
        group_affinities=("fire",),
    ),

    "minimal": StylePreset(
        name="Minimalist",
        description="Clean, simple, lots of whitespace",
        guidance="""Sparse design with careful use of space.
Few colors, clean lines. Let negative space do the work.
Focus on essential shapes and forms.""",
        example_prompt="Minimalist ANSI art with clean lines",
        primary_chars="█▄▀─│",
        char_weights="█:20% ▄▀:40% ─│:20% space:20%",
        color_palette=(
            "bright_white", "white", "bright_black",
        ),
        letter_height=4,
        shading_direction="none",
        spacing=2,
        lettering_guidance="""Letters are thin and elegant. Minimal use of full blocks —
prefer ▄▀ half-blocks and thin lines. Only 1-2 colors. Generous spacing between
letters. The negative space is as important as the positive. Think modern typography
rendered in minimal ANSI. Clean, legible, understated.""",
        group_affinities=(),
    ),

    "fire": StylePreset(
        name="Fire Graphics",
        description="Modern Fire Graphics collective style - detailed and vibrant",
        guidance="""Highly detailed artwork with intricate shading. Uses the full
range of block characters with sophisticated color layering. Modern take on
classic BBS aesthetics with more complex compositions.""",
        example_prompt="In the style of Fire Graphics collective",
        primary_chars="█▄▀▓▒░▐▌",
        char_weights="█:20% ▄▀:30% ▓▒░:30% ▐▌:20%",
        color_palette=(
            "bright_white", "bright_cyan", "cyan",
            "bright_black", "white", "bright_magenta",
        ),
        letter_height=7,
        shading_direction="left-to-right",
        spacing=1,
        lettering_guidance="""Intricate and detailed lettering with layered shading.
Each stroke has multiple depth levels using ░▒▓█ progressions. Half-blocks ▄▀▐▌
create smooth curves and fine detail. Colors shift gradually across each letter.
Letters can overlap or interlock slightly for a flowing composition.
Ornamental flourishes — subtle decorative elements around letterforms.""",
        group_affinities=("fire",),
    ),
}


def get_style(name: str) -> StylePreset | None:
    """Get a style preset by name (case-insensitive)."""
    return STYLES.get(name.lower())


def list_styles() -> list[str]:
    """Get list of available style names."""
    return list(STYLES.keys())


def get_style_guidance(name: str) -> str:
    """Get the guidance text for a style, or empty string if not found."""
    style = get_style(name)
    return style.guidance if style else ""
