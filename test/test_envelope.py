from __future__ import annotations

import asyncio

import pytest

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from context.envelope import build_agent_envelope, envelope_to_dict
from contracts.domain_contracts import (
    Stage1MetacognitivePayload,
    get_contract,
)
from model._model_response import ChatResponse
from stage1_agent.Metacognitive_Analysis_agent import MetacognitiveAnalysisAgent


@pytest.fixture
def stage1_payload() -> Stage1MetacognitivePayload:
    """构造真实契约模型 `Stage1MetacognitivePayload`，用于封装测试。"""

    return Stage1MetacognitivePayload(
        message="任务涉及事实检索与比较，核心挑战在于知识时效性。",
        data={
            "problem_type": {
                "label": "fact_verification",
                "reasoning": "任务要求比较两位公众人物的年龄，需要准确检索出生日期。",
            },
            "next_steps": [
                "使用外部搜索工具检索最新出生日期信息",
                "验证信息来源的可靠性",
            ],
            "key_challenges": [
                {"challenge": "缺乏实时数据", "impact": "可能导致结果滞后"}
            ],
            "required_capabilities": [
                {
                    "name": "knowledge_retrieval",
                    "ability_source": "library",
                    "role": "检索权威来源",
                    "risk": "忽视信息时效性",
                }
            ],
            "complexity_assessment": {"level": "medium", "drivers": ["多源对比"]},
            "timeliness_and_knowledge_boundary": {
                "status": "Knowledge Boundary: Insufficient",
                "note": "缺乏 2024 年后的更新",
            },
            "content_quality": {
                "completeness": 0.6,
                "accuracy": 0.5,
                "timeliness": 0.4,
                "gaps": ["需要实时信息核验"],
            },
        },
        metadata={
            "agent": "stage1_metacognitive",
            "language": "zh-CN",
        },
    )


def test_build_agent_envelope_with_contract(stage1_payload: Stage1MetacognitivePayload) -> None:
    """使用真实契约 payload 验证封装结构。"""

    contract = get_contract("stage1_metacognitive")
    contract_envelope = contract.envelope_model(payload=stage1_payload)

    envelope = build_agent_envelope(
        contract_envelope,
        agent_name="MetacognitiveAnalysisAgent",
        stage="stage1",
        function="metacognitive_analysis",
        doc="system prompt",
        model_name="deepseek-chat",
    )
    envelope_dict = envelope_to_dict(envelope)

    assert envelope_dict["agent"]["name"] == "MetacognitiveAnalysisAgent"
    assert envelope_dict["agent"]["stage"] == "stage1"
    assert envelope_dict["agent"]["function"] == "metacognitive_analysis"
    assert envelope_dict["payload"]["payload"]["message"].startswith("任务涉及事实检索")
    assert envelope_dict["meta"]["tags"]["model"] == "deepseek-chat"
    assert envelope_dict["meta"]["tags"]["contract_type"] == "stage1_metacognitive"
    assert envelope_dict["meta"]["tags"]["contract_version"] == "1.0.0"


class StubModel:
    """替代 DeepSeekChatModel 的桩对象，返回契约化 payload。"""

    model_name = "deepseek-chat"

    async def __call__(  # noqa: D401 - 与真实模型保持一致签名
        self,
        *,
        messages,
        structured_model=None,
        payload_contract=None,
        **kwargs,
    ) -> ChatResponse:
        contract = payload_contract or get_contract("stage1_metacognitive")
        payload = contract.payload_model(
            message="集成测试：由桩模型生成的分析内容。",
            data={
                "problem_type": {"label": "test", "reasoning": "just a test"},
                "key_challenges": [],
                "required_capabilities": [],
                "complexity_assessment": {"level": "simple", "drivers": []},
                "timeliness_and_knowledge_boundary": {"status": "ok", "note": ""},
                "content_quality": {
                    "completeness": 1.0,
                    "accuracy": 1.0,
                    "timeliness": 1.0,
                    "gaps": [],
                },
                "next_steps": [],
            },
            metadata={"agent": "stub"},
        )
        envelope = contract.envelope_model(payload=payload)
        return ChatResponse(content=tuple(), payload=envelope)


@pytest.fixture
def stub_agent(monkeypatch: pytest.MonkeyPatch) -> MetacognitiveAnalysisAgent:
    """构造使用桩模型的 MetacognitiveAnalysisAgent。"""

    agent = MetacognitiveAnalysisAgent.__new__(MetacognitiveAnalysisAgent)
    agent._system_prompt = "stub prompt"  # type: ignore[attr-defined]
    agent._model = StubModel()  # type: ignore[attr-defined]
    agent._default_contract = get_contract("stage1_metacognitive")  # type: ignore[attr-defined]
    return agent


def test_agent_integration_envelope(stub_agent: MetacognitiveAnalysisAgent) -> None:
    """集成调用 agent.analyze，验证封装成功附加在 metadata 中。"""

    response = asyncio.run(
        stub_agent.analyze(
            objective="验证 envelope 封装",
            context="用于测试的上下文。",
            recent_thoughts=None,
            conversation_history=None,
            critiques=None,
            pending_actions=None,
            tool_catalog=None,
        )
    )

    assert isinstance(response, ChatResponse)
    assert response.metadata and "_agent_envelope" in response.metadata

    agent_envelope = response.metadata["_agent_envelope"]
    assert agent_envelope["agent"]["name"] == stub_agent.agent_name
    assert agent_envelope["agent"]["stage"] == stub_agent.agent_stage
    assert agent_envelope["agent"]["function"] == stub_agent.agent_function
    assert agent_envelope["meta"]["tags"]["model"] == "deepseek-chat"
    assert agent_envelope["payload"]["payload"]["message"].startswith("集成测试：")

