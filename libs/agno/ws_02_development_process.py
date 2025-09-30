from agno.agent import Agent
from agno.vllm import model
from agno.media import Image

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

# agent.cli_app(input="Tell me a 5 second short story about a robot", stream=True)
agent.print_response(
    "Tell me about this image and give me the latest news about it.",
    images=[
        Image(
            url="https://image.so.com/z?a=viewPage&ch=wallpaper&src=home_wallpaper&ancestor=list&clw=247#grpid=7f80c03365e58722ab4d1ad49f4c9b70&id=f0e9549b9e659288a2bb254e40433c85&prevsn=0&currsn=30"
        )
    ],
    stream=True,
)
