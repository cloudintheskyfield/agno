from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.vllm import VLLM
import langfuse_self_host
from langfuse_self_host import lf
from agno.tools.hackernews import HackerNewsTools

# 启用流式输出调试（详细模式）
try:
    from stream_debug_utils import enable_stream_debug
    enable_stream_debug(verbose=True)
    print("✅ 流式输出调试已启用（详细模式）")
except ImportError:
    print("⚠️ 流式调试工具不可用，使用基础调试")

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

print("\n🚀 开始流式响应测试...")
print("你将看到每个 chunk 的详细调试信息：")
print("• Chunk 编号和内容长度")
print("• 每个 chunk 的实际内容")
print("• 最终的统计信息")
print("=" * 60)

p = lf.get_prompt('ws', label='latest')
agent.print_response("Summarize the top 5 stories on hackernews in Chinese", stream=True)
