"""
OI-045 Case-Based Reasoning Engine

Turns similar historical memories into evidence-based expectations.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from collections import defaultdict

from .oracle_similarity_intelligence_engine import (
    oracle_similarity_intelligence_engine,
    OracleSimilarityIntelligenceEngine,
)


class CaseBasedReasoningEngine:
    module_name = "oi_045_case_based_reasoning_engine"

    def __init__(self, similarity_engine: Optional[OracleSimilarityIntelligenceEngine] = None) -> None:
        self.similarity_engine = similarity_engine or oracle_similarity_intelligence_engine

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "similarity_engine": self.similarity_engine.status()["status"],
        }

    def reason_from_cases(
        self,
        current_setup: Dict[str, Any],
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 25,
        min_similarity: float = 0.0,
    ) -> Dict[str, Any]:
        similarity_result = self.similarity_engine.find_similar_setups(
            current_setup=current_setup,
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
            min_similarity=min_similarity,
        )

        matches = similarity_result.get("top_matches", [])
        weighted = self._weighted_outcome_projection(matches)
        clusters = self._cluster_cases(matches)
        reasoning = self._build_reasoning(matches, weighted, clusters)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "query": current_setup,
            "case_count": len(matches),
            "expected_resolution": weighted["expected_resolution"],
            "expected_probability": weighted["expected_probability"],
            "historical_support": weighted["historical_support"],
            "weighted_yes": weighted["weighted_yes"],
            "weighted_no": weighted["weighted_no"],
            "weighted_unknown": weighted["weighted_unknown"],
            "avg_similarity_pct": weighted["avg_similarity_pct"],
            "avg_confidence": weighted["avg_confidence"],
            "risk_level": weighted["risk_level"],
            "clusters": clusters,
            "reasoning": reasoning,
            "similarity": similarity_result,
        }

    def _weighted_outcome_projection(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not matches:
            return {
                "expected_resolution": "UNKNOWN",
                "expected_probability": None,
                "historical_support": 0,
                "weighted_yes": 0.0,
                "weighted_no": 0.0,
                "weighted_unknown": 0.0,
                "avg_similarity_pct": 0.0,
                "avg_confidence": None,
                "risk_level": "unknown",
            }

        yes_weight = 0.0
        no_weight = 0.0
        unknown_weight = 0.0
        total_weight = 0.0
        similarities = []
        confidences = []

        for match in matches:
            memory = match.get("memory", {})
            similarity = float(match.get("similarity", 0.0))
            confidence = float(memory.get("confidence", 50.0)) / 100.0
            importance = float(memory.get("importance", 50.0)) / 100.0

            weight = max(0.01, similarity * 0.60 + confidence * 0.25 + importance * 0.15)
            total_weight += weight
            similarities.append(match.get("similarity_pct", 0.0))
            confidences.append(float(memory.get("confidence", 50.0)))

            result = self._extract_result(memory)

            if result == "YES":
                yes_weight += weight
            elif result == "NO":
                no_weight += weight
            else:
                unknown_weight += weight

        known = yes_weight + no_weight

        if known <= 0:
            expected_resolution = "UNKNOWN"
            expected_probability = None
        else:
            yes_prob = yes_weight / known
            no_prob = no_weight / known

            if yes_prob >= no_prob:
                expected_resolution = "YES"
                expected_probability = round(yes_prob, 4)
            else:
                expected_resolution = "NO"
                expected_probability = round(no_prob, 4)

        avg_similarity = sum(similarities) / len(similarities)
        avg_confidence = sum(confidences) / len(confidences)

        risk_level = self._risk_level(expected_probability, avg_similarity, len(matches))

        return {
            "expected_resolution": expected_resolution,
            "expected_probability": expected_probability,
            "historical_support": len(matches),
            "weighted_yes": round(yes_weight / total_weight, 4) if total_weight else 0.0,
            "weighted_no": round(no_weight / total_weight, 4) if total_weight else 0.0,
            "weighted_unknown": round(unknown_weight / total_weight, 4) if total_weight else 0.0,
            "avg_similarity_pct": round(avg_similarity, 2),
            "avg_confidence": round(avg_confidence, 2),
            "risk_level": risk_level,
        }

    def _cluster_cases(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        buckets = defaultdict(list)

        for match in matches:
            memory = match.get("memory", {})
            payload = memory.get("payload", {}) or {}

            key = (
                payload.get("pattern_name")
                or payload.get("regime")
                or payload.get("category")
                or memory.get("memory_type")
                or "unknown_cluster"
            )

            buckets[str(key)].append(match)

        clusters = []

        for name, items in buckets.items():
            yes = 0
            no = 0
            unknown = 0

            for item in items:
                result = self._extract_result(item.get("memory", {}))
                if result == "YES":
                    yes += 1
                elif result == "NO":
                    no += 1
                else:
                    unknown += 1

            known = yes + no

            clusters.append({
                "cluster": name,
                "occurrences": len(items),
                "yes_count": yes,
                "no_count": no,
                "unknown_count": unknown,
                "yes_rate": round(yes / known, 4) if known else None,
                "avg_similarity_pct": round(sum(i["similarity_pct"] for i in items) / len(items), 2),
            })

        clusters.sort(key=lambda c: (c["occurrences"], c["avg_similarity_pct"]), reverse=True)
        return clusters

    def _build_reasoning(
        self,
        matches: List[Dict[str, Any]],
        weighted: Dict[str, Any],
        clusters: List[Dict[str, Any]],
    ) -> List[str]:
        if not matches:
            return ["No historical cases were available for this setup."]

        lines = []

        lines.append(
            f"Oracle found {len(matches)} similar historical cases with average similarity "
            f"{weighted['avg_similarity_pct']}%."
        )

        if weighted["expected_probability"] is not None:
            pct = round(weighted["expected_probability"] * 100, 2)
            lines.append(
                f"Weighted historical evidence favors {weighted['expected_resolution']} at {pct}%."
            )
        else:
            lines.append("Historical cases did not contain enough resolved outcomes.")

        if clusters:
            top = clusters[0]
            lines.append(
                f"Largest case cluster is '{top['cluster']}' with {top['occurrences']} occurrences."
            )

            if top["yes_rate"] is not None:
                lines.append(
                    f"That cluster resolved YES {round(top['yes_rate'] * 100, 2)}% of known outcomes."
                )

        lines.append(f"Risk level classified as {weighted['risk_level']}.")

        return lines

    def _extract_result(self, memory: Dict[str, Any]) -> str:
        payload = memory.get("payload", {}) or {}
        outcome = payload.get("outcome", {}) if isinstance(payload.get("outcome"), dict) else {}

        result = (
            outcome.get("result")
            or outcome.get("resolved_side")
            or outcome.get("winner")
            or payload.get("result")
            or payload.get("resolved_side")
        )

        if result is None:
            return "UNKNOWN"

        result = str(result).upper()

        if result in {"YES", "NO"}:
            return result

        return "UNKNOWN"

    def _risk_level(self, probability: Optional[float], avg_similarity_pct: float, count: int) -> str:
        if probability is None or count < 3:
            return "high"

        if probability >= 0.80 and avg_similarity_pct >= 80 and count >= 10:
            return "low"

        if probability >= 0.65 and avg_similarity_pct >= 65 and count >= 5:
            return "medium"

        return "high"


case_based_reasoning_engine = CaseBasedReasoningEngine()
