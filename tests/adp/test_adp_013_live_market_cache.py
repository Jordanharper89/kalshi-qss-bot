"""
Test ADP-013 Live Market Cache without hitting Kalshi.
"""

from qseries_v2.adapters.live_market_cache import LiveKalshiMarketCache


class FakeIngestion:
    def __init__(self):
        self.call_count = 0

    def fetch_markets(self, status="open", limit=1000, cursor=None):
        self.call_count += 1

        if self.call_count == 1:
            return {
                "status": "ok",
                "cursor": None,
                "markets": [
                    {
                        "ticker": "SERIES-EVENT-001",
                        "event_ticker": "EVENT",
                        "series_ticker": "SERIES",
                        "category": "Test",
                        "title": "Market 1",
                        "yes_bid": 40,
                        "yes_ask": 42,
                        "status": "open",
                    },
                    {
                        "ticker": "SERIES-EVENT-002",
                        "event_ticker": "EVENT",
                        "series_ticker": "SERIES",
                        "category": "Test",
                        "title": "Market 2",
                        "yes_bid": 50,
                        "yes_ask": 52,
                        "status": "open",
                    },
                ],
            }

        return {
            "status": "ok",
            "cursor": None,
            "markets": [
                {
                    "ticker": "SERIES-EVENT-001",
                    "event_ticker": "EVENT",
                    "series_ticker": "SERIES",
                    "category": "Test",
                    "title": "Market 1",
                    "yes_bid": 41,
                    "yes_ask": 43,
                    "status": "open",
                },
                {
                    "ticker": "SERIES-EVENT-003",
                    "event_ticker": "EVENT2",
                    "series_ticker": "SERIES",
                    "category": "Other",
                    "title": "Market 3",
                    "yes_bid": 60,
                    "yes_ask": 62,
                    "status": "open",
                },
            ],
        }


class FakeEventBus:
    def __init__(self):
        self.events = []

    def publish(self, event_type, payload):
        self.events.append((event_type, payload))


def test_adp_013():
    ingestion = FakeIngestion()
    bus = FakeEventBus()
    cache = LiveKalshiMarketCache(ingestion=ingestion, event_bus=bus, refresh_interval_seconds=5)

    first = cache.refresh()
    assert first["status"] == "ok"
    assert first["count"] == 2
    assert first["added"] == 2
    assert cache.get_market("SERIES-EVENT-001")["yes_bid"] == 40
    assert len(cache.get_event("EVENT")) == 2
    assert len(cache.get_series("SERIES")) == 2
    assert len(cache.get_category("Test")) == 2

    second = cache.refresh()
    assert second["status"] == "ok"
    assert second["count"] == 2
    assert second["added"] == 1
    assert second["changed"] == 1
    assert second["removed"] == 1
    assert cache.get_market("SERIES-EVENT-001")["yes_bid"] == 41
    assert cache.get_market("SERIES-EVENT-002") is None

    stats = cache.statistics()
    assert stats["market_count"] == 2
    assert stats["refresh_count"] == 2
    assert stats["read_only"] is True
    assert len(bus.events) >= 2

    print("[PASS] ADP-013 Live Market Cache & Synchronization Engine")
    print(stats)


if __name__ == "__main__":
    test_adp_013()
