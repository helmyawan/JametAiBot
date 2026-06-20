import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
LLM_API_URL = os.getenv("LLM_API_URL", "http://YOUR_LLM_SERVER_IP:20128/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "JametAI")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 30))
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", 5))
MAX_HISTORY = int(os.getenv("MAX_HISTORY", 20))

import logging
log = logging.getLogger("jamet")

try:
    with open("soul.md", "r", encoding="utf-8") as f:
        SOUL_PROMPT = f.read()
except FileNotFoundError:
    SOUL_PROMPT = "Kamu adalah JametAI."
    log.warning("soul.md not found! Using fallback prompt.")
