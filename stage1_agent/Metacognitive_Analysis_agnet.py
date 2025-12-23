# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path
from typing import Any, AsyncGenerator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from agents import BaseAgent
from MCP.tavily import get_default_tavily_search_tool
from model import ChatResponse

PROMPT_PATH = Path(__file__).with_name("reasoner.md")
ABILITY_LIBRARY_DIR = PROJECT_ROOT / "ability_library"


class MetacognitiveAnalysisAgent(BaseAgent):
    agent_name: str = "MetacognitiveAnalysisAgent"
    agent_stage: str = "stage1"
    agent_function: str = "metacognitive_analysis"

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._last_metacognitive_search: dict[str, Any] | None = None

    def _load_default_prompt(self) -> str | None:
        if not PROMPT_PATH.exists():
            return None

        content = PROMPT_PATH.read_text(encoding="utf-8").strip()
        ability_sections: list[str] = []

        if ABILITY_LIBRARY_DIR.exists() and ABILITY_LIBRARY_DIR.is_dir():
            library_files = sorted(ABILITY_LIBRARY_DIR.glob("*.md"))
            for ability_file in library_files:
                data = ability_file.read_text(encoding="utf-8").strip()
                if not data:
                    continue
                title = ability_file.stem.replace("_", " ")
                section_header = f"## Ability Library: {title}"
                ability_sections.append(f"{section_header}\n\n{data}")

        if ability_sections:
            merged_sections = "\n\n".join(ability_sections).strip()
            if content:
                content = f"{content}\n\n{merged_sections}"
            else:
                content = merged_sections

        return content or None

    async def analyze(
        self,
        *,
        context: str,
        perform_metacognitive_search: bool = True,
        structured_model: Any | None = None,
        **kwargs: Any,
    ) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        objective_text = self._extract_objective_from_context(context)
        context_text = self._extract_context_snapshot_from_context(context)

        metacognitive_snapshot: dict[str, Any] | None = None
        if perform_metacognitive_search and objective_text:
            metacognitive_snapshot = await self._prepare_metacognitive_search(
                objective=objective_text,
                context=context_text,
            )
            self._last_metacognitive_search = metacognitive_snapshot

        user_content = context.strip()
        if metacognitive_snapshot:
            user_content += "\n\n## External Failure Mode Research\n\n"
            user_content += self._format_metacognitive_snapshot(metacognitive_snapshot)

        messages: list[dict[str, str]] = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})

        messages.append({"role": "user", "content": user_content})

        result = await self._model(
            messages=messages,
            structured_model=structured_model,
            **kwargs,
        )

        if inspect.isasyncgen(result):
            return result

        return result

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

    @staticmethod
    def _extract_objective_from_context(context: str) -> str:
        lines = context.split("\n")
        capture = False
        objective_lines: list[str] = []
        for line in lines:
            if line.strip().startswith("## Objective"):
                capture = True
                continue
            if capture:
                if line.strip().startswith("## "):
                    break
                objective_lines.append(line)
        return "\n".join(objective_lines).strip()

    @staticmethod
    def _extract_context_snapshot_from_context(context: str) -> str:
        lines = context.split("\n")
        capture = False
        snapshot_lines: list[str] = []
        for line in lines:
            if line.strip().startswith("## Context Snapshot"):
                capture = True
                continue
            if capture:
                if line.strip().startswith("## "):
                    break
                snapshot_lines.append(line)
        return "\n".join(snapshot_lines).strip()


    async def _prepare_metacognitive_search(
        self,
        *,
        objective: str,
        context: str | None,
    ) -> dict[str, Any] | None:
        objective_text = (objective or "").strip()
        if not objective_text:
            return None

        abstraction = await self._derive_task_abstraction(
            objective=objective_text,
            context=context or "",
        )
        queries = self._construct_metacognitive_queries(abstraction, objective_text)
        if not queries:
            return {
                "status": "skipped",
                "reason": "Failed to construct search queries.",
                "abstraction": abstraction,
                "tool_descriptor": "tavily_search (not executed)",
            }

        try:
            search_tool = await get_default_tavily_search_tool()
            tool_descriptor = f"{search_tool.name} (MCP)"
        except Exception as exc:
            return {
                "status": "failed",
                "reason": f"Unable to load Tavily tool: {exc}",
                "abstraction": abstraction,
                "queries": queries,
                "tool_descriptor": "tavily_search (unavailable)",
            }

        snapshots: list[dict[str, str]] = []
        for query in queries:
            snapshot: dict[str, str] = {"query": query}
            try:
                result = await search_tool(query=query)
                snapshot["evidence"] = self._summarize_tool_response(result)
            except Exception as exc:
                snapshot["error"] = str(exc)
            snapshots.append(snapshot)

        return {
            "status": "completed",
            "abstraction": abstraction,
            "queries": queries,
            "snapshots": snapshots,
            "tool_descriptor": tool_descriptor,
        }

    async def _derive_task_abstraction(
        self,
        *,
        objective: str,
        context: str,
    ) -> dict[str, str]:
        system_prompt = (
            "You extract concise task abstractions. Respond with compact JSON "
            'containing keys "task_category" and "core_mechanism" (both short '
            "phrases in Chinese or English). Avoid explanations."
        )
        user_prompt = (
            "Objective:\n"
            f"{objective.strip()}\n\n"
            "Context:\n"
            f"{(context or '').strip() or 'None'}"
        )

        try:
            response = await self._model(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
            if inspect.isasyncgen(response):
                text_chunks: list[str] = []
                async for item in response:
                    text_chunks.append(self._extract_text(item))
                raw_text = "".join(text_chunks).strip()
            else:
                raw_text = self._extract_text(response)
        except Exception:
            raw_text = None

        abstraction: dict[str, str] = {}
        if raw_text:
            try:
                parsed = json.loads(raw_text)
                if isinstance(parsed, dict):
                    abstraction["task_category"] = str(parsed.get("task_category", "")).strip()
                    abstraction["core_mechanism"] = str(parsed.get("core_mechanism", "")).strip()
            except json.JSONDecodeError:
                trimmed = raw_text.strip()
                if trimmed.startswith("{") and trimmed.endswith("}"):
                    try:
                        parsed = json.loads(trimmed)
                    except json.JSONDecodeError:
                        parsed = {}
                    if isinstance(parsed, dict):
                        abstraction["task_category"] = str(parsed.get("task_category", "")).strip()
                        abstraction["core_mechanism"] = str(parsed.get("core_mechanism", "")).strip()

        if not abstraction.get("task_category"):
            abstraction["task_category"] = self._fallback_task_category(objective)
        if not abstraction.get("core_mechanism"):
            abstraction["core_mechanism"] = self._fallback_core_mechanism(objective)

        return abstraction

    @staticmethod
    def _fallback_task_category(objective: str) -> str:
        lowered = objective.lower()
        if "research" in lowered or "investigat" in lowered or "analysis" in lowered:
            return "Research Task"
        if "implement" in lowered or "build" in lowered or "develop" in lowered:
            return "System Implementation"
        if "debug" in lowered or "error" in lowered or "issue" in lowered:
            return "Debugging"
        if "plan" in lowered or "strategy" in lowered:
            return "Strategy Planning"
        return "General Problem Analysis"

    @staticmethod
    def _fallback_core_mechanism(objective: str) -> str:
        lowered = objective.lower()
        if "multi-hop" in lowered or "chain" in lowered:
            return "Multi-hop Reasoning"
        if "search" in lowered or "retrieve" in lowered:
            return "Information Retrieval"
        if "code" in lowered or "implement" in lowered:
            return "Code Implementation"
        if "evaluate" in lowered or "assess" in lowered:
            return "Evaluation Analysis"
        return "Cross-document Reasoning"

    @staticmethod
    def _construct_metacognitive_queries(
        abstraction: dict[str, str],
        objective: str,
    ) -> list[str]:
        task_category = abstraction.get("task_category") or ""
        core_mechanism = abstraction.get("core_mechanism") or ""
        category = task_category or objective.strip().split("\n", 1)[0]
        mechanism = core_mechanism or category

        category = category.strip()
        mechanism = mechanism.strip()
        if not category and not mechanism:
            return []

        concept_query = f"{category} common pitfalls risks".strip()
        tool_query = f"{mechanism} edge cases failure".strip()
        llm_query = f"LLM hallucination in {category or mechanism}".strip()

        queries: list[str] = []
        for query in (concept_query, tool_query, llm_query):
            normalized = query.strip()
            if normalized:
                queries.append(normalized)
        return queries

    def _summarize_tool_response(self, tool_response: Any) -> str:
        if tool_response is None:
            return "No response returned."

        text_chunks: list[str] = []
        content = getattr(tool_response, "content", None)
        if isinstance(content, (list, tuple)):
            for block in content:
                text = getattr(block, "text", "")
                if text:
                    text_chunks.append(text.strip())
        elif isinstance(tool_response, str):
            text_chunks.append(tool_response.strip())
        else:
            text_chunks.append(str(tool_response))

        combined = "\n".join(chunk for chunk in text_chunks if chunk).strip()
        if not combined:
            combined = str(tool_response)

        normalized = " ".join(combined.split())
        if normalized.startswith("{") or normalized.startswith("["):
            try:
                parsed = json.loads(normalized)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                snippets: list[str] = []
                for item in parsed[:3]:
                    if isinstance(item, dict):
                        title = str(item.get("title") or item.get("name") or "")[:80].strip()
                        snippet = str(
                            item.get("snippet")
                            or item.get("content")
                            or item.get("summary")
                            or ""
                        ).strip()
                        if snippet:
                            snippet = " ".join(snippet.split())
                        entry = title or snippet
                        if entry:
                            if snippet and title:
                                entry = f"{title}: {snippet[:120]}"
                            snippets.append(entry[:140])
                if snippets:
                    normalized = " | ".join(snippets)
            elif isinstance(parsed, dict):
                parts: list[str] = []
                for key in ("title", "name", "summary", "snippet", "content"):
                    value = parsed.get(key)
                    if value:
                        parts.append(f"{key}: {str(value)[:100]}")
                if parts:
                    normalized = " | ".join(parts)

        if len(normalized) > 900:
            normalized = normalized[:900].rstrip() + "..."
        return normalized or combined[:120]

    @staticmethod
    def _format_metacognitive_snapshot(snapshot: dict[str, Any]) -> str:
        lines: list[str] = []
        status = snapshot.get("status", "unknown")
        lines.append(f"- Status: {status}")

        abstraction = snapshot.get("abstraction") or {}
        if isinstance(abstraction, dict):
            task_category = abstraction.get("task_category")
            core_mechanism = abstraction.get("core_mechanism")
            if task_category:
                lines.append(f"- Task Category: {task_category}")
            if core_mechanism:
                lines.append(f"- Core Mechanism: {core_mechanism}")

        snapshots = snapshot.get("snapshots")
        if isinstance(snapshots, list):
            for idx, item in enumerate(snapshots, 1):
                if not isinstance(item, dict):
                    continue
                query = item.get("query", "")
                evidence = item.get("evidence")
                error = item.get("error")
                heading = f"{idx}. Query: {query}"
                if evidence:
                    lines.append(f"{heading}\n    Evidence: {evidence}")
                elif error:
                    lines.append(f"{heading}\n    Error: {error}")
        elif snapshot.get("reason"):
            lines.append(f"- Note: {snapshot['reason']}")

        queries = snapshot.get("queries")
        if not snapshots and queries:
            lines.append(f"- Pending Queries: {queries}")

        return "\n".join(lines).strip()
