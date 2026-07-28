import asyncio
import logging
from uuid import uuid4

from langchain.messages import HumanMessage
from rich.markdown import Markdown

from config import PRIMARY_COLOR, SECONDARY_COLOR, console
from graph import create_graph
from state import initialize_trip_planner_states
from validators import check_query

logger = logging.getLogger(__name__)


def print_welcome_message():
    """Print the assistant's intro and usage instructions."""
    console.print(
        f"\n[{PRIMARY_COLOR}]Hi! I'm your travel planner AI assistant.[/{PRIMARY_COLOR}]\n"
        "To start planning, tell me:\n"
        "   • where you're flying from and to\n"
        "   • how many travellers\n"
        "   • your departure and return dates\n"
        "   • the currency you'd like prices in (optional)\n"
        "\n[italic]Example: \"Plan a trip from Toronto to Paris, Sept 14-19 2026. "
        "Budget $3000 (comfortable) CAD, 2 travelers.\"[/italic]\n"
        f"\n[{SECONDARY_COLOR}]Type 'exit' or 'quit' at any time to end the chat.[/{SECONDARY_COLOR}]\n"
    )


async def plan_trip():
    """Run the interactive trip-planning chat loop until the user exits."""
    thread_id = uuid4()
    is_first_run = True

    with console.status(f"[{PRIMARY_COLOR}]Initializing travel planner AI assistant...[/{PRIMARY_COLOR}]\n"):
        trip_planner_states = initialize_trip_planner_states()
        graph = await create_graph()

    print_welcome_message()

    while True:
        query = console.input(f"\n[{PRIMARY_COLOR}]You: [/{PRIMARY_COLOR}] ")
        if query.strip().lower() in {"exit", "quit"}:
            break

        query_check_result = check_query(query)
        if query_check_result:
            logger.warning(query_check_result)
            return query_check_result

        console.print("\n")
        with console.status(f"\n[{PRIMARY_COLOR}]Processing your request...") as status:
            result = await graph.ainvoke(
                {
                    "messages": [HumanMessage(content=query)],
                    **(trip_planner_states if is_first_run else {})
                },
                config={"configurable": {"thread_id": thread_id, "status": status}, "tags": ["TP-2"]},
            )

            is_first_run = False

            console.print("\n")
            console.print(Markdown(result.get("final_itinerary")))
            console.print("\n")

def main():
    asyncio.run(plan_trip())


if __name__ == "__main__":
    main()
