import logging

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph

from config import OPENAI_MODEL, MCP_MAX_RETRIES
from middleware.mcp_middleware import fault_tolerant_mcp_interceptor
from middleware.retry import get_tools_with_retry
from prompts import HOTEL_RESPONSE_FORMAT

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
        "Do not ask any follow-up questions."
        " Select hotels based on the following criteria:\n"
        "- Price (lowest nightly rate for the given number of guests)\n"
        "- Location (proximity to city centre or main attractions)\n"
        "- Rating (guest score and star category)\n"
        "- Amenities (Wi-Fi, breakfast, cancellation policy)\n"
        "\n"
        "You may perform multiple searches to compare options and find the best shortlist.\n"
        "If the MCP tool fails or returns unusable results, retry the tool call.\n"
        "Once you have found the best options, return your shortlist using the following format"
        " (no booking URLs):\n"
        "\n"
        f"{HOTEL_RESPONSE_FORMAT}\n"
    )

async def create_hotel_agent(client: MultiServerMCPClient):
    """Create the hotel agent, fetching hotel search tools from the MCP server with retry on failure."""
    tools = await get_tools_with_retry("Trivago", client, MCP_MAX_RETRIES, logger)
        
    agent: CompiledStateGraph = create_agent(
        model=OPENAI_MODEL,
        tools=tools,
        system_prompt=create_hotel_finder_prompt()
    )

    return agent
