from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "executive_historical_trend_engine.py"
TEST = ROOT / "test_oi_143_executive_historical_trend_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-143 Executive Historical Trend Engine
Read-only Oracle Intelligence module.

Purpose:
- Convert historical confidence evolution into executive trend intelligence.
- Track market-level historical trend posture, confidence direction, memory support,
  and executive-grade trend summaries.
- Produce read-only trend cards for downstream timeline intelligence.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class ExecutiveHistoricalTrendEngine:
    module = "oi_143_executive_historical_trend_engine"

    def __init__(self):
        self.last_trend_report = {}

    def build_historical_trends(self, confidence_evolution_report=None, memory_report=None, pattern_report=None):
        confidence_evolution_report = confidence_evolution_report or {}
        memory_report = memory_report or {}
        pattern_report = pattern_report or {}

        evolution_packets = [
            x for x in confidence_evolution_report.get("confidence_evolution_packets", [])
            if isinstance(x, dict)
        ]
        memory_profiles = [
            x for x in memory_report.get("market_memory_profiles", [])
            if isinstance(x, dict)
        ]
        patterns = [
            x for x in pattern_report.get("patterns", [])
            if isinstance(x, dict)
        ]

        memory_index = self._index(memory_profiles, "market")
        pattern_index = self._patterns_by_market(patterns)

        trend_cards = []
        for packet in evolution_packets:
            market = str(packet.get("market") or "UNKNOWN")
            memory = memory_index.get(market, {})
            market_patterns = pattern_index.get(market, [])
            trend_cards.append(self._trend_card(packet, memory, market_patterns))

        trend_cards.sort(
            key=lambda x: (
                x["trend_score"],
                x["evolved_confidence"],
                x["market"],
            ),
            reverse=True,
        )

        for idx, card in enumerate(trend_cards, start=1):
            card["trend_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_142_historical_confidence_evolution_engine",
                "oi_140_oracle_market_memory_engine",
                "oi_139_historical_visibility_pattern_engine",
            ],
            "trend_count": len(trend_cards),
            "historical_trend_cards": trend_cards,
            "top_historical_trends": trend_cards[:10],
            "trend_summary": self._summary(trend_cards),
            "executive_brief": self._executive_brief(trend_cards),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "executive_historical_trend_context_only",
            },
        }

        self.last_trend_report = report
        return report

    def _trend_card(self, packet, memory, patterns):
        market = str(packet.get("market") or "UNKNOWN")
        evolved_confidence = self._float(packet.get("evolved_confidence"), 0)
        confidence_delta = self._float(packet.get("confidence_delta"), 0)
        historical_support = self._float(packet.get("historical_support"), 0)
        memory_strength = self._float(memory.get("memory_strength"), packet.get("memory_strength") or 0)
        avg_pattern_score = self._avg(patterns, "pattern_score", packet.get("avg_pattern_score") or 0)

        trend_score = self._trend_score(
            evolved_confidence=evolved_confidence,
            confidence_delta=confidence_delta,
            historical_support=historical_support,
            memory_strength=memory_strength,
            avg_pattern_score=avg_pattern_score,
            pattern_count=len(patterns),
        )

        trend_direction = self._direction(confidence_delta, packet.get("confidence_trajectory"))
        trend_tier = self._tier(trend_score)
        executive_posture = self._posture(trend_score, trend_direction, evolved_confidence)

        return {
            "market": market,
            "case_id": packet.get("case_id"),
            "case_type": packet.get("case_type"),
            "trend_score": round(trend_score, 4),
            "trend_tier": trend_tier,
            "trend_direction": trend_direction,
            "executive_trend_posture": executive_posture,
            "evolved_confidence": round(evolved_confidence, 4),
            "confidence_delta": round(confidence_delta, 4),
            "confidence_tier": packet.get("confidence_tier"),
            "confidence_trajectory": packet.get("confidence_trajectory"),
            "historical_support": round(historical_support, 4),
            "memory_strength": round(memory_strength, 4),
            "memory_tier": memory.get("memory_tier") or packet.get("memory_tier"),
            "avg_pattern_score": round(avg_pattern_score, 4),
            "pattern_count": len(patterns),
            "best_match_market": packet.get("best_match_market"),
            "best_match_tier": packet.get("best_match_tier"),
            "trend_note": self._note(market, trend_score, trend_direction, executive_posture),
            "executive_takeaway": self._takeaway(market, trend_tier, trend_direction, evolved_confidence),
            "read_only": True,
            "execution_allowed": False,
        }

    def _trend_score(
        self,
        evolved_confidence,
        confidence_delta,
        historical_support,
        memory_strength,
        avg_pattern_score,
        pattern_count,
    ):
        direction_component = 0.0
        if confidence_delta > 0:
            direction_component = min(confidence_delta * 2.5, 12)
        elif confidence_delta < 0:
            direction_component = max(confidence_delta * 1.5, -10)

        pattern_component = min(pattern_count * 3, 12)

        score = (
            evolved_confidence * 0.34
            + historical_support * 0.24
            + memory_strength * 0.18
            + avg_pattern_score * 0.14
            + pattern_component
            + direction_component
        )

        return max(0.0, min(100.0, score))

    def _direction(self, delta, trajectory):
        trajectory = str(trajectory or "")
        delta = self._float(delta, 0)

        if "strengthening" in trajectory or delta >= 5:
            return "improving"
        if "weakening" in trajectory or delta <= -8:
            return "deteriorating"
        if "uncertain" in trajectory:
            return "uncertain"
        return "stable"

    def _tier(self, score):
        if score >= 85:
            return "dominant_historical_trend"
        if score >= 70:
            return "strong_historical_trend"
        if score >= 50:
            return "developing_historical_trend"
        if score >= 30:
            return "weak_historical_trend"
        return "insufficient_historical_trend"

    def _posture(self, score, direction, confidence):
        if score >= 85 and direction in {"improving", "stable"}:
            return "executive_priority_watch"
        if score >= 70:
            return "executive_monitor"
        if direction == "deteriorating":
            return "executive_caution"
        if confidence < 50:
            return "limited_historical_signal"
        return "standard_historical_review"

    def _note(self, market, score, direction, posture):
        return (
            f"{market} historical trend is {direction} with score {round(score, 2)} "
            f"and executive posture {posture}. Oracle provides read-only historical "
            "trend context only; Q Series owns execution decisions."
        )

    def _takeaway(self, market, tier, direction, confidence):
        return (
            f"{market}: {tier}, direction={direction}, evolved confidence="
            f"{round(confidence, 2)}. Use as executive historical context only."
        )

    def _summary(self, cards):
        tier_counts = {}
        direction_counts = {}
        posture_counts = {}

        for card in cards:
            tier = card["trend_tier"]
            direction = card["trend_direction"]
            posture = card["executive_trend_posture"]

            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
            posture_counts[posture] = posture_counts.get(posture, 0) + 1

        top = cards[0] if cards else None

        return {
            "trend_count": len(cards),
            "trend_tier_counts": tier_counts,
            "trend_direction_counts": direction_counts,
            "executive_posture_counts": posture_counts,
            "top_market": top["market"] if top else None,
            "top_trend_tier": top["trend_tier"] if top else None,
            "top_trend_score": top["trend_score"] if top else None,
            "priority_watch_count": posture_counts.get("executive_priority_watch", 0),
            "execution_allowed": False,
            "read_only": True,
        }

    def _executive_brief(self, cards):
        top = cards[0] if cards else None
        if not top:
            headline = "No executive historical trends available."
        else:
            headline = (
                f"Top historical trend is {top['market']} with posture "
                f"{top['executive_trend_posture']} and trend tier {top['trend_tier']}."
            )

        return {
            "headline": headline,
            "top_market": top["market"] if top else None,
            "top_direction": top["trend_direction"] if top else None,
            "top_posture": top["executive_trend_posture"] if top else None,
            "trend_count": len(cards),
            "execution_allowed": False,
            "execution_owner": "Q Series",
            "read_only": True,
        }

    def _patterns_by_market(self, patterns):
        out = {}
        for pattern in patterns:
            markets = pattern.get("markets", []) or []
            for market in markets:
                market = str(market)
                out.setdefault(market, []).append(pattern)

            key = str(pattern.get("pattern_key") or "")
            if pattern.get("pattern_type") == "market_visibility" and key:
                out.setdefault(key, []).append(pattern)

        return out

    def _index(self, rows, key):
        out = {}
        for row in rows:
            if isinstance(row, dict):
                value = str(row.get(key) or "").strip()
                if value:
                    out[value] = row
        return out

    def _avg(self, rows, field, default=0.0):
        values = []
        for row in rows:
            value = row.get(field)
            if value is None:
                continue
            values.append(self._float(value, default))

        if not values:
            return self._float(default, 0.0)

        return sum(values) / len(values)

    def _float(self, value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except Exception:
            return default

    def diagnostics(self):
        return {
            "module": self.module,
            "status": "ok",
            "has_trend_report": bool(self.last_trend_report),
            "trend_count": self.last_trend_report.get("trend_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


executive_historical_trend_engine = ExecutiveHistoricalTrendEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.executive_historical_trend_engine import (
    executive_historical_trend_engine,
)


def test_oi_143_executive_historical_trend_engine():
    evolution = {
        "confidence_evolution_packets": [
            {
                "case_id": "case-crypto-001",
                "market": "CRYPTO",
                "case_type": "digest_snapshot",
                "baseline_confidence": 89.3764,
                "historical_support": 88.801,
                "evolved_confidence": 89.175,
                "confidence_delta": -0.2014,
                "confidence_tier": "institutional_confidence",
                "confidence_trajectory": "stable",
                "best_match_market": "CRYPTO",
                "best_match_tier": "near_match",
                "memory_strength": 92,
                "memory_tier": "institutional_memory",
                "avg_pattern_score": 89.7,
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "case_id": "case-nasdaq-001",
                "market": "NASDAQ",
                "case_type": "strategic_briefing",
                "baseline_confidence": 72.7342,
                "historical_support": 68.744,
                "evolved_confidence": 72.015,
                "confidence_delta": -0.7192,
                "confidence_tier": "strong_confidence",
                "confidence_trajectory": "stable",
                "best_match_market": "NASDAQ",
                "best_match_tier": "strong_match",
                "memory_strength": 71,
                "memory_tier": "strong_memory",
                "avg_pattern_score": 55.2,
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    memory = {
        "market_memory_profiles": [
            {
                "market": "CRYPTO",
                "memory_strength": 92,
                "memory_tier": "institutional_memory",
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "memory_strength": 71,
                "memory_tier": "strong_memory",
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    patterns = {
        "patterns": [
            {
                "pattern_key": "CRYPTO",
                "pattern_type": "market_visibility",
                "pattern_score": 89.7,
                "markets": ["CRYPTO"],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "pattern_key": "CRYPTO",
                "pattern_type": "archive_time_visibility",
                "pattern_score": 89.72,
                "markets": ["CRYPTO"],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "pattern_key": "NASDAQ",
                "pattern_type": "market_visibility",
                "pattern_score": 55.2,
                "markets": ["NASDAQ"],
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = executive_historical_trend_engine.build_historical_trends(
        evolution,
        memory,
        patterns,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["trend_count"] == 2
    assert report["historical_trend_cards"][0]["trend_rank"] == 1
    assert report["historical_trend_cards"][0]["market"] == "CRYPTO"
    assert report["historical_trend_cards"][0]["execution_allowed"] is False
    assert report["historical_trend_cards"][0]["read_only"] is True
    assert report["trend_summary"]["execution_allowed"] is False
    assert report["trend_summary"]["read_only"] is True
    assert report["executive_brief"]["execution_allowed"] is False
    assert report["executive_brief"]["execution_owner"] == "Q Series"

    diag = executive_historical_trend_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["trend_count"] == report["trend_count"]

    print("[PASS] OI-143 Executive Historical Trend Engine")
    print({
        "trend_count": report["trend_count"],
        "summary": report["trend_summary"],
        "brief": report["executive_brief"],
        "top": report["historical_trend_cards"][0],
    })


if __name__ == "__main__":
    test_oi_143_executive_historical_trend_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .executive_historical_trend_engine import executive_historical_trend_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-143 INSTALLER")
print(" Executive Historical Trend Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-143 installed")
print()
print("Run:")
print("py test_oi_143_executive_historical_trend_engine.py")