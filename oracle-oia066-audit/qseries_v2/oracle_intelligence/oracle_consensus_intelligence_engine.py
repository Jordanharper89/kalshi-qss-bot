"""
OI-054 Oracle Consensus Intelligence Engine

Purpose:
- Aggregate independent Oracle subsystem outputs into a consensus vote.
- Measure agreement, disagreement, confidence spread, research stability, and outliers.
- Strengthen Oracle research packets before they are presented to Q Series.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Any, Dict, List, Optional

from .oracle_intelligence_synthesis_engine import (
    oracle_intelligence_synthesis_engine,
    OracleIntelligenceSynthesisEngine,
)


class OracleConsensusIntelligenceEngine:
    module_name = "oi_054_oracle_consensus_intelligence_engine"

    def __init__(self, synthesis_engine: Optional[OracleIntelligenceSynthesisEngine] = None) -> None:
        self.synthesis_engine = synthesis_engine or oracle_intelligence_synthesis_engine

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "synthesis_engine": self._safe_status(self.synthesis_engine),
        }

    def build_consensus(
        self,
        current_setup: Dict[str, Any],
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 25,
    ) -> Dict[str, Any]:
        synthesis = self.synthesis_engine.synthesize(
            current_setup=current_setup,
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
            include_graph=True,
        )

        votes = self._extract_votes(synthesis)
        consensus = self._calculate_consensus(votes)
        explanation = self._explain(consensus, votes)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "market_ticker": synthesis.get("summary", {}).get("market_ticker"),
            "consensus": consensus,
            "votes": votes,
            "explanation": explanation,
            "synthesis": synthesis,
        }

    def build_consensus_from_synthesis(self, synthesis: Dict[str, Any]) -> Dict[str, Any]:
        votes = self._extract_votes(synthesis)
        consensus = self._calculate_consensus(votes)
        explanation = self._explain(consensus, votes)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "market_ticker": synthesis.get("summary", {}).get("market_ticker"),
            "consensus": consensus,
            "votes": votes,
            "explanation": explanation,
            "synthesis": synthesis,
        }

    def _extract_votes(self, synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
        votes = []

        summary = synthesis.get("summary", {}) or {}
        reasoning = synthesis.get("case_reasoning", {}) or {}
        distribution = synthesis.get("outcome_distribution", {}) or {}
        retrieval = synthesis.get("analog_retrieval", {}) or {}
        confidence = synthesis.get("adjusted_confidence", {}) or {}
        dna = synthesis.get("market_dna", {}) or {}
        graph = synthesis.get("knowledge_graph_context", {}) or {}

        resolution = distribution.get("resolution_distribution", {}) or {}

        self._add_vote(
            votes,
            engine="case_reasoning",
            side=reasoning.get("expected_resolution"),
            confidence=self._prob_to_conf(reasoning.get("expected_probability")),
            weight=0.24,
            evidence={"case_count": reasoning.get("case_count"), "risk_level": reasoning.get("risk_level")},
        )

        expected = resolution.get("expected_resolution")
        prob = resolution.get("yes_probability") if expected == "YES" else resolution.get("no_probability")
        self._add_vote(
            votes,
            engine="outcome_distribution",
            side=expected,
            confidence=self._prob_to_conf(prob),
            weight=0.24,
            evidence={"known_outcomes": resolution.get("known_outcome_count")},
        )

        top_analog = summary.get("top_analog") or {}
        self._add_vote(
            votes,
            engine="analog_retrieval",
            side=summary.get("expected_resolution"),
            confidence=top_analog.get("retrieval_score_pct") or retrieval.get("summary", {}).get("avg_retrieval_score_pct"),
            weight=0.18,
            evidence={"analog_count": summary.get("analog_count")},
        )

        self._add_vote(
            votes,
            engine="adaptive_confidence",
            side=summary.get("expected_resolution"),
            confidence=confidence.get("adjusted_confidence") or summary.get("adjusted_confidence"),
            weight=0.16,
            evidence={"delta": confidence.get("delta") or summary.get("confidence_delta")},
        )

        dna_traits = len(dna.get("traits", []) or [])
        dna_conf = min(95.0, 55.0 + dna_traits * 2.0) if dna_traits else None
        self._add_vote(
            votes,
            engine="market_dna",
            side=summary.get("expected_resolution"),
            confidence=dna_conf,
            weight=0.10,
            evidence={"dna_family": dna.get("dna_family"), "traits": dna_traits},
        )

        graph_summary = graph.get("graph_summary", {}) or {}
        graph_nodes = graph_summary.get("total_nodes") or summary.get("graph_nodes") or 0
        graph_edges = graph_summary.get("total_edges") or summary.get("graph_edges") or 0
        graph_conf = min(90.0, 50.0 + min(graph_nodes, 50) * 0.4 + min(graph_edges, 100) * 0.2)
        self._add_vote(
            votes,
            engine="knowledge_graph",
            side=summary.get("expected_resolution"),
            confidence=graph_conf if graph_nodes or graph_edges else None,
            weight=0.08,
            evidence={"nodes": graph_nodes, "edges": graph_edges},
        )

        return votes

    def _add_vote(
        self,
        votes: List[Dict[str, Any]],
        engine: str,
        side: Any,
        confidence: Any,
        weight: float,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> None:
        side = str(side or "UNKNOWN").upper()
        if side not in {"YES", "NO"}:
            side = "UNKNOWN"

        conf = self._clean_confidence(confidence)

        votes.append({
            "engine": engine,
            "side": side,
            "confidence": conf,
            "weight": float(weight),
            "usable": side in {"YES", "NO"} and conf is not None,
            "evidence": evidence or {},
        })

    def _calculate_consensus(self, votes: List[Dict[str, Any]]) -> Dict[str, Any]:
        usable = [v for v in votes if v.get("usable")]

        if not usable:
            return {
                "consensus_side": "UNKNOWN",
                "consensus_score": None,
                "consensus_score_pct": None,
                "agreement_pct": 0.0,
                "disagreement_pct": 100.0,
                "confidence_spread": None,
                "research_stability": "unknown",
                "research_certainty_index": 0.0,
                "outlier_engines": [],
            }

        yes_strength = 0.0
        no_strength = 0.0
        total_strength = 0.0

        for vote in usable:
            strength = vote["weight"] * (vote["confidence"] / 100.0)
            total_strength += strength

            if vote["side"] == "YES":
                yes_strength += strength
            elif vote["side"] == "NO":
                no_strength += strength

        if yes_strength >= no_strength:
            side = "YES"
            winning = yes_strength
            losing = no_strength
        else:
            side = "NO"
            winning = no_strength
            losing = yes_strength

        consensus_score = winning / total_strength if total_strength else 0.0
        agreement_votes = [v for v in usable if v["side"] == side]
        agreement_weight = sum(v["weight"] for v in agreement_votes)
        usable_weight = sum(v["weight"] for v in usable)

        agreement_pct = agreement_weight / usable_weight if usable_weight else 0.0
        disagreement_pct = 1.0 - agreement_pct

        confidences = [v["confidence"] for v in usable]
        spread = pstdev(confidences) if len(confidences) > 1 else 0.0

        outliers = self._outliers(usable, side, spread)
        stability = self._stability(consensus_score, agreement_pct, spread, outliers)

        certainty = self._certainty_index(
            consensus_score=consensus_score,
            agreement_pct=agreement_pct,
            spread=spread,
            usable_count=len(usable),
            outlier_count=len(outliers),
        )

        return {
            "consensus_side": side,
            "consensus_score": round(consensus_score, 4),
            "consensus_score_pct": round(consensus_score * 100.0, 2),
            "agreement_pct": round(agreement_pct * 100.0, 2),
            "disagreement_pct": round(disagreement_pct * 100.0, 2),
            "confidence_spread": round(spread, 2),
            "research_stability": stability,
            "research_certainty_index": round(certainty, 2),
            "yes_strength": round(yes_strength, 4),
            "no_strength": round(no_strength, 4),
            "outlier_engines": outliers,
            "usable_votes": len(usable),
            "total_votes": len(votes),
        }

    def _outliers(self, votes: List[Dict[str, Any]], consensus_side: str, spread: float) -> List[Dict[str, Any]]:
        if not votes:
            return []

        avg_conf = mean(v["confidence"] for v in votes)
        outliers = []

        for vote in votes:
            reason = None

            if vote["side"] != consensus_side:
                reason = "opposes_consensus"
            elif spread >= 12 and abs(vote["confidence"] - avg_conf) >= spread:
                reason = "confidence_outlier"

            if reason:
                outliers.append({
                    "engine": vote["engine"],
                    "side": vote["side"],
                    "confidence": vote["confidence"],
                    "reason": reason,
                })

        return outliers

    def _stability(
        self,
        consensus_score: float,
        agreement_pct: float,
        spread: float,
        outliers: List[Dict[str, Any]],
    ) -> str:
        if consensus_score >= 0.80 and agreement_pct >= 0.85 and spread <= 10 and not outliers:
            return "high"

        if consensus_score >= 0.65 and agreement_pct >= 0.65 and spread <= 18:
            return "medium"

        return "low"

    def _certainty_index(
        self,
        consensus_score: float,
        agreement_pct: float,
        spread: float,
        usable_count: int,
        outlier_count: int,
    ) -> float:
        base = consensus_score * 45.0 + agreement_pct * 35.0
        count_bonus = min(usable_count, 6) * 3.0
        spread_penalty = min(spread, 30.0) * 0.7
        outlier_penalty = outlier_count * 6.0

        return max(0.0, min(100.0, base + count_bonus - spread_penalty - outlier_penalty))

    def _explain(self, consensus: Dict[str, Any], votes: List[Dict[str, Any]]) -> List[str]:
        if consensus["consensus_side"] == "UNKNOWN":
            return ["Oracle could not form a usable consensus from subsystem votes."]

        lines = [
            f"Oracle consensus favors {consensus['consensus_side']} with {consensus['consensus_score_pct']}% consensus strength.",
            f"Subsystem agreement is {consensus['agreement_pct']}% with {consensus['disagreement_pct']}% disagreement.",
            f"Research stability is {consensus['research_stability']}.",
            f"Research certainty index is {consensus['research_certainty_index']}/100.",
        ]

        outliers = consensus.get("outlier_engines", [])
        if outliers:
            names = ", ".join(o["engine"] for o in outliers)
            lines.append(f"Outlier engines detected: {names}.")
        else:
            lines.append("No major outlier engines detected.")

        return lines

    def _prob_to_conf(self, value: Any) -> Optional[float]:
        if value is None:
            return None

        try:
            v = float(value)
            if v <= 1:
                v *= 100.0
            return self._clean_confidence(v)
        except Exception:
            return None

    def _clean_confidence(self, value: Any) -> Optional[float]:
        if value is None:
            return None

        try:
            v = float(value)
            return round(max(0.0, min(100.0, v)), 2)
        except Exception:
            return None

    def _safe_status(self, engine: Any) -> str:
        try:
            return engine.status().get("status", "unknown")
        except Exception:
            return "error"


oracle_consensus_intelligence_engine = OracleConsensusIntelligenceEngine()
