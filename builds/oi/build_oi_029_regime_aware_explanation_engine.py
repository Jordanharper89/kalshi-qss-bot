from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
TEST_FILE = ROOT / "test_oi_029_regime_aware_explanation_engine.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

ENGINE = OI_DIR / "regime_aware_explanation_engine.py"

ENGINE.write_text(textwrap.dedent(r'''
"""
OI-029 Regime-Aware Explanation Engine

Purpose:
- Convert OI-028 fusion packets into clean Oracle explanations.
- Produce summary, bullet reasoning, risk/context notes, and API-safe payloads.
- Read-only.
- No execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


@dataclass
class ExplanationPacket:
    module: str
    status: str
    generated_at: str
    market: Dict[str, Any]
    headline: str
    summary: str
    component_breakdown: List[Dict[str, Any]]
    reasoning_bullets: List[str]
    context_notes: List[str]
    risk_notes: List[str]
    oracle_report_text: str
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RegimeAwareExplanationEngine:
    """
    Converts fused Oracle intelligence into human-readable explanation.
    """

    def __init__(self, fusion_engine=None):
        self.fusion_engine = fusion_engine
        self.last_packet: Optional[Dict[str, Any]] = None

        if self.fusion_engine is None:
            try:
                from .multi_factor_intelligence_fusion_engine import oracle_fusion_engine
                self.fusion_engine = oracle_fusion_engine
            except Exception:
                pass

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "OI-029 Regime-Aware Explanation Engine",
            "status": "ok" if self.fusion_engine is not None else "missing_fusion_engine",
            "fusion_engine_ready": self.fusion_engine is not None,
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def explain_market(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        fusion = self._get_fusion_packet(live_market)
        packet = self.from_fusion_packet(fusion)
        self.last_packet = packet
        return packet

    def from_fusion_packet(self, fusion: Dict[str, Any]) -> Dict[str, Any]:
        market = fusion.get("market", {}) or {}
        overall = fusion.get("overall_score", {}) or {}
        components = fusion.get("component_scores", {}) or {}

        headline = self._headline(market, overall, components)
        summary = self._summary(overall, components)
        breakdown = self._component_breakdown(components)
        bullets = self._reasoning_bullets(fusion, components)
        context_notes = self._context_notes(fusion, components)
        risk_notes = self._risk_notes(fusion, components)
        report_text = self._report_text(headline, summary, breakdown, bullets, context_notes, risk_notes)

        packet = ExplanationPacket(
            module="OI-029 Regime-Aware Explanation Engine",
            status=fusion.get("status", "unknown"),
            generated_at=self._now(),
            market=market,
            headline=headline,
            summary=summary,
            component_breakdown=breakdown,
            reasoning_bullets=bullets,
            context_notes=context_notes,
            risk_notes=risk_notes,
            oracle_report_text=report_text,
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        return packet

    def api_payload(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        packet = self.explain_market(live_market)
        return {
            "module": "oracle_regime_aware_explanation_payload",
            "status": packet.get("status"),
            "market": packet.get("market"),
            "headline": packet.get("headline"),
            "summary": packet.get("summary"),
            "reasoning": packet.get("reasoning_bullets"),
            "context_notes": packet.get("context_notes"),
            "risk_notes": packet.get("risk_notes"),
            "read_only": True,
            "execution_allowed": False,
        }

    def latest(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return {
                "module": "OI-029 Regime-Aware Explanation Engine",
                "status": "no_explanation_yet",
                "read_only": True,
                "execution_allowed": False,
            }
        return self.last_packet

    def _get_fusion_packet(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        if self.fusion_engine is None:
            return {
                "module": "missing_fusion_engine",
                "status": "missing_fusion_engine",
                "market": {
                    "ticker": live_market.get("ticker") or live_market.get("market_ticker") or live_market.get("symbol"),
                    "category": live_market.get("category") or live_market.get("market_category") or "unknown",
                    "timestamp": live_market.get("timestamp"),
                },
                "overall_score": {"score": 0.0, "label": "thin"},
                "component_scores": {},
                "explanation": ["Fusion engine unavailable."],
                "read_only": True,
                "execution_allowed": False,
            }

        if hasattr(self.fusion_engine, "analyze_market"):
            return self.fusion_engine.analyze_market(live_market)

        if hasattr(self.fusion_engine, "fusion_packet"):
            return self.fusion_engine.fusion_packet(live_market)

        return {
            "status": "invalid_fusion_engine",
            "market": {},
            "overall_score": {"score": 0.0, "label": "thin"},
            "component_scores": {},
            "read_only": True,
            "execution_allowed": False,
        }

    def _headline(self, market: Dict[str, Any], overall: Dict[str, Any], components: Dict[str, Any]) -> str:
        ticker = market.get("ticker") or "Unknown Market"
        score = _safe_float(overall.get("score"))
        label = overall.get("label") or self._label(score)

        regime = (components.get("regime") or {}).get("regime")
        if regime:
            return f"{ticker}: Oracle alignment {label} under {regime} regime"

        return f"{ticker}: Oracle alignment {label}"

    def _summary(self, overall: Dict[str, Any], components: Dict[str, Any]) -> str:
        score = _safe_float(overall.get("score"))
        label = overall.get("label") or self._label(score)

        strongest = self._strongest_component(components)
        weakest = self._weakest_component(components)

        return (
            f"Oracle Intelligence score is {round(score, 4)} ({label}). "
            f"Strongest factor: {strongest}. Weakest factor: {weakest}. "
            "This is read-only analytical context and not an execution command."
        )

    def _component_breakdown(self, components: Dict[str, Any]) -> List[Dict[str, Any]]:
        out = []
        for name, data in components.items():
            out.append({
                "component": name,
                "score": _safe_float(data.get("score")),
                "label": data.get("label") or self._label(_safe_float(data.get("score"))),
                "details": data.get("details"),
                "regime": data.get("regime"),
            })

        return sorted(out, key=lambda x: x["score"], reverse=True)

    def _reasoning_bullets(self, fusion: Dict[str, Any], components: Dict[str, Any]) -> List[str]:
        bullets = []

        for item in self._component_breakdown(components):
            bullets.append(
                f"{item['component'].replace('_', ' ').title()} scored {item['score']} ({item['label']})."
            )

        for line in fusion.get("explanation", [])[:6]:
            if line and line not in bullets:
                bullets.append(str(line))

        return bullets[:12]

    def _context_notes(self, fusion: Dict[str, Any], components: Dict[str, Any]) -> List[str]:
        notes = []

        regime = (components.get("regime") or {}).get("regime")
        if regime:
            notes.append(f"Market regime context: {regime}.")

        source_status = fusion.get("source_status", {}) or {}
        if source_status:
            notes.append(f"Source status: {source_status}.")

        overall = fusion.get("overall_score", {}) or {}
        interpretation = overall.get("interpretation")
        if interpretation:
            notes.append(str(interpretation))

        return notes or ["No additional context notes available."]

    def _risk_notes(self, fusion: Dict[str, Any], components: Dict[str, Any]) -> List[str]:
        notes = [
            "Oracle explanation is analysis-only.",
            "Execution remains disabled inside Oracle.",
        ]

        data_quality = _safe_float((components.get("data_quality") or {}).get("score"))
        if data_quality < 50:
            notes.append("Data quality is limited; interpretation should be treated as lower confidence.")

        baseline = _safe_float((components.get("baseline") or {}).get("score"))
        if baseline >= 85:
            notes.append("Baseline deviation is extreme; abnormal behavior can increase uncertainty.")

        regime = _safe_float((components.get("regime") or {}).get("score"))
        if regime >= 85:
            notes.append("Regime score is very high; market environment may dominate individual signal behavior.")

        return notes

    def _report_text(
        self,
        headline: str,
        summary: str,
        breakdown: List[Dict[str, Any]],
        bullets: List[str],
        context_notes: List[str],
        risk_notes: List[str],
    ) -> str:
        lines = [
            headline,
            "",
            summary,
            "",
            "Component Breakdown:",
        ]

        for item in breakdown:
            lines.append(f"- {item['component']}: {item['score']} ({item['label']})")

        lines.append("")
        lines.append("Oracle Reasoning:")
        for bullet in bullets:
            lines.append(f"- {bullet}")

        lines.append("")
        lines.append("Context Notes:")
        for note in context_notes:
            lines.append(f"- {note}")

        lines.append("")
        lines.append("Risk / Safety Notes:")
        for note in risk_notes:
            lines.append(f"- {note}")

        return "\n".join(lines)

    def _strongest_component(self, components: Dict[str, Any]) -> str:
        if not components:
            return "none"
        name, data = max(components.items(), key=lambda kv: _safe_float((kv[1] or {}).get("score")))
        return f"{name} ({_safe_float(data.get('score'))})"

    def _weakest_component(self, components: Dict[str, Any]) -> str:
        if not components:
            return "none"
        name, data = min(components.items(), key=lambda kv: _safe_float((kv[1] or {}).get("score")))
        return f"{name} ({_safe_float(data.get('score'))})"

    def _label(self, score: float) -> str:
        if score >= 85:
            return "very_high"
        if score >= 70:
            return "high"
        if score >= 50:
            return "moderate"
        if score >= 25:
            return "low"
        return "thin"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_explanation_engine = RegimeAwareExplanationEngine()
''').strip() + "\n", encoding="utf-8")

TEST_FILE.write_text(textwrap.dedent(r'''
from qseries_v2.oracle_intelligence.regime_aware_explanation_engine import RegimeAwareExplanationEngine


class FakeFusionEngine:
    def analyze_market(self, live_market):
        return {
            "module": "OI-028 Regime Fusion Integration",
            "status": "ok",
            "market": {
                "ticker": live_market.get("ticker"),
                "category": live_market.get("category"),
                "timestamp": live_market.get("timestamp"),
            },
            "component_scores": {
                "rhythm": {"score": 65.0, "label": "moderate", "details": "Rhythm context available."},
                "baseline": {"score": 82.5, "label": "high", "details": "Behavior is unusual versus baseline."},
                "pattern": {"score": 94.8, "label": "very_high", "details": "Strong historical match."},
                "historical_confidence": {"score": 89.7, "label": "very_high", "details": "Sample size: 42."},
                "data_quality": {"score": 96.0, "label": "very_high", "details": "Excellent."},
                "regime": {
                    "score": 88.4,
                    "label": "very_high",
                    "regime": "high_liquidity_low_volatility",
                    "details": "Deep liquidity with controlled movement.",
                },
            },
            "overall_score": {
                "score": 86.25,
                "label": "very_high",
                "interpretation": "Oracle intelligence alignment is very high across fused historical and regime factors.",
            },
            "explanation": [
                "Detected market regime: high_liquidity_low_volatility.",
                "Similar historical pattern occurrences: 42.",
                "Current market behavior is meaningfully unusual versus historical baselines.",
                "Read-only Oracle analysis only. Execution remains disabled.",
            ],
            "source_status": {
                "rhythm": "ok",
                "baseline": "ok",
                "pattern": "ok",
                "regime": "ok",
            },
            "read_only": True,
            "execution_allowed": False,
        }


def test_oi_029_regime_aware_explanation_engine():
    engine = RegimeAwareExplanationEngine(fusion_engine=FakeFusionEngine())

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["fusion_engine_ready"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "BTC-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T14:30:00+00:00",
    }

    packet = engine.explain_market(live_market)

    assert packet["status"] == "ok"
    assert packet["headline"]
    assert "BTC-TEST" in packet["headline"]
    assert "high_liquidity_low_volatility" in packet["headline"]
    assert packet["summary"]
    assert packet["component_breakdown"]
    assert packet["component_breakdown"][0]["component"] in {"data_quality", "pattern", "historical_confidence", "regime"}
    assert packet["reasoning_bullets"]
    assert packet["context_notes"]
    assert packet["risk_notes"]
    assert packet["oracle_report_text"]
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    payload = engine.api_payload(live_market)
    assert payload["module"] == "oracle_regime_aware_explanation_payload"
    assert payload["headline"]
    assert payload["reasoning"]
    assert payload["read_only"] is True
    assert payload["execution_allowed"] is False

    latest = engine.latest()
    assert latest["headline"] == packet["headline"]

    print("[PASS] OI-029 Regime-Aware Explanation Engine")
    print({
        "headline": packet["headline"],
        "top_component": packet["component_breakdown"][0],
        "risk_notes": len(packet["risk_notes"]),
    })


if __name__ == "__main__":
    test_oi_029_regime_aware_explanation_engine()
''').strip() + "\n", encoding="utf-8")

INIT = OI_DIR / "__init__.py"
content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""

line = "from .regime_aware_explanation_engine import RegimeAwareExplanationEngine, oracle_explanation_engine\n"
if line not in content:
    content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")

print("========================================")
print(" OI-029 INSTALLER")
print(" Regime-Aware Explanation Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT}")
print("")
print("[DONE] OI-029 installed")
print("")
print("Run:")
print("python test_oi_029_regime_aware_explanation_engine.py")