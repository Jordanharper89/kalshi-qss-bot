
from qseries_v2.oracle_intelligence.market_confidence_calibration_engine import market_confidence_calibration_engine


def test_oi_099_market_confidence_calibration_engine():
    items = [
        {"market": "NASDAQ", "confidence": 82, "signal_type": "stability"},
        {"market": "AI-SECTOR", "confidence": 74, "signal_type": "recovery"},
        {"market": "FED-RATE", "confidence": 61, "signal_type": "stability"},
    ]
    history = {
        "NASDAQ": {"win_rate": 0.72, "sample_size": 140, "avg_error": 12},
        "recovery": {"win_rate": 0.58, "sample_size": 40, "avg_error": 20},
        "default": {"win_rate": 0.50, "sample_size": 10, "avg_error": 25},
    }

    report = market_confidence_calibration_engine.calibrate_confidence(items, history)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["item_count"] == 3
    assert report["calibrated_items"][0]["calibrated_confidence"] >= report["calibrated_items"][-1]["calibrated_confidence"]
    assert report["top_confidence"] is not None

    print("[PASS] OI-099 Market Confidence Calibration Engine")
    print({"items": report["item_count"], "top": report["top_confidence"], "counts": report["reliability_counts"]})


if __name__ == "__main__":
    test_oi_099_market_confidence_calibration_engine()
