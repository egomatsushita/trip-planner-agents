
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from budget import budget_evaluator_node, budget_tier_downgrader_node
from flights import (
    create_flights_agent,
    create_kiwi_client,
    load_kiwi_tools,
    make_flights_node,
)
from hotels import (
    create_hotel_agent,
    create_trivago_client,
    load_trivago_tools,
    make_hotels_node,
)
from itinerary import itinerary_writer_node
from router import (
    GATHER_DETAILS,
    GIVE_ADVICE,
    GIVE_UP,
    HANDLE_FEEDBACK,
    PROCEED,
    REQUEST_DETAILS,
    DOWNGRADE_BUDGET_TIER,
    RETRY_FLIGHTS,
    RETRY_HOTELS,
    RECHECK_BUDGET,
    route_after_budget_evaluation,
    route_after_budget_tier_downgrade,
    route_after_feedback,
    route_after_trip_details_parsing,
    route_from_start_node,
)
from state import TripPlannerState
from supervisor import advisor_node, feedback_handler_node, trip_details_parser_node, requester_node

TRIP_DETAILS_PARSER = "trip_details_parser"
FLIGHTS_AGENT = "flights_agent"
HOTELS_AGENT = "hotels_agent"
BUDGET_EVALUATOR = "budget_evaluator"
BUDGET_TIER_DOWNGRADER = "budget_tier_downgrader"
ITINERARY_WRITER = "itinerary_writer"
FEEDBACK_HANDLER = "feedback_handler"
ADVISOR = "advisor"
REQUESTER = "requester"


async def create_worker_nodes():
    kiwi_client = create_kiwi_client()
    kiwi_tools = await load_kiwi_tools(kiwi_client)
    flights_agent = create_flights_agent(kiwi_tools)
    flights_node = make_flights_node(flights_agent)

    trivago_client = create_trivago_client()
    trivago_tools = await load_trivago_tools(trivago_client)
    hotels_agent = create_hotel_agent(trivago_tools)
    hotels_node = make_hotels_node(hotels_agent)

    return flights_node, hotels_node


async def create_graph():
    flights_node, hotels_node = await create_worker_nodes()
    memory = InMemorySaver()

    graph = (
        StateGraph(TripPlannerState)
        .add_node(TRIP_DETAILS_PARSER, trip_details_parser_node)
        .add_node(FLIGHTS_AGENT, flights_node)
        .add_node(HOTELS_AGENT, hotels_node)
        .add_node(BUDGET_EVALUATOR, budget_evaluator_node)
        .add_node(BUDGET_TIER_DOWNGRADER, budget_tier_downgrader_node)
        .add_node(ITINERARY_WRITER, itinerary_writer_node)
        .add_node(FEEDBACK_HANDLER, feedback_handler_node)
        .add_node(ADVISOR, advisor_node)
        .add_node(REQUESTER, requester_node)
        .add_conditional_edges(
            START,
            route_from_start_node,
            {
                GATHER_DETAILS: TRIP_DETAILS_PARSER, 
                HANDLE_FEEDBACK: FEEDBACK_HANDLER,
            }
        )
        .add_conditional_edges(
            TRIP_DETAILS_PARSER,
            route_after_trip_details_parsing,
            {
                REQUEST_DETAILS: REQUESTER,
                RETRY_FLIGHTS: FLIGHTS_AGENT,
                RETRY_HOTELS: HOTELS_AGENT,
            }
        )
        .add_conditional_edges(
            FEEDBACK_HANDLER,
            route_after_feedback,
            {
                GIVE_ADVICE: ADVISOR,
                PROCEED: ITINERARY_WRITER,
                RECHECK_BUDGET: BUDGET_EVALUATOR,
                RETRY_FLIGHTS: FLIGHTS_AGENT,
                RETRY_HOTELS: HOTELS_AGENT,
                REQUEST_DETAILS: REQUESTER,
            }
        )
        .add_edge(FLIGHTS_AGENT, BUDGET_EVALUATOR)
        .add_edge(HOTELS_AGENT, BUDGET_EVALUATOR)
        .add_conditional_edges(
            BUDGET_EVALUATOR,
            route_after_budget_evaluation,
            {
                PROCEED: ITINERARY_WRITER,
                RETRY_FLIGHTS: FLIGHTS_AGENT,
                RETRY_HOTELS: HOTELS_AGENT,
                DOWNGRADE_BUDGET_TIER: BUDGET_TIER_DOWNGRADER,
            }
        )
        .add_conditional_edges(
            BUDGET_TIER_DOWNGRADER,
            route_after_budget_tier_downgrade,
            {
                GIVE_UP: ITINERARY_WRITER,
                RECHECK_BUDGET: BUDGET_EVALUATOR,
            }
        )
        .add_edge(ITINERARY_WRITER, END)
        .add_edge(ADVISOR, END)
        .add_edge(REQUESTER, END)
        .compile(checkpointer=memory)
    )

    return graph
