from qseries_v2.oracle_intelligence.market_dna_fingerprinting_engine import market_dna_fingerprinting_engine


def test_oi_046_market_dna_fingerprinting_engine():
    setup_a = {
        "ticker": "DNA-A",
        "price": 79,
        "implied_probability": 79,
        "volume": 12000,
        "liquidity": 25000,
        "spread": 2,
        "momentum": 8,
        "volatility": 4,
        "time_to_expiration_minutes": 180,
        "category": "crypto",
        "regime": "trend",
        "pattern_name": "strong_momentum",
        "tags": ["momentum", "yes"],
    }

    setup_b = dict(setup_a)
    setup_b["ticker"] = "DNA-B"
    setup_b["price"] = 77

    setup_c = {
        "ticker": "DNA-C",
        "price": 31,
        "implied_probability": 31,
        "volume": 700,
        "liquidity": 900,
        "spread": 12,
        "momentum": -4,
        "volatility": 10,
        "time_to_expiration_minutes": 600,
        "category": "weather",
        "regime": "chop",
        "pattern_name": "weak_reversal",
        "tags": ["weak", "no"],
    }

    fp_a = market_dna_fingerprinting_engine.fingerprint_market(setup_a)
    fp_b = market_dna_fingerprinting_engine.fingerprint_market(setup_b)
    fp_c = market_dna_fingerprinting_engine.fingerprint_market(setup_c)

    assert fp_a["status"] == "ok"
    assert fp_a["read_only"] is True
    assert fp_a["dna_id"].startswith("dna_")
    assert fp_a["dna_family"].startswith("family_")
    assert len(fp_a["traits"]) > 0

    close = market_dna_fingerprinting_engine.compare_fingerprints(fp_a, fp_b)
    far = market_dna_fingerprinting_engine.compare_fingerprints(fp_a, fp_c)

    assert close["dna_similarity"] > far["dna_similarity"]

    status = market_dna_fingerprinting_engine.status()
    assert status["status"] == "ok"

    print("[PASS] OI-046 Market DNA Fingerprinting Engine")
    print({
        "dna_a": fp_a["dna_id"],
        "family_a": fp_a["dna_family"],
        "close_similarity_pct": close["dna_similarity_pct"],
        "far_similarity_pct": far["dna_similarity_pct"],
    })


if __name__ == "__main__":
    test_oi_046_market_dna_fingerprinting_engine()
