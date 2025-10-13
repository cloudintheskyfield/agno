from agno.models.vllm import VLLM
import langfuse_self_host
import os

os.environ['AGNO_TELEMETRY'] = 'false'

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
    max_tokens=11000,
    temperature=1,
)


q3_32b = VLLM(
    id='Qwen3-32B',
    base_url='http://223.109.239.14:10015/v1/',
    max_tokens=10000,
    temperature=1,
)

q3_coder_30b_a3b_instruct = VLLM(
    id='Qwen3-Coder-30B-A3B-Instruct',
    base_url='http://223.109.239.14:10014/v1/',
    max_tokens=30000,
    temperature=1,
)
