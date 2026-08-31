"""Generic WeChat private-chat worker with context-token persistence and aggregation."""
from __future__ import annotations
import os,asyncio,random,time
from datetime import datetime,timezone
from storage import get,upsert_setting
from context import build_context
from conversation_store import save_message,recent
from llm_runtime import call_llm
from free_tools import TOOL_SCHEMAS,TOOL_DISPATCH

OWNER_ID=os.getenv("WX_OWNER_ID","")
_token_cache={};_pending=None
WINDOW=23.5*3600

def persist_context_token(token):
    upsert_setting("wx_context_token",token);upsert_setting("wx_context_token_at",datetime.now(timezone.utc).isoformat())
def restore_context_token():
    if not OWNER_ID:return
    rows=get("bot_settings","key=in.(wx_context_token,wx_context_token_at)&select=key,value")
    d={r.get('key'):r.get('value') for r in rows};t=d.get("wx_context_token");at=d.get("wx_context_token_at")
    if not t or not at:return
    try:ts=datetime.fromisoformat(at).timestamp()
    except Exception:return
    if time.time()-ts<WINDOW:_token_cache[OWNER_ID]=(t,ts)
def _token(uid):
    x=_token_cache.get(uid)
    return x[0] if x and time.time()-x[1]<WINDOW else ""
def _text(msg):
    for item in msg.get("item_list") or []:
        if item.get("type")==1:
            t=((item.get("text_item") or {}).get("text") or "").strip()
            if t:return t
    return ""
async def _tool_chat(messages):
    for _ in range(6):
        text,calls=await call_llm(messages,tools=TOOL_SCHEMAS,channel="wx")
        if not calls:return text
        a={"role":"assistant","tool_calls":calls};
        if text:a["content"]=text
        messages.append(a)
        for tc in calls:
            import json
            fn=tc.get("function") or {};name=fn.get("name","")
            try:args=json.loads(fn.get("arguments") or "{}")
            except Exception:args={}
            h=TOOL_DISPATCH.get(name)
            try:r=await asyncio.to_thread(h,args) if h else f"Unknown tool: {name}"
            except Exception as exc:r=f"Tool failed: {type(exc).__name__}"
            messages.append({"role":"tool","tool_call_id":tc.get("id",""),"content":str(r)})
    t,_=await call_llm(messages,channel="wx");return t
async def _reply(uid):
    global _pending
    try:
        await asyncio.sleep(random.randint(4,12));tok=_token(uid)
        if not tok:return
        reply=(await _tool_chat([{"role":"system","content":build_context()+"\n\nCurrent scene: WeChat private chat."}]+recent("wx_message",50))).strip()
        if not reply:return
        from wx_bot import send_wx_message
        if await send_wx_message(uid,tok,reply):save_message("assistant",reply,scene="wx_message",source="wechat")
    except asyncio.CancelledError:pass
    finally:
        if _pending is asyncio.current_task():_pending=None
async def handle_message(msg):
    global _pending
    if msg.get("message_type")==2 or msg.get("group_id"):return
    uid=msg.get("from_user_id","");tok=msg.get("context_token","")
    if not uid:return
    if OWNER_ID and uid!=OWNER_ID:return
    if tok:
        _token_cache[uid]=(tok,time.time());await asyncio.to_thread(persist_context_token,tok)
    text=_text(msg)
    if not text:return
    save_message("user",f"[WeChat] {text}",scene="wx_message",source="wechat")
    if _pending and not _pending.done():_pending.cancel()
    _pending=asyncio.create_task(_reply(uid))
