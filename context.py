"""Public context-builder skeleton.

The private project has a much richer context engine. This public version keeps
only the extension boundary and intentionally omits personal memories, device
state, health data, locations, schedules, private diaries and relationship data.
"""

import os
from prompts import build_default_persona


def build_context() -> str:
    assistant_name = os.environ.get("ASSISTANT_NAME", "Assistant")
    user_name = os.environ.get("USER_NAME", "User")
    private_persona = os.environ.get("PERSONA_TEXT", "").strip()

    parts = [build_default_persona(assistant_name, user_name)]
    if private_persona:
        parts.append(private_persona)
    return "\n\n".join(parts)


# Extension point:
# Replace build_context() in a private overlay if you want to load your own
# database-backed memories, summaries, schedules or cross-platform context.
