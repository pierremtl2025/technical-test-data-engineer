import pandas as pd
import pytest
from dagster import build_op_context
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import DateTime

from moovitamix_fastapi.classes_out import ListenHistoryOut, TracksOut, UsersOut
from pipelines.load import load_to_postgres


def dummy_create_engine(db_url):
    class DummyEngine:
        pass

    return DummyEngine()


calls = []


def fake_to_sql(_self, name, _engine, if_exists, index, dtype):
    calls.append(
        {
            "table": name,
            "if_exists": if_exists,
            "index": index,
            "dtype": dtype,
        }
    )


@pytest.fixture(autouse=True)
def patch_dependencies(monkeypatch):
    # patch create_engine in the load module so it does not connect to a real DB.
    monkeypatch.setattr("pipelines.load.create_engine", dummy_create_engine)
    # patch DataFrame.to_sql to record the arguments
    monkeypatch.setattr(pd.DataFrame, "to_sql", fake_to_sql)
    # clear the calls list before each test
    calls.clear()


def test_load_to_postgres():
    dummy_track = TracksOut.generate_fake()
    dummy_user = UsersOut.generate_fake()
    dummy_history = ListenHistoryOut.generate_fake()

    tracks = [dummy_track]
    users = [dummy_user]
    listen_history = [dummy_history]

    context = build_op_context()
    load_to_postgres(context, tracks, users, listen_history)

    assert len(calls) == 3
    expected_tables = {"tracks", "users", "listen_history"}
    actual_tables = {call["table"] for call in calls}
    assert actual_tables == expected_tables

    for call in calls:
        if call["table"] == "listen_history":
            # should have an 'items' entry
            assert "items" in call["dtype"]
            # and it should be a JSONB instance
            assert isinstance(call["dtype"]["items"], JSONB)
        if call["table"] in {"tracks", "users"}:
            for col in ("created_at", "updated_at"):
                assert isinstance(call["dtype"].get(col), DateTime)
