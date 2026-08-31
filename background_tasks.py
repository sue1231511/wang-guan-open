"""Background jobs for reminders, summaries, proactive messaging and rolling compression.

Private deployments can override prompts and delivery adapters without changing scheduling code.
Secret diary parsing is intentionally not part of the public build.
"""
from __future__ import annotations
import asyncio, random, logging
from datetime import datetime, timezone
from storage import get, update
from conversation_store import recent
from llm_runtime import call_llm
from prompts import PROACTIVE_EXAMPLE
from scheduled import run_nightly_summary, run_platform_batch_compress

log=logging.getLogger(__name__)

async def reminder_checker(send_callback=None):
    while True:
        await asyncio.sleep(60)
        rows=get("reminders",f"is_done=eq.false&trigger_at=lte.{datetime.now(timezone.utc).isoformat()}&order=trigger_at.asc")
        for row in rows:
            msg=(row.get("message") or "").strip()
            if not msg:
                update("reminders",f"id=eq.{row['id']}",{"is_done":True});continue
            ok=True
            if send_callback:
                try: ok=bool(await send_callback(msg))
                except Exception: ok=False
            if ok:update("reminders",f"id=eq.{row['id']}",{"is_done":True})

async def proactive_loop(send_callback=None):
    while True:
        await asyncio.sleep(random.randint(900,3600))
        if not send_callback:continue
        history=recent("message",30)
        messages=[{"role":"system","content":PROACTIVE_EXAMPLE}]+history
        if not history or history[-1].get("role")!="user":messages.append({"role":"user","content":"(background trigger)"})
        try:
            text,_=await call_llm(messages,max_tokens=1200,channel="chat")
        except Exception as exc:
            log.warning("proactive loop failed: %s",exc);continue
        s=(text or "").strip()
        if s.startswith("SEND\n"):
            await send_callback(s[5:].strip())

async def summary_loop():
    while True:
        await asyncio.sleep(1800)
        try: await asyncio.to_thread(run_nightly_summary)
        except Exception as exc: log.warning("summary loop failed: %s",exc)

async def platform_compress_loop():
    while True:
        await asyncio.sleep(90)
        try:
            rows=get("chat_context","select=id&limit=101")
            if len(rows)>=100: await asyncio.to_thread(run_platform_batch_compress)
        except Exception as exc:log.warning("platform compress failed: %s",exc)

REGISTERED_TASKS=[summary_loop,platform_compress_loop]
