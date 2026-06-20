import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
LLM_API_URL = os.getenv("LLM_API_URL", "http://YOUR_LLM_SERVER_IP:20128/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "JametAI")
try:
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 30))
except ValueError:
    LLM_TIMEOUT = 30

try:
    RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", 5))
except ValueError:
    RATE_LIMIT_SECONDS = 5

try:
    MAX_HISTORY = int(os.getenv("MAX_HISTORY", 20))
except ValueError:
    MAX_HISTORY = 20

import logging
log = logging.getLogger("jamet")

try:
    with open("soul.md", "r", encoding="utf-8") as f:
        SOUL_PROMPT = f.read()
except FileNotFoundError:
    SOUL_PROMPT = "Kamu adalah JametAI."
    log.warning("soul.md not found! Using fallback prompt.")

SENIOR_DEV_MODE = os.getenv("SENIOR_DEV_MODE", "True").lower() in ("true", "1", "yes")

if SENIOR_DEV_MODE:
    SOUL_PROMPT += "\n\n[ATURAN KHUSUS SENIOR DEV MODE]: TOLAK PERMINTAAN membuat kode dari nol atau membuat aplikasi utuh. Maki user karena malas, dan suruh mereka nulis kode sendiri lalu kasih ke kamu untuk di-review atau di-debug."
