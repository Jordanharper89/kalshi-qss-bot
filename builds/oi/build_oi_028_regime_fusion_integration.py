from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
TEST_FILE = ROOT / "test_oi_028_regime_fusion_integration.py"

FUSION_FILE = OI_DIR / "multi_factor_intelligence_fusion_engine.py"

if not FUSION_FILE.exists():
    raise FileNotFoundError("Missing OI-026 fusion engine. Install OI-026 first.")

FUSION_FILE.write_text(textwrap.dedent(r'''
"""
OI-026 / OI-028 Multi-Factor Intelligence Fusion Engine

OI-026:
- Fuse rhythm, baseline, and pattern intelligence.

OI-028:
- Adds market regime intelligence from OI-027 as a first-class component.

Read-only analysis only.
No execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


DEFAULT_WEIGHTS = {
    "rhythm": 0.17,
    "baseline": 0.22,
    "pattern": 0.30,
    "historical_confidence": 0.10,
    "data_quality": 0.08,
    "regime": 0.13,
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


@dataclass
class FusionPacket:
    module: str
    status: str
    generated_at: str
    market: Dict[str, Any]
    component_scores: Dict[str, Any]
    weights: Dict[str, float]
    overall_score: Dict[str, Any]
    explanation: List[str]
    source_status: Dict[str, Any]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MultiFactorIntelligenceFusionEngine:
    """
    Oracle meta-analysis engine.

    Fuses:
    - Rhythm
    - Baseline
    - Pattern recognition
    - Historical confidence
    - Data quality
    - Market regime

    This engine does not execute trades.
    """

    def __init__(
        self,
        rhythm_service=None,
        baseline_engine=None,
        pattern_engine=None,
        regime_engine=None,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.rhythm_service = rhythm_service
        self.baseline_engine = baseline_engine
        self.pattern_engine = pattern_engine
        self.regime_engine = regime_engine
        self.weights = self._normalize_weights(weights or DEFAULT_WEIGHTS)
        self.last_packet: Optional[Dict[str, Any]] = None

        if self.rhythm_service is None:
            try:
                from .oracle_rhythm_service import oracle_rhythm_service
                self.rhythm_service = oracle_rhythm_service
            except Exception:
                pass

        if self.baseline_engine is None:
            try:
                from .historical_market_baseline_engine import oracle_market_baseline_engine
                self.baseline_engine = oracle_market_baseline_engine
            except Exception:
                pass

        if self.pattern_engine is None:
            try:
                from .historical_pattern_recognition_engine import oracle_pattern_engine
                self.pattern_engine = oracle_pattern_engine
            except Exception:
                pass

        if self.regime_engine is None:
            try:
                from .market_regime_detection_engine import oracle_regime_engine
                self.regime_engine = oracle_regime_engine
            except Exception:
                pass

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "OI-028 Regime Fusion Integration",
            "status": "ok",
            "rhythm_service_ready": self.rhythm_service is not None,
            "baseline_engine_ready": self.baseline_engine is not None,
            "pattern_engine_ready": self.pattern_engine is not None,
            "regime_engine_ready": self.regime_engine is not None,
            "weights": self.weights,
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def analyze_market(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        rhythm_context = self._get_rhythm_context()
        baseline_comparison = self._get_baseline_comparison(live_market)
        pattern_result = self._get_pattern_result(live_market)
        regime_result = self._get_regime_result(live_market)

        scores = self._component_scores(
            rhythm_context=rhythm_context,
            baseline_comparison=baseline_comparison,
            pattern_result=pattern_result,
            regime_result=regime_result,
        )

        overall = self._overall_score(scores)
        explanation = self._explain_from_sources(
            scores,
            rhythm_context,
            baseline_comparison,
            pattern_result,
            regime_result,
        )

        packet = FusionPacket(
            module="OI-028 Regime Fusion Integration",
            status="ok",
            generated_at=self._now(),
            market=self._market_identity(live_market),
            component_scores=scores,
            weights=self.weights,
            overall_score=overall,
            explanation=explanation,
            source_status={
                "rhythm": rhythm_context.get("status", "unknown"),
                "baseline": baseline_comparison.get("status", "unknown"),
                "pattern": pattern_result.get("status", "unknown"),
                "regime": regime_result.get("status", "unknown"),
            },
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_packet = packet
        return packet

    def fusion_packet(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        return self.analyze_market(live_market)

    def component_scores(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        return self.analyze_market(live_market).get("component_scores", {})

    def explain(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        packet = self.analyze_market(live_market)
        return {
            "module": "OI-028 Regime Fusion Integration",
            "status": packet.get("status"),
            "market": packet.get("market"),
            "overall_score": packet.get("overall_score"),
            "explanation": packet.get("explanation", []),
            "read_only": True,
            "execution_allowed": False,
        }

    def _get_rhythm_context(self) -> Dict[str, Any]:
        if self.rhythm_service is None:
            return {"status": "missing_rhythm_service"}

        try:
            if hasattr(self.rhythm_service, "get_oracle_context"):
                return self.rhythm_service.get_oracle_context()
            if hasattr(self.rhythm_service, "api_payload"):
                payload = self.rhythm_service.api_payload()
                return payload.get("context", payload)
        except Exception as exc:
            return {"status": "rhythm_error", "error": str(exc)}

        return {"status": "invalid_rhythm_service"}

    def _get_baseline_comparison(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.baseline_engine is None:
            return {"status": "missing_baseline_engine"}

        try:
            if hasattr(self.baseline_engine, "compare_live_market"):
                return self.baseline_engine.compare_live_market(live_market)
        except Exception as exc:
            return {"status": "baseline_error", "error": str(exc)}

        return {"status": "invalid_baseline_engine"}

    def _get_pattern_result(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.pattern_engine is None:
            return {"status": "missing_pattern_engine"}

        try:
            if hasattr(self.pattern_engine, "find_similar_markets"):
                return self.pattern_engine.find_similar_markets(live_market)
            if hasattr(self.pattern_engine, "compare_pattern"):
                return self.pattern_engine.compare_pattern(live_market)
        except Exception as exc:
            return {"status": "pattern_error", "error": str(exc)}

        return {"status": "invalid_pattern_engine"}

    def _get_regime_result(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.regime_engine is None:
            return {"status": "missing_regime_engine"}

        try:
            if hasattr(self.regime_engine, "detect_regime"):
                return self.regime_engine.detect_regime(live_market)
            if hasattr(self.regime_engine, "get_regime"):
                return self.regime_engine.get_regime()
        except Exception as exc:
            return {"status": "regime_error", "error": str(exc)}

        return {"status": "invalid_regime_engine"}

    def _component_scores(
        self,
        rhythm_context: Dict[str, Any],
        baseline_comparison: Dict[str, Any],
        pattern_result: Dict[str, Any],
        regime_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "rhythm": self._rhythm_score(rhythm_context),
            "baseline": self._baseline_score(baseline_comparison),
            "pattern": self._pattern_score(pattern_result),
            "historical_confidence": self._historical_confidence_score(pattern_result),
            "data_quality": self._data_quality_score(pattern_result, baseline_comparison, regime_result),
            "regime": self._regime_score(regime_result),
        }

    def _rhythm_score(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if context.get("status") not in {"ok", None} and not context.get("market_clock"):
            return {"score": 0.0, "label": "missing", "details": "Rhythm context unavailable."}

        clock = context.get("market_clock", {}) or {}
        activity = clock.get("best_activity_hours", []) or []
        volume = clock.get("highest_volume_hours", []) or []
        liquidity = clock.get("strongest_liquidity_hours", []) or []

        raw = min(100.0, (len(activity) * 25.0) + (len(volume) * 20.0) + (len(liquidity) * 20.0))
        if raw == 0 and context.get("summary"):
            raw = 50.0

        return {
            "score": round(_clamp(raw), 4),
            "label": self._label(raw),
            "details": "Rhythm score reflects timing, activity, volume, and liquidity context.",
        }

    def _baseline_score(self, comparison: Dict[str, Any]) -> Dict[str, Any]:
        abnormality = comparison.get("abnormality_score", {}) or {}
        score = _safe_float(abnormality.get("score"))

        return {
            "score": round(_clamp(score), 4),
            "label": abnormality.get("label") or self._label(score),
            "details": comparison.get("interpretation", "Baseline comparison unavailable."),
        }

    def _pattern_score(self, result: Dict[str, Any]) -> Dict[str, Any]:
        top_matches = result.get("top_matches", []) or []
        if top_matches:
            score = _safe_float(top_matches[0].get("similarity"))
        else:
            score = _safe_float((result.get("pattern_summary") or {}).get("average_similarity"))

        return {
            "score": round(_clamp(score), 4),
            "label": self._label(score),
            "details": f"Pattern score based on {len(top_matches)} returned top matches.",
        }

    def _historical_confidence_score(self, result: Dict[str, Any]) -> Dict[str, Any]:
        conf = result.get("confidence", {}) or {}
        score = _safe_float(conf.get("score"))

        return {
            "score": round(_clamp(score), 4),
            "label": conf.get("label") or self._label(score),
            "details": f"Sample size: {conf.get('sample_size', 0)}.",
        }

    def _data_quality_score(
        self,
        pattern_result: Dict[str, Any],
        baseline_comparison: Dict[str, Any],
        regime_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        conf = pattern_result.get("confidence", {}) or {}
        pattern_quality = _safe_float(conf.get("data_quality_score"))

        checked = _safe_float((baseline_comparison.get("abnormality_score") or {}).get("metrics_checked"))
        baseline_quality = min(100.0, checked * 4.0)

        regime_sample = _safe_float((regime_result.get("regime_features") or {}).get("sample_size"))
        regime_quality = min(100.0, regime_sample / 2.5)

        score = max(pattern_quality, baseline_quality, regime_quality)

        return {
            "score": round(_clamp(score), 4),
            "label": self._label(score),
            "details": conf.get("data_quality") or "Data quality estimated from pattern, baseline, and regime samples.",
        }

    def _regime_score(self, result: Dict[str, Any]) -> Dict[str, Any]:
        current = result.get("current_regime", {}) or {}
        score = _safe_float(current.get("score"))
        confidence = current.get("confidence", {}) or {}
        confidence_score = _safe_float(confidence.get("score"))

        blended = score
        if confidence_score:
            blended = (score * 0.65) + (confidence_score * 0.35)

        return {
            "score": round(_clamp(blended), 4),
            "label": current.get("label") or self._label(blended),
            "regime": current.get("name"),
            "details": current.get("description", "Regime context unavailable."),
        }

    def _overall_score(self, scores: Dict[str, Any]) -> Dict[str, Any]:
        total = 0.0

        for key, weight in self.weights.items():
            total += _safe_float((scores.get(key) or {}).get("score")) * weight

        total = round(_clamp(total), 4)

        return {
            "score": total,
            "label": self._label(total),
            "interpretation": self._overall_interpretation(total),
        }

    def _explain_from_sources(
        self,
        scores: Dict[str, Any],
        rhythm_context: Dict[str, Any],
        baseline_comparison: Dict[str, Any],
        pattern_result: Dict[str, Any],
        regime_result: Dict[str, Any],
    ) -> List[str]:
        lines = []

        for key in ["rhythm", "baseline", "pattern", "historical_confidence", "data_quality", "regime"]:
            data = scores.get(key, {})
            lines.append(f"{key.replace('_', ' ').title()} score: {data.get('score')} ({data.get('label')}).")

        regime = (regime_result.get("current_regime") or {}).get("name")
        if regime:
            lines.append(f"Detected market regime: {regime}.")

        pattern_summary = pattern_result.get("pattern_summary", {}) or {}
        if pattern_summary.get("occurrences"):
            lines.append(f"Similar historical pattern occurrences: {pattern_summary.get('occurrences')}.")

        baseline_text = baseline_comparison.get("interpretation")
        if baseline_text:
            lines.append(baseline_text)

        rhythm_summary = rhythm_context.get("summary", []) or []
        if rhythm_summary:
            lines.append(str(rhythm_summary[0]))

        lines.append("Read-only Oracle analysis only. Execution remains disabled.")

        return lines

    def _market_identity(self, market: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ticker": market.get("ticker") or market.get("market_ticker") or market.get("symbol"),
            "category": market.get("category") or market.get("market_category") or "unknown",
            "timestamp": market.get("timestamp"),
        }

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        cleaned = {key: max(0.0, _safe_float(value)) for key, value in weights.items()}
        total = sum(cleaned.values())

        if total <= 0:
            return DEFAULT_WEIGHTS.copy()

        return {key: round(value / total, 6) for key, value in cleaned.items()}

    def _label(self, score: float) -> str:
        score = _safe_float(score)

        if score >= 85:
            return "very_high"
        if score >= 70:
            return "high"
        if score >= 50:
            return "moderate"
        if score >= 25:
            return "low"
        return "thin"

    def _overall_interpretation(self, score: float) -> str:
        if score >= 85:
            return "Oracle intelligence alignment is very high across fused historical and regime factors."
        if score >= 70:
            return "Oracle intelligence alignment is high across fused historical and regime factors."
        if score >= 50:
            return "Oracle intelligence alignment is moderate across fused historical and regime factors."
        if score >= 25:
            return "Oracle intelligence alignment is limited across fused historical and regime factors."
        return "Oracle intelligence alignment is thin or missing."

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_fusion_engine = MultiFactorIntelligenceFusionEngine()
''').strip() + "\n", encoding="utf-8")

TEST_FILE.write_text(textwrap.dedent(r'''
from qseries_v2.oracle_intelligence.multi_factor_intelligence_fusion_engine import MultiFactorIntelligenceFusionEngine


class FakeRhythmService:
    def get_oracle_context(self):
        return {
            "status": "ok",
            "context_type": "market_rhythm",
            "summary": ["Oracle analyzed rhythm behavior from historical market records."],
            "market_clock": {
                "best_activity_hours": [{"key": "14", "score": 900}],
                "highest_volume_hours": [{"key": "14", "score": 800}],
                "strongest_liquidity_hours": [{"key": "15", "score": 3000}],
            },
            "read_only": True,
            "execution_allowed": False,
        }


class FakeBaselineEngine:
    def compare_live_market(self, live_market):
        return {
            "status": "ok",
            "abnormality_score": {
                "score": 82.5,
                "label": "high",
                "abnormal_metrics": 12,
                "metrics_checked": 24,
            },
            "interpretation": "Current market behavior is meaningfully unusual versus historical baselines.",
            "read_only": True,
            "execution_allowed": False,
        }


class FakePatternEngine:
    def find_similar_markets(self, live_market):
        return {
            "status": "ok",
            "matches_found": 42,
            "top_matches": [
                {"similarity": 94.8, "label": "extremely_similar"},
                {"similarity": 91.2, "label": "extremely_similar"},
            ],
            "pattern_summary": {
                "occurrences": 42,
                "average_similarity": 88.4,
            },
            "confidence": {
                "score": 89.7,
                "label": "very_high",
                "sample_size": 42,
                "data_quality": "excellent",
                "data_quality_score": 96.0,
                "historical_consistency": 91.0,
            },
            "read_only": True,
            "execution_allowed": False,
        }


class FakeRegimeEngine:
    def detect_regime(self, live_market):
        return {
            "status": "ok",
            "rows_analyzed": 300,
            "current_regime": {
                "name": "high_liquidity_low_volatility",
                "score": 87.0,
                "label": "very_high",
                "confidence": {
                    "score": 91.0,
                    "label": "very_high",
                    "sample_size": 250,
                },
                "description": "Deep liquidity with controlled price movement.",
            },
            "regime_features": {
                "sample_size": 250,
                "avg_liquidity": 3500,
                "avg_volume": 1800,
                "avg_spread": 4.0,
                "price_volatility": 8.2,
            },
            "oracle_context": {
                "context_type": "market_regime",
                "status": "ok",
            },
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_028_regime_fusion_integration():
    engine = MultiFactorIntelligenceFusionEngine(
        rhythm_service=FakeRhythmService(),
        baseline_engine=FakeBaselineEngine(),
        pattern_engine=FakePatternEngine(),
        regime_engine=FakeRegimeEngine(),
    )

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["regime_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
        "yes_price": 52,
        "volume": 1200,
        "liquidity": 3000,
    }

    packet = engine.analyze_market(live_market)

    assert packet["module"] == "OI-028 Regime Fusion Integration"
    assert packet["status"] == "ok"
    assert packet["component_scores"]["regime"]["score"] > 85
    assert packet["component_scores"]["regime"]["regime"] == "high_liquidity_low_volatility"
    assert packet["source_status"]["regime"] == "ok"
    assert packet["overall_score"]["score"] > 80
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    explanation = engine.explain(live_market)
    assert "Detected market regime" in " ".join(explanation["explanation"])
    assert explanation["read_only"] is True
    assert explanation["execution_allowed"] is False

    print("[PASS] OI-028 Regime Fusion Integration")
    print({
        "overall_score": packet["overall_score"],
        "regime_score": packet["component_scores"]["regime"],
        "source_status": packet["source_status"],
    })


if __name__ == "__main__":
    test_oi_028_regime_fusion_integration()
''').strip() + "\n", encoding="utf-8")

print("========================================")
print(" OI-028 INSTALLER")
print(" Regime Fusion Integration")
print("========================================")
print(f"[OK] Patched {FUSION_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print("")
print("[DONE] OI-028 installed")
print("")
print("Run:")
print("python test_oi_028_regime_fusion_integration.py")