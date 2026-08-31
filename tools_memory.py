from memory_store import search_memory,list_memories,add_memory

def memory_search(query,limit=5):
    rows=search_memory(query,limit)
    return "\n".join(f"- [{r.get('memory_layer')}|{r.get('importance')}] {r.get('content','')}" for r in rows) or "No matching memory."
def memory_list(memory_layer="",limit=10):
    rows=list_memories(memory_layer,limit)
    return "\n".join(f"- [{r.get('memory_layer')}|{r.get('importance')}] {r.get('content','')}" for r in rows) or "Memory is empty."
def memory_add(content,memory_layer="current",importance=3,summary="",category=""):
    if memory_layer not in ("memo","current"):return "Public autonomous tools may only write memo/current layers."
    add_memory(content,memory_layer,importance,summary,category);return "Memory saved."
SCHEMAS=[
{"type":"function","function":{"name":"memory_search","description":"Search the layered memory store.","parameters":{"type":"object","properties":{"query":{"type":"string"},"limit":{"type":"integer","default":5}},"required":["query"]}}},
{"type":"function","function":{"name":"memory_list","description":"List memories by optional layer.","parameters":{"type":"object","properties":{"memory_layer":{"type":"string","default":""},"limit":{"type":"integer","default":10}}}}},
{"type":"function","function":{"name":"memory_add","description":"Add a memo/current memory.","parameters":{"type":"object","properties":{"content":{"type":"string"},"memory_layer":{"type":"string","enum":["memo","current"],"default":"current"},"importance":{"type":"integer","default":3},"summary":{"type":"string"},"category":{"type":"string"}},"required":["content"]}}}]
DISPATCH={"memory_search":lambda a:memory_search(a.get("query",""),a.get("limit",5)),"memory_list":lambda a:memory_list(a.get("memory_layer",""),a.get("limit",10)),"memory_add":lambda a:memory_add(a.get("content",""),a.get("memory_layer","current"),a.get("importance",3),a.get("summary",""),a.get("category",""))}
