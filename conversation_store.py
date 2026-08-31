"""Conversation persistence shared by API, Telegram, QQ and WeChat adapters."""
from __future__ import annotations
from storage import get, insert


def save_message(role: str, content: str, *, scene: str = "message", source: str = "", message_id=None):
    if not content: return
    body = {"type": scene, "role": role, "content": content}
    if source: body["source"] = source
    if message_id is not None: body["message_id"] = str(message_id)
    try: insert("chat_context", body)
    except Exception: pass


def recent(scene: str = "message", limit: int = 30, with_ids: bool = False) -> list:
    rows = get("chat_context", f"type=eq.{scene}&order=seq.desc&limit={max(1,min(limit,100))}")
    rows.reverse()
    out=[]
    for r in rows:
        content=r.get("content","")
        if with_ids and r.get("message_id") is not None:
            content=f"[id:{r['message_id']}] {content}"
        out.append({"role":r.get("role","user"),"content":content})
    return out


def recent_groups(limit: int = 50) -> list:
    rows = get("chat_context", f"type=like.group_*&order=seq.desc&limit={max(1,min(limit,200))}")
    rows.reverse(); return rows
