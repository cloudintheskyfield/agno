"""Programmatic API for running the multi-people chat scenario.

This module wraps the helpers defined in `ws_12_multi_people_chat_agno.py` and exposes
functions that accept a topic and character configurations, returning the
conversation transcript as structured data instead of printing to stdout.
"""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple
from uuid import uuid4

from ws_12_multi_people_chat_agno import (
    _calc_length_guidance,
    _chunk_to_text,
    _is_stream_response,
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


def _prepare_chat(
    topic: str,
    *,
    characters: Optional[Sequence[Dict[str, Any]]],
    characters_config_path: Optional[Path | str],
    duration_seconds: int,
    session_id: Optional[str],
) -> Tuple[List[Any], str, str, str, str, str]:
    character_configs = _load_characters(
        characters=characters,
        characters_config_path=characters_config_path or DEFAULT_CONFIG_PATH,
    )
    agents = [build_agent(cfg) for cfg in character_configs]

    base_session = session_id.strip() if isinstance(session_id, str) else ""
    if base_session:
        final_session_id = base_session
    else:
        session_suffix = slugify(topic)
        unique_suffix = f"{session_suffix}-{uuid4().hex[:8]}" if session_suffix else uuid4().hex[:8]
        final_session_id = f"api-multi-chat-{unique_suffix}"

    base_prompt = (
        "请围绕上述主题分享你的洞见，语气自然、含蓄，"
        "在潜台词中体现你对其他伙伴观点的理解；无需直接说明引用来源。"
    )
    length_guidance = _calc_length_guidance(duration_seconds, len(agents))
    member_list = "、".join(agent.name for agent in agents)
    summary_intro = "、".join(f"{agent.name}" for agent in agents)

    return agents, final_session_id, base_prompt, length_guidance, member_list, summary_intro


def run_multi_people_chat(
    topic: str,
    *,
    characters: Optional[Sequence[Dict[str, Any]]] = None,
    characters_config_path: Optional[Path | str] = None,
    rounds: int = 1,
    duration_seconds: int = 10,
    session_id: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], str]:
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
    session_id:
        Optional fixed session identifier supplied by the caller. When omitted, a new
        unique session id is generated for each invocation.

    Returns
    -------
    tuple[list[dict], str]
        Ordered transcript entries together with the session identifier actually used.
    """

    (
        agents,
        session_id,
        base_prompt,
        length_guidance,
        member_list,
        _summary_intro,
    ) = _prepare_chat(
        topic,
        characters=characters,
        characters_config_path=characters_config_path,
        duration_seconds=duration_seconds,
        session_id=session_id,
    )

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

    return transcript, session_id


def stream_multi_people_chat(
    topic: str,
    *,
    characters: Optional[Sequence[Dict[str, Any]]] = None,
    characters_config_path: Optional[Path | str] = None,
    rounds: int = 1,
    duration_seconds: int = 10,
    session_id: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    """Yield streaming events for the multi-agent discussion.

    Each yielded dictionary contains either incremental ``delta`` text or the final
    ``content`` for an agent turn.
    """

    (
        agents,
        session_id,
        base_prompt,
        length_guidance,
        member_list,
        summary_intro,
    ) = _prepare_chat(
        topic,
        characters=characters,
        characters_config_path=characters_config_path,
        duration_seconds=duration_seconds,
        session_id=session_id,
    )

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
                stream=True,
            )

            chunks: List[str] = []
            if _is_stream_response(response):
                for chunk in response:  # type: ignore[assignment]
                    delta = _chunk_to_text(chunk)
                    if not delta:
                        continue
                    chunks.append(delta)
                    yield {
                        "type": "chunk",
                        "round": round_index,
                        "speaker": agent.name,
                        "delta": delta,
                        "elapsed": round(perf_counter() - start, 3),
                        "session_id": session_id,
                    }
                content = "".join(chunks).strip()
            else:
                content = getattr(response, "content", str(response)).strip()
                if content:
                    yield {
                        "type": "chunk",
                        "round": round_index,
                        "speaker": agent.name,
                        "delta": content,
                        "elapsed": round(perf_counter() - start, 3),
                        "session_id": session_id,
                    }

            elapsed = perf_counter() - start
            history.append(f"{agent.name}: {content}")
            yield {
                "type": "message",
                "round": round_index,
                "speaker": agent.name,
                "content": content,
                "elapsed": round(elapsed, 3),
                "session_id": session_id,
            }

    yield {
        "type": "summary",
        "topic": topic,
        "participants": summary_intro,
        "rounds": rounds,
        "session_id": session_id,
    }


__all__ = ["run_multi_people_chat", "stream_multi_people_chat"]
