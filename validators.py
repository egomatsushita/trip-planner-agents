"""Input validation functions shared across all agents."""

import re
from datetime import date


ALLOWED_CURRENCIES = {"USD", "CAD", "EUR", "GBP", "JPY", "RUB", "BRL", "INR", "CNY"}
MAX_TRIP_NIGHTS = 90
MAX_QUERY_LENGTH = 300
MAX_LOCATION_LENGTH = 100
LOCATION_FORMAT = re.compile(r"^.+\s\([A-Z]{3}\)$")


def check_query(query: str) -> str | None:
    """Return an error message if the query exceeds the maximum allowed length, otherwise None."""
    if len(query) > MAX_QUERY_LENGTH:
        return f"Query must be at most {MAX_QUERY_LENGTH} characters."
    return None


def check_location(label: str, value: str) -> str | None:
    """Return an error message if the location value is too long or contains invalid characters, otherwise None."""
    if len(value) > MAX_LOCATION_LENGTH:
        return f"{label} must be at most {MAX_LOCATION_LENGTH} characters."
    if not value.isprintable():
        return f"{label} contains invalid characters."
    if not LOCATION_FORMAT.match(value):
        return f"{label} must follow the format 'City (XXX)', e.g. 'Toronto (YYZ)' - {value}"
    return None


def check_adults(adults: int) -> str | None:
    """Return an error message if the adult count is out of the allowed range, otherwise None."""
    if adults <= 0:
        return "Adults must be positive and greater than zero."
    if adults > 10:
        return "Maximum of 10 adults."
    return None


def check_currency(currency: str) -> str | None:
    """Return an error message if the currency is not in the allowed list, otherwise None."""
    if currency not in ALLOWED_CURRENCIES:
        return f"Unsupported currency: {currency}. Supported: {', '.join(sorted(ALLOWED_CURRENCIES))}"
    return None


def check_dates(start_date: str, end_date: str) -> str | None:
    """Return an error message if the travel dates are malformed, out of order, or out of range, otherwise None."""
    try:
        start = date.fromisoformat(start_date)
    except ValueError:
        return f"Start date must be in 'YYYY-MM-DD' format - {start_date}"
    try:
        end = date.fromisoformat(end_date)
    except ValueError:
        return f"End date must be in 'YYYY-MM-DD' format - {end_date}"

    if start < date.today():
        return "Start date cannot be in the past."
    if end <= start:
        return "End date must be after the start date."
    if (end - start).days > MAX_TRIP_NIGHTS:
        return f"Trip length must be at most {MAX_TRIP_NIGHTS} nights."
    return None
