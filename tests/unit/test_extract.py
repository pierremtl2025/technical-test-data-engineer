import pytest
import requests
from dagster import build_op_context

from moovitamix_fastapi.classes_out import ListenHistoryOut, TracksOut, UsersOut
from pipelines.extract import fetch_listen_history, fetch_tracks, fetch_users
from pipelines.helpers import API_BASE


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.mark.parametrize(
    "op_def, model, endpoint",
    [
        (fetch_tracks, TracksOut, "/tracks"),
        (fetch_users, UsersOut, "/users"),
        (fetch_listen_history, ListenHistoryOut, "/listen_history"),
    ],
)
def test_extract_ops(monkeypatch, op_def, model, endpoint):
    fake_record = model.generate_fake().model_dump()
    payload = {"items": [fake_record]}

    def fake_get(url, timeout=None, **kwargs):
        assert url == f"{API_BASE}{endpoint}"
        return DummyResponse(payload)

    monkeypatch.setattr(requests, "get", fake_get)
    context = build_op_context()
    results = op_def(context)
    assert isinstance(results, list)
    assert len(results) == 1
    assert isinstance(results[0], model)
