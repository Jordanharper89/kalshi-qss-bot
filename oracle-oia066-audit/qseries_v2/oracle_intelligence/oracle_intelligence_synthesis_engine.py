"""
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
