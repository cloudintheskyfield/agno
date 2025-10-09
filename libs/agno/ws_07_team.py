# 首先禁用所有 metrics 输出
import disable_metrics

from agno.team import Team
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.vllm import q72b
# from agno.tools.openweather import OpenWeatherTools
from agno.tools.duckduckgo import DuckDuckGoTools  # 使用更稳定的 DuckDuckGo 搜索

print("🚀 启动 Team 测试...")
print("使用 DuckDuckGo 搜索工具替代 Google 搜索以避免连接问题")

agent_1 = Agent(name="News Agent", role="Get the latest news", model=q72b)

# 使用 DuckDuckGo 替代 Google 搜索，更稳定
agent_2 = Agent(
    name="Weather Agent",
    role="Get the weather for the next 7 days",
    model=q72b,
    tools=[DuckDuckGoTools()]
)

team = Team(name="News and Weather Team", members=[agent_1, agent_2], model=q72b)

# print("📝 执行查询: 今天东京天气怎么样?")
#
# try:
#     # Synchronous execution
#     result = team.run("今天东京天气怎么样?")
#
#     team.print_response("What is the weather in Tokyo?")
#
#     # Or for streaming
#     team.print_response("What is the weather in Tokyo?", stream=True)
#     print("✅ 查询完成")
#     # print(result)
# except Exception as e:
#     print(f"❌ 查询失败: {e}")
#     print("💡 建议: 检查网络连接或尝试使用其他搜索工具")

# Asynchronous execution
# result = await team.arun("What is the weather in Tokyo?")

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
    stream=True,
    stream_intermediate_steps=True
)
for event in response_stream:
    if event.event == "TeamRunContent":
        print(f"Content: {event.content}")
    elif event.event == "TeamToolCallStarted":
        print(f"Tool call started: {event.tool}")
    elif event.event == "ToolCallStarted":
        print(f"Member tool call started: {event.tool}")
    elif event.event == "ToolCallCompleted":
        print(f"Member tool call completed: {event.tool}")
    elif event.event == "TeamReasoningStep":
        print(f"Reasoning step: {event.content}")
