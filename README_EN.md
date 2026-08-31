# Wang Guan Open

> [中文](README.md)

Wang Guan Open is a general-purpose gateway and runtime framework for personal AI systems.

It brings model providers, chat clients, messaging platforms, context, memory, tool calling and background jobs into one runtime. It exposes an OpenAI-compatible API and can also connect directly to Telegram, QQ and WeChat.

If you want to build a long-running AI system with memory, multiple model providers, multiple chat entry points and room for custom tools and background automation, this project can be used as the foundation.

## Core capabilities

### OpenAI-compatible gateway

Endpoint:

```text
POST /v1/chat/completions
```

Supports:

- SSE streaming
- OpenAI-compatible request format
- reasoning-content compatibility
- upstream timeouts
- multi-key rotation on failures
- transparent forwarding of client-managed tools
- optional internal Tool Calling

### Multi-provider / multi-model runtime

Each provider can contain:

- Base URL
- multiple API keys
- multiple models
- active model
- custom headers

Independent model channels are supported for:

- chat
- background
- vision
- proactive
- QQ
- WeChat

Configuration can come from environment variables, Supabase `llm_config`, or the generic Runtime Provider managed by the MiniApp.

### Context Builder

Before each model call, the gateway can assemble:

- System Prompt
- Persona Profile
- `core / current / long_term` layered memories
- cross-platform rolling summaries
- `ACTIVE / DORMANT` threads
- current time
- custom Context Providers

Additional context sources can be registered without turning the main gateway into a monolith.

### Memory and conversation maintenance

Supabase-backed persistence supports:

- conversation history
- layered memories
- optional Mem0 semantic memory
- daily summaries
- current-memory refresh
- thread scanning and state maintenance
- cross-platform batch compression
- rolling-summary merging
- long-term memory extraction
- recent-summary window maintenance

The runtime is designed for long-lived AI sessions rather than stateless one-off requests.

### Tool Calling / MCP

Internal tools use a simple registry pattern:

```python
SCHEMAS = [...]
DISPATCH = {...]
```

and are aggregated by `free_tools.py`.

The MCP helper layer includes:

- initialize
- reusable sessions
- `Mcp-Session-Id`
- session rebuild after invalidation
- JSON / SSE response parsing

Generic examples are included and can be replaced or extended with your own tools and MCP services.

### Messaging platforms

Current adapters include:

- Telegram webhook
- Telegram private/group chat
- QQ OneBot v11 forward WebSocket
- QQ private/group chat
- QQ REPLY / AT formatting
- WeChat iLink text long polling
- persisted WeChat `context_token`
- delayed message aggregation
- tool loops inside platform conversations

### Vision / speech helpers

Generic helpers are included for:

- Vision
- STT
- TTS

Platform-specific image, audio, reply and sticker behavior can be extended on top of the existing adapters.

### Reminders and background jobs

The independent background process handles jobs such as:

- reminder checking and delivery
- daily / weekly recurring reminders
- nightly summaries
- cross-platform message compression
- rolling-summary maintenance

`entrypoint.sh` starts both the real-time gateway and background process.

### MiniApp admin console

A lightweight admin page is included for:

- provider management
- multiple API keys
- multiple models
- active-model selection
- System Prompt editing
- Context preview
- memory inspection
- thread inspection
- reminder inspection
- manual summary / compression triggers
- streaming chat tests
- Runtime config import / export

Open:

```text
/miniapp
```

## Quick start

Copy `.env.example` and configure at least:

```env
API_SECRET=please-change-this
LLM_BASE_URL=https://your-provider.example/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the gateway:

```bash
python main.py
```

To run the gateway and background process together:

```bash
./entrypoint.sh
```

Docker uses the same entrypoint.

## Common configuration

### Gateway

```env
API_SECRET=
PORT=8000
UPSTREAM_READ_TIMEOUT=180
SYSTEM_INJECTION_MODE=prepend
PERSIST_CONVERSATIONS=1
```

`SYSTEM_INJECTION_MODE` supports:

- `prepend`
- `append`
- `replace`

### Default model

```env
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

### Independent model channels

```env
CHAT_BASE_URL=
CHAT_API_KEY=
CHAT_MODEL=

BG_CHAT_BASE_URL=
BG_CHAT_API_KEY=
BG_CHAT_MODEL=

VISION_BASE_URL=
VISION_API_KEY=
VISION_MODEL=

PROACTIVE_BASE_URL=
PROACTIVE_API_KEY=
PROACTIVE_MODEL=

QQ_LLM_BASE_URL=
QQ_LLM_API_KEY=
QQ_LLM_MODEL=

WX_LLM_BASE_URL=
WX_LLM_API_KEY=
WX_LLM_MODEL=
```

Channels without their own configuration fall back to the resolved chat model.

### Supabase

```env
SUPABASE_URL=
SUPABASE_KEY=
```

Used for conversation history, memories, threads, reminders, summaries and selected runtime configuration.

### Telegram

```env
TG_BOT_TOKEN=
TG_OWNER_ID=
TG_GROUP_IDS=
TG_WEBHOOK_SECRET=
```

### QQ

```env
QQ_WS_TOKEN=
QQ_BOT_ID=
QQ_OWNER_ID=
QQ_GROUP_IDS=
```

OneBot v11 WebSocket endpoint:

```text
/qq-ws
```

### WeChat

```env
WX_ILINK_TOKEN=
WX_ILINK_BOT_ID=
WX_OWNER_ID=
```

## Extension points

The project is designed to be extended through separate modules instead of growing one large core file.

Typical extension points:

```text
Context Provider  -> new context sources
Tool Module       -> new callable tools
MCP               -> external capabilities
Platform Adapter  -> additional chat platforms
Background Task   -> periodic jobs
MiniApp           -> custom administration features
```

## License

PolyForm Noncommercial License 1.0.0.

Learning, research, modification and non-commercial deployment/distribution are allowed. Commercial sale, paid SaaS, paid hosting and other commercial use are outside the license. See `LICENSE` for the full terms.
