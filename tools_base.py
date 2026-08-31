"""Shared tool utilities: Supabase access, MCP session reuse and target context."""
from __future__ import annotations
import os,json,threading,logging,requests
from contextvars import ContextVar
from app_config import SUPABASE_URL,SUPABASE_KEY

log=logging.getLogger(__name__)
_SB_HEADERS={"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}","Content-Type":"application/json"}

_send_ctx:ContextVar[dict|None]=ContextVar("send_ctx",default=None)
def set_send_context(platform:str,target_type:str,target_id:str):_send_ctx.set({"platform":platform,"target_type":target_type,"target_id":target_id})
def get_send_context():return _send_ctx.get()

_sessions={};_lock=threading.Lock()
def _headers(sid=""):
    h={"Content-Type":"application/json","Accept":"application/json, text/event-stream"}
    if sid:h["Mcp-Session-Id"]=sid
    return h

def _parse(resp):
    if "text/event-stream" in resp.headers.get("Content-Type",""):
        last=None
        for line in resp.text.splitlines():
            if line.startswith("data:"):
                try:
                    obj=json.loads(line[5:].strip())
                    if "id" in obj:last=obj
                except Exception:pass
        return last
    try:return resp.json()
    except Exception:return None

def _init(url,timeout=15):
    r=requests.post(url,json={"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"wang-guan-open","version":"1.0"}}},headers=_headers(),timeout=timeout);r.raise_for_status()
    sid=r.headers.get("Mcp-Session-Id","") or ""
    requests.post(url,json={"jsonrpc":"2.0","method":"notifications/initialized"},headers=_headers(sid),timeout=10)
    with _lock:_sessions[url]=sid
    return sid

def mcp_call(url,label,tool_name,args,timeout=30):
    if not url:return f"{label} unavailable: MCP URL is not configured"
    def attempt(sid):
        r=requests.post(url,json={"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":tool_name,"arguments":args}},headers=_headers(sid),timeout=timeout);r.raise_for_status();d=_parse(r)
        if not d:raise RuntimeError("invalid MCP response")
        if "error" in d:raise RuntimeError(str(d["error"]))
        result=d.get("result",{}); content=result.get("content",[])
        return content[0].get("text","") if content else ""
    with _lock:sid=_sessions.get(url)
    try:
        if sid is None:sid=_init(url)
        return attempt(sid)
    except Exception:
        try:return attempt(_init(url))
        except Exception as exc:return f"{label} failed: {exc}"
