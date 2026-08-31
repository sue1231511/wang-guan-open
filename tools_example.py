"""Example public tool module.

A tool domain contains implementation + SCHEMAS + DISPATCH. Private tool services
from the author's deployment are not distributed in this repository.
"""


def echo(text: str) -> str:
    return text


SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "echo",
            "description": "Return the supplied text. Example tool for extension.",
            "parameters": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        },
    }
]

DISPATCH = {"echo": lambda args: echo(args.get("text", ""))}
