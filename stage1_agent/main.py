# -*- coding: utf-8 -*-
"""Command-line interface for running MetacognitiveAnalysisAgent interactively."""
from __future__ import annotations

import argparse
import asyncio
import os
import re
from getpass import getpass
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv

# 导入模板生成代理
import sys as sys_module
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys_module.path:
    sys_module.path.insert(0, PARENT_DIR)

from Document_Checking.template_generation import TemplateGenerationAgent, TemplateGenerationConfig
from tool_catalog import load_tool_catalog

try:
    from .Metacognitive_Analysis_agent import MetacognitiveAnalysisAgent
except ImportError:
    import sys
    import os

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    if CURRENT_DIR not in sys.path:
        sys.path.insert(0, CURRENT_DIR)

    from Metacognitive_Analysis_agent import MetacognitiveAnalysisAgent

from config import ModelConfig

EXIT_COMMANDS = {"exit", "quit", "q"}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
DEFAULT_TOOL_CATALOG = load_tool_catalog()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="metacognitive-agent",
        description="Interactively run the MetacognitiveAnalysisAgent backed by DeepSeek.",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        help="DeepSeek API key (falls back to DEEPSEEK_API_KEY environment variable).",
    )
    parser.add_argument(
        "--model",
        default="deepseek-chat",
        help="DeepSeek model name (default: deepseek-chat).",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Enable streaming responses (default: disabled).",
    )
    parser.add_argument(
        "--base-url",
        default="https://api.deepseek.com",
        help="DeepSeek API base URL (default: https://api.deepseek.com).",
    )
    parser.add_argument(
        "--reasoning-effort",
        choices=["low", "medium", "high"],
        default="medium",
        help="Reasoning effort level for the DeepSeek model (default: medium).",
    )
    parser.add_argument(
        "--system-prompt",
        dest="system_prompt",
        help="Optional custom system prompt. If omitted, the default prompt from reasoner.md is used.",
    )
    return parser.parse_args()


def _ensure_api_key(cli_api_key: str | None) -> str:
    api_key = cli_api_key or os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        return api_key

    while not api_key:
        api_key = getpass("请输入 DeepSeek API Key (输入后按回车): ").strip()
    return api_key


def _print_banner() -> None:
    print("=" * 72)
    print("Metacognitive Analysis Agent (DeepSeek)")
    print("输入 'exit' / 'quit' / 'q' 退出程序")
    print("提示: 留空可跳过可选字段")
    print("=" * 72)


def _collect_tool_catalog(raw: str) -> list[str] | None:
    if not raw.strip():
        return None
    tools: list[str] = []
    for entry in raw.split(","):
        cleaned = entry.strip()
        if cleaned:
            tools.append(cleaned)
    return tools or None


def _save_result_to_template(
    template_agent: TemplateGenerationAgent,
    objective: str,
    result_text: str | None,
) -> None:
    """将分析结果保存到最新的模板文档中。"""
    from datetime import datetime
    
    # 获取最新的模板文档
    docs = sorted(template_agent.finish_form_dir.glob("*.md"), reverse=True)
    if not docs:
        print("⚠ 没有可用的模板文档")
        return
    
    latest_doc = docs[0]
    
    # 准备结果内容
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = (result_text or "（无内容）").strip()
    formatted_result = f"#### 自动生成结果（{timestamp}）\n\n**目标**: {objective}\n\n{body}\n"
    
    # 追加到文档
    current_content = latest_doc.read_text(encoding="utf-8")
    stage1_pattern = re.compile(
        r"(<!-- STAGE1_ANALYSIS_START -->)(?P<content>.*?)(<!-- STAGE1_ANALYSIS_END -->)",
        re.DOTALL,
    )
    match = stage1_pattern.search(current_content)
    if match:
        replacement = f"{match.group(1)}\n{formatted_result}{match.group(3)}"
        updated_content = (
            current_content[: match.start()]
            + replacement
            + current_content[match.end() :]
        )
    else:
        fallback_entry = (
            f"\n## 分析结果 [{timestamp}]\n\n"
            f"**目标**: {objective}\n\n"
            f"**分析结果**:\n{body}\n\n---\n"
        )
        updated_content = current_content + fallback_entry
    latest_doc.write_text(updated_content, encoding="utf-8")
    
    relative_path = template_agent._to_relative_string(latest_doc)
    print(f"✓ 结果已保存到: {relative_path}")


async def _interactive_loop(agent: MetacognitiveAnalysisAgent, template_agent: TemplateGenerationAgent) -> None:
    _print_banner()

    while True:
        try:
            objective = input("目标 (必填)> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            break

        if not objective:
            print("目标不能为空，请重新输入。")
            continue

        if objective.lower() in EXIT_COMMANDS:
            print("已退出。")
            break

        context = input("上下文 (可选)> ").strip() or None
        recent_thoughts = input("近期思考 (可选)> ").strip() or None
        conversation_history_raw = input("对话历史 (可选，使用 '角色:内容' 以 '|' 分隔)> ").strip()
        critiques_raw = input("外部评价 (可选，使用 '|' 分隔)> ").strip()
        pending_actions_raw = input("待执行动作 (可选，使用 '|' 分隔)> ").strip()
        tools_raw = input("可访问工具 (可选，逗号分隔)> ").strip()

        conversation_history = None
        if conversation_history_raw:
            entries = []
            for item in conversation_history_raw.split("|"):
                if not item.strip():
                    continue
                if ":" in item:
                    role, content = item.split(":", 1)
                    entries.append({"role": role.strip(), "content": content.strip()})
                else:
                    entries.append({"role": "unknown", "content": item.strip()})
            conversation_history = entries or None

        critiques = [c.strip() for c in critiques_raw.split("|") if c.strip()] or None
        pending_actions = [a.strip() for a in pending_actions_raw.split("|") if a.strip()] or None
        tool_catalog = _collect_tool_catalog(tools_raw)
        if not tool_catalog:
            tool_catalog = DEFAULT_TOOL_CATALOG or None

        print("\n生成分析中，请稍候...\n")
        try:
            result_text = await agent.analyze_text(
                objective=objective,
                context=context,
                recent_thoughts=recent_thoughts,
                conversation_history=conversation_history,
                critiques=critiques,
                pending_actions=pending_actions,
                tool_catalog=tool_catalog,
            )
        except Exception as exc:  # pylint: disable=broad-except
            print(f"发生错误: {exc}\n")
            continue

        print("-" * 72)
        print(result_text or "<无内容>")
        print("-" * 72 + "\n")
        
        # 保存结果到模板文档
        try:
            _save_result_to_template(template_agent, objective, result_text)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"保存结果失败: {exc}\n")


async def _main_async(args: argparse.Namespace) -> None:
    config = ModelConfig(
        api_key=_ensure_api_key(args.api_key),
        model_name=args.model,
        stream=args.stream,
        base_url=args.base_url,
        reasoning_effort=args.reasoning_effort,
    )

    agent = MetacognitiveAnalysisAgent(config=config, system_prompt=args.system_prompt)
    
    # 初始化模板生成代理
    template_config = TemplateGenerationConfig(
        threshold=8,
        finish_form_dir=PROJECT_ROOT / "finish_form",
        template_path=PROJECT_ROOT / "form_templates" / "standard template.md",
    )
    template_agent = TemplateGenerationAgent(config=template_config)
    
    # 确保有足够的模板
    print("正在检查模板...")
    template_result = template_agent.run()
    if template_result.get("created"):
        print(f"✓ 已创建新模板: {template_result['created']}")
    print(f"✓ 现有模板数: {len(template_result.get('documents', []))}\n")
    
    await _interactive_loop(agent, template_agent)


def main() -> None:
    args = _parse_args()
    try:
        asyncio.run(_main_async(args))
    except KeyboardInterrupt:
        print("\n已退出。")


if __name__ == "__main__":
    main()
