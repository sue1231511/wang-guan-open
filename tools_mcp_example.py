"""Example external MCP tools. Configure URLs yourself; no private service endpoint is shipped."""
import os
from tools_base import mcp_call
WEATHER_MCP_URL=os.getenv("WEATHER_MCP_URL","")
SEARCH_MCP_URL=os.getenv("SEARCH_MCP_URL","")
def get_weather(city):return mcp_call(WEATHER_MCP_URL,"weather","get_weather",{"city":city})
def web_search(query):return mcp_call(SEARCH_MCP_URL,"search","search",{"query":query})
SCHEMAS=[{"type":"function","function":{"name":"get_weather","description":"Query weather through your configured MCP server.","parameters":{"type":"object","properties":{"city":{"type":"string"}},"required":["city"]}}},{"type":"function","function":{"name":"web_search","description":"Search the web through your configured MCP server.","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}}]
DISPATCH={"get_weather":lambda a:get_weather(a.get("city","")),"web_search":lambda a:web_search(a.get("query",""))}
