# -*- coding: utf-8 -*-
"""Minimal DeepSeek chat model implementation."""

from __future__ import annotations

import asyncio
from typing import Any, Literal

import httpx

from ._model_base import ChatModelBase
from ._model_response import ChatResponse, ResponseBlock
from ._model_usage import ChatUsage


class DeepSeekChatModel(ChatModelBase):
    """Lightweight DeepSeek client used by the metacognitive agent."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        stream: bool = False,
        base_url: str = "https://api.deepseek.com",
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        generate_kwargs: dict[str, Any] | None = None,
        timeout: float = 60.0,
        max_retries: int = 2,
        retry_base_delay: float = 1.0,
        retry_backoff_factor: float = 2.0,
    ) -> None:
        if not api_key:
            raise ValueError("DeepSeek API key must be provided.")

        super().__init__(model_name=model_name, stream=bool(stream))
        if stream:
            raise NotImplementedError("Streaming mode is not supported yet.")

        self._api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.reasoning_effort = reasoning_effort
        self.generate_kwargs = generate_kwargs or {}
        self.timeout = timeout
        self._endpoint = f"{self.base_url}/chat/completions"
        self._max_retries = max(0, int(max_retries))
        self._retry_base_delay = max(0.0, float(retry_base_delay))
        backoff = float(retry_backoff_factor)
        self._retry_backoff_factor = backoff if backoff >= 1.0 else 1.0
        self._retry_exceptions = (httpx.TimeoutException, httpx.NetworkError)

    async def __call__(
        self,
        messages: list[dict[str, Any]],
        structured_model: Any | None = None,
        payload_contract: Any | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        if structured_model is not None:
            raise NotImplementedError("structured_model is not supported.")

        if not isinstance(messages, list):
            raise TypeError("messages must be a list of role/content dicts.")

        # 参数保留用于兼容旧接口，当前实现不再处理契约。
        _ = payload_contract

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            **self.generate_kwargs,
            **kwargs,
        }

        if self.reasoning_effort and "reasoning_effort" not in payload:
            payload["reasoning_effort"] = self.reasoning_effort

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response: httpx.Response | None = None
            last_exc: Exception | None = None
            for attempt in range(self._max_retries + 1):
                try:
                    response = await client.post(
                        self._endpoint,
                        headers=headers,
                        json=payload,
                    )
                except self._retry_exceptions as exc:
                    last_exc = exc
                    if attempt >= self._max_retries:
                        raise RuntimeError(
                            f"DeepSeek API request failed after {attempt + 1} attempts: {exc}"
                        ) from exc
                    await self._sleep_before_retry(attempt)
                    continue

                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    detail = exc.response.text
                    raise RuntimeError(
                        f"DeepSeek API error ({exc.response.status_code}): {detail}",
                    ) from exc

                break
            else:  # pragma: no cover - defensive fallback
                raise RuntimeError(
                    f"DeepSeek API request failed after {self._max_retries + 1} attempts."
                ) from last_exc

            if response is None:  # pragma: no cover - defensive fallback
                raise RuntimeError("DeepSeek API did not return a response.")

        data = response.json()
        blocks: list[ResponseBlock] = []

        first_choice = (data.get("choices") or [{}])[0]
        message = first_choice.get("message") or {}
        reasoning = message.get("reasoning_content")
        content = message.get("content")

        if reasoning:
            blocks.append(ResponseBlock(type="thinking", thinking=reasoning))

        if isinstance(content, str):
            blocks.append(ResponseBlock(type="text", text=content))
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        blocks.append(
                            ResponseBlock(type="text", text=item.get("text")),
                        )
                    elif item.get("type") == "reasoning":
                        blocks.append(
                            ResponseBlock(
                                type="thinking",
                                thinking=item.get("text"),
                            ),
                        )

        usage_data = data.get("usage") or {}
        usage = ChatUsage(
            input_tokens=usage_data.get("prompt_tokens"),
            output_tokens=usage_data.get("completion_tokens"),
            total_tokens=usage_data.get("total_tokens"),
        )

        response = ChatResponse(
            content=tuple(blocks),
            usage=usage,
            raw=data,
        )

        return response

    async def _sleep_before_retry(self, attempt: int) -> None:
        """Sleep before the next retry attempt based on exponential backoff."""

        if self._retry_base_delay <= 0:
            return

        delay = self._retry_base_delay * (self._retry_backoff_factor ** attempt)
        if delay <= 0:
            return
        await asyncio.sleep(delay)

