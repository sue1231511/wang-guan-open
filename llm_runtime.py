"""Unified streaming OpenAI-compatible LLM caller used by bots and background tasks."""
from __future__ import annotations
import json, logging, httpx
from llm_channels import get_config, record_result

log=logging.getLogger(__name__)


def _safe_headers(api_key:str, extra_headers:dict|None=None) -> dict:
    custom={str(k):str(v) for k,v in (extra_headers or {}).items()}
    for key in list(custom):
        if key.lower() in {"authorization","content-type"}:
            custom.pop(key,None)
    return {**custom,"Authorization":f"Bearer {api_key}","Content-Type":"application/json"}


async def call_llm(messages:list,max_tokens:int=4096,tools:list|None=None,extra_body:dict|None=None,channel:str="chat") -> tuple[str,list]:
    cfg=get_config(channel)
    if not cfg.get("api_key") or not cfg.get("model"):
        raise RuntimeError(f"LLM channel '{channel}' is not configured")
    payload={"model":cfg["model"],"messages":messages,"max_tokens":max_tokens,"stream":True}
    if tools:payload["tools"]=tools
    if extra_body:payload.update(extra_body)
    headers=_safe_headers(cfg["api_key"],cfg.get("extra_headers"))
    content=[]; tc_map={}; got_done=False
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=30,read=180,write=30,pool=30),http2=False) as client:
            async with client.stream("POST",cfg["base_url"]+"/chat/completions",headers=headers,json=payload) as resp:
                if resp.status_code>=400:
                    body=(await resp.aread()).decode(errors="ignore")[:500]
                    raise RuntimeError(f"Upstream HTTP {resp.status_code}: {body}")
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):continue
                    s=line[5:].strip()
                    if s=="[DONE]":got_done=True;break
                    try:d=json.loads(s)
                    except Exception:continue
                    choices=d.get("choices") or []
                    if not choices:continue
                    delta=choices[0].get("delta") or {}
                    if delta.get("content"):content.append(delta["content"])
                    for td in delta.get("tool_calls") or []:
                        i=td.get("index",0); e=tc_map.setdefault(i,{"id":"","type":"function","function":{"name":"","arguments":""}})
                        if td.get("id"):e["id"]=td["id"]
                        fn=td.get("function") or {}
                        if fn.get("name"):e["function"]["name"]=fn["name"]
                        if fn.get("arguments"):e["function"]["arguments"]+=fn["arguments"]
        record_result(cfg.get("config_id"),True,channel)
    except Exception:
        record_result(cfg.get("config_id"),False,channel); raise
    if not got_done:log.warning("LLM stream ended without [DONE] channel=%s",channel)
    return "".join(content).strip(),[tc_map[i] for i in sorted(tc_map)]
