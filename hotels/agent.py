import logging

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

from config import OPENAI_MODEL, MCP_MAX_RETRIES
from middleware.mcp_middleware import fault_tolerant_mcp_interceptor
from middleware.retry import get_tools_with_retry

logger = logging.getLogger(__name__)


def create_trivago_client():
    """Create a fault-tolerant MCP client connected to the Trivago hotel search server."""
    client = MultiServerMCPClient(
        {
            "mcp_trivago_search": {
                "url": "https://mcp.trivago.com/mcp",
                "transport": "streamable_http"
            }
        },
        tool_interceptors=[fault_tolerant_mcp_interceptor()]
    )

    return client

def create_hotel_finder_prompt():
    """Create the system prompt for the hotel finder agent."""
    return (
        "You are a hotel search specialist. Find the best hotel options at the destination.\n"
        "\n"
        "Do not ask any follow-up questions.\n"
        "Use the exact check-in and check-out dates given in the request to compute nightly and total price\n"
        "Select hotels based on the following criteria:\n"
        "- Price (lowest nightly rate for the given number of guests)\n"
        "- Rating (guest score and star category)\n"
        "- Location (proximity to city centre or main attractions)\n"
        "- Amenities (Wi-Fi, breakfast, cancellation policy)\n"
        "\n"
        "If the MCP tool fails or returns unusable results, retry the tool call once.\n"
        "RULE — Final response: Once the search tool call succeeds, respond with exactly the word "
        "'Done'. Do not repeat, reformat, or comment on the tool's output in your response — "
        "the raw tool result is read directly, your final message is discarded.\n"
        "NOTE - No markdown, no code fences, no commentary\n"
        "\n"
        "RULE — Search calls: Make at most one search call per distinct destination/dates/guests query.\n"
        "Do not repeat a search with the same input to double-check or refine results — reuse what the first "
        "successful call already returned.\n"
    )


async def load_trivago_tools(client: MultiServerMCPClient) -> list[BaseTool]:
    """Load the Trivago client tools with retry on failure."""
    tools = await get_tools_with_retry("Trivago", client, MCP_MAX_RETRIES, logger)
    return tools


def create_hotel_agent(tools: list[BaseTool]):
    """Create the hotel agent."""
    agent: CompiledStateGraph = create_agent(
        model=OPENAI_MODEL,
        tools=tools,
        system_prompt=create_hotel_finder_prompt(),
    )

    return agent
