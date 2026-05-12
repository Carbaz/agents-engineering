"""Example of using MCPServerStdio to create a server process and list its tools."""

import asyncio

from agents.mcp import MCPServerStdio


async def main():
    """Async create a server process and list its tools."""
    fetch_params = {"command": "uvx", "args": ["mcp-server-fetch"]}

    async with MCPServerStdio(
        params=fetch_params, client_session_timeout_seconds=60) as server:
        fetch_tools = await server.list_tools()

    print(fetch_tools)

    playwright_params = {"command": "npx", "args": ["@playwright/mcp@latest"]}

    async with MCPServerStdio(
        params=playwright_params, client_session_timeout_seconds=60) as server:
        playwright_tools = await server.list_tools()

    print(playwright_tools)


if __name__ == "__main__":
    asyncio.run(main())
