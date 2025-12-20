# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Literal

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from model import ChatResponse, OpenAIChatModel

PROMPT_PATH = Path(__file__).with_name("thinking.md")
ABILITY_LIBRARY_DIR = PROJECT_ROOT / "ability_library"


@dataclass(slots=True)
class CapabilityUpgradeConfig:
    api_key: str | None = None
    model_name: str = "gemini-2.5-pro"
    stream: bool = False
    base_url: str | None = "https://xh-hk.a3e.top/v1"
    reasoning_effort: Literal["low", "medium", "high"] | None = None
    system_prompt: str | None = None
    generate_kwargs: dict[str, Any] | None = field(default_factory=dict)
    organization: str | None = None
    client_args: dict[str, Any] | None = field(default_factory=dict)
    timeout: float = 60.0
    max_retries: int = 2
    retry_base_delay: float = 1.0
    retry_backoff_factor: float = 2.0
    max_library_chars: int | None = 120_000
    attach_envelope: bool = True
    summary_width: int = 160
    auto_apply_patch: bool = False
    backup_before_write: bool = True
    library_file: str | None = None


class CapabilityUpgradeAgent:
    agent_name: str = "CapabilityUpgradeAgent"
    agent_stage: str = "library"
    agent_function: str = "capability_upgrade"

    def __init__(
        self,
        config: CapabilityUpgradeConfig | None = None,
        **overrides: Any,
    ) -> None:
        config_data = asdict(config or CapabilityUpgradeConfig())
        config_data.update(overrides)

        api_key = (
            config_data.get("api_key")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("KIMI_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
        )
        if not api_key:
            raise ValueError(
                "OpenAI/Kimi API key is required. Provide it via `api_key` "
                "or set OPENAI_API_KEY / KIMI_API_KEY environment variable.",
            )

        client_args = dict(config_data.get("client_args") or {})
        base_url = config_data.get("base_url")
        if base_url:
            client_args["base_url"] = base_url

        timeout = config_data.get("timeout")
        if timeout is not None:
            client_args.setdefault("timeout", float(timeout))

        max_retries = config_data.get("max_retries")
        if max_retries is not None:
            client_args.setdefault("max_retries", int(max_retries))

        self._model = OpenAIChatModel(
            model_name=config_data.get("model_name", "gemini-2.5-pro"),
            api_key=api_key,
            stream=bool(config_data.get("stream", False)),
            reasoning_effort=config_data.get("reasoning_effort"),
            organization=config_data.get("organization"),
            client_args=client_args or None,
            generate_kwargs=config_data.get("generate_kwargs") or {},
        )

        max_library_chars = config_data.get("max_library_chars")
        self._max_library_chars: int | None = (
            int(max_library_chars) if max_library_chars is not None else None
        )
        self._library_snapshot: str | None = self._load_library_snapshot(self._max_library_chars)

        self._custom_system_prompt: bool = bool(config_data.get("system_prompt"))
        self._system_prompt: str | None = config_data.get("system_prompt") or self._compose_default_system_prompt()

        self._attach_envelope: bool = bool(config_data.get("attach_envelope", True))
        self._auto_apply_patch: bool = bool(config_data.get("auto_apply_patch", False))
        self._backup_before_write: bool = bool(config_data.get("backup_before_write", True))

        library_file = config_data.get("library_file") or str(
            ABILITY_LIBRARY_DIR / "core_capabilities.md"
        )
        self._library_file: Path = Path(library_file).expanduser().resolve()
        self._library_file.parent.mkdir(parents=True, exist_ok=True)

        self._last_patch_markdown: str | None = None
        self._last_applied_path: Path | None = None

    @property
    def system_prompt(self) -> str | None:
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, prompt: str | None) -> None:
        if prompt is None:
            self._system_prompt = None
            self._custom_system_prompt = False
            return

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("system_prompt must be a non-empty string.")

        self._system_prompt = prompt.strip()
        self._custom_system_prompt = True

    def refresh_system_prompt(
        self,
        *,
        force: bool = False,
        max_library_chars: int | None = None,
    ) -> None:
        if max_library_chars is not None:
            self._max_library_chars = max(1, int(max_library_chars))

        self._library_snapshot = self._load_library_snapshot(self._max_library_chars)

        if force or not self._custom_system_prompt:
            self._system_prompt = self._compose_default_system_prompt()
            self._custom_system_prompt = False

    async def evaluate(
        self,
        *,
        context: str,
        payload_contract: Any | None = None,
        structured_model: Any | None = None,
        **kwargs: Any,
    ) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        messages: list[dict[str, str]] = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})

        messages.append({"role": "user", "content": context.strip()})

        result = await self._model(
            messages=messages,
            structured_model=structured_model,
            payload_contract=payload_contract,
            **kwargs,
        )

        if inspect.isasyncgen(result):
            return result

        if self._attach_envelope or self._auto_apply_patch:
            text_content = self._extract_text(result)
            patch_markdown = self._extract_patch_markdown(text_content)
            applied_path: Path | None = None
            if patch_markdown and self._auto_apply_patch:
                applied_path = self.apply_patch(patch_markdown)

            self._last_patch_markdown = patch_markdown
            self._last_applied_path = applied_path

            if self._attach_envelope:
                result = self._attach_agent_envelope(
                    result,
                    raw_text=text_content,
                    patch_markdown=patch_markdown,
                    applied_path=applied_path,
                )
        return result

    async def evaluate_text(self, **kwargs: Any) -> str:
        response = await self.evaluate(**kwargs)
        if inspect.isasyncgen(response):
            chunks: list[str] = []
            async for chunk in response:
                chunks.append(self._extract_text(chunk))
            return "".join(chunks).strip()

        text_content = self._extract_text(response)
        patch_markdown = self._extract_patch_markdown(text_content)

        applied_path: Path | None = self._last_applied_path if self._auto_apply_patch else None
        if patch_markdown and self._auto_apply_patch and applied_path is None:
            applied_path = self.apply_patch(patch_markdown)

        self._last_patch_markdown = patch_markdown
        self._last_applied_path = applied_path
        return text_content

    @property
    def last_patch_markdown(self) -> str | None:
        return self._last_patch_markdown

    @property
    def last_applied_path(self) -> Path | None:
        return self._last_applied_path

    def apply_patch(self, markdown: str, *, backup: bool | None = None) -> Path | None:
        patch = (markdown or "").strip()
        if not patch:
            return None

        target_file = self._library_file
        if backup is None:
            backup = self._backup_before_write

        if backup and target_file.exists():
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            backup_path = target_file.with_suffix(
                target_file.suffix + f".bak-{timestamp}"
            )
            backup_path.write_text(
                target_file.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        existing_size = target_file.stat().st_size if target_file.exists() else 0
        append_text = patch
        if existing_size > 0 and not patch.startswith("\n"):
            append_text = "\n\n" + append_text

        append_text = append_text.rstrip() + "\n"
        with target_file.open("a", encoding="utf-8") as handler:
            handler.write(append_text)

        self._last_patch_markdown = patch
        self._last_applied_path = target_file
        return target_file

    def _compose_default_system_prompt(self) -> str | None:
        template = self._load_prompt_template()
        library_snapshot = self._library_snapshot

        if template and library_snapshot:
            return f"{template}\n\n## Current Capability Library Snapshot\n\n{library_snapshot}"
        if template:
            return template
        return library_snapshot

    @staticmethod
    def _load_prompt_template() -> str | None:
        if not PROMPT_PATH.exists():
            return None
        content = PROMPT_PATH.read_text(encoding="utf-8").strip()
        return content or None

    def _load_library_snapshot(self, max_chars: int | None) -> str | None:
        if not ABILITY_LIBRARY_DIR.exists():
            return None

        sections: list[str] = []
        for md_file in sorted(ABILITY_LIBRARY_DIR.glob("*.md")):
            text = md_file.read_text(encoding="utf-8").strip()
            if not text:
                continue
            title = md_file.stem.replace("_", " ").title()
            sections.append(f"### {title}\n\n{text}")

        if not sections:
            return None

        combined = "\n\n".join(sections).strip()
        if max_chars is not None and len(combined) > max_chars:
            truncated = combined[: max_chars].rstrip()
            truncated += "\n\n...[Content truncated]..."
            return truncated
        return combined

    @staticmethod
    def _extract_text(response: ChatResponse) -> str:
        parts: list[str] = []
        for block in response.content:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                parts.append(getattr(block, "text", "") or "")
            elif block_type == "thinking":
                parts.append("[Reasoning]\n" + (getattr(block, "thinking", "") or ""))
        if parts:
            return "\n".join(part.strip() for part in parts if part).strip()
        payload = getattr(response, "payload", None)
        if payload is not None:
            return str(payload)
        if response.metadata:
            return str(response.metadata)
        return ""

    @staticmethod
    def _extract_patch_markdown(text_content: str | None) -> str | None:
        if not text_content:
            return None

        patch_lines: list[str] = []
        recording = False
        for line in text_content.splitlines():
            if not recording and line.strip().startswith("###"):
                recording = True
            if recording:
                patch_lines.append(line)

        patch = "\n".join(patch_lines).strip()
        return patch or None

    def _attach_agent_envelope(
        self,
        response: ChatResponse,
        *,
        raw_text: str,
        patch_markdown: str | None,
        applied_path: Path | None,
    ) -> ChatResponse:
        if not raw_text:
            return response
        return response


__all__ = [
    "CapabilityUpgradeConfig",
    "CapabilityUpgradeAgent",
]
