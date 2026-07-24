from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model

from config import OPENAI_MODEL, PRIMARY_COLOR, SECONDARY_COLOR
from state import TripPlannerState, TripDetails


trip_details_parser = init_chat_model(model=OPENAI_MODEL).with_structured_output(TripDetails)

async def trip_details_parser_node(state: TripPlannerState, config: RunnableConfig):
    """Extract structured trip details from the user's latest message."""
    status = config["configurable"].get("status")
    last_message = state["messages"][-1].content
    if status:
        status.update(f"[{PRIMARY_COLOR}]Gathering trip details...")
    trip_details = await trip_details_parser.ainvoke(
        f"Extract structured trip details from this request:\n\n{last_message}"
    )
    if status:
        status.console.print(
            f"[{SECONDARY_COLOR}]✓ Got it — {trip_details.origin} → {trip_details.destination}, "
            f"{trip_details.start_date} to {trip_details.end_date}, {trip_details.adults} traveler(s)"
        )
    return {"trip_details": trip_details.model_dump()}

