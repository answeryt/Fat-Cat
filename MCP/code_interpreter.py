# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import sys
import traceback
from contextlib import asynccontextmanager, redirect_stdout, redirect_stderr
from dataclasses import dataclass
from typing import AsyncIterator, Any


@dataclass
class ToolResponse:
    content: list[TextContent]


@dataclass
class TextContent:
    text: str

class PythonExecutor:
    def __init__(self):
        
        self.globals = {} 
        
    async def __call__(self, code: str) -> ToolResponse:
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            sys.stdout = output_buffer
            sys.stderr = error_buffer
            
            exec(code, self.globals)
            
            stdout_text = output_buffer.getvalue()
            stderr_text = error_buffer.getvalue()
            
            result_text = ""
            if stdout_text:
                result_text += stdout_text
            if stderr_text:
                result_text += f"\n[Error Output]: {stderr_text}"
            
            if not result_text:
                result_text = "Code executed successfully with no output"
            
            return ToolResponse(content=[TextContent(text=result_text)])
            
        except Exception as e:
            # 加上 Traceback 有助于 Agent 自我纠错
            error_msg = f"Execution Error: {str(e)}\n{traceback.format_exc()}"
            return ToolResponse(content=[TextContent(text=error_msg)])
        
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

@asynccontextmanager
async def code_interpreter_tool(
    tool_name: str,
    *,
    config: Any = None,
    wrap_tool_result: bool = True,
) -> AsyncIterator[PythonExecutor]:
    executor = PythonExecutor()
    try:
        yield executor
    finally:
        pass


__all__ = [
    "code_interpreter_tool",
]
