"""Corpus indexing for ANSI art ZIP archives.

Extracts .ans files from ZIP archives, parses them, renders to LlmText format,
and indexes by metadata for example selection during LLM-based generation.
"""

from __future__ import annotations

import json
import logging
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterator

from bbs_ansi_art.codec.ansi_parser import AnsiParser
from bbs_ansi_art.core.canvas import Canvas
from bbs_ansi_art.render.llm_text import LlmTextRenderer
from bbs_ansi_art.sauce.reader import parse_sauce_bytes, SAUCE_RECORD_SIZE

logger = logging.getLogger(__name__)

# Block/shade characters used in BBS ANSI art
BLOCK_CHARS = frozenset("█▄▀▌▐░▒▓")
# All characters typically found in ANSI lettering
LETTERING_CHARS = frozenset("█▄▀▌▐░▒▓─│┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬")

# File extensions to extract from ZIPs
ANS_EXTENSIONS = {".ans", ".asc", ".ice"}


@dataclass
class CorpusEntry:
    """A single indexed artwork from the corpus."""

    archive_path: str
    filename: str
    llm_text: str
    width: int
    height: int
    title: str = ""
    author: str = ""
    group: str = ""
    year: int | None = None
    # Computed analysis
    char_density: float = 0.0
    color_count: int = 0
    shading_ratio: float = 0.0
    has_lettering: bool = False
    dominant_colors: list[str] = field(default_factory=list)
    estimated_tokens: int = 0

    def to_dict(self) -> dict:
        """Serialize for caching."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CorpusEntry:
        """Deserialize from cache."""
        return cls(**data)


class CorpusIndex:
    """Index of ANSI artworks extracted from ZIP archives.

    Usage:
        corpus = CorpusIndex("/path/to/16colo.rs/archive/")
        corpus.build()
        corpus.save_cache("~/.cache/bbs-ansi-art/corpus.json")

        # Later:
        corpus = CorpusIndex.load_cache("~/.cache/bbs-ansi-art/corpus.json")
        examples = corpus.select_examples("acid", count=15)
    """

    def __init__(self, corpus_path: Path | str | None = None):
        self.corpus_path = Path(corpus_path).expanduser() if corpus_path else None
        self.entries: list[CorpusEntry] = []
        self._renderer = LlmTextRenderer(
            include_row_markers=True, compact=True, include_reset=True,
        )

    def build(
        self,
        max_files: int | None = None,
        max_height: int = 50,
        min_height: int = 3,
    ) -> None:
        """Scan ZIP archives, extract .ans files, parse, analyze, and index.

        Args:
            max_files: Maximum total files to index (None = all).
            max_height: Skip artwork taller than this (scene art, not lettering).
            min_height: Skip artwork shorter than this.
        """
        if not self.corpus_path or not self.corpus_path.exists():
            raise FileNotFoundError(f"Corpus path not found: {self.corpus_path}")

        self.entries.clear()
        count = 0

        # Find all ZIP files recursively
        zip_files = sorted(self.corpus_path.rglob("*.zip"))
        logger.info("Found %d ZIP archives in %s", len(zip_files), self.corpus_path)

        for zip_path in zip_files:
            try:
                for entry in self._extract_from_zip(zip_path):
                    if entry.height < min_height or entry.height > max_height:
                        continue
                    self.entries.append(entry)
                    count += 1
                    if max_files and count >= max_files:
                        logger.info("Reached max_files limit: %d", max_files)
                        return
            except Exception as exc:
                logger.warning("Failed to process %s: %s", zip_path, exc)

        logger.info("Indexed %d artwork entries", len(self.entries))

    def save_cache(self, path: Path | str) -> None:
        """Persist index to JSON for fast reload."""
        path = Path(path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "corpus_path": str(self.corpus_path) if self.corpus_path else None,
            "entry_count": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved corpus cache: %d entries to %s", len(self.entries), path)

    @classmethod
    def load_cache(cls, path: Path | str) -> CorpusIndex:
        """Load previously built index from JSON cache."""
        path = Path(path).expanduser()
        data = json.loads(path.read_text(encoding="utf-8"))
        index = cls(data.get("corpus_path"))
        index.entries = [CorpusEntry.from_dict(e) for e in data["entries"]]
        logger.info("Loaded corpus cache: %d entries from %s", len(index.entries), path)
        return index

    def select_examples(
        self,
        style: str,
        count: int = 15,
        max_tokens: int = 600_000,
        prefer_lettering: bool = True,
        max_height: int = 35,
    ) -> list[CorpusEntry]:
        """Select the best corpus examples for a given style.

        Args:
            style: Style name (e.g., "acid", "ice", "neon").
            count: Maximum number of examples to return.
            max_tokens: Token budget for all examples combined.
            prefer_lettering: Prefer entries detected as lettering/logos.
            max_height: Maximum height for selected examples.

        Returns:
            List of CorpusEntry objects, best matches first.
        """
        from bbs_ansi_art.llm.styles import get_style

        preset = get_style(style)
        affinities = preset.group_affinities if preset else ()
        palette = set(preset.color_palette) if preset else set()

        # Score each entry
        scored: list[tuple[float, CorpusEntry]] = []
        for entry in self.entries:
            if entry.height > max_height:
                continue

            score = 0.0

            # Group affinity bonus
            entry_group = entry.group.lower()
            entry_archive = entry.archive_path.lower()
            for affinity in affinities:
                if affinity in entry_group or affinity in entry_archive:
                    score += 50.0
                    break

            # Lettering bonus
            if prefer_lettering and entry.has_lettering:
                score += 30.0

            # Size preference: small logos score higher
            if entry.height <= 15:
                score += 20.0
            elif entry.height <= 25:
                score += 10.0

            # Color palette match
            if palette and entry.dominant_colors:
                overlap = len(palette & set(entry.dominant_colors))
                score += overlap * 5.0

            # Shading richness (for styles that use it)
            if preset and preset.shading_direction != "none":
                score += entry.shading_ratio * 20.0

            # Color diversity
            score += min(entry.color_count, 8) * 1.0

            scored.append((score, entry))

        # Sort by score descending
        scored.sort(key=lambda x: -x[0])

        # Select within token budget, favoring diversity
        selected: list[CorpusEntry] = []
        seen_authors: set[str] = set()
        token_total = 0

        for _score, entry in scored:
            if len(selected) >= count:
                break
            if token_total + entry.estimated_tokens > max_tokens:
                continue

            # Diversity: limit 3 per author
            author_key = entry.author.lower().strip()
            if author_key and sum(1 for s in selected if s.author.lower().strip() == author_key) >= 3:
                continue

            selected.append(entry)
            seen_authors.add(author_key)
            token_total += entry.estimated_tokens

        return selected

    def list_groups(self) -> list[tuple[str, int]]:
        """List all art groups in the corpus with entry counts.

        Returns:
            List of (group_name, count) tuples sorted by count descending.
        """
        groups: dict[str, int] = {}
        for e in self.entries:
            g = e.group.strip() if e.group.strip() else "(unknown)"
            groups[g] = groups.get(g, 0) + 1
        return sorted(groups.items(), key=lambda x: -x[1])

    def list_artists(self) -> list[tuple[str, int]]:
        """List all artists in the corpus with entry counts.

        Returns:
            List of (artist_name, count) tuples sorted by count descending.
        """
        artists: dict[str, int] = {}
        for e in self.entries:
            a = e.author.strip() if e.author.strip() else "(unknown)"
            artists[a] = artists.get(a, 0) + 1
        return sorted(artists.items(), key=lambda x: -x[1])

    def select_by_group(
        self,
        group: str,
        count: int = 15,
        max_tokens: int = 600_000,
        prefer_lettering: bool = True,
        max_height: int = 35,
    ) -> list[CorpusEntry]:
        """Select examples from a specific art group.

        Args:
            group: Group name to match (case-insensitive substring).
            count: Maximum number of examples.
            max_tokens: Token budget.
            prefer_lettering: Prefer lettering/logo pieces.
            max_height: Maximum height.

        Returns:
            Matching entries, best first.
        """
        group_lower = group.lower()
        candidates = [
            e for e in self.entries
            if group_lower in e.group.lower() or group_lower in e.archive_path.lower()
        ]

        if not candidates:
            logger.warning("No corpus entries match group %r", group)
            return []

        # Score by lettering + size
        scored: list[tuple[float, CorpusEntry]] = []
        for entry in candidates:
            if entry.height > max_height:
                continue
            score = 0.0
            if prefer_lettering and entry.has_lettering:
                score += 30.0
            if entry.height <= 15:
                score += 20.0
            elif entry.height <= 25:
                score += 10.0
            score += entry.shading_ratio * 20.0
            score += min(entry.color_count, 8) * 1.0
            scored.append((score, entry))

        scored.sort(key=lambda x: -x[0])

        selected: list[CorpusEntry] = []
        token_total = 0
        for _score, entry in scored:
            if len(selected) >= count:
                break
            if token_total + entry.estimated_tokens > max_tokens:
                continue
            selected.append(entry)
            token_total += entry.estimated_tokens

        return selected

    def _extract_from_zip(self, zip_path: Path) -> Iterator[CorpusEntry]:
        """Extract and index .ans files from a ZIP archive."""
        # Infer year from directory structure
        year = self._infer_year(zip_path)

        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue

                ext = Path(info.filename).suffix.lower()
                if ext not in ANS_EXTENSIONS:
                    continue

                try:
                    raw = zf.read(info.filename)
                    entry = self._parse_entry(
                        raw=raw,
                        filename=info.filename,
                        archive_path=str(zip_path),
                        year=year,
                    )
                    if entry:
                        yield entry
                except Exception as exc:
                    logger.debug(
                        "Failed to parse %s in %s: %s",
                        info.filename, zip_path.name, exc,
                    )

    def _parse_entry(
        self,
        raw: bytes,
        filename: str,
        archive_path: str,
        year: int | None,
    ) -> CorpusEntry | None:
        """Parse raw .ans bytes into a CorpusEntry."""
        # Extract SAUCE metadata
        sauce = None
        data = raw
        if len(raw) >= SAUCE_RECORD_SIZE:
            sauce = parse_sauce_bytes(raw[-SAUCE_RECORD_SIZE:])
            if sauce:
                # Strip SAUCE from data
                eof_pos = raw.rfind(b"\x1a")
                if eof_pos != -1:
                    data = raw[:eof_pos]

        width = 80
        if sauce and sauce.tinfo1 and sauce.tinfo1 > 0:
            width = sauce.tinfo1

        # Parse ANSI to canvas
        parser = AnsiParser(width=width)
        parser.feed(data)
        canvas = parser.get_canvas()

        if canvas.current_height < 1:
            return None

        # Render to LlmText
        llm_text = self._renderer.render(canvas)

        # Analyze the canvas
        analysis = self._analyze_canvas(canvas)

        # Estimate tokens (~3.5 chars per token for this format)
        estimated_tokens = max(1, len(llm_text) // 3)

        title = sauce.title if sauce else ""
        author = sauce.author if sauce else ""
        group = sauce.group if sauce else ""

        # Override year from SAUCE date if available
        if sauce and sauce.date:
            year = sauce.date.year

        return CorpusEntry(
            archive_path=archive_path,
            filename=filename,
            llm_text=llm_text,
            width=width,
            height=canvas.current_height,
            title=title,
            author=author,
            group=group,
            year=year,
            estimated_tokens=estimated_tokens,
            **analysis,
        )

    def _analyze_canvas(self, canvas: Canvas) -> dict:
        """Compute analysis metrics for a canvas."""
        total_cells = 0
        non_space = 0
        block_count = 0
        color_set: set[str] = set()
        color_freq: dict[str, int] = {}

        from bbs_ansi_art.render.llm_text import COLOR_NAMES, BRIGHT_COLOR_NAMES

        for _x, _y, cell in canvas.cells():
            total_cells += 1
            if cell.char != " ":
                non_space += 1
            if cell.char in BLOCK_CHARS:
                block_count += 1

            # Track colors
            if cell.bold and cell.fg in BRIGHT_COLOR_NAMES:
                name = BRIGHT_COLOR_NAMES[cell.fg]
            elif cell.fg in COLOR_NAMES:
                name = COLOR_NAMES[cell.fg]
            else:
                name = f"fg{cell.fg}"

            color_set.add(name)
            color_freq[name] = color_freq.get(name, 0) + 1

        # Dominant colors (top 5)
        sorted_colors = sorted(color_freq.items(), key=lambda x: -x[1])
        dominant = [c for c, _ in sorted_colors[:5] if c != "white"]

        char_density = non_space / total_cells if total_cells > 0 else 0.0
        shading_ratio = block_count / non_space if non_space > 0 else 0.0

        # Lettering detection heuristic
        has_lettering = self._detect_lettering(canvas)

        return {
            "char_density": round(char_density, 3),
            "color_count": len(color_set),
            "shading_ratio": round(shading_ratio, 3),
            "has_lettering": has_lettering,
            "dominant_colors": dominant,
        }

    def _detect_lettering(self, canvas: Canvas) -> bool:
        """Heuristic: detect if artwork contains large block lettering.

        Looks for horizontal bands where block characters dominate,
        suggesting text/logo content rather than scene illustration.
        """
        if canvas.current_height < 3:
            return False

        # Check each row for block character density
        dense_rows = 0
        for row in canvas.rows():
            block_count = 0
            total = 0
            for cell in row:
                if cell.char != " ":
                    total += 1
                    if cell.char in BLOCK_CHARS:
                        block_count += 1

            if total > 0 and block_count / total > 0.5:
                dense_rows += 1

        # Lettering typically has 3-10 dense rows forming a band
        ratio = dense_rows / canvas.current_height if canvas.current_height > 0 else 0
        return 3 <= dense_rows <= 15 and 0.15 < ratio < 0.9

    @staticmethod
    def _infer_year(zip_path: Path) -> int | None:
        """Infer year from directory structure (e.g., archive/1996/pack.zip)."""
        for part in zip_path.parts:
            if part.isdigit() and 1980 <= int(part) <= 2030:
                return int(part)
        return None
