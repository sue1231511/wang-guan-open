# Extending the public skeleton

## Add a tool

Create `tools_weather.py`, `tools_search.py`, or another domain module with the same three pieces used by `tools_example.py`:

```python
def my_tool(value: str) -> str:
    ...

SCHEMAS = [{...}]
DISPATCH = {"my_tool": lambda args: my_tool(args.get("value", ""))}
```

Then aggregate it in `free_tools.py`.

## Add a private persona

Do not hard-code it into the public repository. Recommended choices:

- deploy-time `PERSONA_TEXT`
- a private database table
- a separate private Python module mounted only in your deployment
- a private overlay repository

## Add a UI

Replace the placeholder under `miniapp/` with your own frontend. The original private project's MiniApp is intentionally not published.

## Add personal context

Extend `context.build_context()` privately. Typical sources might include recent conversation summaries or your own memory store. Do not copy secrets, raw personal datasets or private identity labels into a public repository.
