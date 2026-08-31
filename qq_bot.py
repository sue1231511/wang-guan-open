"""Generic OneBot v11 forward-WebSocket transport for QQ/NapCat-compatible bridges."""
from __future__ import annotations
import os,asyncio,json,uuid,logging
from starlette.websockets import WebSocket,WebSocketDisconnect

log=logging.getLogger(__name__)
WS_TOKEN=os.getenv("QQ_WS_TOKEN",os.getenv("NAPCAT_WS_TOKEN",""))
_conn:WebSocket|None=None
_loop=None
_lock=asyncio.Lock()
_pending={}

async def send_action(action,params):
    if _conn is None:return False
    payload={"action":action,"params":params,"echo":str(uuid.uuid4())}
    async with _lock:
        await _conn.send_text(json.dumps(payload,ensure_ascii=False))
    return True

async def send_action_wait(action,params,timeout=5):
    if _conn is None:return None
    echo=str(uuid.uuid4()); fut=asyncio.get_running_loop().create_future();_pending[echo]=fut
    async with _lock:await _conn.send_text(json.dumps({"action":action,"params":params,"echo":echo},ensure_ascii=False))
    try:return await asyncio.wait_for(asyncio.shield(fut),timeout)
    except asyncio.TimeoutError:_pending.pop(echo,None);return None

async def send_qq_msg(target_type,target_id,message):
    action="send_private_msg" if target_type=="private" else "send_group_msg"
    key="user_id" if target_type=="private" else "group_id"
    return await send_action(action,{key:int(target_id),"message":message})

async def get_msg(message_id):
    r=await send_action_wait("get_msg",{"message_id":int(message_id)});return r.get("data") if r and r.get("status")=="ok" else None

async def websocket_endpoint(ws:WebSocket):
    global _conn,_loop
    auth=(ws.headers.get("authorization") or "").replace("Bearer ","").replace("bearer ","").strip()
    if WS_TOKEN and auth!=WS_TOKEN:
        await ws.close(code=1008);return
    await ws.accept();this=ws;_conn=this;_loop=asyncio.get_running_loop()
    from qq_workers import handle_event
    try:
        while True:
            raw=await ws.receive_text()
            try:data=json.loads(raw)
            except Exception:continue
            echo=data.get("echo")
            if echo and echo in _pending:
                fut=_pending.pop(echo)
                if not fut.done():fut.set_result(data)
                continue
            if data.get("post_type") and data.get("post_type")!="meta_event":asyncio.create_task(handle_event(data))
    except WebSocketDisconnect:pass
    finally:
        if _conn is this:
            _conn=None
            for fut in list(_pending.values()):
                if not fut.done():fut.cancel()
            _pending.clear()
