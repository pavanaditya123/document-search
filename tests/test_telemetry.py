from app.telemetry import configure_logfire


def test_starts_without_a_logfire_token(monkeypatch):
    # The scheduled eval job crashed here: logfire refused to configure
    # when no token was set. Tracing must be optional.
    monkeypatch.delenv("LOGFIRE_TOKEN", raising=False)
    assert configure_logfire(service_name="test") is False


def test_empty_token_counts_as_missing(monkeypatch):
    monkeypatch.setenv("LOGFIRE_TOKEN", "")
    assert configure_logfire(service_name="test") is False
