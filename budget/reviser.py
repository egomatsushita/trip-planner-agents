from state import TripPlannerState, BudgetTier, MAX_RETRY

budget_tier_to_attempt = {
    BudgetTier.COMFORTABLE: MAX_RETRY - 2,
    BudgetTier.BALANCED: MAX_RETRY - 1,
    BudgetTier.CHEAPEST: MAX_RETRY,
}

def budget_reviser_node(state: TripPlannerState):
    """Step the trip down to a cheaper budget tier when over budget, tracking the revision attempt count."""
    trip_details = state["trip_details"]
    budget_tier = trip_details["budget_tier"]
    new_retry_attempts = {"revision": budget_tier_to_attempt[budget_tier]}

    if budget_tier == BudgetTier.CHEAPEST:
        return {"retry_attempts": new_retry_attempts}

    if budget_tier == BudgetTier.COMFORTABLE:
        new_budget_tier = BudgetTier.BALANCED
    elif budget_tier == BudgetTier.BALANCED:
        new_budget_tier = BudgetTier.CHEAPEST

    new_trip_details = {**trip_details, "budget_tier": new_budget_tier}
    return {"trip_details": new_trip_details, "retry_attempts": new_retry_attempts}
