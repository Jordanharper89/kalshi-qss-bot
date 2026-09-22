
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
