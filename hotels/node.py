import json

from langgraph.graph.state import CompiledStateGraph

from state import TripPlannerState, HotelOption


def make_hotels_node(hotels_agent: CompiledStateGraph):
    """Build a graph node that runs the hotels agent and collects its structured hotel options."""
    async def hotels_node(state: TripPlannerState):
        try:
            response = await hotels_agent.ainvoke({"messages": state["messages"]})
            options = response["messages"][-1].content
            hotel_options = [HotelOption(**h).model_dump() for h in json.loads(options)]
            return {"hotel_options": hotel_options}
        except Exception:
            return {"hotel_options": []}
    return hotels_node