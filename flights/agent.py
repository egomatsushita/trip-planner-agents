import logging

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

from state import FlightSearchResponse
from config import OPENAI_MODEL, MCP_MAX_RETRIES, MCP_KIWI_URL
from middleware.retry import get_tools_with_retry
from middleware.mcp_middleware import fault_tolerant_mcp_interceptor

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
        "RETURN — a JSON object with options - `FlighSearchResponse` schema. And each option follow `FlightOption` schema.\n"
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
        "RULE — Flexible date parameters: When searching the flexible window, use only an explicit date range\n"
        "(e.g. departureDateFrom/departureDateTo for departure, and the equivalent for return) — do not also set\n"
        "a flex-days parameter (e.g. departureDateFlexDays). Combining an explicit date-range parameter with a\n"
        "flex-days parameter is invalid and will be rejected by the tool.\n"
        "\n"
        "You may need to make up to two searches: one for the preferred dates, and one for the flexible window\n"
        "if the request provides one — do not make additional searches beyond these for the same query.\n"
        "You will be given no extra information, only the origin, destination, and travel dates.\n"
        "It is your job to think critically about the best options.\n"
        "If the MCP tool fails transiently (timeout, network error, malformed or empty output), try that same\n"
        "call again. If the tool instead returns a validation or schema error, do not retry with the same\n"
        "parameters — the request itself was invalid; correct the parameters based on the error before calling\n"
        "the tool again.\n"
    )


async def load_kiwi_tools(kiwi_client: MultiServerMCPClient) -> list[BaseTool]:
    """Load the Kiwi client tools with retry on failure."""
    tools = await get_tools_with_retry("Kiwi", kiwi_client, MCP_MAX_RETRIES, logger)
    return tools



def create_flights_agent(tools: list[BaseTool]):
    """Create the travel agent."""
    travel_agent: CompiledStateGraph = create_agent(
        model=OPENAI_MODEL,
        tools=tools,
        system_prompt=create_flight_finder_prompt(),
        response_format=FlightSearchResponse,
    )
    return travel_agent
