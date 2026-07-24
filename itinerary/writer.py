
from langchain_core.runnables import RunnableConfig

from config import PRIMARY_COLOR
from state import TripPlannerState


def _format_stops(stops: int) -> str:
    return "Nonstop" if stops == 0 else f"{stops} stop{'s' if stops != 1 else ''}"


def itinerary_writer_node(state: TripPlannerState, config: RunnableConfig):
    """Render the trip details, selected flight and hotel, and budget summary into a markdown itinerary."""
    status = config["configurable"].get("status")
    if status:
        status.update(f"[{PRIMARY_COLOR}]Writing your itinerary...")

    details = state["trip_details"]
    flight = state["draft_plan"]["flight"]
    hotel = state["draft_plan"]["hotel"]
    budget_decision = state["budget_decision"]
    currency = details.get("currency")

    if flight:
        flight_itinerary = (
            f"**Price:** {flight.get('currency')} {flight.get('price_total'):,.2f} total\n"
            "\n"
            f"- **Airline:** {flight.get('airline')}\n"
            f"- **Cabin:** {flight.get('cabin')}\n"
            f"- **Outbound:** {flight.get('departure_route')} at {flight.get('departure_time')} "
            f"| {_format_stops(flight.get('departure_stops'))}\n"
            f"- **Return:** {flight.get('return_route')} at {flight.get('return_time')} "
            f"| {_format_stops(flight.get('return_stops'))}\n"
        )
    else:
        flight_itinerary = "No flight options available."

    if hotel:
        highlights = "".join(f"    - {highlight}\n" for highlight in hotel.get("highlights", [])) if hotel else ""

        hotel_itinerary = (
            f"**Price:** {hotel.get('currency')} {hotel.get('price_per_night'):,.2f} / night "
            f"· {hotel.get('price_per_stay'):,.2f} total\n"
            "\n"
            f"- **Hotel:** {hotel.get('name')}\n"
            f"- **Location:** {hotel.get('location')} ({hotel.get('distance')})\n"
            f"- **Stay:** {hotel.get('check_in')} – {hotel.get('check_out')}\n"
            f"- **Rating:** {hotel.get('review_rating')} / 10 ({hotel.get('review_count'):,} reviews) "
            f"· {hotel.get('hotel_rating')}-star\n"
            f"- **Highlights**\n"
            f"{highlights}"
        )
    else:
        hotel_itinerary = "No hotel options available."

    breakdown = budget_decision.get("breakdown") or {}
    total_cost = budget_decision.get("total_cost", 0.0)
    budget = details.get("budget")
    budget_tier = details.get("budget_tier")

    budget_itinerary = (
        f"**Tier:** {budget_tier.capitalize()}\n"
        f"**Total Cost:** {currency} {total_cost:,.2f}\n"
        "\n"
        f"- **Flight:** {currency} {breakdown.get('flight', 0.0):,.2f}\n"
        f"- **Hotel:** {currency} {breakdown.get('hotel', 0.0):,.2f}\n"
    )

    if budget:
        used_pct = (total_cost / budget) * 100
        budget_itinerary += f"- **Budget:** {currency} {budget:,.2f} ({used_pct:,.0f}% used)\n"

    if budget_decision.get("approved", True):
        closing = "Happy with this plan? Let me know if you'd like to adjust the dates, travelers, or budget."
    else:
        reasons = budget_decision.get("reasons") or []
        note = " ".join(reasons)
        if note:
            budget_itinerary += f"\n**Note:** {note}\n"
        closing = (
            "This is the closest option I could find within your budget constraints — "
            "want to raise your budget, or should I keep this plan as-is?"
        )

    return {
        "final_itinerary": (
            "## Your Itinerary\n"
            "\n"
            f"**Trip:** {details.get('origin')} → {details.get('destination')}\n"
            f"**Dates:** {details.get('start_date')} – {details.get('end_date')}\n"
            f"**Travelers:** {details.get('adults')}\n"
            "\n"
            "---\n"
            "\n"
            "### Selected Flight\n"
            f"{flight_itinerary}"
            "\n"
            "---\n"
            "\n"
            "### Selected Hotel\n"
            f"{hotel_itinerary}"
            "\n"
            "---\n"
            "\n"
            "### Budget\n"
            f"{budget_itinerary}"
            "\n"
            "---\n"
            "\n"
            f"{closing}\n"
        )
    }
