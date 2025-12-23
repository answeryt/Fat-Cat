# -*- coding: utf-8 -*-
"""Document orchestrator for unified document generation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from workflow.content_extractor import ContentExtractor, ExtractedContent
from workflow.finish_form_utils import update_form_section, read_form_section


@dataclass
class StageOutput:
    stage: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolCallRecord:
    iteration: int
    tool_name: str
    tool_args: dict[str, Any]
    tool_output: str | None
    tool_error: str | None
    timestamp: datetime = field(default_factory=datetime.now)
    extracted: ExtractedContent | None = None


class DocumentOrchestrator:
    def __init__(self, document_path: Path, encoding: str = "utf-8"):
        self.document_path = document_path
        self.encoding = encoding
        self.data_dir = document_path.parent / ".data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.extractor = ContentExtractor()
        self.stage_outputs: dict[str, StageOutput] = {}
        self.tool_calls: list[ToolCallRecord] = []
        self.extracted_info: dict[str, Any] = {}
        
        self.raw_outputs_file = self.data_dir / f"{document_path.stem}_raw_outputs.json"
        self.extracted_info_file = self.data_dir / f"{document_path.stem}_extracted_info.json"
    
    def register_stage_output(self, stage: str, content: str):
        self.stage_outputs[stage] = StageOutput(stage=stage, content=content)
        
        marker_map = {
            'stage1': 'STAGE1_ANALYSIS',
            'stage2_candidate': 'STAGE2A_ANALYSIS',
            'stage2_selection': 'STAGE2B_ANALYSIS',
            'stage2_upgrade': 'STAGE2C_ANALYSIS',
            'stage3': 'STAGE3_PLAN',
            'stage4': 'STAGE4_FINAL_ANSWER',
        }
        
        marker = marker_map.get(stage)
        if marker:
            update_form_section(
                self.document_path,
                marker_name=marker,
                content=content,
                encoding=self.encoding,
            )
    
    def register_tool_call(
        self,
        iteration: int,
        tool_name: str,
        tool_args: dict[str, Any],
        tool_output: str | None,
        tool_error: str | None,
    ):
        record = ToolCallRecord(
            iteration=iteration,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_output=tool_output,
            tool_error=tool_error,
        )
        
        if tool_output and tool_name == 'web_scrape':
            url = tool_args.get('url', '')
            record.extracted = self.extractor.extract_from_web_scrape(tool_output, url)
            self.extracted_info[f"tool_call_{iteration}"] = {
                'url': url,
                'title': record.extracted.title,
                'summary': record.extracted.summary,
                'key_data': record.extracted.key_data,
            }
        
        self.tool_calls.append(record)
        self._save_raw_data()
        self._update_tool_log_summary()
    
    
    def _save_raw_data(self):
        raw_data = {
            'tool_calls': [
                {
                    'iteration': r.iteration,
                    'tool_name': r.tool_name,
                    'tool_args': r.tool_args,
                    'tool_output': r.tool_output,
                    'tool_error': r.tool_error,
                    'timestamp': r.timestamp.isoformat(),
                }
                for r in self.tool_calls
            ]
        }
        
        with open(self.raw_outputs_file, 'w', encoding=self.encoding) as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)
        
        with open(self.extracted_info_file, 'w', encoding=self.encoding) as f:
            json.dump(self.extracted_info, f, ensure_ascii=False, indent=2)
    
    def _update_tool_log_summary(self):
        if not self.tool_calls:
            return
        
        summary_lines = []
        tool_stats = {}
        
        for record in self.tool_calls:
            tool_name = record.tool_name
            if tool_name not in tool_stats:
                tool_stats[tool_name] = {'count': 0, 'summaries': []}
            
            tool_stats[tool_name]['count'] += 1
            summary = self.extractor.extract_tool_call_summary(
                record.tool_name,
                record.tool_args,
                record.tool_output,
                record.tool_error,
            )
            tool_stats[tool_name]['summaries'].append(summary)
        
        summary_lines.append("### 工具使用摘要\n")
        
        for tool_name, stats in tool_stats.items():
            summary_lines.append(f"#### {tool_name}")
            summary_lines.append(f"执行次数: {stats['count']}")
            summary_lines.append("关键调用:")
            for summary in stats['summaries'][:10]:
                summary_lines.append(f"- {summary}")
            if len(stats['summaries']) > 10:
                summary_lines.append(f"- ... 还有 {len(stats['summaries']) - 10} 次调用")
            summary_lines.append("")
        
        summary_lines.append(f"完整工具日志见: `.data/{self.document_path.stem}_raw_outputs.json`")
        
        summary_content = '\n'.join(summary_lines)
        
        existing = read_form_section(self.document_path, marker_name="STAGE4_TOOL_CALLS") or ""
        if existing == "`待填写`" or not existing.strip() or "工具使用摘要" not in existing:
            update_form_section(
                self.document_path,
                marker_name="STAGE4_TOOL_CALLS",
                content=summary_content,
                header="### 1. Execution Log",
                encoding=self.encoding,
            )
    
    def finalize_document(self):
        self._update_task_overview()
        self._add_info_index()
    
    def _update_task_overview(self):
        objective_section = read_form_section(self.document_path, marker_name="EXTERNAL_INFO") or ""
        objective_match = re.search(r'### 任务目标\s*\n\n(.+?)(?=\n###|\n<!--|$)', objective_section, re.DOTALL)
        objective = objective_match.group(1).strip() if objective_match else ""
        
        overview_content = f"""- 任务目标：{objective[:100] if objective else '未设置'}
- 任务状态：{'已完成' if self.stage_outputs.get('stage4') else '进行中'}
- 关键信息摘要：工具调用 {len(self.tool_calls)} 次，完成 {len(self.stage_outputs)} 个阶段"""
        
        current_content = self.document_path.read_text(encoding=self.encoding)
        overview_pattern = re.compile(r'## 任务概览\s*\n\n(- 任务目标：.*?\n- 任务状态：.*?\n- 关键信息摘要：.*?)(?=\n---|\n##|$)', re.DOTALL)
        if overview_pattern.search(current_content):
            current_content = overview_pattern.sub(f"## 任务概览\n\n{overview_content}", current_content)
        else:
            placeholder_pattern = re.compile(r'## 任务概览\s*\n\n- 任务目标：\s*\n- 任务状态：\s*\n- 关键信息摘要：\s*(?=\n---|\n##|$)', re.DOTALL)
            if placeholder_pattern.search(current_content):
                current_content = placeholder_pattern.sub(f"## 任务概览\n\n{overview_content}\n", current_content)
            else:
                current_content = current_content.replace("## 任务概览\n\n- 任务目标：\n- 任务状态：\n- 关键信息摘要：", f"## 任务概览\n\n{overview_content}")
        
        self.document_path.write_text(current_content, encoding=self.encoding)
    
    def _add_info_index(self):
        index_content = f"""
---

## 详细信息索引

- 完整工具日志: `.data/{self.document_path.stem}_raw_outputs.json`
- 提取的结构化信息: `.data/{self.document_path.stem}_extracted_info.json`
- 工具调用总数: {len(self.tool_calls)}
- 阶段输出数量: {len(self.stage_outputs)}
"""
        
        current_content = self.document_path.read_text(encoding=self.encoding)
        if "详细信息索引" not in current_content:
            current_content = current_content.rstrip() + index_content
            self.document_path.write_text(current_content, encoding=self.encoding)

