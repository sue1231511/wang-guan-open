"""Background jobs for reminders, summaries, proactive messaging and rolling compression.

Private deployments can override prompts and delivery adapters without changing scheduling code.
Secret diary parsing is intentionally not part of the public build.
"""
from __future__ import annotations
import asyncio, random, logging, os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from storage import get, update, get_setting, upsert_setting
from conversation_store import recent
from llm_runtime import call_llm
from prompts import PROACTIVE_EXAMPLE
from scheduled import run_nightly_summary, run_platform_batch_compress
from app_config import DEFAULT_TIMEZONE

log=logging.getLogger(__name__)


def _default_reminder_sender():
    """Build a delivery callback from configured public transports.

    Telegram is supported out of the box. Other platforms can pass their own callback
    when registering reminder_checker. Missing delivery configuration returns None;
    due reminders must stay pending rather than being silently consumed.
    """
    token=os.getenv("TG_BOT_TOKEN","").strip()
    owner=os.getenv("TG_OWNER_ID",os.getenv("TG_CHAT_ID","")).strip()
    if token and owner:
        async def _send(message:str) -> bool:
            from telegram_bot import send_message
            return bool(await asyncio.to_thread(send_message,message,owner))
        return _send
    return None


async def reminder_checker(send_callback=None):
    sender=send_callback or _default_reminder_sender()
    if sender is None:
        log.info("Reminder checker has no delivery transport; due reminders will remain pending")
    while True:
        await asyncio.sleep(60)
        rows=get("reminders",f"is_done=eq.false&trigger_at=lte.{datetime.now(timezone.utc).isoformat()}&order=trigger_at.asc")
        for row in rows:
            msg=(row.get("message") or "").strip()
            if not msg:
                update("reminders",f"id=eq.{row['id']}",{"is_done":True})
                continue
            if sender is None:
                continue
            try:
                ok=bool(await sender(msg))
            except Exception as exc:
                log.warning("reminder delivery failed id=%s: %s",row.get("id"),exc)
                ok=False
            if ok:
                update("reminders",f"id=eq.{row['id']}",{"is_done":True})

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
    tz=ZoneInfo(DEFAULT_TIMEZONE)
    hour=max(0,min(int(os.getenv("NIGHTLY_SUMMARY_HOUR","4")),23))
    while True:
        await asyncio.sleep(60)
        now=datetime.now(tz)
        day_key=now.strftime("%Y-%m-%d")
        if now.hour!=hour:
            continue
        if get_setting("last_nightly_summary_day","")==day_key:
            continue
        try:
            await asyncio.to_thread(run_nightly_summary)
            upsert_setting("last_nightly_summary_day",day_key)
        except Exception as exc:
            log.warning("summary loop failed: %s",exc)

async def platform_compress_loop():
    while True:
        await asyncio.sleep(90)
        try:
            rows=get("chat_context","select=id&limit=101")
            if len(rows)>=100: await asyncio.to_thread(run_platform_batch_compress)
        except Exception as exc:log.warning("platform compress failed: %s",exc)

REGISTERED_TASKS=[reminder_checker,summary_loop,platform_compress_loop]
