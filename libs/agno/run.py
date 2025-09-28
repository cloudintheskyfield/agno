from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.vllm import VLLM
import langfuse_self_host
from langfuse_self_host import lf
from agno.tools.hackernews import HackerNewsTools

# model = VLLM(
#     id='/mnt/data3/nlp/ws/model/Qwen2/Qwen2.5-Omni-7B',
#     base_url='http://223.109.239.14:10011/v1/'
# )
model = VLLM(
    id='Qwen3-Omni-Thinking',
    base_url='http://223.109.239.14:10026/v1/',
    max_tokens=32768
)
agent = Agent(
    model=model,
    tools=[HackerNewsTools()],
    tool_choice="none",  # 禁用自动工具选择，因为VLLM服务器没有启用--enable-auto-tool-choice
    markdown=True,
)
p = lf.get_prompt('ws', label='latest')
agent.print_response("Summarize the top 5 stories on hackernews in Chinese", stream=True)
