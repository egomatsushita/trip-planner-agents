from dataclasses import dataclass
from typing import Annotated

from langchain.agents import AgentState
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel


def merge_finished_tools(current: set[str], update: set[str]) -> set[str]:
    """Merge concurrent tool completions within the same step"""
    return current | update


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

