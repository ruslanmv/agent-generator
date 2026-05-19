"""POST /api/test/chat — exchange a chat turn against the configured provider.

Routes inference through whatever provider the Space is configured
with (defaults to OllaBridge). For the public demo this means real
OpenAI-compatible inference against the free OllaBridge Space at
ruslanmv-ollabridge.hf.space.

The endpoint is intentionally provider-agnostic — it loads the
``OllaBridgeProvider`` directly when the Space's provider is set to
``ollabridge`` / ``ollama``, and otherwise delegates to the
agent-generator BaseProvider registry. No tool calls are executed
server-side in the demo; the SPA renders them as visual cards.
"""

from __future__ import annotations

import time
from typing import Annotated, Literal

from agent_generator.providers import PROVIDERS
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..config import SpaceSettings, get_settings
from .ollabridge import _PairingSession, get_pairing_session

router = APIRouter(prefix="/api/test", tags=["test"])


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., max_length=8000)


class ChatRequest(BaseModel):
    agent_id: str | None = None
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=50)
    model: str | None = None
    system_prompt: str | None = Field(default=None, max_length=4000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=16, le=8192)


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    role: Literal["assistant"]
    content: str
    model: str
    usage: Usage
    elapsed_ms: int


def _flatten(messages: list[ChatMessage], system_prompt: str | None) -> str:
    """Collapse the message list into a single prompt string. The
    OllaBridge / Ollama free tier accepts a chat-completions array
    natively, but our BaseProvider contract only exposes a
    ``generate(prompt: str)`` method. So we render the conversation
    in a stable transcript format the model can pick up on."""
    parts: list[str] = []
    if system_prompt:
        parts.append(f"System: {system_prompt}\n")
    for m in messages:
        speaker = m.role.capitalize()
        parts.append(f"{speaker}: {m.content}")
    parts.append("Assistant:")
    return "\n\n".join(parts)


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    body: ChatRequest,
    settings: Annotated[SpaceSettings, Depends(get_settings)],
    session: Annotated[_PairingSession, Depends(get_pairing_session)],
) -> ChatResponse:
    provider_name = settings.provider
    if provider_name == "keyword":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "LLM provider is disabled (AG_DEMO_PROVIDER=keyword). Set the "
                "provider to ollabridge / openai / watsonx to enable chat."
            ),
        )
    provider_cls = PROVIDERS.get(provider_name)
    if provider_cls is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Provider '{provider_name}' is not registered.",
        )

    # Pull session pairing token + URL when present.
    server_url = session.server_url or settings.ollabridge_url
    token = session.token or settings.ollabridge_token

    shadow = type("ShadowSettings", (), {})()
    shadow.ollabridge_url = server_url
    shadow.ollabridge_model = body.model or settings.ollabridge_model
    shadow.ollabridge_token = token
    shadow.temperature = body.temperature
    shadow.max_tokens = body.max_tokens
    shadow.model = body.model or settings.ollabridge_model

    provider = provider_cls(shadow)
    prompt = _flatten(body.messages, body.system_prompt)

    started = time.perf_counter()
    try:
        content = provider.generate(prompt)
    except Exception as exc:  # noqa: BLE001 — surface upstream error verbatim
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{provider_name} call failed: {exc}",
        ) from exc
    elapsed_ms = int((time.perf_counter() - started) * 1000)

    # Best-effort usage accounting (BaseProvider.tokenize is a rough
    # estimate but enough for the inspector).
    try:
        prompt_tokens = provider.tokenize(prompt)
        completion_tokens = provider.tokenize(content)
    except Exception:  # noqa: BLE001
        prompt_tokens = completion_tokens = 0

    return ChatResponse(
        role="assistant",
        content=content,
        model=shadow.model or "unknown",
        usage=Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
        elapsed_ms=elapsed_ms,
    )
