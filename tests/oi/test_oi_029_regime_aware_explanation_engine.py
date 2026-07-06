from qseries_v2.oracle_intelligence.regime_aware_explanation_engine import RegimeAwareExplanationEngine


class FakeFusionEngine:
    def analyze_market(self, live_market):
        return {
            "module": "OI-028 Regime Fusion Integration",
            "status": "ok",
            "market": {
                "ticker": live_market.get("ticker"),
                "category": live_market.get("category"),
                "timestamp": live_market.get("timestamp"),
            },
            "component_scores": {
                "rhythm": {"score": 65.0, "label": "moderate", "details": "Rhythm context available."},
                "baseline": {"score": 82.5, "label": "high", "details": "Behavior is unusual versus baseline."},
                "pattern": {"score": 94.8, "label": "very_high", "details": "Strong historical match."},
                "historical_confidence": {"score": 89.7, "label": "very_high", "details": "Sample size: 42."},
                "data_quality": {"score": 96.0, "label": "very_high", "details": "Excellent."},
                "regime": {
                    "score": 88.4,
                    "label": "very_high",
                    "regime": "high_liquidity_low_volatility",
                    "details": "Deep liquidity with controlled movement.",
                },
            },
            "overall_score": {
                "score": 86.25,
                "label": "very_high",
                "interpretation": "Oracle intelligence alignment is very high across fused historical and regime factors.",
            },
            "explanation": [
                "Detected market regime: high_liquidity_low_volatility.",
                "Similar historical pattern occurrences: 42.",
                "Current market behavior is meaningfully unusual versus historical baselines.",
                "Read-only Oracle analysis only. Execution remains disabled.",
            ],
            "source_status": {
                "rhythm": "ok",
                "baseline": "ok",
                "pattern": "ok",
                "regime": "ok",
            },
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_029_regime_aware_explanation_engine():
    engine = RegimeAwareExplanationEngine(fusion_engine=FakeFusionEngine())

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["fusion_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
    }

    packet = engine.explain_market(live_market)

    assert packet["status"] == "ok"
    assert packet["headline"]
    assert "BTC-TEST" in packet["headline"]
    assert "high_liquidity_low_volatility" in packet["headline"]
    assert packet["summary"]
    assert packet["component_breakdown"]
    assert packet["component_breakdown"][0]["component"] in {"data_quality", "pattern", "historical_confidence", "regime"}
    assert packet["reasoning_bullets"]
    assert packet["context_notes"]
    assert packet["risk_notes"]
    assert packet["oracle_report_text"]
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    payload = engine.api_payload(live_market)
    assert payload["module"] == "oracle_regime_aware_explanation_payload"
    assert payload["headline"]
    assert payload["reasoning"]
    assert payload["read_only"] is True
    assert payload["execution_allowed"] is False

    latest = engine.latest()
    assert latest["headline"] == packet["headline"]

    print("[PASS] OI-029 Regime-Aware Explanation Engine")
    print({
        "headline": packet["headline"],
        "top_component": packet["component_breakdown"][0],
        "risk_notes": len(packet["risk_notes"]),
    })


if __name__ == "__main__":
    test_oi_029_regime_aware_explanation_engine()
