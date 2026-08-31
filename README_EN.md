# Wang Guan Open

> [中文](README.md)

`wang-guan-open` is the **source-available edition** extracted from a private AI gateway project.

It publishes reusable engineering structure, interfaces, and extension patterns. It does not include the original project's private persona, relationship settings, custom UI, personal memories, life data, private tools, or private service configuration.

**This project is not Open Source Software under the OSI definition.** It is licensed under the PolyForm Noncommercial License 1.0.0 and is intended for noncommercial use only. Selling the project, commercializing derivatives, or providing paid services based on it is not permitted under the license. See `LICENSE` for the complete terms.

---

## 1. Purpose

This repository is an extensible AI gateway skeleton for building long-running personal AI systems, companion-style AI, chatbot gateways, or agent services.

The public layer focuses on reusable patterns such as:

- an OpenAI-compatible `/v1/chat/completions` endpoint
- OpenAI-compatible upstream LLM providers
- dynamic system-context construction
- prompt extension hooks
- Function Calling / Tool Calling patterns
- background and autonomous task structure
- MiniApp / admin-page mounting
- a private-overlay architecture

The public version does not assume what the AI should be called, who the user is, or what relationship exists between them.

---

## 2. Relationship to the private project

The private production repository has been used for real personal scenarios for a long time and contains information that belongs only to its original author, including:

- private persona prompts
- relationship settings and private forms of address
- private conversation rules
- original MiniApp HTML / CSS / JavaScript
- private long-term memories and diaries
- device, location, health, and work-schedule data
- private email contacts
- household, pet, and fictional-world data
- private MCP / API services
- private tool implementations
- bot IDs, group IDs, tokens, keys, and service configuration

None of that belongs in this repository.

This repository is not a mirror of the private project and does not attempt to preserve a one-to-one file layout. It is the reusable engineering layer extracted from it.

```text
Private production project
├─ gateway core
├─ context system
├─ background tasks
├─ tool system
├─ private persona / prompts
├─ private UI
├─ private life data
├─ private services
└─ personal behavior logic

        ↓ public-safe extraction only

wang-guan-open
├─ generic gateway structure
├─ context extension interface
├─ prompt examples
├─ tool extension pattern
├─ background-task example
└─ MiniApp mounting example
```

---

## 3. Current architecture

The public edition is rebuilt from the latest private-project architecture rather than copied from an older generalized snapshot.

```text
container
├─ main.py
│  └─ realtime HTTP / OpenAI-compatible gateway
└─ background_main.py
   └─ independent background-task process
```

Both processes are launched by `entrypoint.sh`. If either exits, the other is stopped as well so the deployment platform can restart the service as one unit instead of leaving a half-dead deployment running.

The public core also keeps several reusable engineering patterns from the latest architecture:

- `bg_executor.py`: bounded shared thread pool for fire-and-forget work
- `context.py`: registerable Context Provider mechanism
- `free_tools.py`: Schema / Dispatch aggregation layer for tools
- `background_tasks.py`: background coroutine registration point
- `platforms/`: extension boundary for transport adapters

The private deployment's personal behavior layer is intentionally excluded from these structures.

---

## 4. OpenAI-compatible gateway

The public skeleton exposes:

```text
POST /v1/chat/completions
```

It can connect to an upstream provider that implements the OpenAI Chat Completions API format.

Basic configuration:

```env
API_SECRET=change-me
LLM_BASE_URL=https://example.com/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
```

> **Always set `API_SECRET` for any public deployment.** When it is empty, the public build rejects `/v1/chat/completions` by default. Unauthenticated access is only enabled when `ALLOW_INSECURE_NO_SECRET=1` is explicitly set, and that option is intended for local testing only. Otherwise, exposing the service publicly can let anyone consume your upstream model quota.
>
> Cross-origin browser access is disabled by default. Set `CORS_ALLOW_ORIGIN` only when needed, using one or more trusted origins separated by commas. Avoid `*` on public deployments.

Run locally:

```bash
pip install -r requirements.txt
python main.py
```

Default bind address:

```text
0.0.0.0:8000
```

---

## 5. Context Builder

`context.py` provides the extension point for system-context construction.

Minimal example:

```python
def build_context() -> str:
    return "Your system context here"
```

You can add your own:

- persona configuration
- user profile
- long-term memory
- conversation summaries
- time and calendar context
- database state
- domain-specific information

Private context queries and personal data injection logic from the production project are intentionally not published.

Sensitive configuration should live in environment variables, a private database, or a separate private overlay.

---

## 6. Prompts

`prompts.py` contains only generic examples and template patterns.

The following material from the private project is intentionally excluded:

- original persona text
- private forms of address
- relationship-specific rules
- autonomous/free-activity prompts
- private diary and summary prompts
- personal behavior rules

Prefer placeholders or environment variables:

```python
AI_NAME = os.environ.get("AI_NAME", "AI")
USER_NAME = os.environ.get("USER_NAME", "User")
```

Do not commit real private prompt material into a public repository.

---

## 7. Tool extensions

The private project contains many integrations and tool implementations. Those concrete implementations are not part of this repository.

The public version keeps only the extension pattern:

```python
def example_tool(text: str) -> str:
    return text

SCHEMAS = [{
    "type": "function",
    "function": {
        "name": "example_tool",
        "description": "Example tool",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string"}
            },
            "required": ["text"]
        }
    }
}]

DISPATCH = {
    "example_tool": lambda args: example_tool(args["text"])
}
```

`free_tools.py` acts as the aggregation layer.

You can create your own modules following the same convention:

```text
tools_weather.py
tools_search.py
tools_calendar.py
tools_memory.py
tools_xxx.py
```

---

## 8. Background tasks

`background_main.py` keeps the basic organization pattern for background workloads such as:

- scheduled summaries
- memory maintenance
- synchronization
- periodic checks
- autonomous agent jobs
- message polling

The private project's personal automation and life-specific behavior are not included.

---

## 9. MiniApp / UI

The production MiniApp is a private UI designed and iterated by the original author over time.

**Its original HTML, CSS, JavaScript, component structure, and visual design are not part of this public repository.**

The repository therefore contains only a minimal mounting example:

```text
miniapp/miniapp.html
```

Design your own frontend.

This is an intentional publication boundary, not an incomplete feature.

---

## 10. Recommended private overlay

Keep the public core and your personal layer separate:

```text
wang-guan-open/        # source-available public core

my-private-overlay/    # your private repository
├─ persona/
├─ prompts/
├─ ui/
├─ tools/
├─ integrations/
└─ private-config/
```

See `PRIVATE_OVERLAY.example.md` for a minimal example.

This structure makes future sharing, migration, and privacy review substantially easier.

---

## 11. License

This project is licensed under the **PolyForm Noncommercial License 1.0.0**.

Permitted examples include:

- personal study and research
- noncommercial deployment
- source modification
- noncommercial derivative works
- noncommercial redistribution in compliance with the license

Commercial use is not licensed, including examples such as:

- selling this project or a derivative
- including it in a paid product
- providing a paid SaaS or hosted service based on it
- other use intended for commercial gain

For commercial licensing, obtain separate permission from the author.

Because commercial use is restricted, this project is **source-available**, not Open Source Software under the OSI definition.

The complete legal terms are in `LICENSE`.

---

## 12. Project boundary

This repository publishes how the system is built. It does not publish the author's private AI.

The engineering structure may be studied and adapted for noncommercial purposes, but the author's persona, relationship model, UI, memories, private data, and private services remain outside the public project.
