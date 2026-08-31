"""Small Supabase REST helper used by the public build.

The private project contains the same style of persistence, but this module deliberately
contains no personal table contents or IDs. Missing Supabase configuration simply disables
persistence instead of crashing the gateway.
"""
from __future__ import annotations
import logging
import requests
from app_config import SUPABASE_URL, SUPABASE_KEY

log = logging.getLogger(__name__)


def enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def _headers(prefer: str | None = None) -> dict:
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def get(table: str, query: str = "") -> list:
    if not enabled():
        return []
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?{query}", headers=_headers(), timeout=10)
        if not r.ok:
            log.warning("storage.get %s HTTP %s: %s", table, r.status_code, r.text[:200])
            return []
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception as exc:
        log.warning("storage.get %s failed: %s", table, exc)
        return []


def insert(table: str, body: dict) -> list:
    if not enabled():
        return []
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/{table}", headers=_headers("return=representation"),
        json=body, timeout=10,
    )
    if not r.ok:
        raise RuntimeError(f"Supabase insert {table}: HTTP {r.status_code} {r.text[:300]}")
    try:
        data = r.json()
        return data if isinstance(data, list) else [data]
    except Exception:
        return []


def update(table: str, query: str, body: dict) -> None:
    if not enabled():
        return
    r = requests.patch(f"{SUPABASE_URL}/rest/v1/{table}?{query}", headers=_headers(), json=body, timeout=10)
    if not r.ok:
        raise RuntimeError(f"Supabase update {table}: HTTP {r.status_code} {r.text[:300]}")


def delete_ids(table: str, ids: list, batch_size: int = 200) -> None:
    if not enabled() or not ids:
        return
    for i in range(0, len(ids), batch_size):
        batch = ids[i:i+batch_size]
        q = ",".join(str(x) for x in batch)
        r = requests.delete(f"{SUPABASE_URL}/rest/v1/{table}?id=in.({q})", headers=_headers(), timeout=10)
        if not r.ok:
            raise RuntimeError(f"Supabase delete {table}: HTTP {r.status_code} {r.text[:300]}")


def upsert_setting(key: str, value: str) -> None:
    if not enabled():
        return
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/bot_settings",
        headers=_headers("resolution=merge-duplicates"),
        json={"key": key, "value": value}, timeout=10,
    )
    if not r.ok:
        raise RuntimeError(f"Supabase setting {key}: HTTP {r.status_code} {r.text[:300]}")


def get_setting(key: str, default=None):
    rows = get("bot_settings", f"key=eq.{key}&select=value&limit=1")
    return rows[0].get("value") if rows else default
