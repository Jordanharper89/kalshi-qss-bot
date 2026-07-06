from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "cross_market_anomaly_detection_engine.py"
TEST = ROOT / "test_oi_097_cross_market_anomaly_detection_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-097 Cross-Market Anomaly Detection Engine

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
class CrossMarketAnomaly:
    anomaly_id: str
    anomaly_type: str
    markets: List[str]
    anomaly_score: float
    severity: str
    explanation: str
    evidence: Dict[str, Any]

    def to_dict(self):
        return asdict(self)


class CrossMarketAnomalyDetectionEngine:
    module = "oi_097_cross_market_anomaly_detection_engine"

    def __init__(self):
        self.last_report = {}

    def detect_anomalies(
        self,
        current_dashboard=None,
        previous_dashboard=None,
        influence_graph=None,
        transition_graph=None,
        alert_report=None,
        min_score=20.0,
    ):
        current_dashboard = current_dashboard or {}
        previous_dashboard = previous_dashboard or {}
        influence_graph = influence_graph or {}
        transition_graph = transition_graph or {}
        alert_report = alert_report or {}

        current = self._index(current_dashboard.get("cards", []), "market")
        previous = self._index(previous_dashboard.get("cards", []), "market")
        regimes = self._index(transition_graph.get("nodes", []), "market")

        anomalies = []
        anomalies.extend(self._health_shift_anomalies(current, previous))
        anomalies.extend(self._influence_health_divergence(current, influence_graph.get("edges", [])))
        anomalies.extend(self._regime_health_conflicts(current, regimes))
        anomalies.extend(self._alert_health_conflicts(current, alert_report.get("alerts", [])))

        filtered = [a for a in anomalies if a.anomaly_score >= min_score]
        filtered.sort(key=lambda a: a.anomaly_score, reverse=True)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "anomaly_count": len(filtered),
            "anomalies": [a.to_dict() for a in filtered],
            "critical_anomalies": [a.to_dict() for a in filtered if a.severity == "critical"],
            "high_anomalies": [a.to_dict() for a in filtered if a.severity == "high"],
            "summary": self._summary(filtered),
        }
        self.last_report = report
        return report

    def _index(self, rows, key):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                value = _safe_str(row.get(key)).strip()
                if value:
                    out[value] = row
        return out

    def _health_shift_anomalies(self, current, previous):
        out = []
        for market, cur in current.items():
            if market not in previous:
                continue
            cur_score = _safe_float(cur.get("health_score"))
            prev_score = _safe_float(previous[market].get("health_score"))
            delta = cur_score - prev_score
            if abs(delta) >= 12:
                score = _clamp(abs(delta) * 4.2)
                direction = "improved" if delta > 0 else "deteriorated"
                out.append(CrossMarketAnomaly(
                    anomaly_id=f"health_shift_{market}".lower(),
                    anomaly_type="health_shift",
                    markets=[market],
                    anomaly_score=round(score, 4),
                    severity=self._severity(score),
                    explanation=f"{market} health {direction} by {round(abs(delta), 2)} points.",
                    evidence={"current_health": cur_score, "previous_health": prev_score, "delta": round(delta, 4)},
                ))
        return out

    def _influence_health_divergence(self, current, edges):
        out = []
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            source = _safe_str(edge.get("source")).strip()
            target = _safe_str(edge.get("target")).strip()
            influence = _safe_float(edge.get("influence_score"))
            if source not in current or target not in current:
                continue

            source_health = _safe_float(current[source].get("health_score"))
            target_health = _safe_float(current[target].get("health_score"))
            gap = abs(source_health - target_health)

            if influence >= 60 and gap >= 35:
                score = _clamp(influence * 0.55 + gap * 0.45)
                out.append(CrossMarketAnomaly(
                    anomaly_id=f"influence_health_divergence_{source}_{target}".lower(),
                    anomaly_type="influence_health_divergence",
                    markets=[source, target],
                    anomaly_score=round(score, 4),
                    severity=self._severity(score),
                    explanation=f"Strong influence between {source} and {target} conflicts with a large health gap.",
                    evidence={"influence_score": influence, "source_health": source_health, "target_health": target_health, "health_gap": round(gap, 4)},
                ))
        return out

    def _regime_health_conflicts(self, current, regimes):
        out = []
        for market, card in current.items():
            regime = _safe_str(regimes.get(market, {}).get("regime"))
            health = _safe_float(card.get("health_score"))
            if regime in {"stress", "contagion", "contraction"} and health >= 65:
                score = _clamp((health - 50) * 1.8)
                out.append(CrossMarketAnomaly(
                    anomaly_id=f"regime_health_conflict_{market}".lower(),
                    anomaly_type="regime_health_conflict",
                    markets=[market],
                    anomaly_score=round(score, 4),
                    severity=self._severity(score),
                    explanation=f"{market} shows healthy dashboard status despite high-risk regime {regime}.",
                    evidence={"regime": regime, "health_score": health},
                ))
        return out

    def _alert_health_conflicts(self, current, alerts):
        out = []
        for alert in alerts:
            if not isinstance(alert, dict):
                continue
            market = _safe_str(alert.get("market")).strip()
            priority = _safe_str(alert.get("priority"))
            if market not in current:
                continue
            health = _safe_float(current[market].get("health_score"))
            if priority in {"critical", "high"} and health >= 65:
                score = _clamp(health * 0.55 + (30 if priority == "critical" else 20))
                out.append(CrossMarketAnomaly(
                    anomaly_id=f"alert_health_conflict_{market}".lower(),
                    anomaly_type="alert_health_conflict",
                    markets=[market],
                    anomaly_score=round(score, 4),
                    severity=self._severity(score),
                    explanation=f"{market} has high-priority alert but dashboard health remains strong.",
                    evidence={"priority": priority, "health_score": health, "alert_type": alert.get("alert_type")},
                ))
        return out

    def _severity(self, score):
        if score >= 80:
            return "critical"
        if score >= 60:
            return "high"
        if score >= 40:
            return "elevated"
        return "watch"

    def _summary(self, anomalies):
        counts = {}
        for anomaly in anomalies:
            counts[anomaly.severity] = counts.get(anomaly.severity, 0) + 1
        return {"severity_counts": counts, "top_anomaly": anomalies[0].to_dict() if anomalies else None}

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_report": bool(self.last_report),
            "anomaly_count": self.last_report.get("anomaly_count", 0),
            "read_only": True,
        }


cross_market_anomaly_detection_engine = CrossMarketAnomalyDetectionEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.cross_market_anomaly_detection_engine import cross_market_anomaly_detection_engine


def test_oi_097_cross_market_anomaly_detection_engine():
    current_dashboard = {"cards": [{"market": "NASDAQ", "health_score": 32}, {"market": "FED-RATE", "health_score": 78}, {"market": "AI-SECTOR", "health_score": 72}]}
    previous_dashboard = {"cards": [{"market": "NASDAQ", "health_score": 55}, {"market": "FED-RATE", "health_score": 76}, {"market": "AI-SECTOR", "health_score": 70}]}
    influence_graph = {"edges": [{"source": "FED-RATE", "target": "NASDAQ", "influence_score": 83}]}
    transition_graph = {"nodes": [{"market": "AI-SECTOR", "regime": "stress"}, {"market": "NASDAQ", "regime": "contraction"}]}
    alert_report = {"alerts": [{"market": "AI-SECTOR", "priority": "high", "alert_type": "persistent_risk_pressure"}]}

    report = cross_market_anomaly_detection_engine.detect_anomalies(current_dashboard, previous_dashboard, influence_graph, transition_graph, alert_report)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["anomaly_count"] >= 3
    assert report["anomalies"][0]["anomaly_score"] >= report["anomalies"][-1]["anomaly_score"]

    print("[PASS] OI-097 Cross-Market Anomaly Detection Engine")
    print({"anomalies": report["anomaly_count"], "summary": report["summary"], "top": report["anomalies"][0]})


if __name__ == "__main__":
    test_oi_097_cross_market_anomaly_detection_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .cross_market_anomaly_detection_engine import cross_market_anomaly_detection_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-097 INSTALLER")
print(" Cross-Market Anomaly Detection Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-097 installed")
print()
print("Run:")
print("python test_oi_097_cross_market_anomaly_detection_engine.py")