"""Input validation functions shared across all agents."""

from datetime import date

from state import TripDetails


ALLOWED_CURRENCIES = {"USD", "CAD", "EUR", "GBP", "JPY", "RUB", "BRL", "INR", "CNY"}
MAX_TRIP_NIGHTS = 90
MAX_QUERY_LENGTH = 300
MAX_LOCATION_LENGTH = 100

OFF_TOPIC_MESSAGE = (
    "This doesn't look like a trip planning request. Try something like: "
    "'Plan a trip from Toronto to Paris, Sept 14-19, 2 travelers.'"
)


def check_query(query: str) -> str | None:
    """Return an error message if the query exceeds the maximum allowed length, otherwise None."""
    if len(query) > MAX_QUERY_LENGTH:
        return f"Query must be at most {MAX_QUERY_LENGTH} characters."
    return None


def check_location(label: str, value: str) -> str | None:
    """Return an error message if the location value is missing, too long, or malformed, otherwise None."""
    if not value:
        return f"{label} is missing — which city did you mean?"
    if len(value) > MAX_LOCATION_LENGTH:
        return f"{label} must be at most {MAX_LOCATION_LENGTH} characters."
    if not value.isprintable():
        return f"{label} contains invalid characters."
    return None


def check_adults(adults: int) -> str | None:
    """Return an error message if the adult count is out of the allowed range, otherwise None."""
    if adults <= 0:
        return "Adults must be positive and greater than zero."
    if adults > 10:
        return "Maximum of 10 adults."
    return None


def check_currency(currency: str) -> str | None:
    """Return an error message if the currency is missing or not in the allowed list, otherwise None."""
    if not currency:
        return f"Currency is missing — which would you like? Supported: {', '.join(sorted(ALLOWED_CURRENCIES))}"
    if currency not in ALLOWED_CURRENCIES:
        return f"'{currency}' isn't a supported currency. Supported: {', '.join(sorted(ALLOWED_CURRENCIES))}"
    return None


def check_dates(start_date: str, end_date: str) -> str | None:
    """Return an error message if the travel dates are missing, malformed, out of order, or out of range, otherwise None."""
    if not start_date or not end_date:
        return "I'm missing your departure and/or return date — could you provide both?"
    try:
        start = date.fromisoformat(start_date)
    except ValueError:
        return f"I couldn't read the start date '{start_date}' — could you provide it as 'YYYY-MM-DD'?"
    try:
        end = date.fromisoformat(end_date)
    except ValueError:
        return f"I couldn't read the end date '{end_date}' — could you provide it as 'YYYY-MM-DD'?"

    if start < date.today():
        return "Start date cannot be in the past."
    if end <= start:
        return "End date must be after the start date."
    if (end - start).days > MAX_TRIP_NIGHTS:
        return f"Trip length must be at most {MAX_TRIP_NIGHTS} nights."
    return None


def validate_trip_details(trip_details: TripDetails) -> list[str] | None:
    """Run all field-level checks against the trip details, returning the failure messages, or None if valid."""
    check_results = [
        check_location("Origin", trip_details.origin),
        check_location("Destination", trip_details.destination),
        check_adults(trip_details.adults),
        check_currency(trip_details.currency),
        check_dates(trip_details.start_date, trip_details.end_date),
    ]
    if any(check_results):
        failed_checks = [msg for msg in check_results if msg is not None]
        return failed_checks

    return None
