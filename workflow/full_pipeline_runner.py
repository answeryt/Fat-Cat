# -*- coding: utf-8 -*-
"""多阶段代理全流程调度器。"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import httpx

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from config import ModelConfig
from Document_Checking.template_generation import (
    TemplateGenerationAgent,
    TemplateGenerationConfig,
)
from capability_upgrade_agent.capability_upgrade_agent import (
    CapabilityUpgradeAgent,
    CapabilityUpgradeConfig,
)
from stage1_agent.Metacognitive_Analysis_agnet import MetacognitiveAnalysisAgent
from stage2_agent.Strategy_Selection_agent import StrategySelectionAgent
from stage2_candidate_agent.Candidate_Selection_agent import CandidateSelectionAgent
from stage2_capability_upgrade_agent.stage2_capability_upgrade_agent import (
    Stage2CapabilityUpgradeAgent,
    Stage2CapabilityUpgradeConfig,
)
from stage3_agent.Step_agent import Stage3ExecutionAgent
from stage4_agent.Executor_agent import Stage4ExecutorAgent
from stage4_agent.tools_bridge import create_tools_bridge
from Watcher_Agent import WatcherAgent
from tool_catalog import load_tool_catalog
from Memory_system.memory_bridge import (
    MemoryBridge,
    create_stage1_context,
    create_stage2a_context,
    create_stage2b_context,
    create_stage3_context,
    create_stage4_context,
)


LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SharedModelConfig:
    api_key: str | None = None
    model_name: str = "kimi-k2-250905"
    stream: bool = False
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"


class FullPipelineRunner:

    def __init__(
        self,
        *,
        shared_config: SharedModelConfig,
        finish_form_dir: Path | None = None,
        template_path: Path | None = None,
        encoding: str = "utf-8",
        template_threshold: int = 8,
        strategy_auto_apply: bool = True,
        capability_auto_apply: bool = False,
        watcher_enabled: bool | None = None,
        watcher_config: ModelConfig | None = None,
    ) -> None:
        self._encoding = encoding
        self._finish_form_dir = Path(finish_form_dir or PROJECT_ROOT / "finish_form").expanduser().resolve()
        self._template_path = Path(
            template_path or PROJECT_ROOT / "form_templates" / "standard template.md"
        ).expanduser().resolve()
        self._finish_form_dir.mkdir(parents=True, exist_ok=True)

        if not self._template_path.is_file():
            raise FileNotFoundError(f"模板文件未找到: {self._template_path}")

        model_config = ModelConfig(
            api_key=shared_config.api_key
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("KIMI_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY"),
            model_name=shared_config.model_name,
            stream=shared_config.stream,
            base_url=shared_config.base_url,
        )
        model_config.validate()

        template_config = TemplateGenerationConfig(
            threshold=template_threshold,
            finish_form_dir=self._finish_form_dir,
            template_path=self._template_path,
            encoding=encoding,
        )
        self._template_agent = TemplateGenerationAgent(config=template_config)
        self._default_tool_catalog: Sequence[str] | None = load_tool_catalog() or None

        self._stage1_agent = MetacognitiveAnalysisAgent(config=model_config)
        self._candidate_agent = CandidateSelectionAgent(config=model_config)
        self._stage2_agent = StrategySelectionAgent(config=model_config)
        self._stage2_selection_retry_attempts = 3
        self._stage2_selection_retry_delay = 1.0

        stage2_upgrade_config = Stage2CapabilityUpgradeConfig(
            api_key=model_config.api_key,
            model_name=model_config.model_name,
            stream=model_config.stream,
            base_url=model_config.base_url,
            auto_apply_patch=strategy_auto_apply,
        )
        self._stage2_upgrade_agent = Stage2CapabilityUpgradeAgent(config=stage2_upgrade_config)

        capability_config = CapabilityUpgradeConfig(
            api_key=model_config.api_key,
            model_name=model_config.model_name,
            stream=model_config.stream,
            base_url=model_config.base_url,
            auto_apply_patch=capability_auto_apply,
        )
        self._capability_agent = CapabilityUpgradeAgent(config=capability_config)

        self._stage3_agent = Stage3ExecutionAgent(config=model_config)
        self._stage4_agent = Stage4ExecutorAgent(config=model_config)
        self._tools_bridge = create_tools_bridge()

        watcher_flag = watcher_enabled if watcher_enabled is not None else True
        self._watcher_agent: WatcherAgent | None = None
        if watcher_flag:
            try:
                watcher_model_config = watcher_config if watcher_config else model_config
                self._watcher_agent = WatcherAgent(config=watcher_model_config)
            except Exception as exc:
                LOGGER.warning("WatcherAgent 初始化失败，已自动禁用：%s", exc)
                self._watcher_agent = None

    async def run(
        self,
        *,
        objective: str,
        context_snapshot: str | None = None,
        candidate_limit: int | None = None,
        tool_catalog: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        resolved_tool_catalog = self._resolve_tool_catalog(tool_catalog)
        document_path = self._prepare_finish_form_document(objective, context_snapshot, resolved_tool_catalog)

        stage1_text = await self._run_stage1(document_path, objective=objective)

        stage2_candidate_text = await self._run_stage2_candidate(
            document_path,
            objective=objective,
            candidate_limit=candidate_limit,
        )

        stage2_selection_text = await self._run_stage2_selection(
            document_path,
            objective=objective,
        )

        stage2_upgrade_text = await self._run_stage2_upgrade(document_path)

        stage3_text = await self._run_stage3(document_path, objective=objective)

        stage4_text = await self._run_stage4(document_path, objective=objective)

        watcher_audit_text = MemoryBridge.load_stage_output(document_path, "WATCHER_AUDIT") or None

        capability_upgrade_text = await self._run_capability_upgrade(document_path)

        return {
            "document": self._relativize(document_path),
            "stage1": stage1_text,
            "stage2_candidate": stage2_candidate_text,
            "stage2_selection": stage2_selection_text,
            "stage2_upgrade": stage2_upgrade_text,
            "stage3": stage3_text,
            "stage4": stage4_text,
            "watcher_audit": watcher_audit_text,
            "capability_upgrade": capability_upgrade_text,
        }

    def _prepare_finish_form_document(
        self,
        objective: str,
        context_snapshot: str | None,
        tool_catalog: Sequence[str] | None,
    ) -> Path:
        before = set(self._finish_form_dir.glob("*.md"))
        result = self._template_agent.run()
        created = result.get("created")
        if created:
            candidate = (PROJECT_ROOT / created).resolve()
            if candidate.exists():
                self._write_external_context(candidate, objective, context_snapshot, tool_catalog)
                return candidate

        after = set(self._finish_form_dir.glob("*.md"))
        new_docs = after - before
        if new_docs:
            doc = max(new_docs, key=lambda item: item.stat().st_mtime)
            self._write_external_context(doc, objective, context_snapshot, tool_catalog)
            return doc

        if after:
            doc = max(after, key=lambda item: item.stat().st_mtime)
            self._write_external_context(doc, objective, context_snapshot, tool_catalog)
            return doc

        raise RuntimeError("未能创建或定位 finish_form 文档。")

    def _write_external_context(
        self,
        document_path: Path,
        objective: str,
        context_snapshot: str | None,
        tool_catalog: Sequence[str] | None,
    ) -> None:
        content = document_path.read_text(encoding=self._encoding)
        updated = False

        objective_marker_start = "<!-- EXTERNAL_OBJECTIVE_START -->"
        objective_marker_end = "<!-- EXTERNAL_OBJECTIVE_END -->"
        if objective_marker_start in content and objective_marker_end in content:
            start_idx = content.find(objective_marker_start) + len(objective_marker_start)
            end_idx = content.find(objective_marker_end)
            new_content = f"\n{objective}\n"
            content = content[:start_idx] + new_content + content[end_idx:]
            updated = True

        context_marker_start = "<!-- EXTERNAL_CONTEXT_START -->"
        context_marker_end = "<!-- EXTERNAL_CONTEXT_END -->"
        if context_marker_start in content and context_marker_end in content:
            start_idx = content.find(context_marker_start) + len(context_marker_start)
            end_idx = content.find(context_marker_end)
            new_content = f"\n{context_snapshot or ''}\n"
            content = content[:start_idx] + new_content + content[end_idx:]
            updated = True

        tool_marker_start = "<!-- EXTERNAL_TOOL_CATALOG_START -->"
        tool_marker_end = "<!-- EXTERNAL_TOOL_CATALOG_END -->"
        if tool_marker_start in content and tool_marker_end in content:
            start_idx = content.find(tool_marker_start) + len(tool_marker_start)
            end_idx = content.find(tool_marker_end)
            if tool_catalog:
                tool_list = "\n".join(f"- {tool}" for tool in tool_catalog)
                new_content = f"\n{tool_list}\n"
            else:
                new_content = "\n"
            content = content[:start_idx] + new_content + content[end_idx:]
            updated = True

        if updated:
            document_path.write_text(content, encoding=self._encoding)

    @staticmethod
    def _relativize(path: Path) -> str:
        try:
            return path.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            return path.as_posix()

    def _resolve_tool_catalog(
        self,
        tool_catalog: Sequence[str] | None,
    ) -> Sequence[str] | None:
        if tool_catalog:
            return tool_catalog
        return self._default_tool_catalog

    async def _run_stage1(
        self,
        document_path: Path,
        *,
        objective: str,
    ) -> str:
        context_block = create_stage1_context(
            finish_form_path=str(document_path),
            objective=objective,
        )
        try:
            result_text = await self._stage1_agent.analyze_text(
                context=context_block,
                finish_form_path=str(document_path),
            )
        except Exception as exc:
            self._log_stage_exception("阶段一代理执行失败", exc)
            raise

        return self._normalize_stage_output(result_text)

    async def _run_stage2_candidate(
        self,
        document_path: Path,
        *,
        objective: str,
        candidate_limit: int | None,
    ) -> str:
        context = create_stage2a_context(
            finish_form_path=str(document_path),
            objective=objective,
        )

        kwargs: dict[str, Any] = {}
        if candidate_limit is not None:
            kwargs["candidate_limit"] = candidate_limit

        try:
            result_text = await self._candidate_agent.analyze_text(
                context=context,
                finish_form_path=str(document_path),
                **kwargs,
            )
        except Exception as exc:
            self._log_stage_exception("阶段二-A 候选策略生成失败", exc)
            raise

        return self._normalize_stage_output(result_text)

    async def _run_stage2_selection(
        self,
        document_path: Path,
        *,
        objective: str,
    ) -> str:
        try:
            result_text = await self._run_stage2_selection_with_retries(
                document_path=document_path,
                objective=objective,
            )
        except Exception as exc:
            self._log_stage_exception("阶段二-B 策略遴选失败", exc)
            raise

        return self._normalize_stage_output(result_text)

    async def _run_stage2_selection_with_retries(
        self,
        *,
        document_path: Path,
        objective: str,
    ) -> str:
        context = create_stage2b_context(
            finish_form_path=str(document_path),
            objective=objective,
        )

        retries = 0
        while True:
            try:
                return await self._stage2_agent.analyze_text(
                    context=context,
                    finish_form_path=str(document_path),
                )
            except httpx.HTTPError as exc:
                retries += 1
                if retries >= self._stage2_selection_retry_attempts:
                    raise
                LOGGER.warning(
                    "Stage 2 Selection attempt %d/%d failed: %s; retrying after %.1fs",
                    retries,
                    self._stage2_selection_retry_attempts,
                    exc,
                    self._stage2_selection_retry_delay,
                )
                await asyncio.sleep(self._stage2_selection_retry_delay)

    async def _run_stage2_upgrade(self, document_path: Path) -> str | None:
        context = create_stage2b_context(
            finish_form_path=str(document_path),
            objective="",
        )
        try:
            result_text = await self._stage2_upgrade_agent.evaluate_text(
                context=context,
                finish_form_path=str(document_path),
            )
        except Exception as exc:
            self._log_stage_exception("阶段二-C 策略库升级代理执行失败", exc)
            raise

        body = self._normalize_stage_output(result_text).strip()
        return body or None

    async def _run_stage3(
        self,
        document_path: Path,
        *,
        objective: str,
    ) -> str:
        context = create_stage3_context(
            finish_form_path=str(document_path),
            objective=objective,
        )

        try:
            result_text = await self._stage3_agent.analyze_text(
                context=context,
                finish_form_path=str(document_path),
            )
        except Exception as exc:
            self._log_stage_exception("阶段三执行规划代理执行失败", exc)
            raise

        return self._normalize_stage_output(result_text)

    async def _run_stage4(
        self,
        document_path: Path,
        *,
        objective: str,
    ) -> str:
        context = create_stage4_context(
            finish_form_path=str(document_path),
            objective=objective,
        )

        try:
            result_text = await self._stage4_agent.analyze_text(
                context=context,
                finish_form_path=str(document_path),
                enable_tool_loop=True,
                tools_bridge=self._tools_bridge,
                watcher_agent=self._watcher_agent,
            )
        except Exception as exc:
            self._log_stage_exception("阶段四执行记录代理执行失败", exc)
            raise

        return self._normalize_stage_output(result_text)

    async def _run_capability_upgrade(self, document_path: Path) -> str | None:
        context = create_stage1_context(
            finish_form_path=str(document_path),
            objective="",
        )
        try:
            result_text = await self._capability_agent.evaluate_text(
                context=context,
            )
        except Exception as exc:
            self._log_stage_exception("能力库升级代理执行失败", exc)
            raise
        return self._normalize_stage_output(result_text).strip() or None

    @staticmethod
    def _log_stage_exception(stage: str, exc: Exception) -> None:
        import traceback

        print("\n" + "=" * 60)
        print(f"{stage}，异常详情：{exc.__class__.__name__}: {exc}")
        traceback.print_exc(limit=None)
        print("=" * 60 + "\n")

    @staticmethod
    def _normalize_stage_output(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, str):
            return value

        if isinstance(value, (list, tuple)):
            segments = [
                FullPipelineRunner._normalize_stage_output(item).strip()
                for item in value
            ]
            return "\n".join(segment for segment in segments if segment)

        if isinstance(value, dict):
            for key in ("text", "content"):
                candidate = value.get(key)
                if candidate is not None:
                    return FullPipelineRunner._normalize_stage_output(candidate)
            segments: list[str] = []
            for key, item in value.items():
                normalized = FullPipelineRunner._normalize_stage_output(item).strip()
                if normalized:
                    segments.append(f"{key}: {normalized}")
            return "\n".join(segments)

        text_attr = getattr(value, "text", None)
        if isinstance(text_attr, str):
            return text_attr

        content_attr = getattr(value, "content", None)
        if content_attr is not None:
            return FullPipelineRunner._normalize_stage_output(content_attr)

        if hasattr(value, "__dict__"):
            try:
                payload = {
                    key: val
                    for key, val in value.__dict__.items()
                    if not key.startswith("_")
                }
            except Exception:
                payload = None
            if payload:
                try:
                    return json.dumps(payload, ensure_ascii=False)
                except TypeError:
                    pass

        return str(value)


def _parse_tool_catalog(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items or None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="运行阶段 1-4 代理与能力升级代理的全流程调度器。",
    )
    parser.add_argument("--objective", help="任务目标描述。")
    parser.add_argument("--context", help="补充上下文说明。")
    parser.add_argument("--candidate-limit", type=int, help="候选策略数量上限。")
    parser.add_argument("--finish-dir", type=Path, help="finish_form 目录路径。")
    parser.add_argument("--template", type=Path, help="标准模板文件路径。")
    parser.add_argument("--encoding", default="utf-8", help="文档读写编码（默认 utf-8）。")
    parser.add_argument("--api-key", dest="api_key", help="API Key。")
    parser.add_argument("--model", default=os.getenv("MODEL_NAME", "gemini-3-pro"), help="模型名称。")
    parser.add_argument("--base-url", default=os.getenv("MODEL_BASE_URL", "https://xh-hk.a3e.top/v1"), help="模型服务基础地址。")
    parser.add_argument("--stream", action="store_true", help="启用流式输出。")
    parser.add_argument(
        "--no-strategy-auto-apply",
        action="store_true",
        help="禁用阶段二策略库自动写入。",
    )
    parser.add_argument(
        "--auto-apply-capability",
        action="store_true",
        help="启用能力库自动写入。",
    )
    parser.add_argument(
        "--tool-catalog",
        help="可用工具清单，使用逗号分隔。",
    )
    parser.add_argument(
        "--no-watcher",
        action="store_true",
        help="禁用 Watcher 审计代理。",
    )
    parser.add_argument("--watcher-api-key", help="Watcher 代理使用的 API Key。")
    parser.add_argument("--watcher-model", help="Watcher 代理模型名称。")
    parser.add_argument("--watcher-base-url", help="Watcher 代理服务基础地址。")
    parser.add_argument(
        "--watcher-reasoning-effort",
        choices=["low", "medium", "high"],
        help="Watcher 代理推理深度。",
    )
    parser.add_argument("--watcher-stream", action="store_true", help="启用 Watcher 代理流式响应。")
    return parser.parse_args()


def _print_stage_outputs(result: dict[str, Any]) -> None:
    divider = "=" * 80
    sections = [
        ("阶段一代理输出", "stage1"),
        ("阶段二候选策略输出", "stage2_candidate"),
        ("阶段二策略遴选输出", "stage2_selection"),
        ("阶段三代理输出", "stage3"),
        ("阶段四代理输出", "stage4"),
    ]

    print(divider)
    print("阶段代理执行日志")
    print(divider)
    for title, key in sections:
        content = result.get(key)
        print(f"\n{title}")
        print("-" * len(title))
        if content:
            print(content.strip())
        else:
            print("（无输出）")
    print("\n" + divider)


async def _async_main(args: argparse.Namespace) -> dict[str, Any]:
    api_key = (
        os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("KIMI_API_KEY")
        or args.api_key
    )
    model_name = os.getenv("MODEL_NAME") or args.model
    base_url = os.getenv("MODEL_BASE_URL") or args.base_url
    
    shared_config = SharedModelConfig(
        api_key=api_key,
        model_name=model_name,
        stream=args.stream,
        base_url=base_url,
    )
    watcher_enabled = not args.no_watcher
    watcher_config = None
    if watcher_enabled:
        watcher_stream = shared_config.stream
        if args.watcher_stream:
            watcher_stream = True

        watcher_api_key = (
            os.getenv("DEEPSEEK_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("KIMI_API_KEY")
            or args.watcher_api_key
            or shared_config.api_key
        )
        watcher_model_name = args.watcher_model or os.getenv("MODEL_NAME") or shared_config.model_name
        watcher_base_url = args.watcher_base_url or os.getenv("MODEL_BASE_URL") or shared_config.base_url
        
        watcher_config = ModelConfig(
            api_key=watcher_api_key,
            model_name=watcher_model_name,
            stream=watcher_stream,
            base_url=watcher_base_url,
            reasoning_effort=args.watcher_reasoning_effort,
        )
    runner = FullPipelineRunner(
        shared_config=shared_config,
        finish_form_dir=args.finish_dir,
        template_path=args.template,
        encoding=args.encoding,
        strategy_auto_apply=not args.no_strategy_auto_apply,
        capability_auto_apply=args.auto_apply_capability,
        watcher_enabled=watcher_enabled,
        watcher_config=watcher_config,
    )
    tool_catalog = _parse_tool_catalog(args.tool_catalog)
    return await runner.run(
        objective=args.objective,
        context_snapshot=args.context,
        candidate_limit=args.candidate_limit,
        tool_catalog=tool_catalog,
    )


def main() -> None:
    args = _parse_args()
    if not args.objective:
        try:
            args.objective = input("请输入任务目标: ").strip()
        except KeyboardInterrupt:
            print("\n已取消。")
            raise SystemExit(130) from None
    if not args.objective:
        print("未提供任务目标，已取消执行。")
        raise SystemExit(1)
    try:
        result = asyncio.run(_async_main(args))
    except KeyboardInterrupt:
        print("已取消。")
        raise SystemExit(130) from None
    except Exception as exc:
        print(f"执行失败：{exc}")
        raise SystemExit(1) from exc

    _print_stage_outputs(result)

    document = result.get("document")
    print("全流程执行完成。")
    if document:
        print(f"- 协作表单：{document}")
    if result.get("stage2_upgrade"):
        print("- 已生成策略库升级补丁。")
    if result.get("capability_upgrade"):
        print("- 已完成能力库升级评估。")


if __name__ == "__main__":
    main()
