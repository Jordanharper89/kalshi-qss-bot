from qseries_v2.oracle_intelligence.oracle_opportunity_queue_manager import OracleOpportunityQueueManager
from qseries_v2.oracle_intelligence.oracle_research_scheduler import OracleResearchScheduler


def test_oi_059_oracle_research_scheduler():
    queue = OracleOpportunityQueueManager()
    scheduler = OracleResearchScheduler(queue)

    discovery = {
        "top_opportunities": [
            {
                "ticker": "SCH-CRITICAL",
                "opportunity_score": 94.0,
                "priority": "critical",
                "priority_weight": 5,
                "suggested_analysis_depth": "full_oracle_consensus",
                "reason_codes": ["rapid_volume_acceleration", "cross_market_divergence_detected"],
            },
            {
                "ticker": "SCH-WATCH",
                "opportunity_score": 58.0,
                "priority": "watch",
                "priority_weight": 2,
                "suggested_analysis_depth": "light_watch_report",
                "reason_codes": ["low_signal_watch_only"],
            },
        ]
    }

    ingest = queue.ingest_discovery_result(discovery)
    assert ingest["added"] == 2

    evaluation = scheduler.evaluate_queue()
    assert evaluation["status"] == "ok"
    assert evaluation["evaluated"] == 2
    assert evaluation["items"][0]["ticker"] == "SCH-CRITICAL"
    assert evaluation["items"][0]["research_priority"] == "CRITICAL"

    job = scheduler.schedule_next(min_score=55)
    assert job["status"] == "scheduled"
    assert job["ticker"] == "SCH-CRITICAL"
    assert job["research_depth"] == "full_oracle_consensus"

    batch = scheduler.schedule_batch(min_score=55, max_jobs=2)
    assert batch["status"] == "ok"
    assert batch["scheduled_count"] == 1
    assert batch["scheduled"][0]["ticker"] == "SCH-WATCH"

    jobs = scheduler.scheduled_jobs()
    assert len(jobs) == 2
    assert len({j["ticker"] for j in jobs}) == 2

    completed = scheduler.complete_job("SCH-CRITICAL", {"report": "done"})
    assert completed["status"] == "ok"

    skipped = scheduler.skip_job("SCH-WATCH", "watch_only")
    assert skipped["status"] == "ok"

    status = scheduler.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True
    assert status["scheduled_jobs"] == 0

    print("[PASS] OI-059.1 Oracle Research Scheduler Reserved Fix")
    print(status)


if __name__ == "__main__":
    test_oi_059_oracle_research_scheduler()
