# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, AsyncGenerator

from config import ModelConfig
from model import ChatResponse, OpenAIChatModel


class BaseAgent(ABC):
    agent_name: str
    agent_stage: str
    agent_function: str

    def __init__(
        self,
        config: ModelConfig | None = None,
        system_prompt: str | None = None,
        **overrides: Any,
    ) -> None:
        if config is None:
            config = ModelConfig.from_env(**overrides)

        config.validate()

        if system_prompt is None:
            system_prompt = self._load_default_prompt()
        self._system_prompt = system_prompt.strip() if system_prompt else None

        client_args = dict(config.client_args)
        if config.base_url:
            client_args["base_url"] = config.base_url

        self._model = OpenAIChatModel(
            model_name=config.model_name,
            api_key=config.api_key,
            stream=config.stream,
            reasoning_effort=config.reasoning_effort,
            organization=config.organization,
            client_args=client_args or None,
            generate_kwargs=config.generate_kwargs,
        )

    @property
    def system_prompt(self) -> str | None:
        return self._system_prompt

    @system_prompt.setter
    def system_prompt(self, prompt: str | None) -> None:
        if prompt is None:
            self._system_prompt = None
            return
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("System prompt must be a non-empty string when provided.")
        self._system_prompt = prompt.strip()

    @abstractmethod
    def _load_default_prompt(self) -> str | None:
        pass

    @staticmethod
    def _extract_text(response: ChatResponse) -> str:
        parts: list[str] = []
        for block in response.content:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                parts.append(getattr(block, "text", ""))
            elif block_type == "thinking":
                parts.append("[Reasoning]\n" + getattr(block, "thinking", ""))
        if parts:
            return "\n".join(part.strip() for part in parts if part).strip()
        if response.metadata:
            return json.dumps(response.metadata, ensure_ascii=False, indent=2)
        return ""

    async def analyze(
        self,
        *,
        context: str,
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
            **kwargs,
        )

        if inspect.isasyncgen(result):
            return result

        return result


__all__ = ["BaseAgent"]

