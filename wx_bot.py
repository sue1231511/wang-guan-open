"""Generic WeChat iLink text adapter.

Keeps long polling, token reload and context-token based sending. Private notification
channels and private login state are not bundled; configure credentials through env/Supabase.
"""
from __future__ import annotations
import os,asyncio,uuid,struct,base64,logging,httpx
from storage import get

log=logging.getLogger(__name__)
TOKEN=os.getenv("WX_ILINK_TOKEN","")
BASE=os.getenv("WX_ILINK_BASEURL","https://ilinkai.weixin.qq.com").rstrip("/")
BOT_ID=os.getenv("WX_ILINK_BOT_ID","")
_current_token=TOKEN;_current_bot_id=BOT_ID

def _uin():return base64.b64encode(str(struct.unpack(">I",os.urandom(4))[0]).encode()).decode()
def _headers():return {"Content-Type":"application/json","AuthorizationType":"ilink_bot_token","Authorization":f"Bearer {_current_token}","X-WECHAT-UIN":_uin(),"iLink-App-Id":"bot","iLink-App-ClientVersion":"65536"}
def _base_info():return {"channel_version":"2.0.0"}

def _load_creds():
    rows=get("bot_settings","key=in.(wx_ilink_token,wx_ilink_bot_id)&select=key,value")
    return {r.get("key"):r.get("value") for r in rows}

async def send_wx_message(to_user_id,context_token,text,retries=1):
    if not _current_token or not _current_bot_id or not context_token:return False
    payload={"msg":{"from_user_id":_current_bot_id,"to_user_id":to_user_id,"client_id":str(uuid.uuid4()),"message_type":2,"message_state":2,"context_token":context_token,"item_list":[{"type":1,"text_item":{"text":text}}]},"base_info":_base_info()}
    delay=5
    for attempt in range(retries+4):
        try:
            async with httpx.AsyncClient(timeout=15) as client:r=await client.post(BASE+"/ilink/bot/sendmessage",headers=_headers(),json=payload)
            d=r.json();ret=d.get("ret",0)
            if ret==0:return True
            if d.get("errcode")==-14:return False
            if ret==-2 and attempt<retries+3:
                await asyncio.sleep(delay);delay=min(delay*2,60);continue
            if attempt<retries:continue
            return False
        except (httpx.TimeoutException,httpx.ConnectError):
            if attempt<retries:continue
            return False
    return False

async def async_wx_bot():
    global _current_token,_current_bot_id
    creds=await asyncio.to_thread(_load_creds)
    _current_token=creds.get("wx_ilink_token") or TOKEN
    _current_bot_id=creds.get("wx_ilink_bot_id") or BOT_ID
    if not _current_token:
        log.info("WX_ILINK_TOKEN not configured; WeChat adapter disabled")
        return
    from wx_workers import handle_message,restore_context_token
    await asyncio.to_thread(restore_context_token)
    buf="";errors=0
    while True:
        try:
            async with httpx.AsyncClient(timeout=28) as client:r=await client.post(BASE+"/ilink/bot/getupdates",headers=_headers(),json={"get_updates_buf":buf,"base_info":_base_info()})
            d=r.json()
            if d.get("errcode")==-14:
                await asyncio.sleep(60);continue
            if d.get("ret",0)!=0:
                errors+=1;await asyncio.sleep(min(5*errors,60));continue
            errors=0;buf=d.get("get_updates_buf") or buf
            for msg in d.get("msgs") or []:asyncio.create_task(handle_message(msg))
        except (httpx.TimeoutException,httpx.ConnectError,httpx.ReadTimeout):await asyncio.sleep(.5)
        except Exception as exc:
            errors+=1;log.warning("WeChat poll failed: %s",exc);await asyncio.sleep(min(5*errors,60))
