"""Administrative endpoints for public MiniApp and diagnostics."""
import os, hmac, json, asyncio
from starlette.responses import JSONResponse
from memory_store import list_memories
from storage import get, delete_ids
from scheduled import run_nightly_summary, run_platform_batch_compress
from context import build_context

API_SECRET=os.getenv("API_SECRET","")

def auth_ok(request):
    if not API_SECRET:return False
    raw=request.headers.get("authorization",""); token=raw.split(" ",1)[-1].strip() if " " in raw else raw.strip()
    return hmac.compare_digest(token,API_SECRET)

async def context_preview(request):
    if not auth_ok(request):return JSONResponse({"error":"unauthorized"},401)
    text=await asyncio.to_thread(build_context)
    return JSONResponse({"ok":True,"content":text,"length":len(text)})

async def memories(request):
    if not auth_ok(request):return JSONResponse({"error":"unauthorized"},401)
    return JSONResponse({"ok":True,"items":list_memories(limit=100)})

async def threads(request):
    if not auth_ok(request):return JSONResponse({"error":"unauthorized"},401)
    return JSONResponse({"ok":True,"items":get("threads","order=created_at.desc&limit=100")})

async def reminders(request):
    if not auth_ok(request):return JSONResponse({"error":"unauthorized"},401)
    return JSONResponse({"ok":True,"items":get("reminders","order=trigger_at.asc&limit=100")})

async def trigger_summary(request):
    if not auth_ok(request):return JSONResponse({"error":"unauthorized"},401)
    await asyncio.to_thread(run_nightly_summary);return JSONResponse({"ok":True})

async def trigger_compress(request):
    if not auth_ok(request):return JSONResponse({"error":"unauthorized"},401)
    await asyncio.to_thread(run_platform_batch_compress);return JSONResponse({"ok":True})
