from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model

from config import OPENAI_MODEL, PRIMARY_COLOR
from state import TripPlannerState

advisor = init_chat_model(model=OPENAI_MODEL)


async def advisor_node(state: TripPlannerState, config: RunnableConfig):
    """Answer an advisory question about the current plan and append the response to the itinerary."""
    status = config["configurable"].get("status")
    if status:
        status.update(f"[{PRIMARY_COLOR}]Looking into your question...")

    last_message = state["messages"][-1].content
    relevant_state = {
        "trip_details": state["trip_details"],
        "flight_options": state["flight_options"],
        "hotel_options": state["hotel_options"],
        "draft_plan": state["draft_plan"],
        "budget_decision": state["budget_decision"],
    }

    response = await advisor.ainvoke(
        f"Current trip planner state: {relevant_state}\n\n"
        "Answer user's question using the state values above if needed.\n\n"
        f"{last_message}"
    )

    final_itinerary = state["final_itinerary"]
    final_itinerary += "\n\n"
    final_itinerary += response.content

    return {"final_itinerary": final_itinerary}