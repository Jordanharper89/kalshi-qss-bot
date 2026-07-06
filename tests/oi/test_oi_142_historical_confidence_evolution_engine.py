
from qseries_v2.oracle_intelligence.historical_confidence_evolution_engine import (
    historical_confidence_evolution_engine,
)


def test_oi_142_historical_confidence_evolution_engine():
    comparisons = {
        "comparison_packets": [
            {
                "case_id": "case-crypto-001",
                "market": "CRYPTO",
                "case_type": "digest_snapshot",
                "case_score": 91,
                "best_match_market": "CRYPTO",
                "best_similarity_score": 85.588,
                "top_matches": [
                    {
                        "market": "CRYPTO",
                        "similarity_score": 85.588,
                        "similarity_tier": "near_match",
                        "read_only": True,
                        "execution_allowed": False,
                    }
                ],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "case_id": "case-nasdaq-001",
                "market": "NASDAQ",
                "case_type": "strategic_briefing",
                "case_score": 73,
                "best_match_market": "NASDAQ",
                "best_similarity_score": 72.114,
                "top_matches": [
                    {
                        "market": "NASDAQ",
                        "similarity_score": 72.114,
                        "similarity_tier": "strong_match",
                        "read_only": True,
                        "execution_allowed": False,
                    }
                ],
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
                "pattern_key": "NASDAQ",
                "pattern_type": "market_visibility",
                "pattern_score": 55.2,
                "markets": ["NASDAQ"],
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = historical_confidence_evolution_engine.build_confidence_evolution(
        comparisons,
        memory,
        patterns,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["evolution_count"] == 2
    assert report["confidence_evolution_packets"][0]["evolution_rank"] == 1
    assert report["confidence_evolution_packets"][0]["market"] == "CRYPTO"
    assert report["confidence_evolution_packets"][0]["evolved_confidence"] >= 80
    assert report["confidence_evolution_packets"][0]["execution_allowed"] is False
    assert report["confidence_evolution_packets"][0]["read_only"] is True
    assert report["evolution_summary"]["execution_allowed"] is False
    assert report["evolution_summary"]["read_only"] is True

    diag = historical_confidence_evolution_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["evolution_count"] == report["evolution_count"]

    print("[PASS] OI-142 Historical Confidence Evolution Engine")
    print({
        "evolution_count": report["evolution_count"],
        "summary": report["evolution_summary"],
        "top": report["confidence_evolution_packets"][0],
    })


if __name__ == "__main__":
    test_oi_142_historical_confidence_evolution_engine()
