"""Input validation functions shared across all agents."""

ALLOWED_CURRENCIES = {"USD", "CAD", "EUR", "GBP", "JPY", "RUB", "BRL", "INR", "CNY"}
MAX_QUERY_LENGTH = 300
MAX_LOCATION_LENGTH = 100


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
