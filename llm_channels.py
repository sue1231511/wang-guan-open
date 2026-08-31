"""Multi-channel LLM configuration and key rotation.

Channels mirror the private deployment's useful separation without carrying private names:
chat / background / vision / proactive / qq / wx.
"""
from __future__ import annotations
import os, threading, time, logging, requests
from app_config import SUPABASE_URL, SUPABASE_KEY

log = logging.getLogger(__name__)
_CACHE: dict[str, tuple[float, dict]] = {}
_LOCK = threading.Lock()
TTL = 30

CHANNEL_COLUMNS = {
    "chat": "active",
    "background": "bg_active",
    "vision": "vision_active",
    "proactive": "free_activity_active",
    "qq": "qq_active",
    "wx": "wx_active",
}

ENV_PREFIX = {
    "chat": "CHAT", "background": "BG_CHAT", "vision": "VISION",
    "proactive": "PROACTIVE", "qq": "QQ_LLM", "wx": "WX_LLM",
}


def _pick_key(row: dict) -> str:
    keys = row.get("api_keys") or []
    if keys:
        idx = row.get("current_key_index", 0) or 0
        if not isinstance(idx, int) or idx < 0 or idx >= len(keys): idx = 0
        return keys[idx]
    return row.get("api_key", "")


def _env_config(channel: str) -> dict:
    p = ENV_PREFIX[channel]
    base = os.getenv(f"{p}_BASE_URL", os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
    key = os.getenv(f"{p}_API_KEY", os.getenv("LLM_API_KEY", ""))
    model = os.getenv(f"{p}_MODEL", os.getenv("LLM_MODEL", ""))
    return {"base_url": base, "api_key": key, "model": model, "extra_headers": {}, "channel": channel}


def get_config(channel: str = "chat") -> dict:
    if channel not in CHANNEL_COLUMNS:
        raise ValueError(f"Unknown LLM channel: {channel}")
    now = time.time()
    cached = _CACHE.get(channel)
    if cached and now - cached[0] < TTL:
        return cached[1]
    with _LOCK:
        cached = _CACHE.get(channel)
        if cached and time.time() - cached[0] < TTL:
            return cached[1]
        cfg = None
        if SUPABASE_URL and SUPABASE_KEY:
            col = CHANNEL_COLUMNS[channel]
            try:
                r = requests.get(
                    f"{SUPABASE_URL}/rest/v1/llm_config?{col}=eq.true&limit=1",
                    headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}, timeout=5,
                )
                rows = r.json() if r.ok else []
                if rows:
                    row = rows[0]
                    cfg = {
                        "base_url": row["base_url"].rstrip("/"), "api_key": _pick_key(row),
                        "model": row["model"], "extra_headers": row.get("extra_headers") or {},
                        "config_id": row.get("id"), "channel": channel,
                    }
            except Exception as exc:
                log.warning("LLM config %s fallback to env: %s", channel, exc)
        cfg = cfg or _env_config(channel)
        if channel != "chat" and (not cfg.get("api_key") or not cfg.get("model")):
            cfg = get_config("chat")
        _CACHE[channel] = (time.time(), cfg)
        return cfg


def clear_cache(channel: str | None = None):
    if channel: _CACHE.pop(channel, None)
    else: _CACHE.clear()


def record_result(config_id, success: bool, channel: str = "chat", fail_threshold: int = 3):
    """Report key health. If matching RPCs exist, Supabase can atomically rotate keys/providers.
    Public deployments that do not install these optional RPCs simply keep working without rotation.
    """
    if not config_id or not SUPABASE_URL or not SUPABASE_KEY:
        return
    rpc = "llm_config_record_success" if success else "llm_config_record_failure"
    payload = {"p_config_id": config_id}
    if not success: payload["p_fail_threshold"] = fail_threshold
    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/{rpc}",
            headers={"apikey": SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}","Content-Type":"application/json"},
            json=payload, timeout=5,
        )
    except Exception as exc:
        log.debug("record_result ignored: %s", exc)
    clear_cache(channel)
