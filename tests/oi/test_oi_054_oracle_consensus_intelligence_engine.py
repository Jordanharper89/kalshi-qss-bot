from qseries_v2.oracle_intelligence.oracle_consensus_intelligence_engine import OracleConsensusIntelligenceEngine


class FakeSynthesisEngine:
    def status(self):
        return {"status": "ok"}

    def synthesize(self, *args, **kwargs):
        return {
            "summary": {
                "market_ticker": "CONSENSUS-TEST",
                "expected_resolution": "YES",
                "expected_probability": 0.84,
                "adjusted_confidence": 82,
                "confidence_delta": -2,
                "risk_level": "medium",
                "tail_risk_level": "low",
                "analog_count": 12,
                "top_analog": {
                    "market_ticker": "ANALOG-1",
                    "retrieval_score_pct": 88,
                    "similarity_pct": 86,
                    "dna_similarity_pct": 84,
                },
                "graph_nodes": 20,
                "graph_edges": 30,
            },
            "case_reasoning": {
                "expected_resolution": "YES",
                "expected_probability": 0.86,
                "case_count": 12,
                "risk_level": "medium",
            },
            "outcome_distribution": {
                "resolution_distribution": {
                    "expected_resolution": "YES",
                    "yes_probability": 0.82,
                    "no_probability": 0.18,
                    "known_outcome_count": 12,
                },
            },
            "analog_retrieval": {
                "summary": {
                    "avg_retrieval_score_pct": 80,
                },
            },
            "adjusted_confidence": {
                "adjusted_confidence": 82,
                "delta": -2,
            },
            "market_dna": {
                "dna_family": "family_test",
                "traits": ["a", "b", "c", "d", "e", "f"],
            },
            "knowledge_graph_context": {
                "graph_summary": {
                    "total_nodes": 20,
                    "total_edges": 30,
                },
            },
        }


def test_oi_054_oracle_consensus_intelligence_engine():
    engine = OracleConsensusIntelligenceEngine(FakeSynthesisEngine())

    result = engine.build_consensus({"ticker": "CONSENSUS-TEST"})

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["market_ticker"] == "CONSENSUS-TEST"
    assert result["consensus"]["consensus_side"] == "YES"
    assert result["consensus"]["consensus_score_pct"] >= 80
    assert result["consensus"]["usable_votes"] >= 5
    assert len(result["votes"]) >= 6
    assert len(result["explanation"]) >= 3

    status = engine.status()
    assert status["status"] == "ok"

    print("[PASS] OI-054 Oracle Consensus Intelligence Engine")
    print({
        "consensus": result["consensus"],
        "votes": result["votes"],
        "explanation": result["explanation"],
    })


if __name__ == "__main__":
    test_oi_054_oracle_consensus_intelligence_engine()
