from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "oracle_network_intelligence_engine.py"
TEST = ROOT / "test_oi_100_oracle_network_intelligence_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-100 Oracle Network Intelligence Engine
Read-only Oracle Intelligence module.
"""

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


class OracleNetworkIntelligenceEngine:
    module = "oi_100_oracle_network_intelligence_engine"

    def __init__(self):
        self.last_network = {}

    def build_network_intelligence(
        self,
        influence_graph=None,
        stability_index=None,
        health_dashboard=None,
        anomaly_report=None,
        recovery_forecast=None,
        confidence_report=None,
    ):
        influence_graph = influence_graph or {}
        stability_index = stability_index or {}
        health_dashboard = health_dashboard or {}
        anomaly_report = anomaly_report or {}
        recovery_forecast = recovery_forecast or {}
        confidence_report = confidence_report or {}

        influence_nodes = self._index(influence_graph.get("nodes", []), "market")
        stability = self._index(stability_index.get("scores", []), "market")
        health = self._index(health_dashboard.get("cards", []), "market")
        recovery = self._index(recovery_forecast.get("forecasts", []), "market")
        confidence = self._index(confidence_report.get("calibrated_items", []), "market")
        anomaly_counts = self._anomaly_counts(anomaly_report.get("anomalies", []))

        markets = set(influence_nodes) | set(stability) | set(health) | set(recovery) | set(confidence) | set(anomaly_counts)

        nodes = []
        for market in markets:
            h = health.get(market, {})
            s = stability.get(market, {})
            r = recovery.get(market, {})
            c = confidence.get(market, {})
            i = influence_nodes.get(market, {})

            health_score = _f(h.get("health_score"), 50)
            stability_score = _f(s.get("stability_score"), 50)
            recovery_score = _f(r.get("recovery_score"), 50)
            calibrated_confidence = _f(c.get("calibrated_confidence"), 50)
            influence_role = _s(i.get("role"), "unknown")
            anomalies = anomaly_counts.get(market, 0)

            network_score = _clamp(
                health_score * 0.28
                + stability_score * 0.24
                + recovery_score * 0.18
                + calibrated_confidence * 0.18
                + max(0, 100 - anomalies * 18) * 0.12
            )

            nodes.append({
                "market": market,
                "network_score": round(network_score, 4),
                "network_tier": self._tier(network_score),
                "health_score": round(health_score, 4),
                "stability_score": round(stability_score, 4),
                "recovery_score": round(recovery_score, 4),
                "calibrated_confidence": round(calibrated_confidence, 4),
                "influence_role": influence_role,
                "anomaly_count": anomalies,
                "read_only": True,
            })

        nodes.sort(key=lambda x: x["network_score"], reverse=True)

        network = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "market_count": len(nodes),
            "global_stability_score": stability_index.get("global_stability_score"),
            "risk_posture": stability_index.get("risk_posture"),
            "nodes": nodes,
            "top_network_markets": nodes[:10],
            "weak_network_markets": sorted(nodes, key=lambda x: x["network_score"])[:10],
            "network_tier_counts": self._counts(nodes),
            "summary": self._summary(nodes, stability_index, anomaly_report),
        }
        self.last_network = network
        return network

    def _index(self, rows, key):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                value = _s(row.get(key)).strip()
                if value:
                    out[value] = row
        return out

    def _anomaly_counts(self, anomalies):
        out = {}
        for a in anomalies:
            if not isinstance(a, dict):
                continue
            for m in a.get("markets", []):
                market = _s(m).strip()
                if market:
                    out[market] = out.get(market, 0) + 1
        return out

    def _tier(self, score):
        if score >= 80:
            return "elite"
        if score >= 65:
            return "strong"
        if score >= 45:
            return "mixed"
        if score >= 25:
            return "weak"
        return "critical"

    def _counts(self, nodes):
        out = {}
        for n in nodes:
            out[n["network_tier"]] = out.get(n["network_tier"], 0) + 1
        return out

    def _summary(self, nodes, stability_index, anomaly_report):
        avg = sum(n["network_score"] for n in nodes) / max(1, len(nodes))
        return {
            "average_network_score": round(avg, 4),
            "market_count": len(nodes),
            "global_stability_score": stability_index.get("global_stability_score"),
            "risk_posture": stability_index.get("risk_posture"),
            "anomaly_count": anomaly_report.get("anomaly_count", 0),
            "top_market": nodes[0]["market"] if nodes else None,
            "weakest_market": sorted(nodes, key=lambda x: x["network_score"])[0]["market"] if nodes else None,
        }

    def diagnostics(self):
        return {"module": self.module, "status": "ok", "has_network": bool(self.last_network), "market_count": self.last_network.get("market_count", 0), "read_only": True}


oracle_network_intelligence_engine = OracleNetworkIntelligenceEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.oracle_network_intelligence_engine import oracle_network_intelligence_engine


def test_oi_100_oracle_network_intelligence_engine():
    influence_graph = {"nodes": [{"market": "NASDAQ", "role": "bridge"}, {"market": "FED-RATE", "role": "dominant_source"}]}
    stability_index = {
        "global_stability_score": 62,
        "risk_posture": "heightened_monitoring",
        "scores": [{"market": "NASDAQ", "stability_score": 50}, {"market": "FED-RATE", "stability_score": 72}],
    }
    health_dashboard = {"cards": [{"market": "NASDAQ", "health_score": 32}, {"market": "FED-RATE", "health_score": 78}]}
    anomaly_report = {"anomaly_count": 1, "anomalies": [{"markets": ["NASDAQ"], "anomaly_score": 96}]}
    recovery_forecast = {"forecasts": [{"market": "NASDAQ", "recovery_score": 40}, {"market": "FED-RATE", "recovery_score": 77}]}
    confidence_report = {"calibrated_items": [{"market": "NASDAQ", "calibrated_confidence": 68}, {"market": "FED-RATE", "calibrated_confidence": 73}]}

    network = oracle_network_intelligence_engine.build_network_intelligence(
        influence_graph, stability_index, health_dashboard, anomaly_report, recovery_forecast, confidence_report
    )

    assert network["status"] == "ok"
    assert network["read_only"] is True
    assert network["market_count"] == 2
    assert network["nodes"][0]["network_score"] >= network["nodes"][-1]["network_score"]
    assert network["summary"]["top_market"] is not None

    print("[PASS] OI-100 Oracle Network Intelligence Engine")
    print({"markets": network["market_count"], "summary": network["summary"], "top": network["nodes"][0]})


if __name__ == "__main__":
    test_oi_100_oracle_network_intelligence_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .oracle_network_intelligence_engine import oracle_network_intelligence_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-100 INSTALLER")
print(" Oracle Network Intelligence Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-100 installed")
print()
print("Run:")
print("py test_oi_100_oracle_network_intelligence_engine.py")