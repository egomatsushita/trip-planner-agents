from state import (
    TripPlannerState,
    MAX_RETRY,
    INTENT_NEW_SEARCH,
    INTENT_BUDGET_ADJUSTMENT,
    INTENT_ADVISORY_QUESTION,
    INTENT_FINALIZE,
)

REQUEST_DETAILS = "request_details"
GATHER_DETAILS = "gather_details"
HANDLE_FEEDBACK = "handle_feedback"
PROCEED = "proceed"
DOWNGRADE_BUDGET_TIER = "downgrade_budget_tier"
GIVE_UP = "give_up"
GIVE_ADVICE = "give_advice"
RECHECK_BUDGET = "recheck_budget"
RETRY_FLIGHTS = "retry_flights"
RETRY_HOTELS = "retry_hotels"

def route_from_start_node(state: TripPlannerState):
    """Route to the trip details parser if trip details haven't been captured yet, 
    otherwise to the feedback handler."""
    if not state.get("trip_details"):
        return GATHER_DETAILS
    return HANDLE_FEEDBACK


def route_after_budget_evaluation(state: TripPlannerState):
    """Proceed if the plan fits the budget, retry a failed search, or downgrade the budget tier otherwise."""
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
    return DOWNGRADE_BUDGET_TIER


def route_after_budget_tier_downgrade(state: TripPlannerState):
    """Give up once the downgrade counter maxes out (no cheaper tier left),
    otherwise re-check the budget with the new tier."""
    if state["retry_attempts"]["budget_tier_downgrade"] == MAX_RETRY:
        return GIVE_UP
    return RECHECK_BUDGET


def route_after_feedback(state: TripPlannerState):
    """Ask for corrected details if the merged trip details are invalid, otherwise route based on the
    classified feedback intent: re-search, recheck budget, answer a question, or finalize."""
    validation = state.get("trip_details_validation")
    intent = state["feedback_intent"]

    if validation and validation["status"] == "invalid":
        return REQUEST_DETAILS
    if intent == INTENT_NEW_SEARCH:
        return [RETRY_FLIGHTS, RETRY_HOTELS]
    if intent == INTENT_BUDGET_ADJUSTMENT:
        return RECHECK_BUDGET
    if intent == INTENT_ADVISORY_QUESTION:
        return GIVE_ADVICE
    if intent == INTENT_FINALIZE:
        return PROCEED


def route_after_trip_details_parsing(state: TripPlannerState):
    """Ask for corrected details if the parsed trip details are invalid, otherwise proceed to search."""
    validation = state.get("trip_details_validation")
    if validation and validation["status"] == "invalid":
        return REQUEST_DETAILS
    return [RETRY_FLIGHTS, RETRY_HOTELS]
