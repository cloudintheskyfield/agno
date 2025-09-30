from agno.models.vllm import VLLM
import langfuse_self_host

q3o = VLLM(
    id='/data/shared/Qwen3-Omni/model',
    # id='qwen2__5-72b',
    base_url='http://223.109.239.14:10022/v1/',
    max_tokens=32768,
    temperature=1,
)

q72b = VLLM(
    id='qwen2__5-72b',
    base_url='http://223.109.239.14:10000/v1/',
    max_tokens=10000,
    temperature=1,
)
