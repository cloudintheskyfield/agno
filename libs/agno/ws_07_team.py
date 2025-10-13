# 首先禁用所有 metrics 输出
import disable_metrics

import contextlib
from collections.abc import Iterable, Mapping
from typing import Any, Callable, Dict, Iterable as _IterableType, Iterator, Optional

from agno.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.run.team import TeamRunEvent
from agno.vllm import q72b
# from agno.tools.openweather import OpenWeatherTools
from agno.tools.duckduckgo import DuckDuckGoTools  # 使用更稳定的 DuckDuckGo 搜索

print("🚀 启动 Team 测试...")
print("使用 DuckDuckGo 搜索工具替代 Google 搜索以避免连接问题")

agent_1 = Agent(name="News Agent", id="news-agent", role="Get the latest news", model=q72b)

# 使用 DuckDuckGo 替代 Google 搜索，更稳定
agent_2 = Agent(
    name="Weather Agent",
    id="weather-agent",
    role="Get the weather for the next 7 days",
    model=q72b,
    tools=[DuckDuckGoTools()]
)


def _to_dict(arguments: Any) -> Dict[str, Any]:
    if isinstance(arguments, Mapping):
        return dict(arguments)
    if hasattr(arguments, "kwargs"):
        return dict(getattr(arguments, "kwargs") or {})
    if arguments is None:
        return {}
    if isinstance(arguments, Iterable) and not isinstance(arguments, (str, bytes, bytearray)):
        return dict(arguments)
    return dict(arguments)


def delegate_task_hook(
    function_name: str,
    function_call: Callable[..., Any],
    arguments: Any,
    session_state: Dict[str, Any],
    **_: Any,
):
    """为 delegate_task_to_member 自动补全参数，避免缺参报错"""

    if function_name != "delegate_task_to_member":
        return function_call(**_to_dict(arguments))

    args_dict = _to_dict(arguments)

    if not args_dict.get("member_id"):
        args_dict["member_id"] = session_state.get("preferred_member_id", "weather-agent")

    if not args_dict.get("task_description"):
        user_question = session_state.get("latest_user_query", "用户询问今天东京的天气")
        args_dict["task_description"] = (
            session_state.get("delegate_task_description")
            or f"请根据用户问题《{user_question}》查询并总结东京未来7天的天气情况"
        )

    if not args_dict.get("expected_output"):
        args_dict["expected_output"] = (
            session_state.get("delegate_expected_output")
            or "返回结构化摘要，至少包含每日天气现象、最高/最低气温"
        )

    session_state.setdefault("delegate_history", []).append({
        "member_id": args_dict["member_id"],
        "task_description": args_dict["task_description"],
        "expected_output": args_dict["expected_output"],
    })

    # 委托调用保持非流式，避免多个成员流式干扰
    with contextlib.ExitStack() as stack:
        stack.enter_context(_disable_streaming_context(session_state))
        result = function_call(**args_dict)

    return result


@contextlib.contextmanager
def _disable_streaming_context(session_state: Dict[str, Any]):
    """在委托工具执行期间标记非流式调用"""

    session_state.setdefault("_delegate_context", 0)
    session_state["_delegate_context"] += 1
    try:
        yield
    finally:
        session_state["_delegate_context"] -= 1


def _should_stream(session_state: Optional[Dict[str, Any]]) -> bool:
    if not session_state:
        return True
    if session_state.get("_delegate_context"):
        return False
    return session_state.get("enable_stream", True)


team = Team(
    name="News and Weather Team",
    members=[agent_1, agent_2],
    model=q72b,
    tool_hooks=[delegate_task_hook],
    show_members_responses=True,
    store_events=True,
)

# streaming fail
# for chunk in team.run("今天东京天气怎么样?", stream=True, stream_intermediate_steps=True):
#     print(chunk.content, end="", flush=True)

# async def f():
#     async for chunk in team.arun("今天东京天气怎么样?", stream=True, stream_intermediate_steps=True):
#         print(chunk.content, end="", flush=True)
#
# import asyncio
# asyncio.run(f())


# Stream with intermediate steps
response_stream = team.run(
    "今天东京天气怎么样?",
    stream=_should_stream({
        "latest_user_query": "今天东京天气怎么样?",
        "preferred_member_id": "weather-agent",
        "enable_stream": True,
    }),
    stream_intermediate_steps=True,
    session_state={
        "latest_user_query": "今天东京天气怎么样?",
        "preferred_member_id": "weather-agent",
        "enable_stream": True,
    },
)
for event in response_stream:
    if event.event == TeamRunEvent.run_content.value:
        print(f"Content: {event.content}")
    elif event.event == TeamRunEvent.tool_call_started.value:
        print(f"Tool call started: {event.tool}")
    elif event.event == TeamRunEvent.tool_call_completed.value:
        print(f"Tool call completed: {event.tool}")
    elif event.event == TeamRunEvent.reasoning_step.value:
        print(f"Reasoning step: {event.content}")
