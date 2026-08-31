from datetime import datetime,timezone
from storage import insert,get,update

def reminder_add(message,trigger_at,repeat_type="once"):
    insert("reminders",{"message":message,"trigger_at":trigger_at,"repeat_type":repeat_type,"is_done":False});return "Reminder created."
def reminder_list(include_done=False):
    q="order=trigger_at.asc&limit=50"+("" if include_done else "&is_done=eq.false")
    rows=get("reminders",q);return "\n".join(f"- {r.get('trigger_at')} | {r.get('message')} | {r.get('repeat_type','once')}" for r in rows) or "No reminders."
SCHEMAS=[{"type":"function","function":{"name":"reminder_add","description":"Create a reminder. trigger_at must be an ISO timestamp.","parameters":{"type":"object","properties":{"message":{"type":"string"},"trigger_at":{"type":"string"},"repeat_type":{"type":"string","enum":["once","daily","weekly"],"default":"once"}},"required":["message","trigger_at"]}}},{"type":"function","function":{"name":"reminder_list","description":"List reminders.","parameters":{"type":"object","properties":{"include_done":{"type":"boolean","default":False}}}}}]
DISPATCH={"reminder_add":lambda a:reminder_add(a.get("message",""),a.get("trigger_at",""),a.get("repeat_type","once")),"reminder_list":lambda a:reminder_list(a.get("include_done",False))}
