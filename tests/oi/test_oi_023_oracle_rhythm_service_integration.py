from qseries_v2.oracle_intelligence.oracle_rhythm_service import OracleRhythmService


class FakeAnalyzer:
    def __init__(self):
        self.analyze_calls = 0

    def diagnostics(self):
        return {
            "status": "ok",
            "database_exists": True,
        }

    def analyze(self):
        self.analyze_calls += 1
        return {
            "module": "OI-021 Market Rhythm Analyzer",
            "status": "ok",
            "rows_analyzed": 144,
            "hourly_activity": {
                "13": {"activity_score": 500},
                "14": {"activity_score": 900},
            },
            "category_patterns": {
                "crypto": {"records": 90},
                "sports": {"records": 54},
            },
            "read_only": True,
            "execution_allowed": False,
        }

    def get_snapshot(self):
        return self.analyze()

    def oracle_insights(self):
        return {
            "module": "oracle_market_rhythm_insights",
            "status": "ok",
            "rows_analyzed": 144,
            "best_activity_hours": [{"key": "14", "score": 900}],
            "strongest_liquidity_hours": [{"key": "14", "score": 3000}],
            "widest_spread_hours": [{"key": "3", "score": 8}],
            "highest_volume_hours": [{"key": "14", "score": 700}],
            "highest_volatility_hours": [{"key": "20", "score": 12}],
            "category_patterns": {
                "crypto": {
                    "records": 90,
                    "top_hours": [{"hour": "14", "activity_score": 900}],
                    "volume": {"avg": 700},
                    "liquidity": {"avg": 3000},
                    "spread": {"avg": 3},
                    "price_volatility": 12,
                },
                "sports": {
                    "records": 54,
                    "top_hours": [{"hour": "19", "activity_score": 600}],
                    "volume": {"avg": 400},
                    "liquidity": {"avg": 1800},
                    "spread": {"avg": 4},
                    "price_volatility": 7,
                },
            },
            "read_only": True,
            "execution_allowed": False,
        }


class FakeBridge:
    def __init__(self):
        self.build_calls = 0

    def diagnostics(self):
        return {
            "status": "ok",
            "analyzer_ready": True,
            "read_only": True,
            "execution_allowed": False,
        }

    def build_packet(self):
        self.build_calls += 1
        return {
            "module": "OI-022 Rhythm Insight Bridge",
            "status": "ok",
            "rows_analyzed": 144,
            "market_clock": {
                "best_activity_hours": [{"key": "14", "score": 900}],
                "highest_volume_hours": [{"key": "14", "score": 700}],
            },
            "category_intelligence": {
                "count": 2,
                "categories_ranked": [
                    {"category": "crypto", "records": 90},
                    {"category": "sports", "records": 54},
                ],
            },
            "oracle_summary": [
                "Oracle analyzed 144 historical market records.",
                "Most active historical hour bucket: 14.",
                "Rhythm intelligence is context-only and execution remains disabled.",
            ],
            "read_only": True,
            "execution_allowed": False,
        }

    def get_packet(self):
        return self.build_packet()

    def oracle_context(self):
        packet = self.build_packet()
        return {
            "context_type": "market_rhythm",
            "module": "oracle_rhythm_context",
            "status": packet["status"],
            "rows_analyzed": packet["rows_analyzed"],
            "summary": packet["oracle_summary"],
            "market_clock": packet["market_clock"],
            "category_intelligence": packet["category_intelligence"],
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_023_oracle_rhythm_service_integration():
    analyzer = FakeAnalyzer()
    bridge = FakeBridge()
    service = OracleRhythmService(analyzer=analyzer, bridge=bridge)

    diagnostics = service.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["analyzer_ready"] is True
    assert diagnostics["bridge_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    state = service.refresh()
    assert state["status"] == "ok"
    assert state["rows_analyzed"] == 144
    assert state["rhythm_snapshot_ready"] is True
    assert state["rhythm_packet_ready"] is True
    assert state["read_only"] is True
    assert state["execution_allowed"] is False

    context = service.get_oracle_context()
    assert context["context_type"] == "market_rhythm"
    assert context["rows_analyzed"] == 144
    assert context["market_clock"]["best_activity_hours"][0]["key"] == "14"
    assert context["read_only"] is True
    assert context["execution_allowed"] is False

    payload = service.api_payload()
    assert payload["module"] == "oracle_rhythm_service_payload"
    assert payload["status"] == "ok"
    assert payload["state"]["rows_analyzed"] == 144
    assert payload["context"]["context_type"] == "market_rhythm"
    assert payload["read_only"] is True
    assert payload["execution_allowed"] is False

    print("[PASS] OI-023 Oracle Rhythm Service Integration")
    print({
        "status": payload["status"],
        "rows_analyzed": payload["state"]["rows_analyzed"],
        "context_type": payload["context"]["context_type"],
        "top_activity_hour": payload["context"]["market_clock"]["best_activity_hours"][0],
    })


if __name__ == "__main__":
    test_oi_023_oracle_rhythm_service_integration()
