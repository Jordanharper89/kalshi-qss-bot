"""
Oracle Consensus Engine

ORACLE-046

Purpose:
- Collect independent subsystem opinions.
- Convert subsystem outputs into weighted votes.
- Detect agreement, disagreement, conflict, and final direction.
- Produce institutional-style final recommendations.

Initial engines:
- Market Intelligence
- Evidence Engine
- Historical Similarity
- Learning Engine
- Final Fusion
- Arbitrage Engine
- Research Engine
- Opportunity Ranking
- Historical Memory placeholder
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
import math


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return float(value)
        return float(value)
    except Exception:
        return default


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _lower_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _extract_any(item: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    for key in keys:
        if key in item and item.get(key) is not None:
            return item.get(key)
    return default


@dataclass
class EngineVote:
    engine: str
    direction: str
    confidence: float
    weight: float
    weighted_score: float
    reason: str
    raw_signal: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleConsensusEngine:
    def __init__(self):
        self.version = "ORACLE-046"
        self.engine_weights = {
            "market_intelligence": 1.15,
            "evidence_engine": 1.20,
            "historical_similarity": 0.95,
            "learning_engine": 1.10,
            "final_fusion": 1.35,
            "arbitrage_engine": 1.30,
            "research_engine": 0.90,
            "opportunity_ranking": 1.00,
            "historical_memory": 0.55,
        }

    def _normalize_direction(self, raw: Any, fallback_score: Optional[float] = None) -> str:
        text = _lower_text(raw)

        buy_yes_words = [
            "buy_yes", "buy yes", "yes", "long_yes", "long yes",
            "recommend_yes", "positive_yes"
        ]
        buy_no_words = [
            "buy_no", "buy no", "no", "long_no", "long no",
            "recommend_no", "positive_no"
        ]
        watch_words = [
            "watch", "monitor", "wait", "hold", "neutral_positive",
            "developing", "relative value"
        ]
        pass_words = [
            "pass", "avoid", "skip", "reject", "no_trade", "bad",
            "weak", "false_positive"
        ]

        if any(word in text for word in buy_yes_words):
            return "BUY YES"
        if any(word in text for word in buy_no_words):
            return "BUY NO"
        if any(word in text for word in pass_words):
            return "PASS"
        if any(word in text for word in watch_words):
            return "WATCH"

        if fallback_score is not None:
            score = _safe_float(fallback_score)
            if score >= 75:
                return "BUY YES"
            if score >= 58:
                return "WATCH"
            if score <= 35:
                return "PASS"

        return "WATCH"

    def _direction_value(self, direction: str) -> float:
        direction = direction.upper()
        if direction == "BUY YES":
            return 1.0
        if direction == "BUY NO":
            return -1.0
        if direction == "WATCH":
            return 0.25
        return 0.0

    def _make_vote(
        self,
        engine: str,
        item: Dict[str, Any],
        direction_keys: List[str],
        confidence_keys: List[str],
        reason_keys: List[str],
        fallback_score_keys: Optional[List[str]] = None,
    ) -> Optional[EngineVote]:
        if not isinstance(item, dict):
            return None

        fallback_score = None
        if fallback_score_keys:
            fallback_score = _extract_any(item, fallback_score_keys, None)

        raw_direction = _extract_any(item, direction_keys, None)
        direction = self._normalize_direction(raw_direction, fallback_score)

        confidence = _safe_float(
            _extract_any(item, confidence_keys, fallback_score if fallback_score is not None else 50.0),
            50.0,
        )
        confidence = _clamp(confidence)

        weight = self.engine_weights.get(engine, 1.0)
        weighted_score = self._direction_value(direction) * confidence * weight

        reason = str(_extract_any(item, reason_keys, f"{engine} signal interpreted as {direction}"))

        return EngineVote(
            engine=engine,
            direction=direction,
            confidence=round(confidence, 2),
            weight=round(weight, 2),
            weighted_score=round(weighted_score, 2),
            reason=reason[:280],
            raw_signal=raw_direction,
        )

    def collect_votes(self, opportunity: Dict[str, Any]) -> List[EngineVote]:
        votes: List[EngineVote] = []

        # Market Intelligence
        mi = opportunity.get("market_intelligence") or opportunity.get("intelligence") or {}
        vote = self._make_vote(
            "market_intelligence",
            mi,
            ["recommendation", "direction", "signal", "action"],
            ["confidence", "confidence_score", "score", "intelligence_score"],
            ["reason", "summary", "explanation", "thesis"],
            ["score", "intelligence_score", "edge_score"],
        )
        if vote:
            votes.append(vote)

        # Evidence Engine
        ev = opportunity.get("evidence") or opportunity.get("evidence_engine") or {}
        vote = self._make_vote(
            "evidence_engine",
            ev,
            ["recommendation", "direction", "signal", "verdict"],
            ["confidence", "evidence_confidence", "score", "evidence_score"],
            ["reason", "summary", "evidence_summary", "thesis"],
            ["evidence_score", "score"],
        )
        if vote:
            votes.append(vote)

        # Historical Similarity
        sim = opportunity.get("similarity") or opportunity.get("historical_similarity") or {}
        vote = self._make_vote(
            "historical_similarity",
            sim,
            ["recommendation", "direction", "signal", "match_bias"],
            ["confidence", "similarity_confidence", "score", "similarity_score"],
            ["reason", "summary", "match_summary", "thesis"],
            ["similarity_score", "score"],
        )
        if vote:
            votes.append(vote)

        # Learning Engine
        learn = opportunity.get("learning") or opportunity.get("learning_engine") or {}
        vote = self._make_vote(
            "learning_engine",
            learn,
            ["recommendation", "direction", "signal", "learned_bias"],
            ["confidence", "learning_confidence", "score", "learning_score"],
            ["reason", "summary", "learning_summary", "thesis"],
            ["learning_score", "score"],
        )
        if vote:
            votes.append(vote)

        # Final Fusion
        fusion = opportunity.get("fusion") or opportunity.get("final_fusion") or {}
        vote = self._make_vote(
            "final_fusion",
            fusion,
            ["recommendation", "direction", "signal", "final_action"],
            ["confidence", "fusion_confidence", "score", "fusion_score", "final_score"],
            ["reason", "summary", "fusion_summary", "thesis"],
            ["fusion_score", "final_score", "score"],
        )
        if vote:
            votes.append(vote)

        # Arbitrage Engine
        arb = opportunity.get("arbitrage") or opportunity.get("arbitrage_engine") or {}
        vote = self._make_vote(
            "arbitrage_engine",
            arb,
            ["recommendation", "direction", "signal", "kind"],
            ["confidence", "confidence_score", "edge_pct", "arb_score"],
            ["reason", "summary", "explanation", "recommendation"],
            ["confidence", "edge_pct", "arb_score"],
        )
        if vote:
            votes.append(vote)

        # Research Engine
        research = opportunity.get("research") or opportunity.get("research_engine") or {}
        vote = self._make_vote(
            "research_engine",
            research,
            ["recommendation", "direction", "signal", "action"],
            ["confidence", "score", "research_score"],
            ["reason", "summary", "thesis", "explanation"],
            ["score", "research_score"],
        )
        if vote:
            votes.append(vote)

        # Opportunity Ranking
        ranking = opportunity.get("ranking") or opportunity.get("opportunity_ranking") or {}
        vote = self._make_vote(
            "opportunity_ranking",
            ranking,
            ["recommendation", "direction", "signal", "rank_action"],
            ["confidence", "score", "rank_score", "opportunity_score"],
            ["reason", "summary", "rank_reason", "thesis"],
            ["score", "rank_score", "opportunity_score"],
        )
        if vote:
            votes.append(vote)

        # Historical Memory placeholder
        memory = opportunity.get("historical_memory") or {}
        if memory:
            vote = self._make_vote(
                "historical_memory",
                memory,
                ["recommendation", "direction", "signal"],
                ["confidence", "score", "memory_score"],
                ["reason", "summary", "memory_summary"],
                ["score", "memory_score"],
            )
            if vote:
                votes.append(vote)
        else:
            votes.append(
                EngineVote(
                    engine="historical_memory",
                    direction="WATCH",
                    confidence=25.0,
                    weight=self.engine_weights["historical_memory"],
                    weighted_score=round(0.25 * 25.0 * self.engine_weights["historical_memory"], 2),
                    reason="Historical Memory placeholder active; no stored memory vote yet.",
                    raw_signal="placeholder",
                )
            )

        return votes

    def calculate_consensus(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        votes = self.collect_votes(opportunity)

        if not votes:
            return {
                "module": "oracle_consensus_engine",
                "version": self.version,
                "status": "no_votes",
                "timestamp": datetime.utcnow().isoformat(),
                "final_recommendation": "WATCH",
                "consensus_confidence": 0.0,
                "consensus_strength": "NO SIGNAL",
                "engine_agreement_pct": 0.0,
                "weighted_agreement": 0.0,
                "conflicts": [],
                "votes": [],
            }

        direction_counts: Dict[str, int] = {}
        weighted_direction_scores: Dict[str, float] = {}

        for vote in votes:
            direction_counts[vote.direction] = direction_counts.get(vote.direction, 0) + 1
            weighted_direction_scores[vote.direction] = weighted_direction_scores.get(vote.direction, 0.0) + abs(vote.weighted_score)

        leading_direction = max(
            weighted_direction_scores,
            key=lambda k: weighted_direction_scores.get(k, 0.0),
        )

        total_votes = len(votes)
        leading_votes = direction_counts.get(leading_direction, 0)
        engine_agreement_pct = round((leading_votes / total_votes) * 100.0, 2)

        total_weighted_abs = sum(abs(v.weighted_score) for v in votes) or 1.0
        leading_weighted = weighted_direction_scores.get(leading_direction, 0.0)
        weighted_agreement = round((leading_weighted / total_weighted_abs) * 100.0, 2)

        buy_yes_power = weighted_direction_scores.get("BUY YES", 0.0)
        buy_no_power = weighted_direction_scores.get("BUY NO", 0.0)
        watch_power = weighted_direction_scores.get("WATCH", 0.0)
        pass_power = weighted_direction_scores.get("PASS", 0.0)

        conflict_pairs = []
        if buy_yes_power > 0 and buy_no_power > 0:
            conflict_pairs.append("BUY YES vs BUY NO")
        if leading_direction in ("BUY YES", "BUY NO") and pass_power > leading_weighted * 0.35:
            conflict_pairs.append(f"{leading_direction} vs PASS")
        if leading_direction in ("BUY YES", "BUY NO") and watch_power > leading_weighted * 0.45:
            conflict_pairs.append(f"{leading_direction} vs WATCH")

        conflict_penalty = min(30.0, len(conflict_pairs) * 12.5)

        avg_confidence = sum(v.confidence for v in votes) / len(votes)
        consensus_confidence = (
            (weighted_agreement * 0.48)
            + (engine_agreement_pct * 0.27)
            + (avg_confidence * 0.25)
            - conflict_penalty
        )
        consensus_confidence = round(_clamp(consensus_confidence), 2)

        if consensus_confidence >= 82 and weighted_agreement >= 70:
            strength = "VERY STRONG"
        elif consensus_confidence >= 72 and weighted_agreement >= 62:
            strength = "STRONG"
        elif consensus_confidence >= 60:
            strength = "MODERATE"
        elif consensus_confidence >= 45:
            strength = "WEAK"
        else:
            strength = "CONFLICTED"

        final_recommendation = leading_direction

        if consensus_confidence < 48:
            final_recommendation = "PASS"
        elif consensus_confidence < 62 and leading_direction in ("BUY YES", "BUY NO"):
            final_recommendation = "WATCH"

        if "BUY YES vs BUY NO" in conflict_pairs and consensus_confidence < 72:
            final_recommendation = "WATCH"

        terminal_summary = self._build_terminal_summary(
            opportunity=opportunity,
            votes=votes,
            final_recommendation=final_recommendation,
            consensus_confidence=consensus_confidence,
            strength=strength,
            engine_agreement_pct=engine_agreement_pct,
            weighted_agreement=weighted_agreement,
            conflicts=conflict_pairs,
        )

        return {
            "module": "oracle_consensus_engine",
            "version": self.version,
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "final_recommendation": final_recommendation,
            "consensus_confidence": consensus_confidence,
            "consensus_strength": strength,
            "engine_agreement_pct": engine_agreement_pct,
            "weighted_agreement": weighted_agreement,
            "direction_counts": direction_counts,
            "weighted_direction_scores": {
                k: round(v, 2) for k, v in weighted_direction_scores.items()
            },
            "conflicts": conflict_pairs,
            "votes": [v.to_dict() for v in votes],
            "terminal_summary": terminal_summary,
        }

    def _build_terminal_summary(
        self,
        opportunity: Dict[str, Any],
        votes: List[EngineVote],
        final_recommendation: str,
        consensus_confidence: float,
        strength: str,
        engine_agreement_pct: float,
        weighted_agreement: float,
        conflicts: List[str],
    ) -> str:
        ticker = (
            opportunity.get("ticker")
            or opportunity.get("market_ticker")
            or opportunity.get("series_ticker")
            or "UNKNOWN"
        )

        title = (
            opportunity.get("title")
            or opportunity.get("market_title")
            or opportunity.get("name")
            or "Untitled opportunity"
        )

        vote_lines = []
        for vote in votes:
            vote_lines.append(
                f"- {vote.engine}: {vote.direction} "
                f"({vote.confidence:.1f}% conf, weight {vote.weight:.2f})"
            )

        conflict_text = ", ".join(conflicts) if conflicts else "None detected"

        return (
            "\n"
            "================ ORACLE CONSENSUS TERMINAL ================\n"
            f"Ticker: {ticker}\n"
            f"Market: {title}\n"
            f"Final Recommendation: {final_recommendation}\n"
            f"Consensus Confidence: {consensus_confidence:.2f}%\n"
            f"Consensus Strength: {strength}\n"
            f"Engine Agreement: {engine_agreement_pct:.2f}%\n"
            f"Weighted Agreement: {weighted_agreement:.2f}%\n"
            f"Conflicts: {conflict_text}\n"
            "---------------- Engine Votes ----------------\n"
            + "\n".join(vote_lines)
            + "\n============================================================\n"
        )

    def analyze_many(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for item in opportunities or []:
            enriched = dict(item)
            enriched["consensus"] = self.calculate_consensus(item)
            results.append(enriched)

        results.sort(
            key=lambda x: (
                x.get("consensus", {}).get("consensus_confidence", 0),
                x.get("consensus", {}).get("weighted_agreement", 0),
            ),
            reverse=True,
        )
        return results

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "oracle_consensus_engine",
            "version": self.version,
            "status": "ok",
            "engine_weights": dict(self.engine_weights),
            "engines": list(self.engine_weights.keys()),
        }


oracle_consensus_engine = OracleConsensusEngine()




# ============================================================
# ORACLE-046.0.3 Consensus Signal Adapter
# ============================================================

def _oracle04603_num(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _oracle04603_text(value):
    return str(value or "").strip()


def _oracle04603_direction_from_ranked(item):
    side = _oracle04603_text(item.get("side")).upper()
    grade = _oracle04603_text(item.get("grade")).upper()
    rec = _oracle04603_text(item.get("recommendation") or item.get("raw", {}).get("recommendation"))
    raw_rec = _oracle04603_text(item.get("raw", {}).get("raw", {}).get("recommendation"))
    combined = f"{side} {grade} {rec} {raw_rec}".lower()

    if "buy yes" in combined or side == "YES":
        return "BUY YES"
    if "buy no" in combined or side == "NO":
        return "BUY NO"
    if "pass" in combined or grade == "PASS":
        return "PASS"
    if "investigate" in combined or "relative value" in combined or "underpriced" in combined:
        return "WATCH"
    return "WATCH"


def _oracle04603_grade_confidence(grade, score):
    grade = _oracle04603_text(grade).upper()
    score = _oracle04603_num(score, 50)

    if grade == "A+":
        return 94
    if grade == "A":
        return 88
    if grade == "A-":
        return 82
    if grade == "B+":
        return 74
    if grade == "B":
        return 66
    if grade == "C":
        return 52
    if grade == "PASS":
        return max(35, min(58, score))
    return max(35, min(90, score))


def _oracle04603_edge_quality(edge, edge_pct=None):
    edge = abs(_oracle04603_num(edge, 0))
    ep = abs(_oracle04603_num(edge_pct, edge * 100))

    if ep >= 75:
        return 92
    if ep >= 50:
        return 86
    if ep >= 25:
        return 78
    if ep >= 10:
        return 66
    if ep >= 3:
        return 54
    return 38


def _oracle04603_build_adapted_opportunity(item):
    if not isinstance(item, dict):
        return item

    raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
    raw_raw = raw.get("raw") if isinstance(raw.get("raw"), dict) else {}

    ticker = item.get("ticker") or raw.get("ticker") or raw_raw.get("ticker")
    title = item.get("title") or raw.get("title") or raw_raw.get("title")

    overall_score = _oracle04603_num(item.get("overall_score"), 50)
    adaptive_score = _oracle04603_num(item.get("adaptive_score"), overall_score)
    base_conf = _oracle04603_num(item.get("confidence") or raw.get("confidence") or raw_raw.get("confidence"), 50)
    edge = _oracle04603_num(item.get("edge") or raw.get("edge") or raw_raw.get("edge"), 0)
    edge_pct = _oracle04603_num(raw_raw.get("edge_pct"), edge * 100)
    grade = item.get("grade", "PASS")
    risk = _oracle04603_text(item.get("risk", "UNKNOWN")).upper()
    reason = item.get("reason") or raw.get("reason") or raw_raw.get("reason") or ""
    recommendation = raw.get("recommendation") or raw_raw.get("recommendation") or item.get("recommendation") or ""
    kind = raw_raw.get("kind") or raw.get("kind") or ""

    direction = _oracle04603_direction_from_ranked(item)

    edge_quality = _oracle04603_edge_quality(edge, edge_pct)
    grade_conf = _oracle04603_grade_confidence(grade, adaptive_score)

    risk_penalty = 0
    if risk == "HIGH":
        risk_penalty = 18
    elif risk == "MEDIUM":
        risk_penalty = 8
    elif risk == "LOW":
        risk_penalty = 0

    # If ranking already says PASS, make final fusion more cautious.
    fusion_direction = direction
    if _oracle04603_text(grade).upper() == "PASS":
        fusion_direction = "PASS" if adaptive_score < 55 else "WATCH"

    adapted = dict(item)

    adapted["market_intelligence"] = {
        "recommendation": direction if adaptive_score >= 58 else "WATCH",
        "confidence": max(35, min(95, adaptive_score)),
        "reason": f"Market intelligence score {overall_score:.2f}, adaptive score {adaptive_score:.2f}.",
    }

    adapted["evidence"] = {
        "recommendation": "WATCH" if base_conf >= 70 else "PASS",
        "confidence": max(35, min(95, base_conf)),
        "reason": f"Evidence confidence from opportunity confidence: {base_conf:.2f}.",
    }

    adapted["historical_similarity"] = {
        "recommendation": "WATCH",
        "confidence": 50,
        "reason": "Historical similarity vote is neutral until real matched analog outcomes are attached.",
    }

    adapted["learning_engine"] = {
        "recommendation": "WATCH" if item.get("learning_multiplier", 1.0) >= 1 else "PASS",
        "confidence": max(35, min(80, adaptive_score)),
        "reason": item.get("learning_note", "Learning engine neutral adjustment."),
    }

    adapted["final_fusion"] = {
        "recommendation": fusion_direction,
        "confidence": max(35, min(95, grade_conf - risk_penalty)),
        "reason": f"Final fusion derived from grade={grade}, risk={risk}, adaptive_score={adaptive_score:.2f}.",
    }

    adapted["arbitrage"] = {
        "recommendation": recommendation or direction,
        "confidence": max(35, min(98, edge_quality)),
        "reason": reason or f"Arbitrage kind={kind}, edge_pct={edge_pct:.2f}.",
        "kind": kind,
        "edge_pct": edge_pct,
    }

    adapted["research"] = {
        "recommendation": "WATCH" if recommendation else "PASS",
        "confidence": max(35, min(80, (base_conf * 0.55) + (adaptive_score * 0.45))),
        "reason": recommendation or reason or "No research recommendation attached.",
    }

    adapted["ranking"] = {
        "recommendation": fusion_direction,
        "confidence": max(35, min(95, adaptive_score)),
        "reason": f"Opportunity Ranking score={overall_score:.2f}, adaptive_score={adaptive_score:.2f}, grade={grade}.",
    }

    adapted["historical_memory"] = {
        "recommendation": "WATCH",
        "confidence": 25,
        "reason": "Historical Memory placeholder active; no stored memory vote yet.",
    }

    adapted["ticker"] = ticker
    adapted["title"] = title

    return adapted


if "OracleConsensusEngine" in globals():
    _oracle04603_original_calculate_consensus = OracleConsensusEngine.calculate_consensus

    def _oracle04603_calculate_consensus(self, opportunity):
        adapted = _oracle04603_build_adapted_opportunity(opportunity)
        result = _oracle04603_original_calculate_consensus(self, adapted)

        if isinstance(result, dict):
            result["adapter"] = {
                "version": "ORACLE-046.0.3",
                "status": "applied",
                "source_shape": "ranked_opportunity",
            }

        return result

    OracleConsensusEngine.calculate_consensus = _oracle04603_calculate_consensus

# ============================================================
# END ORACLE-046.0.3
# ============================================================




# ============================================================
# ORACLE-046.0.4 Consensus Recommendation Calibration
# ============================================================

def _oracle04604_calibrated_direction_value(self, direction):
    """
    Calibrated vote power.

    Old issue:
    PASS returned 0.0, so PASS votes appeared in direction_counts
    but had no weighted power.

    New behavior:
    BUY YES = positive directional conviction
    BUY NO  = negative directional conviction
    WATCH   = neutral-but-actionable monitoring conviction
    PASS    = defensive rejection conviction
    """
    direction = str(direction or "").upper().strip()

    if direction == "BUY YES":
        return 1.0
    if direction == "BUY NO":
        return -1.0
    if direction == "WATCH":
        return 0.35
    if direction == "PASS":
        return 0.70

    return 0.20


def _oracle04604_recommendation_overlay(result):
    if not isinstance(result, dict):
        return result

    scores = result.get("weighted_direction_scores") or {}
    counts = result.get("direction_counts") or {}

    buy_yes = float(scores.get("BUY YES", 0) or 0)
    buy_no = float(scores.get("BUY NO", 0) or 0)
    watch = float(scores.get("WATCH", 0) or 0)
    passed = float(scores.get("PASS", 0) or 0)

    confidence = float(result.get("consensus_confidence", 0) or 0)
    weighted_agreement = float(result.get("weighted_agreement", 0) or 0)

    original = result.get("final_recommendation", "WATCH")

    # Defensive override: if PASS is strongest, do not allow fake strong WATCH.
    if passed > max(watch, buy_yes, buy_no):
        if confidence >= 60:
            result["final_recommendation"] = "PASS"
        else:
            result["final_recommendation"] = "WATCH"

    # Watch override: if WATCH is strongest but PASS is close, downgrade confidence.
    elif watch >= max(buy_yes, buy_no) and passed >= watch * 0.55:
        result["final_recommendation"] = "WATCH"
        result["consensus_strength"] = "CAUTIOUS WATCH"

    # Directional buy gates.
    elif buy_yes > max(watch, passed, buy_no):
        if confidence >= 72 and weighted_agreement >= 60:
            result["final_recommendation"] = "BUY YES"
        elif confidence >= 58:
            result["final_recommendation"] = "WATCH"
        else:
            result["final_recommendation"] = "PASS"

    elif buy_no > max(watch, passed, buy_yes):
        if confidence >= 72 and weighted_agreement >= 60:
            result["final_recommendation"] = "BUY NO"
        elif confidence >= 58:
            result["final_recommendation"] = "WATCH"
        else:
            result["final_recommendation"] = "PASS"

    result["calibration"] = {
        "version": "ORACLE-046.0.4",
        "status": "applied",
        "original_recommendation": original,
        "calibrated_recommendation": result.get("final_recommendation"),
        "pass_power": round(passed, 2),
        "watch_power": round(watch, 2),
        "buy_yes_power": round(buy_yes, 2),
        "buy_no_power": round(buy_no, 2),
        "direction_counts": counts,
    }

    return result


if "OracleConsensusEngine" in globals():
    OracleConsensusEngine._direction_value = _oracle04604_calibrated_direction_value

    if "_oracle04604_original_calculate_consensus" not in globals():
        _oracle04604_original_calculate_consensus = OracleConsensusEngine.calculate_consensus

        def _oracle04604_calculate_consensus(self, opportunity):
            result = _oracle04604_original_calculate_consensus(self, opportunity)
            return _oracle04604_recommendation_overlay(result)

        OracleConsensusEngine.calculate_consensus = _oracle04604_calculate_consensus

# ============================================================
# END ORACLE-046.0.4
# ============================================================




# ============================================================
# ORACLE-046.0.5 Consensus Terminal Formatter
# ============================================================

def _oracle04605_fmt_num(value, digits=2):
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return "0.00"


def _oracle04605_build_compact_card(result, opportunity=None):
    if not isinstance(result, dict):
        return "🧠 ORACLE CONSENSUS\nStatus: unavailable"

    opportunity = opportunity if isinstance(opportunity, dict) else {}

    ticker = (
        opportunity.get("ticker")
        or opportunity.get("market_ticker")
        or result.get("ticker")
        or "UNKNOWN"
    )

    title = (
        opportunity.get("title")
        or opportunity.get("market_title")
        or result.get("title")
        or "Untitled opportunity"
    )

    final = result.get("final_recommendation", "WATCH")
    conf = result.get("consensus_confidence", 0)
    strength = result.get("consensus_strength", "UNKNOWN")
    agreement = result.get("engine_agreement_pct", 0)
    weighted = result.get("weighted_agreement", 0)
    counts = result.get("direction_counts") or {}
    scores = result.get("weighted_direction_scores") or {}
    conflicts = result.get("conflicts") or []

    vote_lines = []
    for direction in ("BUY YES", "BUY NO", "WATCH", "PASS"):
        if direction in counts:
            vote_lines.append(
                f"{direction}: {counts.get(direction, 0)} engines | power {_oracle04605_fmt_num(scores.get(direction, 0))}"
            )

    if not vote_lines:
        vote_lines.append("No engine votes detected")

    conflict_text = ", ".join(conflicts) if conflicts else "None"

    calibration = result.get("calibration") or {}
    adapter = result.get("adapter") or {}

    reason_bits = []

    if adapter.get("status") == "applied":
        reason_bits.append("Signal adapter translated ranked opportunity fields into subsystem votes.")

    if calibration.get("status") == "applied":
        reason_bits.append(
            f"Calibrated recommendation: {calibration.get('calibrated_recommendation', final)}."
        )

    if final == "PASS":
        reason_bits.append("Consensus rejected execution because defensive/pass power dominated or confidence was insufficient.")
    elif final == "WATCH":
        reason_bits.append("Consensus sees enough signal to monitor, but not enough confirmed strength for execution.")
    elif final in ("BUY YES", "BUY NO"):
        reason_bits.append("Consensus reached directional execution-grade agreement.")

    if not reason_bits:
        reason_bits.append("Consensus generated from weighted subsystem votes.")

    return (
        "🧠 ORACLE CONSENSUS\n"
        f"Ticker: {ticker}\n"
        f"Market: {title}\n\n"
        f"Final: {final}\n"
        f"Strength: {strength}\n"
        f"Confidence: {_oracle04605_fmt_num(conf)}%\n"
        f"Engine Agreement: {_oracle04605_fmt_num(agreement)}%\n"
        f"Weighted Agreement: {_oracle04605_fmt_num(weighted)}%\n\n"
        "Votes / Power:\n"
        + "\n".join(f"- {line}" for line in vote_lines)
        + "\n\n"
        f"Conflicts: {conflict_text}\n\n"
        "Reason:\n"
        + "\n".join(f"- {line}" for line in reason_bits)
    )


def _oracle04605_build_terminal_card(result, opportunity=None):
    compact = _oracle04605_build_compact_card(result, opportunity)

    votes = result.get("votes") if isinstance(result, dict) else []
    vote_lines = []

    if isinstance(votes, list):
        for vote in votes:
            if not isinstance(vote, dict):
                continue
            vote_lines.append(
                f"- {vote.get('engine')}: {vote.get('direction')} "
                f"({vote.get('confidence')}% conf, weight {vote.get('weight')})"
            )

    if not vote_lines:
        vote_lines.append("- No detailed votes available")

    return (
        "\n================ ORACLE CONSENSUS TERMINAL ================\n"
        + compact
        + "\n\nDetailed Engine Votes:\n"
        + "\n".join(vote_lines)
        + "\n============================================================\n"
    )


if "OracleConsensusEngine" in globals():
    if "_oracle04605_original_calculate_consensus" not in globals():
        _oracle04605_original_calculate_consensus = OracleConsensusEngine.calculate_consensus

        def _oracle04605_calculate_consensus(self, opportunity):
            result = _oracle04605_original_calculate_consensus(self, opportunity)

            if isinstance(result, dict):
                result["compact_card"] = _oracle04605_build_compact_card(result, opportunity)
                result["terminal_card"] = _oracle04605_build_terminal_card(result, opportunity)
                result["formatter"] = {
                    "version": "ORACLE-046.0.5",
                    "status": "applied",
                    "formats": ["compact_card", "terminal_card"],
                }

            return result

        OracleConsensusEngine.calculate_consensus = _oracle04605_calculate_consensus

# ============================================================
# END ORACLE-046.0.5
# ============================================================


if __name__ == "__main__":
    sample = {
        "ticker": "TEST-MARKET",
        "title": "Sample Oracle consensus opportunity",
        "market_intelligence": {
            "recommendation": "BUY YES",
            "confidence": 78,
            "reason": "Market intelligence sees strong directional pressure.",
        },
        "evidence": {
            "recommendation": "BUY YES",
            "confidence": 82,
            "reason": "Evidence stack supports YES side.",
        },
        "historical_similarity": {
            "recommendation": "WATCH",
            "confidence": 61,
            "reason": "Similar setups were profitable but not clean enough.",
        },
        "learning_engine": {
            "recommendation": "BUY YES",
            "confidence": 74,
            "reason": "Learning engine favors this setup type.",
        },
        "final_fusion": {
            "recommendation": "BUY YES",
            "confidence": 84,
            "reason": "Fusion layer confirms directional opportunity.",
        },
        "arbitrage": {
            "recommendation": "Relative value: later market may be underpriced",
            "confidence": 76,
            "reason": "Arbitrage engine found non-false-positive relative value.",
        },
        "research": {
            "recommendation": "WATCH",
            "confidence": 63,
            "reason": "Research context is constructive but incomplete.",
        },
        "ranking": {
            "recommendation": "BUY YES",
            "confidence": 80,
            "reason": "Opportunity ranking places this near the top.",
        },
    }

    result = oracle_consensus_engine.calculate_consensus(sample)
    print(result["terminal_summary"])
    print({
        "status": result["status"],
        "final_recommendation": result["final_recommendation"],
        "consensus_confidence": result["consensus_confidence"],
        "consensus_strength": result["consensus_strength"],
        "engine_agreement_pct": result["engine_agreement_pct"],
        "weighted_agreement": result["weighted_agreement"],
        "conflicts": result["conflicts"],
    })
