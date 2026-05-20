import logging
from telethon import events
from userbot.client import client
import userbot.client as ub_client
import database as db
from userbot.responder import maybe_respond

logger = logging.getLogger(__name__)


def _get_monitored_ids() -> set:
    channels = db.get_active_channels()
    result = set()
    for c in channels:
        try:
            result.add(int(c))
        except ValueError:
            result.add(c)
    return result


def _in_monitored(chat_id, monitored: set) -> bool:
    return chat_id in monitored or str(chat_id) in {str(m) for m in monitored}


def register_handlers():

    @client.on(events.NewMessage())
    async def on_channel_post(event):
        """Посты в каналах (не комментарии)."""
        if not event.is_channel:
            return
        # Пропускаем сообщения в группах-обсуждениях (они придут в on_comment)
        if event.message.reply_to:
            return

        monitored = _get_monitored_ids()
        if not _in_monitored(event.chat_id, monitored):
            return

        await maybe_respond(client, event)

    @client.on(events.NewMessage())
    async def on_comment(event):
        """
        Комментарии в обсуждениях каналов — обычные сообщения в linked group,
        у которых reply_to указывает на пост канала.
        Реагируем только если:
          1. Нас тегнули (@наш_username) — отвечаем всегда
          2. Это комментарий в обсуждении одного из мониторируемых каналов
        """
        if not event.message.reply_to:
            return

        text = event.message.text or ""

        # Проверяем тег бота в тексте комментария
        username = ub_client.bot_username
        bot_tagged = bool(
            username and f"@{username}".lower() in text.lower()
        )
        # Также проверяем mention entities (если написали через @упоминание)
        if not bot_tagged and ub_client.bot_id:
            for entity in (event.message.entities or []):
                from telethon.tl.types import MessageEntityMentionName
                if isinstance(entity, MessageEntityMentionName):
                    if entity.user_id == ub_client.bot_id:
                        bot_tagged = True
                        break

        if bot_tagged:
            # Тегнули нас напрямую — отвечаем всегда, без кулдауна
            await maybe_respond(client, event, force_reply=True)
            return

        # Если не тегнули — проверяем, в нашем ли это канале
        monitored = _get_monitored_ids()

        # reply_to_channel_id есть у комментариев к каналу
        reply_to = event.message.reply_to
        origin_channel = getattr(reply_to, "channel_id", None)

        if origin_channel and _in_monitored(origin_channel, monitored):
            await maybe_respond(client, event)
