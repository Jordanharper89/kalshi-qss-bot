"""
Test ADP-012 Live Kalshi Market Ingestion without hitting Kalshi.

Validates:
- environment handling
- response parsing
- market normalization
- event bus emission
- diagnostics
"""

from qseries_v2.adapters.live_kalshi_market_ingestion import (
    LiveKalshiMarketIngestion,
    KalshiMarketIngestionError,
)


class FakeResponse:
    status_code = 200
    text = "ok"

    def json(self):
        return {
            "markets": [
                {
                    "ticker": "TEST-MARKET-001",
                    "event_ticker": "TEST-EVENT",
                    "market_type": "binary",
                    "title": "Test market title",
                    "subtitle": "Test subtitle",
                    "yes_bid": 44,
                    "yes_ask": 46,
                    "no_bid": 54,
                    "no_ask": 56,
                    "last_price": 45,
                    "volume": 123,
                    "open_interest": 456,
                    "liquidity": 789,
                    "status": "open",
                    "close_time": "2026-12-31T00:00:00Z",
                    "expiration_time": "2026-12-31T00:00:00Z",
                    "category": "Test",
                }
            ],
            "cursor": "next-cursor",
        }


class FakeAuthSession:
    class Config:
        base_url = "https://external-api.demo.kalshi.co/trade-api/v2"

    config = Config()

    def __init__(self):
        self.calls = []

    def request(self, method, path, params=None):
        self.calls.append((method, path, params))
        return FakeResponse()


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


def test_adp_012():
    auth = FakeAuthSession()
    bus = FakeEventBus()

    ingestion = LiveKalshiMarketIngestion(
        environment="demo",
        auth_session=auth,
        event_bus=bus,
    )

    diag = ingestion.diagnostics()
    assert diag["status"] == "ok"
    assert diag["has_auth_session"] is True
    assert diag["read_only"] is True

    snapshot = ingestion.fetch_open_markets(limit=1)

    assert snapshot["status"] == "ok"
    assert snapshot["count"] == 1
    assert snapshot["cursor"] == "next-cursor"
    assert snapshot["markets"][0]["ticker"] == "TEST-MARKET-001"
    assert snapshot["markets"][0]["yes_bid"] == 44
    assert snapshot["markets"][0]["raw"]["ticker"] == "TEST-MARKET-001"
    assert auth.calls[0][0] == "GET"
    assert auth.calls[0][1] == "/markets"
    assert auth.calls[0][2]["status"] == "open"
    assert len(bus.events) >= 1

    try:
        LiveKalshiMarketIngestion(environment="bad-env")
        raise AssertionError("bad environment should fail")
    except KalshiMarketIngestionError:
        pass

    print("[PASS] ADP-012 Live Kalshi Market Ingestion")
    print({
        "diagnostics": diag,
        "snapshot_status": snapshot["status"],
        "snapshot_count": snapshot["count"],
        "sample": snapshot["markets"][0]["ticker"],
    })


if __name__ == "__main__":
    test_adp_012()
