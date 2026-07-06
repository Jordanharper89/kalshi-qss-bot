from qseries_v2.oracle_intelligence.live_relationship_monitor import LiveRelationshipMonitor


class FakeRelationshipEngine:
    def correlation_snapshot(self, live_markets=None):
        return {
            "status": "ok",
            "market_correlations": {
                "pair_count": 2,
                "pairs": [
                    {
                        "market_a": "BTC",
                        "market_b": "ETH",
                        "correlation": 0.92,
                        "relationship": "strong_positive",
                    },
                    {
                        "market_a": "BTC",
                        "market_b": "GOLD",
                        "correlation": -0.70,
                        "relationship": "negative",
                    },
                ],
            },
            "lead_lag": {
                "relationships": [
                    {
                        "leader": "BTC",
                        "follower": "ETH",
                        "lag_buckets": 3,
                        "correlation": 0.88,
                    }
                ]
            },
            "influence_scores": {
                "BTC": {"ticker": "BTC", "score": 82.0, "label": "high"},
                "ETH": {"ticker": "ETH", "score": 55.0, "label": "moderate"},
            },
            "live_context": {"status": "ok"},
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_038_live_relationship_monitor():
    monitor = LiveRelationshipMonitor(relationship_engine=FakeRelationshipEngine())

    diagnostics = monitor.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["relationship_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_markets = [
        {"ticker": "BTC", "price_change": 5.0, "volume_change": 120.0},
        {"ticker": "ETH", "price_change": -0.5, "volume_change": 15.0},
        {"ticker": "GOLD", "price_change": 2.0, "volume_change": 20.0},
    ]

    packet = monitor.monitor(live_markets)

    assert packet["status"] == "ok"
    assert packet["live_markets_analyzed"] == 3
    assert packet["historical_relationships_found"] == 2
    assert packet["drift_alerts"]
    assert packet["delayed_followers"]
    assert packet["relationship_anomalies"]
    assert packet["monitor_summary"]["total_alerts"] > 0
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    alerts = monitor.relationship_alerts(live_markets)
    assert alerts["alerts"]["drift"]

    latest = monitor.latest()
    assert latest["status"] == "ok"

    print("[PASS] OI-038 Live Relationship Monitor")
    print({
        "summary": packet["monitor_summary"],
        "drift_count": len(packet["drift_alerts"]),
        "delayed_count": len(packet["delayed_followers"]),
        "anomaly_count": len(packet["relationship_anomalies"]),
    })


if __name__ == "__main__":
    test_oi_038_live_relationship_monitor()
