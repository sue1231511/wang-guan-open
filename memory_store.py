"""Layered memory + semantic memory hooks."""
from __future__ import annotations
import os, uuid, logging, requests
from storage import get, insert, update
from app_config import MEM0_USER_ID

log=logging.getLogger(__name__)


def list_memories(layer: str = "", limit: int = 20) -> list:
    q=f"select=id,content,summary,memory_layer,importance,category,tags&order=importance.desc&limit={max(1,min(limit,100))}"
    if layer: q += f"&memory_layer=eq.{layer}"
    return get("memories", q)


def add_memory(content: str, layer: str = "current", importance: int = 3, summary: str = "", category: str = ""):
    body={"content":content,"memory_layer":layer,"importance":max(1,min(int(importance),5))}
    if summary: body["summary"]=summary
    if category: body["category"]=category
    return insert("memories",body)


def search_memory(query: str, limit: int = 5) -> list:
    safe="".join(c for c in query if c not in "&=?(),*")
    return get("memories", f"select=id,content,summary,memory_layer,importance,category,tags&or=(content.ilike.*{safe}*,summary.ilike.*{safe}*)&order=importance.desc&limit={max(1,min(limit,20))}")


class SemanticMemory:
    def __init__(self):
        self.client=None
        key=os.getenv("MEM0_API_KEY","").strip()
        if key:
            try:
                from mem0 import MemoryClient
                self.client=MemoryClient(api_key=key)
            except Exception as exc: log.warning("Mem0 disabled: %s",exc)
    def search(self,q,limit=3):
        if not self.client or not q.strip(): return []
        try:
            r=self.client.search(query=q,filters={"user_id":MEM0_USER_ID},limit=limit)
            return r.get("results",r) if isinstance(r,dict) else (r or [])
        except Exception: return []
    def add_turn(self,user_text,assistant_text):
        if not self.client or not user_text: return False
        try:
            self.client.add([{"role":"user","content":user_text},{"role":"assistant","content":assistant_text}],user_id=MEM0_USER_ID)
            return True
        except Exception: return False

semantic_memory=SemanticMemory()
