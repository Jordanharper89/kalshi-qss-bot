from qseries_v2.oracle_intelligence.rhythm_insight_bridge import RhythmInsightBridge


class FakeAnalyzer:
    def diagnostics(self):
        return {
            "status": "ok",
            "database_exists": True,
        }

    def analyze(self):
        return {
            "status": "ok",
            "rows_analyzed": 100,
            "category_patterns": {
                "crypto": {
                    "records": 60,
                    "top_hours": [{"hour": "14", "activity_score": 900}],
                    "volume": {"avg": 500},
                    "liquidity": {"avg": 2000},
                    "spread": {"avg": 3.5},
                    "price_volatility": 8.2,
                },
                "sports": {
                    "records": 40,
                    "top_hours": [{"hour": "19", "activity_score": 700}],
                    "volume": {"avg": 350},
                    "liquidity": {"avg": 1200},
                    "spread": {"avg": 4.1},
                    "price_volatility": 6.4,
                },
            },
        }

    def oracle_insights(self):
        return {
            "status": "ok",
            "rows_analyzed": 100,
            "best_activity_hours": [{"key": "14", "score": 900}],
            "strongest_liquidity_hours": [{"key": "15", "score": 2000}],
            "widest_spread_hours": [{"key": "3", "score": 7.5}],
            "highest_volume_hours": [{"key": "14", "score": 500}],
            "highest_volatility_hours": [{"key": "20", "score": 9.2}],
            "category_patterns": self.analyze()["category_patterns"],
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_022_rhythm_insight_bridge():
    bridge = RhythmInsightBridge(FakeAnalyzer())

    diagnostics = bridge.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["analyzer_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    packet = bridge.build_packet()
    assert packet["status"] == "ok"
    assert packet["rows_analyzed"] == 100
    assert packet["market_clock"]["best_activity_hours"]
    assert packet["liquidity_intelligence"]["top_hours"]
    assert packet["spread_intelligence"]["top_hours"]
    assert packet["volume_intelligence"]["top_hours"]
    assert packet["volatility_intelligence"]["top_hours"]
    assert packet["category_intelligence"]["count"] == 2
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    context = bridge.oracle_context()
    assert context["context_type"] == "market_rhythm"
    assert context["read_only"] is True
    assert context["execution_allowed"] is False
    assert context["summary"]

    print("[PASS] OI-022 Rhythm Insight Bridge")
    print({
        "rows_analyzed": packet["rows_analyzed"],
        "top_activity_hour": packet["market_clock"]["best_activity_hours"][0],
        "categories": [
            c["category"]
            for c in packet["category_intelligence"]["categories_ranked"]
        ],
    })


if __name__ == "__main__":
    test_oi_022_rhythm_insight_bridge()
