"""Public prompt templates.

These are intentionally generic examples. Replace them in your private deployment or through
bot_settings. The public repository does not ship the author's persona, relationship wording,
private names, diary instructions or household lore.
"""
from app_config import AI_NAME, USER_NAME

BASE_PERSONA_EXAMPLE = f"""You are {AI_NAME}. You are a conversational assistant for {USER_NAME}.
Speak naturally and follow the user's configured preferences. Do not invent private facts."""

GROUP_CHAT_EXAMPLE = """You are participating in a group chat. Use the supplied speaker labels to understand who is talking to whom. Reply briefly when addressed or when you have something useful to add. If no reply is needed, output PASS."""

PROACTIVE_EXAMPLE = """Review recent context and decide whether a proactive message would be useful. Output SEND followed by the message, or PASS. Do not manufacture urgency or personal facts."""

FREE_ACTIVITY_EXAMPLE = """You are in a background autonomous-work cycle. Inspect available context and tools. You may perform useful low-risk actions, read memory, or record an activity log. Do not perform sensitive external actions unless the deployment explicitly enables them."""

CHAT_DAY_SUMMARY = """Summarize the following conversation period {period_start} to {period_end}. Preserve concrete events, decisions, preferences and unresolved items. Do not invent details.\n\n{content}"""
CHAT_WEEK_SUMMARY = CHAT_DAY_SUMMARY
CHAT_MONTH_SUMMARY = CHAT_DAY_SUMMARY
CHAT_YEAR_SUMMARY = CHAT_DAY_SUMMARY
ACTIVITY_DAY_SUMMARY = """Summarize background activity from {period_start} to {period_end}. Preserve actions, results and important failures.\n\n{content}"""
PLATFORM_BATCH_SUMMARY = """Summarize this batch of cross-platform messages from {period_start} to {period_end}. Preserve scene distinctions and unresolved items.\n\n{content}\n\n{taboo_instruction}"""
PLATFORM_SUMMARY_MERGE = """Merge these rolling summaries into one coherent recent-context summary as of {current_time}. Remove duplicates, keep dates and unresolved items.\n\n{content}\n\n{taboo_instruction}"""
CURRENT_MEMORY_REFRESH = """Rewrite the current-state memory layer from the recent summaries. Return JSON only: {{\"memories\":[{{\"content\":\"...\",\"importance\":3}}]}}.\nExisting ({current_count}):\n{current_memories}\n\nRecent summaries ({summary_count}):\n{chat_summaries}"""
THREAD_SCAN = """Maintain unresolved threads. Given existing threads and the latest summary, return JSON only with new_threads and updates. Use ACTIVE for new threads, DORMANT for paused, SILENT for resolved/closed.\n\nExisting:\n{existing_threads}\n\nLatest:\n{chat_summary}"""
PLATFORM_MEMORY_EXTRACT = """Extract only genuinely durable new memories from the new rolling summaries. Avoid duplicates against existing memories. Return JSON only: {{\"memories\":[]}} or objects with content/category/importance/emotion_valence.\nExisting:\n{existing_memories}\n\nNew:\n{content}"""
PERSONA_REFLECTION = """Update the configurable persona while preserving its established stable traits. Return JSON only: {{\"persona\":\"...\"}}.\nCurrent persona:\n{persona}\n\nMemories:\n{memories}\n\nRecent summary:\n{chat_summary}"""
