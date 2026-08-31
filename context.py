"""Generic context builder.

This public module intentionally contains no personal names, relationship rules,
health/location/work data, private memories, diaries, or private platform history.
Use providers below to assemble your own context.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Callable

ContextProvider = Callable[[], str]
_PROVIDERS: list[ContextProvider] = []


def register_context_provider(provider: ContextProvider) -> None:
    if provider not in _PROVIDERS:
        _PROVIDERS.append(provider)


def unregister_context_provider(provider: ContextProvider) -> None:
    if provider in _PROVIDERS:
        _PROVIDERS.remove(provider)


def _base_prompt() -> str:
    # Runtime config is optional. Environment variable remains a deployment-level
    # fallback, while the public MiniApp can edit the generic prompt without
    # exposing the private project's prompt system.
    try:
        from runtime_config import get_system_prompt
        runtime_prompt = get_system_prompt()
    except Exception:
        runtime_prompt = ""
    return (runtime_prompt or os.environ.get(
        "SYSTEM_PROMPT",
        "You are a helpful AI assistant. Follow the user's instructions and the configured policies.",
    )).strip()


def _time_context() -> str:
    return f"Current UTC time: {datetime.now(timezone.utc).isoformat(timespec='minutes')}"


def build_context() -> str:
    parts = [_base_prompt()]
    for provider in list(_PROVIDERS):
        try:
            value = (provider() or "").strip()
        except Exception as exc:
            value = f"[context provider failed: {type(exc).__name__}]"
        if value:
            parts.append(value)
    if os.environ.get("INCLUDE_TIME_CONTEXT", "1") != "0":
        parts.append(_time_context())
    return "\n\n".join(parts)


