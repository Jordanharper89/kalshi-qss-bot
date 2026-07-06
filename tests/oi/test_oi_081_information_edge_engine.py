from qseries_v2.oracle_intelligence.information_edge_engine import information_edge_engine


def test_oi_081_information_edge_engine():
    market = {
        "ticker": "INFO-EDGE-TEST",
        "price": 52,
        "price_delta_pct": 1,
        "volume": 50000,
        "previous_volume": 10000,
        "liquidity": 30000,
        "spread": 2,
        "cross_market_confirmation": 0.85,
    }

    information = {
        "headline": "Major catalyst released",
        "source": "official_feed",
        "source_tier": "official",
        "age_seconds": 45,
        "expected_price_move_pct": 8,
    }

    packet = {
        "research_quality_score": 90,
        "summary": {
            "expected_probability": 0.72,
            "research_quality_score": 90,
        },
        "signals": {
            "final_research_grade": "A",
        },
    }

    result = information_edge_engine.score_information_edge(market, information, packet)

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["ticker"] == "INFO-EDGE-TEST"
    assert result["information_edge_score"] >= 70
    assert result["edge_grade"] in {"A+", "A", "A-", "B+", "B"}
    assert result["execution_enabled"] is False
    assert "fresh_information" in result["reason_codes"]
    assert "reliable_source" in result["reason_codes"]

    batch = information_edge_engine.score_batch(
        markets=[market, {"ticker": "WEAK", "price": 90}],
        information_by_ticker={"INFO-EDGE-TEST": information},
        packets_by_ticker={"INFO-EDGE-TEST": packet},
    )

    assert batch["status"] == "ok"
    assert batch["markets_scored"] == 2
    assert batch["top_edges"][0]["ticker"] == "INFO-EDGE-TEST"

    status = information_edge_engine.status()
    assert status["status"] == "ok"

    print("[PASS] OI-081 Information Edge Engine")
    print({
        "score": result["information_edge_score"],
        "grade": result["edge_grade"],
        "level": result["edge_level"],
        "reasons": result["reason_codes"],
        "catchup_minutes": result["estimated_market_catchup_minutes"],
    })


if __name__ == "__main__":
    test_oi_081_information_edge_engine()
