import os
import json
import hmac
import logging
import asyncio
import httpx
import uvicorn

from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.requests import Request
from starlette.routing import Route

from context import build_context

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

API_SECRET = os.environ.get("API_SECRET", "")
UPSTREAM_READ_TIMEOUT = int(os.environ.get("UPSTREAM_READ_TIMEOUT", "180"))


def _upstream_config():
    base = os.environ.get("LLM_BASE_URL", "").rstrip("/")
    key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "")
    if not base or not key or not model:
        raise RuntimeError("LLM_BASE_URL, LLM_API_KEY and LLM_MODEL are required")
    return base, key, model


def _authorized(request: Request) -> bool:
    if not API_SECRET:
        return True
    raw = request.headers.get("authorization", "")
    token = raw.split(" ", 1)[-1].strip() if " " in raw else raw.strip()
    return hmac.compare_digest(token, API_SECRET)


async def health(_: Request):
    return JSONResponse({"ok": True})


async def miniapp(_: Request):
    return FileResponse("miniapp/miniapp.html", media_type="text/html")


async def chat_completions(request: Request):
    if not _authorized(request):
        return JSONResponse({"error": {"message": "Unauthorized"}}, status_code=401)

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": {"message": "Invalid JSON"}}, status_code=400)

    messages = list(payload.get("messages") or [])
    system_prompt = build_context()
    if messages and messages[0].get("role") == "system":
        messages[0] = {**messages[0], "content": system_prompt}
    else:
        messages.insert(0, {"role": "system", "content": system_prompt})

    base, api_key, model = _upstream_config()
    payload["messages"] = messages
    payload["model"] = model

    # Public skeleton uses a buffered response for simplicity. If your client
    # requires SSE streaming, replace this route with your own streaming proxy.
    payload["stream"] = False
    timeout = httpx.Timeout(connect=30, read=UPSTREAM_READ_TIMEOUT, write=30, pool=30)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except Exception as exc:
        log.exception("upstream request failed")
        return JSONResponse({"error": {"message": str(exc)}}, status_code=502)

    try:
        data = resp.json()
    except Exception:
        return JSONResponse(
            {"error": {"message": "Upstream returned a non-JSON response"}},
            status_code=502,
        )
    return JSONResponse(data, status_code=resp.status_code)


app = Starlette(routes=[
    Route("/health", health, methods=["GET"]),
    Route("/miniapp", miniapp, methods=["GET"]),
    Route("/v1/chat/completions", chat_completions, methods=["POST"]),
])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
