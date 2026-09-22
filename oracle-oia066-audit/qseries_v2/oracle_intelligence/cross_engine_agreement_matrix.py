"""
OI-078 Cross-Engine Agreement Matrix

Purpose:
- Measure agreement/disagreement between Oracle subsystem votes.
- Track pair accuracy, false agreement, false disagreement, confidence spread,
  alpha contribution, and consensus diversity.
- Help Oracle understand which engine combinations are strongest or weakest.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple


class CrossEngineAgreementMatrix:
    module_name = "oi_078_cross_engine_agreement_matrix"

    def __init__(self) -> None:
        self._pair_history: Dict[str, List[Dict[str, Any]]] = {}

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "pairs_tracked": len(self._pair_history),
            "records": sum(len(v) for v in self._pair_history.values()),
        }

    def analyze_votes(
        self,
        votes: List[Dict[str, Any]],
        actual_side: Optional[str] = None,
        market_ticker: Optional[str] = None,
        record: bool = True,
    ) -> Dict[str, Any]:
        clean_votes = [self._clean_vote(v) for v in votes or []]
        clean_votes = [v for v in clean_votes if v["side"] in {"YES", "NO"}]

        actual = self._side(actual_side)
        pair_rows = []

        for a, b in combinations(clean_votes, 2):
            row = self._pair_result(a, b, actual, market_ticker)

            if record:
                self._pair_history.setdefault(row["pair_key"], []).append(row)

            pair_rows.append(row)

        matrix = self._matrix(pair_rows)
        diversity = self._consensus_diversity(clean_votes, pair_rows)
        summary = self._summary(pair_rows)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "market_ticker": market_ticker,
            "actual_side": actual,
            "vote_count": len(clean_votes),
            "pair_count": len(pair_rows),
            "pairs": pair_rows,
            "matrix": matrix,
            "consensus_diversity": diversity,
            "summary": summary,
        }

    def analyze_consensus_packet(
        self,
        packet: Dict[str, Any],
        actual_side: Optional[str] = None,
        record: bool = True,
    ) -> Dict[str, Any]:
        votes = packet.get("consensus_votes", []) or []
        ticker = packet.get("market_ticker") or packet.get("summary", {}).get("market_ticker")

        return self.analyze_votes(
            votes=votes,
            actual_side=actual_side,
            market_ticker=ticker,
            record=record,
        )

    def historical_matrix(self) -> Dict[str, Any]:
        rows = []

        for pair_key, records in self._pair_history.items():
            rows.append(self._historical_pair_summary(pair_key, records))

        rows.sort(key=lambda r: (r["historical_accuracy"], r["agreement_pct"]), reverse=True)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "pair_count": len(rows),
            "pairs": rows,
            "strongest_pair": rows[0] if rows else None,
            "weakest_pair": rows[-1] if rows else None,
            "recommended_pair_boosts": self._recommended_pair_boosts(rows),
        }

    def _pair_result(
        self,
        a: Dict[str, Any],
        b: Dict[str, Any],
        actual: Optional[str],
        market_ticker: Optional[str],
    ) -> Dict[str, Any]:
        engines = sorted([a["engine"], b["engine"]])
        pair_key = "+".join(engines)

        agreed = a["side"] == b["side"]
        avg_confidence = (a["confidence"] + b["confidence"]) / 2.0
        confidence_spread = abs(a["confidence"] - b["confidence"])

        pair_side = a["side"] if agreed else "DISAGREE"

        correct_agreement = bool(agreed and actual and pair_side == actual)
        false_agreement = bool(agreed and actual and pair_side != actual)
        useful_disagreement = bool((not agreed) and actual and (a["side"] == actual or b["side"] == actual))
        false_disagreement = bool((not agreed) and actual and a["side"] != actual and b["side"] != actual)

        alpha_contribution = self._alpha_contribution(
            agreed=agreed,
            correct_agreement=correct_agreement,
            false_agreement=false_agreement,
            useful_disagreement=useful_disagreement,
            avg_confidence=avg_confidence,
        )

        return {
            "pair_key": pair_key,
            "engines": engines,
            "market_ticker": market_ticker,
            "engine_a": a,
            "engine_b": b,
            "agreed": agreed,
            "pair_side": pair_side,
            "actual_side": actual,
            "avg_confidence": round(avg_confidence, 2),
            "confidence_spread": round(confidence_spread, 2),
            "correct_agreement": correct_agreement,
            "false_agreement": false_agreement,
            "useful_disagreement": useful_disagreement,
            "false_disagreement": false_disagreement,
            "alpha_contribution": round(alpha_contribution, 4),
        }

    def _historical_pair_summary(self, pair_key: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(records)
        agreements = [r for r in records if r["agreed"]]
        disagreements = [r for r in records if not r["agreed"]]
        resolved = [r for r in records if r.get("actual_side") in {"YES", "NO"}]

        correct = [
            r for r in resolved
            if (
                (r["agreed"] and r["correct_agreement"])
                or ((not r["agreed"]) and r["useful_disagreement"])
            )
        ]

        false_agreements = [r for r in records if r["false_agreement"]]
        false_disagreements = [r for r in records if r["false_disagreement"]]

        return {
            "pair_key": pair_key,
            "engines": pair_key.split("+"),
            "count": total,
            "agreement_pct": round(len(agreements) / total * 100.0, 2) if total else 0.0,
            "disagreement_pct": round(len(disagreements) / total * 100.0, 2) if total else 0.0,
            "historical_accuracy": round(len(correct) / len(resolved) * 100.0, 2) if resolved else 0.0,
            "false_agreement_rate": round(len(false_agreements) / total * 100.0, 2) if total else 0.0,
            "false_disagreement_rate": round(len(false_disagreements) / total * 100.0, 2) if total else 0.0,
            "avg_confidence": round(sum(r["avg_confidence"] for r in records) / total, 2) if total else 0.0,
            "avg_confidence_spread": round(sum(r["confidence_spread"] for r in records) / total, 2) if total else 0.0,
            "avg_alpha_contribution": round(sum(r["alpha_contribution"] for r in records) / total, 4) if total else 0.0,
        }

    def _matrix(self, pairs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        matrix: Dict[str, Dict[str, Any]] = {}

        for pair in pairs:
            a, b = pair["engines"]
            matrix.setdefault(a, {})
            matrix.setdefault(b, {})

            cell = {
                "agreed": pair["agreed"],
                "pair_side": pair["pair_side"],
                "avg_confidence": pair["avg_confidence"],
                "confidence_spread": pair["confidence_spread"],
                "alpha_contribution": pair["alpha_contribution"],
            }

            matrix[a][b] = cell
            matrix[b][a] = cell

        return matrix

    def _consensus_diversity(
        self,
        votes: List[Dict[str, Any]],
        pairs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not votes:
            return {
                "diversity_level": "unknown",
                "diversity_score": 0.0,
                "agreement_density": 0.0,
                "engine_count": 0,
            }

        pair_count = len(pairs)
        agreement_count = sum(1 for p in pairs if p["agreed"])
        agreement_density = agreement_count / pair_count if pair_count else 0.0

        unique_sides = set(v["side"] for v in votes)
        engine_count = len(set(v["engine"] for v in votes))
        avg_confidence_spread = (
            sum(p["confidence_spread"] for p in pairs) / pair_count
            if pair_count else 0.0
        )

        diversity_score = 50.0
        diversity_score += min(engine_count, 8) * 5.0
        diversity_score += (1.0 - agreement_density) * 20.0
        diversity_score -= min(avg_confidence_spread, 30.0) * 0.5

        if len(unique_sides) == 1 and engine_count >= 4:
            diversity_score += 10.0

        diversity_score = max(0.0, min(100.0, diversity_score))

        if diversity_score >= 80:
            level = "high"
        elif diversity_score >= 60:
            level = "medium"
        else:
            level = "low"

        return {
            "diversity_level": level,
            "diversity_score": round(diversity_score, 2),
            "agreement_density": round(agreement_density, 4),
            "engine_count": engine_count,
            "avg_confidence_spread": round(avg_confidence_spread, 2),
        }

    def _summary(self, pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not pairs:
            return {
                "strongest_pair": None,
                "weakest_pair": None,
                "agreement_pairs": 0,
                "disagreement_pairs": 0,
            }

        strongest = max(pairs, key=lambda p: p["alpha_contribution"])
        weakest = min(pairs, key=lambda p: p["alpha_contribution"])

        return {
            "strongest_pair": {
                "pair_key": strongest["pair_key"],
                "alpha_contribution": strongest["alpha_contribution"],
                "agreed": strongest["agreed"],
            },
            "weakest_pair": {
                "pair_key": weakest["pair_key"],
                "alpha_contribution": weakest["alpha_contribution"],
                "agreed": weakest["agreed"],
            },
            "agreement_pairs": sum(1 for p in pairs if p["agreed"]),
            "disagreement_pairs": sum(1 for p in pairs if not p["agreed"]),
        }

    def _recommended_pair_boosts(self, rows: List[Dict[str, Any]]) -> Dict[str, float]:
        boosts = {}

        for row in rows:
            accuracy = row["historical_accuracy"]
            alpha = row["avg_alpha_contribution"]
            false_agreement = row["false_agreement_rate"]

            if accuracy >= 85 and alpha > 0 and false_agreement <= 10:
                boost = 3.0
            elif accuracy >= 75 and alpha > 0:
                boost = 1.5
            elif accuracy <= 55 or false_agreement >= 30:
                boost = -3.0
            else:
                boost = 0.0

            boosts[row["pair_key"]] = boost

        return boosts

    def _alpha_contribution(
        self,
        agreed: bool,
        correct_agreement: bool,
        false_agreement: bool,
        useful_disagreement: bool,
        avg_confidence: float,
    ) -> float:
        base = avg_confidence / 100.0

        if correct_agreement:
            return base
        if false_agreement:
            return -base
        if useful_disagreement:
            return base * 0.35
        if not agreed:
            return -base * 0.15
        return 0.0

    def _clean_vote(self, vote: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "engine": str(vote.get("engine") or "unknown_engine"),
            "side": self._side(vote.get("side")),
            "confidence": self._num(vote.get("confidence"), 50.0),
            "weight": self._num(vote.get("weight"), 0.0),
            "raw": vote,
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


cross_engine_agreement_matrix = CrossEngineAgreementMatrix()
