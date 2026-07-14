import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "WARNING"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
MCP_KIWI_URL = os.getenv("MCP_KIWI_URL")
TRAVEL_AGENT_TIMEOUT = float(os.getenv("TRAVEL_AGENT_TIMEOUT", "120.0"))
MCP_MAX_RETRIES = 3

for name, value in [("OPENAI_API_KEY", OPENAI_API_KEY), ("OPENAI_MODEL", OPENAI_MODEL), ("MCP_KIWI_URL", MCP_KIWI_URL)]:
    if not value:
        raise EnvironmentError(f"Required environment variable '{name}' is not set.")
