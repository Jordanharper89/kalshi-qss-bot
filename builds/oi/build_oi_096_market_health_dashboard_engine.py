from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "market_health_dashboard_engine.py"
TEST = ROOT / "test_oi_096_market_health_dashboard_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-096 Market Health Dashboard Engine

Read-only Oracle Intelligence module.
"""

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
class MarketHealthCard:
    market: str
    health_score: float
    health_tier: str
    stability_score: float
    fragility_score: float
    resilience_score: float
    contagion_score: float
    alert_priority: str
    dashboard_status: str
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketHealthDashboardEngine:
    module = "oi_096_market_health_dashboard_engine"

    def __init__(self) -> None:
        self.last_dashboard: Dict[str, Any] = {}

    def build_dashboard(
        self,
        stability_index: Optional[Dict[str, Any]] = None,
        fragility_report: Optional[Dict[str, Any]] = None,
        resilience_report: Optional[Dict[str, Any]] = None,
        contagion_report: Optional[Dict[str, Any]] = None,
        alert_report: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        stability_index = stability_index or {}
        fragility_report = fragility_report or {}
        resilience_report = resilience_report or {}
        contagion_report = contagion_report or {}
        alert_report = alert_report or {}

        stability = self._index(stability_index.get("scores", []), "market")
        fragility = self._index(fragility_report.get("scores", []), "market")
        resilience = self._index(resilience_report.get("scores", []), "market")
        contagion = self._index(contagion_report.get("market_scores", []), "market")
        alerts = self._alerts_by_market(alert_report.get("alerts", []))

        markets = set(stability) | set(fragility) | set(resilience) | set(contagion) | set(alerts)

        cards = []
        for market in markets:
            s = stability.get(market, {})
            f = fragility.get(market, {})
            r = resilience.get(market, {})
            c = contagion.get(market, {})

            stability_score = _safe_float(s.get("stability_score"), 50.0)
            fragility_score = _safe_float(f.get("fragility_score"), 0.0)
            resilience_score = _safe_float(r.get("resilience_score"), 50.0)
            contagion_score = _safe_float(c.get("systemic_importance_score"), 0.0)
            vulnerability = _safe_float(c.get("vulnerability_score"), 0.0)
            alert_priority = self._highest_alert_priority(alerts.get(market, []))

            penalty = {"critical": 28, "high": 20, "elevated": 12, "watch": 6, "info": 0, "none": 0}.get(alert_priority, 0)

            health_score = _clamp(
                stability_score * 0.34
                + resilience_score * 0.26
                + (100 - fragility_score) * 0.20
                + (100 - contagion_score) * 0.12
                + (100 - vulnerability) * 0.08
                - penalty
            )

            cards.append(MarketHealthCard(
                market=market,
                health_score=round(health_score, 4),
                health_tier=self._tier(health_score),
                stability_score=round(stability_score, 4),
                fragility_score=round(fragility_score, 4),
                resilience_score=round(resilience_score, 4),
                contagion_score=round(contagion_score, 4),
                alert_priority=alert_priority,
                dashboard_status=self._status(health_score, alert_priority),
                reasons=self._reasons(health_score, stability_score, fragility_score, resilience_score, contagion_score, alert_priority),
            ))

        cards.sort(key=lambda x: x.health_score, reverse=True)

        dashboard = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "market_count": len(cards),
            "global_stability_score": stability_index.get("global_stability_score"),
            "global_stability_tier": stability_index.get("global_stability_tier"),
            "risk_posture": stability_index.get("risk_posture"),
            "cards": [c.to_dict() for c in cards],
            "best_health_markets": [c.to_dict() for c in cards[:10]],
            "worst_health_markets": [c.to_dict() for c in sorted(cards, key=lambda x: x.health_score)[:10]],
            "health_tier_counts": self._counts(cards),
            "dashboard_summary": self._summary(cards, stability_index, alert_report),
        }
        self.last_dashboard = dashboard
        return dashboard

    def _index(self, rows, key):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                value = _safe_str(row.get(key)).strip()
                if value:
                    out[value] = row
        return out

    def _alerts_by_market(self, rows):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                market = _safe_str(row.get("market")).strip()
                if market:
                    out.setdefault(market, []).append(row)
        return out

    def _highest_alert_priority(self, rows):
        rank = {"critical": 5, "high": 4, "elevated": 3, "watch": 2, "info": 1}
        best = "none"
        best_rank = 0
        for row in rows:
            priority = _safe_str(row.get("priority"), "none")
            if rank.get(priority, 0) > best_rank:
                best = priority
                best_rank = rank.get(priority, 0)
        return best

    def _tier(self, score):
        if score >= 80:
            return "healthy"
        if score >= 65:
            return "stable"
        if score >= 45:
            return "mixed"
        if score >= 25:
            return "weak"
        return "critical"

    def _status(self, score, priority):
        if priority == "critical" or score < 25:
            return "red"
        if priority == "high" or score < 45:
            return "orange"
        if priority in {"elevated", "watch"} or score < 65:
            return "yellow"
        return "green"

    def _counts(self, cards):
        counts = {"healthy": 0, "stable": 0, "mixed": 0, "weak": 0, "critical": 0}
        for card in cards:
            counts[card.health_tier] = counts.get(card.health_tier, 0) + 1
        return counts

    def _reasons(self, health, stability, fragility, resilience, contagion, priority):
        reasons = [f"Health score is {round(health, 2)}."]
        if stability < 45:
            reasons.append("Stability is weak.")
        if fragility >= 65:
            reasons.append("Fragility is elevated.")
        if resilience >= 65:
            reasons.append("Resilience support is strong.")
        if contagion >= 65:
            reasons.append("Systemic contagion pressure is elevated.")
        if priority not in {"none", "info"}:
            reasons.append(f"Active alert priority is {priority}.")
        return reasons[:8]

    def _summary(self, cards, stability_index, alert_report):
        avg = sum(c.health_score for c in cards) / max(1, len(cards))
        return {
            "average_health_score": round(avg, 4),
            "red_markets": len([c for c in cards if c.dashboard_status == "red"]),
            "orange_markets": len([c for c in cards if c.dashboard_status == "orange"]),
            "alert_count": alert_report.get("alert_count", 0),
            "global_stability_score": stability_index.get("global_stability_score"),
            "risk_posture": stability_index.get("risk_posture"),
        }

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_dashboard": bool(self.last_dashboard),
            "market_count": self.last_dashboard.get("market_count", 0),
            "read_only": True,
        }


market_health_dashboard_engine = MarketHealthDashboardEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.market_health_dashboard_engine import market_health_dashboard_engine


def test_oi_096_market_health_dashboard_engine():
    stability_index = {
        "global_stability_score": 62.6,
        "global_stability_tier": "mixed",
        "risk_posture": "heightened_monitoring",
        "scores": [
            {"market": "NASDAQ", "stability_score": 50.8},
            {"market": "FED-RATE", "stability_score": 74.5},
        ],
    }
    fragility_report = {"scores": [{"market": "NASDAQ", "fragility_score": 71.1}, {"market": "FED-RATE", "fragility_score": 28.0}]}
    resilience_report = {"scores": [{"market": "NASDAQ", "resilience_score": 35.0}, {"market": "FED-RATE", "resilience_score": 78.4}]}
    contagion_report = {"market_scores": [{"market": "NASDAQ", "systemic_importance_score": 75.1, "vulnerability_score": 83.1}, {"market": "FED-RATE", "systemic_importance_score": 52.0, "vulnerability_score": 20.0}]}
    alert_report = {"alert_count": 2, "alerts": [{"market": "NASDAQ", "priority": "high"}, {"market": "GLOBAL", "priority": "elevated"}]}

    dashboard = market_health_dashboard_engine.build_dashboard(stability_index, fragility_report, resilience_report, contagion_report, alert_report)

    assert dashboard["status"] == "ok"
    assert dashboard["read_only"] is True
    assert dashboard["market_count"] >= 2
    assert dashboard["cards"][0]["health_score"] >= dashboard["cards"][-1]["health_score"]
    assert any(c["market"] == "NASDAQ" for c in dashboard["cards"])

    print("[PASS] OI-096 Market Health Dashboard Engine")
    print({"markets": dashboard["market_count"], "summary": dashboard["dashboard_summary"], "worst": dashboard["worst_health_markets"][0]})


if __name__ == "__main__":
    test_oi_096_market_health_dashboard_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .market_health_dashboard_engine import market_health_dashboard_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-096 INSTALLER")
print(" Market Health Dashboard Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-096 installed")
print()
print("Run:")
print("python test_oi_096_market_health_dashboard_engine.py")