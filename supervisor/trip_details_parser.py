from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model

from config import OPENAI_MODEL, PRIMARY_COLOR, SECONDARY_COLOR
from state import TripPlannerState, TripDetails, TripRequest
from validators import validate_trip_details, OFF_TOPIC_MESSAGE


trip_details_parser = init_chat_model(model=OPENAI_MODEL).with_structured_output(TripRequest)


async def get_trip_details(message: str) -> TripDetails | None:
    trip_request: TripRequest = await trip_details_parser.ainvoke(message)
    trip_details = trip_request.trip_details
    if trip_details is not None:
        return trip_details
    return None


async def trip_details_parser_node(state: TripPlannerState, config: RunnableConfig):
    """Extract structured trip details from the user's latest message."""
    status = config["configurable"].get("status")
    last_message = state["messages"][-1].content

    if status:
        status.update(f"[{PRIMARY_COLOR}]Gathering trip details...")

    trip_details = await get_trip_details(f"Extract structured trip details from this request:\n\n{last_message}")
    if not trip_details:
        return {"trip_details_validation": {"status": "invalid", "reasons": [OFF_TOPIC_MESSAGE]}}

    errors = validate_trip_details(trip_details)
    if errors:
        return {"trip_details_validation": {"status": "invalid", "reasons": errors}}

    if status:
        status.console.print(
            f"[{SECONDARY_COLOR}]✓ Got it — {trip_details.origin} → {trip_details.destination}, "
            f"{trip_details.start_date} to {trip_details.end_date}, {trip_details.adults} traveler(s)"
        )

    return {"trip_details": trip_details.model_dump(), "trip_details_validation": None}

