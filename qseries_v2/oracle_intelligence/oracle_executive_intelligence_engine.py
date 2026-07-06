
"""
OI-113 Oracle Executive Intelligence Engine

Read-only executive synthesis layer.

Purpose:
- Convert Oracle Digest / Briefing / Decision Support outputs into executive intelligence.
- Produce concise executive status, priority themes, risk posture, action posture,
  and boardroom-ready summaries.
- Oracle remains strictly READ-ONLY. It never executes trades.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


@dataclass
class ExecutiveIntelligenceEngine:
    """
    Builds an executive-level read-only Oracle intelligence packet.
    """

    name: str = "OI-113 Oracle Executive Intelligence Engine"
    version: str = "1.0.0"
    read_only: bool = True
    history: List[Dict[str, Any]] = field(default_factory=list)

    def evaluate(self, oracle_digest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        digest = oracle_digest or {}

        risks = self._extract_risks(digest)
        priorities = self._extract_priorities(digest)
        themes = self._build_themes(digest, risks, priorities)

        executive_score = self._score(digest, risks, priorities)
        posture = self._posture(executive_score, risks)

        packet = {
            "module": "oracle_executive_intelligence_engine",
            "status": "ok",
            "read_only": True,
            "generated_at": _utc_now(),
            "executive_score": executive_score,
            "executive_posture": posture,
            "headline": self._headline(posture, executive_score),
            "priority_count": len(priorities),
            "risk_count": len(risks),
            "themes": themes,
            "top_priorities": priorities[:5],
            "top_risks": risks[:5],
            "executive_summary": self._summary(posture, executive_score, themes, risks, priorities),
            "recommended_oracle_focus": self._focus(posture, risks, priorities),
            "execution_permission": False,
            "execution_owner": "Q Series",
        }

        self.history.append(packet)
        return packet

    def _extract_risks(self, digest: Dict[str, Any]) -> List[Dict[str, Any]]:
        raw = []
        for key in ("risks", "top_risks", "risk_items", "alerts", "anomalies"):
            raw.extend(_as_list(digest.get(key)))

        risks = []
        for item in raw:
            if isinstance(item, dict):
                label = _text(item.get("label") or item.get("name") or item.get("type") or item.get("title"), "unnamed_risk")
                severity = _as_float(item.get("severity") or item.get("risk_score") or item.get("score") or item.get("confidence"), 50.0)
            else:
                label = _text(item, "unnamed_risk")
                severity = 50.0

            risks.append({
                "label": label,
                "severity": max(0.0, min(100.0, severity)),
            })

        return sorted(risks, key=lambda x: x["severity"], reverse=True)

    def _extract_priorities(self, digest: Dict[str, Any]) -> List[Dict[str, Any]]:
        raw = []
        for key in ("priorities", "top_priorities", "market_priority_queue", "attention_items", "digest_items"):
            raw.extend(_as_list(digest.get(key)))

        priorities = []
        for item in raw:
            if isinstance(item, dict):
                label = _text(item.get("label") or item.get("market") or item.get("name") or item.get("title"), "unnamed_priority")
                priority = _as_float(item.get("priority") or item.get("priority_score") or item.get("score") or item.get("confidence"), 50.0)
            else:
                label = _text(item, "unnamed_priority")
                priority = 50.0

            priorities.append({
                "label": label,
                "priority": max(0.0, min(100.0, priority)),
            })

        return sorted(priorities, key=lambda x: x["priority"], reverse=True)

    def _build_themes(
        self,
        digest: Dict[str, Any],
        risks: List[Dict[str, Any]],
        priorities: List[Dict[str, Any]],
    ) -> List[str]:
        themes = []

        for key in ("themes", "strategic_themes", "summary_themes"):
            for item in _as_list(digest.get(key)):
                clean = _text(item).strip()
                if clean and clean not in themes:
                    themes.append(clean)

        if risks and "Risk concentration requires review" not in themes:
            themes.append("Risk concentration requires review")

        if priorities and "Priority queue has actionable intelligence" not in themes:
            themes.append("Priority queue has actionable intelligence")

        if not themes:
            themes.append("Oracle intelligence stable with no dominant executive theme")

        return themes[:7]

    def _score(
        self,
        digest: Dict[str, Any],
        risks: List[Dict[str, Any]],
        priorities: List[Dict[str, Any]],
    ) -> float:
        base = _as_float(
            digest.get("digest_score")
            or digest.get("oracle_score")
            or digest.get("confidence")
            or digest.get("confidence_score"),
            70.0,
        )

        risk_drag = sum(r["severity"] for r in risks[:3]) / 15.0 if risks else 0.0
        priority_lift = sum(p["priority"] for p in priorities[:3]) / 30.0 if priorities else 0.0

        score = base - risk_drag + priority_lift
        return round(max(0.0, min(100.0, score)), 2)

    def _posture(self, score: float, risks: List[Dict[str, Any]]) -> str:
        max_risk = risks[0]["severity"] if risks else 0.0

        if max_risk >= 85 or score < 45:
            return "defensive"
        if max_risk >= 70 or score < 60:
            return "cautious"
        if score >= 80:
            return "aggressive_review"
        return "balanced_review"

    def _headline(self, posture: str, score: float) -> str:
        mapping = {
            "defensive": "Executive posture defensive; risk control is primary.",
            "cautious": "Executive posture cautious; selective review preferred.",
            "balanced_review": "Executive posture balanced; review top-ranked intelligence.",
            "aggressive_review": "Executive posture strong; high-priority intelligence deserves attention.",
        }
        return mapping.get(posture, f"Executive posture {posture}; score {score}.")

    def _summary(
        self,
        posture: str,
        score: float,
        themes: List[str],
        risks: List[Dict[str, Any]],
        priorities: List[Dict[str, Any]],
    ) -> str:
        top_theme = themes[0] if themes else "No dominant theme"
        top_risk = risks[0]["label"] if risks else "No major risk"
        top_priority = priorities[0]["label"] if priorities else "No major priority"

        return (
            f"Oracle executive score is {score} with posture '{posture}'. "
            f"Primary theme: {top_theme}. "
            f"Top priority: {top_priority}. "
            f"Top risk: {top_risk}. "
            "This packet is read-only and routes execution responsibility to Q Series."
        )

    def _focus(
        self,
        posture: str,
        risks: List[Dict[str, Any]],
        priorities: List[Dict[str, Any]],
    ) -> List[str]:
        focus = []

        if posture in ("defensive", "cautious"):
            focus.append("Review risk posture before expanding exposure")
            focus.append("Prioritize anomalies, fragility, and recovery forecast")
        else:
            focus.append("Review highest-ranked priority markets")
            focus.append("Compare decision support packets against digest themes")

        if risks:
            focus.append(f"Inspect risk driver: {risks[0]['label']}")
        if priorities:
            focus.append(f"Inspect priority driver: {priorities[0]['label']}")

        focus.append("Do not execute from Oracle; hand execution decisions to Q Series")
        return focus


oracle_executive_intelligence_engine = ExecutiveIntelligenceEngine()


def build_executive_intelligence(oracle_digest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return oracle_executive_intelligence_engine.evaluate(oracle_digest)
