"""Connection settings for TWS. Override any value via environment variables or a .env file."""
import os

from dotenv import load_dotenv

load_dotenv()

TWS_HOST = os.getenv("TWS_HOST", "127.0.0.1")
TWS_PORT = int(os.getenv("TWS_PORT", "7497"))  # 7497 = TWS paper, 7496 = TWS live
TWS_CLIENT_ID = int(os.getenv("TWS_CLIENT_ID", "1"))

# Safety guard: refuse to run against anything but a paper account unless explicitly disabled.
PAPER_ONLY = os.getenv("PAPER_ONLY", "1") == "1"
