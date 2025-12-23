# 任务协作表（finish_form）

## 任务概览

- 任务目标：Black Book starred the actress and writer of what heritage?
- 任务状态：已完成
- 关键信息摘要：工具调用 10 次，完成 6 个阶段
---

## 外部信息

<!-- EXTERNAL_INFO_START -->
### 任务目标

Black Book starred the actress and writer of what heritage?

### 外部上下文


### 可用工具清单

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
<!-- EXTERNAL_INFO_END -->

---

## 阶段一：元能力分析（Stage 1）

<!-- STAGE1_ANALYSIS_START -->
### 1. `problem_type`
- **`type`**: `knowledge_lookup` / `fact_verification`
- **`key_challenges`**:
  - **实体消歧**：需要准确识别“Black Book”所指的具体对象（电影、书籍、组织等），存在同名实体干扰。
  - **属性精确查询**：问题要求查询演员和编剧的“heritage”（文化/民族/血统背景），而非简单的国籍或出生地，需要从传记资料中提炼。
  - **信息源可靠性**：答案依赖于外部网络信息，需验证信息来源的权威性（如维基百科、权威媒体），避免使用粉丝网站或不可靠博客。
  - **多步骤推理**：流程为“识别实体 → 查找主演/编剧 → 查询其背景 → 提炼‘heritage’”，任一环节出错都会导致最终答案错误。

### 2. `required_capabilities`
| 能力 ID | 名称 | 角色 | 风险 |
| :--- | :--- | :--- | :--- |
| **C1** | `knowledge_retrieval` | 核心执行能力。用于搜索“Black Book”电影信息、主演和编剧的个人背景资料，并筛选可信来源。 | 检索到过时、错误或来源不明的信息，导致后续推理基础错误。 |
| **A1** | `language_understanding` | 解析问题意图。将“heritage”抽象为“民族/文化/血统背景”，并指导检索方向，避免与“国籍”混淆。 | 对“heritage”理解偏差，导致检索关键词错误，例如只搜索“nationality”。 |
| **E1** | `verification` | 质量保障。对检索到的信息进行交叉验证（如对比多个来源），检查主演/编剧身份是否与电影匹配，确保答案一致性。 | 验证流于形式，未发现不同来源间的矛盾信息，或接受了单一不可靠来源的结论。 |
| **D1** | `tool_use` | 工具调用。按“搜索 → 抓取 → 分析”组合，有效使用 `web_search` 和 `web_scrape` 获取深度信息。 | 搜索查询构建不佳，或过度依赖摘要而忽略抓取全文进行细节核实。 |

### 3. `common_failure_modes`
- **错误护栏 #1 — 触发条件**: 对“Black Book”实体识别错误（如误认为是书籍而非电影）。**影响**: 后续所有搜索方向错误，答案完全偏离。**立即检查**: 使用 `web_search` 查询“Black Book movie cast writer”进行初步确认，阻止下游直到实体明确。
- **错误护栏 #2 — 触发条件**: 将“heritage”简单等同于“nationality”或“birthplace”。**影响**: 答案不准确（如回答“Dutch”而非“Jewish”）。**立即检查**: 在检索演员/编剧信息时，强制搜索包含“heritage”、“ethnicity”、“background”等关键词。
- **[外部警示]: 未能访问外部失败经验** — **触发条件**: 外部搜索失败，无法获取关于信息检索任务常见陷阱的社区经验。**影响**: 对潜在的“同名混淆”、“过时信息”、“来源偏见”等风险缺乏预判。**立即检查**: 将此视为高风险任务，要求下游阶段（Stage 2/3）对任何单一来源的信息保持高度怀疑，必须执行多源交叉验证。

### 4. `content_quality`
- **`completeness`**: `0.8` - 任务目标清晰，但缺乏对“Black Book”具体版本的限定（如上映年份），存在歧义空间。
- **`accuracy`**: `0.7` - 答案完全依赖外部动态信息，当前无法保证准确性。
- **`timeliness`**: `1.0` - 问题不涉及时效性强的数据，主要依赖相对稳定的个人背景信息。
- **`gaps`**: `None` - 所有可用信息（目标、工具）已明确。

### 5. `timeliness_and_knowledge_boundary`
- **知识边界**: 模型内部知识截止至2024年1月。关于电影《Black Book》（2006年）及其主演卡里斯·范·侯登（Carice van Houten）、编剧保罗·范霍文（Paul Verhoeven）等人的最新个人背景信息（如近期关于其血统的访谈）可能缺失，必须通过 `web_search` 获取最新资料。
- **外部验证需求**: 所有事实性断言（电影主演、编剧身份、个人血统）都必须引用来自维基百科、权威电影数据库（IMDb）或可靠新闻网站的外部来源。
<!-- STAGE1_ANALYSIS_END -->

---

## 阶段二-A：候选策略产出（Stage 2-A）

<!-- STAGE2A_ANALYSIS_START -->
### Stage 2-A: 候选策略选择

| strategy_id | title | summary | covers_challenges | risks_or_costs | notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **I4** | `authority_evidence_first_with_cross_source_snapshot` | 从模糊实体查询开始，通过权威来源确认实体及关联对象，并对其关键属性进行跨源快照验证，确保事实准确与可溯源。 | 1. **实体消歧**：通过限定词搜索明确目标实体。<br>2. **属性精确查询**：从权威页面提取“heritage”等属性。<br>3. **信息源可靠性**：强制使用权威来源并构建跨源快照验证。<br>4. **[外部警示] 缓解**：通过“跨源证据快照构建与验证”步骤，主动检测并处理来源矛盾，降低单一来源偏见风险。 | 1. **执行成本高**：需对每个关联对象进行至少两次权威抓取和快照对比，耗时较长。<br>2. **依赖网络质量**：若权威页面无法访问或信息缺失，流程可能受阻。 | **首选策略**。其步骤设计（实体确认→属性提取→跨源验证）与任务流程高度匹配，能系统性覆盖所有关键挑战，尤其是针对外部警示的验证要求。 |
| **I3** | `evidence_snapshot_verification` | 明确待验证事实，优先检索权威原始来源，通过至少两个独立渠道交叉验证数据，整理为结构化快照并输出带引用的结论。 | 1. **信息源可靠性**：核心是跨源交叉验证。<br>2. **属性精确查询**：通过快照对比确保“heritage”描述的准确性。<br>3. **[外部警示] 部分缓解**：通过多源验证降低过时或错误信息风险，但未像I4那样内置实体消歧和矛盾裁决机制。 | 1. **前提假设**：需要先明确待验证的具体事实（如“Carice van Houten的heritage是什么”），对初始实体识别依赖较强。<br>2. **矛盾处理有限**：若来源矛盾，策略仅提示进一步验证，缺乏强制增量搜索的故障保护。 | **备选策略**。作为I4的精简版，专注于验证环节。若任务实体已非常明确（如已知是2006年电影），可快速进入验证阶段。需与I1或初始搜索结合以完成实体识别。 |
| **I1** | `evidence_first_research` | 明确待验证假设列表，按优先级排序，对每一项先查找原始权威来源，再扩展至二次引用，记录时保留来源与可信度标记。 | 1. **信息源可靠性**：强调从权威原始来源开始。<br>2. **多步骤推理**：通过假设列表结构化研究过程。 | 1. **覆盖缺口**：**未直接覆盖[外部警示]**。策略本身不强制跨源验证，也未内置矛盾检测与裁决机制，仍存在接受单一不可靠来源结论的风险。<br>2. **对“heritage”理解依赖强**：若初始假设（搜索关键词）设置偏差，可能导致检索方向错误。 | **基础策略**。提供可靠信息检索的基本框架，但对抗外部警示所提风险的能力较弱。适合作为组合的一部分，为I3或I4提供初步信息搜集。 |

### Notes for Stage 2-B
1.  **首选I4**：因其设计完美匹配“模糊实体→关联对象→属性验证”的任务链，且内置了应对[外部警示]的跨源验证与矛盾裁决机制，是风险覆盖最全面的策略。
2.  **组合考量**：若考虑效率，可将**I1**用于快速实体识别与初步信息搜集，然后由**I3**进行深度验证。但此组合仍需人工确保I1的检索质量，且矛盾处理不如I4自动。
3.  **缺口提醒**：所有策略均依赖外部工具(`web_search`, `web_scrape`)的成功执行。若网络或工具出现故障，需有备用方案（如尝试不同查询词、切换提供商）。
<!-- STAGE2A_ANALYSIS_END -->

---

## 阶段二-B：策略遴选（Stage 2-B）

<!-- STAGE2B_ANALYSIS_START -->
### 1. Final Strategy Snapshot

- **strategy_id**: `I4`
- **strategy_title**: 基于权威证据与跨源快照的实体-关联对象属性验证策略
- **key_steps**:
  1.  **实体确认**：使用限定词（如“2006 film”）搜索“Black Book”，抓取权威页面（如维基百科）确认其为电影，并提取主演和编剧名单。
  2.  **属性初步提取**：针对名单中的每位关键人物（主演、编剧），分别抓取其个人权威页面（如维基百科、IMDb），初步提取关于其“heritage”（民族/血统背景）的描述。
  3.  **跨源快照验证**：为每个人物的“heritage”描述，再抓取一个独立可靠来源（如权威新闻网站、传记数据库）进行交叉验证，将两处信息整理为结构化快照，对比一致性。
  4.  **答案整合与溯源**：基于验证一致的快照，整合电影主演和编剧的heritage信息，形成最终答案。所有关键事实陈述必须附带可追溯的引用来源（URL及原文摘要）。
- **success_criteria**:
  1.  最终答案明确指出了电影《Black Book》的主演和编剧分别是谁，并准确描述了各自的heritage。
  2.  答案中的每项事实（人物身份、heritage描述）都至少有两个独立、可靠的来源支持，且来源信息一致。
  3.  输出包含了所有引用来源的链接和关键原文摘录，确保可验证性。
- **failure_indicators**:
  1.  无法通过权威来源明确识别出目标电影实体，或提取的主演/编剧名单存在明显错误或遗漏。
  2.  在跨源验证步骤中，对于关键人物的heritage描述，两个独立来源存在无法解释的根本性矛盾。
  3.  最终答案未能提供任何引用来源，或提供的来源不可靠（如粉丝网站、未经验证的博客）。

### 2. Handover Notes for Stage 3

- **key_ideas**:
  1.  **证据先行，权威优先**：所有信息必须从权威原始页面抓取，避免依赖摘要或二次加工内容。
  2.  **交叉验证，构建快照**：对每个关键属性（heritage）必须进行至少两个独立来源的交叉验证，并将结果结构化对比，这是质量的核心保障。
  3.  **全程溯源**：最终答案的每一部分都应有明确的来源“锚点”，确保可审计。
- **mapped_challenges**:
  - **实体消歧**：通过 `key_step 1` 使用限定词搜索和抓取权威页面来**机制避免**。
  - **属性精确查询**：通过 `key_step 2` 和 `3` 从个人页面提取“heritage”并进行跨源验证来**工具检测**。
  - **信息源可靠性**：通过强制使用权威页面和跨源快照验证来**机制避免**单一不可靠来源。
  - **[外部警示]: 未能访问外部失败经验**：通过 `key_step 3` 的跨源快照验证主动检测矛盾，并通过策略内置的故障保护（触发增量搜索）来**机制避免**对潜在陷阱（如过时信息、来源偏见）缺乏预判的风险。
- **tools_and_resources**:
  - **核心工具链**：`web_search` (用于初始实体搜索和寻找个人页面URL) → `web_scrape` (用于抓取维基百科、IMDb等权威页面全文) → LLM分析（用于提取信息、构建快照、整合答案）。
  - **备用方案**：若 `web_scrape` 对某个权威站点失败，可尝试用 `web_search` 查找该页面的其他镜像或缓存版本。
- **risks_and_assumptions**:
  1.  **假设权威页面信息准确且最新**：维基百科等页面可能未及时更新个人背景信息。**缓解**：通过跨源验证（如新闻网站）来检测并补充最新信息。
  2.  **假设“heritage”在个人页面中有明确描述**：可能页面只提及国籍或出生地。**缓解**：在提取信息时，需结合上下文（如“of ... descent”、“ethnic background”）进行推断，并在快照中注明推断依据。
  3.  **策略护栏 #1 — 触发条件**: 在 `key_step 3` 中，两个独立权威来源对同一人物的heritage描述存在根本性矛盾（如一个说“Dutch”，一个说“Jewish Dutch”）。**影响**: 无法生成可信的单一答案，强行选择可能导致错误。**故障保护**: 立即触发一次**增量搜索**，使用更具体的查询词（如“`[人物姓名] heritage controversy` 或 `ethnicity`”）寻找第三方裁决或最新澄清报道。若仍无法解决，则在最终答案中明确报告该矛盾点，说明各方说法，而非给出确定性结论。
- **tips_for_stage3**:
  1.  **顺序执行**：严格按 `key_steps` 顺序进行，完成实体确认后再处理个人页面，避免信息混淆。
  2.  **验证点前置**：在抓取个人页面后，立即检查该人物是否确实与电影《Black Book》关联（如页面作品列表），防止人物关联错误。
  3.  **并行处理**：在 `key_step 2` 和 `3`，可以对多位人物（主演、编剧）同步进行属性提取和跨源验证，以提升效率。
  4.  **结构化记录**：为每个人物创建一个简单的结构化笔记（如：`姓名`、`角色`、`来源1_heritage`、`来源2_heritage`、`验证状态`），便于最终整合。
  5.  **增量搜索准备**：如果触发策略护栏，进行增量搜索时，查询意图应聚焦于解决具体矛盾（例如：“Carice van Houten Jewish ancestry confirmation”），期望输出是能佐证某一方或提供新视角的权威文章。
<!-- STAGE2B_ANALYSIS_END -->

## 阶段二-C：能力升级评估（Stage 2-C）

<!-- STAGE2C_ANALYSIS_START -->
DECISION: APPLY
ACTION: enhance_existing
CATEGORY: I
TARGET_ID: I4
REFERENCE_IDS: I1,I3
coverage_gap: 现有策略 I1 和 I3 未系统性地处理从模糊实体查询到关联对象属性验证的完整链路，特别是缺乏对“实体-关联对象-属性”三层结构的明确拆解和验证。
reuse_failure: I1 专注于假设驱动的权威信息检索，但未强制要求对关联对象属性进行跨源验证；I3 专注于事实的跨源快照验证，但前提是待验证事实已明确，缺乏从模糊实体开始的引导机制。
new_value: 此补充为 I4 策略增加了明确的“挑战映射”和“故障保护”部分，将抽象的策略步骤与 Stage 1 分析中识别的具体风险（幻觉、矛盾、关联验证）直接挂钩，并提供了具体的矛盾处理流程（增量搜索），使策略更具可操作性和风险抵御能力。
REASON: 补充内容将策略步骤与具体挑战和故障保护机制关联，增强了策略的指导性和鲁棒性。

#### `authority_evidence_first_with_cross_source_snapshot` (I4)
- **适用场景**：需要从模糊实体查询开始，最终获取并验证其关联对象的特定属性（如人物血统、产品规格）的复杂信息检索任务。
- **策略步骤**：
  1.  **实体确认与权威信息获取**：使用限定词搜索明确目标实体，抓取权威页面（如维基百科、官方数据库）提取核心关联对象（如主演、编剧）。
  2.  **关键属性初步提取**：针对每个关联对象，搜索并抓取其个人权威页面，初步提取目标属性（如“heritage”）的描述。
  3.  **跨源证据快照构建与验证**：为每个对象的属性信息，再抓取一个独立可靠来源进行交叉验证，将两处描述整理为结构化快照，对比一致性。
  4.  **答案整合与溯源**：基于验证一致的快照整合最终答案，确保所有关键事实陈述都附带可追溯的引用来源（URL及原文摘要）。
- **典型示例**：查询电影《Black Book》主演和编剧的血统：先确认电影实体并获取人员名单；再分别查询各人员的维基百科页面提取血统描述；随后从IMDb或权威新闻网站获取第二来源验证；最后输出带引用和快照对比的完整答案。
- **注意事项**：若在步骤3中发现来源间存在根本性矛盾，应触发增量搜索寻求第三方裁决，而非强行给出结论。
- **挑战映射**：
  - **幻觉风险**：通过步骤2和3强制要求所有属性描述必须从权威页面提取并交叉验证，避免LLM生成未经证实的内容。
  - **边缘案例/矛盾**：步骤3的跨源快照构建会主动检测描述差异。若发现根本矛盾，将触发增量搜索（如搜索“`[人物姓名] heritage controversy`”）寻找第三方裁决。
  - **人物关联验证**：步骤1在提取名单后，必须执行显式检查，确认关联对象（如主演与编剧）是否为同一人（通过个人页面关联作品列表验证）。
- **故障保护**：若步骤3中两个独立权威来源对属性的描述存在无法调和的根本性矛盾，立即触发一次**增量搜索**，使用更具体的查询寻找第三方裁决或最新澄清。若仍无法解决，则在答案中明确报告矛盾点，而非强行给出结论。

AUTO_APPLY_STATUS: applied (enhanced existing strategy I4)
<!-- STAGE2C_ANALYSIS_END -->
---

## 阶段三：执行步骤规划（Stage 3）

<!-- STAGE3_PLAN_START -->
### 1. Execution Plan Overview

| step_id | goal | actions | expected_output | tools | quality_checks | related_risks |
|---------|------|---------|-----------------|-------|----------------|---------------|
| **S1-1** | 确认“Black Book”实体为电影，并获取其主演和编剧名单。 | 1. **精确搜索**：使用查询 `“Black Book” 2006 film cast writer` 进行 `web_search`。<br>2. **广泛搜索回退**：若精确搜索未返回明确结果，则使用 `“Black Book” film cast` 进行第二次搜索。<br>3. **抓取候选**：从搜索结果中，选择最权威的候选URL（如维基百科、IMDb页面），使用 `web_scrape` 抓取其完整内容。<br>4. **有限探索性执行**：使用 `code_interpreter` 快速检查抓取内容，确认页面明确提及“Black Book”是一部电影，并定位到“Cast”和“Writer(s)”或“Directed by”等相关章节。<br>5. **记录关键信息**：提取主演（主演女演员）和编剧（或导演/编剧）的姓名，并记录来源URL。 | 1. 一个文本文件 `entity_confirmation.txt`，包含：<br>   - 确认的实体：`Black Book (2006 film)`。<br>   - 主演女演员姓名 `A`。<br>   - 编剧姓名 `W`。<br>   - 来源URL `U1`。<br>2. 如果搜索失败（2次广泛搜索无结果），则记录差距到 `gaps_log.txt` 并停止。 | `web_search`, `web_scrape`, `code_interpreter` | 1. **描述**：搜索应返回至少1个包含“Black Book”和“film”关键词的权威结果（如维基百科、IMDb）。<br>2. **描述**：抓取的页面内容应明确包含“Cast”和“Writer”或类似章节，并能清晰识别出主演女演员和编剧的姓名。<br>3. **描述**：信息来源应为维基百科、IMDb或权威电影数据库。 | **错误护栏 #1**（实体识别错误）<br>**[外部警示]**（缺乏预判风险） |
| **S1-2** | 为主演 `A` 提取其“heritage”的初步描述。 | 1. **精确搜索**：使用查询 `“[主演姓名 A]” heritage ethnicity background` 进行 `web_search`。<br>2. **广泛搜索回退**：若未找到直接页面，则搜索 `“[主演姓名 A]” biography`。<br>3. **抓取候选**：选择最权威的个人页面URL（如维基百科传记页），使用 `web_scrape` 抓取。<br>4. **信息提取**：从抓取内容中，定位并提取与“heritage”、“ethnicity”、“descent”、“background”相关的描述性文本段落 `P_A1`。<br>5. **关联验证**：快速检查页面内容是否提及该演员与电影《Black Book》的关联（如作品列表）。<br>6. **记录**：将提取的描述 `P_A1` 和来源URL `U_A1` 写入结构化笔记。 | 1. 一个结构化笔记条目（例如，在 `heritage_notes.md` 中），包含：<br>   - 姓名：`A`<br>   - 角色：`Actress`<br>   - 来源1_heritage：`[描述文本 P_A1]`<br>   - 来源1_URL：`U_A1`<br>   - 验证状态：`待验证` | `web_search`, `web_scrape` | 1. **描述**：搜索应返回包含演员姓名和“heritage”或“ethnicity”关键词的相关结果。<br>2. **描述**：抓取的内容应包含明确的关于民族、血统或文化背景的描述性句子或段落，长度足以支持分析。<br>3. **描述**：信息来源应为可信的传记页面（如维基百科）或权威新闻/访谈。 | **错误护栏 #2**（heritage理解偏差）<br>**策略护栏 #1**（信息矛盾风险） |
| **S1-3** | 为编剧 `W` 提取其“heritage”的初步描述。 | 1. **精确搜索**：使用查询 `“[编剧姓名 W]” heritage ethnicity background` 进行 `web_search`。<br>2. **广泛搜索回退**：若未找到直接页面，则搜索 `“[编剧姓名 W]” biography`。<br>3. **抓取候选**：选择最权威的个人页面URL，使用 `web_scrape` 抓取。<br>4. **信息提取**：从抓取内容中，定位并提取与“heritage”相关的描述性文本段落 `P_W1`。<br>5. **关联验证**：快速检查页面是否提及该编剧与电影《Black Book》的关联。<br>6. **记录**：将提取的描述 `P_W1` 和来源URL `U_W1` 写入结构化笔记。 | 1. 更新 `heritage_notes.md`，添加编剧的笔记条目，包含：<br>   - 姓名：`W`<br>   - 角色：`Writer`<br>   - 来源1_heritage：`[描述文本 P_W1]`<br>   - 来源1_URL：`U_W1`<br>   - 验证状态：`待验证` | `web_search`, `web_scrape` | 1. **描述**：搜索应返回包含编剧姓名和背景关键词的相关结果。<br>2. **描述**：抓取的内容应包含关于其血统或文化背景的明确描述。<br>3. **描述**：信息来源应为可信的传记页面或权威资料。 | **错误护栏 #2**（heritage理解偏差）<br>**策略护栏 #1**（信息矛盾风险） |
| **S2-1** | 对主演 `A` 的“heritage”描述进行跨源验证。 | 1. **增量搜索 — 验证查询**：使用与S1-2不同的查询意图，如 `“[主演姓名 A]” ancestry family background interview` 进行 `web_search`，寻找独立来源。<br>2. **抓取候选**：从结果中选择一个与 `U_A1` 不同且可靠的URL（如权威新闻网站、传记数据库文章），使用 `web_scrape` 抓取。<br>3. **信息提取与对比**：从新页面提取关于 `A` 的“heritage”描述 `P_A2`。将 `P_A1` 与 `P_A2` 进行语义对比，检查核心事实（如具体的民族称谓）是否一致。<br>4. **裁决与记录**：<br>   - 若一致：在笔记中更新验证状态为`已验证`，并记录来源2_URL `U_A2` 和描述 `P_A2`。<br>   - **若触发策略护栏 #1**（根本性矛盾）：则执行“增量搜索 — 矛盾解决”，查询 `“[主演姓名 A]” heritage controversy clarification`，仅进行1次搜索。若找到裁决性文章，抓取并记录；若未找到，则在笔记中记录矛盾点。 | 1. 更新 `heritage_notes.md` 中主演 `A` 的条目，增加：<br>   - 来源2_heritage：`[描述文本 P_A2]` 或 `[矛盾说明]`<br>   - 来源2_URL：`U_A2` 或 `N/A`<br>   - 验证状态：`已验证` 或 `存在矛盾` | `web_search`, `web_scrape` | 1. **描述**：第二次搜索找到的来源应与第一次来源独立且权威。<br>2. **描述**：从第二个来源提取的描述应包含可对比的核心信息。<br>3. **描述**：对比结果应显示两个来源对核心民族/血统背景的描述在语义上一致。若不一致，必须触发矛盾处理流程。 | **策略护栏 #1**（信息矛盾）<br>**[外部警示]**（来源偏见/过时信息） |
| **S2-2** | 对编剧 `W` 的“heritage”描述进行跨源验证。 | 1. **增量搜索 — 验证查询**：使用与S1-3不同的查询，如 `“[编剧姓名 W]” Dutch heritage documentary` 进行 `web_search`。<br>2. **抓取候选**：选择独立可靠URL，使用 `web_scrape` 抓取。<br>3. **信息提取与对比**：提取描述 `P_W2`，与 `P_W1` 进行语义对比。<br>4. **裁决与记录**：同S2-1，处理一致或矛盾情况。 | 1. 更新 `heritage_notes.md` 中编剧 `W` 的条目，增加第二来源信息和验证状态。 | `web_search`, `web_scrape` | 1. **描述**：验证来源应独立且可信。<br>2. **描述**：提取的描述应可用于有效对比。<br>3. **描述**：对比结果应显示一致性或明确记录矛盾。 | **策略护栏 #1**（信息矛盾）<br>**[外部警示]**（来源偏见/过时信息） |
| **S3-1** | 整合已验证的信息，形成最终可溯源的答案。 | 1. **读取笔记**：从 `heritage_notes.md` 读取所有已验证（或标记矛盾）的人物信息。<br>2. **答案构建**：根据笔记，构建最终答案文本。格式为：<br>   - 电影《Black Book》的主演是 `[A]`，其heritage是 `[描述 H_A]`。<br>   - 编剧是 `[W]`，其heritage是 `[描述 H_W]`。<br>3. **引用附加**：为每个事实陈述附加对应的来源URL（`U_A1`, `U_A2`, `U_W1`, `U_W2`）及关键原文摘录。<br>4. **输出文件**：将最终答案写入 `final_answer.txt`，确保格式清晰。 | 1. 文件 `final_answer.txt`，包含：<br>   - 明确的最终答案陈述。<br>   - 每个陈述后附带的引用来源列表（URL和简短摘录）。<br>2. 如果存在未解决的矛盾，答案中需明确说明。 | (无) | 1. **描述**：最终答案必须明确回答“actress and writer of what heritage”这一问题。<br>2. **描述**：答案中的每个事实点（人物身份、heritage描述）都必须有至少一个已验证的来源引用。<br>3. **描述**：输出格式应便于阅读和验证。 | **成功标准 #1, #2, #3** |

### 2. Notes for Executor

- **关键检查点**：
  1.  **S1-1实体确认**：必须确认是“2006年电影”，并准确提取主演（女演员）和编剧姓名。这是所有后续步骤的基础。
  2.  **S2-1/S2-2跨源验证**：这是质量核心。必须确保两个来源独立，并进行语义级一致性对比。一旦发现根本矛盾，立即触发增量搜索解决，否则记录矛盾。
  3.  **S3-1溯源整合**：最终答案必须附带引用，确保可验证性，覆盖所有成功标准。

- **风险提示**：
  - **覆盖错误护栏 #1**：通过S1-1的限定词搜索和权威页面抓取来避免实体识别错误。
  - **覆盖错误护栏 #2**：通过在S1-2/S1-3的搜索查询中强制包含“heritage”、“ethnicity”等关键词，并在提取时关注描述性文本，而非仅国籍。
  - **覆盖[外部警示]**：通过S2-1/S2-2的跨源快照验证步骤，主动检测并处理来源矛盾、过时信息等风险。
  - **覆盖策略护栏 #1**：在跨源验证步骤（S2-1，S2-2）中内置了矛盾检测和增量搜索的故障保护流程。

### 3. 工具链

<toolchain>
<step>
<step_id>S1-1</step_id>
<tool_sequence>
<tool>
<tool_id>web_search</tool_id>
<input>用户问题 & Stage 2 策略</input>
<output>候选URL列表（用于确认电影实体）</output>
</tool>
<tool>
<tool_id>web_scrape</tool_id>
<input>候选URL（如维基百科页）</input>
<output>页面完整Markdown内容</output>
</tool>
<tool>
<tool_id>code_interpreter</tool_id>
<input>抓取的Markdown内容</input>
<output>确认实体类型及提取人名列表</output>
</tool>
</tool_sequence>
</step>
<step>
<step_id>S1-2, S1-3</step_id>
<tool_sequence>
<tool>
<tool_id>web_search</tool_id>
<input>从S1-1获取的人名 + “heritage”等关键词</input>
<output>个人传记页面URL</output>
</tool>
<tool>
<tool_id>web_scrape</tool_id>
<input>个人页面URL</input>
<output>个人页面完整内容</output>
</tool>
</tool_sequence>
</step>
<step>
<step_id>S2-1, S2-2</step_id>
<tool_sequence>
<tool>
<tool_id>web_search</tool_id>
<input>人名 + 不同的背景查询词</input>
<output>第二个独立来源的URL</output>
</tool>
<tool>
<tool_id>web_scrape</tool_id>
<input>第二个来源URL</input>
<output>第二个来源的完整内容</output>
</tool>
</tool_sequence>
</step>
</toolchain>
<!-- STAGE3_PLAN_END -->

---

## Live Execution Plan

<!-- LIVE_EXECUTION_PLAN_START -->
Objective: Black Book starred the actress and writer of what heritage?

| step_id | goal | status | tool | args | expected_output |
|---------|------|--------|------|------|-----------------|
| S1 | Search for the film "Black Book" to identify its starring actress and writer. | failed | web_search | {"query": "\"Black Book\" actress writer heritage", "max_results": 5} | Clear identification of the film's lead actress and writer. |
| S1.1 | Search for the film's Wikipedia page to get authoritative cast and crew info. | done | web_search | {"query": "Black Book 2006 film Wikipedia", "max_results": 3} | Direct link to the Wikipedia page for 'Black Book (2006 film)'. |
| S1.2 | Search for the film's starring actress and writer using specific names from the Wikipedia result. | done | web_search | {"query": "\"Black Book\" Carice van Houten Paul Verhoeven Gerard Soeteman starring writer", "max_results": 5} | Confirmation of the starring actress (Carice van Houten) and writers (Paul Verhoeven, Gerard Soeteman). |
| S2 | Extract the name of the starring actress and the writer from the film's page. | pending | scrape_website | {"url": "https://en.wikipedia.org/wiki/Black_Book_(film)", "extraction_instruction": "Extract the main article text, specifically the sections containing 'Starring' and 'Written by' or 'Screenplay by'. Focus on the first few paragraphs after the infobox."} | The main content of the Wikipedia page, including cast and crew. |
| S2.1 | Bypass donation banner and scrape the main content of the Wikipedia page. | pending | scrape_website | {"url": "https://en.wikipedia.org/wiki/Black_Book_(film)", "extraction_instruction": "Extract the main article text, specifically the 'Starring' and 'Written by' sections. Ignore any donation banners or pop-ups."} | The main content of the Wikipedia page, including cast and crew. |
| S2.2 | Use Google Cache to access the Wikipedia page and bypass the donation banner. | pending | google_cache | {"url": "https://en.wikipedia.org/wiki/Black_Book_(film)"} | A cached version of the Wikipedia page without the donation overlay. |
| S3 | Search for the heritage/ethnicity of the identified actress and writer. | done | web_search | {"query": "Carice van Houten heritage ethnicity", "max_results": 3} | Information about the actress's heritage. |
| S3.1 | Search for the heritage/ethnicity of the writer Paul Verhoeven. | pending | web_search | {"query": "Paul Verhoeven heritage ethnicity", "max_results": 3} | Information about the writer/director Paul Verhoeven's heritage. |
| S3.2 | Search for the heritage/ethnicity of the writer Gerard Soeteman. | pending | web_search | {"query": "Gerard Soeteman heritage ethnicity", "max_results": 3} | Information about the writer Gerard Soeteman's heritage. |
| S4 | Synthesize the answer based on the gathered heritage information. | pending | calculate | {"operation": "synthesize_answer", "data": "heritage info from S3, S3.1, and S3.2"} | A clear answer stating the heritage of the actress and writer(s) from Black Book. |
<!-- LIVE_EXECUTION_PLAN_END -->

---

## 阶段四：执行与复盘（Stage 4）

### 1. Execution Log

<!-- STAGE4_TOOL_CALLS_START -->
### 工具使用摘要

#### web_search
执行次数: 1
关键调用:
- 搜索查询: '"Black Book" actress writer heritage' | 返回 5 个结果

完整工具日志见: `.data/auto_generated_template_20251223_014749_raw_outputs.json`
<!-- STAGE4_TOOL_CALLS_END -->

<!-- STAGE4_FINAL_ANSWER_START -->
现在搜索编剧Paul Verhoeven的血统信息：

[TOOL_CALL]
tool: web_search
query: "Paul Verhoeven heritage ethnicity"
max_results: 3
[/TOOL_CALL]
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
Last revision for tool: web_search

```plan
Objective: Black Book starred the actress and writer of what heritage?

| step_id | goal | status | tool | args | expected_output |
|---------|------|--------|------|------|-----------------|
| S1 | Search for the film "Black Book" to identify its starring actress and writer. | failed | web_search | {"query": "\"Black Book\" actress writer heritage", "max_results": 5} | Clear identification of the film's lead actress and writer. |
| S1.1 | Search for the film's Wikipedia page to get authoritative cast and crew info. | done | web_search | {"query": "Black Book 2006 film Wikipedia", "max_results": 3} | Direct link to the Wikipedia page for 'Black Book (2006 film)'. |
| S1.2 | Search for the film's starring actress and writer using specific names from the Wikipedia result. | done | web_search | {"query": "\"Black Book\" Carice van Houten Paul Verhoeven Gerard Soeteman starring writer", "max_results": 5} | Confirmation of the starring actress (Carice van Houten) and writers (Paul Verhoeven, Gerard Soeteman). |
| S2 | Extract the name of the starring actress and the writer from the film's page. | pending | scrape_website | {"url": "https://en.wikipedia.org/wiki/Black_Book_(film)", "extraction_instruction": "Extract the main article text, specifically the sections containing 'Starring' and 'Written by' or 'Screenplay by'. Focus on the first few paragraphs after the infobox."} | The main content of the Wikipedia page, including cast and crew. |
| S2.1 | Bypass donation banner and scrape the main content of the Wikipedia page. | pending | scrape_website | {"url": "https://en.wikipedia.org/wiki/Black_Book_(film)", "extraction_instruction": "Extract the main article text, specifically the 'Starring' and 'Written by' sections. Ignore any donation banners or pop-ups."} | The main content of the Wikipedia page, including cast and crew. |
| S2.2 | Use Google Cache to access the Wikipedia page and bypass the donation banner. | pending | google_cache | {"url": "https://en.wikipedia.org/wiki/Black_Book_(film)"} | A cached version of the Wikipedia page without the donation overlay. |
| S3 | Search for the heritage/ethnicity of the identified actress and writer. | done | web_search | {"query": "Carice van Houten heritage ethnicity", "max_results": 3} | Information about the actress's heritage. |
| S3.1 | Search for the heritage/ethnicity of the writer Paul Verhoeven. | pending | web_search | {"query": "Paul Verhoeven heritage ethnicity", "max_results": 3} | Information about the writer/director Paul Verhoeven's heritage. |
| S3.2 | Search for the heritage/ethnicity of the writer Gerard Soeteman. | pending | web_search | {"query": "Gerard Soeteman heritage ethnicity", "max_results": 3} | Information about the writer Gerard Soeteman's heritage. |
| S4 | Synthesize the answer based on the gathered heritage information. | pending | calculate | {"operation": "synthesize_answer", "data": "heritage info from S3, S3.1, and S3.2"} | A clear answer stating the heritage of the actress and writer(s) from Black Book. |
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

```text
[CHECKLIST]
"指令1" -> [DONE/PENDING] (执行说明)
"指令2" -> [DONE/PENDING] (执行说明)
[/CHECKLIST]
```

<!-- EXECUTOR_CHECKLIST_END -->


---

## 完成文档位置索引

- `finish_form/auto_generated_template_20251222_171850.md`
- `finish_form/auto_generated_template_20251222_172244.md`
- `finish_form/auto_generated_template_20251222_172617.md`
- `finish_form/auto_generated_template_20251222_173001.md`
- `finish_form/auto_generated_template_20251222_175109.md`
- `finish_form/auto_generated_template_20251223_004405.md`
- `finish_form/auto_generated_template_20251223_012428.md`
- `finish_form/auto_generated_template_20251223_013052.md`
- `finish_form/auto_generated_template_20251223_014749.md`
---

## 详细信息索引

- 完整工具日志: `.data/auto_generated_template_20251223_014749_raw_outputs.json`
- 提取的结构化信息: `.data/auto_generated_template_20251223_014749_extracted_info.json`
- 工具调用总数: 10
- 阶段输出数量: 6
