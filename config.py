import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "WARNING"))
logging.getLogger("mcp.client.streamable_http").setLevel(logging.ERROR)

# Environmental Variables (Required)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
MCP_KIWI_URL = os.getenv("MCP_KIWI_URL")

for name, value in [("OPENAI_API_KEY", OPENAI_API_KEY), ("OPENAI_MODEL", OPENAI_MODEL), ("MCP_KIWI_URL", MCP_KIWI_URL)]:
    if not value:
        raise EnvironmentError(f"Required environment variable '{name}' is not set.")

# Environmental Variables (Optional)
TRAVEL_AGENT_TIMEOUT = float(os.getenv("TRAVEL_AGENT_TIMEOUT", "120.0"))
HOTEL_AGENT_TIMEOUT = float(os.getenv("HOTEL_AGENT_TIMEOUT", "120.0"))
SUPERVISOR_TIMEOUT = float(os.getenv("SUPERVISOR_TIMEOUT", "300.0"))
PRIMARY_COLOR = os.getenv("PRIMARY_COLOR", "dark_cyan")
SECONDARY_COLOR = os.getenv("SECONDARY_COLOR", "sea_green3")
MCP_MAX_RETRIES = 3
