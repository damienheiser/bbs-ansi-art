#!/usr/bin/env python3
"""Generate ANSI art text via LLM with corpus-informed style.

Supports multiple providers: claude, codex, gemini, opencode, llama,
plus API providers: anthropic, openai, google.

Usage:
    # Build corpus index (one-time)
    python generate_art.py --build-corpus /path/to/16colo.rs/archive/

    # Generate with Claude (default)
    python generate_art.py "HELLO WORLD" --style acid
    python generate_art.py "BBS" --style neon --color bright_cyan

    # Use different providers
    python generate_art.py "TEST" --provider codex --model o4-mini
    python generate_art.py "TEST" --provider gemini --model gemini-2.5-pro
    python generate_art.py "TEST" --provider openai --model gpt-4o
    python generate_art.py "TEST" --provider llama --model llama3.3

    # Use specific corpus group for examples
    python generate_art.py "FIRE" --style neon --corpus-group fire
    python generate_art.py "RETRO" --style acid --corpus-group lazarus

    # Browse corpus
    python generate_art.py --list-corpus
    python generate_art.py --list-styles
    python generate_art.py --list-providers
"""

import argparse
import logging
import sys
import os
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bbs_ansi_art.llm.corpus import CorpusIndex
from bbs_ansi_art.llm.generator import AnsiTextGenerator
from bbs_ansi_art.llm.styles import STYLES
from bbs_ansi_art.llm.providers import list_providers
from bbs_ansi_art.render.terminal import TerminalRenderer

DEFAULT_CACHE = os.path.expanduser("~/.cache/bbs-ansi-art/corpus.json")

# ── Rich help formatter ──

EPILOG = textwrap.dedent("""\

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    STYLES
      acid          Classic ACiD Productions 1990s — cyan/magenta, heavy shading
      ice           iCE Advertisements — clean, professional, blue/cyan
      blocky        Simple block chars, oldschool — solid █, high contrast
      ascii         Pure ASCII art (no block chars) — #@= density shading
      amiga         Amiga demoscene — colorful rainbow, smooth curves
      dark          Gothic/moody — deep reds, shadows, atmospheric
      neon          Cyberpunk neon glow — bright on black, electric
      minimal       Clean, thin, whitespace — elegant, understated
      fire          Fire Graphics collective — intricate, layered detail

    PROVIDERS
      CLI (no API key needed — just install and authenticate the tool):
        claude        Claude Code CLI (default). Models: opus, sonnet, haiku
        codex         OpenAI Codex CLI. Models: o4-mini, o3
        gemini        Google Gemini CLI. Models: gemini-2.5-pro
        opencode      Opencode CLI
        llama         Meta Llama CLI. Models: llama3.3

      API (needs SDK + env var):
        anthropic     Anthropic API (ANTHROPIC_API_KEY). pip install anthropic
        openai        OpenAI API (OPENAI_API_KEY). pip install openai
        google        Google GenAI API (GOOGLE_API_KEY). pip install google-genai

    COLORS (for --color monochrome mode)
      bright_cyan    bright_white   bright_red     bright_green
      bright_yellow  bright_blue    bright_magenta cyan
      white          red            green          yellow
      blue           magenta        bright_black

    EXAMPLES

      # Fastest — no API call, local block font
      python generate_text.py "HELLO" --scheme acid

      # Quick — Claude with style guidance only, no corpus
      python generate_art.py "HELLO" --style acid --examples 0

      # Balanced — a few corpus examples for better quality
      python generate_art.py "BBS ART" --style neon --examples 5

      # Best — Opus with many examples (slower, highest quality)
      python generate_art.py "ANSI" --style acid --model opus --examples 15

      # Monochrome — style shapes in a single color
      python generate_art.py "MONO" --style fire --color bright_cyan

      # Custom instructions
      python generate_art.py "BBS" -i "Add a drop shadow" -i "Extra tall letters"

      # Specific corpus group
      python generate_art.py "RETRO" --corpus-group lazarus --examples 5

      # Different provider
      python generate_art.py "TEST" --provider codex --model o4-mini --examples 0

      # Save as .ans file
      python generate_art.py "SAVE ME" --style ice --save output.ans

      # Cost-capped generation
      python generate_art.py "BUDGET" --max-budget 0.50

    CORPUS SETUP
      The generator is best with real ANSI art examples from 16colo.rs:

        # Mirror the archive (wget)
        wget -r -np -nH --cut-dirs=1 -A "*.zip" -P ~/ansi-corpus \\
          https://16colo.rs/archive/

        # Build the index (~60s for full archive)
        python generate_art.py --build-corpus ~/ansi-corpus/

        # Browse what's in it
        python generate_art.py --list-corpus

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


def build_corpus(corpus_path: str, cache_path: str) -> None:
    """Build and cache the corpus index."""
    print(f"Building corpus index from: {corpus_path}")
    corpus = CorpusIndex(corpus_path)
    corpus.build(max_height=40, min_height=3)
    corpus.save_cache(cache_path)
    print(f"Indexed {len(corpus.entries)} entries")
    print(f"  Lettering pieces: {sum(1 for e in corpus.entries if e.has_lettering)}")
    print(f"  Cache saved to: {cache_path}")


def generate_text(
    text: str,
    style: str,
    width: int,
    num_examples: int,
    cache_path: str,
    save_path: str | None,
    model: str,
    max_budget: float | None,
    color: str | None = None,
    extra_instructions: list[str] | None = None,
    provider: str = "claude",
    corpus_group: str | None = None,
) -> None:
    """Generate and display ANSI art text."""
    corpus = None
    if os.path.exists(cache_path):
        corpus = CorpusIndex.load_cache(cache_path)
        print(f"Loaded corpus: {len(corpus.entries)} entries", file=sys.stderr)
    else:
        print("No corpus cache found. Generating without examples.", file=sys.stderr)
        print(f"  Build with: python {sys.argv[0]} --build-corpus /path/to/archive/", file=sys.stderr)

    gen = AnsiTextGenerator(corpus=corpus, model=model, provider=provider)

    # Build instructions list
    instructions = list(extra_instructions or [])
    if color:
        instructions.append(
            f"MONOCHROME: Use ONLY [{color}] as the color for all lettering. "
            f"You may use [bright_black] for shadows and [{color}] shading variants "
            f"(e.g. lighter/darker) but NO other hue. The block shapes, shading "
            f"technique, and character usage should still follow the {style} style."
        )

    desc = f"{style} style via {provider}"
    if color:
        desc += f", mono {color}"
    if corpus_group:
        desc += f", group={corpus_group}"
    print(f"Generating '{text}' in {desc}...", file=sys.stderr)

    result = gen.generate(
        text=text,
        style=style,
        width=width,
        num_examples=num_examples,
        max_budget_usd=max_budget,
        instructions=instructions or None,
        corpus_group=corpus_group,
    )

    # Display
    renderer = TerminalRenderer()
    print(renderer.render(result.canvas))

    # Stats
    print(file=sys.stderr)
    print(f"  Provider: {result.provider}", file=sys.stderr)
    print(f"  Model: {result.model}", file=sys.stderr)
    if result.cost_usd:
        print(f"  Cost: ${result.cost_usd:.4f}", file=sys.stderr)
    if result.duration_ms:
        print(f"  Duration: {result.duration_ms}ms", file=sys.stderr)
    print(f"  Canvas: {result.canvas.width}x{result.canvas.current_height}", file=sys.stderr)

    if save_path:
        result.document.save(save_path)
        print(f"  Saved to: {save_path}", file=sys.stderr)


def show_styles() -> None:
    """Print available styles."""
    print("Available styles:\n")
    for name, preset in STYLES.items():
        colors = ", ".join(preset.color_palette[:3]) if preset.color_palette else "(default)"
        print(f"  {name:12s}  {preset.description}")
        print(f"  {'':12s}  height={preset.letter_height} chars={preset.primary_chars} colors={colors}")
        print()


def show_corpus(cache_path: str) -> None:
    """Print corpus groups and artists."""
    if not os.path.exists(cache_path):
        print(f"No corpus cache at {cache_path}")
        print(f"Build with: python {sys.argv[0]} --build-corpus /path/to/archive/")
        return

    corpus = CorpusIndex.load_cache(cache_path)
    print(f"Corpus: {len(corpus.entries)} entries, "
          f"{sum(1 for e in corpus.entries if e.has_lettering)} lettering pieces\n")

    print("=== ART GROUPS (use with --corpus-group) ===\n")
    for group, count in corpus.list_groups()[:30]:
        lettering = sum(1 for e in corpus.entries
                        if (group.lower() in e.group.lower()) and e.has_lettering)
        print(f"  {count:4d} pieces  {lettering:3d} lettering  {group}")

    print(f"\n=== TOP ARTISTS ===\n")
    for artist, count in corpus.list_artists()[:20]:
        print(f"  {count:4d} pieces  {artist}")


def show_providers() -> None:
    """Print available providers."""
    info = {
        "claude":    ("Claude CLI",      "opus",                "claude -p (default)"),
        "codex":     ("Codex CLI",       "o4-mini",             "codex exec"),
        "gemini":    ("Gemini CLI",      "gemini-2.5-pro",      "gemini -p"),
        "opencode":  ("Opencode CLI",    "default",             "opencode -p"),
        "llama":     ("Llama CLI",       "llama3.3",            "llama run"),
        "anthropic": ("Anthropic API",   "claude-opus-4-20250514", "pip install anthropic"),
        "openai":    ("OpenAI API",      "gpt-4o",              "pip install openai"),
        "google":    ("Google GenAI API", "gemini-2.5-pro",     "pip install google-genai"),
    }
    print("Available providers:\n")
    print(f"  {'Provider':12s}  {'Name':18s}  {'Default Model':28s}  {'Requires'}")
    print(f"  {'─' * 12}  {'─' * 18}  {'─' * 28}  {'─' * 25}")
    for name in list_providers():
        desc, model, req = info.get(name, (name, "default", ""))
        print(f"  {name:12s}  {desc:18s}  {model:28s}  {req}")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="generate_art.py",
        description="Generate stylized ANSI block lettering via LLM, "
                    "informed by a corpus of real BBS-era artwork.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ── Positional ──
    parser.add_argument(
        "text", nargs="*", metavar="TEXT",
        help="Text to render as block lettering. Multi-word is joined. "
             "Example: 'HELLO WORLD'. Omit to use --list-* or --build-corpus.",
    )

    # ── Style & appearance ──
    style_group = parser.add_argument_group(
        "style & appearance",
        "Control the visual style and output dimensions.",
    )
    style_group.add_argument(
        "--style", "-s", default="acid", metavar="NAME",
        help="Art style preset. Determines color palette, character usage, "
             "shading direction, and letter height. "
             "Choices: acid, ice, blocky, ascii, amiga, dark, neon, minimal, fire. "
             "Default: acid. Use --list-styles for descriptions.",
    )
    style_group.add_argument(
        "--width", "-w", type=int, default=80, metavar="COLS",
        help="Maximum output width in terminal columns. Art is generated to "
             "fit within this width. Default: 80.",
    )
    style_group.add_argument(
        "--color", "-c", metavar="COLOR",
        help="Monochrome mode: render using only this single color for all "
             "lettering. Block shapes and shading still follow the chosen "
             "--style, but the hue is constrained. bright_black is allowed "
             "for shadows. Example: --color bright_cyan. "
             "See --help epilog for full color list.",
    )

    # ── LLM provider ──
    llm_group = parser.add_argument_group(
        "LLM provider",
        "Choose which LLM to use for generation.",
    )
    llm_group.add_argument(
        "--provider", default="claude", metavar="NAME",
        help="LLM provider to use. CLI providers (claude, codex, gemini, "
             "opencode, llama) shell out to an installed CLI tool — no API key "
             "needed. API providers (anthropic, openai, google) call the "
             "Python SDK directly and need an env var (ANTHROPIC_API_KEY, "
             "OPENAI_API_KEY, GOOGLE_API_KEY). Default: claude. "
             "Use --list-providers for details.",
    )
    llm_group.add_argument(
        "--model", default="opus", metavar="MODEL",
        help="Model name or alias passed to the provider. For Claude: opus "
             "(best quality, 1M context), sonnet (faster), haiku (fastest). "
             "For Codex: o4-mini, o3. For Gemini: gemini-2.5-pro. "
             "For OpenAI API: gpt-4o. Default: opus.",
    )
    llm_group.add_argument(
        "--max-budget", type=float, metavar="USD",
        help="Maximum cost cap in USD. Passed to the provider if supported "
             "(currently Claude CLI --max-budget-usd). The generation will "
             "abort if cost would exceed this. Example: --max-budget 0.50.",
    )
    llm_group.add_argument(
        "--instruction", "-i", action="append", dest="instructions",
        metavar="TEXT",
        help="Extra instruction passed to the LLM. Can be repeated. "
             "Appended to the generation prompt after all style/corpus "
             "guidance. Example: -i 'Add a drop shadow' -i 'Extra tall'.",
    )

    # ── Corpus ──
    corpus_group = parser.add_argument_group(
        "corpus & examples",
        "Control which real ANSI artwork examples are included in the prompt.",
    )
    corpus_group.add_argument(
        "--examples", "-n", type=int, default=15, metavar="N",
        help="Number of real ANSI artwork examples to include in the prompt. "
             "More examples = better style fidelity but slower/costlier. "
             "0 = no examples (style guidance only, fastest). "
             "3-5 = good balance. 10-15 = best quality. Default: 15.",
    )
    corpus_group.add_argument(
        "--corpus-group", metavar="GROUP",
        help="Override automatic example selection: use only artworks from "
             "this art group. Case-insensitive substring match against group "
             "name and archive path. Example: --corpus-group fire, "
             "--corpus-group lazarus, --corpus-group CiA. "
             "Use --list-corpus to see available groups.",
    )
    corpus_group.add_argument(
        "--cache", default=DEFAULT_CACHE, metavar="PATH",
        help="Path to the corpus cache JSON file. Built with --build-corpus. "
             f"Default: {DEFAULT_CACHE}",
    )

    # ── Output ──
    output_group = parser.add_argument_group(
        "output",
        "Control where and how results are saved.",
    )
    output_group.add_argument(
        "--save", metavar="FILE",
        help="Save the generated art as a .ans file with SAUCE metadata "
             "(title, author, dimensions). The art is also printed to stdout. "
             "Example: --save output.ans.",
    )

    # ── Setup commands ──
    setup_group = parser.add_argument_group(
        "setup & discovery",
        "Build the corpus or explore available options.",
    )
    setup_group.add_argument(
        "--build-corpus", metavar="PATH",
        help="Build (or rebuild) the corpus index from a directory of ZIP "
             "archives. Recursively finds all .zip files, extracts .ans files, "
             "parses them, analyzes style features, and saves a JSON cache. "
             "The 16colo.rs archive is the recommended source. "
             "Example: --build-corpus ~/ansi-corpus/",
    )
    setup_group.add_argument(
        "--list-styles", action="store_true",
        help="Print all available style presets with descriptions, character "
             "usage, color palettes, and letter heights, then exit.",
    )
    setup_group.add_argument(
        "--list-corpus", action="store_true",
        help="Print corpus statistics: total entries, lettering pieces, top "
             "art groups (with --corpus-group names), and top artists. "
             "Requires a built corpus cache.",
    )
    setup_group.add_argument(
        "--list-providers", action="store_true",
        help="Print all available LLM providers with their type (CLI/API), "
             "default model, and installation requirements, then exit.",
    )

    # ── Debug ──
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging. Shows corpus loading, example selection, "
             "provider invocation details, and CLI commands.",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    if args.list_styles:
        show_styles()
        return
    if args.list_corpus:
        show_corpus(args.cache)
        return
    if args.list_providers:
        show_providers()
        return
    if args.build_corpus:
        build_corpus(args.build_corpus, args.cache)
        return

    if not args.text:
        parser.print_help()
        return

    text = " ".join(args.text)
    generate_text(
        text=text,
        style=args.style,
        width=args.width,
        num_examples=args.examples,
        cache_path=args.cache,
        save_path=args.save,
        model=args.model,
        max_budget=args.max_budget,
        color=args.color,
        extra_instructions=args.instructions,
        provider=args.provider,
        corpus_group=args.corpus_group,
    )


if __name__ == "__main__":
    main()
