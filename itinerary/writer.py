
from state import TripPlannerState


def _format_stops(stops: int) -> str:
    return "Nonstop" if stops == 0 else f"{stops} stop{'s' if stops != 1 else ''}"


def itinerary_writer_node(state: TripPlannerState):
    """Render the trip details and selected flight and hotel into a markdown itinerary summary."""
    details = state["trip_details"]
    flight = state["draft_plan"]["flight"]
    hotel = state["draft_plan"]["hotel"]

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

    return {
        "final_itinerary": (
            "## Your Itinerary\n"
            "\n"
            f"**Trip:** {details.get('origin')} → {details.get('destination')}\n"
            f"**Dates:** {details.get('start_date')} – {details.get('end_date')}\n"
            f"**Travelers:** {details.get('adults')}\n"
            "\n"
            "### Selected Flight\n"
            f"{flight_itinerary}"
            "\n"
            "### Selected Hotel\n"
            f"{hotel_itinerary}"
        )
    }