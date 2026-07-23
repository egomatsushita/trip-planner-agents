from langchain.chat_models import init_chat_model

from config import OPENAI_MODEL
from state import TripPlannerState, TripDetails


trip_details_parser = init_chat_model(model=OPENAI_MODEL).with_structured_output(TripDetails)

def trip_details_parser_node(state: TripPlannerState):
    """Extract structured trip details from the user's latest message."""
    last_message = state["messages"][-1].content
    trip_details = trip_details_parser.invoke(
        f"Extract structured trip details from this request:\n\n{last_message}"
    )
    return {"trip_details": trip_details.model_dump()}

