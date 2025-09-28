from agno.agent import Agent, RunOutput
from agno.vllm import model
from agno.utils.pprint import pprint_run_response
from typing import Iterator
from agno.agent import Agent, RunOutputEvent
from agno.models.openai import OpenAIChat
from agno.utils.pprint import pprint_run_response


agent = Agent(model=model, description='你是一个故事家')

# Run agent and return the response as a variable
response: RunOutput = agent.run("讲个鬼故事， 给出完整故事，别加省略号")

# Print the response in markdown format
pprint_run_response(response, markdown=True)


# agent2 = Agent(
#     model=model,
#     description="You write movie scripts.",
# )
#
# response = agent2.run("写一个关于生活在纽约的女孩的电影剧本")
# pprint_run_response(response, markdown=True)
#
# # Stream with intermediate steps
# response_stream: Iterator[RunOutputEvent] = agent2.run(
#     "Tell me a 5 second short story about a lion",
#     stream=True,
#     stream_intermediate_steps=True
# )
