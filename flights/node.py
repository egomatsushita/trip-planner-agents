from langgraph.graph.state import CompiledStateGraph

from state import TripPlannerState


def make_flights_node(flights_agent: CompiledStateGraph):
    """Build a graph node that runs the flights agent and collects its structured flight options."""
    async def flights_node(state: TripPlannerState):
        try:
            response = await flights_agent.ainvoke({"messages": state["messages"]})
            flight_options = [
                opt.model_dump()
                for opt in response["structured_response"].options
            ]
            return {"flight_options": flight_options}
        except Exception:
            return {"flight_options": []}
    return flights_node