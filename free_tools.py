"""Public tool registry.

The private deployment has additional personal tools. Public code keeps the complete registry
pattern and several useful generic implementations. Add a module with SCHEMAS + DISPATCH and
append it below. No secret diary implementation is registered here.
"""
from tools_memory import SCHEMAS as M_SCHEMAS,DISPATCH as M_DISPATCH
from tools_activity import SCHEMAS as A_SCHEMAS,DISPATCH as A_DISPATCH
from tools_reminder import SCHEMAS as R_SCHEMAS,DISPATCH as R_DISPATCH
from tools_mcp_example import SCHEMAS as X_SCHEMAS,DISPATCH as X_DISPATCH
TOOL_SCHEMAS=M_SCHEMAS+A_SCHEMAS+R_SCHEMAS+X_SCHEMAS
TOOL_DISPATCH={**M_DISPATCH,**A_DISPATCH,**R_DISPATCH,**X_DISPATCH}
