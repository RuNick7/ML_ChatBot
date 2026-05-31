import database as db


def test_channel_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "bot.db"))
    db.init_db()

    db.add_channel("@alpha", "Alpha")
    db.add_channel("-100123", "Numeric")
    db.remove_channel("@alpha")

    assert db.get_active_channels() == ["-100123"]
    assert db.get_all_channels() == [
        {"channel_id": "@alpha", "channel_name": "Alpha", "active": 0},
        {"channel_id": "-100123", "channel_name": "Numeric", "active": 1},
    ]


def test_record_response_enables_cooldown(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "bot.db"))
    db.init_db()

    assert not db.is_on_cooldown("channel-1", cooldown_minutes=45)

    db.record_response("channel-1", 101)

    assert db.is_on_cooldown("channel-1", cooldown_minutes=45)
