from agno.agent import Agent
from agno.vllm import model

import asyncio

agent = Agent(model=model)

# agent.print_response("Tell me a 5 second short story about a robot")

# Or for streaming
# agent.print_response("Tell me a 5 second short story about a robot", stream=True)

# Or async
# await agent.aprint_response("Tell me a 5 second short story about a robot")

# Or for async streaming
# asyncio.run(agent.aprint_response(
#     "给我讲一个关于机器人的五秒钟短故事。", stream=True, debug_mode=True)
# )

agent.cli_app(input="Tell me a 5 second short story about a robot", stream=True)
