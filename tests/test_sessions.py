import json

import pytest

from app import sessions


@pytest.fixture
def tmp_sessions_file(tmp_path, monkeypatch):
    path = tmp_path / "sessions_data.json"
    monkeypatch.setattr(sessions, "SESSIONS_FILE", str(path))
    return path


def test_create_then_get_roundtrips_fields(tmp_sessions_file):
    sessions.create_session("s1", user_query="how is my squat?", video_filename="squat.mp4")

    got = sessions.get_session("s1")

    assert got["session_id"] == "s1"
    assert got["user_query"] == "how is my squat?"
    assert got["video_filename"] == "squat.mp4"
    assert got["status"] == "pending"
    assert got["created_at"] == got["updated_at"]


def test_get_missing_returns_none(tmp_sessions_file):
    assert sessions.get_session("nope") is None


def test_update_merges_fields_and_bumps_updated_at(tmp_sessions_file):
    sessions.create_session("s1")
    original = sessions.get_session("s1")

    updated = sessions.update_session("s1", status="completed", response="looks good")

    assert updated["status"] == "completed"
    assert updated["response"] == "looks good"
    assert updated["updated_at"] >= original["updated_at"]
    assert updated["created_at"] == original["created_at"]


def test_update_missing_session_returns_none(tmp_sessions_file):
    assert sessions.update_session("ghost", status="x") is None


def test_list_sessions_is_newest_first_and_limited(tmp_sessions_file, monkeypatch):
    times = iter([
        "2026-01-01T00:00:00+00:00",
        "2026-01-02T00:00:00+00:00",
        "2026-01-03T00:00:00+00:00",
    ])

    class FakeDT:
        @staticmethod
        def now(tz=None):
            class _T:
                def isoformat(self_inner):
                    return next(times)
            return _T()

    monkeypatch.setattr(sessions, "datetime", FakeDT)

    sessions.create_session("oldest")
    sessions.create_session("middle")
    sessions.create_session("newest")

    listed = sessions.list_sessions(limit=2)

    assert [s["session_id"] for s in listed] == ["newest", "middle"]
    assert set(listed[0].keys()) == {
        "session_id", "exercise_label", "video_filename", "status", "created_at",
    }


def test_create_prunes_to_max_sessions(tmp_sessions_file, monkeypatch):
    monkeypatch.setattr(sessions, "MAX_SESSIONS", 3)

    counter = iter(range(100))

    class FakeDT:
        @staticmethod
        def now(tz=None):
            class _T:
                def isoformat(self_inner):
                    return f"2026-01-{next(counter):02d}T00:00:00+00:00"
            return _T()

    monkeypatch.setattr(sessions, "datetime", FakeDT)

    for sid in ["a", "b", "c", "d", "e"]:
        sessions.create_session(sid)

    with open(tmp_sessions_file) as f:
        data = json.load(f)

    assert set(data.keys()) == {"c", "d", "e"}
