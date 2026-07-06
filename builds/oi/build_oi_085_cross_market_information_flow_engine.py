from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "cross_market_information_flow_engine.py"
TEST = ROOT / "test_oi_085_cross_market_information_flow_engine.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-085 Cross-Market Information Flow Engine

Purpose:
- Combine propagation and causal inference into one information-flow graph.
- Score live cross-market information flow, laggards, causal confidence, and edge priority.
- Read-only Oracle intelligence layer.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class CrossMarketInformationFlowEngine:
    module_name = "oi_085_cross_market_information_flow_engine"

    def __init__(self, propagation_engine=None, causal_engine=None) -> None:
        self.propagation_engine = propagation_engine
        self.causal_engine = causal_engine
        self._flow_history: List[Dict[str, Any]] = []

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "flow_records": len(self._flow_history),
            "has_propagation_engine": self.propagation_engine is not None,
            "has_causal_engine": self.causal_engine is not None,
        }

    def build_flow_report(
        self,
        source_market: str,
        live_markets: List[Dict[str, Any]],
        elapsed_minutes: float,
        event_type: Optional[str] = None,
        propagation_result: Optional[Dict[str, Any]] = None,
        causal_graph: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if propagation_result is None and self.propagation_engine is not None:
            propagation_result = self.propagation_engine.detect_lagging_markets(
                source_market=source_market,
                live_markets=live_markets,
                elapsed_minutes=elapsed_minutes,
                event_type=event_type,
            )

        if causal_graph is None and self.causal_engine is not None:
            causal_graph = self.causal_engine.causal_graph()

        propagation_result = propagation_result or {"results": [], "lagging_markets": []}
        causal_graph = causal_graph or {"links": []}

        causal_by_target = {
            link.get("target_market"): link
            for link in causal_graph.get("links", [])
            if link.get("source_market") == source_market
        }

        flows = []
        for row in propagation_result.get("results", []):
            target = row.get("ticker")
            causal = causal_by_target.get(target)
            flows.append(self._score_flow(source_market, row, causal))

        flows.sort(key=lambda x: x["information_flow_score"], reverse=True)

        report = {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "source_market": source_market,
            "event_type": event_type,
            "elapsed_minutes": float(elapsed_minutes),
            "flow_count": len(flows),
            "flows": flows,
            "priority_flows": [f for f in flows if f["priority"] in {"critical", "high"}],
            "summary": self._summary(flows),
        }

        self._flow_history.append(report)
        return report

    def latest_flow_report(self) -> Optional[Dict[str, Any]]:
        return self._flow_history[-1] if self._flow_history else None

    def flow_history(self, limit: int = 25) -> Dict[str, Any]:
        return {
            "status": "ok",
            "read_only": True,
            "count": len(self._flow_history),
            "history": self._flow_history[-limit:],
        }

    def _score_flow(
        self,
        source_market: str,
        propagation_row: Dict[str, Any],
        causal_link: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        propagation_score = float(propagation_row.get("information_edge_score") or 0.0)
        causal_confidence = float((causal_link or {}).get("causal_confidence") or 35.0)
        lag = float(propagation_row.get("reaction_lag_minutes") or 0.0)

        flow_score = propagation_score * 0.55 + causal_confidence * 0.35 + min(max(lag, 0.0), 60.0) * 0.10
        flow_score = max(0.0, min(100.0, flow_score))

        reasons = list(propagation_row.get("reason_codes", []))
        if causal_confidence >= 75:
            reasons.append("strong_causal_confirmation")
        elif causal_confidence < 50:
            reasons.append("weak_causal_confirmation")

        priority = self._priority(flow_score)

        return {
            "source_market": source_market,
            "target_market": propagation_row.get("ticker"),
            "read_only": True,
            "information_flow_score": round(flow_score, 2),
            "priority": priority,
            "lagging": propagation_row.get("lagging", False),
            "propagation_score": round(propagation_score, 2),
            "causal_confidence": round(causal_confidence, 2),
            "reaction_lag_minutes": round(lag, 2),
            "reason_codes": reasons,
            "recommended_research_action": self._research_action(priority),
        }

    def _priority(self, score: float) -> str:
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 55:
            return "medium"
        if score >= 40:
            return "watch"
        return "low"

    def _research_action(self, priority: str) -> str:
        if priority in {"critical", "high"}:
            return "run_full_oracle_consensus"
        if priority == "medium":
            return "run_standard_research"
        if priority == "watch":
            return "monitor"
        return "ignore"

    def _summary(self, flows: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not flows:
            return {
                "top_flow": None,
                "priority_count": 0,
                "avg_flow_score": 0.0,
            }

        return {
            "top_flow": flows[0],
            "priority_count": len([f for f in flows if f["priority"] in {"critical", "high"}]),
            "avg_flow_score": round(sum(f["information_flow_score"] for f in flows) / len(flows), 2),
        }


cross_market_information_flow_engine = CrossMarketInformationFlowEngine()
'''

test_code = r'''from qseries_v2.oracle_intelligence.cross_market_information_flow_engine import CrossMarketInformationFlowEngine


def test_oi_085_cross_market_information_flow_engine():
    engine = CrossMarketInformationFlowEngine()

    propagation = {
        "results": [
            {
                "ticker": "COIN",
                "lagging": False,
                "information_edge_score": 35,
                "reaction_lag_minutes": 2,
                "reason_codes": ["reaction_in_line"],
            },
            {
                "ticker": "MSTR",
                "lagging": True,
                "information_edge_score": 90,
                "reaction_lag_minutes": 12,
                "reason_codes": ["expected_reaction_window_passed", "market_underreacted"],
            },
        ],
        "lagging_markets": [{"ticker": "MSTR"}],
    }

    causal_graph = {
        "links": [
            {"source_market": "BTC", "target_market": "COIN", "causal_confidence": 65},
            {"source_market": "BTC", "target_market": "MSTR", "causal_confidence": 88},
        ]
    }

    report = engine.build_flow_report(
        source_market="BTC",
        live_markets=[],
        elapsed_minutes=15,
        event_type="crypto_news",
        propagation_result=propagation,
        causal_graph=causal_graph,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["flow_count"] == 2
    assert report["flows"][0]["target_market"] == "MSTR"
    assert report["flows"][0]["priority"] in {"critical", "high"}
    assert report["summary"]["priority_count"] >= 1

    history = engine.flow_history()
    assert history["count"] == 1

    status = engine.status()
    assert status["status"] == "ok"

    print("[PASS] OI-085 Cross-Market Information Flow Engine")
    print({"summary": report["summary"], "top": report["flows"][0]})


if __name__ == "__main__":
    test_oi_085_cross_market_information_flow_engine()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .cross_market_information_flow_engine import cross_market_information_flow_engine, CrossMarketInformationFlowEngine\n"
if export_line not in init_text:
    init_text += "\n" + export_line
INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-085 INSTALLER")
print(" Cross-Market Information Flow Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-085 installed")
print()
print("Run:")
print("python test_oi_085_cross_market_information_flow_engine.py")