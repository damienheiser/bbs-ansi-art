"""ANSI art text generator using Claude CLI.

Generates stylized block lettering by assembling a mega-prompt from corpus
examples and style guidance, then calling the Claude CLI (`claude -p`) to
produce LlmText output that gets parsed back to Canvas/AnsiDocument.

Requires the `claude` CLI to be installed and authenticated.
No anthropic Python package needed.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import TYPE_CHECKING

from bbs_ansi_art.core.canvas import Canvas
from bbs_ansi_art.core.document import AnsiDocument
from bbs_ansi_art.render.llm_text import LlmTextParser
from bbs_ansi_art.sauce.record import SauceRecord

if TYPE_CHECKING:
    from bbs_ansi_art.llm.corpus import CorpusIndex

logger = logging.getLogger(__name__)


@dataclass
class TextGenResult:
    """Result of ANSI text generation."""

    canvas: Canvas
    document: AnsiDocument
    llm_text: str
    style: str
    input_text: str
    cost_usd: float = 0.0
    duration_ms: int = 0
    model: str = ""


# Available color names for the format spec
ALL_COLORS = [
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
    "bright_black", "bright_red", "bright_green", "bright_yellow",
    "bright_blue", "bright_magenta", "bright_cyan", "bright_white",
]


SYSTEM_PROMPT = """You are an expert ANSI artist specializing in BBS-era block lettering.
You create stylized text/lettering in a structured annotation format.

## OUTPUT FORMAT

Each line of output follows this exact format:
```
ROW 0: [color]characters[reset]
ROW 1: [bright_cyan]██▄▀[white]TEXT[reset]
```

Rules:
- Each row starts with `ROW N: ` where N is the 0-based row number
- Colors are annotated as `[color_name]` for foreground or `[fg/bg]` for both
- Available colors: {colors}
- End each row with `[reset]` if any colors were used
- Maximum width: {width} columns (count only visible characters, not color tags)
- Output ONLY the ROW lines — no explanation, no markdown fences, no commentary

## BLOCK CHARACTERS

These CP437 block characters are your primary tools:
- █ (full block) — solid fills, thick strokes
- ▄ (lower half) — bottom curves, descenders, transitions
- ▀ (upper half) — top curves, ascenders, transitions
- ▌ (left half) — vertical thin strokes
- ▐ (right half) — vertical thin strokes
- ░ (light shade) — soft glow, fading edges
- ▒ (medium shade) — medium shadow/depth
- ▓ (dark shade) — deep shadow, near-solid

Use ▄▀ half-blocks for curves and flowing transitions — this is the key to
"flowing" text that looks organic rather than rigid and blocky.

## STYLE: {style_name}

{style_description}

{style_guidance}

### Lettering Technique
{lettering_guidance}

### Character Usage
Primary characters: {primary_chars}
Distribution: {char_weights}
Letter height: {letter_height} rows
Spacing between letters: {spacing} column(s)
Shading direction: {shading_direction}

### Color Palette (in priority order)
{palette_text}
"""

USER_PROMPT_WITH_EXAMPLES = """Here are {num_examples} examples of real ANSI artwork. Study their character usage, color patterns, shading techniques, and how they build letterforms:

{examples_text}

---

Now create ANSI block lettering that spells: "{text}"

Requirements:
- Width: {width} columns maximum
- Height: approximately {height} rows
- Style: {style_name}
- Every letter must be CLEARLY READABLE — legibility is paramount
- Use the shading and color techniques from the examples above
- Letters should flow naturally with {shading_direction} shading
- Output ONLY the ROW format lines, nothing else
{extra_instructions}"""

USER_PROMPT_NO_EXAMPLES = """Create ANSI block lettering that spells: "{text}"

Requirements:
- Width: {width} columns maximum
- Height: approximately {height} rows
- Style: {style_name}
- Every letter must be CLEARLY READABLE — legibility is paramount
- Use ▄▀ half-blocks for smooth curves and flowing transitions
- Use ░▒▓ for shading depth and gradients
- Output ONLY the ROW format lines, nothing else
{extra_instructions}"""


def _find_claude_cli() -> str:
    """Find the claude CLI binary."""
    path = shutil.which("claude")
    if path:
        return path
    # Common install locations
    for candidate in [
        os.path.expanduser("~/.claude/local/claude"),
        "/usr/local/bin/claude",
        "/opt/homebrew/bin/claude",
    ]:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise FileNotFoundError(
        "Claude CLI not found. Install from: https://docs.anthropic.com/en/docs/claude-code"
    )


class AnsiTextGenerator:
    """Generate stylized ANSI block lettering via Claude CLI.

    Uses `claude -p` (print mode) to run non-interactively. Requires the
    Claude CLI to be installed and authenticated — no API key or anthropic
    package needed.

    Usage:
        gen = AnsiTextGenerator(corpus=corpus)
        result = gen.generate("HELLO", style="acid", width=80)
        print(result.document.render())
    """

    def __init__(
        self,
        corpus: CorpusIndex | None = None,
        model: str = "opus",
        claude_path: str | None = None,
    ):
        """
        Args:
            corpus: Pre-built corpus index for examples. None = no examples.
            model: Model alias or full name (default: "opus" for 1M context).
            claude_path: Path to claude CLI binary. None = auto-detect.
        """
        self.corpus = corpus
        self.model = model
        self.claude_path = claude_path
        self._parser = LlmTextParser()

    def generate(
        self,
        text: str,
        style: str = "acid",
        width: int = 80,
        height: int | None = None,
        num_examples: int = 15,
        instructions: list[str] | None = None,
        timeout: int = 600,
        max_budget_usd: float | None = None,
    ) -> TextGenResult:
        """Generate stylized ANSI block lettering.

        Args:
            text: Text to render as block lettering.
            style: Style preset name (e.g., "acid", "ice", "neon").
            width: Maximum output width in columns.
            height: Desired height in rows (None = auto based on style).
            num_examples: Number of corpus examples to include.
            instructions: Additional generation instructions.
            timeout: CLI timeout in seconds.
            max_budget_usd: Maximum cost cap passed to claude CLI.

        Returns:
            TextGenResult with canvas, document, and metadata.
        """
        from bbs_ansi_art.llm.styles import get_style

        preset = get_style(style)
        if not preset:
            raise ValueError(
                f"Unknown style: {style!r}. "
                f"Available: acid, ice, blocky, ascii, amiga, dark, neon, minimal, fire"
            )

        claude_bin = self.claude_path or _find_claude_cli()

        if height is None:
            height = preset.letter_height

        # Select corpus examples
        examples = []
        if self.corpus and num_examples > 0:
            examples = self.corpus.select_examples(
                style=style,
                count=num_examples,
                max_tokens=600_000,
            )

        # Build prompts
        messages = self._build_messages(
            text=text,
            style=preset,
            width=width,
            height=height,
            examples=examples,
            instructions=instructions or [],
        )

        system_prompt = messages[0]["content"]
        user_prompt = messages[1]["content"]

        logger.info(
            "Generating '%s' in %s style (%d examples, model=%s)",
            text, style, len(examples), self.model,
        )

        # Write the user prompt to a temp file to avoid shell argument limits
        # (corpus examples can be very large — easily 500K+ chars)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8",
        ) as prompt_file:
            prompt_file.write(user_prompt)
            prompt_path = prompt_file.name

        try:
            raw_output, metadata = self._run_claude(
                claude_bin=claude_bin,
                system_prompt=system_prompt,
                prompt_path=prompt_path,
                timeout=timeout,
                max_budget_usd=max_budget_usd,
            )
        finally:
            os.unlink(prompt_path)

        # Validate and parse
        cleaned = self._validate_output(raw_output, width)
        canvas = self._parse_result(cleaned, width)

        # Wrap in document
        sauce = SauceRecord(
            title=text[:35],
            author="Claude",
            group="bbs-ansi-art",
            tinfo1=width,
            tinfo2=canvas.current_height,
        )
        document = AnsiDocument(canvas=canvas, sauce=sauce)

        return TextGenResult(
            canvas=canvas,
            document=document,
            llm_text=cleaned,
            style=style,
            input_text=text,
            cost_usd=metadata.get("cost_usd", 0.0),
            duration_ms=metadata.get("duration_ms", 0),
            model=metadata.get("model", self.model),
        )

    def _run_claude(
        self,
        claude_bin: str,
        system_prompt: str,
        prompt_path: str,
        timeout: int,
        max_budget_usd: float | None,
    ) -> tuple[str, dict]:
        """Execute the claude CLI and return (output_text, metadata).

        Uses `claude -p` with `--output-format json` for structured results,
        piping the prompt via stdin from a temp file.
        """
        # Write system prompt to a temp file too (can be very large)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8",
        ) as sys_file:
            sys_file.write(system_prompt)
            sys_prompt_path = sys_file.name

        cmd = [
            claude_bin,
            "-p",
            "--model", self.model,
            "--output-format", "text",
            "--system-prompt", system_prompt,
            "--no-session-persistence",
            # Disable all tools — we only want text generation
            "--disallowed-tools",
            "Bash", "Read", "Write", "Edit", "Glob", "Grep",
            "Agent", "Skill", "WebFetch", "WebSearch",
            "NotebookEdit", "LSP",
        ]

        if max_budget_usd is not None:
            cmd.extend(["--max-budget-usd", str(max_budget_usd)])

        # Read prompt from file and pipe to stdin
        with open(prompt_path, "r", encoding="utf-8") as f:
            user_prompt = f.read()

        logger.debug(
            "Running: %s (prompt: %d chars, system: %d chars)",
            " ".join(cmd[:6]) + " ...",
            len(user_prompt),
            len(system_prompt),
        )

        try:
            result = subprocess.run(
                cmd,
                input=user_prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        finally:
            os.unlink(sys_prompt_path)

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise RuntimeError(
                f"Claude CLI exited with code {result.returncode}: {stderr}"
            )

        raw_output = result.stdout.strip()
        metadata: dict = {}

        # Text mode: output is the raw response text
        # Try to parse as JSON first (if --output-format json was used)
        if raw_output.startswith("[{") or raw_output.startswith("{"):
            try:
                return self._parse_cli_json(raw_output)
            except Exception:
                pass

        return raw_output, metadata

    def _parse_cli_json(self, raw_json: str) -> tuple[str, dict]:
        """Parse the JSON array output from `claude -p --output-format json`.

        Returns (result_text, metadata_dict).
        """
        metadata: dict = {}

        try:
            events = json.loads(raw_json)
        except json.JSONDecodeError:
            # If JSON parsing fails, treat the entire output as raw text
            logger.warning("Failed to parse CLI JSON output, using raw text")
            return raw_json, metadata

        result_text = ""

        for event in events:
            event_type = event.get("type", "")

            if event_type == "result":
                result_text = event.get("result", "")
                metadata["cost_usd"] = event.get("total_cost_usd", 0.0)
                metadata["duration_ms"] = event.get("duration_ms", 0)
                metadata["is_error"] = event.get("is_error", False)

                usage = event.get("usage", {})
                metadata["input_tokens"] = usage.get("input_tokens", 0)
                metadata["output_tokens"] = usage.get("output_tokens", 0)

                # Extract model from modelUsage keys
                model_usage = event.get("modelUsage", {})
                if model_usage:
                    metadata["model"] = next(iter(model_usage))

            elif event_type == "system" and event.get("subtype") == "init":
                metadata["session_id"] = event.get("session_id", "")
                metadata["model"] = event.get("model", "")

        if not result_text:
            # Fallback: look for assistant message content
            for event in events:
                if event.get("type") == "assistant":
                    msg = event.get("message", {})
                    for block in msg.get("content", []):
                        if block.get("type") == "text":
                            result_text = block.get("text", "")
                            if result_text:
                                break
                if result_text:
                    break

        return result_text, metadata

    def _build_messages(
        self,
        text: str,
        style,
        width: int,
        height: int,
        examples: list,
        instructions: list[str],
    ) -> list[dict]:
        """Build the system + user messages for the CLI call."""
        # System message
        palette_lines = []
        for i, color in enumerate(style.color_palette):
            palette_lines.append(f"  {i + 1}. {color}")
        palette_text = "\n".join(palette_lines) if palette_lines else "  (use style-appropriate colors)"

        system = SYSTEM_PROMPT.format(
            colors=", ".join(ALL_COLORS),
            width=width,
            style_name=style.name,
            style_description=style.description,
            style_guidance=style.guidance,
            lettering_guidance=style.lettering_guidance or style.guidance,
            primary_chars=style.primary_chars,
            char_weights=style.char_weights or "(balanced)",
            letter_height=style.letter_height,
            spacing=style.spacing,
            shading_direction=style.shading_direction,
            palette_text=palette_text,
        )

        # User message
        extra = ""
        if instructions:
            extra = "\n".join(f"- {inst}" for inst in instructions)
            extra = f"\nAdditional instructions:\n{extra}"

        if examples:
            examples_text = self._format_examples(examples)
            user = USER_PROMPT_WITH_EXAMPLES.format(
                num_examples=len(examples),
                examples_text=examples_text,
                text=text,
                width=width,
                height=height,
                style_name=style.name,
                shading_direction=style.shading_direction,
                extra_instructions=extra,
            )
        else:
            user = USER_PROMPT_NO_EXAMPLES.format(
                text=text,
                width=width,
                height=height,
                style_name=style.name,
                extra_instructions=extra,
            )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    def _format_examples(self, examples: list) -> str:
        """Format corpus examples for inclusion in the prompt."""
        parts = []
        for i, entry in enumerate(examples):
            header_parts = [f"=== EXAMPLE {i + 1}"]
            if entry.title:
                header_parts.append(f'"{entry.title}"')
            if entry.author:
                header_parts.append(f"by {entry.author}")
            meta = []
            if entry.group:
                meta.append(entry.group)
            if entry.year:
                meta.append(str(entry.year))
            if meta:
                header_parts.append(f"({', '.join(meta)})")
            header_parts.append(f"[{entry.width}x{entry.height}]")
            header = " ".join(header_parts) + " ==="

            parts.append(header)
            parts.append(entry.llm_text)
            parts.append("")

        return "\n".join(parts)

    def _validate_output(self, raw: str, width: int) -> str:
        """Validate and clean LLM output.

        Handles common issues:
        - Markdown code fences
        - Non-ROW preamble/postamble text
        - Missing row markers
        - Lines exceeding width
        """
        lines = raw.strip().split("\n")
        cleaned: list[str] = []

        # Strip markdown fences
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        row_pattern = re.compile(r"^ROW\s+\d+:\s*")

        for line in lines:
            line = line.rstrip()

            # Skip non-ROW lines (LLM commentary)
            if not row_pattern.match(line) and not line.startswith("ROW "):
                # But if it looks like art content (has color tags), try to recover
                if "[" in line and any(c in line for c in "█▄▀░▒▓▐▌"):
                    cleaned.append(f"ROW {len(cleaned)}: {line}")
                continue

            cleaned.append(line)

        # Renumber rows sequentially
        renumbered: list[str] = []
        for i, line in enumerate(cleaned):
            # Strip existing ROW marker and add correct one
            content = row_pattern.sub("", line)
            renumbered.append(f"ROW {i}: {content}")

        return "\n".join(renumbered)

    def _parse_result(self, llm_text: str, width: int) -> Canvas:
        """Parse validated LlmText to Canvas with error recovery."""
        try:
            return self._parser.parse(llm_text, width=width)
        except Exception as exc:
            logger.warning("Full parse failed (%s), attempting line-by-line recovery", exc)

            # Line-by-line recovery
            canvas = Canvas(width=width)
            for line in llm_text.split("\n"):
                try:
                    partial = self._parser.parse(line, width=width)
                    for x, y, cell in partial.cells():
                        if not cell.is_default():
                            canvas.ensure_row(canvas.current_height)
                            target_y = canvas.current_height - 1
                            if x < width:
                                canvas.set(x, target_y, cell.copy())
                except Exception:
                    continue

            return canvas
