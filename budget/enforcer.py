from state import TripPlannerState


def _get_flight_by_budget_tier(budget_tier: str, flights: list):
    if not flights:
        return None
    if budget_tier == "cheapest":
        return min(flights, key=lambda f: f["price_total"])
    if budget_tier == "comfortable":
        return max(flights, key=lambda f: f["price_total"])
    if budget_tier == "balanced":
        return sorted(flights, key=lambda f: f["price_total"])[len(flights) // 2]
    return None

def _get_hotel_by_budget_tier(budget_tier: str, hotels: list):
    if not hotels:
        return None
    if budget_tier == "cheapest":
        return min(hotels, key=lambda f: f["price_per_stay"])
    if budget_tier == "comfortable":
        return max(hotels, key=lambda f: f["price_per_stay"])
    if budget_tier == "balanced":
        return sorted(hotels, key=lambda f: f["price_per_stay"])[len(hotels) // 2]
    return None


def budget_enforcer_node(state: TripPlannerState):
    """Pick a flight and hotel option per the trip's budget tier and flag any overage against the budget."""
    trip_details = state["trip_details"]
    budget = trip_details.get("budget", float("inf"))
    budget_tier = trip_details["budget_tier"]
    flights = state.get("flight_options", [])
    hotels = state.get("hotel_options", [])
    flight = _get_flight_by_budget_tier(budget_tier, flights)
    hotel = _get_hotel_by_budget_tier(budget_tier, hotels)

    flight_cost = flight["price_total"] if flight else 0.0
    hotel_cost = hotel["price_per_stay"] if hotel else 0.0
    total_cost = flight_cost + hotel_cost
    over_budget_by = max(0.0, total_cost - budget)

    reasons = []
    if over_budget_by > 0:
        reasons.append(
            f"{budget_tier.capitalize()} available combination (${total_cost:,.2f}) exceeds budget "
            f"(${budget:,.2f}) by ${over_budget_by:,.2f}."
        )
    if flight is None:
        reasons.append("No flight options available.")
    if hotel is None:
        reasons.append("No hotel options available.")

    budget_decision = {
        "approved": over_budget_by == 0 and flight is not None and hotel is not None,
        "total_cost": total_cost,
        "over_budget_by": over_budget_by,
        "over_budget_pct": (over_budget_by / budget) if over_budget_by else 0.0,
        "breakdown": {"flight": flight_cost, "hotel": hotel_cost},
        "reasons": reasons,
    }

    return {
        "budget_decision": budget_decision,
        "draft_plan": {"flight": flight, "hotel": hotel}
    }
            