# -*- coding: utf-8 -*-
"""Tavily MCP integration helpers.

This module wraps the public Tavily MCP server described in the official
documentation `Tavily MCP Server <https://docs.tavily.com/documentation/mcp>`_,
providing a thin convenience layer for this project:

* ``TavilyMCPConfig``: configuration dataclass that reads ``TAVILY_*`` related
  environment variables and resolves the remote MCP endpoint.
* ``create_tavily_client``: factory that returns a configured
  :class:`~MCP._http_stateless_client.HttpStatelessClient` instance.
* ``discover_tavily_tool_catalog``: helper used by agents to surface the list
  of Tavily tools (name + description) as natural-language hints.
* ``get_tavily_tool``: utility that returns a callable MCP tool function by
  name (e.g. ``"search"``) so that higher level code can invoke the Tavily API
  without manually handling the MCP handshake each time.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
import os
from typing import Iterable, Literal, cast

import mcp.types

from ._http_stateless_client import HttpStatelessClient
from ._mcp_function import MCPToolFunction

DEFAULT_REMOTE_URL_TEMPLATE = "https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}"
DEFAULT_CLIENT_NAME = "tavily-mcp"
_VALID_TRANSPORTS = {"streamable_http", "sse"}


def _coerce_transport(value: str | None) -> Literal["streamable_http", "sse"]:
    normalized = (value or "streamable_http").strip().lower()
    if normalized not in _VALID_TRANSPORTS:
        raise ValueError(
            f"Unsupported Tavily MCP transport '{value}'. "
            "Accepted values: 'streamable_http', 'sse'.",
        )
    return cast(Literal["streamable_http", "sse"], normalized)


def _coerce_headers(raw: str | None) -> dict[str, str]:
    """Allow headers to be configured via JSON in ``TAVILY_MCP_HEADERS``."""

    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError(
            "TAVILY_MCP_HEADERS must be a valid JSON object of string pairs.",
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError("TAVILY_MCP_HEADERS must decode to a JSON object.")

    headers: dict[str, str] = {}
    for key, val in parsed.items():
        headers[str(key)] = str(val)
    return headers


@dataclass(slots=True)
class TavilyMCPConfig:
    """Configuration container for the Tavily MCP client."""

    api_key: str | None = None
    url: str | None = None
    name: str = DEFAULT_CLIENT_NAME
    transport: Literal["streamable_http", "sse"] = "streamable_http"
    timeout: float = 30.0
    sse_read_timeout: float = 60.0 * 5
    headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "TavilyMCPConfig":
        """Build config using ``TAVILY_*`` environment variables."""

        transport = _coerce_transport(os.getenv("TAVILY_MCP_TRANSPORT"))
        # 仅从环境变量读取，不再使用任何硬编码密钥
        api_key = os.getenv("TAVILY_API_KEY") or None
        return cls(
            api_key=api_key,
            url=os.getenv("TAVILY_MCP_URL"),
            name=os.getenv("TAVILY_MCP_NAME", DEFAULT_CLIENT_NAME),
            transport=transport,
            timeout=float(os.getenv("TAVILY_MCP_TIMEOUT", "30") or 30),
            sse_read_timeout=float(os.getenv("TAVILY_MCP_SSE_TIMEOUT", str(60 * 5)) or (60 * 5)),
            headers=_coerce_headers(os.getenv("TAVILY_MCP_HEADERS")),
        )

    def resolve_url(self) -> str:
        """Resolved MCP endpoint URL, falling back to Tavily hosted remote server."""

        if self.url:
            return self.url

        if not self.api_key:
            raise ValueError(
                "Tavily MCP server URL is not configured. Either provide `url` "
                "explicitly or set TAVILY_API_KEY to use Tavily's hosted remote server.",
            )

        return DEFAULT_REMOTE_URL_TEMPLATE.format(api_key=self.api_key)


def create_tavily_client(config: TavilyMCPConfig | None = None) -> HttpStatelessClient:
    """Return a configured HTTP MCP client for Tavily."""

    cfg = config or TavilyMCPConfig.from_env()
    url = cfg.resolve_url()
    headers = cfg.headers or None

    return HttpStatelessClient(
        name=cfg.name,
        transport=cfg.transport,
        url=url,
        headers=headers,
        timeout=cfg.timeout,
        sse_read_timeout=cfg.sse_read_timeout,
    )


async def discover_tavily_tool_catalog(
    config: TavilyMCPConfig | None = None,
) -> list[str]:
    """Return a list of human-readable Tavily tool descriptions.

    Each entry is represented as ``"<name>: <description>"``.
    """

    client = create_tavily_client(config=config)
    tools = await client.list_tools()
    catalog: list[str] = []
    for tool in tools:
        description = tool.description or ""
        description = description.strip()
        catalog.append(f"{tool.name}: {description}" if description else tool.name)
    return catalog


async def get_tavily_tool(
    tool_name: str,
    *,
    config: TavilyMCPConfig | None = None,
    wrap_tool_result: bool = True,
) -> MCPToolFunction:
    """Fetch an :class:`MCPToolFunction` for the given Tavily tool name."""

    client = create_tavily_client(config=config)
    return await client.get_callable_function(
        func_name=tool_name,
        wrap_tool_result=wrap_tool_result,
    )


async def get_default_tavily_search_tool(
    *,
    config: TavilyMCPConfig | None = None,
    wrap_tool_result: bool = True,
    search_tool_name: str | None = None,
) -> MCPToolFunction:
    """Convenience wrapper returning the primary Tavily ``search`` tool."""

    if not search_tool_name:
        tools = await list_tavily_tools(config=config)
        for tool in tools:
            if "search" in tool.name.lower():
                search_tool_name = tool.name
                break

    if not search_tool_name:
        raise ValueError("Unable to detect a Tavily search tool in the catalog.")

    return await get_tavily_tool(
        search_tool_name,
        config=config,
        wrap_tool_result=wrap_tool_result,
    )


async def list_tavily_tools(
    *,
    config: TavilyMCPConfig | None = None,
) -> Iterable[mcp.types.Tool]:
    """Expose the raw :class:`~mcp.types.Tool` list for advanced workflows."""

    client = create_tavily_client(config=config)
    return await client.list_tools()


__all__ = [
    "TavilyMCPConfig",
    "create_tavily_client",
    "discover_tavily_tool_catalog",
    "get_default_tavily_search_tool",
    "get_tavily_tool",
    "list_tavily_tools",
]

