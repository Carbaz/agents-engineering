"""Windows + Jupyter fix for MCP server creation."""

import mcp
mcp.client.stdio._original_stdio_client = mcp.client.stdio.stdio_client
patched = lambda server, *_: mcp.client.stdio._original_stdio_client(server, None)  # noqa: E731
mcp.stdio_client = mcp.client.stdio.stdio_client = patched
