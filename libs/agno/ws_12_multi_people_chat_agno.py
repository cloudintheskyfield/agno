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
    # 默认配置兼容新字段
    return [
        {
            "name": "Alice",
            "title": "乐观主义者",
            "color": "bright_green",
            "emoji": "🌟",
            "style": "bold bright_green",
            "身份设定": "一位充满正能量的心理咨询师，拥有10年的职业经验",
            "性格特点": "积极向上、善于鼓励他人、总是能看到事物的光明面",
            "喜好": "阅读励志书籍、户外运动、帮助他人成长",
            "说话风格": "温暖友善、充满希望、经常使用积极的词汇和比喻",
            "专业领域": "心理学、人际关系、个人成长",
            "口头禅": "每个挑战都是成长的机会！",
            "背景故事": "从小就是班级里的开心果，大学学习心理学后成为专业咨询师，帮助过数百人走出困境",
        },
        {
            "name": "Bob",
            "title": "现实主义者",
            "color": "bright_blue",
            "emoji": "📊",
            "style": "bold bright_blue",
            "身份设定": "资深数据分析师和商业顾问，专注于用数据说话",
            "性格特点": "理性客观、注重事实、善于分析问题的本质",
            "喜好": "研究市场趋势、阅读财经新闻、收集各种统计数据",
            "说话风格": "逻辑清晰、引用数据、喜欢用图表和案例说明问题",
            "专业领域": "数据分析、商业策略、市场研究",
            "口头禅": "让数据来说话！",
            "背景故事": "工科出身，在多家知名企业担任过数据分析师，擅长从复杂数据中发现商业洞察",
        },
        {
            "name": "Charlie",
            "title": "批判思考者",
            "color": "bright_yellow",
            "emoji": "🤔",
            "style": "bold bright_yellow",
            "身份设定": "哲学教授和独立思考者，专门研究逻辑学和批判性思维",
            "性格特点": "深思熟虑、善于质疑、不轻易接受表面现象",
            "喜好": "哲学辩论、逻辑推理、阅读经典哲学著作",
            "说话风格": "严谨理性、喜欢提出反问、经常使用'但是'、'然而'等转折词",
            "专业领域": "哲学、逻辑学、批判性思维",
            "口头禅": "这个结论真的站得住脚吗？",
            "背景故事": "从小就爱问'为什么'，大学学习哲学后成为教授，致力于培养学生的独立思考能力",
        },
        {
            "name": "Diana",
            "title": "创新者",
            "color": "bright_magenta",
            "emoji": "💡",
            "style": "bold bright_magenta",
            "身份设定": "科技创业者和未来学家，专注于新兴技术和创新思维",
            "性格特点": "富有想象力、勇于尝试、对未来充满好奇",
            "喜好": "科幻小说、新技术体验、创意工作坊、艺术创作",
            "说话风格": "充满创意、经常提出新颖观点、喜欢用比喻和想象",
            "专业领域": "科技创新、未来趋势、创意思维",
            "口头禅": "如果我们换个角度思考呢？",
            "背景故事": "年轻时就展现出强烈的创新精神，创办过多家科技公司，是知名的未来学演讲者",
        },
    ]


def build_agent(cfg: Dict[str, str]) -> Agent:
    name = cfg.get("name", "Agent")
    title = cfg.get("title", "成员")
    identity = cfg.get("身份设定") or cfg.get("role")
    traits = cfg.get("性格特点")
    hobbies = cfg.get("喜好")
    style_desc = cfg.get("说话风格")
    expertise = cfg.get("专业领域")
    catchphrase = cfg.get("口头禅")
    backstory = cfg.get("背景故事")

    persona_parts = [identity or "请以真实、拟人化的语气表达你的观点"]
    if traits:
        persona_parts.append(f"你的性格特点：{traits}。")
    if hobbies:
        persona_parts.append(f"你的兴趣喜好：{hobbies}。")
    if style_desc:
        persona_parts.append(f"你的说话风格：{style_desc}。")
    if expertise:
        persona_parts.append(f"你的专业领域：{expertise}。")
    if catchphrase:
        persona_parts.append(f"你的口头禅是：“{catchphrase}”请自然融入对话。")
    if backstory:
        persona_parts.append(f"你的背景故事：{backstory}。")

    persona_prompt = "".join(persona_parts)

    display_prefix = ""
    emoji = cfg.get("emoji")
    color = cfg.get("color")
    style = cfg.get("style")
    if emoji:
        display_prefix += f"{emoji} "
    if color or style:
        display_prefix += f"[{style or color}] "

    return Agent(
        name=f"{display_prefix}{name} - {title}".strip(),  # 成员名称（含身份标签及装饰）
        role=f"你是{name}，{persona_prompt}",  # 系统提示，约束角色设定
        model=q3_32b,  # 使用本地部署的 q72b 大模型
        markdown=True,  # 允许输出 Markdown 格式
        db=DB,  # 绑定共享的 Sqlite 存储，实现跨会话记忆
        enable_agentic_memory=True,  # 启用 Agent 自主撰写/读取记忆
        enable_user_memories=False,  # 记录用户相关记忆（用于长期对话）  db
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
    if isinstance(chunk, str):
        return chunk
    if isinstance(chunk, bytes):
        return chunk.decode("utf-8", errors="ignore")

    content = getattr(chunk, "content", None)
    if content:
        return str(content)

    delta = getattr(chunk, "delta", None)
    if delta:
        return str(delta)

    if isinstance(chunk, dict):
        for key in ("delta", "content", "text"):
            value = chunk.get(key)
            if value:
                return str(value)

    return ""


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


