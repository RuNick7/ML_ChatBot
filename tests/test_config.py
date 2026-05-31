import importlib
import sys
import types

import pytest


ENV_KEYS = [
    "TG_API_ID",
    "TG_API_HASH",
    "TG_PHONE",
    "BOT_TOKEN",
    "OPENAI_API_KEY",
    "TARGET_TAG",
    "RESPONSE_PROBABILITY",
    "COOLDOWN_MINUTES",
    "ACTIVE_HOURS_START",
    "ACTIVE_HOURS_END",
    "ADMIN_USER_ID",
    "SESSION_STRING",
]

VALID_ENV = {
    "TG_API_ID": "123456",
    "TG_API_HASH": "hash",
    "TG_PHONE": "+79001234567",
    "BOT_TOKEN": "token",
    "OPENAI_API_KEY": "openai-key",
    "TARGET_TAG": "@ExampleBot",
    "RESPONSE_PROBABILITY": "0.75",
    "COOLDOWN_MINUTES": "15",
    "ACTIVE_HOURS_START": "9",
    "ACTIVE_HOURS_END": "23",
    "ADMIN_USER_ID": "42",
    "SESSION_STRING": "session",
}


def _reload_config(monkeypatch, overrides=None, remove=None):
    overrides = overrides or {}
    remove = set(remove or [])

    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    for key, value in VALID_ENV.items():
        if key not in remove:
            monkeypatch.setenv(key, overrides.get(key, value))

    dotenv_module = types.ModuleType("dotenv")
    dotenv_module.load_dotenv = lambda: None
    sys.modules["dotenv"] = dotenv_module
    sys.modules.pop("config", None)
    return importlib.import_module("config")


def test_config_loads_valid_environment(monkeypatch):
    config = _reload_config(monkeypatch, overrides={"ACTIVE_HOURS_END": "25"})

    assert config.TG_API_ID == 123456
    assert config.TARGET_TAG == "@ExampleBot"
    assert config.RESPONSE_PROBABILITY == 0.75
    assert config.ACTIVE_HOURS_END == 25
    assert config.SESSION_STRING == "session"


def test_config_reports_missing_required_values(monkeypatch):
    with pytest.raises(RuntimeError) as exc_info:
        _reload_config(monkeypatch, remove={"BOT_TOKEN", "ADMIN_USER_ID"})

    message = str(exc_info.value)
    assert "BOT_TOKEN" in message
    assert "ADMIN_USER_ID" in message
    assert "Fix the following entries" in message


def test_config_reports_invalid_ranges(monkeypatch):
    with pytest.raises(RuntimeError) as exc_info:
        _reload_config(
            monkeypatch,
            overrides={
                "RESPONSE_PROBABILITY": "1.5",
                "COOLDOWN_MINUTES": "0",
                "ACTIVE_HOURS_START": "24",
            },
        )

    message = str(exc_info.value)
    assert "RESPONSE_PROBABILITY" in message
    assert "COOLDOWN_MINUTES" in message
    assert "ACTIVE_HOURS_START" in message
