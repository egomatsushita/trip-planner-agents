from langchain_core.runnables import RunnableConfig

from config import PRIMARY_COLOR, SECONDARY_COLOR
from state import (
    TripPlannerState,
    BUDGET_TIER_CHEAPEST,
    BUDGET_TIER_BALANCED,
    BUDGET_TIER_COMFORTABLE,
    MAX_RETRY,
)

budget_tier_to_attempt = {
    BUDGET_TIER_COMFORTABLE: MAX_RETRY - 2,
    BUDGET_TIER_BALANCED: MAX_RETRY - 1,
    BUDGET_TIER_CHEAPEST: MAX_RETRY,
}

def budget_tier_downgrader_node(state: TripPlannerState, config: RunnableConfig):
    """Step the trip down to a cheaper budget tier when over budget, tracking the downgrade attempt count."""
    status = config["configurable"].get("status")
    if status:
        status.update(f"[{PRIMARY_COLOR}]Adjusting your plan to fit your budget...")

    trip_details = state["trip_details"]
    budget_tier = trip_details["budget_tier"]
    new_retry_attempts = {"budget_tier_downgrade": budget_tier_to_attempt[budget_tier]}

    if budget_tier == BUDGET_TIER_CHEAPEST:
        if status:
            status.console.print(f"[{SECONDARY_COLOR}]✗ No cheaper tier available")
        return {"retry_attempts": new_retry_attempts}

    if budget_tier == BUDGET_TIER_COMFORTABLE:
        new_budget_tier = BUDGET_TIER_BALANCED
    elif budget_tier == BUDGET_TIER_BALANCED:
        new_budget_tier = BUDGET_TIER_CHEAPEST

    if status:
        status.console.print(f"[{SECONDARY_COLOR}]→ Trying {new_budget_tier} tier")

    new_trip_details = {**trip_details, "budget_tier": new_budget_tier}
    return {"trip_details": new_trip_details, "retry_attempts": new_retry_attempts}
