# -*- coding: utf-8 -*-
"""Simple usage statistics container."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ChatUsage:
    """The usage of a chat model API invocation."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    time: float | None = None
