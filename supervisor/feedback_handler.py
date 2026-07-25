
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model

from config import OPENAI_MODEL, PRIMARY_COLOR
from state import BudgetTier, ClassifiedIntent, TripPlannerState, Intent, initialize_retry_attempts
from supervisor.trip_details_parser import trip_details_parser


intent_classifier = init_chat_model(model=OPENAI_MODEL).with_structured_output(ClassifiedIntent)


async def feedback_handler_node(state: TripPlannerState, config: RunnableConfig):
    """Classify the user's follow-up message into a feedback intent and merge any updated trip details."""
    status = config["configurable"].get("status")
    if status:
        status.update(f"[{PRIMARY_COLOR}]Reviewing your feedback...")

    last_message = state["messages"][-1].content
    classified = await intent_classifier.ainvoke(
        f"Classify what this follow-up trip-planning message wants:\n\n{last_message}"
    )
    intent = classified.intent.value

    result = {"feedback_intent": intent}

    if intent in {Intent.NEW_SEARCH, Intent.BUDGET_ADJUSTMENT}:
        current_trip_details = {**state['trip_details'], "budget_tier": BudgetTier.COMFORTABLE.value}
        updated_trip_details = await trip_details_parser.ainvoke(
            f"Current trip details:\n{current_trip_details}\n\n"
            f"Update them based on this follow-up message, keeping any field not mentioned unchanged:\n\n{last_message}"
        )
        result["trip_details"] = updated_trip_details.model_dump()
        result["retry_attempts"] = initialize_retry_attempts()

    return result
