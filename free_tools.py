"""Public tool aggregation layer.

Add your own tools_*.py modules and merge their SCHEMAS/DISPATCH here. The private
repository's personal tool implementations are intentionally not included.
"""
from tools_example import SCHEMAS as _EXAMPLE_SCHEMAS, DISPATCH as _EXAMPLE_DISPATCH

TOOL_SCHEMAS = list(_EXAMPLE_SCHEMAS)
TOOL_DISPATCH = {**_EXAMPLE_DISPATCH}
