
from qseries_v2.oracle_intelligence.oracle_knowledge_catalog_engine import (
    oracle_knowledge_catalog_engine,
)


def test_oi_145_oracle_knowledge_catalog_engine():
    timeline = {
        "market_timelines": [
            {
                "market": "CRYPTO",
                "timeline_score": 100,
                "timeline_tier": "institutional_timeline",
                "timeline_phase": "executive_timeline_active",
                "event_count": 4,
                "timeline_events": [
                    {
                        "event_type": "confidence_evolution",
                        "event_source": "confidence",
                        "event_score": 89.175,
                        "event_tier": "institutional_confidence",
                        "event_label": "stable",
                        "timeline_position": 1,
                        "source_keys": {
                            "case_id": "case-crypto-001",
                            "market": "CRYPTO",
                            "confidence_tier": "institutional_confidence",
                        },
                        "read_only": True,
                        "execution_allowed": False,
                    },
                    {
                        "event_type": "executive_trend",
                        "event_source": "trend",
                        "event_score": 89.4486,
                        "event_tier": "dominant_historical_trend",
                        "event_label": "executive_priority_watch",
                        "timeline_position": 2,
                        "source_keys": {
                            "case_id": "case-crypto-001",
                            "market": "CRYPTO",
                            "trend_tier": "dominant_historical_trend",
                        },
                        "read_only": True,
                        "execution_allowed": False,
                    },
                ],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "timeline_score": 72,
                "timeline_tier": "strong_timeline",
                "timeline_phase": "archive_phase",
                "event_count": 2,
                "timeline_events": [],
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    trends = {
        "historical_trend_cards": [
            {
                "market": "CRYPTO",
                "trend_score": 89.4486,
                "trend_tier": "dominant_historical_trend",
                "trend_direction": "stable",
                "executive_trend_posture": "executive_priority_watch",
                "case_id": "case-crypto-001",
                "case_type": "digest_snapshot",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "trend_score": 58.2,
                "trend_tier": "developing_historical_trend",
                "trend_direction": "stable",
                "executive_trend_posture": "standard_historical_review",
                "case_id": "case-nasdaq-001",
                "case_type": "strategic_briefing",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    evolution = {
        "confidence_evolution_packets": [
            {
                "market": "CRYPTO",
                "case_id": "case-crypto-001",
                "case_type": "digest_snapshot",
                "evolved_confidence": 89.175,
                "confidence_tier": "institutional_confidence",
                "confidence_trajectory": "stable",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "case_id": "case-nasdaq-001",
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
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "memory_strength": 56.1,
                "memory_tier": "developing_memory",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = oracle_knowledge_catalog_engine.build_knowledge_catalog(
        timeline,
        trends,
        evolution,
        memory,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["knowledge_record_count"] == 2
    assert report["knowledge_records"][0]["knowledge_rank"] == 1
    assert report["knowledge_records"][0]["market"] == "CRYPTO"
    assert report["knowledge_records"][0]["knowledge_status"] == "executive_ready_knowledge"
    assert report["knowledge_records"][0]["execution_allowed"] is False
    assert report["knowledge_records"][0]["read_only"] is True
    assert report["knowledge_records"][0]["event_catalog"][0]["execution_allowed"] is False
    assert report["knowledge_summary"]["execution_allowed"] is False
    assert report["knowledge_summary"]["read_only"] is True
    assert report["executive_knowledge_brief"]["execution_allowed"] is False
    assert report["executive_knowledge_brief"]["execution_owner"] == "Q Series"

    diag = oracle_knowledge_catalog_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["knowledge_record_count"] == report["knowledge_record_count"]

    print("[PASS] OI-145 Oracle Knowledge Catalog Engine")
    print({
        "knowledge_record_count": report["knowledge_record_count"],
        "summary": report["knowledge_summary"],
        "brief": report["executive_knowledge_brief"],
        "top": report["knowledge_records"][0],
    })


if __name__ == "__main__":
    test_oi_145_oracle_knowledge_catalog_engine()
