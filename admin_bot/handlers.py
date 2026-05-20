from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

import config
import database as db
from userbot.responder import set_paused, is_paused

router = Router()


def _admin_only(message: Message) -> bool:
    return message.from_user.id == config.ADMIN_USER_ID


@router.message(Command("start"))
async def cmd_start(message: Message):
    if _admin_only(message):
        await message.answer(
            "Управление юзерботом:\n"
            "/addchannel @username или channel_id\n"
            "/removechannel @username или channel_id\n"
            "/channels — список каналов\n"
            "/settag @тег — тег обязательного ответа\n"
            "/setprobability 0.3 — вероятность ответа\n"
            "/setcooldown 45 — кулдаун в минутах\n"
            "/status — текущие настройки\n"
            "/pause — пауза\n"
            "/resume — возобновить"
        )
        return

    await message.answer(
        "Привет 👋\n\n"
        "📢 Подписывайся на канал — там полезный контент без воды:\n"
        "👉 @MikhailAkhk\n\n"
        "🔒 Нужен VPN? Попробуй <b>KairaVPN</b> — 30 дней бесплатно, потом всего 89 ₽/мес:\n"
        "👉 @KairaVPN_bot",
        parse_mode="HTML",
    )


@router.message(Command("addchannel"))
async def cmd_add_channel(message: Message):
    if not _admin_only(message):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /addchannel @channel или -1001234567890")
        return
    channel = args[1].strip()
    db.add_channel(channel, channel)
    await message.answer(f"Канал добавлен: {channel}")


@router.message(Command("removechannel"))
async def cmd_remove_channel(message: Message):
    if not _admin_only(message):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /removechannel @channel или -1001234567890")
        return
    channel = args[1].strip()
    db.remove_channel(channel)
    await message.answer(f"Канал отключён: {channel}")


@router.message(Command("channels"))
async def cmd_channels(message: Message):
    if not _admin_only(message):
        return
    channels = db.get_all_channels()
    if not channels:
        await message.answer("Нет добавленных каналов.")
        return
    lines = []
    for c in channels:
        status = "✅" if c["active"] else "❌"
        name = c["channel_name"] or c["channel_id"]
        lines.append(f"{status} {name} ({c['channel_id']})")
    await message.answer("\n".join(lines))


@router.message(Command("settag"))
async def cmd_set_tag(message: Message):
    if not _admin_only(message):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /settag @yourtag")
        return
    tag = args[1].strip()
    db.set_setting("target_tag", tag)
    await message.answer(f"Тег установлен: {tag}")


@router.message(Command("setprobability"))
async def cmd_set_prob(message: Message):
    if not _admin_only(message):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /setprobability 0.3")
        return
    try:
        prob = float(args[1].strip())
        assert 0.0 <= prob <= 1.0
    except (ValueError, AssertionError):
        await message.answer("Число от 0.0 до 1.0")
        return
    db.set_setting("response_probability", str(prob))
    await message.answer(f"Вероятность ответа: {prob:.0%}")


@router.message(Command("setcooldown"))
async def cmd_set_cooldown(message: Message):
    if not _admin_only(message):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /setcooldown 45")
        return
    try:
        minutes = int(args[1].strip())
        assert minutes > 0
    except (ValueError, AssertionError):
        await message.answer("Целое число больше 0")
        return
    db.set_setting("cooldown_minutes", str(minutes))
    await message.answer(f"Кулдаун: {minutes} мин")


@router.message(Command("status"))
async def cmd_status(message: Message):
    if not _admin_only(message):
        return
    tag = db.get_setting("target_tag", config.TARGET_TAG)
    prob = db.get_setting("response_probability", str(config.RESPONSE_PROBABILITY))
    cooldown = db.get_setting("cooldown_minutes", str(config.COOLDOWN_MINUTES))
    h_start = db.get_setting("active_hours_start", str(config.ACTIVE_HOURS_START))
    h_end = db.get_setting("active_hours_end", str(config.ACTIVE_HOURS_END))
    paused = "⏸ ПАУЗА" if is_paused() else "▶️ Активен"
    active_channels = len(db.get_active_channels())

    text = (
        f"Статус: {paused}\n"
        f"Каналов: {active_channels}\n"
        f"Тег: {tag or '—'}\n"
        f"Вероятность: {float(prob):.0%}\n"
        f"Кулдаун: {cooldown} мин\n"
        f"Часы: {h_start}:00 – {int(h_end) % 24:02d}:00 МСК"
    )
    await message.answer(text)


@router.message(Command("pause"))
async def cmd_pause(message: Message):
    if not _admin_only(message):
        return
    set_paused(True)
    await message.answer("Юзербот на паузе.")


@router.message(Command("resume"))
async def cmd_resume(message: Message):
    if not _admin_only(message):
        return
    set_paused(False)
    await message.answer("Юзербот возобновлён.")
