"""Public summary, rolling-context, memory-refresh and thread maintenance tasks."""
from __future__ import annotations
import json, re, logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import prompts
from storage import get, insert, update, delete_ids, upsert_setting
from app_config import DEFAULT_TIMEZONE, AI_NAME, USER_NAME

log=logging.getLogger(__name__)
TZ=ZoneInfo(DEFAULT_TIMEZONE)


def _llm(system,user,max_tokens=4000):
    import asyncio
    from llm_runtime import call_llm
    text,_=asyncio.run(call_llm([{"role":"system","content":system},{"role":"user","content":user}],max_tokens=max_tokens,channel="background"))
    return (text or "").strip()


def _day_range(day):
    s=day.replace(hour=0,minute=0,second=0,microsecond=0)
    e=day.replace(hour=23,minute=59,second=59,microsecond=999999)
    return s.astimezone(timezone.utc).isoformat(),e.astimezone(timezone.utc).isoformat(),s,e


def run_chat_day_summary(target_date=None):
    day=target_date or datetime.now(TZ)-timedelta(days=1)
    s,e,ps,pe=_day_range(day)
    rows=get("chat_context",f"type=eq.message&created_at=gte.{s}&created_at=lte.{e}&order=seq.asc")
    if not rows:return
    content="\n".join(f"{USER_NAME if r.get('role')=='user' else AI_NAME}: {r.get('content','')}" for r in rows)
    prompt=prompts.CHAT_DAY_SUMMARY.format(period_start=ps,period_end=pe,content=content)
    summary=_llm("Summarize faithfully.",prompt)
    if not summary:return
    insert("chat_summaries",{"period":"day","content":summary,"period_start":ps.isoformat(),"period_end":pe.isoformat()})
    delete_ids("chat_context",[r["id"] for r in rows if r.get("id") is not None])


def run_current_memory_refresh():
    sums=get("chat_summaries","period=eq.day&order=period_end.desc&limit=3&select=content,period_start")
    if not sums:return
    cur=get("memories","memory_layer=eq.current&order=importance.desc&select=id,content,importance")
    prompt=prompts.CURRENT_MEMORY_REFRESH.format(current_count=len(cur),current_memories="\n".join(f"- {r.get('content','')}" for r in cur) or "(none)",summary_count=len(sums),chat_summaries="\n\n".join(r.get("content","") for r in reversed(sums)))
    raw=_llm("Return valid JSON only.",prompt)
    try:
        m=re.search(r'\{.*\}',raw,re.S); data=json.loads(m.group(0)) if m else {}; items=data.get("memories",[])
    except Exception:return
    if not items:return
    delete_ids("memories",[r["id"] for r in cur if r.get("id") is not None])
    for x in items:
        c=(x.get("content") or "").strip()
        if c: insert("memories",{"content":c,"memory_layer":"current","importance":max(1,min(int(x.get("importance",3)),5))})


def run_thread_scan():
    sums=get("chat_summaries","period=eq.day&order=period_end.desc&limit=1&select=content")
    if not sums:return
    threads=get("threads","status=in.(ACTIVE,DORMANT)&order=created_at.asc&select=id,title,synthetic_guess,status,evidence")
    existing="\n".join(f"[id={t.get('id')} status={t.get('status')}] {t.get('title')} | {t.get('synthetic_guess','')}" for t in threads) or "(none)"
    raw=_llm("Return valid JSON only.",prompts.THREAD_SCAN.format(existing_threads=existing,chat_summary=sums[0].get("content","")),2500)
    try:
        m=re.search(r'\{.*\}',raw,re.S); data=json.loads(m.group(0)) if m else {}
    except Exception:return
    for t in data.get("new_threads",[]):
        if t.get("title") and t.get("synthetic_guess"): insert("threads",{"title":t["title"],"synthetic_guess":t["synthetic_guess"],"evidence":t.get("evidence"),"status":"ACTIVE"})
    for u in data.get("updates",[]):
        if u.get("id") and u.get("status") in ("DORMANT","SILENT"):
            body={"status":u["status"],"last_event_at":datetime.now(timezone.utc).isoformat()}
            if u.get("evidence"):body["evidence"]=u["evidence"]
            update("threads",f"id=eq.{u['id']}",body)


def run_platform_batch_compress(limit=100):
    rows=[]
    for q in ("type=eq.message","type=eq.wx_message","type=like.group_*"):
        rows += get("chat_context",f"{q}&order=seq.asc&limit={limit}&select=id,type,role,content,seq,created_at")
    rows=sorted(rows,key=lambda r:r.get("seq",0))[:limit]
    if not rows:return
    lines=[]
    for r in rows:
        scene="private" if r.get("type")=="message" else ("wechat" if r.get("type")=="wx_message" else "group")
        lines.append(f"[{scene}] {r.get('role')}: {r.get('content','')}")
    now=datetime.now(TZ)
    summary=_llm("Summarize cross-platform context faithfully.",prompts.PLATFORM_BATCH_SUMMARY.format(content="\n".join(lines),taboo_instruction="",period_start="",period_end=now.isoformat()),8000)
    if not summary:return
    insert("platform_rolling_summary",{"content":summary,"source_platforms":"public-adapters","period_start":(rows[0].get("created_at") or now.isoformat()),"period_end":now.isoformat()})
    delete_ids("chat_context",[r["id"] for r in rows if r.get("id") is not None])


def run_nightly_summary(target_date=None):
    run_chat_day_summary(target_date)
    run_current_memory_refresh()
    run_thread_scan()
    upsert_setting("last_summary_run",datetime.now(TZ).isoformat())
