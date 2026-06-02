import pytest


@pytest.fixture(autouse=True)
def _no_backoff_sleep(monkeypatch):
    monkeypatch.setattr("mfr24.transport.time.sleep", lambda _seconds: None)
