"""Shared prompt templates and response format definitions for all agents."""

FLIGHT_RESPONSE_FORMAT = """
## Flights

### 1) [LABEL: e.g. Cheapest, Fastest, Best Value, Fewest Stops]
**Price:** [CURRENCY] [X,XXX.XX] total

**Departing Flight**
- **Route:** [ORIG] → [DEST] | [Nonstop or N stop(s)]
- **Time:** [Mon DD] at [HH:MM] → [Mon DD] at [HH:MM] | [Xh Ym]
- **Cabin:** [Economy / Business / First]
- **Airline:** [FULL AIRLINE NAME: e.g. Air Transat, Air Canada, TAP Portugal]

**Returning Flight**
- **Route:** [DEST] → [ORIG] | [Nonstop or N stop(s)]
- **Time:** [Mon DD] at [HH:MM] → [Mon DD] at [HH:MM] | [Xh Ym]
- **Cabin:** [Economy / Business / First]
- **Airline:** [FULL AIRLINE NAME: e.g. Air Transat, Air Canada, TAP Portugal]

**Link:** [BOOKING URL: e.g. https://www.kiwi.com/booking/abcd1234]

--- [Repeat for each additional option]

### N) [Repeat for each additional option]
"""

HOTEL_RESPONSE_FORMAT = """
## Hotels

### 1) [LABEL: e.g. Best Value, Most Central, Top Rated, Budget Pick]
**Price:** [CURRENCY] [X,XXX.XX] / night · [X,XXX.XX] total ([N] nights)

**Hotel**
- **Name:** [FULL HOTEL NAME]
- **Location:** [NEIGHBORHOOD: e.g. Copacabana], [CITY: e.g. Rio de Janeiro]
- **Rating:** [X.X / 10] ([N,NNN reviews: e.g. 1,234 reviews]) · [N-star: e.g. 3-star]
- **Link:** [HOTEL URL: e.g. https://www.trivago.com/hotel/abcd1234]

**Highlights**
- [Standout amenity or feature]
- [Standout amenity or feature]
- [Standout amenity or feature]

--- [Repeat for each additional option]

### N) [Repeat for each additional option]
"""
