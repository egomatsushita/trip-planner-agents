
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from budget import budget_enforcer_node, budget_reviser_node
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
    REVISE_BUDGET,
    RETRY_FLIGHTS,
    RETRY_HOTELS,
    RECHECK_BUDGET,
    route_after_budget_enforcer,
    route_after_budget_revision,
    route_after_feedback,
    route_from_start_node,
)
from state import TripPlannerState
from supervisor import advisor_node, feedback_handler_node, trip_details_parser_node

TRIP_DETAILS_PARSER = "trip_details_parser"
FLIGHTS_AGENT = "flights_agent"
HOTELS_AGENT = "hotels_agent"
BUDGET_ENFORCER = "budget_enforcer"
BUDGET_REVISER = "budget_reviser"
ITINERARY_WRITER = "itinerary_writer"
FEEDBACK_HANDLER = "feedback_handler"
ADVISOR = "advisor"

path_to_node = {
    GATHER_DETAILS: TRIP_DETAILS_PARSER, 
    GIVE_ADVICE: ADVISOR,
    GIVE_UP: ITINERARY_WRITER,
    HANDLE_FEEDBACK: FEEDBACK_HANDLER,
    PROCEED: ITINERARY_WRITER,
    RECHECK_BUDGET: BUDGET_ENFORCER,
    RETRY_FLIGHTS: FLIGHTS_AGENT,
    RETRY_HOTELS: HOTELS_AGENT,
    REVISE_BUDGET: BUDGET_REVISER,
}


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
        .add_node(BUDGET_ENFORCER, budget_enforcer_node)
        .add_node(BUDGET_REVISER, budget_reviser_node)
        .add_node(ITINERARY_WRITER, itinerary_writer_node)
        .add_node(FEEDBACK_HANDLER, feedback_handler_node)
        .add_node(ADVISOR, advisor_node)
        .add_conditional_edges(
            START,
            route_from_start_node,
            {k: path_to_node[k] for k in (GATHER_DETAILS, HANDLE_FEEDBACK)}
        )
        .add_edge(TRIP_DETAILS_PARSER, FLIGHTS_AGENT)
        .add_edge(TRIP_DETAILS_PARSER, HOTELS_AGENT)
        .add_conditional_edges(
            FEEDBACK_HANDLER,
            route_after_feedback,
            {k: path_to_node[k] for k in (RETRY_FLIGHTS, RETRY_HOTELS, RECHECK_BUDGET, GIVE_ADVICE, PROCEED)}
        )
        .add_edge(FLIGHTS_AGENT, BUDGET_ENFORCER)
        .add_edge(HOTELS_AGENT, BUDGET_ENFORCER)
        .add_conditional_edges(
            BUDGET_ENFORCER,
            route_after_budget_enforcer,
            {k: path_to_node[k] for k in (PROCEED, REVISE_BUDGET, RETRY_FLIGHTS, RETRY_HOTELS)}
        )
        .add_conditional_edges(
            BUDGET_REVISER,
            route_after_budget_revision,
            {k: path_to_node[k] for k in (GIVE_UP, RECHECK_BUDGET)}
        )
        .add_edge(ITINERARY_WRITER, END)
        .add_edge(ADVISOR, END)
        .compile(checkpointer=memory)
    )

    return graph
