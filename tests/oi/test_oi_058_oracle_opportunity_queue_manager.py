from qseries_v2.oracle_intelligence.oracle_opportunity_queue_manager import OracleOpportunityQueueManager


def test_oi_058_oracle_opportunity_queue_manager():
    queue = OracleOpportunityQueueManager()

    discovery = {
        "top_opportunities": [
            {
                "ticker": "QUEUE-HIGH",
                "opportunity_score": 91.5,
                "priority": "critical",
                "priority_weight": 5,
                "reason_codes": ["rapid_volume_acceleration"],
            },
            {
                "ticker": "QUEUE-LOW",
                "opportunity_score": 61.0,
                "priority": "watch",
                "priority_weight": 2,
                "reason_codes": ["low_signal_watch_only"],
            },
        ]
    }

    ingest = queue.ingest_discovery_result(discovery)
    assert ingest["status"] == "ok"
    assert ingest["added"] == 2
    assert ingest["queued"] == 2

    duplicate = queue.enqueue({
        "ticker": "QUEUE-HIGH",
        "opportunity_score": 95.0,
        "priority": "critical",
        "priority_weight": 5,
    })
    assert duplicate["action"] == "updated"

    peeked = queue.peek(limit=2)
    assert peeked[0]["ticker"] == "QUEUE-HIGH"
    assert peeked[0]["opportunity_score"] == 95.0

    next_item = queue.next_opportunity(min_score=80)
    assert next_item["ticker"] == "QUEUE-HIGH"

    processed = queue.mark_processed("QUEUE-HIGH", {"research_status": "done"})
    assert processed["status"] == "ok"
    assert processed["queued"] == 1
    assert processed["processed"] == 1

    requeued = queue.requeue("QUEUE-HIGH")
    assert requeued["status"] == "ok"
    assert requeued["queued"] == 2

    skipped = queue.mark_skipped("QUEUE-LOW", "below_threshold")
    assert skipped["status"] == "ok"

    snapshot = queue.snapshot()
    assert snapshot["counts"]["queued"] == 1
    assert snapshot["counts"]["processed"] == 1

    status = queue.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-058 Oracle Opportunity Queue Manager")
    print({
        "queued": status["queued"],
        "processed": status["processed"],
        "top": queue.peek(limit=1)[0]["ticker"],
    })


if __name__ == "__main__":
    test_oi_058_oracle_opportunity_queue_manager()
