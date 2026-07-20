import asyncio
from datetime import date, timedelta
import logging

from langchain.agents import create_agent
from langchain.messages import HumanMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from agents.state import Context, TripDetails, TripPlannerState
from config import (
    HOTEL_AGENT_TIMEOUT,
    OPENAI_MODEL,
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    TRAVEL_AGENT_TIMEOUT,
)
from prompts import create_supervisor_prompt
from validators import check_adults, check_currency, check_dates, check_location

logger = logging.getLogger(__name__)

FLIGHT_DATE_FLEXIBILITY_DAYS = 15


async def _invoke_subagent(subagent_label: str, subagent: CompiledStateGraph, query: str, timeout: float) -> dict:
    """Invoke a subagent and return a dict with 'status' ('success' or 'error') and 'data' (message content or error string)."""
    try:
        response = await asyncio.wait_for(
            subagent.ainvoke({"messages": [HumanMessage(content=query)]}),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.error(f"{subagent_label} search timed out after {timeout}s")
        return {
            "status": "error",
            "data": f"{subagent_label} search timed out. Please try again."
        }

    if not response["messages"]:
        logger.error(f"{subagent_label} returned no messages.")
        return {
            "status": "error",
            "data": f"{subagent_label} returned no results. Please try again"
        }

    return {
        "status": "success",
        "data": response["messages"][-1].content
    }



@tool
async def search_flights(runtime: ToolRuntime) -> Command:
    """Invoke the travel agent to search for flights based on the current state."""
    travel_agent = runtime.context.travel_agent
    origin = runtime.state["trip_details"].origin
    destination = runtime.state["trip_details"].destination
    currency = runtime.state["trip_details"].currency
    adults = runtime.state["trip_details"].adults
    start_date = runtime.state["trip_details"].start_date
    end_date = runtime.state["trip_details"].end_date
    finished_tools = runtime.state["finished_tools"]
    window_start = (date.fromisoformat(start_date) - timedelta(days=FLIGHT_DATE_FLEXIBILITY_DAYS)).isoformat()
    window_end = (date.fromisoformat(end_date) + timedelta(days=FLIGHT_DATE_FLEXIBILITY_DAYS)).isoformat()
    query = (
        f"Find flights from {origin} to {destination} in {currency} for {adults} adults. "
        f"Preferred dates: departing {start_date}, returning {end_date}. "
        f"You may also search departure/return dates within {window_start} to {window_end} "
        "if a meaningfully cheaper option exists on shifted dates."
    )

    status = runtime.config["configurable"].get("status")
    if status:
        status.update(f"[{SECONDARY_COLOR}]Searching for flights from {origin} to {destination}...")

    logger.info(f"Travel agent invoked: {origin} -> {destination} ({currency}) - {adults} Adults")
    response = await _invoke_subagent("Travel", travel_agent, query, TRAVEL_AGENT_TIMEOUT)
    logger.info("Travel agent finished.")

    if status:
        if response["status"] == "success":
            status.console.print(f"[{SECONDARY_COLOR}]✓ Flights found")
        if response["status"] == "success" and len(finished_tools) == len(runtime.tools) - 1:
            status.update(f"[{PRIMARY_COLOR}]Putting it all together...")
        else:
            status.update(f"[{PRIMARY_COLOR}]Gathering trip details...")

    return Command(update={
        "finished_tools": finished_tools | {"search_flights"},
        "messages": [ToolMessage(content=response["data"], tool_call_id=runtime.tool_call_id)]
    })


@tool
async def search_hotels(runtime: ToolRuntime) -> Command:
    """Invoke the hotel agent to search for hotels based on the current state."""
    hotel_agent = runtime.context.hotel_agent
    destination = runtime.state["trip_details"].destination
    currency = runtime.state["trip_details"].currency
    adults = runtime.state["trip_details"].adults
    start_date = runtime.state["trip_details"].start_date
    end_date = runtime.state["trip_details"].end_date
    finished_tools = runtime.state["finished_tools"]
    nights = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days
    city = destination.split("(")[0].strip() or destination
    query = (
        f"Find hotels in {city} in {currency} for {adults} adults, "
        f"checking in {start_date} and checking out {end_date} ({nights} nights)."
    )

    status = runtime.config["configurable"].get("status")
    if status:
        status.update(f"[{SECONDARY_COLOR}]Searching for hotels in {city}...")

    logger.info(f"Hotel agent invoked: {city} ({currency}) - {adults} Adults")
    response = await _invoke_subagent("Hotel", hotel_agent, query, HOTEL_AGENT_TIMEOUT)
    logger.info("Hotel agent finished.")

    if status:
        if response["status"] == "success":
            status.console.print(f"[{SECONDARY_COLOR}]✓ Hotels found")
        if response["status"] == "success" and len(finished_tools) == len(runtime.tools) - 1:
            status.update(f"[{PRIMARY_COLOR}]Putting it all together...")
        else:
            status.update(f"[{PRIMARY_COLOR}]Gathering trip details...")

    return Command(update={
        "finished_tools": finished_tools | {"search_hotels"},
        "messages": [ToolMessage(content=response["data"], tool_call_id=runtime.tool_call_id)]
    })


@tool
def update_state(trip_details: TripDetails, runtime: ToolRuntime) -> str:
    """Update the state when you know all of the values: origin, destination, and travel dates.
    origin and destination must follow the format 'City (XXX)' where XXX is the
    three-letter IATA airport code, e.g. 'Toronto (YYZ)', 'Paris (CDG)'.
    start_date and end_date are the departure and return dates, in 'YYYY-MM-DD' format.
    This tool must be called alone, without any other tool calls.
    It must complete and return to make the information available to other tools.
    """
    check_results = [
        check_location("Origin", trip_details.origin),
        check_location("Destination", trip_details.destination),
        check_adults(trip_details.adults),
        check_currency(trip_details.currency),
        check_dates(trip_details.start_date, trip_details.end_date),
    ]
    if any(check_results):
        failed_checks = [msg for msg in check_results if msg is not None]
        return Command(update={
            "messages": [
                ToolMessage(
                    content=f"Failed to update state. {' | '.join(failed_checks)}",
                    tool_call_id=runtime.tool_call_id
                )
            ]
        })

    logger.info(f"State updated: {trip_details.model_dump_json()}")
    return Command(update={
        "trip_details": trip_details,
        "finished_tools": set(["update_state"]),
        "messages": [ToolMessage(content="Successfully updated state.", tool_call_id=runtime.tool_call_id)]
    })


def create_supervisor_config(status=None):
    """Build the LangGraph config, injecting agents into the supervisor's runtime."""
    config = {
        "configurable": {"status": status},
        "tags": ["TP"],
        "recursion_limit": 20
    }
    return config


def create_supervisor():
    """Create the trip planner supervisor agent with flight and hotel search tools."""
    supervisor = create_agent(
        model=OPENAI_MODEL,
        tools=[search_flights, search_hotels, update_state],
        state_schema=TripPlannerState,
        context_schema=Context,
        system_prompt=create_supervisor_prompt(),
        checkpointer=InMemorySaver(),
    )
    return supervisor
