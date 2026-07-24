import json

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from config import PRIMARY_COLOR, SECONDARY_COLOR
from state import TripPlannerState, HotelOption


def make_hotels_node(hotels_agent: CompiledStateGraph):
    """Build a graph node that runs the hotels agent and collects its structured hotel options."""
    async def hotels_node(state: TripPlannerState, config: RunnableConfig) -> dict:
        status = config["configurable"].get("status")
        retry_attempts = state["retry_attempts"]
        new_retry_attempts = {"hotel_search": retry_attempts["hotel_search"] + 1,}

        if status:
            status.update(f"[{PRIMARY_COLOR}]Searching for flights and hotels...")

        try:
            response = await hotels_agent.ainvoke({"messages": state["messages"]})
            options = response["messages"][-1].content
            hotel_options = [HotelOption(**h).model_dump() for h in json.loads(options)]
            if status:
                status.console.print(f"[{SECONDARY_COLOR}]✓ Hotels found")
            return {"hotel_options": hotel_options, "retry_attempts": new_retry_attempts}
        except Exception:
            return {"hotel_options": [], "retry_attempts": new_retry_attempts}
    return hotels_node
