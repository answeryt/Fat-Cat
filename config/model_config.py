# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(slots=True)
class ModelConfig:
    api_key: str | None = None
    base_url: str | None = None
    organization: str | None = None
    model_name: str = "kimi-k2-250905"
    stream: bool = False
    reasoning_effort: Literal["low", "medium", "high"] | None = None
    client_args: dict[str, Any] = field(default_factory=dict)
    generate_kwargs: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls, **overrides: Any) -> ModelConfig:
        base_config = cls(
            api_key=(
                os.getenv("OPENAI_API_KEY")
                or os.getenv("KIMI_API_KEY")
                or os.getenv("DEEPSEEK_API_KEY")
            ),
            base_url=os.getenv(
                "MODEL_BASE_URL",
                "https://ark.cn-beijing.volces.com/api/v3",
            ),
            model_name=os.getenv("MODEL_NAME", "kimi-k2-250905"),
        )
        for key, value in overrides.items():
            if hasattr(base_config, key):
                setattr(base_config, key, value)
        return base_config

    def validate(self) -> None:
        if not self.api_key:
            raise ValueError(
                "API key is required. Set via OPENAI_API_KEY, "
                "KIMI_API_KEY, or DEEPSEEK_API_KEY environment variable."
            )


__all__ = ["ModelConfig"]

