from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "oracle_intelligence_synthesis_engine.py"
TEST = ROOT / "test_oi_051_oracle_intelligence_synthesis_engine.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-051 Oracle Intelligence Synthesis Engine

Phase IV entry point.

Purpose:
- Combine Oracle reasoning modules into one consolidated research packet.
- Pull together:
  - similarity intelligence
  - case-based reasoning
  - market DNA
  - analog retrieval
  - outcome distribution
  - adaptive confidence learning
  - knowledge graph context

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .oracle_similarity_intelligence_engine import oracle_similarity_intelligence_engine
from .case_based_reasoning_engine import case_based_reasoning_engine
from .market_dna_fingerprinting_engine import market_dna_fingerprinting_engine
from .analog_market_retrieval_engine import analog_market_retrieval_engine
from .outcome_distribution_engine import outcome_distribution_engine
from .adaptive_confidence_learning_engine import adaptive_confidence_learning_engine
from .oracle_knowledge_graph import oracle_knowledge_graph


class OracleIntelligenceSynthesisEngine:
    module_name = "oi_051_oracle_intelligence_synthesis_engine"

    def __init__(
        self,
        similarity_engine=None,
        reasoning_engine=None,
        dna_engine=None,
        retrieval_engine=None,
        distribution_engine=None,
        confidence_engine=None,
        knowledge_graph=None,
    ) -> None:
        self.similarity_engine = similarity_engine or oracle_similarity_intelligence_engine
        self.reasoning_engine = reasoning_engine or case_based_reasoning_engine
        self.dna_engine = dna_engine or market_dna_fingerprinting_engine
        self.retrieval_engine = retrieval_engine or analog_market_retrieval_engine
        self.distribution_engine = distribution_engine or outcome_distribution_engine
        self.confidence_engine = confidence_engine or adaptive_confidence_learning_engine
        self.knowledge_graph = knowledge_graph or oracle_knowledge_graph

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "engines": {
                "similarity": self._safe_status(self.similarity_engine),
                "reasoning": self._safe_status(self.reasoning_engine),
                "dna": self._safe_status(self.dna_engine),
                "retrieval": self._safe_status(self.retrieval_engine),
                "distribution": self._safe_status(self.distribution_engine),
                "confidence": self._safe_status(self.confidence_engine),
                "knowledge_graph": self._safe_status(self.knowledge_graph),
            },
        }

    def synthesize(
        self,
        current_setup: Dict[str, Any],
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 25,
        include_graph: bool = True,
    ) -> Dict[str, Any]:
        dna = self.dna_engine.fingerprint_market(current_setup)

        retrieval = self.retrieval_engine.retrieve_analogs(
            current_setup=current_setup,
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
        )

        reasoning = self.reasoning_engine.reason_from_cases(
            current_setup=current_setup,
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
        )

        distribution = self.distribution_engine.build_distribution(
            current_setup=current_setup,
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
        )

        confidence_report = self.confidence_engine.learn_confidence(
            memory_type="forecast",
            limit=10000,
        )

        raw_confidence = self._derive_raw_confidence(reasoning, distribution)
        adjusted_confidence = self.confidence_engine.adjust_confidence(
            raw_confidence=raw_confidence,
            context={
                "source": self.module_name,
                "market_ticker": current_setup.get("ticker") or current_setup.get("market_ticker"),
                "dna_family": dna.get("dna_family"),
            },
            learning_report=confidence_report,
        )

        graph_context = self._graph_context(current_setup) if include_graph else {}

        summary = self._summary(
            current_setup=current_setup,
            dna=dna,
            retrieval=retrieval,
            reasoning=reasoning,
            distribution=distribution,
            adjusted_confidence=adjusted_confidence,
            graph_context=graph_context,
        )

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "query": current_setup,
            "summary": summary,
            "market_dna": dna,
            "analog_retrieval": retrieval,
            "case_reasoning": reasoning,
            "outcome_distribution": distribution,
            "confidence_learning": confidence_report,
            "adjusted_confidence": adjusted_confidence,
            "knowledge_graph_context": graph_context,
        }

    def _derive_raw_confidence(self, reasoning: Dict[str, Any], distribution: Dict[str, Any]) -> float:
        reason_prob = reasoning.get("expected_probability")
        resolution = distribution.get("resolution_distribution", {})
        yes_prob = resolution.get("yes_probability")
        no_prob = resolution.get("no_probability")
        expected = resolution.get("expected_resolution")

        candidates = []

        if reason_prob is not None:
            candidates.append(float(reason_prob) * 100.0)

        if expected == "YES" and yes_prob is not None:
            candidates.append(float(yes_prob) * 100.0)

        if expected == "NO" and no_prob is not None:
            candidates.append(float(no_prob) * 100.0)

        if not candidates:
            return 50.0

        return max(0.0, min(100.0, sum(candidates) / len(candidates)))

    def _graph_context(self, current_setup: Dict[str, Any]) -> Dict[str, Any]:
        ticker = current_setup.get("ticker") or current_setup.get("market_ticker")
        node_id = f"market:{ticker}" if ticker else None

        try:
            graph_build = self.knowledge_graph.build_from_memory(clear_existing=True, limit=10000)
            summary = self.knowledge_graph.graph_summary()

            neighbors = {}
            if node_id and self.knowledge_graph.get_node(node_id):
                neighbors = self.knowledge_graph.neighbors(node_id, limit=10)

            return {
                "status": "ok",
                "graph_build": graph_build,
                "graph_summary": summary,
                "market_node": node_id,
                "neighbors": neighbors,
            }
        except Exception as exc:
            return {
                "status": "error",
                "error": str(exc),
                "market_node": node_id,
            }

    def _summary(
        self,
        current_setup: Dict[str, Any],
        dna: Dict[str, Any],
        retrieval: Dict[str, Any],
        reasoning: Dict[str, Any],
        distribution: Dict[str, Any],
        adjusted_confidence: Dict[str, Any],
        graph_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        resolution = distribution.get("resolution_distribution", {})
        movement = distribution.get("movement_distribution", {})
        timing = distribution.get("timing_distribution_minutes", {})
        tail_risk = distribution.get("tail_risk", {})

        return {
            "market_ticker": current_setup.get("ticker") or current_setup.get("market_ticker"),
            "dna_id": dna.get("dna_id"),
            "dna_family": dna.get("dna_family"),
            "top_analog": self._top_analog(retrieval),
            "analog_count": retrieval.get("analog_count", 0),
            "expected_resolution": resolution.get("expected_resolution") or reasoning.get("expected_resolution"),
            "expected_probability": resolution.get("yes_probability") if resolution.get("expected_resolution") == "YES" else resolution.get("no_probability"),
            "case_reasoning_probability": reasoning.get("expected_probability"),
            "adjusted_confidence": adjusted_confidence.get("adjusted_confidence"),
            "confidence_delta": adjusted_confidence.get("delta"),
            "avg_expected_move": movement.get("mean"),
            "median_expected_move": movement.get("median"),
            "avg_resolution_minutes": timing.get("mean"),
            "tail_risk_level": tail_risk.get("tail_risk_level"),
            "risk_level": reasoning.get("risk_level"),
            "graph_nodes": graph_context.get("graph_summary", {}).get("total_nodes"),
            "graph_edges": graph_context.get("graph_summary", {}).get("total_edges"),
            "research_ready": True,
        }

    def _top_analog(self, retrieval: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        analogs = retrieval.get("top_analogs", [])
        if not analogs:
            return None

        top = analogs[0]
        memory = top.get("memory", {})

        return {
            "market_ticker": memory.get("market_ticker"),
            "retrieval_score_pct": top.get("retrieval_score_pct"),
            "similarity_pct": top.get("similarity_pct"),
            "dna_similarity_pct": top.get("dna_similarity_pct"),
        }

    def _safe_status(self, engine: Any) -> str:
        try:
            return engine.status().get("status", "unknown")
        except Exception:
            return "error"


oracle_intelligence_synthesis_engine = OracleIntelligenceSynthesisEngine()
'''

test_code = r'''from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_memory_engine import OracleMemoryEngine
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import OraclePersistentMemoryStore
from qseries_v2.oracle_intelligence.oracle_memory_persistence_bridge import OracleMemoryPersistenceBridge
from qseries_v2.oracle_intelligence.oracle_similarity_intelligence_engine import OracleSimilarityIntelligenceEngine
from qseries_v2.oracle_intelligence.case_based_reasoning_engine import CaseBasedReasoningEngine
from qseries_v2.oracle_intelligence.market_dna_fingerprinting_engine import MarketDNAFingerprintingEngine
from qseries_v2.oracle_intelligence.analog_market_retrieval_engine import AnalogMarketRetrievalEngine
from qseries_v2.oracle_intelligence.outcome_distribution_engine import OutcomeDistributionEngine
from qseries_v2.oracle_intelligence.adaptive_confidence_learning_engine import AdaptiveConfidenceLearningEngine
from qseries_v2.oracle_intelligence.oracle_knowledge_graph import OracleKnowledgeGraph
from qseries_v2.oracle_intelligence.oracle_intelligence_synthesis_engine import OracleIntelligenceSynthesisEngine


def test_oi_051_oracle_intelligence_synthesis_engine():
    test_db = Path("qseries_v2") / "data" / "test_oracle_synthesis.sqlite3"

    if test_db.exists():
        test_db.unlink()

    memory_engine = OracleMemoryEngine()
    store = OraclePersistentMemoryStore(test_db)
    bridge = OracleMemoryPersistenceBridge(memory_engine, store)

    similarity = OracleSimilarityIntelligenceEngine(bridge)
    reasoning = CaseBasedReasoningEngine(similarity)
    dna = MarketDNAFingerprintingEngine()
    retrieval = AnalogMarketRetrievalEngine(similarity, dna)
    distribution = OutcomeDistributionEngine(retrieval)
    confidence = AdaptiveConfidenceLearningEngine(bridge)
    graph = OracleKnowledgeGraph(bridge)

    synthesis = OracleIntelligenceSynthesisEngine(
        similarity_engine=similarity,
        reasoning_engine=reasoning,
        dna_engine=dna,
        retrieval_engine=retrieval,
        distribution_engine=distribution,
        confidence_engine=confidence,
        knowledge_graph=graph,
    )

    for i in range(8):
        bridge.remember_and_persist(
            memory_type="forecast",
            market_ticker=f"SYN-YES-{i}",
            title=f"Synthesis YES case {i}",
            summary="Synthesis historical YES case.",
            confidence=86,
            importance=84,
            tags=["momentum", "yes"],
            source_module="test_oi_051",
            payload={
                "ticker": f"SYN-YES-{i}",
                "price": 78 + (i % 3),
                "implied_probability": 78 + (i % 3),
                "volume": 12000 + i * 100,
                "liquidity": 25000,
                "spread": 2,
                "momentum": 8,
                "volatility": 4,
                "time_to_expiration_minutes": 180,
                "category": "crypto",
                "regime": "trend",
                "strategy": "momentum",
                "pattern_name": "strong_momentum",
                "forecast": {
                    "predicted_side": "YES",
                    "confidence": 86,
                    "probability": 0.86,
                },
                "outcome": {
                    "result": "YES",
                    "move_pct": 5 + i,
                    "time_to_resolution_minutes": 30 + i,
                },
            },
        )

    for i in range(2):
        bridge.remember_and_persist(
            memory_type="forecast",
            market_ticker=f"SYN-NO-{i}",
            title=f"Synthesis NO case {i}",
            summary="Synthesis historical NO case.",
            confidence=74,
            importance=68,
            tags=["momentum", "no"],
            source_module="test_oi_051",
            payload={
                "ticker": f"SYN-NO-{i}",
                "price": 76,
                "implied_probability": 76,
                "volume": 10000,
                "liquidity": 22000,
                "spread": 3,
                "momentum": 7,
                "volatility": 5,
                "time_to_expiration_minutes": 190,
                "category": "crypto",
                "regime": "trend",
                "strategy": "momentum",
                "pattern_name": "strong_momentum",
                "forecast": {
                    "predicted_side": "YES",
                    "confidence": 74,
                    "probability": 0.74,
                },
                "outcome": {
                    "result": "NO",
                    "move_pct": -4,
                    "time_to_resolution_minutes": 42,
                },
            },
        )

    current = {
        "ticker": "SYN-CURRENT",
        "price": 79,
        "implied_probability": 79,
        "volume": 12100,
        "liquidity": 25000,
        "spread": 2,
        "momentum": 8,
        "volatility": 4,
        "time_to_expiration_minutes": 180,
        "category": "crypto",
        "regime": "trend",
        "strategy": "momentum",
        "pattern_name": "strong_momentum",
        "tags": ["momentum", "yes"],
    }

    result = synthesis.synthesize(current, limit=10)

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["summary"]["research_ready"] is True
    assert result["summary"]["analog_count"] == 10
    assert result["summary"]["expected_resolution"] == "YES"
    assert result["summary"]["adjusted_confidence"] is not None
    assert result["market_dna"]["dna_id"].startswith("dna_")
    assert result["analog_retrieval"]["top_analogs"]
    assert result["case_reasoning"]["expected_resolution"] == "YES"
    assert result["outcome_distribution"]["resolution_distribution"]["expected_resolution"] == "YES"

    status = synthesis.status()
    assert status["status"] == "ok"

    print("[PASS] OI-051 Oracle Intelligence Synthesis Engine")
    print(result["summary"])


if __name__ == "__main__":
    test_oi_051_oracle_intelligence_synthesis_engine()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .oracle_intelligence_synthesis_engine import oracle_intelligence_synthesis_engine, OracleIntelligenceSynthesisEngine\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-051 INSTALLER")
print(" Oracle Intelligence Synthesis Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-051 installed")
print()
print("Run:")
print("python test_oi_051_oracle_intelligence_synthesis_engine.py")