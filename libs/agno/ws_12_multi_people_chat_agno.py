import disable_metrics

import json
import re
from collections.abc import Iterable
from time import perf_counter
from pathlib import Path
from typing import Dict, List

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.vllm import q72b, q3o, q3_coder_30b_a3b_instruct, q3_32b


CONFIG_PATH = Path(__file__).with_name("characters_config.json")
DB = SqliteDb(db_file="multi_people_chat.db")
USER_ID = "multi-agent-forum"


def load_character_configs() -> List[Dict[str, str]]:
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        characters = data.get("characters") if isinstance(data, dict) else None
        if isinstance(characters, list) and characters:
            return characters
    return [
        {"name": "Alice", "title": "乐观主义者", "role": "用积极乐观的视角参与讨论"},
        {"name": "Bob", "title": "现实主义者", "role": "用理性与数据进行分析"},
        {"name": "Charlie", "title": "批判思考者", "role": "提出问题并探索不同观点"},
        {"name": "Diana", "title": "创新者", "role": "分享前沿趋势与创意方案"},
    ]


def build_agent(cfg: Dict[str, str]) -> Agent:
    name = cfg.get("name", "Agent")
    title = cfg.get("title", "成员")
    persona = cfg.get("role") or cfg.get("身份设定") or "请以真实、拟人化的语气表达你的观点"
    return Agent(
        name=f"{name} - {title}",  # 成员名称（含身份标签）
        role=f"你是{name}，{persona}。",  # 系统提示，约束角色设定
        model=q3_32b,  # 使用本地部署的 q72b 大模型
        markdown=True,  # 允许输出 Markdown 格式
        db=DB,  # 绑定共享的 Sqlite 存储，实现跨会话记忆
        enable_agentic_memory=True,  # 启用 Agent 自主撰写/读取记忆
        enable_user_memories=True,  # 记录用户相关记忆（用于长期对话）  db
        add_memories_to_context=False,  # 将历史记忆注入上下文
        stream=False,
        add_history_to_context=False,  # 自动带入历史消息

        enable_session_summaries=True,  # 允许生成会话摘要
        add_session_summary_to_context=False,  # 将摘要注入上下文，支持长期回顾 实时动态记忆更新
    )


agents = [build_agent(cfg) for cfg in load_character_configs()]


def slugify(value: str) -> str:
    slug = re.sub(r"[^0-9a-zA-Z]+", "-", value).strip("-").lower()
    return slug or "topic"


def _calc_length_guidance(duration_seconds: int, speaker_count: int) -> str:
    base_total_chars = (600, 900)  # 约等于3-5分钟的讨论量
    duration = max(duration_seconds, 1)
    factor = duration / 10  # 以10秒为基准线性放缩
    total_min = int(base_total_chars[0] * factor)
    total_max = int(base_total_chars[1] * factor)
    per_min = max(80, total_min // max(speaker_count, 1))
    per_max = max(per_min + 40, total_max // max(speaker_count, 1))
    return (
        f"整体目标长度约为{total_min}-{total_max}字，每位成员控制在{per_min}-{per_max}字之间，"
        "请自然断句并保留对话的节奏感。"
    )


def _is_stream_response(response: object) -> bool:
    return isinstance(response, Iterable) and not isinstance(response, (str, bytes, dict))


def _chunk_to_text(chunk: object) -> str:
    if hasattr(chunk, "content") and getattr(chunk, "content"):
        return str(getattr(chunk, "content"))
    if hasattr(chunk, "delta") and getattr(chunk, "delta"):
        return str(getattr(chunk, "delta"))
    if isinstance(chunk, dict):
        for key in ("content", "delta", "text"):
            if chunk.get(key):
                return str(chunk[key])
    return str(chunk)


def chat(topic: str, rounds: int = 1, duration_seconds: int = 10) -> None:
    session_id = f"multi-chat-{slugify(topic)}"
    member_list = "、".join(agent.name for agent in agents)
    base_prompt = (
        "请围绕上述主题分享你的洞见，语气自然、含蓄，"
        "在潜台词中体现你对其他伙伴观点的理解；无需直接说明引用来源。"
    )
    length_guidance = _calc_length_guidance(duration_seconds, len(agents))
    history: List[str] = []

    for _ in range(rounds):
        for agent in agents:
            if history:
                recent = "\n".join(history[-4:])
                peer_guidance = (
                    f"已有观点摘录：\n{recent}\n"
                    "请至少点名回应其中一位成员的观点，可引用对方的具体主张或语气，"
                    "务必使用真实姓名或身份称谓，避免出现@某位伙伴等笼统表达。"
                )
            else:
                peer_guidance = (
                    f"参与者名单：{member_list}。你是开场者之一，请给出鲜明立场，"
                    "同时埋下可供其他伙伴延伸的线索。"
                )

            prompt = (
                f"讨论主题：《{topic}》。{base_prompt}"
                f"\n{peer_guidance}"
                f"\n{length_guidance}\n请保持角色设定，言之有物而不过度赘述。"
            )
            start = perf_counter()
            reply = agent.run(
                prompt,
                user_id=USER_ID,
                session_id=session_id,
                stream=True,
            )
            if _is_stream_response(reply):
                print(f"{agent.name} (流式输出):", flush=True)
                segments: List[str] = []
                for chunk in reply:  # type: ignore[assignment]
                    text = _chunk_to_text(chunk)
                    if text:
                        print(text, end="", flush=True)
                        segments.append(text)
                print()  # 换行
                content = "".join(segments).strip()
            else:
                content = getattr(reply, "content", str(reply)).strip()
                print(content)
            elapsed = perf_counter() - start
            print(f"{agent.name} (耗时 {elapsed:.2f}s)\n")
            history.append(f"{agent.name}: {content}")


if __name__ == "__main__":
    chat("应不应该上班", rounds=1, duration_seconds=6)


