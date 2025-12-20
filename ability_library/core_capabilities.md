## 核心能力库使用说明

- **文件位置**：`ability_library/core_capabilities.md`
- **服务对象**：Stage 1 元分析代理，用于在 `reasoner.md` 的“所需能力识别”步骤中快速定位能力。
- **协作说明**：Stage 1 仅查阅此能力库完成能力识别；策略相关资源由 Stage 2 系列代理在 `strategy_library/strategy.md` 中处理。
- **检索提示**：按分类（A–H）或编号（如 `A1`、`B2`）搜索，可在 IDE 中迅速跳转对应能力定义。

---

### 能力索引总览

| 编号 | 名称 | 简短别名 | 典型适配问题类型 |
| --- | --- | --- | --- |
| A1 | `language_understanding` | 语言理解抽象 | requirement_clarification、conceptual_explanation |
| A2 | `critical_analysis` | 论证质检 | argument_evaluation、bias_detection |
| B1 | `multi_hop_reasoning` | 多跳推理 | multi_step_reasoning、problem_diagnosis |
| B2 | `causal_reasoning` | 因果分析 | causal_analysis、what_if |
| B3 | `mathematical_reasoning` | 数学推导 | mathematical_problem、algorithm_design |
| B4 | `system_thinking` | 系统思维 | system_design、process_optimization |
| C1 | `knowledge_retrieval` | 事实检索 | knowledge_lookup、fact_verification |
| C2 | `research` | 研究综述 | research_question、literature_review |
| C3 | `context_memory` | 跨文档记忆 | long_context_synthesis、cross_doc_analysis |
| D1 | `tool_use` | 工具调用 | tool_instruction、data_collection |
| D2 | `code_generation` | 代码生成 | code_generation、refactoring |
| D3 | `planning` | 计划制定 | project_planning、execution_strategy |
| D4 | `code_review` | 代码审查 | code_review、risk_assessment |
| E1 | `verification` | 结果验证 | result_validation、consistency_check |
| E2 | `debugging` | 缺陷排查 | debugging、bug_fixing |
| E3 | `optimization` | 性能优化 | performance_tuning、efficiency_improvement |
| E4 | `auto_correction` | 自动修复 | error_recovery、code_auto_fix |
| E5 | `stage_feedback` | 阶段反馈 | cross_stage_adjustment、upstream_correction |
| E6 | `retry_orchestration` | 重试编排 | failure_recovery、adaptive_retry |
| F1 | `creative_ideation` | 创意发散 | brainstorming、product_ideation |
| F2 | `system_design` | 架构设计 | system_design、architecture_review |
| G1 | `multimodal_understanding` | 跨模态理解 | multimodal_analysis、diagram_explanation |
| H1 | `safety_compliance` | 安全合规 | policy_compliance、security_review |
| H2 | `ethical_judgment` | 伦理评估 | ethical_assessment、fairness_analysis |

> 注：Stage 1 元分析代理可直接透过此列表定位能力，若新增能力，请同步补充表格行与下方详细描述。

---

### A. 语言与理解能力

#### `language_understanding` (A1)
- **适配问题类型**：`requirement_clarification`、`conceptual_explanation`
- **能力说明**：将口语化或模糊描述抽象为结构化任务目标。
- **典型示例**：用户提出“帮我梳理这个想法是否可行”，需提炼约束并输出执行清单。

#### `critical_analysis` (A2)
- **适配问题类型**：`argument_evaluation`、`bias_detection`
- **能力说明**：质疑隐含假设、评估论证强度、识别逻辑谬误与偏差。
- **典型示例**：审视市场预测报告是否缺乏数据支撑或存在推理漏洞。

---

### B. 推理与思维能力

#### `multi_hop_reasoning` (B1)
- **适配问题类型**：`multi_step_reasoning`、`problem_diagnosis`
- **能力说明**：拆解复杂问题为可验证的中间结论并保持逻辑依赖一致。
- **典型示例**：根据多轮实验数据推导产品缺陷的根本原因链。

#### `causal_reasoning` (B2)
- **适配问题类型**：`causal_analysis`、`what_if`
- **能力说明**：识别因果关系、执行反事实推理并构建因果模型。
- **典型示例**：回答“若降低广告预算 20%，销量会受到怎样的影响？”

#### `mathematical_reasoning` (B3)
- **适配问题类型**：`mathematical_problem`、`algorithm_design`
- **能力说明**：进行等式变换、离散构造、反例/不变量分析，必要时结合工具计算。
- **典型示例**：推导算法复杂度或验证概率模型的参数取值合理性。

#### `system_thinking` (B4)
- **适配问题类型**：`system_design`、`process_optimization`
- **能力说明**：以整体视角理解系统动态、平衡约束并分析涌现行为。
- **典型示例**：规划供应链优化方案时，协调库存、物流与成本之间的反馈。

---

### C. 知识与证据能力

#### `knowledge_retrieval` (C1)
- **适配问题类型**：`knowledge_lookup`、`fact_verification`
- **能力说明**：执行信息检索、筛选可信来源、对齐验证并保留引用。
- **典型示例**：比较两位公众人物的出生日期并提供可靠来源链接。

#### `research` (C2)
- **适配问题类型**：`research_question`、`literature_review`
- **能力说明**：构建研究假设、设计验证方案、整合多源信息得出结论。
- **典型示例**：撰写“可持续建筑材料最新进展”的综述报告并列出证据。

#### `context_memory` (C3)
- **适配问题类型**：`long_context_synthesis`、`cross_doc_analysis`
- **能力说明**：跨多文档/多轮对话保持上下文一致与引用准确。
- **典型示例**：汇总多次会议纪要，并关联上一轮决议与当前行动项。

---

### D. 工具与执行能力

#### `tool_use` (D1)
- **适配问题类型**：`tool_instruction`、`data_collection`
- **能力说明**：指导或亲自调用外部工具（搜索、代码执行、OCR 等）完成辅助任务。
- **典型示例**：说明如何调用 API 获取实时汇率并整理成表格。

#### `code_generation` (D2)
- **适配问题类型**：`code_generation`、`refactoring`
- **能力说明**：生成、重构或优化代码文本，需与执行/验证工具配合使用。
- **典型示例**：根据需求生成 Python 脚本并解释核心模块逻辑。

#### `planning` (D3)
- **适配问题类型**：`project_planning`、`execution_strategy`
- **能力说明**：拆分长程目标，规划阶段任务、重试/回退策略与检查点。
- **典型示例**：制定三周迭代上线计划并为每周设定验收标准。

#### `code_review` (D4)
- **适配问题类型**：`code_review`、`risk_assessment`
- **能力说明**：从架构、逻辑与风格角度审查代码，识别潜在缺陷并提出改进建议。
- **典型示例**：审阅微服务合并请求，指出并发控制风险并建议补充回归测试。

---

### E. 验证与质量能力

#### `verification` (E1)
- **适配问题类型**：`result_validation`、`consistency_check`
- **能力说明**：执行单位、边界条件、数值反推等一致性校验并标注不确定性。
- **典型示例**：核对财务报表合计与明细是否相符并指出异常项。

#### `debugging` (E2)
- **适配问题类型**：`debugging`、`bug_fixing`
- **能力说明**：定位缺陷、分析根因、提出修复策略并验证有效性。
- **典型示例**：排查微服务 API 间歇性 500 错误的触发条件与解决方案。

#### `optimization` (E3)
- **适配问题类型**：`performance_tuning`、`efficiency_improvement`
- **能力说明**：提升性能、降低资源消耗、改进流程效率。
- **典型示例**：优化 SQL 查询计划以降低延迟并减少 CPU 占用。

#### `auto_correction` (E4)
- **适配问题类型**：`error_recovery`、`code_auto_fix`
- **能力说明**：基于错误信息自动分析原因并生成修复方案，支持代码修复、参数调整、逻辑纠正等。
- **典型示例**：检测到断言失败后分析测试用例，自动修正算法实现中的边界条件或递推公式。

#### `stage_feedback` (E5)
- **适配问题类型**：`cross_stage_adjustment`、`upstream_correction`
- **能力说明**：将执行阶段发现的问题反馈到前置阶段，触发策略调整、能力重评估或计划修正。
- **典型示例**：代码执行失败时自动更新Stage 1的风险评估表格，并建议Stage 2选择备用策略。

#### `retry_orchestration` (E6)
- **适配问题类型**：`failure_recovery`、`adaptive_retry`
- **能力说明**：设计智能重试机制，包括退避策略、条件判断、资源分配与终止条件。
- **典型示例**：API调用失败时根据错误类型选择指数退避或立即重试，超过阈值后切换到降级方案。

---

### F. 创新与设计能力

#### `creative_ideation` (F1)
- **适配问题类型**：`brainstorming`、`product_ideation`
- **能力说明**：发散思维、跨域迁移并生成创新方案。
- **典型示例**：为在线教育应用设计新的互动激励机制。

#### `system_design` (F2)
- **适配问题类型**：`system_design`、`architecture_review`
- **能力说明**：进行系统架构划分、模块接口定义与协作策略设计。
- **典型示例**：设计高可用消息队列系统并说明扩展与容错策略。

---

### G. 跨模态与感知能力

#### `multimodal_understanding` (G1)
- **适配问题类型**：`multimodal_analysis`、`diagram_explanation`
- **能力说明**：解析图表、截图、公式等非文本信息并与文本对齐。
- **典型示例**：解读运营仪表盘截图并总结关键指标趋势与异常点。

---

### H. 伦理与安全能力

#### `safety_compliance` (H1)
- **适配问题类型**：`policy_compliance`、`security_review`
- **能力说明**：审查数据来源可靠性、最小化敏感数据并避免越权操作。
- **典型示例**：评估客户数据使用方案是否满足隐私与合规要求。

#### `ethical_judgment` (H2)
- **适配问题类型**：`ethical_assessment`、`fairness_analysis`
- **能力说明**：进行价值权衡、道德推理与公平性评估。
- **典型示例**：分析招聘算法对不同群体是否存在潜在偏见。

---

> 维护说明：新增或修改能力时，请按照“编号 + 问题类型 + 说明 + 示例”的结构补充内容，Stage1 Agent 会自动加载该能力库。
