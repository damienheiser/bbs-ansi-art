"""LLM provider runners for ANSI art generation.

Each provider wraps a CLI tool or API that can accept a system prompt +
user prompt and return generated text. The prompt format (LlmText ROW
annotations) is provider-agnostic — any LLM that can follow instructions
can generate ANSI art.

CLI providers (claude, codex, gemini, opencode, llama):
  Don't need --model — the CLI picks its own default.
  If --model is passed, it's forwarded to the CLI.

API providers (anthropic, openai, google):
  Always need a model name. Defaults are baked in.
"""

from __future__ import annotations

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


# API providers need explicit model names. CLI providers don't.
API_DEFAULT_MODELS = {
    "anthropic": "claude-opus-4-20250514",
    "openai": "gpt-4o",
    "google": "gemini-2.5-pro",
}


def get_provider(name: str) -> type:
    """Get a provider class by name."""
    providers = {
        "claude": ClaudeCliProvider,
        "codex": CodexCliProvider,
        "gemini": GeminiCliProvider,
        "opencode": OpencodeCliProvider,
        "llama": LlamaCliProvider,
        "anthropic": AnthropicApiProvider,
        "openai": OpenaiApiProvider,
        "google": GoogleApiProvider,
    }
    key = name.lower().replace("-", "").replace("_", "")
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


def is_api_provider(name: str) -> bool:
    """Return True if the provider is an API provider (requires --model)."""
    return name.lower() in API_DEFAULT_MODELS


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
# model=None means "let the CLI pick its own default"


class ClaudeCliProvider:
    """Claude Code CLI (`claude -p`)."""

    name = "claude"

    def __init__(self, model: str | None = None, binary: str | None = None, **_kw):
        self.model = model  # None = CLI picks default
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
            "--output-format", "text",
            "--system-prompt", system_prompt,
            "--no-session-persistence",
            "--disallowed-tools",
            "Bash", "Read", "Write", "Edit", "Glob", "Grep",
            "Agent", "Skill", "WebFetch", "WebSearch",
            "NotebookEdit", "LSP",
        ]
        if self.model:
            cmd.extend(["--model", self.model])
        if max_budget_usd is not None:
            cmd.extend(["--max-budget-usd", str(max_budget_usd)])

        result = _run_cli(cmd, user_prompt, timeout)
        if result.returncode != 0:
            raise RuntimeError(f"claude exited {result.returncode}: {result.stderr.strip()}")

        return ProviderResult(
            text=result.stdout.strip(),
            metadata={"model": self.model or "(cli default)"},
        )


class CodexCliProvider:
    """OpenAI Codex CLI (`codex exec`)."""

    name = "codex"

    def __init__(self, model: str | None = None, binary: str | None = None, **_kw):
        self.model = model
        self.binary = binary or _find_binary("codex")

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: int = 600,
        max_budget_usd: float | None = None,
    ) -> ProviderResult:
        combined = f"{system_prompt}\n\n---\n\n{user_prompt}"
        prompt_path = _write_temp(combined, suffix=".md")
        try:
            cmd = [
                self.binary, "exec",
                "--full-auto",
                "--ephemeral",
                "-q",
                f"Follow the instructions in {prompt_path} exactly. Output ONLY the ROW lines.",
            ]
            if self.model:
                cmd.extend(["-m", self.model])

            result = _run_cli(cmd, "", timeout)
        finally:
            os.unlink(prompt_path)

        if result.returncode != 0:
            stderr = result.stderr.strip()
            for line in stderr.split("\n"):
                if "ERROR" in line or "error" in line.lower():
                    stderr = line
                    break
            raise RuntimeError(f"codex exited {result.returncode}: {stderr}")

        return ProviderResult(
            text=result.stdout.strip(),
            metadata={"model": self.model or "(cli default)"},
        )


class GeminiCliProvider:
    """Google Gemini CLI (`gemini -p`)."""

    name = "gemini"

    def __init__(self, model: str | None = None, binary: str | None = None, **_kw):
        self.model = model
        self.binary = binary or _find_binary("gemini")

    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        timeout: int = 600,
        max_budget_usd: float | None = None,
    ) -> ProviderResult:
        policy_path = _write_temp(system_prompt, suffix=".md")
        prompt_path = _write_temp(user_prompt, suffix=".md")
        try:
            cmd = [
                self.binary,
                "-p", f"Follow the instructions in {prompt_path} exactly. Output ONLY the ROW lines.",
                "--yolo",
                "--sandbox", "false",
                "--policy", policy_path,
            ]
            if self.model:
                cmd.extend(["-m", self.model])

            result = _run_cli(cmd, "", timeout)
        finally:
            os.unlink(policy_path)
            os.unlink(prompt_path)

        if result.returncode != 0:
            raise RuntimeError(f"gemini exited {result.returncode}: {result.stderr.strip()}")

        return ProviderResult(
            text=result.stdout.strip(),
            metadata={"model": self.model or "(cli default)"},
        )


class OpencodeCliProvider:
    """Opencode CLI."""

    name = "opencode"

    def __init__(self, model: str | None = None, binary: str | None = None, **_kw):
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
        prompt_path = _write_temp(combined, suffix=".md")
        try:
            cmd = [self.binary, "-p", f"Follow instructions in {prompt_path}. Output ONLY ROW lines."]
            if self.model:
                cmd.extend(["-m", self.model])
            result = _run_cli(cmd, "", timeout)
        finally:
            os.unlink(prompt_path)

        if result.returncode != 0:
            raise RuntimeError(f"opencode exited {result.returncode}: {result.stderr.strip()}")

        return ProviderResult(
            text=result.stdout.strip(),
            metadata={"model": self.model or "(cli default)"},
        )


class LlamaCliProvider:
    """Meta Llama CLI (llama run)."""

    name = "llama"

    def __init__(self, model: str | None = None, binary: str | None = None, **_kw):
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
        prompt_path = _write_temp(combined, suffix=".md")
        try:
            model = self.model or "llama3.3"
            cmd = [self.binary, "run", model, f"Follow instructions in {prompt_path}. Output ONLY ROW lines."]
            result = _run_cli(cmd, "", timeout)
        finally:
            os.unlink(prompt_path)

        if result.returncode != 0:
            raise RuntimeError(f"llama exited {result.returncode}: {result.stderr.strip()}")

        return ProviderResult(
            text=result.stdout.strip(),
            metadata={"model": model},
        )


# ── API Providers ──
# These always require a model name (defaults baked in).


class AnthropicApiProvider:
    """Anthropic Messages API (requires `anthropic` package)."""

    name = "anthropic"

    def __init__(self, model: str | None = None, api_key: str | None = None, **_kw):
        self.model = model or API_DEFAULT_MODELS["anthropic"]
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

    def __init__(self, model: str | None = None, api_key: str | None = None, **_kw):
        self.model = model or API_DEFAULT_MODELS["openai"]
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

    def __init__(self, model: str | None = None, api_key: str | None = None, **_kw):
        self.model = model or API_DEFAULT_MODELS["google"]
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
