import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji
from telethon.errors import FloodWaitError, ReactionInvalidError

from config import API_ID, API_HASH, BOT_TOKEN, REACTION_EMOJI, CHAT_IDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("AutoReactionBot")

# Initialize the Telethon client with the bot token
client = TelegramClient("auto_reaction_session", API_ID, API_HASH)

# Simple in-memory rate limiter: max 1 reaction per second per chat
_last_reaction_time = {}


async def send_reaction(event, emoji: str):
    """
    Send a reaction to the message that triggered the event.
    Handles FloodWait and invalid reaction errors gracefully.
    """
    chat_id = event.chat_id
    message_id = event.message.id

    # Rate limit: avoid reacting too frequently in the same chat
    now = asyncio.get_event_loop().time()
    last = _last_reaction_time.get(chat_id, 0)
    if now - last < 1.0:
        logger.debug("Rate limit: skipping reaction in chat %s", chat_id)
        return
    _last_reaction_time[chat_id] = now

    try:
        await client(
            SendReactionRequest(
                peer=chat_id,
                msg_id=message_id,
                reaction=[ReactionEmoji(emoticon=emoji)],
                big=False,
            )
        )
        logger.info(
            "Reacted with %s to message %s in chat %s",
            emoji, message_id, chat_id,
        )
    except FloodWaitError as e:
        logger.warning(
            "FloodWait: need to wait %s seconds before retrying.", e.seconds
        )
        await asyncio.sleep(e.seconds)
    except ReactionInvalidError:
        logger.error(
            "Invalid reaction '%s' for message %s. "
            "Ensure the emoji is supported in this chat.",
            emoji, message_id,
        )
    except Exception as e:
        logger.exception("Unexpected error while sending reaction: %s", e)


@client.on(events.NewMessage(incoming=True))
async def handler(event):
    """
    Handle every incoming message.
    If CHAT_IDS is configured, only react in those chats.
    """
    # Filter by configured chat IDs (if any)
    if CHAT_IDS and event.chat_id not in CHAT_IDS:
        return

    # Ignore messages sent by the bot itself
    if event.out:
        return

    # Ignore service messages (e.g., user joined, pinned message)
    if event.message.action:
        return

    await send_reaction(event, REACTION_EMOJI)


async def main():
    """Start the bot and run until disconnected."""
    await client.start(bot_token=BOT_TOKEN)
    logger.info("Auto-Reaction Bot started. Listening for messages...")
    if CHAT_IDS:
        logger.info("Monitoring chats: %s", CHAT_IDS)
    else:
        logger.info("Monitoring ALL chats (no CHAT_IDS filter set).")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())