# -*- coding: utf-8 -*-
"""OpenAI Chat Completions API model wrapper."""

from __future__ import annotations

import inspect
import json
from typing import Any, AsyncGenerator, Literal, Type

from pydantic import BaseModel, ValidationError

from ._model_base import ChatModelBase
from ._model_response import ChatResponse, ResponseBlock
from ._model_usage import ChatUsage
from _logging import logger


class OpenAIChatModel(ChatModelBase):
    """Lightweight wrapper around an OpenAI-compatible Chat Completions API."""

    def __init__(
        self,
        model_name: str = "kimi-k2-250905",
        api_key: str | None = None,
        stream: bool = False,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        organization: str | None = None,
        client_args: dict[str, Any] | None = None,
        generate_kwargs: dict[str, Any] | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("OpenAI API key must be provided.")

        try:
            from openai import AsyncOpenAI  # type: ignore import-not-found
        except ImportError as exc:  # pragma: no cover - environment guard
            raise ImportError(
                "未找到 openai 包，请运行 `pip install openai>=1.0` 后重试。",
            ) from exc

        super().__init__(model_name=model_name, stream=bool(stream))

        client_kwargs: dict[str, Any] = dict(client_args or {})
        if organization:
            client_kwargs.setdefault("organization", organization)

        self._client = AsyncOpenAI(
            api_key=api_key,
            **client_kwargs,
        )
        self._generate_kwargs = dict(generate_kwargs or {})
        self.reasoning_effort = reasoning_effort

    async def __call__(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: Literal["auto", "none", "any", "required"] | str | None = None,
        structured_model: Type[BaseModel] | None = None,
        payload_contract: Any | None = None,
        **kwargs: Any,
    ) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        if not isinstance(messages, list):
            raise TypeError("messages must be a list of role/content dictionaries.")

        if tool_choice and tools:
            self._validate_tool_choice(tool_choice, tools)

        if structured_model is not None and (tools or tool_choice):
            logger.warning(
                "提供了 structured_model，工具相关参数将被忽略以保证结构化输出。",
            )
            tools = None
            tool_choice = None

        payload = self._build_request_payload(
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            structured_model=structured_model,
            extra_kwargs=kwargs,
        )

        if self.stream:
            async def completion_stream() -> AsyncGenerator[ChatResponse, None]:
                stream = await self._client.chat.completions.create(**payload)
                final_chunks: list[str] = []
                usage = None
                async for chunk in stream:
                    choices = chunk.choices or []
                    if choices:
                        delta = getattr(choices[0], "delta", None)
                        if delta and getattr(delta, "content", None):
                            final_chunks.append(delta.content)
                    if getattr(chunk, "usage", None):
                        usage = chunk.usage
                aggregated = {
                    "choices": [{"message": {"content": "".join(final_chunks)}}],
                    "usage": usage,
                }
                chat_response = self._parse_completion(
                    aggregated,
                    structured_model=structured_model,
                )
                chat_response = self._attach_contract_payload(
                    chat_response,
                    payload_contract=payload_contract,
                )
                yield chat_response

            return completion_stream()

        completion = await self._client.chat.completions.create(**payload)
        chat_response = self._parse_completion(
            completion,
            structured_model=structured_model,
        )
        chat_response = self._attach_contract_payload(
            chat_response,
            payload_contract=payload_contract,
        )
        return chat_response

    async def aclose(self) -> None:
        close = getattr(self._client, "close", None)
        if close is None:
            close = getattr(self._client, "aclose", None)
        if close is None:
            return
        result = close()
        if inspect.isawaitable(result):
            await result

    def _build_request_payload(
        self,
        *,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        tool_choice: Literal["auto", "none", "any", "required"] | str | None,
        structured_model: Type[BaseModel] | None,
        extra_kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        formatted_messages = [
            self._format_message(message) for message in messages
        ]

        cleaned_kwargs = dict(extra_kwargs or {})
        if "stream" in cleaned_kwargs:
            logger.warning(
                "通过调用参数传入 stream 已被忽略，请在初始化模型时设置。",
            )
            cleaned_kwargs.pop("stream")

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": formatted_messages,
            "stream": self.stream,
            **self._generate_kwargs,
            **cleaned_kwargs,
        }

        if self.reasoning_effort and "reasoning" not in payload:
            payload["reasoning"] = {"effort": self.reasoning_effort}

        if structured_model is not None:
            payload["response_format"] = self._build_response_format(structured_model)
        elif tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = self._normalize_tool_choice(
                    tool_choice,
                )
        elif tool_choice:
            logger.warning(
                "tool_choice=%s 被忽略，因为未提供 tools 参数。",
                tool_choice,
            )

        return payload

    def _format_message(self, message: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(message, dict):
            raise TypeError("Each message must be a dictionary.")

        role = message.get("role")
        if not isinstance(role, str) or not role.strip():
            raise ValueError("Each message requires a non-empty 'role' string.")

        raw_content = message.get("content")
        if isinstance(raw_content, str) or raw_content is None:
            content = raw_content or ""
        elif isinstance(raw_content, list):
            content = raw_content
        elif isinstance(raw_content, dict):
            content = raw_content
        else:
            content = json.dumps(raw_content, ensure_ascii=False)

        formatted: dict[str, Any] = {
            "role": role,
            "content": content,
        }
        if "name" in message:
            formatted["name"] = message["name"]
        return formatted

    def _build_response_format(
        self,
        structured_model: Type[BaseModel],
    ) -> dict[str, Any]:
        schema = structured_model.model_json_schema()
        return {
            "type": "json_schema",
            "json_schema": {
                "name": structured_model.__name__,
                "schema": schema,
                "strict": True,
            },
        }

    def _normalize_tool_choice(
        self,
        tool_choice: Literal["auto", "none", "any", "required"] | str,
    ) -> str | dict[str, Any]:
        if tool_choice in {"auto", "none"}:
            return tool_choice
        if tool_choice in {"any", "required"}:
            logger.warning(
                "Chat Completions API 不支持 tool_choice=%s，已回退为 'auto'。",
                tool_choice,
            )
            return "auto"
        return {
            "type": "function",
            "function": {"name": tool_choice},
        }

    def _parse_completion(
        self,
        completion: Any,
        *,
        structured_model: Type[BaseModel] | None,
    ) -> ChatResponse:
        if hasattr(completion, "model_dump"):
            data: dict[str, Any] = completion.model_dump()
        elif isinstance(completion, dict):
            data = completion
        else:  # pragma: no cover - defensive fallback
            raise TypeError("Unexpected completion type from OpenAI client.")

        blocks: list[ResponseBlock] = []
        tool_calls: list[dict[str, Any]] = []

        # 处理Chat Completions API响应格式
        choices = data.get("choices", [])
        if choices:
            choice = choices[0]
            message = choice.get("message", {})
            
            # 提取文本内容
            content = message.get("content")
            if content:
                blocks.append(ResponseBlock(type="text", text=content))
            
            # 提取工具调用
            if message.get("tool_calls"):
                tool_calls.extend(message["tool_calls"])

        if not blocks:
            # 回退处理：尝试从其他可能的位置提取文本
            text_fallback = self._extract_output_text(data)
            if text_fallback:
                blocks.append(ResponseBlock(type="text", text=text_fallback))

        usage_data = data.get("usage") or {}
        usage = None
        if usage_data:
            usage = ChatUsage(
                input_tokens=usage_data.get("input_tokens"),
                output_tokens=usage_data.get("output_tokens"),
                total_tokens=usage_data.get("total_tokens"),
            )

        metadata: dict[str, Any] = {}
        if tool_calls:
            metadata["tool_calls"] = tool_calls

        structured_payload = None
        if structured_model is not None and blocks:
            aggregated_text = "".join(
                block.as_text() for block in blocks if block.type == "text"
            )
            if aggregated_text:
                try:
                    structured_obj = structured_model.model_validate_json(
                        aggregated_text,
                    )
                    structured_payload = structured_obj.model_dump()
                except (ValidationError, json.JSONDecodeError) as exc:
                    logger.warning(
                        "Structured output 解析失败，将返回原始文本。错误：%s",
                        exc,
                    )

        if structured_payload is not None:
            metadata["structured_output"] = structured_payload

        if not metadata:
            metadata = None

        chat_response = ChatResponse(
            content=tuple(blocks),
            usage=usage,
            raw=data,
            metadata=metadata,
        )

        return chat_response

    @staticmethod
    def _coerce_block_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)

    @staticmethod
    def _extract_output_text(data: dict[str, Any]) -> str:
        texts: list[str] = []
        for output in data.get("output") or []:
            if output.get("type") != "message":
                continue
            for content in output.get("content") or []:
                if content.get("type") in {"output_text", "text"}:
                    text_value = content.get("text")
                    if isinstance(text_value, str) and text_value:
                        texts.append(text_value)
        return "".join(texts)

