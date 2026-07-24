from state import TripPlannerState, MAX_RETRY

GATHER_DETAILS = "gather_details"
HANDLE_FEEDBACK = "handle_feedback"
PROCEED = "proceed"
REVISE = "revise"
GIVE_UP = "give_up"
RECHECK_BUDGET = "recheck_budget"
RETRY_FLIGHTS = "retry_flights"
RETRY_HOTELS = "retry_hotels"

def route_from_start_node(state: TripPlannerState):
    """Route to the trip details parser if trip details haven't been captured yet, 
    otherwise to the feedback handler."""
    if not state.get("trip_details"):
        return GATHER_DETAILS
    return HANDLE_FEEDBACK


def route_after_budget_enforcer(state: TripPlannerState):
    """Proceed if the plan fits the budget, retry a failed search, or revise the budget tier otherwise."""
    budget_decision = state["budget_decision"]
    flight_options = state["flight_options"]
    hotel_options = state["hotel_options"]
    retry_attempts = state["retry_attempts"]

    if budget_decision["approved"]:
        return PROCEED
    if not flight_options and retry_attempts["flight_search"] < MAX_RETRY:
        return RETRY_FLIGHTS
    if not hotel_options and retry_attempts["hotel_search"] < MAX_RETRY:
        return RETRY_HOTELS
    return REVISE


def route_after_budget_revision(state: TripPlannerState):
    """Give up once the revision counter maxes out (no cheaper tier left),
    otherwise re-check the budget with the new tier."""
    if state["retry_attempts"]["revision"] == MAX_RETRY:
        return GIVE_UP
    return RECHECK_BUDGET
