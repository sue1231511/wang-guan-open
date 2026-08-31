import os
import json
import hmac
import logging
import httpx
import uvicorn

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, StreamingResponse
from starlette.routing import Route
from starlette.middleware.cors import CORSMiddleware

from context import build_context
from free_tools import TOOL_SCHEMAS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", force=True)
log = logging.getLogger(__name__)

API_SECRET = os.environ.get("API_SECRET", "").strip()
ALLOW_INSECURE_NO_SECRET = os.environ.get("ALLOW_INSECURE_NO_SECRET", "0") == "1"
CORS_ALLOW_ORIGIN = os.environ.get("CORS_ALLOW_ORIGIN", "").strip()
UPSTREAM_READ_TIMEOUT = int(os.environ.get("UPSTREAM_READ_TIMEOUT", "180"))
INJECT_PUBLIC_TOOLS = os.environ.get("INJECT_PUBLIC_TOOLS", "0") == "1"


def _upstream_config():
    base = os.environ.get("LLM_BASE_URL", "").rstrip("/")
    key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "")
    if not base or not key or not model:
        raise RuntimeError("LLM_BASE_URL, LLM_API_KEY and LLM_MODEL are required")
    return base, key, model


def _authorized(request: Request) -> bool:
    if not API_SECRET:
        return ALLOW_INSECURE_NO_SECRET
    raw = request.headers.get("authorization", "")
    token = raw.split(" ", 1)[-1].strip() if " " in raw else raw.strip()
    return hmac.compare_digest(token, API_SECRET)


def _inject_system(messages: list) -> list:
    messages = list(messages or [])
    system_prompt = build_context()
    if messages and messages[0].get("role") == "system":
        messages[0] = {**messages[0], "content": system_prompt}
    else:
        messages.insert(0, {"role": "system", "content": system_prompt})
    return messages


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

    try:
        base, api_key, model = _upstream_config()
    except RuntimeError as exc:
        return JSONResponse({"error": {"message": str(exc)}}, status_code=500)

    payload["messages"] = _inject_system(payload.get("messages") or [])
    payload["model"] = model

    # Optional example hook. Disabled by default because many clients manage their
    # own tools. The repository only ships a harmless echo example.
    if INJECT_PUBLIC_TOOLS and TOOL_SCHEMAS and not payload.get("tools"):
        payload["tools"] = TOOL_SCHEMAS

    want_stream = bool(payload.get("stream", False))
    timeout = httpx.Timeout(connect=30, read=UPSTREAM_READ_TIMEOUT, write=30, pool=30)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    target = f"{base}/chat/completions"

    if not want_stream:
        try:
            async with httpx.AsyncClient(timeout=timeout, http2=False) as client:
                resp = await client.post(target, headers=headers, json=payload)
        except Exception as exc:
            log.exception("upstream request failed")
            return JSONResponse({"error": {"message": str(exc)}}, status_code=502)
        try:
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            return JSONResponse({"error": {"message": "Upstream returned a non-JSON response"}}, status_code=502)

    async def event_stream():
        client = httpx.AsyncClient(timeout=timeout, http2=False)
        try:
            async with client.stream("POST", target, headers=headers, json=payload) as resp:
                if resp.status_code >= 400:
                    body = (await resp.aread()).decode("utf-8", errors="replace")[:1000]
                    chunk = json.dumps({
                        "choices": [{"index": 0, "delta": {"content": f"[Upstream error {resp.status_code}] {body}"}, "finish_reason": "stop"}]
                    }, ensure_ascii=False)
                    yield f"data: {chunk}\n\ndata: [DONE]\n\n".encode("utf-8")
                    return
                async for raw in resp.aiter_bytes():
                    if raw:
                        yield raw
        except httpx.ReadTimeout:
            chunk = json.dumps({
                "choices": [{"index": 0, "delta": {"content": "[Upstream read timeout]"}, "finish_reason": "stop"}]
            })
            yield f"data: {chunk}\n\ndata: [DONE]\n\n".encode("utf-8")
        except Exception as exc:
            log.exception("stream proxy failed")
            chunk = json.dumps({
                "choices": [{"index": 0, "delta": {"content": f"[Connection interrupted: {type(exc).__name__}]"}, "finish_reason": "stop"}]
            })
            yield f"data: {chunk}\n\ndata: [DONE]\n\n".encode("utf-8")
        finally:
            await client.aclose()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )


app = Starlette(routes=[
    Route("/health", health, methods=["GET"]),
    Route("/miniapp", miniapp, methods=["GET"]),
    Route("/v1/chat/completions", chat_completions, methods=["POST"]),
])

if CORS_ALLOW_ORIGIN:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in CORS_ALLOW_ORIGIN.split(",") if origin.strip()],
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=False,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
