"""
ORACLE-046 Consensus Engine Installer

Creates:
- oracle_consensus_engine.py

Safely patches:
- oracle_continuous_intelligence.py, if found

Purpose:
Every Oracle subsystem casts a weighted vote on each opportunity.
"""

from pathlib import Path
from datetime import datetime
import shutil
import re


ROOT = Path.cwd()

CONSENSUS_FILE = ROOT / "oracle_consensus_engine.py"
CONTINUOUS_FILE = ROOT / "oracle_continuous_intelligence.py"


CONSENSUS_CODE = r'''"""
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
'''


def backup(path: Path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(path.suffix + f".bak_oracle046_{stamp}")
        shutil.copy2(path, backup_path)
        return backup_path
    return None


def write_consensus_file():
    backup_path = backup(CONSENSUS_FILE)
    CONSENSUS_FILE.write_text(CONSENSUS_CODE, encoding="utf-8")
    return backup_path


def patch_continuous_intelligence():
    if not CONTINUOUS_FILE.exists():
        return "oracle_continuous_intelligence.py not found; skipped integration patch"

    text = CONTINUOUS_FILE.read_text(encoding="utf-8", errors="ignore")
    original = text

    if "oracle_consensus_engine" not in text:
        text = (
            "try:\n"
            "    from oracle_consensus_engine import oracle_consensus_engine\n"
            "except Exception:\n"
            "    oracle_consensus_engine = None\n\n"
            + text
        )

    # Conservative generic integration:
    # If file has a get_snapshot method returning a dict, inject consensus enrichment before return.
    if "consensus" not in text:
        pattern = r"(return\s+snapshot)"
        replacement = (
            "if oracle_consensus_engine is not None:\n"
            "            try:\n"
            "                opps = snapshot.get('opportunities') or snapshot.get('alerts') or []\n"
            "                if isinstance(opps, list):\n"
            "                    snapshot['consensus_opportunities'] = oracle_consensus_engine.analyze_many(opps)\n"
            "                    snapshot['consensus'] = {\n"
            "                        'status': 'ok',\n"
            "                        'count': len(snapshot['consensus_opportunities']),\n"
            "                        'top': snapshot['consensus_opportunities'][:5],\n"
            "                    }\n"
            "            except Exception as exc:\n"
            "                snapshot['consensus'] = {'status': 'error', 'error': str(exc)}\n"
            "        return snapshot"
        )

        text, count = re.subn(pattern, replacement, text, count=1)
    else:
        count = 0

    if text != original:
        backup_path = backup(CONTINUOUS_FILE)
        CONTINUOUS_FILE.write_text(text, encoding="utf-8")
        return f"patched oracle_continuous_intelligence.py backup={backup_path}"

    return "oracle_continuous_intelligence.py already appears patched; no changes made"


def main():
    print("===================================")
    print(" ORACLE-046 INSTALLER")
    print(" Consensus Engine")
    print("===================================")

    consensus_backup = write_consensus_file()
    if consensus_backup:
        print(f"Backup created: {consensus_backup.name}")

    print("[OK] Created oracle_consensus_engine.py")

    integration_result = patch_continuous_intelligence()
    print(f"[INFO] {integration_result}")

    print("")
    print("Tests:")
    print(" python oracle_consensus_engine.py")
    print(" python -c \"from oracle_consensus_engine import oracle_consensus_engine; print(oracle_consensus_engine.diagnostics())\"")
    print("")
    print("[DONE] ORACLE-046 Consensus Engine installed")


if __name__ == "__main__":
    main()