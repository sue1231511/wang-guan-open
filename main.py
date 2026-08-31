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
from free_tools import TOOL_SCHEMAS, TOOL_DISPATCH
from runtime_config import (
    load_config,
    save_config,
    get_active_provider,
    get_active_api_key,
    rotate_active_api_key,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", force=True)
log = logging.getLogger(__name__)

API_SECRET = os.environ.get("API_SECRET", "").strip()
ALLOW_INSECURE_NO_SECRET = os.environ.get("ALLOW_INSECURE_NO_SECRET", "0") == "1"
CORS_ALLOW_ORIGIN = os.environ.get("CORS_ALLOW_ORIGIN", "").strip()
UPSTREAM_READ_TIMEOUT = int(os.environ.get("UPSTREAM_READ_TIMEOUT", "180"))
INJECT_PUBLIC_TOOLS = os.environ.get("INJECT_PUBLIC_TOOLS", "0") == "1"
SYSTEM_INJECTION_MODE = os.environ.get("SYSTEM_INJECTION_MODE", "prepend").strip().lower()
if SYSTEM_INJECTION_MODE not in {"prepend", "append", "replace"}:
    SYSTEM_INJECTION_MODE = "prepend"
MAX_INTERNAL_TOOL_ROUNDS = max(1, min(int(os.environ.get("MAX_INTERNAL_TOOL_ROUNDS", "6")), 12))


def _upstream_config():
    provider = get_active_provider()
    if provider:
        base = str(provider.get("base_url") or "").rstrip("/")
        key = get_active_api_key(provider)
        model = str(provider.get("active_model") or provider.get("model") or "")
        extra_headers = provider.get("extra_headers") or {}
        if base and key and model:
            return base, key, model, extra_headers, True

    base = os.environ.get("LLM_BASE_URL", "").rstrip("/")
    key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "")
    if not base or not key or not model:
        raise RuntimeError("Configure an active provider in /miniapp or set LLM_BASE_URL, LLM_API_KEY and LLM_MODEL")
    return base, key, model, {}, False


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


def _headers(api_key: str, extra_headers: dict | None = None) -> dict:
    # Explicit custom headers may be useful for some compatible providers, but the
    # gateway's Authorization and Content-Type always win so an imported config
    # cannot silently redirect credentials into a different header value.
    custom = {str(k): str(v) for k, v in (extra_headers or {}).items()}
    custom.pop("Authorization", None)
    custom.pop("authorization", None)
    custom.pop("Content-Type", None)
    custom.pop("content-type", None)
    return {
        **custom,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _should_rotate(status_code: int) -> bool:
    return status_code in (401, 403, 408, 409, 429) or status_code >= 500


async def health(_: Request):
    provider = get_active_provider()
    return JSONResponse({
        "ok": True,
        "provider_configured": bool(provider) or bool(os.environ.get("LLM_BASE_URL")),
        "auth_enabled": bool(API_SECRET),
    })


async def miniapp(_: Request):
    return FileResponse("miniapp/miniapp.html", media_type="text/html")


async def admin_config(request: Request):
    if not _authorized(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    if request.method == "GET":
        return JSONResponse(load_config())
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"error": "Configuration must be an object"}, status_code=400)
    return JSONResponse(save_config(body))


async def admin_context_preview(request: Request):
    if not _authorized(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return JSONResponse({"context": build_context()})


async def _post_json_with_key_rotation(payload: dict):
    """POST once, and retry across configured keys on auth/rate/server failures."""
    base, api_key, model, extra_headers, runtime_provider = _upstream_config()
    payload["model"] = model
    target = f"{base}/chat/completions"
    timeout = httpx.Timeout(connect=30, read=UPSTREAM_READ_TIMEOUT, write=30, pool=30)

    provider = get_active_provider() if runtime_provider else None
    tries = len(provider.get("api_keys") or []) if provider else 1
    tries = max(1, tries)
    last_resp = None

    async with httpx.AsyncClient(timeout=timeout, http2=False) as client:
        for attempt in range(tries):
            if runtime_provider and attempt > 0:
                base, api_key, model, extra_headers, runtime_provider = _upstream_config()
                payload["model"] = model
                target = f"{base}/chat/completions"
            try:
                resp = await client.post(target, headers=_headers(api_key, extra_headers), json=payload)
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
                if runtime_provider and attempt + 1 < tries:
                    rotate_active_api_key()
                    continue
                raise
            last_resp = resp
            if runtime_provider and _should_rotate(resp.status_code) and attempt + 1 < tries:
                rotate_active_api_key()
                continue
            return resp
    return last_resp


async def _run_internal_tools(payload: dict) -> dict:
    """Run only the public repository's own tools. Client-supplied tools are untouched."""
    working = dict(payload)
    messages = list(working.get("messages") or [])
    working["stream"] = False
    working["tools"] = TOOL_SCHEMAS

    for _round in range(MAX_INTERNAL_TOOL_ROUNDS):
        working["messages"] = messages
        resp = await _post_json_with_key_rotation(working)
        if resp is None:
            raise RuntimeError("Upstream returned no response")
        try:
            data = resp.json()
        except Exception:
            raise RuntimeError("Upstream returned a non-JSON response")
        if resp.status_code >= 400:
            return data

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            return data

        messages.append(message)
        for call in tool_calls:
            function = call.get("function") or {}
            name = function.get("name") or ""
            raw_args = function.get("arguments") or "{}"
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
            except Exception:
                args = {}
            handler = TOOL_DISPATCH.get(name)
            if handler is None:
                result = json.dumps({"error": f"Unknown public tool: {name}"}, ensure_ascii=False)
            else:
                try:
                    value = handler(args)
                    result = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
                except Exception as exc:
                    log.exception("public tool failed: %s", name)
                    result = json.dumps({"error": type(exc).__name__}, ensure_ascii=False)
            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id", ""),
                "content": result,
            })

    return {
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": "[Maximum internal tool rounds reached]"},
            "finish_reason": "stop",
        }]
    }


def _final_text(data: dict) -> str:
    try:
        message = data["choices"][0]["message"]
        content = message.get("content")
        if isinstance(content, str):
            return content
        if content is None:
            return ""
        return json.dumps(content, ensure_ascii=False)
    except Exception:
        return ""


async def chat_completions(request: Request):
    if not _authorized(request):
        return JSONResponse({"error": {"message": "Unauthorized"}}, status_code=401)

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": {"message": "Invalid JSON"}}, status_code=400)

    payload["messages"] = _inject_system(payload.get("messages") or [])
    want_stream = bool(payload.get("stream", False))

    # Only execute tools that this public gateway itself injected. If a client
    # supplied its own tools, the gateway remains a transparent proxy and leaves
    # execution to that client.
    internal_tools = bool(INJECT_PUBLIC_TOOLS and TOOL_SCHEMAS and not payload.get("tools"))
    if internal_tools:
        try:
            data = await _run_internal_tools(payload)
        except Exception as exc:
            log.exception("internal tool loop failed")
            return JSONResponse({"error": {"message": str(exc)}}, status_code=502)
        if not want_stream:
            return JSONResponse(data)

        text = _final_text(data)
        async def one_shot_stream():
            if text:
                chunk = json.dumps({
                    "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}]
                }, ensure_ascii=False)
                yield f"data: {chunk}\n\n".encode("utf-8")
            yield b"data: [DONE]\n\n"
        return StreamingResponse(one_shot_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

    # Transparent path for normal client-managed requests.
    try:
        base, api_key, model, extra_headers, runtime_provider = _upstream_config()
    except RuntimeError as exc:
        return JSONResponse({"error": {"message": str(exc)}}, status_code=500)

    payload["model"] = model
    timeout = httpx.Timeout(connect=30, read=UPSTREAM_READ_TIMEOUT, write=30, pool=30)
    target = f"{base}/chat/completions"

    if not want_stream:
        try:
            resp = await _post_json_with_key_rotation(payload)
        except Exception as exc:
            log.exception("upstream request failed")
            return JSONResponse({"error": {"message": str(exc)}}, status_code=502)
        if resp is None:
            return JSONResponse({"error": {"message": "Upstream returned no response"}}, status_code=502)
        try:
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            return JSONResponse({"error": {"message": "Upstream returned a non-JSON response"}}, status_code=502)

    async def event_stream():
        # Streaming retries keys only before any body bytes are sent. Once streaming
        # starts, switching providers/keys mid-response would corrupt the SSE stream.
        provider = get_active_provider() if runtime_provider else None
        tries = len(provider.get("api_keys") or []) if provider else 1
        tries = max(1, tries)
        for attempt in range(tries):
            if runtime_provider and attempt > 0:
                try:
                    b, k, m, eh, _ = _upstream_config()
                except RuntimeError:
                    break
            else:
                b, k, m, eh = base, api_key, model, extra_headers
            stream_payload = dict(payload)
            stream_payload["model"] = m
            client = httpx.AsyncClient(timeout=timeout, http2=False)
            try:
                async with client.stream("POST", f"{b}/chat/completions", headers=_headers(k, eh), json=stream_payload) as resp:
                    if resp.status_code >= 400:
                        body = (await resp.aread()).decode("utf-8", errors="replace")[:1000]
                        if runtime_provider and _should_rotate(resp.status_code) and attempt + 1 < tries:
                            rotate_active_api_key()
                            continue
                        chunk = json.dumps({
                            "choices": [{"index": 0, "delta": {"content": f"[Upstream error {resp.status_code}] {body}"}, "finish_reason": "stop"}]
                        }, ensure_ascii=False)
                        yield f"data: {chunk}\n\ndata: [DONE]\n\n".encode("utf-8")
                        return
                    async for raw in resp.aiter_bytes():
                        if raw:
                            yield raw
                    return
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
                if runtime_provider and attempt + 1 < tries:
                    rotate_active_api_key()
                    continue
                log.exception("stream proxy failed")
                chunk = json.dumps({
                    "choices": [{"index": 0, "delta": {"content": f"[Connection interrupted: {type(exc).__name__}]"}, "finish_reason": "stop"}]
                })
                yield f"data: {chunk}\n\ndata: [DONE]\n\n".encode("utf-8")
                return
            except Exception as exc:
                log.exception("stream proxy failed")
                chunk = json.dumps({
                    "choices": [{"index": 0, "delta": {"content": f"[Connection interrupted: {type(exc).__name__}]"}, "finish_reason": "stop"}]
                })
                yield f"data: {chunk}\n\ndata: [DONE]\n\n".encode("utf-8")
                return
            finally:
                await client.aclose()

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


app = Starlette(routes=[
    Route("/health", health, methods=["GET"]),
    Route("/miniapp", miniapp, methods=["GET"]),
    Route("/admin/config", admin_config, methods=["GET", "PUT"]),
    Route("/admin/context-preview", admin_context_preview, methods=["GET"]),
    Route("/v1/chat/completions", chat_completions, methods=["POST"]),
])

if CORS_ALLOW_ORIGIN:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in CORS_ALLOW_ORIGIN.split(",") if origin.strip()],
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        allow_credentials=False,
    )


if __name__ == "__main__":
    if API_SECRET == "change-me":
        log.warning("API_SECRET is still the example value 'change-me'. Replace it before public deployment.")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
