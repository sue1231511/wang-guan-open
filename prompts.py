"""Generic prompt templates.

Do not place private persona text, personal relationship instructions, names,
health data, household lore or private correspondence rules in this public
module. Inject those from a private layer instead.
"""


def build_default_persona(assistant_name: str, user_name: str) -> str:
    return (
        f"You are {assistant_name}. You are speaking with {user_name}. "
        "Be helpful, consistent and natural. Follow the user's instructions "
        "and do not invent private facts that were not provided."
    )


SUMMARY_PROMPT = """Summarize the supplied conversation accurately.
Preserve important decisions, unresolved questions and concrete facts.
Do not invent events or personal details.

Conversation:
{content}
"""


THREAD_SCAN_PROMPT = """Inspect the supplied conversation and identify unresolved questions.
Return only genuinely unresolved items. Do not treat ordinary completed events
as open threads.

Conversation:
{content}
"""
