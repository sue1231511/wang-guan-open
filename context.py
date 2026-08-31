"""Public context engine.

The private deployment injects many personal providers. The public build keeps the same
composition pattern but uses generic data sources: configurable persona, layered memories,
rolling cross-platform summary, unresolved threads and time. Optional providers can be
registered by extensions without editing this file.
"""
from __future__ import annotations
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Callable
from app_config import DEFAULT_TIMEZONE, AI_NAME, USER_NAME
from storage import get

ContextProvider=Callable[[],str]
_PROVIDERS:list[ContextProvider]=[]


def register_context_provider(provider:ContextProvider):
    if provider not in _PROVIDERS:_PROVIDERS.append(provider)

def unregister_context_provider(provider:ContextProvider):
    if provider in _PROVIDERS:_PROVIDERS.remove(provider)


def _base_prompt():
    try:
        from runtime_config import get_system_prompt
        p=get_system_prompt()
    except Exception:p=""
    return (p or os.getenv("SYSTEM_PROMPT",f"You are {AI_NAME}, an assistant for {USER_NAME}.")).strip()


def _persona():
    rows=get("persona_profile","select=category,key,content&order=category.asc")
    if not rows:return ""
    groups={}
    for r in rows:groups.setdefault(r.get("category","persona"),[]).append(f"[{r.get('key','item')}] {r.get('content','')}")
    return "【Persona / configurable profile】\n"+"\n".join(f"[{k}]\n"+"\n".join(v) for k,v in groups.items())


def _memories():
    rows=get("memories","memory_layer=in.(core,current,long_term)&order=importance.desc&limit=20&select=content,memory_layer,importance,tags")
    if not rows:return ""
    return "【Layered memory】\n"+"\n".join(f"- [{r.get('memory_layer')}|{r.get('importance',3)}] {r.get('content','')}" for r in rows)


def _threads():
    rows=get("threads","status=in.(ACTIVE,DORMANT)&order=created_at.asc&limit=6&select=title,synthetic_guess,status,evidence")
    if not rows:return ""
    return "【Open threads】\n"+"\n".join(f"- [{r.get('status')}] {r.get('title','')}: {r.get('synthetic_guess','')}" for r in rows)


def _rolling():
    rows=get("platform_rolling_summary","order=id.desc&limit=1&select=content,period_start,period_end")
    if not rows:return ""
    return "【Recent cross-platform context】\n"+(rows[0].get("content") or "")


def _time():
    now=datetime.now(ZoneInfo(DEFAULT_TIMEZONE))
    return f"【Current time】{now.strftime('%Y-%m-%d %H:%M %Z')}"


def build_context():
    parts=[_base_prompt()]
    for fn in (_persona,_memories,_threads,_rolling):
        try:v=(fn() or "").strip()
        except Exception:v=""
        if v:parts.append(v)
    for fn in list(_PROVIDERS):
        try:v=(fn() or "").strip()
        except Exception as exc:v=f"[context provider failed: {type(exc).__name__}]"
        if v:parts.append(v)
    if os.getenv("INCLUDE_TIME_CONTEXT","1")!="0":parts.append(_time())
    return "\n\n".join(parts)
