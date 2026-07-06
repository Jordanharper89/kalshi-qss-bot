from qseries_v2.oracle_intelligence.oracle_consensus_report_composer import OracleConsensusReportComposer


class FakeConsensusPacketBridge:
    def status(self):
        return {"status": "ok"}

    def build_consensus_packet(self, *args, **kwargs):
        return {
            "status": "ok",
            "read_only": True,
            "packet_type": "oracle_consensus_research_packet",
            "market_ticker": "CONSENSUS-REPORT-TEST",
            "summary": {
                "market_ticker": "CONSENSUS-REPORT-TEST",
                "expected_resolution": "YES",
                "expected_probability": 0.84,
                "adjusted_confidence": 82,
                "confidence_delta": -2,
                "risk_level": "medium",
                "tail_risk_level": "low",
                "analog_count": 12,
            },
            "signals": {
                "final_research_grade": "A",
                "execution_owner": "Q Series",
                "actionable": False,
            },
            "consensus": {
                "consensus_side": "YES",
                "consensus_score_pct": 87.5,
                "agreement_pct": 92.0,
                "disagreement_pct": 8.0,
                "research_stability": "high",
                "research_certainty_index": 91.0,
                "outlier_engines": [],
            },
            "consensus_votes": [
                {"engine": "case_reasoning", "side": "YES", "confidence": 86, "weight": 0.24, "usable": True},
                {"engine": "outcome_distribution", "side": "YES", "confidence": 82, "weight": 0.24, "usable": True},
            ],
            "consensus_explanation": [
                "Oracle consensus favors YES.",
                "Research stability is high.",
            ],
            "api": {
                "execution_enabled": False,
            },
        }


def test_oi_056_oracle_consensus_report_composer():
    composer = OracleConsensusReportComposer(FakeConsensusPacketBridge())

    terminal = composer.compose_consensus_report({"ticker": "CONSENSUS-REPORT-TEST"}, format="terminal")
    assert terminal["status"] == "ok"
    assert terminal["read_only"] is True
    assert "ORACLE CONSENSUS RESEARCH REPORT" in terminal["report"]
    assert "Consensus Score: 87.5%" in terminal["report"]
    assert "case_reasoning: YES" in terminal["report"]
    assert "Execution remains Q Series only." in terminal["report"]

    telegram = composer.compose_consensus_report({"ticker": "CONSENSUS-REPORT-TEST"}, format="telegram")
    assert "🧠 Oracle Consensus Research Report" in telegram["report"]
    assert "*Oracle Consensus Summary*" in telegram["report"]

    api = composer.compose_consensus_report({"ticker": "CONSENSUS-REPORT-TEST"}, format="api")
    assert "Oracle Consensus Summary" in api["report"]

    status = composer.status()
    assert status["status"] == "ok"

    print("[PASS] OI-056 Oracle Consensus Report Composer")
    print({
        "market_ticker": terminal["market_ticker"],
        "format": terminal["format"],
        "sections": len(terminal["sections"]),
    })


if __name__ == "__main__":
    test_oi_056_oracle_consensus_report_composer()
