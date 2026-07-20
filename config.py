import logging
import os
import warnings

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

load_dotenv()

# Warnings
warnings.filterwarnings("ignore", message=".*Pydantic serializer warnings.*")

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

# Rich
console = Console(theme=Theme({
    "markdown.h1": f"bold {PRIMARY_COLOR}",
    "markdown.h2": f"bold {PRIMARY_COLOR}",
    "markdown.h3": f"bold {SECONDARY_COLOR}",
}))

# Logging
logging.basicConfig(
    level=os.getenv("LOGGING_LEVEL", "WARNING"),
    format="%(message)s",
    handlers=[RichHandler(console=console, show_path=False, markup=True)],
)
logging.getLogger("mcp.client.streamable_http").setLevel(logging.ERROR)
