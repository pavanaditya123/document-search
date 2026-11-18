"""Logfire setup shared by the API, the ingestion CLI and the eval app.

Tracing is optional. With LOGFIRE_TOKEN set, spans go to Logfire. Without it
the app still starts and simply does not send telemetry. Before this, a
missing token crashed the API on startup (that is what broke the scheduled
eval job in CI).
"""

import os

import logfire


def configure_logfire(service_name: str | None = None) -> bool:
    """Configure Logfire. Returns True if traces will actually be sent."""
    token = os.getenv("LOGFIRE_TOKEN") or None
    logfire.configure(
        token=token,
        service_name=service_name,
        send_to_logfire="if-token-present",
    )
    return token is not None
