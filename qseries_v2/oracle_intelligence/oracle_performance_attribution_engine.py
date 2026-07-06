"""
OI-077 Oracle Performance Attribution Engine

Purpose:
- Attribute Oracle prediction performance to contributing engines/evidence.
- Identify strongest positive contributors, weakest contributors, false confidence,
  alpha contribution, and negative attribution.
- Feed Meta Intelligence, Dynamic Weighting, and Research Quality layers.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class OraclePerformanceAttributionEngine:
    module_name = "oi_077_oracle_performance_attribution_engine"

    def __init__(self) -> None:
        self._records: List[Dict[str, Any]] = []

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "records": len(self._records),
        }

    def attribute_packet(
        self,
        packet: Dict[str, Any],
        actual_side: Optional[str] = None,
        market_ticker: Optional[str] = None,
    ) -> Dict[str, Any]:
        summary = packet.get("summary", {}) or {}
        signals = packet.get("signals", {}) or {}
        votes = packet.get("consensus_votes", []) or []
        consensus = packet.get("consensus", {}) or {}

        ticker = market_ticker or packet.get("market_ticker") or summary.get("market_ticker")
        predicted = self._side(
            summary.get("expected_resolution")
            or signals.get("expected_resolution")
            or consensus.get("consensus_side")
        )
        actual = self._side(actual_side)

        correct = predicted == actual if predicted and actual else None
        contributors = self._engine_contributors(votes, predicted, actual)
        attribution = self._aggregate_contributors(contributors)

        result = {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "market_ticker": ticker,
            "predicted_side": predicted,
            "actual_side": actual,
            "correct": correct,
            "contributors": contributors,
            "attribution": attribution,
            "packet_quality": {
                "research_grade": signals.get("final_research_grade") or signals.get("research_grade"),
                "research_quality_score": summary.get("research_quality_score"),
                "consensus_score_pct": consensus.get("consensus_score_pct") or summary.get("consensus_score_pct"),
                "agreement_pct": consensus.get("agreement_pct") or summary.get("agreement_pct"),
            },
            "execution_enabled": False,
            "execution_owner": "Q Series",
        }

        self._records.append(result)
        return result

    def attribution_summary(self, limit: Optional[int] = None) -> Dict[str, Any]:
        rows = self._records[-limit:] if limit else self._records
        by_engine: Dict[str, Dict[str, Any]] = {}

        for record in rows:
            for contributor in record.get("contributors", []):
                name = contributor["engine"]
                bucket = by_engine.setdefault(name, {
                    "engine": name,
                    "count": 0,
                    "positive_total": 0.0,
                    "negative_total": 0.0,
                    "net_total": 0.0,
                    "correct_support": 0,
                    "false_support": 0,
                })

                bucket["count"] += 1
                bucket["positive_total"] += contributor["positive_contribution"]
                bucket["negative_total"] += contributor["negative_contribution"]
                bucket["net_total"] += contributor["net_contribution"]

                if contributor["supported_correct_outcome"]:
                    bucket["correct_support"] += 1
                if contributor["supported_wrong_outcome"]:
                    bucket["false_support"] += 1

        engine_rows = []
        for item in by_engine.values():
            count = item["count"] or 1
            engine_rows.append({
                "engine": item["engine"],
                "count": item["count"],
                "avg_positive_contribution": round(item["positive_total"] / count, 4),
                "avg_negative_contribution": round(item["negative_total"] / count, 4),
                "avg_net_contribution": round(item["net_total"] / count, 4),
                "correct_support_rate": round(item["correct_support"] / count, 4),
                "false_support_rate": round(item["false_support"] / count, 4),
            })

        engine_rows.sort(key=lambda x: x["avg_net_contribution"], reverse=True)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "records_analyzed": len(rows),
            "engine_attribution": engine_rows,
            "best_engine": engine_rows[0]["engine"] if engine_rows else None,
            "weakest_engine": engine_rows[-1]["engine"] if engine_rows else None,
        }

    def _engine_contributors(
        self,
        votes: List[Dict[str, Any]],
        predicted: Optional[str],
        actual: Optional[str],
    ) -> List[Dict[str, Any]]:
        contributors = []

        for vote in votes:
            engine = vote.get("engine") or "unknown_engine"
            side = self._side(vote.get("side"))
            confidence = self._num(vote.get("confidence"), 50.0)
            weight = self._num(vote.get("weight"), 0.0)

            evidence_strength = max(0.0, min(100.0, confidence)) * max(0.0, weight)
            supports_prediction = side == predicted if side and predicted else False
            supported_correct = side == actual if side and actual else False
            supported_wrong = actual is not None and side is not None and side != actual

            positive = evidence_strength if supported_correct else 0.0
            negative = evidence_strength if supported_wrong else 0.0
            net = positive - negative

            contributors.append({
                "engine": engine,
                "side": side,
                "confidence": round(confidence, 2),
                "weight": round(weight, 4),
                "evidence_strength": round(evidence_strength, 4),
                "supports_prediction": supports_prediction,
                "supported_correct_outcome": supported_correct,
                "supported_wrong_outcome": supported_wrong,
                "positive_contribution": round(positive, 4),
                "negative_contribution": round(negative, 4),
                "net_contribution": round(net, 4),
            })

        contributors.sort(key=lambda x: x["net_contribution"], reverse=True)
        return contributors

    def _aggregate_contributors(self, contributors: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not contributors:
            return {
                "largest_positive_contributor": None,
                "largest_negative_contributor": None,
                "positive_support_count": 0,
                "negative_support_count": 0,
                "alpha_added": 0.0,
                "noise_score": 0.0,
            }

        positive = [c for c in contributors if c["positive_contribution"] > 0]
        negative = [c for c in contributors if c["negative_contribution"] > 0]

        total_positive = sum(c["positive_contribution"] for c in contributors)
        total_negative = sum(c["negative_contribution"] for c in contributors)
        total_strength = sum(c["evidence_strength"] for c in contributors) or 1.0

        largest_positive = max(positive, key=lambda c: c["positive_contribution"]) if positive else None
        largest_negative = max(negative, key=lambda c: c["negative_contribution"]) if negative else None

        alpha_added = (total_positive - total_negative) / total_strength * 100.0
        noise_score = total_negative / total_strength * 100.0

        return {
            "largest_positive_contributor": largest_positive["engine"] if largest_positive else None,
            "largest_negative_contributor": largest_negative["engine"] if largest_negative else None,
            "positive_support_count": len(positive),
            "negative_support_count": len(negative),
            "alpha_added": round(alpha_added, 2),
            "noise_score": round(noise_score, 2),
            "total_positive": round(total_positive, 4),
            "total_negative": round(total_negative, 4),
        }

    def _side(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        value = str(value).upper()
        return value if value in {"YES", "NO"} else None

    def _num(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return default


oracle_performance_attribution_engine = OraclePerformanceAttributionEngine()
