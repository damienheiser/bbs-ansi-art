"""LLM provider runners for ANSI art generation.

Each provider wraps a CLI tool or API that can accept a system prompt +
user prompt and return generated text. The prompt format (LlmText ROW
annotations) is provider-agnostic — any LLM that can follow instructions
can generate ANSI art.

Supported providers:
  CLI:  claude, codex, gemini, opencode, llama
  API:  anthropic, openai, google-genai
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProviderResult:
    """Raw result from a provider invocation."""

    text: str
    metadata: dict


def get_provider(name: str) -> type:
    """Get a provider class by name."""
    providers = {
        # CLI providers
        "claude": ClaudeCliProvider,
        "codex": CodexCliProvider,
        "gemini": GeminiCliProvider,
        "opencode": OpencodeCliProvider,
        "llama": LlamaCliProvider,
        # API providers
        "anthropic": AnthropicApiProvider,
        "openai": OpenaiApiProvider,
        "google": GoogleApiProvider,
    }
    key = name.lower().replace("-", "").replace("_", "")
    # Allow aliases
    aliases = {
        "googlegenai": "google",
        "googleai": "google",
        "openaiapi": "openai",
        "anthropicapi": "anthropic",
    }
    key = aliases.get(key, key)
    cls = providers.get(key)
    if not cls:
        available = ", ".join(sorted(providers.keys()))
        raise ValueError(f"Unknown provider: {name!r}. Available: {available}")
    return cls


def list_providers() -> list[str]:
    """List available provider names."""
    return [
        "claude", "codex", "gemini", "opencode", "llama",
        "anthropic", "openai", "google",
    ]


def _find_binary(name: str, extra_paths: list[str] | None = None) -> str:
    """Find a CLI binary on PATH or common locations."""
    path = shutil.which(name)
    if path:
        return path
    for candidate in extra_paths or []:
        expanded = os.path.expanduser(candidate)
        if os.path.isfile(expanded) and os.access(expanded, os.X_OK):
            return expanded
    raise FileNotFoundError(f"{name} CLI not found on PATH")


def _write_temp(content: str, suffix: str = ".txt") -> str:
    """Write content to a temp file, return path. Caller must unlink."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8",
    ) as f:
        f.write(content)
        return f.name


def _run_cli(
    cmd: list[str],
    stdin_text: str,
    timeout: int,
) -> subprocess.CompletedProcess:
    """Run a CLI command with stdin input."""
    logger.debug("Running: %s", " ".join(cmd[:6]) + " ...")
    return subprocess.run(
        cmd,
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ── CLI Providers ──


class ClaudeCliProvider:
    """Claude Code CLI (`claude -p`)."""

    name = "claude"

    def __init__(self, model: str = "opus", binary: str | None = None):
        self.model = model
        self.binary = binary or _find_binary("claude", [
            "~/.claude/local/claude",
            "~/.local/bin/claude",
        ])

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: int = 600,
        max_budget_usd: float | None = None,
    ) -> ProviderResult:
        cmd = [
            self.binary, "-p",
            "--model", self.model,
            "--output-format", "text",
            "--system-prompt", system_prompt,
            "--no-session-persistence",
            "--disallowed-tools",
            "Bash", "Read", "Write", "Edit", "Glob", "Grep",
            "Agent", "Skill", "WebFetch", "WebSearch",
            "NotebookEdit", "LSP",
        ]
        if max_budget_usd is not None:
            cmd.extend(["--max-budget-usd", str(max_budget_usd)])

        result = _run_cli(cmd, user_prompt, timeout)
        if result.returncode != 0:
            raise RuntimeError(f"claude exited {result.returncode}: {result.stderr.strip()}")

        return ProviderResult(text=result.stdout.strip(), metadata={"model": self.model})


class CodexCliProvider:
    """OpenAI Codex CLI (`codex exec`)."""

    name = "codex"

    def __init__(self, model: str = "o4-mini", binary: str | None = None):
        self.model = model
        self.binary = binary or _find_binary("codex")

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: int = 600,
        max_budget_usd: float | None = None,
    ) -> ProviderResult:
        # Codex uses config for system prompt — combine into user prompt
        combined = f"{system_prompt}\n\n---\n\n{user_prompt}"
        cmd = [
            self.binary, "exec",
            "-m", self.model,
            "--full-auto",
            "--ephemeral",
            combined,
        ]

        result = _run_cli(cmd, "", timeout)
        if result.returncode != 0:
            raise RuntimeError(f"codex exited {result.returncode}: {result.stderr.strip()}")

        return ProviderResult(text=result.stdout.strip(), metadata={"model": self.model})


class GeminiCliProvider:
    """Google Gemini CLI (`gemini -p`)."""

    name = "gemini"

    def __init__(self, model: str = "gemini-2.5-pro", binary: str | None = None):
        self.model = model
        self.binary = binary or _find_binary("gemini")

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: int = 600,
        max_budget_usd: float | None = None,
    ) -> ProviderResult:
        # Gemini uses --policy files for system prompt
        policy_path = _write_temp(system_prompt, suffix=".md")
        try:
            combined = f"{system_prompt}\n\n---\n\n{user_prompt}"
            cmd = [
                self.binary,
                "-p", combined,
                "--yolo",
                "--sandbox", "false",
            ]

            result = _run_cli(cmd, "", timeout)
        finally:
            os.unlink(policy_path)

        if result.returncode != 0:
            raise RuntimeError(f"gemini exited {result.returncode}: {result.stderr.strip()}")

        return ProviderResult(text=result.stdout.strip(), metadata={"model": self.model})


class OpencodeCliProvider:
    """Opencode CLI."""

    name = "opencode"

    def __init__(self, model: str = "default", binary: str | None = None):
        self.model = model
        self.binary = binary or _find_binary("opencode")

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: int = 600,
        max_budget_usd: float | None = None,
    ) -> ProviderResult:
        combined = f"{system_prompt}\n\n---\n\n{user_prompt}"
        cmd = [self.binary, "-p", combined]

        result = _run_cli(cmd, "", timeout)
        if result.returncode != 0:
            raise RuntimeError(f"opencode exited {result.returncode}: {result.stderr.strip()}")

        return ProviderResult(text=result.stdout.strip(), metadata={"model": self.model})


class LlamaCliProvider:
    """Meta Llama CLI (llama run)."""

    name = "llama"

    def __init__(self, model: str = "llama3.3", binary: str | None = None):
        self.model = model
        self.binary = binary or _find_binary("llama", [
            "~/.local/bin/llama",
        ])

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: int = 600,
        max_budget_usd: float | None = None,
    ) -> ProviderResult:
        combined = f"{system_prompt}\n\n---\n\n{user_prompt}"
        cmd = [self.binary, "run", self.model, combined]

        result = _run_cli(cmd, "", timeout)
        if result.returncode != 0:
            raise RuntimeError(f"llama exited {result.returncode}: {result.stderr.strip()}")

        return ProviderResult(text=result.stdout.strip(), metadata={"model": self.model})


# ── API Providers ──


class AnthropicApiProvider:
    """Anthropic Messages API (requires `anthropic` package)."""

    name = "anthropic"

    def __init__(self, model: str = "claude-opus-4-20250514", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: int = 600,
        max_budget_usd: float | None = None,
    ) -> ProviderResult:
        try:
            import anthropic
        except ImportError:
            raise ImportError("pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = response.content[0].text
        return ProviderResult(
            text=text,
            metadata={
                "model": self.model,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )


class OpenaiApiProvider:
    """OpenAI Chat Completions API (requires `openai` package)."""

    name = "openai"

    def __init__(self, model: str = "gpt-4o", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: int = 600,
        max_budget_usd: float | None = None,
    ) -> ProviderResult:
        try:
            import openai
        except ImportError:
            raise ImportError("pip install openai")

        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = response.choices[0].message.content
        return ProviderResult(
            text=text,
            metadata={
                "model": self.model,
                "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                "output_tokens": getattr(response.usage, "completion_tokens", 0),
            },
        )


class GoogleApiProvider:
    """Google Generative AI API (requires `google-genai` package)."""

    name = "google"

    def __init__(self, model: str = "gemini-2.5-pro", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: int = 600,
        max_budget_usd: float | None = None,
    ) -> ProviderResult:
        try:
            from google import genai
        except ImportError:
            raise ImportError("pip install google-genai")

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        text = response.text
        return ProviderResult(text=text, metadata={"model": self.model})
