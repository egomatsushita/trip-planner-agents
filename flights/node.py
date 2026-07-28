import asyncio
import logging

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from config import PRIMARY_COLOR, SECONDARY_COLOR, TRAVEL_AGENT_TIMEOUT
from state import TripPlannerState


logger = logging.getLogger(__name__)


def make_flights_node(flights_agent: CompiledStateGraph):
    """Build a graph node that runs the flights agent and collects its structured flight options."""
    async def flights_node(state: TripPlannerState, config: RunnableConfig):
        status = config["configurable"].get("status")
        retry_attempts = state["retry_attempts"]
        new_retry_attempts = {"flight_search": retry_attempts["flight_search"] + 1}

        if status:
            status.update(f"[{PRIMARY_COLOR}]Searching for flights and hotels...")

        try:
            response = await asyncio.wait_for(
                flights_agent.ainvoke({"messages": state["messages"]}),
                timeout=TRAVEL_AGENT_TIMEOUT
            )
            flight_options = [
                opt.model_dump()
                for opt in response["structured_response"].options
            ]
            if status:
                status.console.print(f"[{SECONDARY_COLOR}]✓ Flights found")
            return {"flight_options": flight_options, "retry_attempts": new_retry_attempts}
        except asyncio.TimeoutError:
            logger.exception(f"Flight search timed out after {TRAVEL_AGENT_TIMEOUT}s")
            return {"flight_options": [], "retry_attempts": new_retry_attempts}
        except Exception:
            logger.exception("Flight search failed.")
            return {"flight_options": [], "retry_attempts": new_retry_attempts}
    return flights_node
