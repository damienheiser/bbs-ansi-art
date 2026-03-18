# bbs-ansi-art

Python library for ANSI art — create, view, convert, and repair BBS-era artwork.

## Features

- **Load & Parse**: Read `.ans`, `.asc`, `.diz` files with CP437 encoding
- **SAUCE Metadata**: Full support for reading and writing SAUCE records
- **Render**: Output to terminal, HTML, plain text, or images (PNG)
- **Create**: Programmatic ANSI art creation with fluent builder API
- **Studio**: Interactive terminal studio with file browser
- **LLM Integration**: Style presets and ArtSpec for AI-generated art

## Installation

```bash
uv pip install bbs-ansi-art
```

With optional dependencies:
```bash
uv pip install bbs-ansi-art[cli]    # Studio and CLI tools
uv pip install bbs-ansi-art[image]  # PNG rendering (requires Pillow)
uv pip install bbs-ansi-art[llm]    # LLM generation support
uv pip install bbs-ansi-art[all]    # Everything
```

## Quick Start

```python
import bbs_ansi_art as ansi

# Load and display ANSI art
doc = ansi.load("artwork.ans")
print(doc.render())

# Check SAUCE metadata
if doc.sauce:
    print(f"Title: {doc.sauce.title}")
    print(f"Author: {doc.sauce.author}")

# Create new ANSI art programmatically
art = (ansi.create(80)
    .fg(36).bold().text("Hello, BBS World!")
    .newline()
    .reset().text("Welcome back to 1994.")
    .build())
```

## Studio

Launch the interactive ANSI art studio:
```bash
bbs-ansi-art studio ~/Downloads/
bbs-ansi-art view artwork.ans -i
```

## LLM Art Generation

Generate stylized ANSI block lettering using Claude — informed by thousands of
real BBS-era artworks from the [16colo.rs](https://16colo.rs) archive.

### Prerequisites

1. **Claude CLI** — install and authenticate:
   ```bash
   # Install Claude Code (the CLI)
   npm install -g @anthropic-ai/claude-code

   # Authenticate (opens browser)
   claude
   ```

2. **Python 3.10+** with this library:
   ```bash
   pip install bbs-ansi-art
   # or from source:
   git clone https://github.com/bkrabach/bbs-ansi-art && cd bbs-ansi-art
   ```

### Step 1: Build a Corpus (optional but recommended)

The generator produces far better results when it has real ANSI artwork examples
to learn from. The [16colo.rs](https://16colo.rs) archive is the gold standard.

**Mirror the archive:**
```bash
# Create a directory for the corpus
mkdir -p ~/ansi-corpus

# Use wget to mirror the archive ZIPs from 16colo.rs
# (each year directory contains pack .zip files with .ans artwork inside)
wget -r -np -nH --cut-dirs=1 -A "*.zip" \
  -P ~/ansi-corpus \
  https://16colo.rs/archive/

# Or use curl + a year range for a smaller download:
for year in 1994 1995 1996 1997 1998 1999 2000 2025; do
  mkdir -p ~/ansi-corpus/$year
  curl -s "https://16colo.rs/year/$year/" | \
    grep -oP 'href="[^"]*\.zip"' | \
    sed 's/href="//;s/"//' | \
    while read url; do
      curl -sO --output-dir ~/ansi-corpus/$year "https://16colo.rs$url"
    done
done
```

**Or use an existing local copy** if you already have 16colo.rs archives.

**Build the corpus index:**
```bash
# This scans all ZIPs, extracts .ans files, parses them, and builds a
# searchable index with style analysis and lettering detection.
# Takes ~60 seconds for the full 16colo.rs archive (~370 ZIP packs).

python examples/generate_art.py --build-corpus ~/ansi-corpus/

# Index is cached to ~/.cache/bbs-ansi-art/corpus.json for instant reuse.
# Typical result: ~3,800 entries, ~390 detected as lettering/logos.
```

### Step 2: Generate Art

All commands assume you're in the project root. Set `PYTHONPATH` once:
```bash
cd ~/github/bbs-ansi-art    # or wherever you cloned it
export PYTHONPATH=src        # needed when running from source
```

**Quick start — no corpus, instant:**
```bash
# Fastest: local block font, no API call at all
python3 examples/generate_text.py "HELLO WORLD"
python3 examples/generate_text.py "BBS" --scheme neon --shadow
python3 examples/generate_text.py "COOL" --scheme fire
```

**Generate with Claude (no corpus):**
```bash
# Fast — style guidance only, no corpus examples
python3 examples/generate_art.py "HELLO WORLD" --style acid --model sonnet --examples 0

# Try different styles
python3 examples/generate_art.py "BBS" --style neon --examples 0
python3 examples/generate_art.py "RETRO" --style ice --examples 0
python3 examples/generate_art.py "DARK" --style dark --examples 0
```

**Generate with corpus examples (better quality):**
```bash
# Good balance of speed and quality (3-5 examples)
python3 examples/generate_art.py "HELLO" --style acid --model sonnet --examples 3

# Best quality — more examples, Opus model (slower, 1M context)
python3 examples/generate_art.py "HELLO" --style acid --model opus --examples 10

# Save output as a .ans file
python3 examples/generate_art.py "BBS ART" --style neon --save output.ans

# Set a cost cap
python3 examples/generate_art.py "TEST" --style fire --max-budget 0.50
```

**List styles and get help:**
```bash
python3 examples/generate_art.py --list-styles
python3 examples/generate_art.py --help
```

**Tuning tips:**
| Flag | Effect |
|------|--------|
| `--examples 0` | Fastest — style guidance only, no corpus |
| `--examples 3-5` | Good balance of speed and quality |
| `--examples 10-15` | Best quality, needs patience |
| `--model sonnet` | Faster generation |
| `--model opus` | Better art quality, 1M context window |
| `--max-budget 0.50` | Cost cap in USD |
| `--width 60` | Narrower output (default: 80) |
| `--save file.ans` | Save as .ans file with SAUCE metadata |

### Available Styles

| Style | Description | Colors | Height |
|-------|-------------|--------|--------|
| `acid` | Classic ACiD Productions 1990s | cyan, magenta, white | 6 rows |
| `ice` | iCE Advertisements - clean, professional | blue, cyan, white | 5 rows |
| `blocky` | Simple block characters, oldschool | bright colors, high contrast | 5 rows |
| `ascii` | Pure ASCII art (no block chars) | white, gray | 5 rows |
| `amiga` | Amiga demoscene, colorful | rainbow cycling | 6 rows |
| `dark` | Gothic, moody | red, magenta, dark | 6 rows |
| `neon` | Cyberpunk neon glow | cyan, magenta, green | 5 rows |
| `minimal` | Clean, thin, lots of whitespace | white, gray | 4 rows |
| `fire` | Fire Graphics collective - detailed | cyan, white, layered | 7 rows |

### Python API

```python
from bbs_ansi_art.llm import CorpusIndex, AnsiTextGenerator

# Without corpus
gen = AnsiTextGenerator(model="sonnet")
result = gen.generate("TEST", style="neon")
print(result.document.render())

# With corpus (better results)
corpus = CorpusIndex.load_cache("~/.cache/bbs-ansi-art/corpus.json")
gen = AnsiTextGenerator(corpus=corpus, model="opus")
result = gen.generate("HELLO", style="acid", width=80, num_examples=10)

print(result.document.render())     # Display in terminal
result.document.save("hello.ans")   # Save as .ans file
print(f"Cost: ${result.cost_usd:.4f}")
```

### Shell Completions

Tab-completion for `--style`, `--model`, and all flags:

```bash
# Bash — add to ~/.bashrc
source /path/to/bbs-ansi-art/completions/generate-art.bash

# Zsh — add to ~/.zshrc
source /path/to/bbs-ansi-art/completions/generate-art.zsh

# Fish — copy to completions dir
cp /path/to/bbs-ansi-art/completions/generate-art.fish \
   ~/.config/fish/completions/generate_art.py.fish
```

## Architecture

```
bbs_ansi_art/
├── core/           # Canvas, Cell, Color, Document
├── codec/          # CP437 encoding, ANSI parser
├── sauce/          # SAUCE metadata read/write
├── render/         # Terminal, HTML, Text, LlmText renderers
├── create/         # Builder API, ArtSpec
├── io/             # File read/write
├── llm/            # LLM-powered generation
│   ├── styles.py   # 9 style presets with quantitative guidance
│   ├── corpus.py   # ZIP archive indexer + example selection
│   └── generator.py # Claude CLI runner + output validation
└── cli/            # Studio and CLI tools
    ├── core/       # Terminal, input handling
    ├── widgets/    # Reusable components
    └── studio/     # Interactive applications
```

## License

MIT License - see [LICENSE](LICENSE) for details.
