from qseries_v2.oracle_intelligence.multi_factor_intelligence_fusion_engine import MultiFactorIntelligenceFusionEngine


class FakeRhythmService:
    def get_oracle_context(self):
        return {
            "status": "ok",
            "context_type": "market_rhythm",
            "summary": ["Oracle analyzed 500 historical market records."],
            "market_clock": {
                "best_activity_hours": [{"key": "14", "score": 900}],
                "highest_volume_hours": [{"key": "14", "score": 800}],
                "strongest_liquidity_hours": [{"key": "15", "score": 3000}],
            },
            "read_only": True,
            "execution_allowed": False,
        }


class FakeBaselineEngine:
    def compare_live_market(self, live_market):
        return {
            "status": "ok",
            "market": {
                "ticker": live_market.get("ticker"),
                "category": live_market.get("category"),
            },
            "abnormality_score": {
                "score": 82.5,
                "label": "high",
                "abnormal_metrics": 12,
                "metrics_checked": 24,
            },
            "interpretation": "Current market behavior is meaningfully unusual versus historical baselines.",
            "read_only": True,
            "execution_allowed": False,
        }


class FakePatternEngine:
    def find_similar_markets(self, live_market):
        return {
            "status": "ok",
            "matches_found": 42,
            "top_matches": [
                {"similarity": 94.8, "label": "extremely_similar"},
                {"similarity": 91.2, "label": "extremely_similar"},
            ],
            "pattern_summary": {
                "occurrences": 42,
                "average_similarity": 88.4,
            },
            "confidence": {
                "score": 89.7,
                "label": "very_high",
                "sample_size": 42,
                "data_quality": "excellent",
                "data_quality_score": 96.0,
                "historical_consistency": 91.0,
            },
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_026_multi_factor_intelligence_fusion_engine():
    engine = MultiFactorIntelligenceFusionEngine(
        rhythm_service=FakeRhythmService(),
        baseline_engine=FakeBaselineEngine(),
        pattern_engine=FakePatternEngine(),
    )

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["rhythm_service_ready"] is True
    assert diagnostics["baseline_engine_ready"] is True
    assert diagnostics["pattern_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
        "yes_price": 52,
        "volume": 1200,
        "liquidity": 3000,
    }

    packet = engine.analyze_market(live_market)
    assert packet["status"] == "ok"
    assert packet["market"]["ticker"] == "BTC-TEST"
    assert packet["component_scores"]["rhythm"]["score"] > 0
    assert packet["component_scores"]["baseline"]["score"] == 82.5
    assert packet["component_scores"]["pattern"]["score"] == 94.8
    assert packet["component_scores"]["historical_confidence"]["score"] == 89.7
    assert packet["component_scores"]["data_quality"]["score"] == 96.0
    assert packet["overall_score"]["score"] > 80
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    scores = engine.component_scores(live_market)
    assert scores["pattern"]["score"] == 94.8

    explanation = engine.explain(live_market)
    assert explanation["overall_score"]["score"] > 80
    assert explanation["explanation"]
    assert explanation["read_only"] is True
    assert explanation["execution_allowed"] is False

    print("[PASS] OI-026 Multi-Factor Intelligence Fusion Engine")
    print({
        "overall_score": packet["overall_score"],
        "component_scores": {
            k: v["score"]
            for k, v in packet["component_scores"].items()
        },
        "source_status": packet["source_status"],
    })


if __name__ == "__main__":
    test_oi_026_multi_factor_intelligence_fusion_engine()
