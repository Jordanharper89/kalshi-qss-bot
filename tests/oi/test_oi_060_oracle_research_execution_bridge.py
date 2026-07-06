from qseries_v2.oracle_intelligence.oracle_opportunity_queue_manager import OracleOpportunityQueueManager
from qseries_v2.oracle_intelligence.oracle_research_scheduler import OracleResearchScheduler
from qseries_v2.oracle_intelligence.oracle_research_execution_bridge import OracleResearchExecutionBridge


class FakeConsensusReportComposer:
    def status(self):
        return {"status": "ok"}

    def compose_consensus_report(self, current_setup, limit=25, format="terminal"):
        return {
            "status": "ok",
            "read_only": True,
            "format": format,
            "market_ticker": current_setup.get("ticker"),
            "report": f"Consensus report for {current_setup.get('ticker')}",
            "sections": [
                {"title": "Oracle Consensus Summary", "lines": ["Consensus Side: YES"]}
            ],
        }


def test_oi_060_oracle_research_execution_bridge():
    queue = OracleOpportunityQueueManager()
    scheduler = OracleResearchScheduler(queue)
    composer = FakeConsensusReportComposer()
    bridge = OracleResearchExecutionBridge(scheduler, composer)

    queue.ingest_discovery_result({
        "top_opportunities": [
            {
                "ticker": "EXEC-TEST-1",
                "opportunity_score": 92.0,
                "priority": "critical",
                "priority_weight": 5,
                "suggested_analysis_depth": "full_oracle_consensus",
                "reason_codes": ["rapid_volume_acceleration"],
                "market": {
                    "ticker": "EXEC-TEST-1",
                    "price": 52,
                    "volume": 10000,
                    "liquidity": 30000,
                    "spread": 2,
                },
            },
            {
                "ticker": "EXEC-TEST-2",
                "opportunity_score": 72.0,
                "priority": "medium",
                "priority_weight": 3,
                "suggested_analysis_depth": "standard_oracle_research",
                "reason_codes": ["historical_analog_support"],
                "market": {
                    "ticker": "EXEC-TEST-2",
                    "price": 48,
                    "volume": 8000,
                    "liquidity": 20000,
                    "spread": 3,
                },
            },
        ]
    })

    one = bridge.run_next_research(min_score=80)
    assert one["status"] == "ok"
    assert one["read_only"] is True
    assert one["research_only_execution"] is True
    assert one["ticker"] == "EXEC-TEST-1"
    assert "Consensus report for EXEC-TEST-1" in one["report"]["report"]

    batch = bridge.run_batch(min_score=55, max_jobs=3)
    assert batch["status"] == "ok"
    assert batch["completed_count"] == 1
    assert batch["results"][0]["ticker"] == "EXEC-TEST-2"

    hist = bridge.history()
    assert hist["count"] == 2

    status = bridge.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True
    assert status["research_runs"] == 2

    print("[PASS] OI-060 Oracle Research Execution Bridge")
    print({
        "research_runs": status["research_runs"],
        "history_count": hist["count"],
        "queue_status": scheduler.status(),
    })


if __name__ == "__main__":
    test_oi_060_oracle_research_execution_bridge()
