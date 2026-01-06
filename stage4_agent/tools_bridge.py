# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import inspect
import io
import os
import sys
import textwrap
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Coroutine

# 导入沙箱模块
from .sandboxed_code_interpreter import CodeSandbox

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str | None = None


class ToolRegistry:
    _instance = None
    _tools: dict[str, Callable] = {}
    _tool_docs: dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._tools = {}
            cls._tool_docs = {}
        return cls._instance

    def register(self, func: Callable) -> Callable:
        name = func.__name__
        self._tools[name] = func
        self._tool_docs[name] = inspect.getdoc(func) or ""
        return func

    def get(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())


registry = ToolRegistry()


def tool(func: Callable) -> Callable:
    registry.register(func)
    return func


class ToolsBridge:
    def __init__(self):
        self._tavily_tool = None
        self._tavily_initialized = False
        # 持久化的代码执行命名空间，跨多次 code_interpreter 调用保持状态
        self._interpreter_globals: dict[str, Any] = {"__builtins__": __builtins__}
        
        # 初始化沙箱
        sandbox_timeout = int(os.getenv("SANDBOX_TIMEOUT", "30"))
        sandbox_memory = int(os.getenv("SANDBOX_MEMORY_MB", "256"))
        isolation_level = os.getenv("SANDBOX_ISOLATION_LEVEL", "high")
        
        self.code_sandbox = CodeSandbox(
            timeout=sandbox_timeout,
            memory_limit_mb=sandbox_memory
        )
        self.isolation_level = isolation_level
        self.sandbox_execution_count = 0

    def reset_interpreter(self):
        """重置代码解释器的命名空间，清除所有已定义的变量和函数"""
        self._interpreter_globals = {"__builtins__": __builtins__}

    def _run_async(self, coro: Coroutine) -> Any:
        try:
            asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            return asyncio.run(coro)

    async def _init_tavily(self):
        if self._tavily_initialized:
            return
        try:
            from MCP.tavily import get_default_tavily_search_tool
            self._tavily_tool = await get_default_tavily_search_tool(wrap_tool_result=True)
        except Exception as e:
            self._tavily_tool = None
            print(f"[ToolsBridge] Tavily init failed: {e}")
        self._tavily_initialized = True

    def call_tool(self, tool_name: str, **kwargs) -> ToolResult:
        tool_func = registry.get(tool_name)
        if tool_func is None:
            return ToolResult(success=False, output="", error=f"Unknown tool: {tool_name}. Available: {registry.list_tools()}")

        try:
            if asyncio.iscoroutinefunction(tool_func):
                result = self._run_async(tool_func(self, **kwargs))
            else:
                result = tool_func(self, **kwargs)
            if isinstance(result, ToolResult):
                return result
            return ToolResult(success=True, output=str(result))
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool invocation error: {type(e).__name__}: {e}\nArgs: {kwargs}\n--- Traceback ---\n{traceback.format_exc()}",
            )


@tool
def web_search(
    bridge: ToolsBridge,
    query: str,
    max_results: int = 5,
    provider: str = "auto",
    fallback_queries: str | list[str] | None = None,
    min_results: int = 1,
) -> ToolResult:
    """统一网络搜索工具，支持多层查询（先宽后窄）、排序去重、自动降级。

    - query: 主查询
    - fallback_queries: 可选，当前查询不足 min_results 时按顺序尝试（字符串或列表）
    - min_results: 认为"有结果"的最低行数（粗略），低于则继续尝试后备查询
    """

    async def _do_search():
        queries: list[str] = [query]
        if fallback_queries:
            if isinstance(fallback_queries, str):
                queries.append(fallback_queries)
            else:
                queries.extend(list(fallback_queries))

        attempts_output: list[str] = []
        for idx, q in enumerate(queries, 1):
            selected_provider = provider.lower()
            if selected_provider == "auto":
                if os.getenv("FIRECRAWL_API_KEY"):
                    selected_provider = "firecrawl"
                elif os.getenv("TAVILY_API_KEY"):
                    selected_provider = "tavily"
                else:
                    selected_provider = "tavily"

            if selected_provider == "firecrawl":
                res = await _search_firecrawl(q, max_results)
            else:
                res = await _search_tavily(bridge, q, max_results)

            if not res.success:
                return res

            non_empty_lines = [l for l in res.output.splitlines() if l.strip()]
            attempts_output.append(f"[Attempt {idx}] query: {q}\n{res.output}")

            if len(non_empty_lines) >= max(min_results, 1):
                return ToolResult(success=True, output="\n\n".join(attempts_output))

        return ToolResult(success=True, output="\n\n".join(attempts_output))

    async def _search_tavily(bridge: ToolsBridge, query: str, max_results: int) -> ToolResult:
        await bridge._init_tavily()
        if bridge._tavily_tool is None:
            return ToolResult(success=False, output="", error="Tavily not available. Check TAVILY_API_KEY.")
        try:
            result = await bridge._tavily_tool(query=query, max_results=max_results)
            content = getattr(result, "content", str(result))

            if isinstance(content, list):
                seen = set()
                deduped = []
                for item in sorted(content, key=lambda x: str(x.get("url", ""))):
                    url = str(item.get("url", "")).strip().lower()
                    title = str(item.get("title", "")).strip().lower()
                    key = (url, title)
                    if key in seen:
                        continue
                    seen.add(key)
                    deduped.append(item)
                content = deduped

            content_str = str(content).strip()
            if not content_str or content_str in ("[]", "{}", "None", "null"):
                return ToolResult(
                    success=True,
                    output=f"[Zero Results] Tavily API responded successfully but returned no results for query: '{query}'\n"
                           f"Possible reasons: query too specific, topic too niche, or no indexed content matches.\n"
                           f"Suggestions: try broader keywords, different phrasing, or alternative search terms."
                )
            return ToolResult(success=True, output=content_str)
        except Exception as e:
            return ToolResult(
                success=False, output="",
                error=f"Tavily API Error: {type(e).__name__}: {e}\n--- Traceback ---\n{traceback.format_exc()}"
            )

    async def _search_firecrawl(query: str, limit: int) -> ToolResult:
        try:
            from MCP.firecrawl import create_firecrawl_client
            client = create_firecrawl_client()
            result = await client.search(query=query, limit=limit)
            if not result.success:
                return ToolResult(success=False, output="", error=f"Firecrawl API returned error: {result.error}")
            if not result.data:
                return ToolResult(
                    success=True,
                    output=f"[Zero Results] Firecrawl API responded successfully but returned no results for query: '{query}'\n"
                           f"Possible reasons: query too specific, topic too niche, or no indexed content matches.\n"
                           f"Suggestions: try broader keywords, different phrasing, or alternative search terms."
                )
            seen = set()
            sorted_items = sorted(result.data, key=lambda x: str(x.get("url", "")))

            output_lines = []
            idx = 0
            for item in sorted_items:
                title = item.get("title", "No title")
                url = item.get("url", "")
                key = (url.strip().lower(), title.strip().lower())
                if key in seen:
                    continue
                seen.add(key)
                idx += 1
                description = item.get("description", item.get("markdown", ""))[:200]
                output_lines.append(f"{idx}. {title}")
                output_lines.append(f"   URL: {url}")
                output_lines.append(f"   {description}")
            return ToolResult(success=True, output="\n".join(output_lines))
        except ValueError as e:
            return ToolResult(
                success=False, output="",
                error=f"Firecrawl config error: {type(e).__name__}: {e}\n--- Traceback ---\n{traceback.format_exc()}"
            )
        except Exception as e:
            return ToolResult(
                success=False, output="",
                error=f"Firecrawl API Error: {type(e).__name__}: {e}\n--- Traceback ---\n{traceback.format_exc()}"
            )

    return bridge._run_async(_do_search())


@tool
def web_scrape(bridge: ToolsBridge, url: str, format: str = "markdown") -> ToolResult:
    """网页抓取工具，提取单个网页内容转为Markdown（仅Firecrawl支持）"""
    async def _do_scrape():
        try:
            from MCP.firecrawl import create_firecrawl_client
            client = create_firecrawl_client()
            # Firecrawl 场景下强制使用 markdown，避免返回 JSON 结构导致后续解析困难
            formats = ["markdown"]
            result = await client.scrape(url=url, formats=formats)
            if not result.success:
                return ToolResult(success=False, output="", error=f"Firecrawl scrape returned error: {result.error}")
            if result.data:
                data = result.data[0]
                content = data.get("markdown", data.get("content", str(data)))
                title = data.get("metadata", {}).get("title", "")
                if not content or not content.strip():
                    return ToolResult(
                        success=True,
                        output=f"[Empty Content] Firecrawl successfully accessed '{url}' but extracted no text content.\n"
                               f"Possible reasons: page requires JavaScript rendering, content behind login, "
                               f"anti-scraping protection, or page is mostly images/media.\n"
                               f"Suggestions: try a different URL, or use web_search to find alternative sources."
                    )
                output = f"Title: {title}\n\n{content}" if title else content
                return ToolResult(success=True, output=output[:5000])
            return ToolResult(
                success=True,
                output=f"[No Data] Firecrawl returned empty data array for '{url}'.\n"
                       f"The page may be inaccessible, blocked, or have no extractable content."
            )
        except ValueError as e:
            return ToolResult(
                success=False, output="",
                error=f"Firecrawl config error: {type(e).__name__}: {e}\nSet FIRECRAWL_API_KEY.\n--- Traceback ---\n{traceback.format_exc()}"
            )
        except Exception as e:
            return ToolResult(
                success=False, output="",
                error=f"Firecrawl scrape error: {type(e).__name__}: {e}\n--- Traceback ---\n{traceback.format_exc()}"
            )

    return bridge._run_async(_do_scrape())


@tool
def code_interpreter(bridge: ToolsBridge, code: str) -> ToolResult:
    """Python代码执行工具，用于计算、数据处理和验证。
    
    使用沙箱环境执行代码，确保安全性。
    注意：持久化命名空间功能受限，仅保存安全结果。
    """
    output_buffer = io.StringIO()
    error_buffer = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr

    try:
        sys.stdout = output_buffer
        sys.stderr = error_buffer

        clean_code = textwrap.dedent(code or "").strip()
        if not clean_code:
            return ToolResult(success=False, output="", error="code_interpreter received empty code snippet")

        # 使用沙箱执行代码，替代危险的 exec()
        bridge.sandbox_execution_count += 1
        
        sandbox_result = bridge.code_sandbox.execute(
            code=clean_code,
            isolation_level=bridge.isolation_level
        )
        
        if not sandbox_result["success"]:
            return ToolResult(
                success=False, 
                output="", 
                error=f"沙箱执行失败: {sandbox_result['error']}\n方法: {sandbox_result.get('method', 'unknown')}"
            )
        
        # 获取沙箱输出
        sandbox_output = sandbox_result.get("output", "")
        
        stdout_text = output_buffer.getvalue()
        stderr_text = error_buffer.getvalue()

        # 构建输出
        output_parts = []
        
        # 添加沙箱执行信息
        output_parts.append(f"[沙箱执行 - {sandbox_result.get('method', 'unknown')}]")
        
        # 添加沙箱输出
        if sandbox_output.strip():
            output_parts.append(sandbox_output.strip())
            
        # 添加本地缓冲区输出（如果有）
        if stdout_text.strip():
            output_parts.append(f"本地输出: {stdout_text.strip()}")
            
        if stderr_text.strip():
            output_parts.append(f"本地错误: {stderr_text.strip()}")

        final_output = "\n".join(output_parts) if output_parts else "代码已执行（无输出）"
        
        return ToolResult(success=True, output=final_output)

    except Exception as e:
        # 错误处理
        stdout_text = output_buffer.getvalue()
        stderr_text = error_buffer.getvalue()
        error_parts = [
            f"沙箱框架异常: {type(e).__name__}: {e}",
            f"\n--- Traceback ---\n{traceback.format_exc()}",
        ]
        if stdout_text.strip():
            error_parts.insert(0, f"--- Stdout before error ---\n{stdout_text.strip()}")
        if stderr_text.strip():
            error_parts.append(f"--- Stderr ---\n{stderr_text.strip()}")
        return ToolResult(success=False, output="", error="\n".join(error_parts))
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


@tool
def calculate(bridge: ToolsBridge, expression: str) -> ToolResult:
    """数学计算工具，用于安全的数学表达式求值"""
    try:
        # 使用沙箱执行数学表达式
        sandbox_result = bridge.code_sandbox.execute(
            code=f"_result_ = {expression}",
            isolation_level="low"  # 数学计算用低隔离级别
        )
        
        if sandbox_result["success"]:
            output = sandbox_result.get("output", "")
            # 提取计算结果
            import re
            numbers = re.findall(r'-?\d+\.?\d*', output)
            if numbers:
                return ToolResult(success=True, output=numbers[0])
            return ToolResult(success=True, output=output[:200])
        else:
            return ToolResult(
                success=False, output="",
                error=f"计算错误: {sandbox_result.get('error', '未知错误')}"
            )
    except Exception as e:
        return ToolResult(
            success=False, output="",
            error=f"Calculate框架错误: {type(e).__name__}: {e}\n--- Traceback ---\n{traceback.format_exc()}"
        )


def create_tools_bridge() -> ToolsBridge:
    return ToolsBridge()


__all__ = [
    "ToolsBridge",
    "ToolResult",
    "ToolRegistry",
    "tool",
    "registry",
    "create_tools_bridge",
    "web_search",
    "web_scrape",
    "code_interpreter",
    "calculate",
]
