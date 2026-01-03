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

PROMPT_PATH = Path(__file__).with_name("verifier.md")
STRATEGY_LIBRARY_DIR = PROJECT_ROOT / "strategy_library"


class StrategySelectionAgent(BaseAgent):
    agent_name: str = "StrategySelectionAgent"
    agent_stage: str = "stage2"
    agent_function: str = "strategy_selection"

    def _load_default_prompt(self) -> str | None:
        if not PROMPT_PATH.exists():
            return None

        content = PROMPT_PATH.read_text(encoding="utf-8").strip()
        strategy_sections: list[str] = []

        if STRATEGY_LIBRARY_DIR.exists() and STRATEGY_LIBRARY_DIR.is_dir():
            library_files = sorted(STRATEGY_LIBRARY_DIR.glob("*.md"))
            for strategy_file in library_files:
                data = strategy_file.read_text(encoding="utf-8").strip()
                if not data:
                    continue
                title = strategy_file.stem.replace("_", " ")
                section_header = f"## Strategy Library: {title}"
                strategy_sections.append(f"{section_header}\n\n{data}")

        if strategy_sections:
            merged_sections = "\n\n".join(strategy_sections).strip()
            if content:
                content = f"{content}\n\n{merged_sections}"
            else:
                content = merged_sections

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
