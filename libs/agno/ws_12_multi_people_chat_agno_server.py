"""FastAPI server exposing the multi-people chat API."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Iterator, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ws_12_multi_people_chat_agno_api import run_multi_people_chat, stream_multi_people_chat

app = FastAPI(
    title="Multi People Chat Server",
    description="Wraps the workshop multi-agent chat into an HTTP API.",
    version="1.0.0",
)


class CharacterConfig(BaseModel):
    name: str
    title: Optional[str] = None
    role: Optional[str] = Field(default=None, description="角色设定或身份描述")

    class Config:
        extra = "allow"


class ChatRequest(BaseModel):
    topic: str = Field(..., description="讨论主题")
    characters: Optional[List[CharacterConfig]] = Field(
        default=None,
        description="自定义角色配置，缺省时读取原脚本默认角色",
    )
    rounds: int = Field(1, ge=1, le=10, description="总轮次，最大10轮")
    duration_seconds: int = Field(
        10,
        ge=1,
        le=120,
        description="预估生成时长，影响提示中的目标字数",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="可选的会话 ID；留空则自动生成新会话",
    )
    stream: bool = Field(
        False,
        description="是否返回流式输出（Server-Sent Text Stream）",
    )


class ChatResponse(BaseModel):
    topic: str
    rounds: int
    duration_seconds: int
    session_id: str
    transcript: List[Dict[str, Any]]


def _generate_stream(
    *,
    topic: str,
    characters: Optional[List[Dict[str, Any]]],
    rounds: int,
    duration_seconds: int,
    session_id: Optional[str],
) -> Iterator[str]:
    for event in stream_multi_people_chat(
        topic,
        characters=characters,
        rounds=rounds,
        duration_seconds=duration_seconds,
        session_id=session_id,
    ):
        payload = json.dumps(event, ensure_ascii=False)
        yield f"data: {payload}\n\n"


@app.get("/health", tags=["system"])
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    characters_data = (
        [character.dict() for character in payload.characters] if payload.characters else None
    )

    if payload.stream:
        try:
            generator = _generate_stream(
                topic=payload.topic,
                characters=characters_data,
                rounds=payload.rounds,
                duration_seconds=payload.duration_seconds,
                session_id=payload.session_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return StreamingResponse(generator, media_type="text/event-stream")

    try:
        transcript, session_id = run_multi_people_chat(
            payload.topic,
            characters=characters_data,
            rounds=payload.rounds,
            duration_seconds=payload.duration_seconds,
            session_id=payload.session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive branch
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        topic=payload.topic,
        rounds=payload.rounds,
        duration_seconds=payload.duration_seconds,
        session_id=session_id,
        transcript=transcript,
    )


__all__ = ["app"]


def _parse_env(name: str, default: str) -> str:
    import os

    return os.getenv(name, default)


if __name__ == "__main__":
    import uvicorn
    import asyncio

    host = _parse_env("CHAT_SERVER_HOST", "0.0.0.0")
    port = int(_parse_env("CHAT_SERVER_PORT", "8000"))
    reload = _parse_env("CHAT_SERVER_RELOAD", "false").lower() in {"1", "true", "yes"}

    try:
        uvicorn.run(app, host=host, port=port, reload=reload)
    except TypeError as exc:
        if "loop_factory" not in str(exc):
            raise

        config = uvicorn.Config(app, host=host, port=port, reload=reload, loop="asyncio")
        server = uvicorn.Server(config)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.serve())
