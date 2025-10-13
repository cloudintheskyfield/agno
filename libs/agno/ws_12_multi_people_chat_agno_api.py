"""Programmatic API for running the multi-people chat scenario.

This module wraps the helpers defined in `ws_12_multi_people_chat_agno.py` and exposes
functions that accept a topic and character configurations, returning the
conversation transcript as structured data instead of printing to stdout.
"""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Iterable, List, Optional, Sequence
from uuid import uuid4

from ws_12_multi_people_chat_agno import (
    _calc_length_guidance,
    build_agent,
    load_character_configs,
    slugify,
    USER_ID,
)

DEFAULT_CONFIG_PATH = Path(__file__).with_name("characters_config.json")


def _normalise_characters(characters: Sequence[Dict[str, Any]]) -> List[Dict[str, str]]:
    return [
        {key: str(value) for key, value in character.items() if value is not None}
        for character in characters
    ]


def _load_characters(
    *,
    characters: Optional[Sequence[Dict[str, Any]]] = None,
    characters_config_path: Optional[Path | str] = None,
) -> List[Dict[str, str]]:
    if characters:
        return _normalise_characters(characters)

    if characters_config_path:
        config_path = Path(characters_config_path)
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                entries = data.get("characters")
                if isinstance(entries, Iterable):
                    return _normalise_characters(entries)  # type: ignore[arg-type]
            if isinstance(data, list):
                return _normalise_characters(data)

    return _normalise_characters(load_character_configs())


def run_multi_people_chat(
    topic: str,
    *,
    characters: Optional[Sequence[Dict[str, Any]]] = None,
    characters_config_path: Optional[Path | str] = None,
    rounds: int = 1,
    duration_seconds: int = 10,
    reuse_session: bool = False,
) -> List[Dict[str, Any]]:
    """Execute a round-based multi-agent discussion and return the transcript.

    Parameters
    ----------
    topic:
        Discussion topic supplied by the caller.
    characters:
        Optional sequence of character dictionaries (keys such as "name", "title",
        "role", "身份设定"). When omitted, the configuration file or default
        characters from the workshop script are used.
    characters_config_path:
        Optional path to a JSON config file. Only consulted when ``characters`` is
        not provided.
    rounds:
        Number of discussion rounds. Each round iterates through all agents once.
    duration_seconds:
        Target runtime budget. The helper scales expected character counts to guide
        response length (10 seconds ≈ 600-900 Chinese characters total).
    reuse_session:
        When ``True`` the session id is derived solely from the topic; otherwise a
        fresh UUID suffix is appended to avoid mixing transcripts across calls.

    Returns
    -------
    list[dict]
        Ordered transcript entries, each containing ``round`` (int), ``speaker``
        (agent name), ``content`` (str) and ``elapsed`` (float seconds).
    """

    character_configs = _load_characters(
        characters=characters,
        characters_config_path=characters_config_path or DEFAULT_CONFIG_PATH,
    )
    agents = [build_agent(cfg) for cfg in character_configs]

    session_suffix = slugify(topic)
    if not reuse_session:
        session_suffix = f"{session_suffix}-{uuid4().hex[:8]}"
    session_id = f"api-multi-chat-{session_suffix}"

    base_prompt = (
        "请围绕上述主题分享你的洞见，语气自然、含蓄，"
        "在潜台词中体现你对其他伙伴观点的理解；无需直接说明引用来源。"
    )
    length_guidance = _calc_length_guidance(duration_seconds, len(agents))
    member_list = "、".join(agent.name for agent in agents)

    transcript: List[Dict[str, Any]] = []
    history: List[str] = []

    for round_index in range(1, rounds + 1):
        for agent in agents:
            if history:
                recent = "\n".join(history[-4:])
                peer_guidance = (
                    f"已有观点摘录：\n{recent}\n"
                    "请至少点名回应其中一位成员的观点，可引用对方的具体主张或语气，"
                    "务必使用真实姓名或身份称谓，避免出现笼统表达。"
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
            response = agent.run(
                prompt,
                user_id=USER_ID,
                session_id=session_id,
                stream=False,
            )
            elapsed = perf_counter() - start
            content = getattr(response, "content", str(response)).strip()

            history.append(f"{agent.name}: {content}")
            transcript.append(
                {
                    "round": round_index,
                    "speaker": agent.name,
                    "content": content,
                    "elapsed": round(elapsed, 3),
                }
            )

    return transcript


__all__ = ["run_multi_people_chat"]
