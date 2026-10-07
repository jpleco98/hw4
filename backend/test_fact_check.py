"""Fact-checker test (usability improvement 3). No API key or network needed.

A scripted FunctionModel first answers with a wrong price ($45) and quantity (4); the output
validator in agent.py must reject it and the agent must end with the real values ($58, 2 left).

Run from backend/:  ../.venv/Scripts/python test_fact_check.py
"""
import asyncio
import os

os.environ.setdefault("PORTKEY_API_KEY", "test-not-used")  # model is overridden below
from pydantic_ai.messages import ModelResponse, ToolCallPart, RetryPromptPart, ModelRequest
from pydantic_ai.models.function import FunctionModel, AgentInfo
from agent import get_agent, USAGE_LIMITS
from models import ShopDeps

calls = []
def scripted(messages, info: AgentInfo):
    calls.append(len(calls))
    out = info.output_tools[0].name
    step = len(calls)
    if step == 1:
        return ModelResponse(parts=[ToolCallPart("check_stock", {"product_id": "saybrook-college-crewneck", "size": "L"})])
    if step == 2:  # hallucinated: wrong price and wrong quantity
        return ModelResponse(parts=[ToolCallPart(out, {"reply": "Yes! Only 4 left in L, and it's $45.00.", "product_ids": ["saybrook-college-crewneck"]})])
    # after the validator's retry message: corrected
    return ModelResponse(parts=[ToolCallPart(out, {"reply": "Yes! Only 2 left in L, and it's $58.00.", "product_ids": ["saybrook-college-crewneck"]})])

async def main():
    deps = ShopDeps()
    agent = get_agent()
    with agent.override(model=FunctionModel(scripted)):
        r = await agent.run("Is the Saybrook crewneck in L and how much?", deps=deps, usage_limits=USAGE_LIMITS)
    retry_msgs = [p.content for m in r.all_messages() if isinstance(m, ModelRequest) for p in m.parts if isinstance(p, RetryPromptPart)]
    print("model calls:", len(calls))
    print("validator feedback sent to model:", retry_msgs[0] if retry_msgs else None)
    print("final reply:", r.output.reply)
    print("report:", deps.fact_check)
    assert retry_msgs and "$45.00" in retry_msgs[0], "validator should have rejected the wrong price"
    assert "$58.00" in r.output.reply and "2 left" in r.output.reply
    assert deps.fact_check.retries == 1
    print("PASS: hallucinated numbers were caught and corrected")

asyncio.run(main())
