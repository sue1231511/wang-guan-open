# Wang Guan Open

> [中文](README.md)

`wang-guan-open` is the **source-available, non-commercial** edition of a private long-running AI gateway. The latest private `wang-guan` codebase is treated as the functional reference: engineering capabilities should be preserved whenever possible, while the author's personal persona, relationship wording, data, visual UI, credentials and private services are removed or replaced with configurable examples.

**This project is not Open Source Software under the OSI definition.** It is licensed under PolyForm Noncommercial License 1.0.0. Commercial resale, paid SaaS, paid hosting and other commercial use are not permitted unless separately authorized. See `LICENSE`.

## What is included

The public build is no longer a minimal skeleton. It currently includes an OpenAI-compatible streaming gateway, configurable Context Builder, Supabase persistence, layered memory, optional Mem0 semantic memory, summaries / threads / reminders, multi-provider and multi-key configuration, internal Tool Calling, reusable MCP sessions, generic Telegram / QQ / WeChat adapters, and a functionally useful MiniApp admin console with a visual design separate from the private UI.

See `docs/MIGRATION_STATUS.md` for the feature-by-feature restoration status.

## Quick start

Configure at least:

```env
API_SECRET=please-change-this
LLM_BASE_URL=https://your-provider.example/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
```

Then:

```bash
pip install -r requirements.txt
python main.py
```

Container deployments may use `entrypoint.sh`, which runs the real-time message process and the independent background process together.

### Security

Set `API_SECRET` for any public deployment. Without it, chat requests are rejected by default unless `ALLOW_INSECURE_NO_SECRET=1` is explicitly enabled for local testing. Browser CORS is disabled by default; use `CORS_ALLOW_ORIGIN` with trusted origins when needed.

Telegram webhooks use an independent `TG_WEBHOOK_SECRET`. If Telegram webhook delivery is enabled, configure the same secret when registering the webhook; `/webhook` rejects requests when it is missing or does not match.

Successful gateway conversations are persisted when Supabase is configured unless `PERSIST_CONVERSATIONS=0` is set. The nightly maintenance task runs once per local day at `NIGHTLY_SUMMARY_HOUR` in `APP_TIMEZONE`, while due reminders remain pending when no delivery transport is configured instead of being silently marked complete.

## System prompt injection

`SYSTEM_INJECTION_MODE` supports:

- `prepend` (default): gateway context first, preserve the client's system prompt
- `append`: client system prompt first, gateway context after it
- `replace`: fully replace the client's system prompt

The public build does not silently discard a client's own system prompt by default.

## Context and memory

The generic Context Builder can assemble a configurable persona, `core/current/long_term` memories, rolling cross-platform summaries, `ACTIVE/DORMANT` threads, time context and extension providers. Optional Mem0 semantic memory can also be enabled with your own credentials.

## Models and channels

The simple deployment path uses `LLM_*`. Independent chat/background/vision/proactive/QQ/WeChat channels are also supported. With a Supabase `llm_config` table, deployments may separate providers using `active`, `bg_active`, `vision_active`, `free_activity_active`, `qq_active` and `wx_active` flags.

The MiniApp supports provider management, multiple API keys and models, Prompt / Context preview, streaming chat testing, memories, threads, reminders, maintenance tasks and config import/export. It preserves the **functional value** of the private MiniApp without publishing the author's visual design.

## Tools and MCP

The public build contains working generic examples for memory, activity logs, reminders and configurable MCP weather/search calls. Tool modules use:

```python
SCHEMAS = [...]
DISPATCH = {...}
```

and are aggregated by `free_tools.py`. `tools_base.py` preserves MCP initialize/session reuse/session rebuild behavior. Private MCP endpoints are not embedded; point the environment variables at your own services.

## Platform adapters

- Telegram: webhook, owner restrictions, group mode, delayed aggregation and tools
- QQ: OneBot v11 forward WebSocket at `/qq-ws`, private/group chat and basic REPLY/AT formatting
- WeChat: iLink text long polling, persisted `context_token` and owner restrictions

A generic Vision / STT / TTS helper layer is included. Remaining private-version media details are being restored through generalized implementations rather than copied with private defaults; see `docs/MIGRATION_STATUS.md`.

## Private overlay

A recommended layout is:

```text
wang-guan-open/       # public engineering layer
my-private-overlay/   # your private layer
├─ persona/
├─ prompts/
├─ ui/
├─ tools/
├─ integrations/
└─ private-config/
```

The author's private persona, relationship terms, original MiniApp UI, private memory contents, health/location/schedule data, private MCP services, real IDs/keys/tokens and private household/world data are not included.

### Secret diary boundary

The private version's diary behavior historically existed in more than one place: a tool module, worker tool lists and background `[DIARY]...[/DIARY]` parsers. The public edition therefore does **not** ship the author's secret-diary implementation or automatic diary-writing behavior. Developers may implement their own private diary tool in a private overlay using the public Tool pattern.

## License

PolyForm Noncommercial License 1.0.0. Learning, research, modification and non-commercial deployment/distribution are allowed under the license; commercial sale, paid services and commercial hosting are not.
