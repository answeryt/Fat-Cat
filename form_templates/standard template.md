# 任务协作表（finish_form）

## 外部信息

<!-- EXTERNAL_OBJECTIVE_START -->
### 任务目标
<!-- EXTERNAL_OBJECTIVE_END -->

<!-- EXTERNAL_CONTEXT_START -->
### 外部上下文
<!-- EXTERNAL_CONTEXT_END -->

<!-- EXTERNAL_TOOL_CATALOG_START -->
### 可用工具清单
<!-- EXTERNAL_TOOL_CATALOG_END -->

---

## 任务基本信息

- Task ID:
- 用户目标（Objective）:
- 重要约束（Constraints）:

---

## 阶段一：元能力分析（Stage 1）

<!-- STAGE1_EXECUTIVE_SUMMARY_START -->
### 1. Executive Summary for Other Agents

（3–6 行，英文为主，概括任务类型、关键挑战、知识边界）
<!-- STAGE1_EXECUTIVE_SUMMARY_END -->

<!-- STAGE1_CAPABILITY_INVENTORY_START -->
### 2. Capability Inventory（简表）

| Capability ID | Name | Role in this task | Main risk |
|---------------|------|-------------------|-----------|
<!-- STAGE1_CAPABILITY_INVENTORY_END -->

<!-- STAGE1_FAILURE_MODES_START -->
### 3. Common Failure Modes

| Capability (ID/Name) | Error pattern | Trigger condition | Downstream risk |

> 标记规则：凡由 Stage 1 外部检索得到的风险，`Error pattern` 需以 `[外部警示]: ...` 开头，`Trigger` 或 `Downstream risk` 中注明来源/引用；若搜索失败，记录 `[外部警示]: 未能访问外部失败经验`。
<!-- STAGE1_FAILURE_MODES_END -->

<!-- STAGE1_RISKS_BOUNDARY_START -->
### 4. Risks & Knowledge Boundary

- Known limits:
- High-risk areas:
<!-- STAGE1_RISKS_BOUNDARY_END -->

---

## 阶段二-A：候选策略产出（Stage 2-A）

<!-- STAGE2A_STRATEGY_CATALOG_START -->
### 1. Candidate Strategy Catalog（简表）

| ID | Title | Summary | Covers challenges | Main risk/cost |
|----|-------|---------|-------------------|----------------|

_提示：在 "Covers challenges" 中标注哪些 Stage 1 `[外部警示]` 被覆盖；未覆盖的高风险需在 "Main risk/cost" 或 "Notes" 中写明缺口。_
<!-- STAGE2A_STRATEGY_CATALOG_END -->

<!-- STAGE2A_NOTES_START -->
### 2. Notes for Stage 2-B

- 补充说明（不超过 5 行）
<!-- STAGE2A_NOTES_END -->

---

## 阶段二-B：策略遴选（Stage 2-B）

<!-- STAGE2B_STRATEGY_SNAPSHOT_START -->
### 1. Final Strategy Snapshot

- strategy_id:
- strategy_title:
- 3–5 key_steps（列表）
- success_criteria（1–3 条）:
- failure_indicators（1–3 条）:
<!-- STAGE2B_STRATEGY_SNAPSHOT_END -->

<!-- STAGE2B_HANDOVER_NOTES_START -->
### 2. Handover Notes for Stage 3

- key_ideas:
- mapped_challenges:
- tools_or_resources:
- risks_and_assumptions:
- common_failure_mitigations（2–4 行概述策略如何规避 Stage1 风险）:
- residual_risks_for_stage3（仍需下游注意的风险或假设）:

> 请在 `mapped_challenges` / `common_failure_mitigations` 中明确列出每条 `[外部警示]` 的缓解位置；若仍未解决，写入 `risks_and_assumptions`。
<!-- STAGE2B_HANDOVER_NOTES_END -->
---

## 阶段三：执行步骤规划（Stage 3）

<!-- STAGE3_EXECUTION_PLAN_START -->
### 1. Execution Plan Overview

| step_id | goal | actions | expected_output | tools | quality_checks | related_risks |
|---------|------|---------|-----------------|-------|----------------|---------------|
<!-- STAGE3_EXECUTION_PLAN_END -->

<!-- STAGE3_NOTES_START -->
### 2. Notes for Executor

- 关键检查点 / 风险提示（含如何覆盖成功标准，≤5 行）
<!-- STAGE3_NOTES_END -->

---

## Live Execution Plan

<!-- LIVE_EXECUTION_PLAN_START -->
`待填写`
<!-- LIVE_EXECUTION_PLAN_END -->

---

## 阶段四：执行与复盘（Stage 4）

### 1. Execution Log

<!-- STAGE4_TOOL_CALLS_START -->
`待填写`
<!-- STAGE4_TOOL_CALLS_END -->

<!-- STAGE4_FINAL_ANSWER_START -->
### 3. Final Answer to User

- **Final Answer**: ...
- **Known facts used**:
- **Inferences made**:
- **Assumptions / uncertainties**:
<!-- STAGE4_FINAL_ANSWER_END -->

<!-- STAGE4_FEEDBACK_START -->
### 4. Feedback to Upstream

- Stage 3:
- Stage 2:
- Stage 1:
<!-- STAGE4_FEEDBACK_END -->

---

## Watcher 审计报告

<!-- WATCHER_AUDIT_START -->

### Overall Verdict

- Stage: 
- Status: [PASS / FAIL]
- Confidence: [low / medium / high]
- Issue Count: 

### Mandatory To-Do List

当 Status 为 FAIL 时必须填写：

```
[ ] (指令1)
[ ] (指令2)
[ ] (指令3)
```

### Analysis Summary

(问题根因分析，不超过3行)

### Audit Verdict

```
Status: [PASS / FAIL]
Blame Stage: [Stage2 / Stage3 / Stage4 / None]
Critical Error: 
To-Do Count: 
```

<!-- WATCHER_AUDIT_END -->

---

## Watcher 实时指导

<!-- WATCHER_REALTIME_START -->
### 实时提醒日志

| 时间戳 | 阶段 | 提醒内容 | 优先级 |
|--------|------|----------|--------|

<!-- WATCHER_REALTIME_END -->

---

## Executor 执行核对

<!-- EXECUTOR_CHECKLIST_START -->

### Checklist Protocol

```
[CHECKLIST]
"指令1" -> [DONE/PENDING] (执行说明)
"指令2" -> [DONE/PENDING] (执行说明)
[/CHECKLIST]
```

<!-- EXECUTOR_CHECKLIST_END -->
