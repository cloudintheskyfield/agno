"""Command-line client for the multi-people chat API helpers.

This script demonstrates both non-streaming and streaming usage of the
`run_multi_people_chat()` and `stream_multi_people_chat()` helpers. It prints
results to stdout so you can quickly verify the behaviour without running the
FastAPI server.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, List

from ws_12_multi_people_chat_agno_api import (
    run_multi_people_chat,
    stream_multi_people_chat,
)


logging.basicConfig(level=logging.ERROR)
logging.getLogger("agno").setLevel(logging.ERROR)
logging.getLogger("agno.agent").setLevel(logging.ERROR)


def _load_custom_characters(path: Optional[str]) -> Optional[Iterable[Dict[str, Any]]]:
    if not path:
        return None

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Custom characters file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, dict) and "characters" in data:
        characters = data["characters"]
    else:
        characters = data

    if not isinstance(characters, list):
        raise ValueError("Characters configuration must be a list or contain a 'characters' list")

    return characters  # type: ignore[return-value]


def run_non_stream(
    *,
    topic: str,
    rounds: int,
    duration_seconds: int,
    session_id: Optional[str],
    characters_path: Optional[str],
) -> None:
    characters = _load_custom_characters(characters_path)
    transcript, final_session_id = run_multi_people_chat(
        topic,
        characters=characters,
        rounds=rounds,
        duration_seconds=duration_seconds,
        session_id=session_id,
    )

    print("===== 非流式讨论结果 =====")
    print(f"Session ID: {final_session_id}")
    print(f"Topic     : {topic}")
    print(f"Rounds    : {rounds}")
    print()

    for entry in transcript:
        round_index = entry.get("round")
        speaker = entry.get("speaker")
        content = entry.get("content")
        elapsed = entry.get("elapsed")
        print(f"[Round {round_index}] {speaker} ({elapsed}s):")
        print(content)
        print("-" * 60)


def run_stream(
    *,
    topic: str,
    rounds: int,
    duration_seconds: int,
    session_id: Optional[str],
    characters_path: Optional[str],
) -> None:
    characters = _load_custom_characters(characters_path)
    print("===== 开始流式讨论 =====")
    current_round = None
    speaker_buffers: Dict[str, List[str]] = {}
    active_speaker: Optional[str] = None

    for event in stream_multi_people_chat(
        topic,
        characters=characters,
        rounds=rounds,
        duration_seconds=duration_seconds,
        session_id=session_id,
    ):
        event_type = event.get("type")

        if event_type == "chunk":
            round_index = event.get("round")
            if current_round != round_index:
                current_round = round_index
                print(f"\n--- 第 {current_round} 轮 ---")
                active_speaker = None
            speaker = event.get("speaker")
            delta = event.get("delta", "")
            if delta:
                speaker_buffers.setdefault(speaker, []).append(delta)
                if active_speaker != speaker:
                    if active_speaker is not None:
                        print()
                    print(f"[{speaker}] ", end="", flush=True)
                    active_speaker = speaker
                print(delta, end="", flush=True)
        elif event_type == "message":
            speaker = event.get("speaker")
            elapsed = event.get("elapsed")
            content = event.get("content") or "".join(speaker_buffers.pop(speaker, []))
            if active_speaker == speaker:
                print()
            if content.strip() and active_speaker != speaker:
                print(f"[{speaker}] {content.strip()}")
            print(f"✔️  {speaker} 发言完成（耗时 {elapsed}s）")
            active_speaker = None
        elif event_type == "summary":
            print("\n===== 讨论总结 =====")
            print(f"Topic     : {event.get('topic')}")
            print(f"Participants: {event.get('participants')}")
            print(f"Rounds    : {event.get('rounds')}")
            print(f"Session ID: {event.get('session_id')}")
        else:
            print(f"\n[未知事件] {event}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-people chat client")
    parser.add_argument("--topic", default='是不是应该工作', help="讨论主题")
    parser.add_argument("--rounds", type=int, default=1, help="讨论轮次，默认 1")
    parser.add_argument(
        "--duration-seconds",
        type=int,
        default=10,
        help="目标持续时间（秒），影响生成提示，默认 10",
    )
    parser.add_argument("--session-id", default=None, help="复用或指定的 session ID")
    parser.add_argument(
        "--characters",
        default=None,
        help="自定义角色配置文件路径（JSON，支持包含 'characters' 字段）",
    )
    parser.add_argument(
        "--stream",
        action="store_false",
        help="开启流式模式，默认关闭",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.stream:
        run_stream(
            topic=args.topic,
            rounds=args.rounds,
            duration_seconds=args.duration_seconds,
            session_id=args.session_id,
            characters_path=args.characters,
        )
    else:
        run_non_stream(
            topic=args.topic,
            rounds=args.rounds,
            duration_seconds=args.duration_seconds,
            session_id=args.session_id,
            characters_path=args.characters,
        )


if __name__ == "__main__":
    main()
