"""Example tool module.

This demonstrates the public tool contract without publishing any of the
private project's real tool implementations.
"""


def echo(text: str) -> str:
    return text


SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "echo",
            "description": "Return the provided text. Example tool only.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    }
]


DISPATCH = {
    "echo": lambda args: echo(args.get("text", "")),
}
