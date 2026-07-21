from dataclasses import dataclass
from typing import Annotated

from langchain.agents import AgentState
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel


def merge_finished_tools(current: set[str], update: set[str]) -> set[str]:
    """Merge concurrent tool completions within the same step"""
    return current | update


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


class TripDetails(BaseModel):
    origin: str
    destination: str
    currency: str = "USD"
    adults: int = 1
    start_date: str
    end_date: str


class TripPlannerState(AgentState):
    trip_details: TripDetails
    finished_tools: Annotated[set[str], merge_finished_tools]
    flight_options: list[FlightOption]
    hotel_options: list[HotelOption]

