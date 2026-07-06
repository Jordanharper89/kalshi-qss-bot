
from qseries_v2.oracle_intelligence.executive_historical_trend_engine import (
    executive_historical_trend_engine,
)


def test_oi_143_executive_historical_trend_engine():
    evolution = {
        "confidence_evolution_packets": [
            {
                "case_id": "case-crypto-001",
                "market": "CRYPTO",
                "case_type": "digest_snapshot",
                "baseline_confidence": 89.3764,
                "historical_support": 88.801,
                "evolved_confidence": 89.175,
                "confidence_delta": -0.2014,
                "confidence_tier": "institutional_confidence",
                "confidence_trajectory": "stable",
                "best_match_market": "CRYPTO",
                "best_match_tier": "near_match",
                "memory_strength": 92,
                "memory_tier": "institutional_memory",
                "avg_pattern_score": 89.7,
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "case_id": "case-nasdaq-001",
                "market": "NASDAQ",
                "case_type": "strategic_briefing",
                "baseline_confidence": 72.7342,
                "historical_support": 68.744,
                "evolved_confidence": 72.015,
                "confidence_delta": -0.7192,
                "confidence_tier": "strong_confidence",
                "confidence_trajectory": "stable",
                "best_match_market": "NASDAQ",
                "best_match_tier": "strong_match",
                "memory_strength": 71,
                "memory_tier": "strong_memory",
                "avg_pattern_score": 55.2,
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    memory = {
        "market_memory_profiles": [
            {
                "market": "CRYPTO",
                "memory_strength": 92,
                "memory_tier": "institutional_memory",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "memory_strength": 71,
                "memory_tier": "strong_memory",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    patterns = {
        "patterns": [
            {
                "pattern_key": "CRYPTO",
                "pattern_type": "market_visibility",
                "pattern_score": 89.7,
                "markets": ["CRYPTO"],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "pattern_key": "CRYPTO",
                "pattern_type": "archive_time_visibility",
                "pattern_score": 89.72,
                "markets": ["CRYPTO"],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "pattern_key": "NASDAQ",
                "pattern_type": "market_visibility",
                "pattern_score": 55.2,
                "markets": ["NASDAQ"],
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = executive_historical_trend_engine.build_historical_trends(
        evolution,
        memory,
        patterns,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["trend_count"] == 2
    assert report["historical_trend_cards"][0]["trend_rank"] == 1
    assert report["historical_trend_cards"][0]["market"] == "CRYPTO"
    assert report["historical_trend_cards"][0]["execution_allowed"] is False
    assert report["historical_trend_cards"][0]["read_only"] is True
    assert report["trend_summary"]["execution_allowed"] is False
    assert report["trend_summary"]["read_only"] is True
    assert report["executive_brief"]["execution_allowed"] is False
    assert report["executive_brief"]["execution_owner"] == "Q Series"

    diag = executive_historical_trend_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["trend_count"] == report["trend_count"]

    print("[PASS] OI-143 Executive Historical Trend Engine")
    print({
        "trend_count": report["trend_count"],
        "summary": report["trend_summary"],
        "brief": report["executive_brief"],
        "top": report["historical_trend_cards"][0],
    })


if __name__ == "__main__":
    test_oi_143_executive_historical_trend_engine()
