from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.vllm import q72b

agent = Agent(tools=[DuckDuckGoTools()], markdown=True, model=q72b)
agent.print_response("国内的9月最新新闻", stream=False)
