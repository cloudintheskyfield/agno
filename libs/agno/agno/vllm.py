from agno.models.vllm import VLLM


model = VLLM(
    id='Qwen3-Omni-Thinking',
    base_url='http://223.109.239.14:10026/v1/',
    max_tokens=32768,
    temperature=1
)
