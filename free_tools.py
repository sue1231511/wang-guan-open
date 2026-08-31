"""Tool aggregation layer.

The private repository's actual free-activity tools are intentionally omitted.
Add your own domain modules and aggregate their SCHEMAS/DISPATCH here.
"""

from tools_example import SCHEMAS as _EXAMPLE_SCHEMAS
from tools_example import DISPATCH as _EXAMPLE_DISPATCH

TOOL_SCHEMAS = [*_EXAMPLE_SCHEMAS]
TOOL_DISPATCH = {**_EXAMPLE_DISPATCH}
