# Wang Guan Open

A clean, open-source gateway skeleton derived from a private personal AI gateway.

This repository intentionally **does not contain** the original owner's private UI, personal prompts, relationship/persona settings, private tool implementations, private service URLs, personal names, household data, private automation logic, or private datasets.

The goal is to keep the reusable architecture and extension pattern while making every identity-specific and private part opt-in.

## Included

- OpenAI-compatible `/v1/chat/completions` proxy
- Environment-based assistant/user naming
- Replaceable context builder
- Replaceable prompt templates
- Minimal MiniApp placeholder only
- Tool aggregation pattern with one harmless example tool
- Background task extension pattern
- Docker deployment example
- Privacy checklist for maintainers

## Deliberately removed

The private project contains modules and data that are not part of this open-source version, including but not limited to:

- Original MiniApp UI/CSS/JS and visual design
- Personal persona and relationship prompts
- Personal nicknames, names and identity anchors
- Private household/pet/world-building data
- Private free-activity prompt and autonomous behavior rules
- Email contacts and personal correspondence rules
- Personal health, cycle, work schedule, device and location context
- Private tools and MCP implementations
- Private bot/channel IDs, URLs, tokens and service-specific configuration
- Personal memories, summaries, diary content and database records

If you need one of these features, implement your own version using the extension examples in this repository.

## Quick start

```bash
cp .env.example .env
# fill in your own values
pip install -r requirements.txt
python main.py
```

Default server port: `8000`.

### Required environment variables

```env
API_SECRET=change-me
LLM_BASE_URL=https://example.com/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
ASSISTANT_NAME=Assistant
USER_NAME=User
```

The upstream URL should normally be an OpenAI-compatible base URL ending in `/v1`.

## MiniApp

`miniapp/miniapp.html` is intentionally only a tiny placeholder. It demonstrates where a UI can be mounted without publishing the private project's original design.

## Tools

The original project's private tool collection is not published here. `tools_example.py` shows the required pattern:

1. implement a function
2. add a schema to `SCHEMAS`
3. add a handler to `DISPATCH`
4. aggregate the module in `free_tools.py`

Create your own `tools_xxx.py` modules for additional domains.

## Prompts

`prompts.py` contains generic examples only. Do not commit your private persona prompt. Keep personal prompts in environment variables, a private database, or a private overlay repository.

## Recommended deployment model

Keep this repository public and maintain a second private repository or private configuration layer containing:

- persona text
- private UI
- private tools
- secret integrations
- user-specific context builders

That split prevents future updates from accidentally publishing private material.

## License

MIT. See `LICENSE`.
