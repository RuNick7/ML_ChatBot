import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    tg_api_id: int
    tg_api_hash: str
    tg_phone: str
    bot_token: str
    openai_api_key: str
    target_tag: str
    response_probability: float
    cooldown_minutes: int
    active_hours_start: int
    active_hours_end: int
    admin_user_id: int
    session_string: str
    session_name: str = "userbot_session"


def _read_required_str(name: str, errors: list[str]) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    errors.append(f"- {name}: field is required")
    return ""


def _read_int(
    name: str,
    errors: list[str],
    *,
    default: int | None = None,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        if default is not None:
            return default
        errors.append(f"- {name}: field is required")
        return 0

    try:
        value = int(raw)
    except ValueError:
        errors.append(f"- {name}: expected integer, got {raw!r}")
        return 0

    if min_value is not None and value < min_value:
        errors.append(f"- {name}: must be >= {min_value}")
    if max_value is not None and value > max_value:
        errors.append(f"- {name}: must be <= {max_value}")
    return value


def _read_float(
    name: str,
    errors: list[str],
    *,
    default: float,
    min_value: float,
    max_value: float,
) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default

    try:
        value = float(raw)
    except ValueError:
        errors.append(f"- {name}: expected float, got {raw!r}")
        return default

    if value < min_value or value > max_value:
        errors.append(f"- {name}: must be between {min_value} and {max_value}")
    return value


def _load_settings() -> Settings:
    errors: list[str] = []

    settings = Settings(
        tg_api_id=_read_int("TG_API_ID", errors, min_value=1),
        tg_api_hash=_read_required_str("TG_API_HASH", errors),
        tg_phone=_read_required_str("TG_PHONE", errors),
        bot_token=_read_required_str("BOT_TOKEN", errors),
        openai_api_key=_read_required_str("OPENAI_API_KEY", errors),
        target_tag=os.getenv("TARGET_TAG", "@Kairachat_bot").strip(),
        response_probability=_read_float(
            "RESPONSE_PROBABILITY",
            errors,
            default=0.30,
            min_value=0.0,
            max_value=1.0,
        ),
        cooldown_minutes=_read_int(
            "COOLDOWN_MINUTES",
            errors,
            default=45,
            min_value=1,
        ),
        active_hours_start=_read_int(
            "ACTIVE_HOURS_START",
            errors,
            default=9,
            min_value=0,
            max_value=23,
        ),
        active_hours_end=_read_int(
            "ACTIVE_HOURS_END",
            errors,
            default=25,
            min_value=1,
            max_value=25,
        ),
        admin_user_id=_read_int("ADMIN_USER_ID", errors, min_value=1),
        session_string=os.getenv("SESSION_STRING", ""),
    )

    if errors:
        message = (
            "Invalid configuration in environment variables or .env.\n"
            "Fix the following entries:\n"
            + "\n".join(errors)
        )
        raise RuntimeError(message)

    return settings


SETTINGS = _load_settings()

TG_API_ID = SETTINGS.tg_api_id
TG_API_HASH = SETTINGS.tg_api_hash
TG_PHONE = SETTINGS.tg_phone

BOT_TOKEN = SETTINGS.bot_token
OPENAI_API_KEY = SETTINGS.openai_api_key

TARGET_TAG = SETTINGS.target_tag
RESPONSE_PROBABILITY = SETTINGS.response_probability
COOLDOWN_MINUTES = SETTINGS.cooldown_minutes
ACTIVE_HOURS_START = SETTINGS.active_hours_start
ACTIVE_HOURS_END = SETTINGS.active_hours_end
ADMIN_USER_ID = SETTINGS.admin_user_id

SESSION_STRING = SETTINGS.session_string
SESSION_NAME = SETTINGS.session_name
