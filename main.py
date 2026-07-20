import asyncio
import logging
from uuid import uuid4

from langchain.messages import HumanMessage
from langgraph.types import Overwrite
from rich.markdown import Markdown

from agents.flight_finder import create_travel_agent, create_kiwi_client
from agents.hotel_finder import create_hotel_agent, create_trivago_client
from agents.supervisor import create_supervisor, create_supervisor_config, Context
from config import SUPERVISOR_TIMEOUT, PRIMARY_COLOR, SECONDARY_COLOR, console
from validators import check_query

logger = logging.getLogger(__name__)


def print_welcome_message():
    console.print(
        f"\n[{PRIMARY_COLOR}]Hi! I'm your travel planner AI assistant.[/{PRIMARY_COLOR}]\n"
        "To start planning, tell me:\n"
        "   • where you're flying from and to\n"
        "   • how many travellers\n"
        "   • your departure and return dates\n"
        "   • the currency you'd like prices in (optional)\n"
        f"\n[{SECONDARY_COLOR}]Type 'exit' or 'quit' at any time to end the chat.[/{SECONDARY_COLOR}]\n"
    )


async def plan_trip():
    token_usage = {}
    turn = 1
    thread_id = uuid4()

    with console.status(f"[{PRIMARY_COLOR}]Initializing travel planner AI assistant...[/{PRIMARY_COLOR}]\n") as status:
        try:
            kiwi_client = create_kiwi_client()
            travel_agent = await create_travel_agent(kiwi_client)
        except Exception as e:
            logger.error(f"Travel agent failed to initialize: {e}")
            logger.error("Flight search is currently unavailable. Please try again later.")
            return

        try:
            trivago_client = create_trivago_client()
            hotel_agent = await create_hotel_agent(trivago_client)
        except Exception as e:
            logger.error(f"Hotel finder agent failed to initialize: {e}")
            logger.error("Hotel search is currently unavailable. Please try again later.")
            return

    supervisor = create_supervisor()

    print_welcome_message()

    while True:
        query = console.input(f"\n[{PRIMARY_COLOR}]You: [/{PRIMARY_COLOR}] ")
        if query.strip().lower() in {"exit", "quit"}:
            break

        query_check_result = check_query(query)
        if query_check_result:
            logger.warning(query_check_result)
            return query_check_result

        try:
            console.print("\n")
            with console.status(f"[{PRIMARY_COLOR}]Gathering trip details...") as status:
                supervisor_config = create_supervisor_config(status=status)
                supervisor_config["configurable"].update({"thread_id": thread_id})
                await supervisor.aupdate_state(
                    supervisor_config,
                    {"finished_tools": Overwrite(set())}
                )
                response = await asyncio.wait_for(
                    supervisor.ainvoke(
                        {"messages": [HumanMessage(content=query)]},
                        config=supervisor_config,
                        context=Context(travel_agent=travel_agent, hotel_agent=hotel_agent),
                    ),
                    timeout=SUPERVISOR_TIMEOUT,
                )
                last_message = response["messages"][-1]

                console.print("\n")
                console.print(Markdown(last_message.content))
                console.print("\n")
                token_usage[str(turn)] = last_message.usage_metadata
                turn += 1

                logger.debug(token_usage)
        except asyncio.TimeoutError:
            logger.error(f"Supervisor timed out after {SUPERVISOR_TIMEOUT}s")
            console.print("Trip planning timed out. Please try again.")
            return


def main():
    asyncio.run(plan_trip())


if __name__ == "__main__":
    main()
