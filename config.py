import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
REACTION_EMOJI = os.getenv("REACTION_EMOJI", "❤️")

_chat_ids_raw = os.getenv("CHAT_IDS", "")
CHAT_IDS = [
    int(cid.strip())
    for cid in _chat_ids_raw.split(",")
    if cid.strip()
]

# Validate required credentials
if not API_ID or not API_HASH or not BOT_TOKEN:
    raise ValueError(
        "Missing required environment variables: "
        "API_ID, API_HASH, and BOT_TOKEN must be set."
    )