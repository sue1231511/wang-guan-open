"""Generic QQ message worker. Keeps owner restrictions, group PASS and real reply/@ tags."""
from __future__ import annotations
import os,asyncio,json,random,re
from context import build_context
from conversation_store import save_message,recent
from llm_runtime import call_llm
from free_tools import TOOL_SCHEMAS,TOOL_DISPATCH
from prompts import GROUP_CHAT_EXAMPLE

BOT_ID=os.getenv("QQ_BOT_ID","");BOT_NAME=os.getenv("QQ_BOT_NAME","Assistant");OWNER_ID=os.getenv("QQ_OWNER_ID","");OWNER_ALIAS=os.getenv("OWNER_ALIAS","Owner")
GROUP_IDS={x.strip() for x in os.getenv("QQ_GROUP_IDS","").split(",") if x.strip()}
_private_pending=None;_group_pending={}
_REPLY_RE=re.compile(r'\[REPLY[:：]\s*(-?\d+)\]',re.I);_AT_RE=re.compile(r'\[AT[:：]\s*(\d+)\]',re.I);_CQ_RE=re.compile(r'\[CQ:[^\]]+\]')

def _clean_cq(s):return _CQ_RE.sub('',s or '').strip()
def _segments(text):
    reply=None;m=_REPLY_RE.search(text)
    if m:reply=m.group(1);text=_REPLY_RE.sub('',text)
    seg=[]
    if reply:seg.append({"type":"reply","data":{"id":reply}})
    pos=0
    for m in _AT_RE.finditer(text):
        if text[pos:m.start()]:seg.append({"type":"text","data":{"text":text[pos:m.start()]}})
        seg.append({"type":"at","data":{"qq":m.group(1)}});pos=m.end()
    if text[pos:]:seg.append({"type":"text","data":{"text":text[pos:]}})
    return seg if (reply or _AT_RE.search(text)) else text.strip()

async def _tool_chat(messages,max_rounds=3):
    for _ in range(max_rounds):
        text,calls=await call_llm(messages,tools=TOOL_SCHEMAS,channel="qq")
        if not calls:return text
        a={"role":"assistant","tool_calls":calls};
        if text:a["content"]=text
        messages.append(a)
        for tc in calls:
            fn=tc.get("function") or {};name=fn.get("name","")
            try:args=json.loads(fn.get("arguments") or "{}")
            except Exception:args={}
            h=TOOL_DISPATCH.get(name)
            try:r=await asyncio.to_thread(h,args) if h else f"Unknown tool: {name}"
            except Exception as exc:r=f"Tool failed: {type(exc).__name__}"
            messages.append({"role":"tool","tool_call_id":tc.get("id",""),"content":str(r)})
    text,_=await call_llm(messages,channel="qq");return text

async def _private_reply():
    global _private_pending
    try:
        await asyncio.sleep(random.randint(3,10));from qq_bot import send_qq_msg
        hist=recent("message",30,with_ids=True);reply=(await _tool_chat([{"role":"system","content":build_context()}]+hist)).strip()
        if not reply:return
        clean=_REPLY_RE.sub('',_AT_RE.sub('',reply)).strip();save_message("assistant",clean,scene="message",source="qq")
        await send_qq_msg("private",int(OWNER_ID),_segments(reply))
    except asyncio.CancelledError:pass
    finally:
        if _private_pending is asyncio.current_task():_private_pending=None

async def _group_reply(gid,force=False):
    task=asyncio.current_task()
    try:
        await asyncio.sleep(random.randint(4,10));from qq_bot import send_qq_msg
        scene=f"group_qq_{gid}";hist=recent(scene,50,with_ids=True)
        instruction=GROUP_CHAT_EXAMPLE+("\nYou were directly mentioned and must reply; do not output PASS." if force else "")
        reply=(await _tool_chat([{"role":"system","content":instruction+"\n\n"+build_context()}]+hist)).strip()
        if not reply or (not force and re.search(r'\bPASS\b',reply,re.I)):return
        clean=_REPLY_RE.sub('',_AT_RE.sub('',reply)).strip();save_message("assistant",f"{BOT_NAME}: {clean}",scene=scene,source="qq-group")
        await send_qq_msg("group",int(gid),_segments(reply))
    except asyncio.CancelledError:pass
    finally:
        if _group_pending.get(gid) is task:_group_pending.pop(gid,None)

async def handle_event(data):
    global _private_pending
    if data.get("post_type")!="message":return
    typ=data.get("message_type","");uid=str(data.get("user_id",""));raw=data.get("raw_message","") or "";mid=data.get("message_id")
    if typ=="private":
        if not OWNER_ID or uid!=OWNER_ID:return
        text=_clean_cq(raw)
        if not text:return
        save_message("user",f"[QQ] {text}",scene="message",source="qq",message_id=mid)
        if _private_pending and not _private_pending.done():_private_pending.cancel()
        _private_pending=asyncio.create_task(_private_reply());return
    if typ!="group":return
    gid=str(data.get("group_id",""));
    if GROUP_IDS and gid not in GROUP_IDS:return
    sender=data.get("sender") or {};name=sender.get("card") or sender.get("nickname") or uid
    llm_name=OWNER_ALIAS if OWNER_ID and uid==OWNER_ID else name
    is_at=bool(BOT_ID and f"[CQ:at,qq={BOT_ID}" in raw)
    text=_clean_cq(raw) or "(sent a non-text message)"
    save_message("user",f"{llm_name}: {text}",scene=f"group_qq_{gid}",source="qq-group",message_id=mid)
    old=_group_pending.get(gid)
    if is_at and old and not old.done():old.cancel()
    if is_at or not old or old.done():_group_pending[gid]=asyncio.create_task(_group_reply(gid,force=is_at))
