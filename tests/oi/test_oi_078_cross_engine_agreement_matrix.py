from qseries_v2.oracle_intelligence.cross_engine_agreement_matrix import CrossEngineAgreementMatrix


def test_oi_078_cross_engine_agreement_matrix():
    matrix = CrossEngineAgreementMatrix()

    packet = {
        "market_ticker": "AGREE-TEST",
        "consensus_votes": [
            {"engine": "case_reasoning_engine", "side": "YES", "confidence": 90, "weight": 0.24},
            {"engine": "outcome_distribution_engine", "side": "YES", "confidence": 86, "weight": 0.24},
            {"engine": "analog_retrieval_engine", "side": "NO", "confidence": 70, "weight": 0.18},
            {"engine": "market_dna_engine", "side": "YES", "confidence": 78, "weight": 0.10},
        ],
    }

    result = matrix.analyze_consensus_packet(packet, actual_side="YES")

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["market_ticker"] == "AGREE-TEST"
    assert result["vote_count"] == 4
    assert result["pair_count"] == 6
    assert result["summary"]["agreement_pairs"] == 3
    assert result["summary"]["disagreement_pairs"] == 3
    assert result["consensus_diversity"]["engine_count"] == 4
    assert "case_reasoning_engine" in result["matrix"]

    historical = matrix.historical_matrix()
    assert historical["status"] == "ok"
    assert historical["pair_count"] == 6
    assert historical["strongest_pair"] is not None
    assert "recommended_pair_boosts" in historical

    status = matrix.status()
    assert status["status"] == "ok"
    assert status["records"] == 6

    print("[PASS] OI-078 Cross-Engine Agreement Matrix")
    print({
        "pair_count": result["pair_count"],
        "diversity": result["consensus_diversity"],
        "strongest_pair": historical["strongest_pair"],
        "weakest_pair": historical["weakest_pair"],
    })


if __name__ == "__main__":
    test_oi_078_cross_engine_agreement_matrix()
