"""Generic media helpers for vision, STT and TTS.

No private voice id, personal caption rule or private service endpoint is embedded. All
provider-specific values are environment variables.
"""
from __future__ import annotations
import os,base64,tempfile,requests,asyncio,re
from llm_channels import get_config,record_result

async def _vision(payload,label="vision"):
    import httpx
    cfg=await asyncio.to_thread(get_config,"vision")
    extra={str(k):str(v) for k,v in (cfg.get("extra_headers") or {}).items() if str(k).lower() not in {"authorization","content-type"}}
    headers={**extra,"Authorization":f"Bearer {cfg['api_key']}","Content-Type":"application/json"}
    payload={**payload,"model":cfg["model"]}
    async with httpx.AsyncClient(timeout=90,http2=False) as c:
        r=await c.post(cfg["base_url"]+"/chat/completions",headers=headers,json=payload)
    if r.status_code>=400:
        record_result(cfg.get("config_id"),False,"vision");raise RuntimeError(f"vision HTTP {r.status_code}: {r.text[:300]}")
    record_result(cfg.get("config_id"),True,"vision")
    return r.json()["choices"][0]["message"]["content"].strip()

def _download(url,headers=None):
    r=requests.get(url,headers=headers or {},timeout=40);r.raise_for_status();return r.content

async def recognize_image_url(url,caption=""):
    data=await asyncio.to_thread(_download,url,{"User-Agent":"wang-guan-open/1.0"})
    b64="data:image/jpeg;base64,"+base64.b64encode(data).decode()
    prompt="Describe the image directly. If it is a meme/sticker, explain its meaning."
    if caption:prompt+=f" The sender also wrote: {caption!r}; use it only as context."
    return await _vision({"max_tokens":4000,"messages":[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":b64}}]}]})

async def recognize_telegram_image(file_id,caption=""):
    token=os.getenv("TG_BOT_TOKEN","")
    if not token:return ""
    info=await asyncio.to_thread(lambda:requests.get(f"https://api.telegram.org/bot{token}/getFile",params={"file_id":file_id},timeout=10).json())
    path=(info.get("result") or {}).get("file_path","")
    if not path:return ""
    return await recognize_image_url(f"https://api.telegram.org/file/bot{token}/{path}",caption)

async def transcribe_url(url,filename="audio.ogg"):
    key=os.getenv("STT_API_KEY",os.getenv("OPENAI_API_KEY","")).strip()
    base=os.getenv("STT_BASE_URL","https://api.openai.com/v1").rstrip("/")
    model=os.getenv("STT_MODEL","whisper-1")
    if not key:return ""
    data=await asyncio.to_thread(_download,url)
    def run():
        from openai import OpenAI
        suffix=os.path.splitext(filename)[1] or ".ogg"
        fd,path=tempfile.mkstemp(suffix=suffix);os.close(fd)
        try:
            with open(path,"wb") as f:f.write(data)
            client=OpenAI(api_key=key,base_url=base)
            with open(path,"rb") as f:r=client.audio.transcriptions.create(model=model,file=f)
            return re.sub(r'[\U00010000-\U0010ffff]','',r.text).strip()
        finally:
            try:os.remove(path)
            except OSError:pass
    return await asyncio.to_thread(run)

async def synthesize_mp3(text):
    key=os.getenv("TTS_API_KEY",os.getenv("OPENAI_API_KEY","")).strip()
    base=os.getenv("TTS_BASE_URL","https://api.openai.com/v1").rstrip("/")
    model=os.getenv("TTS_MODEL","tts-1");voice=os.getenv("TTS_VOICE","alloy")
    if not key:return b""
    def run():
        from openai import OpenAI
        r=OpenAI(api_key=key,base_url=base).audio.speech.create(model=model,voice=voice,input=text[:1200])
        return r.content
    return await asyncio.to_thread(run)
