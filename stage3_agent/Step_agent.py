# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any, AsyncGenerator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from agents import BaseAgent
from model import ChatResponse

PROMPT_PATH = Path(__file__).with_name("step.md")


class Stage3ExecutionAgent(BaseAgent):
    agent_name: str = "Stage3ExecutionAgent"
    agent_stage: str = "stage3"
    agent_function: str = "execution_plan"

    def _load_default_prompt(self) -> str | None:
        if not PROMPT_PATH.exists():
            return None
        content = PROMPT_PATH.read_text(encoding="utf-8").strip()
        return content or None

    async def analyze_text(self, **kwargs: Any) -> str:
        response = await self.analyze(**kwargs)

        if inspect.isasyncgen(response):
            chunks: list[str] = []
            async for item in response:
                chunks.append(self._extract_text(item))
            result_text = "".join(chunks).strip()
        else:
            result_text = self._extract_text(response)

        return result_text


__all__ = [
    "Stage3ExecutionAgent",
]
