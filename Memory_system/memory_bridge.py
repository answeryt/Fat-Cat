# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping, Sequence
from dataclasses import dataclass

import aiofiles

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ContextSection:
    header: str
    content: str
    source: str = ""


class MemoryBridge:
    
    def __init__(self) -> None:
        self._sections: list[ContextSection] = []
    
    def clear(self) -> None:
        self._sections.clear()
    
    def add_section(self, header: str, content: str, source: str = "") -> None:
        if content and content.strip():
            self._sections.append(ContextSection(
                header=header.strip(),
                content=content.strip(),
                source=source.strip(),
            ))
    
    def add_objective(self, objective: str) -> None:
        self.add_section("Objective", objective, source="user_input")
    
    def add_context_snapshot(self, snapshot: str) -> None:
        self.add_section("Context Snapshot", snapshot, source="environment")

    def add_user_context(self, content: str) -> None:
        self.add_section("用户附加上下文", content, source="user_input")

    def add_tool_catalog(self, tools: Sequence[str] | str) -> None:
        if isinstance(tools, str):
            content = tools
        else:
            content = "\n".join(f"- {tool}" for tool in tools if tool.strip())
        self.add_section("Available Tools", content, source="system")
    
    def add_execution_constraints(self, constraints: Sequence[str] | str) -> None:
        if isinstance(constraints, str):
            content = constraints
        else:
            content = "\n".join(f"- {c}" for c in constraints if c.strip())
        self.add_section("Execution Constraints", content, source="system")
    
    def add_attachments(self, attachments: Mapping[str, Any] | Sequence[Any] | str) -> None:
        if isinstance(attachments, str):
            content = attachments
        elif isinstance(attachments, Mapping):
            lines = []
            for k, v in attachments.items():
                lines.append(f"- {k}: {v}")
            content = "\n".join(lines)
        else:
            content = "\n".join(f"- {item}" for item in attachments)
        self.add_section("Task Attachments", content, source="user_input")
    
    def add_raw_section(self, header: str, content: Any, source: str = "") -> None:
        if content is None:
            return
        if isinstance(content, str):
            text = content
        elif isinstance(content, Mapping):
            lines = []
            for k, v in content.items():
                if isinstance(v, (list, tuple)):
                    lines.append(f"### {k}")
                    for item in v:
                        lines.append(f"- {item}")
                else:
                    lines.append(f"**{k}**: {v}")
            text = "\n".join(lines)
        elif isinstance(content, Sequence):
            text = "\n".join(f"- {item}" for item in content)
        else:
            text = str(content)
        self.add_section(header, text, source)
    
    def build_context(self) -> str:
        if not self._sections:
            return ""
        
        parts: list[str] = []
        for section in self._sections:
            header_line = f"## {section.header}"
            if section.source:
                header_line += f" (from {section.source})"
            parts.append(header_line)
            parts.append("")
            parts.append(section.content)
            parts.append("")
        
        return "\n".join(parts).strip()
    
    def build_context_for_stage(self, stage: str) -> str:
        return self.build_context()
    
    @staticmethod
    def from_finish_form(finish_form_path: str | Path) -> MemoryBridge:
        bridge = MemoryBridge()
        path = Path(finish_form_path)
        if not path.exists():
            return bridge

        content = path.read_text(encoding="utf-8")
        bridge.add_section("Collaboration Form", content, source="finish_form")
        return bridge

    @staticmethod
    async def from_finish_form_async(finish_form_path: str | Path) -> MemoryBridge:
        """Async version of from_finish_form that uses non-blocking file I/O."""
        bridge = MemoryBridge()
        path = Path(finish_form_path)
        if not path.exists():
            return bridge

        async with aiofiles.open(path, encoding="utf-8") as f:
            content = await f.read()
        bridge.add_section("Collaboration Form", content, source="finish_form")
        return bridge

    @staticmethod
    def load_stage_output(finish_form_path: str | Path, marker: str) -> str:
        path = Path(finish_form_path)
        if not path.exists():
            return ""

        content = path.read_text(encoding="utf-8")
        start_marker = f"<!-- {marker}_START -->"
        end_marker = f"<!-- {marker}_END -->"

        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            return ""

        section = content[start_idx + len(start_marker):end_idx].strip()
        return section

    @staticmethod
    async def load_stage_output_async(finish_form_path: str | Path, marker: str) -> str:
        """Async version of load_stage_output that uses non-blocking file I/O."""
        path = Path(finish_form_path)
        if not path.exists():
            return ""

        async with aiofiles.open(path, encoding="utf-8") as f:
            content = await f.read()
        start_marker = f"<!-- {marker}_START -->"
        end_marker = f"<!-- {marker}_END -->"

        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            return ""

        section = content[start_idx + len(start_marker):end_idx].strip()
        return section


ANCHOR_PATTERN = re.compile(r"<!--\s*([A-Z0-9_]+)_START\s*-->")


def _load_anchor_sections(finish_form_path: str | Path) -> dict[str, str]:
    path = Path(finish_form_path)
    if not path.exists():
        return {}

    content = path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}

    for match in ANCHOR_PATTERN.finditer(content):
        marker = match.group(1).strip()
        end_marker = f"<!-- {marker}_END -->"
        end_idx = content.find(end_marker, match.end())
        if end_idx == -1:
            continue
        sections[marker] = content[match.end():end_idx].strip()

    return sections


async def _load_anchor_sections_async(finish_form_path: str | Path) -> dict[str, str]:
    """Async version of _load_anchor_sections that uses non-blocking file I/O."""
    path = Path(finish_form_path)
    if not path.exists():
        return {}

    async with aiofiles.open(path, encoding="utf-8") as f:
        content = await f.read()
    sections: dict[str, str] = {}

    for match in ANCHOR_PATTERN.finditer(content):
        marker = match.group(1).strip()
        end_marker = f"<!-- {marker}_END -->"
        end_idx = content.find(end_marker, match.end())
        if end_idx == -1:
            continue
        sections[marker] = content[match.end():end_idx].strip()

    return sections


EXTERNAL_SECTION_DESCRIPTORS = [
    ("EXTERNAL_INFO", "External Information", "external_input"),
    ("EXTERNAL_OBJECTIVE", "Task Objective", "external_input"),
    ("EXTERNAL_CONTEXT", "External Context", "external_input"),
    ("EXTERNAL_TOOL_CATALOG", "Available Tools", "external_input"),
]

STAGE1_SECTION_DESCRIPTORS = [
    ("STAGE1_ANALYSIS", "Stage 1 Analysis", "stage1_agent"),
]

STAGE2A_SECTION_DESCRIPTORS = [
    ("STAGE2A_ANALYSIS", "Stage 2-A Analysis", "stage2a_agent"),
]

STAGE2B_SECTION_DESCRIPTORS = [
    ("STAGE2B_ANALYSIS", "Stage 2-B Analysis", "stage2b_agent"),
]

STAGE3_SECTION_DESCRIPTORS = [
    ("STAGE3_PLAN", "Stage 3 Plan", "stage3_agent"),
]

STAGE4_SECTION_DESCRIPTORS = [
    ("LIVE_EXECUTION_PLAN", "Live Execution Plan", "system"),
    ("STAGE4_TOOL_CALLS", "Execution Log", "stage4_agent"),
    ("STAGE4_FINAL_ANSWER", "Final Answer to User", "stage4_agent"),
    ("STAGE4_FEEDBACK", "Feedback to Upstream", "stage4_agent"),
]

WATCHER_SECTION_DESCRIPTORS = [
    ("WATCHER_AUDIT", "Watcher Audit Report", "watcher_agent"),
    ("WATCHER_REALTIME", "Watcher Realtime Guidance", "watcher_agent"),
]


def _add_sections_from_markers(
    bridge: MemoryBridge,
    anchor_sections: Mapping[str, str],
    descriptors: Sequence[tuple[str, str, str]],
) -> None:
    for marker, header, source in descriptors:
        content = anchor_sections.get(marker)
        if content:
            bridge.add_section(header, content, source)


def create_stage1_context(
    finish_form_path: str | Path,
    objective: str,
    user_context: str | None = None,
) -> str:
    bridge = MemoryBridge()
    bridge.add_objective(objective)
    if user_context:
        bridge.add_user_context(user_context)

    anchor_sections = _load_anchor_sections(finish_form_path)
    descriptors = EXTERNAL_SECTION_DESCRIPTORS + STAGE1_SECTION_DESCRIPTORS
    _add_sections_from_markers(bridge, anchor_sections, descriptors)

    return bridge.build_context()


def create_stage2a_context(
    finish_form_path: str | Path,
    objective: str,
    context_snapshot: str | None = None,
) -> str:
    bridge = MemoryBridge()
    bridge.add_objective(objective)
    if context_snapshot:
        bridge.add_context_snapshot(context_snapshot)

    anchor_sections = _load_anchor_sections(finish_form_path)
    descriptors = (
        EXTERNAL_SECTION_DESCRIPTORS
        + STAGE1_SECTION_DESCRIPTORS
        + STAGE2A_SECTION_DESCRIPTORS
    )
    _add_sections_from_markers(bridge, anchor_sections, descriptors)

    return bridge.build_context()


def create_stage2b_context(
    finish_form_path: str | Path,
    objective: str,
    context_snapshot: str | None = None,
) -> str:
    bridge = MemoryBridge()
    bridge.add_objective(objective)
    if context_snapshot:
        bridge.add_context_snapshot(context_snapshot)

    anchor_sections = _load_anchor_sections(finish_form_path)
    descriptors = (
        EXTERNAL_SECTION_DESCRIPTORS
        + STAGE1_SECTION_DESCRIPTORS
        + STAGE2A_SECTION_DESCRIPTORS
        + STAGE2B_SECTION_DESCRIPTORS
    )
    _add_sections_from_markers(bridge, anchor_sections, descriptors)

    return bridge.build_context()


def create_stage3_context(
    finish_form_path: str | Path,
    objective: str,
    context_snapshot: str | None = None,
    attachments: Mapping[str, Any] | Sequence[Any] | str | None = None,
) -> str:
    bridge = MemoryBridge()
    bridge.add_objective(objective)
    if context_snapshot:
        bridge.add_context_snapshot(context_snapshot)
    if attachments:
        bridge.add_attachments(attachments)

    anchor_sections = _load_anchor_sections(finish_form_path)
    descriptors = (
        EXTERNAL_SECTION_DESCRIPTORS
        + STAGE1_SECTION_DESCRIPTORS
        + STAGE2A_SECTION_DESCRIPTORS
        + STAGE2B_SECTION_DESCRIPTORS
        + STAGE3_SECTION_DESCRIPTORS
    )
    _add_sections_from_markers(bridge, anchor_sections, descriptors)

    return bridge.build_context()


def create_stage4_context(
    finish_form_path: str | Path,
    objective: str,
    attachments: Mapping[str, Any] | Sequence[Any] | str | None = None,
    context_snapshot: str | None = None,
) -> str:
    bridge = MemoryBridge()
    bridge.add_objective(objective)
    if attachments:
        bridge.add_attachments(attachments)
    if context_snapshot:
        bridge.add_context_snapshot(context_snapshot)

    anchor_sections = _load_anchor_sections(finish_form_path)
    descriptors = (
        EXTERNAL_SECTION_DESCRIPTORS
        + STAGE1_SECTION_DESCRIPTORS
        + STAGE2A_SECTION_DESCRIPTORS
        + STAGE2B_SECTION_DESCRIPTORS
        + STAGE3_SECTION_DESCRIPTORS
        + STAGE4_SECTION_DESCRIPTORS
        + WATCHER_SECTION_DESCRIPTORS
    )
    _add_sections_from_markers(bridge, anchor_sections, descriptors)

    return bridge.build_context()


def create_watcher_audit_context(
    finish_form_path: str | Path,
    objective: str,
) -> str:
    """Build specialized audit context for Watcher Agent."""
    bridge = MemoryBridge()
    bridge.add_objective(objective)

    anchor_sections = _load_anchor_sections(finish_form_path)

    watcher_descriptors = [
        ("STAGE1_FAILURE_MODES", "Common Failure Modes", "stage1_agent"),
        ("STAGE2B_STRATEGY_SNAPSHOT", "Final Strategy Snapshot", "stage2b_agent"),
        ("STAGE3_EXECUTION_PLAN", "Execution Plan Overview", "stage3_agent"),
    ]

    _add_sections_from_markers(bridge, anchor_sections, watcher_descriptors)

    return bridge.build_context()


# =============================================================================
# Async versions of context creation functions
# These functions use aiofiles for non-blocking file I/O operations
# =============================================================================


async def create_stage1_context_async(
    finish_form_path: str | Path,
    objective: str,
    user_context: str | None = None,
) -> str:
    """Async version of create_stage1_context using non-blocking file I/O."""
    bridge = MemoryBridge()
    bridge.add_objective(objective)
    if user_context:
        bridge.add_user_context(user_context)

    anchor_sections = await _load_anchor_sections_async(finish_form_path)
    descriptors = EXTERNAL_SECTION_DESCRIPTORS + STAGE1_SECTION_DESCRIPTORS
    _add_sections_from_markers(bridge, anchor_sections, descriptors)

    return bridge.build_context()


async def create_stage2a_context_async(
    finish_form_path: str | Path,
    objective: str,
    context_snapshot: str | None = None,
) -> str:
    """Async version of create_stage2a_context using non-blocking file I/O."""
    bridge = MemoryBridge()
    bridge.add_objective(objective)
    if context_snapshot:
        bridge.add_context_snapshot(context_snapshot)

    anchor_sections = await _load_anchor_sections_async(finish_form_path)
    descriptors = (
        EXTERNAL_SECTION_DESCRIPTORS
        + STAGE1_SECTION_DESCRIPTORS
        + STAGE2A_SECTION_DESCRIPTORS
    )
    _add_sections_from_markers(bridge, anchor_sections, descriptors)

    return bridge.build_context()


async def create_stage2b_context_async(
    finish_form_path: str | Path,
    objective: str,
    context_snapshot: str | None = None,
) -> str:
    """Async version of create_stage2b_context using non-blocking file I/O."""
    bridge = MemoryBridge()
    bridge.add_objective(objective)
    if context_snapshot:
        bridge.add_context_snapshot(context_snapshot)

    anchor_sections = await _load_anchor_sections_async(finish_form_path)
    descriptors = (
        EXTERNAL_SECTION_DESCRIPTORS
        + STAGE1_SECTION_DESCRIPTORS
        + STAGE2A_SECTION_DESCRIPTORS
        + STAGE2B_SECTION_DESCRIPTORS
    )
    _add_sections_from_markers(bridge, anchor_sections, descriptors)

    return bridge.build_context()


async def create_stage3_context_async(
    finish_form_path: str | Path,
    objective: str,
    context_snapshot: str | None = None,
    attachments: Mapping[str, Any] | Sequence[Any] | str | None = None,
) -> str:
    """Async version of create_stage3_context using non-blocking file I/O."""
    bridge = MemoryBridge()
    bridge.add_objective(objective)
    if context_snapshot:
        bridge.add_context_snapshot(context_snapshot)
    if attachments:
        bridge.add_attachments(attachments)

    anchor_sections = await _load_anchor_sections_async(finish_form_path)
    descriptors = (
        EXTERNAL_SECTION_DESCRIPTORS
        + STAGE1_SECTION_DESCRIPTORS
        + STAGE2A_SECTION_DESCRIPTORS
        + STAGE2B_SECTION_DESCRIPTORS
        + STAGE3_SECTION_DESCRIPTORS
    )
    _add_sections_from_markers(bridge, anchor_sections, descriptors)

    return bridge.build_context()


async def create_stage4_context_async(
    finish_form_path: str | Path,
    objective: str,
    attachments: Mapping[str, Any] | Sequence[Any] | str | None = None,
    context_snapshot: str | None = None,
) -> str:
    """Async version of create_stage4_context using non-blocking file I/O."""
    bridge = MemoryBridge()
    bridge.add_objective(objective)
    if attachments:
        bridge.add_attachments(attachments)
    if context_snapshot:
        bridge.add_context_snapshot(context_snapshot)

    anchor_sections = await _load_anchor_sections_async(finish_form_path)
    descriptors = (
        EXTERNAL_SECTION_DESCRIPTORS
        + STAGE1_SECTION_DESCRIPTORS
        + STAGE2A_SECTION_DESCRIPTORS
        + STAGE2B_SECTION_DESCRIPTORS
        + STAGE3_SECTION_DESCRIPTORS
        + STAGE4_SECTION_DESCRIPTORS
        + WATCHER_SECTION_DESCRIPTORS
    )
    _add_sections_from_markers(bridge, anchor_sections, descriptors)

    return bridge.build_context()


async def create_watcher_audit_context_async(
    finish_form_path: str | Path,
    objective: str,
) -> str:
    """Async version of create_watcher_audit_context using non-blocking file I/O."""
    bridge = MemoryBridge()
    bridge.add_objective(objective)

    anchor_sections = await _load_anchor_sections_async(finish_form_path)

    watcher_descriptors = [
        ("STAGE1_FAILURE_MODES", "Common Failure Modes", "stage1_agent"),
        ("STAGE2B_STRATEGY_SNAPSHOT", "Final Strategy Snapshot", "stage2b_agent"),
        ("STAGE3_EXECUTION_PLAN", "Execution Plan Overview", "stage3_agent"),
    ]

    _add_sections_from_markers(bridge, anchor_sections, watcher_descriptors)

    return bridge.build_context()


__all__ = [
    "MemoryBridge",
    "ContextSection",
    # Sync versions
    "create_stage1_context",
    "create_stage2a_context",
    "create_stage2b_context",
    "create_stage3_context",
    "create_stage4_context",
    "create_watcher_audit_context",
    # Async versions
    "create_stage1_context_async",
    "create_stage2a_context_async",
    "create_stage2b_context_async",
    "create_stage3_context_async",
    "create_stage4_context_async",
    "create_watcher_audit_context_async",
]

