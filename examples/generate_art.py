#!/usr/bin/env python3
"""Generate ANSI art text via Claude API with corpus-informed style.

Usage:
    # First time: build corpus index
    python examples/generate_art.py --build-corpus /path/to/16colo.rs/archive/

    # Generate text
    python examples/generate_art.py "HELLO WORLD" --style acid
    python examples/generate_art.py "BBS" --style neon --examples 20
    python examples/generate_art.py "COOL" --style fire --width 60

    # Save output
    python examples/generate_art.py "TEST" --style ice --save output.ans

    # List styles
    python examples/generate_art.py --list-styles
"""

import argparse
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bbs_ansi_art.llm.corpus import CorpusIndex
from bbs_ansi_art.llm.generator import AnsiTextGenerator
from bbs_ansi_art.llm.styles import STYLES
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


async def generate_text(
    text: str,
    style: str,
    width: int,
    num_examples: int,
    cache_path: str,
    save_path: str | None,
    model: str,
    temperature: float,
) -> None:
    """Generate and display ANSI art text."""
    # Load corpus if available
    corpus = None
    if os.path.exists(cache_path):
        corpus = CorpusIndex.load_cache(cache_path)
        print(f"Loaded corpus: {len(corpus.entries)} entries", file=sys.stderr)
    else:
        print("No corpus cache found. Generating without examples.", file=sys.stderr)
        print(f"  Build with: python {sys.argv[0]} --build-corpus /path/to/archive/", file=sys.stderr)

    gen = AnsiTextGenerator(corpus=corpus, model=model)

    print(f"Generating '{text}' in {style} style...", file=sys.stderr)
    result = await gen.generate(
        text=text,
        style=style,
        width=width,
        num_examples=num_examples,
        temperature=temperature,
    )

    # Display
    renderer = TerminalRenderer()
    print(renderer.render(result.canvas))

    # Stats
    print(file=sys.stderr)
    print(
        f"  Tokens: {result.prompt_tokens:,} in / {result.output_tokens:,} out",
        file=sys.stderr,
    )
    print(f"  Canvas: {result.canvas.width}x{result.canvas.current_height}", file=sys.stderr)

    # Save
    if save_path:
        result.document.save(save_path)
        print(f"  Saved to: {save_path}", file=sys.stderr)


def list_styles() -> None:
    """Print available styles."""
    print("Available styles:\n")
    for name, preset in STYLES.items():
        colors = ", ".join(preset.color_palette[:3]) if preset.color_palette else "(default)"
        print(f"  {name:12s}  {preset.description}")
        print(f"  {'':12s}  height={preset.letter_height} chars={preset.primary_chars} colors={colors}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Generate ANSI art text via Claude API")
    parser.add_argument("text", nargs="*", help="Text to render")
    parser.add_argument("--style", "-s", default="acid", help="Style preset (default: acid)")
    parser.add_argument("--width", "-w", type=int, default=80, help="Output width (default: 80)")
    parser.add_argument("--examples", "-n", type=int, default=15, help="Number of corpus examples")
    parser.add_argument("--save", help="Save output as .ans file")
    parser.add_argument("--model", default="claude-opus-4-20250514", help="Claude model to use")
    parser.add_argument("--temperature", "-t", type=float, default=0.7, help="Temperature")
    parser.add_argument("--cache", default=DEFAULT_CACHE, help="Corpus cache path")
    parser.add_argument("--build-corpus", metavar="PATH", help="Build corpus from archive directory")
    parser.add_argument("--list-styles", action="store_true", help="List available styles")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    if args.list_styles:
        list_styles()
        return

    if args.build_corpus:
        build_corpus(args.build_corpus, args.cache)
        return

    if not args.text:
        parser.print_help()
        return

    text = " ".join(args.text)
    asyncio.run(generate_text(
        text=text,
        style=args.style,
        width=args.width,
        num_examples=args.examples,
        cache_path=args.cache,
        save_path=args.save,
        model=args.model,
        temperature=args.temperature,
    ))


if __name__ == "__main__":
    main()
