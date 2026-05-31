import asyncio
import importlib
import sys
import types
from datetime import datetime, timezone


VALID_ENV = {
    "TG_API_ID": "123456",
    "TG_API_HASH": "hash",
    "TG_PHONE": "+79001234567",
    "BOT_TOKEN": "token",
    "OPENAI_API_KEY": "openai-key",
    "TARGET_TAG": "@Kairachat_bot",
    "RESPONSE_PROBABILITY": "0.30",
    "COOLDOWN_MINUTES": "45",
    "ACTIVE_HOURS_START": "9",
    "ACTIVE_HOURS_END": "25",
    "ADMIN_USER_ID": "42",
}


class FakeMessage:
    def __init__(
        self,
        text,
        *,
        message_id=99,
        photo=False,
        reply_to=None,
        date=None,
        entities=None,
    ):
        self.text = text
        self.id = message_id
        self.photo = photo
        self.reply_to = reply_to
        self.date = date or datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
        self.entities = entities or []
        self.replies = []

    async def reply(self, text):
        self.replies.append(text)


class FakeEvent:
    def __init__(self, text, *, chat_id=123, reply_to=None):
        self.chat_id = chat_id
        self.message = FakeMessage(text, reply_to=reply_to)


class FakeClient:
    def __init__(self):
        self.requests = []

    async def __call__(self, request):
        self.requests.append(type(request).__name__)


def _import_responder(monkeypatch):
    for key, value in VALID_ENV.items():
        monkeypatch.setenv(key, value)

    dotenv_module = types.ModuleType("dotenv")
    dotenv_module.load_dotenv = lambda: None
    sys.modules["dotenv"] = dotenv_module

    pytz_module = types.ModuleType("pytz")
    pytz_module.timezone = lambda _name: timezone.utc
    sys.modules["pytz"] = pytz_module

    telethon_module = types.ModuleType("telethon")
    telethon_module.TelegramClient = type("TelegramClient", (), {})
    sys.modules["telethon"] = telethon_module

    functions_messages = types.ModuleType("telethon.tl.functions.messages")
    functions_messages.SetTypingRequest = type("SetTypingRequest", (), {"__init__": lambda self, **kwargs: None})
    functions_messages.SendReactionRequest = type("SendReactionRequest", (), {"__init__": lambda self, **kwargs: None})
    sys.modules["telethon.tl.functions.messages"] = functions_messages

    tl_types = types.ModuleType("telethon.tl.types")
    tl_types.SendMessageTypingAction = type("SendMessageTypingAction", (), {})
    tl_types.ReactionEmoji = type("ReactionEmoji", (), {"__init__": lambda self, emoticon: None})
    tl_types.MessageEntityUrl = type("MessageEntityUrl", (), {})
    tl_types.MessageEntityTextUrl = type("MessageEntityTextUrl", (), {})
    sys.modules["telethon.tl.types"] = tl_types

    gpt_client_module = types.ModuleType("gpt.client")

    async def default_get_reply(*_args, **_kwargs):
        return "stub reply"

    gpt_client_module.get_reply = default_get_reply
    sys.modules["gpt.client"] = gpt_client_module

    for module_name in ("config", "gpt.client", "userbot.responder"):
        sys.modules.pop(module_name, None)

    sys.modules["gpt.client"] = gpt_client_module
    return importlib.import_module("userbot.responder")


def test_has_links_detects_plain_url(monkeypatch):
    responder = _import_responder(monkeypatch)
    event = FakeEvent("Это длинный пост с ссылкой https://example.com внутри")

    assert responder._has_links(event) is True


def test_maybe_respond_replies_when_tagged(monkeypatch):
    responder = _import_responder(monkeypatch)
    client = FakeClient()
    event = FakeEvent("Очень длинный пост с тегом @Kairachat_bot и нормальным текстом")
    captured = {}
    recorded = []

    async def fake_sleep(_seconds):
        return None

    async def fake_get_thread_context(_client, _event):
        return ["ctx"]

    async def fake_get_reply(post_text, **kwargs):
        captured["post_text"] = post_text
        captured.update(kwargs)
        return "generated reply"

    monkeypatch.setattr(responder.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(responder.random, "uniform", lambda _a, _b: 0)
    monkeypatch.setattr(responder, "_get_thread_context", fake_get_thread_context)
    monkeypatch.setattr(responder, "get_reply", fake_get_reply)
    monkeypatch.setattr(responder.db, "get_setting", lambda _key, default="": default)
    monkeypatch.setattr(responder.db, "record_response", lambda channel_id, post_id: recorded.append((channel_id, post_id)))

    asyncio.run(responder.maybe_respond(client, event))

    assert captured["tag_mentioned"] is True
    assert captured["thread_context"] == ["ctx"]
    assert event.message.replies == ["generated reply"]
    assert recorded == [("123", 99)]
    assert "SetTypingRequest" in client.requests


def test_maybe_respond_sets_resistance_mode_for_top_level_request(monkeypatch):
    responder = _import_responder(monkeypatch)
    client = FakeClient()
    event = FakeEvent("Напиши подробный разбор этой ситуации без ссылок и коротких фраз")
    captured = {}

    async def fake_sleep(_seconds):
        return None

    async def fake_get_thread_context(_client, _event):
        return []

    async def fake_get_reply(post_text, **kwargs):
        captured["post_text"] = post_text
        captured.update(kwargs)
        return "refusal"

    monkeypatch.setattr(responder.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(responder.random, "uniform", lambda _a, _b: 0)
    monkeypatch.setattr(responder.random, "random", lambda: 0.0)
    monkeypatch.setattr(responder, "_get_thread_context", fake_get_thread_context)
    monkeypatch.setattr(responder, "get_reply", fake_get_reply)
    monkeypatch.setattr(responder.db, "get_setting", lambda _key, default="": default)
    monkeypatch.setattr(responder.db, "is_on_cooldown", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(responder.db, "record_response", lambda *_args, **_kwargs: None)

    asyncio.run(responder.maybe_respond(client, event))

    assert captured["tag_mentioned"] is False
    assert captured["resistance_mode"] is True
