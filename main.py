import asyncio
import logging

from langchain.messages import HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.theme import Theme

from agents.flight_finder import create_travel_agent, create_kiwi_client
from agents.hotel_finder import create_hotel_agent, create_trivago_client
from agents.supervisor import create_supervisor, create_supervisor_config, Context
from config import SUPERVISOR_TIMEOUT, PRIMARY_COLOR, SECONDARY_COLOR
from validators import check_query

logger = logging.getLogger(__name__)

console = Console(theme=Theme({
    "markdown.h1": f"bold {PRIMARY_COLOR}",
    "markdown.h2": f"bold {PRIMARY_COLOR}",
    "markdown.h3": f"bold {SECONDARY_COLOR}",
}))


async def plan_trip():
    query = "My partner and I are flying from Toronto to Rio de Janeiro. We'd like prices in CAD."
    console.print(f"\n[{PRIMARY_COLOR}]Planning your trip...[/{PRIMARY_COLOR}]\n")

    try:
        kiwi_client = create_kiwi_client()
        travel_agent = await create_travel_agent(kiwi_client)
    except Exception as e:
        logger.error(f"Travel agent failed to initialize: {e}")
        print("Flight search is currently unavailable. Please try again later.")
        return

    try:
        trivago_client = create_trivago_client()
        hotel_agent = await create_hotel_agent(trivago_client)
    except Exception as e:
        logger.error(f"Hotel finder agent failed to initialize: {e}")
        print("Hotel search is currently unavailable. Please try again later.")
        return

    query_check_result = check_query(query)
    if query_check_result:
        print(query_check_result)
        return query_check_result

    supervisor = create_supervisor()

    try:
        with console.status("[dark_cyan]Gathering trip details...") as status:
            supervisor_config = create_supervisor_config(status=status)
            response = await asyncio.wait_for(
                supervisor.ainvoke(
                    {"messages": [HumanMessage(content=query)]},
                    config=supervisor_config,
                    context=Context(travel_agent=travel_agent, hotel_agent=hotel_agent),
                ),
                timeout=SUPERVISOR_TIMEOUT,
            )
    except asyncio.TimeoutError:
        logger.error(f"Supervisor timed out after {SUPERVISOR_TIMEOUT}s")
        print("Trip planning timed out. Please try again.")
        return
    console.print("\n")
    console.print(Markdown(response["messages"][-1].content))
    console.print("\n")


def main():
    asyncio.run(plan_trip())


if __name__ == "__main__":
    main()
