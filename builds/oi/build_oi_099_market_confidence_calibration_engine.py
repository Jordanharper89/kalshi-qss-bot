from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "market_confidence_calibration_engine.py"
TEST = ROOT / "test_oi_099_market_confidence_calibration_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-099 Market Confidence Calibration Engine
Read-only Oracle Intelligence module.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import math, time


def _f(v, d=0.0):
    try:
        x = float(v)
        return d if math.isnan(x) or math.isinf(x) else x
    except Exception:
        return d


def _s(v, d=""):
    return d if v is None else str(v)


def _clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(x)))


@dataclass
class CalibratedConfidence:
    market: str
    raw_confidence: float
    calibrated_confidence: float
    calibration_delta: float
    reliability_tier: str
    reason: str

    def to_dict(self):
        return asdict(self)


class MarketConfidenceCalibrationEngine:
    module = "oi_099_market_confidence_calibration_engine"

    def __init__(self):
        self.last_report = {}

    def calibrate_confidence(self, oracle_items=None, historical_performance=None):
        oracle_items = oracle_items or []
        historical_performance = historical_performance or {}

        rows = []
        for item in oracle_items:
            if not isinstance(item, dict):
                continue

            market = _s(item.get("market") or item.get("label") or item.get("ticker"), "UNKNOWN")
            raw = _f(item.get("confidence"), 50.0)
            signal_type = _s(item.get("signal_type") or item.get("type"), "default")

            perf = historical_performance.get(market, {})
            global_perf = historical_performance.get(signal_type, {})
            default_perf = historical_performance.get("default", {})

            win_rate = _f(perf.get("win_rate", global_perf.get("win_rate", default_perf.get("win_rate", 0.50)))) * 100
            sample_size = _f(perf.get("sample_size", global_perf.get("sample_size", default_perf.get("sample_size", 10))))
            avg_error = _f(perf.get("avg_error", global_perf.get("avg_error", default_perf.get("avg_error", 18))))

            sample_weight = _clamp(sample_size / 100 * 100)
            reliability = _clamp(win_rate * 0.55 + sample_weight * 0.25 + (100 - avg_error) * 0.20)
            calibrated = _clamp(raw * 0.60 + reliability * 0.40)

            rows.append(CalibratedConfidence(
                market=market,
                raw_confidence=round(raw, 4),
                calibrated_confidence=round(calibrated, 4),
                calibration_delta=round(calibrated - raw, 4),
                reliability_tier=self._tier(reliability),
                reason=f"Confidence calibrated using win rate {round(win_rate,2)}%, sample size {int(sample_size)}, and avg error {round(avg_error,2)}.",
            ))

        rows.sort(key=lambda x: x.calibrated_confidence, reverse=True)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "item_count": len(rows),
            "calibrated_items": [r.to_dict() for r in rows],
            "top_confidence": rows[0].to_dict() if rows else None,
            "reliability_counts": self._counts(rows),
        }
        self.last_report = report
        return report

    def _tier(self, score):
        if score >= 80:
            return "excellent"
        if score >= 65:
            return "strong"
        if score >= 45:
            return "moderate"
        if score >= 25:
            return "weak"
        return "poor"

    def _counts(self, rows):
        out = {}
        for r in rows:
            out[r.reliability_tier] = out.get(r.reliability_tier, 0) + 1
        return out

    def diagnostics(self):
        return {"module": self.module, "status": "ok", "has_report": bool(self.last_report), "item_count": self.last_report.get("item_count", 0), "read_only": True}


market_confidence_calibration_engine = MarketConfidenceCalibrationEngine()
''', encoding="utf-8")

TEST.write_text(r'''
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
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .market_confidence_calibration_engine import market_confidence_calibration_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-099 INSTALLER")
print(" Market Confidence Calibration Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-099 installed")
print()
print("Run:")
print("py test_oi_099_market_confidence_calibration_engine.py")