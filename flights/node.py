from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from config import PRIMARY_COLOR, SECONDARY_COLOR
from state import TripPlannerState


def make_flights_node(flights_agent: CompiledStateGraph):
    """Build a graph node that runs the flights agent and collects its structured flight options."""
    async def flights_node(state: TripPlannerState, config: RunnableConfig):
        status = config["configurable"].get("status")
        retry_attempts = state["retry_attempts"]
        new_retry_attempts = {"flight_search": retry_attempts["flight_search"] + 1}

        if status:
            status.update(f"[{PRIMARY_COLOR}]Searching for flights and hotels...")

        try:
            response = await flights_agent.ainvoke({"messages": state["messages"]})
            flight_options = [
                opt.model_dump()
                for opt in response["structured_response"].options
            ]
            if status:
                status.console.print(f"[{SECONDARY_COLOR}]✓ Flights found")
            return {"flight_options": flight_options, "retry_attempts": new_retry_attempts}
        except Exception:
            return {"flight_options": [], "retry_attempts": new_retry_attempts}
    return flights_node
