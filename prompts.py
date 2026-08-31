"""Generic prompt templates.

The author's personal persona, relationship prompts, diary wording, autonomous
behavior rules and private naming conventions are intentionally excluded.
"""

SUMMARY_PROMPT = """Summarize the following conversation accurately and concisely.
Preserve important facts, decisions, unresolved items, and emotional context when relevant.
Do not invent information.

Conversation:
{content}"""

MEMORY_EXTRACT_PROMPT = """Extract only durable facts or preferences worth remembering.
Avoid trivial details and duplicates. Return strict JSON using this shape:
{{"memories": [{{"content": "...", "importance": 1}}]}}
If nothing is worth keeping, return {{"memories": []}}.

Existing memories:
{existing_memories}

New material:
{content}"""

THREAD_SCAN_PROMPT = """Identify unresolved topics that may need follow-up later.
Return strict JSON:
{{"new_threads": [{{"title": "...", "evidence": "..."}}], "updates": []}}
If there is nothing unresolved, return empty arrays.

Conversation summary:
{chat_summary}"""
