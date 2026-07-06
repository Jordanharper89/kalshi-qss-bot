from qseries_v2.oracle_intelligence.multi_factor_intelligence_fusion_engine import MultiFactorIntelligenceFusionEngine


class FakeRhythmService:
    def get_oracle_context(self):
        return {
            "status": "ok",
            "context_type": "market_rhythm",
            "summary": ["Oracle analyzed rhythm behavior from historical market records."],
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


class FakeRegimeEngine:
    def detect_regime(self, live_market):
        return {
            "status": "ok",
            "rows_analyzed": 300,
            "current_regime": {
                "name": "high_liquidity_low_volatility",
                "score": 87.0,
                "label": "very_high",
                "confidence": {
                    "score": 91.0,
                    "label": "very_high",
                    "sample_size": 250,
                },
                "description": "Deep liquidity with controlled price movement.",
            },
            "regime_features": {
                "sample_size": 250,
                "avg_liquidity": 3500,
                "avg_volume": 1800,
                "avg_spread": 4.0,
                "price_volatility": 8.2,
            },
            "oracle_context": {
                "context_type": "market_regime",
                "status": "ok",
            },
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_028_regime_fusion_integration():
    engine = MultiFactorIntelligenceFusionEngine(
        rhythm_service=FakeRhythmService(),
        baseline_engine=FakeBaselineEngine(),
        pattern_engine=FakePatternEngine(),
        regime_engine=FakeRegimeEngine(),
    )

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["regime_engine_ready"] is True
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

    assert packet["module"] == "OI-028 Regime Fusion Integration"
    assert packet["status"] == "ok"
    assert packet["component_scores"]["regime"]["score"] > 85
    assert packet["component_scores"]["regime"]["regime"] == "high_liquidity_low_volatility"
    assert packet["source_status"]["regime"] == "ok"
    assert packet["overall_score"]["score"] > 80
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    explanation = engine.explain(live_market)
    assert "Detected market regime" in " ".join(explanation["explanation"])
    assert explanation["read_only"] is True
    assert explanation["execution_allowed"] is False

    print("[PASS] OI-028 Regime Fusion Integration")
    print({
        "overall_score": packet["overall_score"],
        "regime_score": packet["component_scores"]["regime"],
        "source_status": packet["source_status"],
    })


if __name__ == "__main__":
    test_oi_028_regime_fusion_integration()
