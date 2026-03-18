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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bbs_ansi_art.llm.corpus import CorpusIndex
from bbs_ansi_art.llm.generator import AnsiTextGenerator
from bbs_ansi_art.llm.styles import STYLES
from bbs_ansi_art.llm.providers import list_providers
from bbs_ansi_art.render.terminal import TerminalRenderer

DEFAULT_CACHE = os.path.expanduser("~/.cache/bbs-ansi-art/corpus.json")


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
        description="Generate ANSI art text via LLM (Claude, Codex, Gemini, and more)",
    )
    parser.add_argument("text", nargs="*", help="Text to render")
    parser.add_argument("--style", "-s", default="acid", help="Style preset (default: acid)")
    parser.add_argument("--width", "-w", type=int, default=80, help="Output width (default: 80)")
    parser.add_argument("--examples", "-n", type=int, default=15, help="Number of corpus examples")
    parser.add_argument("--save", help="Save output as .ans file")
    parser.add_argument("--provider", default="claude", help="LLM provider (default: claude)")
    parser.add_argument("--model", default="opus", help="Model alias or name (default: opus)")
    parser.add_argument("--max-budget", type=float, help="Max cost in USD")
    parser.add_argument("--color", "-c", help="Monochrome: single color (e.g. bright_cyan)")
    parser.add_argument("--instruction", "-i", action="append", dest="instructions",
                        help="Extra instruction for the LLM (repeatable)")
    parser.add_argument("--corpus-group", help="Use examples from this art group only")
    parser.add_argument("--cache", default=DEFAULT_CACHE, help="Corpus cache path")
    parser.add_argument("--build-corpus", metavar="PATH", help="Build corpus from archive directory")
    parser.add_argument("--list-styles", action="store_true", help="List style presets")
    parser.add_argument("--list-corpus", action="store_true", help="List corpus groups and artists")
    parser.add_argument("--list-providers", action="store_true", help="List LLM providers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

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
