
from langgraph.graph import START, END, StateGraph

from budget import budget_enforcer_node
from flights import create_kiwi_client, load_kiwi_tools, create_flights_agent, make_flights_node
from hotels import create_hotel_agent, create_trivago_client, load_trivago_tools, make_hotels_node
from itinerary import itinerary_writer_node
from supervisor import trip_details_parser_node
from state import TripPlannerState


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

    graph = (
        StateGraph(TripPlannerState)
        .add_node("trip_details_parser", trip_details_parser_node)
        .add_node("flights_agent", flights_node)
        .add_node("hotels_agent", hotels_node)
        .add_node("budget_enforcer", budget_enforcer_node)
        .add_node("itinerary_writer", itinerary_writer_node)
        .add_edge(START, "trip_details_parser")
        .add_edge("trip_details_parser", "flights_agent")
        .add_edge("trip_details_parser", "hotels_agent")
        .add_edge("flights_agent", "budget_enforcer")
        .add_edge("hotels_agent", "budget_enforcer")
        .add_edge("budget_enforcer", "itinerary_writer")
        .add_edge("itinerary_writer", END)
        .compile()
    )

    return graph
