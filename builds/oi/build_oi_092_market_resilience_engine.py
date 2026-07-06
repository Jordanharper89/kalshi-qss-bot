from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "market_resilience_engine.py"
TEST = ROOT / "test_oi_092_market_resilience_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r"""
\"\"\"
OI-092 Market Resilience Engine

Read-only Oracle Intelligence module.

Purpose:
- Measure how quickly a market is likely to recover from shocks.
- Estimate recovery potential after fragility, contagion, and regime-transition pressure.
- Produce resilience scores, recovery tiers, and recovery profile cards.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
\"\"\"

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import math
import time


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(value)))


@dataclass
class MarketResilienceScore:
    market: str
    resilience_score: float
    recovery_tier: str
    shock_absorption_score: float
    recovery_capacity_score: float
    stability_buffer_score: float
    primary_support: str
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketResilienceEngine:
    module = "oi_092_market_resilience_engine"

    def __init__(self) -> None:
        self.last_report: Dict[str, Any] = {}

    def score_resilience(
        self,
        fragility_report: Optional[Dict[str, Any]] = None,
        transition_graph: Optional[Dict[str, Any]] = None,
        contagion_report: Optional[Dict[str, Any]] = None,
        influence_graph: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        fragility_report = fragility_report or {}
        transition_graph = transition_graph or {}
        contagion_report = contagion_report or {}
        influence_graph = influence_graph or {}

        fragility = self._index(fragility_report.get("scores", []), "market")
        transitions = self._index(transition_graph.get("nodes", []), "market")
        contagion = self._index(contagion_report.get("market_scores", []), "market")
        influence = self._index(influence_graph.get("nodes", []), "market")

        markets = set(fragility.keys()) | set(transitions.keys()) | set(contagion.keys()) | set(influence.keys())

        scores: List[MarketResilienceScore] = []
        for market in markets:
            f = fragility.get(market, {})
            t = transitions.get(market, {})
            c = contagion.get(market, {})
            i = influence.get(market, {})

            fragility_score = _safe_float(f.get("fragility_score"))
            transition_pressure = _safe_float(t.get("transition_pressure"))
            instability = _safe_float(t.get("instability_score"))
            vulnerability = _safe_float(c.get("vulnerability_score"))
            source_strength = _safe_float(c.get("contagion_source_score"))
            systemic = _safe_float(c.get("systemic_importance_score"))
            incoming = _safe_float(i.get("incoming_influence"))
            outgoing = _safe_float(i.get("outgoing_influence"))
            bridge = _safe_float(i.get("bridge_score"))
            role = _safe_str(i.get("role"), "balanced")
            regime = _safe_str(t.get("regime"), "neutral")

            shock_absorption = _clamp(100 - (vulnerability * 0.38 + instability * 0.32 + fragility_score * 0.30))
            recovery_capacity = _clamp(
                (100 - transition_pressure) * 0.35
                + max(0.0, outgoing - incoming) * 0.18
                + source_strength * 0.18
                + (25 if regime in {"stabilization", "accumulation", "neutral"} else 8)
                + (12 if role in {"source", "dominant_source"} else 6 if role == "balanced" else 0)
            )
            stability_buffer = _clamp(
                (100 - fragility_score) * 0.35
                + (100 - vulnerability) * 0.25
                + (100 - instability) * 0.20
                + min(systemic, 65) * 0.10
                + max(0.0, 60 - bridge) * 0.10
            )

            resilience = _clamp(shock_absorption * 0.34 + recovery_capacity * 0.36 + stability_buffer * 0.30)
            components = {
                "shock_absorption_score": shock_absorption,
                "recovery_capacity_score": recovery_capacity,
                "stability_buffer_score": stability_buffer,
            }
            primary_support = max(components.items(), key=lambda kv: kv[1])[0]

            scores.append(
                MarketResilienceScore(
                    market=market,
                    resilience_score=round(resilience, 4),
                    recovery_tier=self._tier(resilience),
                    shock_absorption_score=round(shock_absorption, 4),
                    recovery_capacity_score=round(recovery_capacity, 4),
                    stability_buffer_score=round(stability_buffer, 4),
                    primary_support=primary_support,
                    reasons=self._reasons(role, regime, resilience, primary_support),
                )
            )

        scores.sort(key=lambda x: x.resilience_score, reverse=True)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "input_modules": [
                "oi_091_market_fragility_score_engine",
                "oi_087_market_regime_transition_graph_engine",
                "oi_088_systemic_risk_contagion_engine",
                "oi_086_market_influence_graph_engine",
            ],
            "market_count": len(scores),
            "scores": [s.to_dict() for s in scores],
            "top_resilient_markets": [s.to_dict() for s in scores[:10]],
            "weak_resilience_markets": [s.to_dict() for s in scores if s.recovery_tier in {"weak", "poor"}][:10],
            "recovery_tier_counts": self._counts(scores),
            "highest_resilience": scores[0].to_dict() if scores else None,
        }

        self.last_report = report
        return report

    def _index(self, rows: List[Dict[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            if isinstance(row, dict):
                value = _safe_str(row.get(key)).strip()
                if value:
                    out[value] = row
        return out

    def _tier(self, score: float) -> str:
        if score >= 80:
            return "excellent"
        if score >= 65:
            return "strong"
        if score >= 45:
            return "moderate"
        if score >= 25:
            return "weak"
        return "poor"

    def _counts(self, scores: List[MarketResilienceScore]) -> Dict[str, int]:
        counts = {"excellent": 0, "strong": 0, "moderate": 0, "weak": 0, "poor": 0}
        for score in scores:
            counts[score.recovery_tier] = counts.get(score.recovery_tier, 0) + 1
        return counts

    def _reasons(self, role: str, regime: str, resilience: float, primary_support: str) -> List[str]:
        reasons = [f"Primary resilience support is {primary_support}."]
        if regime:
            reasons.append(f"Current regime state is {regime}.")
        if role:
            reasons.append(f"Influence role is {role}.")
        if resilience >= 65:
            reasons.append("Market has meaningful recovery capacity after shocks.")
        elif resilience < 45:
            reasons.append("Market may recover slowly after new information or contagion.")
        return reasons[:8]

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "status": "ok",
            "has_report": bool(self.last_report),
            "market_count": self.last_report.get("market_count", 0),
            "read_only": True,
        }


market_resilience_engine = MarketResilienceEngine()
""", encoding="utf-8")


# Cleanup defensive escaping if the text renderer preserved escaped docstring characters.
_engine_text = ENGINE.read_text(encoding="utf-8")
_engine_text = _engine_text.replace('\\\"\\\"\\\"', '"""')
ENGINE.write_text(_engine_text, encoding="utf-8")

TEST.write_text(r"""
from qseries_v2.oracle_intelligence.market_resilience_engine import market_resilience_engine


def test_oi_092_market_resilience_engine():
    fragility_report = {
        "scores": [
            {"market": "NASDAQ", "fragility_score": 71.1},
            {"market": "AI-SECTOR", "fragility_score": 62.2},
            {"market": "FED-RATE", "fragility_score": 28.0},
        ]
    }

    transition_graph = {
        "nodes": [
            {"market": "NASDAQ", "regime": "contagion", "transition_pressure": 72, "instability_score": 76},
            {"market": "AI-SECTOR", "regime": "stress", "transition_pressure": 78, "instability_score": 70},
            {"market": "FED-RATE", "regime": "accumulation", "transition_pressure": 35, "instability_score": 25},
        ]
    }

    contagion_report = {
        "market_scores": [
            {"market": "NASDAQ", "vulnerability_score": 83, "contagion_source_score": 77, "systemic_importance_score": 75},
            {"market": "AI-SECTOR", "vulnerability_score": 72, "contagion_source_score": 50, "systemic_importance_score": 63},
            {"market": "FED-RATE", "vulnerability_score": 20, "contagion_source_score": 70, "systemic_importance_score": 52},
        ]
    }

    influence_graph = {
        "nodes": [
            {"market": "NASDAQ", "incoming_influence": 86, "outgoing_influence": 62, "bridge_score": 70, "role": "bridge"},
            {"market": "AI-SECTOR", "incoming_influence": 75, "outgoing_influence": 35, "bridge_score": 54, "role": "sink"},
            {"market": "FED-RATE", "incoming_influence": 5, "outgoing_influence": 90, "bridge_score": 12, "role": "dominant_source"},
        ]
    }

    report = market_resilience_engine.score_resilience(
        fragility_report,
        transition_graph,
        contagion_report,
        influence_graph,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["market_count"] == 3
    assert report["highest_resilience"]["market"] == "FED-RATE"
    assert report["top_resilient_markets"][0]["resilience_score"] >= report["top_resilient_markets"][-1]["resilience_score"]
    assert report["recovery_tier_counts"]

    diag = market_resilience_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True

    print("[PASS] OI-092 Market Resilience Engine")
    print({
        "markets": report["market_count"],
        "highest": report["highest_resilience"],
        "tiers": report["recovery_tier_counts"],
    })


if __name__ == "__main__":
    test_oi_092_market_resilience_engine()
""", encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .market_resilience_engine import market_resilience_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-092 INSTALLER")
print(" Market Resilience Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-092 installed")
print()
print("Run:")
print("python test_oi_092_market_resilience_engine.py")
