# Fat-Cat: The LLM-Native Operating System

A next-generation Agent framework based on global document context and multi-stage reasoning

> 📄 **Paper**: This method is described in detail in our paper, which has been published on arXiv.  
> **Paper Link**: [https://arxiv.org/abs/2602.02206](https://arxiv.org/abs/2602.02206)

<p align="center">
  <img src="image.png" alt="Fat-Cat Framework" width="800">
</p>

## 1. Background & Pain Points: Why Do We Need Fat-Cat?

In the current LLM Agent development paradigm, engineers are facing two core challenges: "the quagmire of context management" and "fragile control flow". I summarize these challenges as the three original sins of Agent design:

### Pain Point One: The JSON Trap

Traditional Agent frameworks (such as early LangChain patterns or Assistant API) tend to pass state through complex JSON objects or list dictionaries.

**Problem:** LLMs are essentially trained on text. Forcing models to parse deeply nested JSON states leads to attention dilution—models often see the trees but miss the forest, easily overlooking critical constraints.

**Engineer's Nightmare:** When debugging, facing thousands of lines of JSON dumps makes it difficult to intuitively understand what the Agent is actually "thinking".

### Pain Point Two: The Static Toolset

Most Agents have "hard-coded" capabilities. When facing unknown problems, Agents can only operate within preset if-else statements or fixed DAG graphs. They lack the ability for **Runtime Learning** and cannot acquire new skills by consulting resources like humans do.

### Pain Point Three: The Absence of Metacognition

This is the most fatal weakness of current Agents—"only execution, no reflection".

**Phenomenon:** Traditional Agents receiving tasks act like reckless interns, directly starting to call tools. Once they hit a dead end (such as code errors or failed searches), they often fall into infinite retry loops or generate hallucinations, forcibly providing wrong answers.

**Missing Link:** Lack of a high-level "monitor" process to evaluate: "Am I doing this correctly?", "Can my current strategy solve this problem?", "Do I need to stop and replan?".

Fat-Cat aims to solve the above problems. It is not just a Bot that executes tasks, but an operating system prototype with "self-awareness" and "evolutionary capabilities".

## 2. Core Design Philosophy

### 2.1 LLM as Operating System

In Fat-Cat, we treat LLM as CPU, Context (document context) as memory (RAM), and external tools as peripherals (I/O).

The Fat-Cat framework itself acts as the Kernel, responsible for process scheduling (Stage switching), memory management (Memory Bridge), and exception handling (Watcher Agent).

### 2.2 Document as Global Context

We abandon fragmented JSON and adopt Markdown documents as carriers of global state. Each Stage's output is a "revision" or "supplement" to this global document.

- Stage 1 generates reasoner.md (problem analysis document)
- Stage 2 generates strategy.md (tactical manual)
- Stage 3 generates step.md (SOP execution table)
- Stage 4 executes and backfills results.

This design makes the Agent's "thinking process" completely visible and debuggable to humans.

## 3. Core Features Deep Dive: Fat-Cat's Metacognitive System

Fat-Cat's core breakthrough lies in constructing a hierarchical metacognitive closed loop. This is not simple Prompt Engineering, but rather forcing Agents to "think twice before acting" through architecture.

🧠 **Stage 1: Metacognitive Analysis (Deep Intent Perception)**

"Think about how to do it before starting"

Traditional Agents receiving "help me write a crawler" might directly start writing code. But in Fat-Cat, Stage 1 Agent (Metacognitive_Analysis_agnet.py) will force metacognitive analysis through reasoner.md:

- **Intent Decomposition:** Does the user really just want code, or do they need deployment?
- **Constraint Extraction:** What are the implicit language, performance, and dependency library requirements?
- **Information Completeness Check:** If information is insufficient, it will refuse to execute and request supplementation, rather than guessing blindly.

🧭 **Stage 2: Dynamic Strategy & Metacognitive Search**

"Know what you don't know, and actively learn"

This is Fat-Cat's most innovative module (stage2_capability_upgrade_agent).

- **Strategy Retrieval:** The Agent first searches the local strategy_library for similar problem-solving experiences.
- **Metacognitive Judgment:** If the retrieved strategies have low matching scores (e.g., encountering a completely new framework or error), the Agent will trigger a **"Capability Upgrade"** signal.
- **Metacognitive Search:**

At this point, the Agent will suspend the current task and launch a subprocess to learn from the internet (via the built-in no‑API search backends and optional headless browser automation). It's not searching for "answers", but rather searching for "methodologies to solve this type of problem".

**Example:** When encountering a new Python library, the Agent will first read the official documentation, summarize usage, generate a new Markdown strategy file to store in the library, and then return to solve the user's problem.

📝 **Stage 3: Logical Step Decomposition**

"Solidify thinking into instructions"

After understanding the problem (Stage 1) and learning the method (Stage 2), Stage 3 (Step_agent.py) will generate a detailed SOP (Standard Operating Procedure). This is not vague natural language, but strict steps similar to pseudocode, ensuring Stage 4's executor won't go astray.

👁️ **Watcher Agent: Runtime Reflection**

"An observer standing outside the system"

Watcher_Agent is an independently running daemon process. It doesn't participate in specific tasks, but monitors global document changes like watching surveillance footage.

- **Infinite Loop Detection:** If Stage 4 outputs the same error log three times consecutively.
- **Goal Deviation:** If execution results don't match the metacognitive goals defined in Stage 1.
- **Intervention Mechanism:** Watcher has the highest authority to interrupt the current Agent, force rollback, or request human intervention.

## 4. Architecture Details & Directory Structure

<p align="center">
  <img src="image.png" alt="Fat-Cat Architecture" width="800">
</p>

```bash
Fat-Cat/
├── agents/                 # Base Agent class definitions
├── ability_library/        # Core capability definitions (Markdown descriptions)
├── strategy_library/       # [Long-term Memory] Strategy library, storing learned problem-solving approaches
├── form_templates/         # Structured output templates
├── stage4_agent/           # [I/O Layer] Tool bridge (web_search/web_scrape/sandbox_*)
├── Memory_system/          # [Memory Management] Handles Markdown document read/write flow
├── Document_Checking/      # [Memory Integrity] Prevents context loss
├── stage1_agent/           # [Prefrontal Cortex] Metacognitive analysis: generates reasoner.md
├── stage2_agent/           # [Scheduler] Strategy selection: generates strategy.md
├── stage2_capability_upgrade_agent/ # [Evolution Module] Responsible for metacognitive search and strategy generation
├── stage3_agent/           # [Commander] Step decomposition: generates step.md
├── stage4_agent/           # [Executor] Task execution and tool invocation
├── Watcher_Agent/          # [Watchdog] Runtime monitoring and exception circuit breaking
├── workflow/               # Pipeline orchestration
├── config/                 # Configuration
└── main.py                 # Entry point
```

## 5. Benchmark Results & Performance Evaluation

To validate the effectiveness of the Fat-Cat framework, we conducted comprehensive benchmark evaluations comparing Fat-Cat Agent against the baseline React Agent across multiple challenging tasks. The results demonstrate significant improvements in accuracy and reliability.

### Experimental Setup

We evaluated both agents on four diverse benchmark datasets, each representing different types of reasoning challenges:

- **HotPotQA (sample200)**: Multi-hop question answering requiring information synthesis across multiple documents
- **Bamboogle**: Complex web search and information retrieval tasks
- **Med_QA (中文)**: Chinese medical question answering, testing domain-specific knowledge and language understanding
- **MBPP**: Python code generation benchmark, evaluating programming capability and code correctness

Both agents were tested under identical conditions using the same LLM models and API configurations to ensure fair comparison. The LLM used was Kimi-K2.

### Performance Comparison

<p align="center">
  <img src="image2.png" alt="Performance Comparison of React Agent and Fat-Cat Agent" width="800">
</p>

### Key Findings

The benchmark results reveal consistent and substantial improvements across all evaluated tasks. As shown in the comparison chart above, Fat-Cat Agent consistently outperforms the React Agent baseline across all four benchmark datasets.

### Analysis & Insights

**1. Multi-Hop Reasoning (HotPotQA)**
The largest improvement (+12.58%) was observed in HotPotQA, which requires synthesizing information from multiple sources. Fat-Cat's metacognitive analysis (Stage 1) and strategic planning (Stage 2) enable better information gathering and cross-document reasoning compared to the reactive baseline.

**2. Code Generation (MBPP)**
Fat-Cat achieved 95.3% accuracy on MBPP, demonstrating the effectiveness of its step-by-step decomposition (Stage 3) and execution planning. The Watcher Agent's runtime monitoring helps catch errors early, preventing cascading failures.

**3. Domain-Specific Tasks (Med_QA)**
Even in specialized domains like medical QA, Fat-Cat's capability upgrade mechanism (Stage 2-C) allows it to learn domain-specific strategies, resulting in a 4% improvement over the baseline.

**4. Web Search & Retrieval (Bamboogle)**
Fat-Cat's metacognitive search capability enables more targeted information retrieval, improving accuracy by 5.4% on complex web search tasks.

### Why Fat-Cat Performs Better

The superior performance can be attributed to Fat-Cat's core architectural advantages:

1. **Metacognitive Analysis**: Stage 1's deep intent perception prevents premature execution and reduces errors from misunderstanding requirements.

2. **Dynamic Strategy Learning**: Stage 2's capability upgrade mechanism allows the Agent to learn new problem-solving approaches on-the-fly, rather than being limited to hard-coded strategies.

3. **Structured Execution**: Stage 3's logical step decomposition creates executable plans that are less prone to deviation and errors.

4. **Runtime Monitoring**: The Watcher Agent provides continuous oversight, detecting and preventing infinite loops, goal deviations, and cascading failures.

5. **Document-Centric Context**: The Markdown-based global context maintains better state coherence across complex multi-step reasoning tasks compared to fragmented JSON state management.

These results validate that Fat-Cat's metacognitive architecture and document-centric design significantly enhance Agent reliability and accuracy across diverse reasoning tasks.

## 6. Quick Start

### Requirements

- Python 3.10+
- Dependencies listed in requirements-full.txt

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-repo/fat-cat.git
cd fat-cat

# 2. Install dependencies (one-click script provided)
python scripts/install_full_pipeline_deps.py
```

### Configuration

Configure LLM API Key in config/model_config.py. Fat-Cat is optimized for long-context models (such as Kimi-K2). It is recommended to use models supporting 32k+ Context for the best experience.

### Running

```bash
# Start the full pipeline
python workflow/full_pipeline_runner.py
```

## 7. Developer Guide: Extension & Evolution

Fat-Cat is a living system. You can make it stronger through the following methods:

### Adding New Tools

Register new tools in `stage4_agent/tools_bridge.py` using the `@tool` decorator. Stage 4 will discover and execute them via the ToolsBridge registry.

### Manual Knowledge Injection (Strategy Injection)

In addition to letting the Agent learn online by itself, you can also directly add Markdown-formatted technical documents to strategy_library/. Stage 2 Agent will immediately index these new knowledge through RAG.

### Adjusting Metacognitive Thresholds

In stage2_agent, you can adjust the confidence threshold for strategy matching. The higher the threshold, the more the Agent tends to trigger "capability upgrades" to search for new knowledge rather than relying on old experience.

## 8. License

[License Information]
