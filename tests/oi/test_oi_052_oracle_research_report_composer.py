from qseries_v2.oracle_intelligence.oracle_research_report_composer import OracleResearchReportComposer


class FakeSynthesisEngine:
    def status(self):
        return {"status": "ok"}

    def synthesize(self, *args, **kwargs):
        return {
            "summary": {
                "market_ticker": "REPORT-TEST",
                "expected_resolution": "YES",
                "expected_probability": 0.82,
                "adjusted_confidence": 79.5,
                "confidence_delta": -2.5,
                "avg_expected_move": 5.2,
                "median_expected_move": 4.8,
                "avg_resolution_minutes": 36,
                "tail_risk_level": "medium",
                "risk_level": "medium",
                "analog_count": 12,
                "graph_nodes": 20,
                "graph_edges": 30,
                "top_analog": {
                    "market_ticker": "ANALOG-1",
                    "retrieval_score_pct": 91.2,
                    "similarity_pct": 88.4,
                    "dna_similarity_pct": 86.0,
                },
            },
            "case_reasoning": {
                "reasoning": [
                    "Oracle found 12 similar historical cases.",
                    "Weighted evidence favors YES.",
                ],
            },
            "outcome_distribution": {
                "resolution_distribution": {
                    "yes_probability": 0.82,
                    "no_probability": 0.18,
                    "known_outcome_count": 12,
                },
                "movement_distribution": {
                    "mean": 5.2,
                    "median": 4.8,
                },
                "timing_distribution_minutes": {
                    "mean": 36,
                },
                "tail_risk": {
                    "tail_risk_level": "medium",
                },
            },
            "analog_retrieval": {
                "summary": {
                    "avg_retrieval_score_pct": 80.1,
                    "avg_similarity_pct": 76.2,
                    "avg_dna_similarity_pct": 70.3,
                },
            },
            "adjusted_confidence": {
                "raw_confidence": 82,
                "adjusted_confidence": 79.5,
                "delta": -2.5,
                "bucket": "80-90",
                "reason": "Oracle confidence is reasonably calibrated.",
            },
            "market_dna": {
                "dna_id": "dna_test",
                "dna_family": "family_test",
                "traits": ["momentum:strong_positive", "regime:trend"],
            },
            "knowledge_graph_context": {
                "market_node": "market:REPORT-TEST",
                "graph_summary": {
                    "total_nodes": 20,
                    "total_edges": 30,
                },
            },
        }


def test_oi_052_oracle_research_report_composer():
    composer = OracleResearchReportComposer(FakeSynthesisEngine())

    terminal = composer.compose_report({"ticker": "REPORT-TEST"}, format="terminal")
    assert terminal["status"] == "ok"
    assert terminal["read_only"] is True
    assert "ORACLE RESEARCH REPORT" in terminal["report"]
    assert "REPORT-TEST" in terminal["report"]
    assert "Expected Resolution: YES" in terminal["report"]

    telegram = composer.compose_report({"ticker": "REPORT-TEST"}, format="telegram")
    assert "🧠 Oracle Research Report" in telegram["report"]
    assert "*Oracle Research Summary*" in telegram["report"]

    api = composer.compose_report({"ticker": "REPORT-TEST"}, format="api")
    assert "Oracle Research Summary" in api["report"]

    status = composer.status()
    assert status["status"] == "ok"

    print("[PASS] OI-052 Oracle Research Report Composer")
    print({
        "market_ticker": terminal["market_ticker"],
        "format": terminal["format"],
        "sections": len(terminal["sections"]),
    })


if __name__ == "__main__":
    test_oi_052_oracle_research_report_composer()
