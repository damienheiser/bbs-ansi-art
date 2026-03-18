"""Tests for LLM integration: styles, corpus, generator."""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bbs_ansi_art.llm.styles import StylePreset, get_style, list_styles, STYLES
from bbs_ansi_art.llm.corpus import CorpusIndex, CorpusEntry
from bbs_ansi_art.llm.generator import AnsiTextGenerator


# ── Styles ──


class TestStyles:
    def test_all_styles_have_required_fields(self):
        for name, preset in STYLES.items():
            assert preset.name, f"{name} missing name"
            assert preset.description, f"{name} missing description"
            assert preset.guidance, f"{name} missing guidance"
            assert preset.example_prompt, f"{name} missing example_prompt"
            assert preset.primary_chars, f"{name} missing primary_chars"
            assert preset.letter_height > 0, f"{name} invalid letter_height"

    def test_get_style_case_insensitive(self):
        assert get_style("acid") is not None
        assert get_style("ACID") is not None
        assert get_style("AcId") is not None

    def test_get_style_unknown(self):
        assert get_style("nonexistent") is None

    def test_list_styles(self):
        styles = list_styles()
        assert "acid" in styles
        assert "ice" in styles
        assert "neon" in styles
        assert len(styles) >= 8

    def test_style_color_palette_is_tuple(self):
        """Frozen dataclass requires immutable fields."""
        for name, preset in STYLES.items():
            assert isinstance(preset.color_palette, tuple), f"{name} palette should be tuple"
            assert isinstance(preset.group_affinities, tuple), f"{name} affinities should be tuple"

    def test_fire_style_exists(self):
        """New fire style should be present."""
        style = get_style("fire")
        assert style is not None
        assert "fire" in style.group_affinities


# ── Corpus ──


class TestCorpusEntry:
    def test_round_trip_serialization(self):
        entry = CorpusEntry(
            archive_path="/test/archive.zip",
            filename="test.ans",
            llm_text="ROW 0: [red]██[reset]",
            width=80,
            height=5,
            title="Test Art",
            author="Tester",
            group="TestGroup",
            year=1996,
            char_density=0.5,
            color_count=4,
            shading_ratio=0.3,
            has_lettering=True,
            dominant_colors=["bright_cyan", "white"],
            estimated_tokens=50,
        )
        data = entry.to_dict()
        restored = CorpusEntry.from_dict(data)
        assert restored.title == "Test Art"
        assert restored.has_lettering is True
        assert restored.dominant_colors == ["bright_cyan", "white"]


class TestCorpusIndex:
    def test_empty_index(self):
        corpus = CorpusIndex()
        assert len(corpus.entries) == 0

    def test_save_load_cache(self):
        corpus = CorpusIndex()
        corpus.entries = [
            CorpusEntry(
                archive_path="/test.zip",
                filename="art.ans",
                llm_text="ROW 0: [white]█[reset]",
                width=80,
                height=3,
                estimated_tokens=10,
            ),
        ]

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            cache_path = f.name

        try:
            corpus.save_cache(cache_path)
            loaded = CorpusIndex.load_cache(cache_path)
            assert len(loaded.entries) == 1
            assert loaded.entries[0].filename == "art.ans"
        finally:
            Path(cache_path).unlink(missing_ok=True)

    def test_select_examples_empty_corpus(self):
        corpus = CorpusIndex()
        examples = corpus.select_examples("acid", count=5)
        assert examples == []

    def test_select_examples_respects_count(self):
        corpus = CorpusIndex()
        corpus.entries = [
            CorpusEntry(
                archive_path=f"/test{i}.zip",
                filename=f"art{i}.ans",
                llm_text=f"ROW 0: [white]{'█' * 10}[reset]",
                width=80,
                height=10,
                author=f"Artist{i}",
                estimated_tokens=50,
            )
            for i in range(20)
        ]
        examples = corpus.select_examples("acid", count=5)
        assert len(examples) == 5

    def test_select_examples_respects_token_budget(self):
        corpus = CorpusIndex()
        corpus.entries = [
            CorpusEntry(
                archive_path=f"/test{i}.zip",
                filename=f"art{i}.ans",
                llm_text="ROW 0: " + "[white]" + "█" * 1000 + "[reset]",
                width=80,
                height=10,
                estimated_tokens=500,
            )
            for i in range(20)
        ]
        examples = corpus.select_examples("acid", count=20, max_tokens=1500)
        assert len(examples) <= 3  # 500 tokens each, budget 1500

    def test_infer_year(self):
        assert CorpusIndex._infer_year(Path("/archive/1996/pack.zip")) == 1996
        assert CorpusIndex._infer_year(Path("/archive/2025/modern.zip")) == 2025
        assert CorpusIndex._infer_year(Path("/some/path/pack.zip")) is None


# ── Generator ──


class TestGenerator:
    def test_build_messages_without_examples(self):
        gen = AnsiTextGenerator(api_key="test")
        style = get_style("acid")
        messages = gen._build_messages(
            text="HELLO",
            style=style,
            width=80,
            height=6,
            examples=[],
            instructions=[],
        )
        assert len(messages) == 2
        assert "ROW" in messages[0]["content"]
        assert "HELLO" in messages[1]["content"]

    def test_build_messages_with_examples(self):
        gen = AnsiTextGenerator(api_key="test")
        style = get_style("acid")
        examples = [
            CorpusEntry(
                archive_path="/test.zip",
                filename="art.ans",
                llm_text="ROW 0: [bright_cyan]████[reset]",
                width=80,
                height=5,
                title="Test",
                author="Artist",
                group="Group",
                year=1996,
                estimated_tokens=20,
            ),
        ]
        messages = gen._build_messages(
            text="TEST",
            style=style,
            width=80,
            height=6,
            examples=examples,
            instructions=["Add shadow"],
        )
        assert "EXAMPLE 1" in messages[1]["content"]
        assert "Artist" in messages[1]["content"]
        assert "Add shadow" in messages[1]["content"]

    def test_validate_output_strips_markdown(self):
        gen = AnsiTextGenerator(api_key="test")
        raw = "```\nROW 0: [red]██[reset]\nROW 1: [blue]▄▄[reset]\n```"
        cleaned = gen._validate_output(raw, 80)
        assert "```" not in cleaned
        assert "ROW 0:" in cleaned
        assert "ROW 1:" in cleaned

    def test_validate_output_strips_commentary(self):
        gen = AnsiTextGenerator(api_key="test")
        raw = "Here is your art:\n\nROW 0: [red]██[reset]\nROW 1: [blue]▄▄[reset]\n\nHope you like it!"
        cleaned = gen._validate_output(raw, 80)
        lines = cleaned.strip().split("\n")
        assert len(lines) == 2
        assert all(line.startswith("ROW") for line in lines)

    def test_validate_output_renumbers(self):
        gen = AnsiTextGenerator(api_key="test")
        raw = "ROW 0: [red]██[reset]\nROW 5: [blue]▄▄[reset]\nROW 99: [green]▀▀[reset]"
        cleaned = gen._validate_output(raw, 80)
        assert "ROW 0:" in cleaned
        assert "ROW 1:" in cleaned
        assert "ROW 2:" in cleaned

    def test_parse_result_basic(self):
        gen = AnsiTextGenerator(api_key="test")
        llm_text = "ROW 0: [bright_cyan]████[reset]\nROW 1: [bright_cyan]█[white]  [bright_cyan]█[reset]"
        canvas = gen._parse_result(llm_text, 80)
        assert canvas.current_height >= 2
        assert canvas.width == 80

    def test_parse_result_empty(self):
        gen = AnsiTextGenerator(api_key="test")
        canvas = gen._parse_result("", 80)
        assert canvas is not None

    def test_generate_sync_requires_api_key(self):
        gen = AnsiTextGenerator(api_key=None)
        with pytest.raises(ValueError, match="API key"):
            gen.generate_sync(text="TEST")

    def test_generate_sync_rejects_unknown_style(self):
        gen = AnsiTextGenerator(api_key="test")
        with pytest.raises(ValueError, match="Unknown style"):
            gen.generate_sync(text="TEST", style="nonexistent")
