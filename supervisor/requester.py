from langchain_core.runnables import RunnableConfig

from config import SECONDARY_COLOR
from state import TripPlannerState


def requester_node(state: TripPlannerState, config: RunnableConfig):
    """Ask the user to correct or clarify their trip details, listing the validation errors."""
    status = config["configurable"].get("status")
    validation = state.get("trip_details_validation")
    reasons = "\n".join(f"- {reason}" for reason in validation["reasons"])

    if status:
        status.console.print(f"[{SECONDARY_COLOR}]⚠ Need a bit more info before I can search")

    return {"final_itinerary": f"A couple of things to sort out before I can search:\n\n{reasons}"}
