"""Generic Telegram adapter: webhook, private/group replies, aggregation and tools."""
from __future__ import annotations
import os,asyncio,json,random,re,requests
from context import build_context
from conversation_store import save_message,recent
from llm_runtime import call_llm
from free_tools import TOOL_SCHEMAS,TOOL_DISPATCH
from prompts import GROUP_CHAT_EXAMPLE

TOKEN=os.getenv("TG_BOT_TOKEN","")
OWNER_ID=os.getenv("TG_OWNER_ID",os.getenv("TG_CHAT_ID",""))
GROUP_IDS={x.strip() for x in os.getenv("TG_GROUP_IDS","").split(",") if x.strip()}
_private_pending=None
_group_pending={}

def send_message(text,chat_id=None):
    chat_id=str(chat_id or OWNER_ID)
    if not TOKEN or not chat_id:return False
    for part in [text[i:i+4000] for i in range(0,len(text),4000)] or [""]:
        try:
            r=requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",json={"chat_id":chat_id,"text":part},timeout=20)
            if not r.json().get("ok"):return False
        except Exception:return False
    return True

async def _tool_chat(messages,tools,max_rounds=6,channel="chat"):
    for _ in range(max_rounds):
        text,calls=await call_llm(messages,tools=tools,channel=channel)
        if not calls:return text
        assistant={"role":"assistant","tool_calls":calls}
        if text:assistant["content"]=text
        messages.append(assistant)
        for tc in calls:
            fn=tc.get("function") or {}; name=fn.get("name","")
            try:args=json.loads(fn.get("arguments") or "{}")
            except Exception:args={}
            handler=TOOL_DISPATCH.get(name)
            try:result=await asyncio.to_thread(handler,args) if handler else f"Unknown tool: {name}"
            except Exception as exc:result=f"Tool failed: {type(exc).__name__}"
            messages.append({"role":"tool","tool_call_id":tc.get("id",""),"content":str(result)})
    text,_=await call_llm(messages,tools=None,channel=channel);return text

async def _private_reply():
    global _private_pending
    try:
        await asyncio.sleep(random.randint(3,10))
        history=recent("message",30)
        messages=[{"role":"system","content":build_context()}]+history
        reply=(await _tool_chat(messages,TOOL_SCHEMAS)).strip()
        if reply:
            save_message("assistant",reply,scene="message",source="telegram")
            await asyncio.to_thread(send_message,reply,OWNER_ID)
    except asyncio.CancelledError:pass
    finally:
        if _private_pending is asyncio.current_task():_private_pending=None

async def _group_reply(chat_id):
    task=asyncio.current_task()
    try:
        await asyncio.sleep(random.randint(5,12))
        scene=f"group_tg_{chat_id}"
        history=recent(scene,40)
        messages=[{"role":"system","content":GROUP_CHAT_EXAMPLE+"\n\n"+build_context()}]+history
        reply=(await _tool_chat(messages,TOOL_SCHEMAS,max_rounds=3)).strip()
        if not reply or re.search(r'\bPASS\b',reply,re.I):return
        save_message("assistant",reply,scene=scene,source="telegram-group")
        await asyncio.to_thread(send_message,reply,chat_id)
    except asyncio.CancelledError:pass
    finally:
        if _group_pending.get(chat_id) is task:_group_pending.pop(chat_id,None)

async def handle_update(update:dict):
    global _private_pending
    msg=update.get("message") or {}; chat=msg.get("chat") or {}; sender=msg.get("from") or {}
    if not msg:return
    chat_id=str(chat.get("id","")); is_group=chat.get("type") in ("group","supergroup")
    text=(msg.get("text") or msg.get("caption") or "").strip()
    if not text:return
    if is_group:
        if GROUP_IDS and chat_id not in GROUP_IDS:return
        name=(sender.get("first_name") or "member")+(" "+sender.get("last_name","") if sender.get("last_name") else "")
        scene=f"group_tg_{chat_id}"; save_message("user",f"{name}: {text}",scene=scene,source="telegram-group",message_id=msg.get("message_id"))
        if not _group_pending.get(chat_id) or _group_pending[chat_id].done():_group_pending[chat_id]=asyncio.create_task(_group_reply(chat_id))
        return
    if OWNER_ID and chat_id!=str(OWNER_ID):return
    save_message("user",text,scene="message",source="telegram",message_id=msg.get("message_id"))
    if _private_pending and not _private_pending.done():_private_pending.cancel()
    _private_pending=asyncio.create_task(_private_reply())
