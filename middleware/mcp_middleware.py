
import logging

import asyncio
from mcp.shared.exceptions import McpError
from mcp.types import CallToolResult, TextContent

from config import MCP_MAX_RETRIES
from middleware.retry import calculate_backoff


logger = logging.getLogger(__name__)


RETRYABLE_MCP_CODES = {-32603}

def fault_tolerant_mcp_interceptor(max_retries: int = MCP_MAX_RETRIES):
    """Intercept MCP tool calls: retry transient failures, convert exceptions to error CallToolResults.

    - Retryable McpError codes (e.g.: -32603): retry with exponential backoff with jitter.
    - All other McpError codes: return error CallToolResult immediately.
    - Any other exception (fetch failed, network error, etc.): retry then return error CallToolResult.
    """
    async def interceptor(request, handler):
        last_error = None
        for attempt in range(max_retries):
            try:
                return await handler(request)
            except McpError as e:
                last_error = e
                logger.error(
                    f"[MCP interceptor] {type(e).__name__} on {request.name} "
                    f"(code {e.error.code}, attempt {attempt+1}/{max_retries}): {e}"
                )
                if e.error.code not in RETRYABLE_MCP_CODES:
                    text_content = f"Tool '{request.name}' failed (error code {e.error.code}). Please try again."
                    return CallToolResult(content=[TextContent(type="text", text=text_content)], isError=True)
            except Exception as e:
                last_error = e
                logger.error(
                    f"[MCP interceptor] {type(e).__name__} on {request.name} "
                    f"(attempt {attempt+1}/{max_retries}): {e}"
                )

            if attempt < max_retries - 1:
                await asyncio.sleep(calculate_backoff(attempt))

        logger.error(f"[MCP interceptor] all {max_retries} retries exhausted for {request.name}: {last_error}")
        text_content = f"Tool '{request.name}' failed after {max_retries} attempts. Please try again later."
        return CallToolResult(content=[TextContent(type="text", text=text_content)], isError=True)

    return interceptor