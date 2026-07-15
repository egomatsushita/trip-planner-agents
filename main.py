import asyncio
import logging

from langchain.messages import HumanMessage

from agents.flight_finder import create_travel_agent, create_kiwi_client
from agents.hotel_finder import create_hotel_agent, create_trivago_client
from agents.supervisor import create_supervisor, create_supervisor_config
from config import SUPERVISOR_TIMEOUT
from validators import check_query

logger = logging.getLogger(__name__)

async def plan_trip():
    query = "My partner and I are flying from Toronto to Paris. We'd like prices in CAD."

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

    supervisor_config = create_supervisor_config(dict(travel_agent=travel_agent, hotel_agent=hotel_agent))

    query_check_result = check_query(query)
    if query_check_result:
        print(query_check_result)
        return query_check_result

    supervisor = create_supervisor()
    try:
        response = await asyncio.wait_for(
            supervisor.ainvoke(
                {"messages": [HumanMessage(content=query)]},
                config=supervisor_config,
            ),
            timeout=SUPERVISOR_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error(f"Supervisor timed out after {SUPERVISOR_TIMEOUT}s")
        print("Trip planning timed out. Please try again.")
        return
    print("\n\n", response["messages"][-1].content, "\n\n")


def main():
    asyncio.run(plan_trip())


if __name__ == "__main__":
    main()
