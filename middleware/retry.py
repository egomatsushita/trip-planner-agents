import asyncio
import random

from langchain_mcp_adapters.client import MultiServerMCPClient

def calculate_backoff(attempt: int) -> float:
    """Calculate exponential backoff with jitter."""
    return 2 ** attempt + random.uniform(0, 1)


async def get_tools_with_retry(mcp_name: str, client: MultiServerMCPClient, max_retries: int, logger) -> list:
    """Fetch MCP tools with exponential backoff, raising RuntimeError after all retries are exhausted."""
    for attempt in range(max_retries):
        try:
            tools = await client.get_tools()
            logger.info(f"Fetched {len(tools)} tool(s) from {mcp_name} MCP server.")
            return tools
        except Exception as e:
            logger.error(f"Failed to fetch tools from {mcp_name} MCP server: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(calculate_backoff(attempt))

    raise RuntimeError(f"Could not connect to {mcp_name} MCP server. Check connectivity.")

        