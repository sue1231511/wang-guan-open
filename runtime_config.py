"""Generic file-backed runtime configuration for the public edition."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(os.environ.get("RUNTIME_CONFIG_PATH", "data/runtime_config.json"))
_LOCK = threading.RLock()
_MAX_PROVIDERS = 100
_MAX_KEYS = 50
_MAX_MODELS = 100

_DEFAULT = {
    "active_provider_id": None,
    "providers": [],
    "system_prompt": "You are a helpful AI assistant.",
}


def _clone_default() -> dict[str, Any]:
    return json.loads(json.dumps(_DEFAULT))


def _ensure_parent() -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _string_list(value, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value[:limit]:
        text = str(item or "").strip()
        if text:
            out.append(text)
    return out


def _clean_provider(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    pid = str(raw.get("id") or "").strip()
    name = str(raw.get("name") or "").strip()[:120]
    base_url = str(raw.get("base_url") or "").strip().rstrip("/")
    api_keys = _string_list(raw.get("api_keys"), _MAX_KEYS)
    if not api_keys and raw.get("api_key"):
        api_keys = [str(raw.get("api_key")).strip()]
    models = _string_list(raw.get("models"), _MAX_MODELS)
    if not models and raw.get("model"):
        models = [str(raw.get("model")).strip()]
    active_model = str(raw.get("active_model") or raw.get("model") or "").strip()
    if active_model not in models and models:
        active_model = models[0]
    headers = raw.get("extra_headers") if isinstance(raw.get("extra_headers"), dict) else {}
    headers = {
        str(k).strip()[:120]: str(v)[:4000]
        for k, v in list(headers.items())[:50]
        if str(k).strip()
    }
    try:
        key_index = int(raw.get("current_key_index", 0))
    except Exception:
        key_index = 0
    if api_keys:
        key_index %= len(api_keys)
    else:
        key_index = 0
    if not pid or not name or not base_url or not api_keys or not models:
        return None
    return {
        "id": pid,
        "name": name,
        "base_url": base_url,
        "api_keys": api_keys,
        "models": models,
        "active_model": active_model,
        "extra_headers": headers,
        "current_key_index": key_index,
    }


def _clean_config(data: Any) -> dict[str, Any]:
    clean = _clone_default()
    if not isinstance(data, dict):
        return clean
    providers = []
    seen = set()
    raw_providers = data.get("providers") if isinstance(data.get("providers"), list) else []
    for raw in raw_providers[:_MAX_PROVIDERS]:
        provider = _clean_provider(raw)
        if provider and provider["id"] not in seen:
            seen.add(provider["id"])
            providers.append(provider)
    active = str(data.get("active_provider_id") or "").strip() or None
    if active not in seen:
        active = providers[0]["id"] if providers else None
    clean["providers"] = providers
    clean["active_provider_id"] = active
    clean["system_prompt"] = str(data.get("system_prompt") or "").strip()[:100000]
    return clean


def load_config() -> dict[str, Any]:
    with _LOCK:
        if not _CONFIG_PATH.exists():
            return _clone_default()
        try:
            data = json.loads(_CONFIG_PATH.read_text("utf-8"))
        except Exception:
            return _clone_default()
        return _clean_config(data)


def save_config(data: dict[str, Any]) -> dict[str, Any]:
    clean = _clean_config(data)
    with _LOCK:
        _ensure_parent()
        tmp = _CONFIG_PATH.with_suffix(_CONFIG_PATH.suffix + ".tmp")
        tmp.write_text(json.dumps(clean, ensure_ascii=False, indent=2), "utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        tmp.replace(_CONFIG_PATH)
        try:
            os.chmod(_CONFIG_PATH, 0o600)
        except OSError:
            pass
    return clean


def get_active_provider() -> dict[str, Any] | None:
    cfg = load_config()
    active = cfg.get("active_provider_id")
    for provider in cfg.get("providers", []):
        if str(provider.get("id")) == str(active):
            return provider
    return None


def get_active_api_key(provider: dict[str, Any]) -> str:
    keys = provider.get("api_keys") or []
    if not keys:
        return ""
    idx = int(provider.get("current_key_index", 0)) % len(keys)
    return str(keys[idx])


def rotate_active_api_key() -> None:
    """Advance the active provider to its next API key for the next request."""
    with _LOCK:
        cfg = load_config()
        active = cfg.get("active_provider_id")
        for provider in cfg.get("providers", []):
            if str(provider.get("id")) != str(active):
                continue
            keys = provider.get("api_keys") or []
            if len(keys) <= 1:
                return
            provider["current_key_index"] = (int(provider.get("current_key_index", 0)) + 1) % len(keys)
            save_config(cfg)
            return


def get_system_prompt() -> str:
    return (load_config().get("system_prompt") or "").strip()
