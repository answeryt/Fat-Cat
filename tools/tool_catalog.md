# 工具目录

本文档维护项目当前可用的外部工具清单，供各阶段 Agent 在生成规划或执行时引用。新增或下线工具时，请同步更新本目录。

## 工具分组概览

### 一、信息获取类

- **网络搜索**（tool_id: web_search）
  - 功能：统一网络搜索接口，支持 Tavily/Firecrawl 后端自动切换
  - 参数：query（搜索词）、max_results（结果数量）、provider（auto/tavily/firecrawl）
  - 适用：事实核验、资讯检索、背景调研、获取目标URL
  - 输出：结构化搜索结果，包含标题、摘要、URL链接

- **网页抓取**（tool_id: web_scrape）
  - 功能：提取指定URL网页的完整内容，转换为Markdown格式
  - 参数：url（目标网页地址）、format（输出格式，默认markdown）
  - 适用：深度阅读搜索结果、提取文章全文、获取详细数据
  - 输出：网页标题 + Markdown格式正文内容

- **GitHub 仓库搜索**（tool_id: github_search）
  - 功能：调用 GitHub Search API 搜索公开仓库，支持关键词、话题、语言等过滤
  - 参数：query（搜索词，支持 GitHub 搜索语法）、max_results（结果数量，默认10，最大30）、sort（排序字段：stars/forks/updated/best-match，默认stars）、order（排序方向：desc/asc，默认desc）
  - 适用：查找开源项目、技术调研、查询特定框架或模式的最新实现（如 agent 编排工作流）
  - 输出：仓库名、URL、简介、Stars、Forks、语言、标签、最近更新时间
  - 注意：设置 `GITHUB_TOKEN` 或 `GH_TOKEN` 环境变量可提升 API 频率上限（5000次/小时 vs 匿名10次/小时）

- **数学计算**（tool_id: calculate）
  - 功能：安全的数学表达式求值，支持math库函数
  - 参数：expression（数学表达式）
  - 适用：简单数学计算、公式验证
  - 输出：计算结果

### 二、代码执行类

- **代码解释器**（tool_id: code_interpreter）
  - 功能：在受控沙箱中执行 Python 代码
  - 适用：脚本编写、数据处理、算法验证、文档同步
  - 基础输出：代码执行结果、图表、处理后的数据结构（所有原始 `stdout/stderr` 需写入执行日志）
  - **子能力（依赖 `install_gaia_dependencies.py` 预装的库）**：
    - Excel / CSV：`pandas` + `openpyxl` 读取工作表、清洗列名、执行聚合或透视操作
    - PDF：`pypdf` 解码多页文档，提取文本与元数据
    - Image：`Pillow` 读取 PNG/JPEG，获取尺寸 / 模式 / EXIF
    - PDB / mmCIF：`BioPython` (`Bio.PDB`) 加载分子结构
    - HTTP 下载：`requests` 拉取远程附件或接口数据
  - 使用规范：凡涉及计算、附件解析或数据凭证，必须实际运行代码解释器并在 `execution_log.actual_output` 中记录 Raw Output 与结论

## 推荐基础链路示例

### 1. 「搜索 → 抓取 → 分析」（推荐组合）
- **步骤**：web_search → web_scrape → code_interpreter
- **适用场景**：需要深度信息获取和分析的任务
- **典型用法**：
  1. web_search 搜索关键词，获取相关URL列表
  2. web_scrape 抓取目标URL的完整内容
  3. code_interpreter 处理和分析抓取的数据
  4. LLM 整理并生成结论

### 2. 「调研 → 计算 → 总结」
- **步骤**：web_search → code_interpreter → 纯 LLM 总结
- **适用场景**：需要外部信息支持的分析计算任务
- **典型用法**：
  1. web_search 获取原始数据摘要
  2. code_interpreter 处理和分析数据
  3. LLM 整理并生成结论

### 3. 「纯计算验证」
- **步骤**：code_interpreter 或 calculate 独立执行
- **适用场景**：逻辑推理、算法验证、数学计算
- **典型用法**：直接调用完成计算任务

### 4. 「循环调研验证」
- **步骤**：web_search ↔ web_scrape ↔ code_interpreter 循环调用
- **适用场景**：需要多轮信息收集和验证的复杂任务
- **典型用法**：
  1. 初步搜索获取基础信息
  2. 抓取关键页面深入了解
  3. 代码分析发现数据缺口
  4. 补充搜索和抓取获取更多信息
  5. 重复直至验证完成

## 工具角色定位

- **web_search**：广度搜索角色，快速获取多个相关结果的摘要和URL
- **web_scrape**：深度获取角色，提取单个URL的完整内容
- **code_interpreter**：计算验证角色，负责数据处理、算法实现、结果验证
- **calculate**：轻量计算角色，快速完成简单数学运算

## 组合使用示例

```
# 场景：查找并分析某公司最新财报数据

# Step 1: 搜索获取URL
[TOOL_CALL]
tool: web_search
query: 苹果公司2024年Q3财报
max_results: 5
success_criteria:
- 返回结果包含财报相关链接
- 来源为官方或权威财经媒体
[/TOOL_CALL]

# Step 2: 抓取详细内容
[TOOL_CALL]
tool: web_scrape
url: https://investor.apple.com/...
format: markdown
success_criteria:
- 成功提取网页内容
- 内容包含财务数据
[/TOOL_CALL]

# Step 3: 代码分析数据
[TOOL_CALL]
tool: code_interpreter
code:
revenue = 94.93  # billion
profit = 23.64   # billion
margin = profit / revenue * 100
print(f"利润率: {margin:.2f}%")
success_criteria:
- 代码执行无报错
- 输出包含计算结果
[/TOOL_CALL]
```
