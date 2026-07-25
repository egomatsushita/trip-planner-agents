from langchain_core.runnables import RunnableConfig

from config import PRIMARY_COLOR, SECONDARY_COLOR
from state import TripPlannerState, BudgetTier, MAX_RETRY

budget_tier_to_attempt = {
    BudgetTier.COMFORTABLE: MAX_RETRY - 2,
    BudgetTier.BALANCED: MAX_RETRY - 1,
    BudgetTier.CHEAPEST: MAX_RETRY,
}

def budget_tier_downgrader_node(state: TripPlannerState, config: RunnableConfig):
    """Step the trip down to a cheaper budget tier when over budget, tracking the downgrade attempt count."""
    status = config["configurable"].get("status")
    if status:
        status.update(f"[{PRIMARY_COLOR}]Adjusting your plan to fit your budget...")

    trip_details = state["trip_details"]
    budget_tier = trip_details["budget_tier"]
    new_retry_attempts = {"budget_tier_downgrade": budget_tier_to_attempt[budget_tier]}

    if budget_tier == BudgetTier.CHEAPEST:
        if status:
            status.console.print(f"[{SECONDARY_COLOR}]✗ No cheaper tier available")
        return {"retry_attempts": new_retry_attempts}

    if budget_tier == BudgetTier.COMFORTABLE:
        new_budget_tier = BudgetTier.BALANCED
    elif budget_tier == BudgetTier.BALANCED:
        new_budget_tier = BudgetTier.CHEAPEST

    if status:
        status.console.print(f"[{SECONDARY_COLOR}]→ Trying {new_budget_tier.value} tier")

    new_trip_details = {**trip_details, "budget_tier": new_budget_tier.value}
    return {"trip_details": new_trip_details, "retry_attempts": new_retry_attempts}
