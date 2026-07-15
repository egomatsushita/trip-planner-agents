import logging

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph

from config import OPENAI_MODEL, MCP_MAX_RETRIES, MCP_KIWI_URL
from middleware.retry import get_tools_with_retry
from middleware.mcp_middleware import fault_tolerant_mcp_interceptor
from prompts import FLIGHT_RESPONSE_FORMAT

logger = logging.getLogger(__name__)


def create_kiwi_client():
    """Create a fault-tolerant MCP client connected to the Kiwi flight search server."""
    kiwi_client = MultiServerMCPClient(
        {
            "flight_server": {
                "transport": "streamable_http",
                "url": MCP_KIWI_URL
            }
        },
        tool_interceptors=[fault_tolerant_mcp_interceptor()]
    )

    return kiwi_client


def create_flight_finder_prompt():
    """Create the system prompt for the flight finder travel agent."""
    return (
        "You are a travel agent. Search for round trip flights to the desired destination location.\n"
        "\n"
        "You are not allowed to ask any more follow up questions,\n"
        "you must find the best flight options based on the following criteria:\n"
        "- Price (lowest, economy class)\n"
        "- Duration (shortest)\n"
        "- Date (time of the year which you believe is best for a visit at this location)\n"
        "- Prefer direct flights with at most 1 stop\n"
        "\n"
        "You may need to make multiple searches to iteratively find the best options.\n"
        "You will be given no extra information, only the origin and destination.\n"
        "It is your job to think critically about the best options.\n"
        "If the MCP tools fails, returns malformed output, or does not give you usable flight results, try the tool again.\n"
        "Once you have found the best options, return your shortlist using the following format (no booking URLs):\n"
        "\n"
        f"{FLIGHT_RESPONSE_FORMAT}\n"
    )


async def create_travel_agent(kiwi_client: MultiServerMCPClient):
    """Create the travel agent, fetching flight search tools from the MCP server with retry on failure."""
    tools = await get_tools_with_retry("Kiwi", kiwi_client, MCP_MAX_RETRIES, logger)

    travel_agent: CompiledStateGraph = create_agent(
        model=OPENAI_MODEL,
        tools=tools,
        system_prompt=create_flight_finder_prompt(),
    )
    return travel_agent
