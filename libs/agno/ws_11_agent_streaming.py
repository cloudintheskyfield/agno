import asyncio

from agno.agent import Agent, RunOutput, RunOutputEvent, RunEvent
from agno.models.anthropic import Claude
from agno.tools.hackernews import HackerNewsTools
from agno.utils.pprint import pprint_run_response
from agno.vllm import q72b, q3o, q3_32b, q3_coder_30b_a3b_instruct
from typing import Iterator


agent = Agent(
    model=q3_32b,
    # tools=[HackerNewsTools()],
    instructions="Write a report on the topic. Output only the report.",
    markdown=True,
    telemetry=False
)

# Run agent with input="Trending startups and products."
stream:  Iterator[RunOutputEvent] = agent.run(input="使用工具获取热门的初创企业和产品.", stream=True)



# Print the response in markdown format
for chunk in stream:
    # if chunk.event == RunEvent.tool_call_started:
    #     print('')
    if chunk.event == RunEvent.run_content:
        print(chunk.content)
    # if chunk.event != RunEvent.run_content:
    #     print('')

#
# asyncio.run(agent.aprint_response(
#     "热门的初创企业和产品。", stream=True, debug_mode=True)
# )
