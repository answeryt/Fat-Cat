"""Command-line interface for running CapabilityUpgradeAgent interactively."""

from __future__ import annotations

import argparse
import asyncio
import os
from getpass import getpass
from pathlib import Path

from dotenv import load_dotenv

try:
    from .capability_upgrade_agent import CapabilityUpgradeAgent, CapabilityUpgradeConfig
except ImportError:
    import os as _os
    import sys as _sys

    CURRENT_DIR = _os.path.dirname(_os.path.abspath(__file__))
    if CURRENT_DIR not in _sys.path:
        _sys.path.insert(0, CURRENT_DIR)

    from capability_upgrade_agent import CapabilityUpgradeAgent, CapabilityUpgradeConfig

EXIT_COMMANDS = {"exit", "quit", "q"}
REFRESH_COMMANDS = {"refresh", "reload"}
APPLY_COMMANDS = {"apply", "write"}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="capability-upgrade-agent",
        description="Interactively run the CapabilityUpgradeAgent for maintaining the ability library.",
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
        help="Optional custom system prompt. If omitted, the default template from thinking.md is used.",
    )
    parser.add_argument(
        "--max-library-chars",
        type=int,
        dest="max_library_chars",
        help="Maximum number of characters to load from the ability library snapshot (default: 120000).",
    )
    parser.add_argument(
        "--no-envelope",
        dest="no_envelope",
        action="store_true",
        help="Disable attaching AgentEnvelope metadata to responses.",
    )
    parser.add_argument(
        "--summary-width",
        type=int,
        default=160,
        help="Maximum width for the metadata summary when envelope attachment is enabled (default: 160).",
    )
    parser.add_argument(
        "--auto-apply",
        dest="auto_apply_patch",
        action="store_true",
        help="Automatically append generated capability definitions to the core capabilities library.",
    )
    parser.add_argument(
        "--no-backup",
        dest="no_backup",
        action="store_true",
        help="Disable automatic backup before writing to the capability library file.",
    )
    parser.add_argument(
        "--library-file",
        dest="library_file",
        help="Path to the capability library markdown file to update "
        "(default: ability_library/core_capabilities.md).",
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
    print("Capability Upgrade Agent")
    print("输入 'exit' / 'quit' / 'q' 退出程序，输入 'refresh' 重新加载能力库快照")
    print("提示: 多条输入可使用 '|' 分隔；留空可跳过可选字段")
    print("=" * 72)


def _parse_delimited(raw: str) -> list[str] | None:
    if not raw.strip():
        return None
    entries = []
    for token in raw.split("|"):
        cleaned = token.strip()
        if cleaned:
            entries.append(cleaned)
    return entries or None


async def _interactive_loop(agent: CapabilityUpgradeAgent) -> None:
    _print_banner()

    while True:
        try:
            report = input("Metacognitive 输出 (必填)> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出。")
            break

        if not report:
            print("Metacognitive 输出不能为空，请重新输入。")
            continue

        lowered = report.lower()
        if lowered in EXIT_COMMANDS:
            print("已退出。")
            break
        if lowered in REFRESH_COMMANDS:
            agent.refresh_system_prompt(force=True)
            print("已重新加载系统提示与能力库快照。\n")
            continue
        if lowered in APPLY_COMMANDS:
            patch = agent.last_patch_markdown
            if not patch:
                print("当前没有可写入的能力补丁，请先生成。\n")
                continue
            applied_path = agent.apply_patch(patch)
            if applied_path:
                print(f"已将能力补丁写入 {applied_path}\n")
            else:
                print("能力补丁为空，未执行写入。\n")
            continue

        suspected_raw = input("疑似新增能力 (可选，使用 '|' 分隔)> ").strip()
        pending_raw = input("待处理能力补丁 (可选，使用 '|' 分隔)> ").strip()
        maintainer_notes = input("维护者备注 (可选)> ").strip() or None
        additional_context = input("额外上下文 (可选)> ").strip() or None
        custom_snapshot = input("临时能力库快照覆盖 (可选)> ").strip() or None

        suspected = _parse_delimited(suspected_raw)
        pending = _parse_delimited(pending_raw)
        snapshot_override = custom_snapshot or None

        print("\n生成能力补丁中，请稍候...\n")
        try:
            result_text = await agent.evaluate_text(
                metacognitive_report=report,
                suspected_new_capabilities=suspected,
                pending_updates=pending,
                maintainer_notes=maintainer_notes,
                additional_context=additional_context,
                library_snapshot=snapshot_override,
            )
        except Exception as exc:  # pylint: disable=broad-except
            print(f"发生错误: {exc}\n")
            continue

        print("-" * 72)
        print(result_text or "<无内容>")
        print("-" * 72 + "\n")

        if agent.last_applied_path:
            print(f"✅ 已自动写入能力库：{agent.last_applied_path}\n")
        elif agent.last_patch_markdown:
            print("提示：输入 'apply' 可写入当前能力补丁；输入 'refresh' 可重载能力库快照。\n")


async def _main_async(args: argparse.Namespace) -> None:
    config = CapabilityUpgradeConfig(
        api_key=_ensure_api_key(args.api_key),
        model_name=args.model,
        stream=args.stream,
        base_url=args.base_url,
        reasoning_effort=args.reasoning_effort,
        system_prompt=args.system_prompt,
        max_library_chars=args.max_library_chars,
        attach_envelope=not args.no_envelope,
        summary_width=args.summary_width,
        auto_apply_patch=args.auto_apply_patch,
        backup_before_write=not args.no_backup,
        library_file=args.library_file,
    )

    agent = CapabilityUpgradeAgent(config=config)
    await _interactive_loop(agent)


def main() -> None:
    args = _parse_args()
    try:
        asyncio.run(_main_async(args))
    except KeyboardInterrupt:
        print("\n已退出。")


if __name__ == "__main__":
    main()
