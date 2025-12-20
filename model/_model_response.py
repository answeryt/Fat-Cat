# -*- coding: utf-8 -*-
"""Lightweight response objects for chat models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Sequence

from ._model_usage import ChatUsage


@dataclass(slots=True)
class ResponseBlock:
    """Single block of model output.

    Only ``text`` and ``thinking`` block types are supported for now,
    which are sufficient for the metacognitive agent.
    """

    type: Literal["text", "thinking"]
    text: str | None = None
    thinking: str | None = None

    def as_text(self) -> str:
        """Return the textual content regardless of block type."""

        if self.type == "thinking":
            return (self.thinking or "").strip()
        return (self.text or "").strip()


@dataclass(slots=True)
class ChatResponse:
    """Minimal chat response container used by the local agent."""

    content: Sequence[ResponseBlock] = field(default_factory=tuple)
    usage: ChatUsage | None = None
    raw: dict | None = None
    metadata: dict | None = None
    payload: Any | None = None
