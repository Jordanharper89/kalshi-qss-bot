
from qseries_v2.oracle_intelligence.historical_case_comparison_engine import (
    historical_case_comparison_engine,
)


def test_oi_141_historical_case_comparison_engine():
    current_cases = {
        "cases": [
            {
                "case_id": "case-crypto-001",
                "market": "CRYPTO",
                "case_type": "digest_snapshot",
                "case_score": 91,
            },
            {
                "case_id": "case-nasdaq-001",
                "market": "NASDAQ",
                "case_type": "strategic_briefing",
                "case_score": 73,
            },
        ]
    }

    memory = {
        "market_memory_profiles": [
            {
                "market": "CRYPTO",
                "memory_strength": 92,
                "memory_tier": "institutional_memory",
                "avg_pattern_score": 89.7,
                "historical_signature": {
                    "market": "CRYPTO",
                    "archive_type_signature": ["digest_snapshot"],
                    "pattern_type_signature": ["market_visibility"],
                    "tier_signature": ["institutional_priority"],
                    "execution_allowed": False,
                    "read_only": True,
                },
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "memory_strength": 71,
                "memory_tier": "strong_memory",
                "avg_pattern_score": 55.2,
                "historical_signature": {
                    "market": "NASDAQ",
                    "archive_type_signature": ["strategic_briefing"],
                    "pattern_type_signature": ["market_visibility"],
                    "tier_signature": ["high_value"],
                    "execution_allowed": False,
                    "read_only": True,
                },
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
                "archive_types": ["digest_snapshot"],
                "catalog_tiers": ["institutional_priority"],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "pattern_key": "NASDAQ",
                "pattern_type": "market_visibility",
                "pattern_score": 55.2,
                "markets": ["NASDAQ"],
                "archive_types": ["strategic_briefing"],
                "catalog_tiers": ["high_value"],
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = historical_case_comparison_engine.compare_cases(current_cases, memory, patterns)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["case_count"] == 2
    assert report["comparison_packet_count"] == 2
    assert report["comparison_packets"][0]["case_rank"] == 1
    assert report["comparison_packets"][0]["top_matches"][0]["execution_allowed"] is False
    assert report["comparison_packets"][0]["top_matches"][0]["read_only"] is True
    assert report["comparison_summary"]["execution_allowed"] is False
    assert report["comparison_summary"]["read_only"] is True
    assert report["comparison_packets"][0]["best_similarity_score"] > 50

    diag = historical_case_comparison_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["comparison_packet_count"] == report["comparison_packet_count"]

    print("[PASS] OI-141 Historical Case Comparison Engine")
    print({
        "case_count": report["case_count"],
        "comparison_packet_count": report["comparison_packet_count"],
        "summary": report["comparison_summary"],
        "top": report["comparison_packets"][0],
    })


if __name__ == "__main__":
    test_oi_141_historical_case_comparison_engine()
