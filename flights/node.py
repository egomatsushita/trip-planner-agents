from langgraph.graph.state import CompiledStateGraph

from state import TripPlannerState


def make_flights_node(flights_agent: CompiledStateGraph):
    """Build a graph node that runs the flights agent and collects its structured flight options."""
    async def flights_node(state: TripPlannerState):
        retry_attempts = state["retry_attempts"]
        new_retry_attempts = {"flight_search": retry_attempts["flight_search"] + 1}

        try:
            response = await flights_agent.ainvoke({"messages": state["messages"]})
            flight_options = [
                opt.model_dump()
                for opt in response["structured_response"].options
            ]
            return {"flight_options": flight_options, "retry_attempts": new_retry_attempts}
        except Exception:
            return {"flight_options": [], "retry_attempts": new_retry_attempts}
    return flights_node
