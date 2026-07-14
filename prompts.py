"""Shared prompt templates and response format definitions for all agents."""

FLIGHT_RESPONSE_FORMAT = """
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

---
### N) [Repeat for each additional option]
"""
