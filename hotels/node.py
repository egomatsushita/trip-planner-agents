import json
import logging
import re

from langchain.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from config import PRIMARY_COLOR, SECONDARY_COLOR
from state import TripPlannerState, HotelOption

logger = logging.getLogger(__name__)


def make_hotels_node(hotels_agent: CompiledStateGraph):
    """Build a graph node that runs the hotels agent and collects its structured hotel options."""
    async def hotels_node(state: TripPlannerState, config: RunnableConfig) -> dict:
        status = config["configurable"].get("status")
        retry_attempts = state["retry_attempts"]
        new_retry_attempts = {"hotel_search": retry_attempts["hotel_search"] + 1}

        if status:
            status.update(f"[{PRIMARY_COLOR}]Searching for flights and hotels...")

        try:
            response = await hotels_agent.ainvoke({"messages": state["messages"]})
            tool_messages = [m for m in response["messages"] if isinstance(m, ToolMessage)]
            raw_result = tool_messages[-1].content[0]
            parsed_hotel_options = parse_hotel_options(raw_result)
            hotel_options = [
                HotelOption(
                    check_in=option["arrival"],
                    check_out=option["departure"],
                    name=option["accommodation_name"],
                    currency=option["currency"],
                    price_per_night=parse_numeric_string(option["price_per_night"]),
                    price_per_stay=parse_numeric_string(option["price_per_stay"]),
                    hotel_rating=int(option["hotel_rating"]),
                    review_rating=float(option["review_rating"]),
                    review_count=parse_numeric_string(option["review_count"]),
                    highlights=option["top_amenities"].split(","),
                    accommodation_url=option["accommodation_url"],
                    distance=option["distance"],
                    main_image=option["main_image"],
                ).model_dump()
                for option in parsed_hotel_options
            ]
            if status:
                status.console.print(f"[{SECONDARY_COLOR}]✓ Hotels found")
            return {"hotel_options": hotel_options, "retry_attempts": new_retry_attempts}
        except Exception:
            logger.exception("Hotel search failed")
            return {"hotel_options": [], "retry_attempts": new_retry_attempts}
    return hotels_node


def parse_hotel_options(raw_result: dict) -> list[dict]:
    """Extract the hotel options list from a raw Trivago MCP tool result.

    The result text leads with a plain-text preamble aimed at an LLM reader, followed by a
    JSON object with `output` (a JSON-encoded hotel array) and `system_message` (ignored)
    keys. Returns an empty list if the result doesn't match this shape.
    """
    text = raw_result["text"]
    json_start = text.index("{")
    parsed = json.loads(text[json_start:])
    options = json.loads(parsed["output"])
    return options


def parse_numeric_string(value: str) -> float:
    """Strip currency symbols, then parse as a float, handling both
    thousands/decimal separator conventions (e.g. '13,778.00' and '13.778,00').
    """
    cleaned = "".join(c for c in value if c.isdigit() or c in ",.")
    cleaned = re.sub(r"[,.](?=\d{3}(?!\d))", "", cleaned)   # drop thousands separators
    cleaned = re.sub(r",(?=\d{2}(?!\d))", ".", cleaned)      # decimal comma -> decimal point
    return float(cleaned) if cleaned else 0.0