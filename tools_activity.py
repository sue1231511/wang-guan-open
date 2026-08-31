from storage import insert,get

def log_activity(thinking="",action="nothing",action_input=None,result=""):
    insert("activity_log",{"thinking":thinking,"action":action,"action_input":action_input or {},"result":result});return "Activity logged."
def activity_recent(limit=5):
    rows=get("activity_log",f"order=created_at.desc&limit={min(max(int(limit),1),20)}&select=created_at,action,thinking,result")
    rows.reverse();return "\n".join(f"[{r.get('created_at','')[:16]}] {r.get('action','')} -> {r.get('result','')}" for r in rows) or "No recent activity."
SCHEMAS=[{"type":"function","function":{"name":"log_activity","description":"Record the completed autonomous/background activity and result.","parameters":{"type":"object","properties":{"thinking":{"type":"string"},"action":{"type":"string"},"action_input":{"type":"object"},"result":{"type":"string"}},"required":["action","result"]}}},{"type":"function","function":{"name":"activity_recent","description":"Read recent autonomous activity logs.","parameters":{"type":"object","properties":{"limit":{"type":"integer","default":5}}}}}]
DISPATCH={"log_activity":lambda a:log_activity(a.get("thinking",""),a.get("action","nothing"),a.get("action_input",{}),a.get("result","")),"activity_recent":lambda a:activity_recent(a.get("limit",5))}
