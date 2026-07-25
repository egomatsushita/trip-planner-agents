from dataclasses import dataclass
from enum import Enum
from typing import Annotated, TypedDict

from langchain.agents import AgentState
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field


MAX_RETRY = 3


def merge_finished_tools(current: set[str], update: set[str]) -> set[str]:
    """Merge concurrent tool completions within the same step"""
    return current | update


def merge_retry_attempts(current: dict, update: dict) -> dict:
    """Merge concurrent retry attempts with the same step"""
    return {**current, **update}


class Intent(str, Enum):
    NEW_SEARCH = "new_search"
    BUDGET_ADJUSTMENT = "budget_adjustment"
    ADVISORY_QUESTION = "advisory_question"
    FINALIZE = "finalize"


class ClassifiedIntent(BaseModel):
    intent: Intent = Field(
        description=(
            f"{Intent.NEW_SEARCH.value}: user wants different flights/hotels/dates. "
            f"{Intent.BUDGET_ADJUSTMENT.value}: user wants a cheaper option. "
            f"{Intent.ADVISORY_QUESTION.value}: open-ended question about the destination "
            "(e.g. 'is it walkable'). "
            f"{Intent.FINALIZE.value}: user is happy, produce the final itinerary."
        )
    )


class FlightOption(BaseModel):
    """A single flight option in the shortlist."""
    label: str
    price_total: float
    currency: str
    departure_route: str
    departure_time: str
    departure_stops: int
    return_route: str
    return_time: str
    return_stops: int
    cabin: str
    airline: str
    booking_url: str


class FlightSearchResponse(BaseModel):
    """Structured shortlist of flight options found for the requested trip."""
    options: list[FlightOption]


class HotelOption(BaseModel):
    """A single hotel option in the shortlist."""
    label: str
    location: str
    check_in: str
    check_out: str
    name: str
    currency: str
    price_per_night: float
    price_per_stay: float
    hotel_rating: float
    review_rating: float
    review_count: int
    highlights: list[str]
    accommodation_url: str
    distance: str
    main_image: str


class HotelSearchResponse(BaseModel):
    """Structured shortlist of hotel optons found for the requested trip."""
    options: list[HotelOption]


@dataclass
class Context:
    travel_agent: CompiledStateGraph
    hotel_agent: CompiledStateGraph


class BudgetTier(str, Enum):
    CHEAPEST = "cheapest"
    BALANCED = "balanced"
    COMFORTABLE = "comfortable"


class TripDetails(BaseModel):
    origin: str = Field(description="Origin city with IATA code", examples=["Toronto (YYZ)"])
    destination: str = Field(description="Destination city with IATA code", examples=["Toronto (YYZ)"])
    currency: str = Field(description="The currency three letters code", default="USD")
    adults: int = Field(description="Number of adult travelers", default=1, gt=0)
    start_date: str = Field(description="ISO date", examples=["2026-09-14"])
    end_date: str = Field(description="ISO date", examples=["2026-09-14"])
    budget: float | None = Field(description="The total budget that limits the trip", gt=0)
    budget_tier: BudgetTier = Field(
        description=(
            "How aggressively to spend within the budget: 'cheapest' picks the lowest-price "
            "options regardless of comfort, 'balanced' favors the best price-to-quality tradeoff "
            "(fewer stops, better ratings), 'comfortable' spends up to the full budget for the "
            f"best cabin and amenities. Infer from the user's wording, default to '{BudgetTier.COMFORTABLE.value}'."
        ),
        default=BudgetTier.COMFORTABLE.value
    )


class DraftPlan(BaseModel):
    flight: FlightOption | None
    hotel: HotelOption | None


class BudgetBreakdown(BaseModel):
    flight: float
    hotel: float


class BudgetDecision(BaseModel):
    approved: bool
    total_cost: float
    over_budget_by: float
    over_budget_pct: float
    breakdown: BudgetBreakdown
    reasons: list[str]


class RetryAttempts(BaseModel):
    flight_search: int = Field(description="Number of times the flight search has been retried", default=0, le=MAX_RETRY)
    hotel_search: int = Field(description="Number of times the hotel search has been retried", default=0, le=MAX_RETRY)
    budget_tier_downgrade: int = Field(description="Number of times the budget tier has been downgraded", default=0, le=MAX_RETRY)


class RetryAttemptsDict(TypedDict):
    flight_search: int
    hotel_search: int
    budget_tier_downgrade: int


class TripPlannerState(AgentState):
    trip_details: TripDetails
    flight_options: list[FlightOption]
    hotel_options: list[HotelOption]
    draft_plan: DraftPlan
    budget_decision: BudgetDecision
    retry_attempts: Annotated[RetryAttemptsDict, merge_retry_attempts]
    final_itinerary: str
    feedback_intent: Intent | None


def initialize_retry_attempts():
    return RetryAttempts().model_dump()

def initialize_trip_planner_states():
    return {
        "flight_options": [],
        "hotel_options": [],
        "draft_plan": {},
        "budget_decision": {},
        "retry_attempts": initialize_retry_attempts(),
        "final_itinerary": "",
        "feedback_intent": None,
    }
