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
        "- Search the preferred departure and return dates given in the request first\n"
        "- Link (booking URL)\n"
        "- Ranking: among results, rank nonstop flights above 1-stop flights, all else being equal\n"
        "\n"
        "RULE — Stopovers: Set the stopover filter to allow at most 1 stop in a single search call.\n"
        "This already includes any nonstop/direct options, so do not make a second call with a stricter\n"
        "(direct-only) or looser stopover filter just to compare — rank within the one result set instead.\n"
        "\n"
        "RULE — Flexible dates: If the request gives a flexible date window in addition to the preferred dates,\n"
        "you may also search shifted departure/return dates within that window.\n"
        "Only include a shifted-date option if it is meaningfully cheaper than the best option on the preferred dates.\n"
        "When you do, clearly label it as an alternative and call out the price difference and the date change\n"
        "using a bolded or italicized Note, e.g. **Note:** Shifting departure to [date] saves [CURRENCY] [X] versus the preferred dates.\n"
        "Never silently replace the preferred dates — always show the preferred-dates option too.\n"
        "\n"
        "You may need to make multiple searches to iteratively find the best options.\n"
        "You will be given no extra information, only the origin, destination, and travel dates.\n"
        "It is your job to think critically about the best options.\n"
        "If the MCP tools fails, returns malformed output, or does not give you usable flight results, try the tool again.\n"
        "Once you have found the best options, return your shortlist using the following format:\n"
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
