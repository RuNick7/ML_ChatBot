import asyncio
import random
import logging
import re
from datetime import datetime, timezone

import pytz
from telethon import TelegramClient
from telethon.tl.functions.messages import SetTypingRequest, SendReactionRequest
from telethon.tl.types import SendMessageTypingAction, ReactionEmoji

import config
import database as db
from gpt.client import get_reply

logger = logging.getLogger(__name__)
MSK = pytz.timezone("Europe/Moscow")

_paused = False

_REQUEST_PATTERNS = re.compile(
    r"(напиши|сделай|придумай|скажи|расскажи|объясни|помоги|дай|покажи|составь)",
    re.IGNORECASE,
)

# Русские буквы для опечаток: замены, которые выглядят как реальные
_TYPO_SWAPS = {
    "а": "о", "о": "а", "е": "и", "и": "е",
    "т": "ть", "н": "нн", "л": "лл",
    "ь": "", "ъ": "",
}


def set_paused(value: bool):
    global _paused
    _paused = value


def is_paused() -> bool:
    return _paused


def _post_hour_msk(event) -> int:
    post_time_utc = event.message.date
    if post_time_utc.tzinfo is None:
        post_time_utc = post_time_utc.replace(tzinfo=timezone.utc)
    return post_time_utc.astimezone(MSK).hour


def _is_dead_hour(hour: int) -> bool:
    return 4 <= hour < 7


def _is_request(text: str) -> bool:
    return bool(_REQUEST_PATTERNS.search(text))


def _inject_typos(text: str) -> str:
    """С шансом 5% вносим 1-2 глупые опечатки в текст ответа."""
    if random.random() > 0.05:
        return text
    words = text.split()
    if len(words) < 3:
        return text
    # Меняем одно случайное слово
    idx = random.randint(0, len(words) - 1)
    word = words[idx]
    if len(word) < 3:
        return text
    # Случайная замена буквы в середине слова
    pos = random.randint(1, len(word) - 2)
    char = word[pos].lower()
    if char in _TYPO_SWAPS:
        replacement = _TYPO_SWAPS[char]
        words[idx] = word[:pos] + replacement + word[pos + 1:]
    return " ".join(words)


async def _maybe_react_clown(client: TelegramClient, event):
    """С шансом 1% ставим реакцию 🤡 — только на посты, прошедшие все фильтры."""
    if random.random() > 0.01:
        return
    try:
        await client(SendReactionRequest(
            peer=event.chat_id,
            msg_id=event.message.id,
            reaction=[ReactionEmoji(emoticon="🤡")],
        ))
        logger.info("Reacted 🤡 to post %d", event.message.id)
    except Exception as exc:
        logger.debug("Reaction failed: %s", exc)


async def maybe_respond(client: TelegramClient, event, force_reply: bool = False):
    if _paused:
        return

    # Пропускаем посты с фото/медиа без текста
    text = event.message.text or ""
    if not text and event.message.photo:
        return
    if event.message.photo and len(text) < 20:
        return
    if len(text) < 20:
        return

    post_hour = _post_hour_msk(event)
    if _is_dead_hour(post_hour):
        return

    channel_id = str(event.chat_id)
    post_id = event.message.id

    target_tag = db.get_setting("target_tag", config.TARGET_TAG).lower()
    tag_mentioned = bool(target_tag and target_tag in text.lower())

    # force_reply = тегнули бота напрямую в комментарии
    if not force_reply and not tag_mentioned:
        cooldown = int(db.get_setting("cooldown_minutes", str(config.COOLDOWN_MINUTES)))
        if db.is_on_cooldown(channel_id, cooldown):
            return

        prob = float(db.get_setting("response_probability", str(config.RESPONSE_PROBABILITY)))
        if random.random() > prob:
            return

    # Мягкий фильтр на задания
    is_request = _is_request(text)
    resistance_mode = False
    if is_request and not tag_mentioned and not force_reply:
        if event.message.reply_to is None:
            resistance_mode = True
            logger.info("Resistance mode for post %d", post_id)

    # Реакцию ставим только на комментарии, не на посты канала
    if event.message.reply_to:
        asyncio.create_task(_maybe_react_clown(client, event))

    if post_hour >= 23 or post_hour < 7:
        delay = random.uniform(120, 600)
    else:
        delay = random.uniform(60, 300)

    logger.info("Waiting %.0fs before responding to post %d in %s", delay, post_id, channel_id)
    await asyncio.sleep(delay)

    try:
        thread_context = await _get_thread_context(client, event)
        reply_text = await get_reply(
            text,
            tag_mentioned=tag_mentioned or force_reply,
            thread_context=thread_context,
            resistance_mode=resistance_mode,
        )
        reply_text = _inject_typos(reply_text)
    except Exception as exc:
        logger.error("GPT error: %s", exc)
        return

    try:
        await client(SetTypingRequest(peer=event.chat_id, action=SendMessageTypingAction()))
        await asyncio.sleep(random.uniform(2, 5))
        await event.message.reply(reply_text)
        db.record_response(channel_id, post_id)
        logger.info("Replied to post %d in %s", post_id, channel_id)
    except Exception as exc:
        logger.error("Send error: %s", exc)


async def _get_thread_context(client: TelegramClient, event, limit: int = 5) -> list[str]:
    try:
        messages = await client.get_messages(
            event.chat_id,
            limit=limit,
            max_id=event.message.id,
        )
        return [m.text for m in reversed(messages) if m.text]
    except Exception:
        return []
