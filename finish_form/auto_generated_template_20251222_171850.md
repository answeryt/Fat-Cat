# 任务协作表（finish_form）

## 外部信息

<!-- EXTERNAL_OBJECTIVE_START -->
Black Book starred the actress and writer of what heritage?
<!-- EXTERNAL_OBJECTIVE_END -->

<!-- EXTERNAL_CONTEXT_START -->

<!-- EXTERNAL_CONTEXT_END -->

<!-- EXTERNAL_TOOL_CATALOG_START -->
- 一、信息获取类 · **网络搜索**（tool_id: web_search）
- 一、信息获取类 · 功能：统一网络搜索接口，支持 Tavily/Firecrawl 后端自动切换
- 一、信息获取类 · 参数：query（搜索词）、max_results（结果数量）、provider（auto/tavily/firecrawl）
- 一、信息获取类 · 适用：事实核验、资讯检索、背景调研、获取目标URL
- 一、信息获取类 · 输出：结构化搜索结果，包含标题、摘要、URL链接
- 一、信息获取类 · **网页抓取**（tool_id: web_scrape）
- 一、信息获取类 · 功能：提取指定URL网页的完整内容，转换为Markdown格式
- 一、信息获取类 · 参数：url（目标网页地址）、format（输出格式，默认markdown）
- 一、信息获取类 · 适用：深度阅读搜索结果、提取文章全文、获取详细数据
- 一、信息获取类 · 输出：网页标题 + Markdown格式正文内容
- 一、信息获取类 · **数学计算**（tool_id: calculate）
- 一、信息获取类 · 功能：安全的数学表达式求值，支持math库函数
- 一、信息获取类 · 参数：expression（数学表达式）
- 一、信息获取类 · 适用：简单数学计算、公式验证
- 一、信息获取类 · 输出：计算结果
- 二、代码执行类 · **代码解释器**（tool_id: code_interpreter）
- 二、代码执行类 · 功能：在受控沙箱中执行 Python 代码
- 二、代码执行类 · 适用：脚本编写、数据处理、算法验证、文档同步
- 二、代码执行类 · 基础输出：代码执行结果、图表、处理后的数据结构（所有原始 `stdout/stderr` 需写入执行日志）
- 二、代码执行类 · **子能力（依赖 `install_gaia_dependencies.py` 预装的库）**：
- 二、代码执行类 · Excel / CSV：`pandas` + `openpyxl` 读取工作表、清洗列名、执行聚合或透视操作
- 二、代码执行类 · PDF：`pypdf` 解码多页文档，提取文本与元数据
- 二、代码执行类 · Image：`Pillow` 读取 PNG/JPEG，获取尺寸 / 模式 / EXIF
- 二、代码执行类 · PDB / mmCIF：`BioPython` (`Bio.PDB`) 加载分子结构
- 二、代码执行类 · HTTP 下载：`requests` 拉取远程附件或接口数据
- 二、代码执行类 · 使用规范：凡涉及计算、附件解析或数据凭证，必须实际运行代码解释器并在 `execution_log.actual_output` 中记录 Raw Output 与结论
- 1. 「搜索 → 抓取 → 分析」（推荐组合） · **步骤**：web_search → web_scrape → code_interpreter
- 1. 「搜索 → 抓取 → 分析」（推荐组合） · **适用场景**：需要深度信息获取和分析的任务
- 1. 「搜索 → 抓取 → 分析」（推荐组合） · **典型用法**：
- 2. 「调研 → 计算 → 总结」 · **步骤**：web_search → code_interpreter → 纯 LLM 总结
- 2. 「调研 → 计算 → 总结」 · **适用场景**：需要外部信息支持的分析计算任务
- 2. 「调研 → 计算 → 总结」 · **典型用法**：
- 3. 「纯计算验证」 · **步骤**：code_interpreter 或 calculate 独立执行
- 3. 「纯计算验证」 · **适用场景**：逻辑推理、算法验证、数学计算
- 3. 「纯计算验证」 · **典型用法**：直接调用完成计算任务
- 4. 「循环调研验证」 · **步骤**：web_search ↔ web_scrape ↔ code_interpreter 循环调用
- 4. 「循环调研验证」 · **适用场景**：需要多轮信息收集和验证的复杂任务
- 4. 「循环调研验证」 · **典型用法**：
- 工具角色定位 · **web_search**：广度搜索角色，快速获取多个相关结果的摘要和URL
- 工具角色定位 · **web_scrape**：深度获取角色，提取单个URL的完整内容
- 工具角色定位 · **code_interpreter**：计算验证角色，负责数据处理、算法实现、结果验证
- 工具角色定位 · **calculate**：轻量计算角色，快速完成简单数学运算
- 组合使用示例 · 返回结果包含财报相关链接
- 组合使用示例 · 来源为官方或权威财经媒体
- 组合使用示例 · 成功提取网页内容
- 组合使用示例 · 内容包含财务数据
- 组合使用示例 · 代码执行无报错
- 组合使用示例 · 输出包含计算结果
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


---

## 完成文档位置索引

- `finish_form/auto_generated_template_20251222_171850.md`
