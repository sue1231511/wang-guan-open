"""Small file-backed runtime configuration store for the public edition.

The private project uses a richer database-backed configuration system. This public
module intentionally keeps only generic provider/model/prompt configuration so the
example MiniApp is useful without publishing the author's private UI or data model.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(os.environ.get("RUNTIME_CONFIG_PATH", "data/runtime_config.json"))
_LOCK = threading.RLock()

_DEFAULT = {
    "active_provider_id": None,
    "providers": [],
    "system_prompt": "You are a helpful AI assistant.",
}


def _ensure_parent() -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    with _LOCK:
        if not _CONFIG_PATH.exists():
            return json.loads(json.dumps(_DEFAULT))
        try:
            data = json.loads(_CONFIG_PATH.read_text("utf-8"))
        except Exception:
            return json.loads(json.dumps(_DEFAULT))
        merged = json.loads(json.dumps(_DEFAULT))
        if isinstance(data, dict):
            merged.update(data)
        if not isinstance(merged.get("providers"), list):
            merged["providers"] = []
        return merged


def save_config(data: dict[str, Any]) -> dict[str, Any]:
    clean = {
        "active_provider_id": data.get("active_provider_id"),
        "providers": data.get("providers") if isinstance(data.get("providers"), list) else [],
        "system_prompt": str(data.get("system_prompt") or "").strip(),
    }
    with _LOCK:
        _ensure_parent()
        tmp = _CONFIG_PATH.with_suffix(_CONFIG_PATH.suffix + ".tmp")
        tmp.write_text(json.dumps(clean, ensure_ascii=False, indent=2), "utf-8")
        tmp.replace(_CONFIG_PATH)
    return clean


def get_active_provider() -> dict[str, Any] | None:
    cfg = load_config()
    active = cfg.get("active_provider_id")
    for provider in cfg.get("providers", []):
        if str(provider.get("id")) == str(active):
            return provider
    return None


def get_system_prompt() -> str:
    return (load_config().get("system_prompt") or "").strip()
