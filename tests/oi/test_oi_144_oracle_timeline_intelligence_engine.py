
from qseries_v2.oracle_intelligence.oracle_timeline_intelligence_engine import (
    oracle_timeline_intelligence_engine,
)


def test_oi_144_oracle_timeline_intelligence_engine():
    trends = {
        "historical_trend_cards": [
            {
                "market": "CRYPTO",
                "case_id": "case-crypto-001",
                "case_type": "digest_snapshot",
                "trend_score": 89.4486,
                "trend_tier": "dominant_historical_trend",
                "trend_direction": "stable",
                "executive_trend_posture": "executive_priority_watch",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "case_id": "case-nasdaq-001",
                "case_type": "strategic_briefing",
                "trend_score": 58.2,
                "trend_tier": "developing_historical_trend",
                "trend_direction": "stable",
                "executive_trend_posture": "standard_historical_review",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    evolution = {
        "confidence_evolution_packets": [
            {
                "case_id": "case-crypto-001",
                "market": "CRYPTO",
                "case_type": "digest_snapshot",
                "evolved_confidence": 89.175,
                "confidence_tier": "institutional_confidence",
                "confidence_trajectory": "stable",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "case_id": "case-nasdaq-001",
                "market": "NASDAQ",
                "case_type": "strategic_briefing",
                "evolved_confidence": 72.015,
                "confidence_tier": "strong_confidence",
                "confidence_trajectory": "stable",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    memory = {
        "market_memory_profiles": [
            {
                "market": "CRYPTO",
                "memory_strength": 92.62,
                "memory_tier": "institutional_memory",
                "historical_signature": {
                    "signature_label": "CRYPTO memory signature: digest_snapshot / market_visibility"
                },
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "memory_strength": 56.1,
                "memory_tier": "developing_memory",
                "historical_signature": {
                    "signature_label": "NASDAQ memory signature: strategic_briefing / market_visibility"
                },
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    catalog = {
        "catalog_records": [
            {
                "catalog_key": "arc-001",
                "archive_id": "arc-001",
                "market": "CRYPTO",
                "archive_type": "digest_snapshot",
                "archive_timestamp": 1800000000,
                "catalog_priority": 94,
                "catalog_tier": "institutional_priority",
                "catalog_label": "CRYPTO digest_snapshot catalog record",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "catalog_key": "arc-002",
                "archive_id": "arc-002",
                "market": "NASDAQ",
                "archive_type": "strategic_briefing",
                "archive_timestamp": 1799999000,
                "catalog_priority": 76,
                "catalog_tier": "high_value",
                "catalog_label": "NASDAQ strategic_briefing catalog record",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = oracle_timeline_intelligence_engine.build_timeline(
        trends,
        evolution,
        memory,
        catalog,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["timeline_count"] == 2
    assert report["market_timelines"][0]["timeline_rank"] == 1
    assert report["market_timelines"][0]["market"] == "CRYPTO"
    assert report["market_timelines"][0]["event_count"] == 4
    assert report["market_timelines"][0]["execution_allowed"] is False
    assert report["market_timelines"][0]["read_only"] is True
    assert report["market_timelines"][0]["timeline_events"][0]["execution_allowed"] is False
    assert report["timeline_summary"]["execution_allowed"] is False
    assert report["timeline_summary"]["read_only"] is True
    assert report["executive_timeline_brief"]["execution_allowed"] is False
    assert report["executive_timeline_brief"]["execution_owner"] == "Q Series"

    diag = oracle_timeline_intelligence_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["timeline_count"] == report["timeline_count"]

    print("[PASS] OI-144 Oracle Timeline Intelligence Engine")
    print({
        "timeline_count": report["timeline_count"],
        "summary": report["timeline_summary"],
        "brief": report["executive_timeline_brief"],
        "top": report["market_timelines"][0],
    })


if __name__ == "__main__":
    test_oi_144_oracle_timeline_intelligence_engine()
