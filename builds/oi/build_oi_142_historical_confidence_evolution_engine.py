from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "historical_confidence_evolution_engine.py"
TEST = ROOT / "test_oi_142_historical_confidence_evolution_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-142 Historical Confidence Evolution Engine
Read-only Oracle Intelligence module.

Purpose:
- Analyze how Oracle confidence evolves across historical case comparisons.
- Convert historical similarity, memory strength, pattern strength, and current case scores
  into confidence evolution packets.
- Identify improving, stable, weakening, and uncertain confidence paths.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class HistoricalConfidenceEvolutionEngine:
    module = "oi_142_historical_confidence_evolution_engine"

    def __init__(self):
        self.last_evolution_report = {}

    def build_confidence_evolution(self, comparison_report=None, memory_report=None, pattern_report=None):
        comparison_report = comparison_report or {}
        memory_report = memory_report or {}
        pattern_report = pattern_report or {}

        packets = [
            x for x in comparison_report.get("comparison_packets", [])
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

        evolution_packets = []
        for packet in packets:
            market = str(packet.get("market") or "UNKNOWN")
            memory = memory_index.get(market, {})
            market_patterns = pattern_index.get(market, [])

            evolution = self._evolution_packet(packet, memory, market_patterns)
            evolution_packets.append(evolution)

        evolution_packets.sort(
            key=lambda x: (
                x["evolved_confidence"],
                x["confidence_delta"],
                x["case_id"],
            ),
            reverse=True,
        )

        for idx, packet in enumerate(evolution_packets, start=1):
            packet["evolution_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_141_historical_case_comparison_engine",
                "oi_140_oracle_market_memory_engine",
                "oi_139_historical_visibility_pattern_engine",
            ],
            "evolution_count": len(evolution_packets),
            "confidence_evolution_packets": evolution_packets,
            "top_evolution_packets": evolution_packets[:10],
            "evolution_summary": self._summary(evolution_packets),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "historical_confidence_evolution_context_only",
            },
        }

        self.last_evolution_report = report
        return report

    def _evolution_packet(self, packet, memory, patterns):
        case_id = str(packet.get("case_id") or "UNKNOWN_CASE")
        market = str(packet.get("market") or "UNKNOWN")
        case_score = self._float(packet.get("case_score"), 50)
        similarity = self._float(packet.get("best_similarity_score"), 0)
        memory_strength = self._float(memory.get("memory_strength"), 0)
        avg_pattern_score = self._avg(patterns, "pattern_score")

        baseline_confidence = self._baseline_confidence(case_score, similarity)
        historical_support = self._historical_support(similarity, memory_strength, avg_pattern_score)
        evolved_confidence = self._evolved_confidence(baseline_confidence, historical_support)
        confidence_delta = evolved_confidence - baseline_confidence

        trajectory = self._trajectory(confidence_delta, evolved_confidence, similarity)
        tier = self._tier(evolved_confidence)

        top_match = {}
        if packet.get("top_matches"):
            top_match = packet.get("top_matches", [{}])[0] or {}

        return {
            "case_id": case_id,
            "market": market,
            "case_type": packet.get("case_type"),
            "baseline_confidence": round(baseline_confidence, 4),
            "historical_support": round(historical_support, 4),
            "evolved_confidence": round(evolved_confidence, 4),
            "confidence_delta": round(confidence_delta, 4),
            "confidence_tier": tier,
            "confidence_trajectory": trajectory,
            "case_score": round(case_score, 4),
            "best_similarity_score": round(similarity, 4),
            "best_match_market": packet.get("best_match_market"),
            "best_match_tier": top_match.get("similarity_tier"),
            "memory_strength": round(memory_strength, 4),
            "memory_tier": memory.get("memory_tier"),
            "avg_pattern_score": round(avg_pattern_score, 4),
            "pattern_count": len(patterns),
            "evolution_note": self._note(
                case_id,
                market,
                evolved_confidence,
                confidence_delta,
                trajectory,
            ),
            "read_only": True,
            "execution_allowed": False,
        }

    def _baseline_confidence(self, case_score, similarity):
        score = case_score * 0.70 + similarity * 0.30
        return max(0.0, min(100.0, score))

    def _historical_support(self, similarity, memory_strength, avg_pattern_score):
        score = (
            similarity * 0.42
            + memory_strength * 0.36
            + avg_pattern_score * 0.22
        )
        return max(0.0, min(100.0, score))

    def _evolved_confidence(self, baseline, historical_support):
        if historical_support >= 80:
            lift = min((historical_support - baseline) * 0.35, 12)
        elif historical_support >= 60:
            lift = min((historical_support - baseline) * 0.18, 6)
        elif historical_support < 35:
            lift = -min((baseline - historical_support) * 0.24, 14)
        else:
            lift = -min((baseline - historical_support) * 0.12, 8)

        return max(0.0, min(100.0, baseline + lift))

    def _trajectory(self, delta, evolved_confidence, similarity):
        if evolved_confidence >= 85 and delta >= 4:
            return "strengthening_high_confidence"
        if delta >= 5:
            return "strengthening"
        if delta <= -8:
            return "weakening"
        if similarity < 35:
            return "historically_uncertain"
        return "stable"

    def _tier(self, score):
        if score >= 85:
            return "institutional_confidence"
        if score >= 70:
            return "strong_confidence"
        if score >= 50:
            return "moderate_confidence"
        if score >= 30:
            return "low_confidence"
        return "insufficient_confidence"

    def _note(self, case_id, market, evolved_confidence, delta, trajectory):
        direction = "increased" if delta > 0 else "decreased" if delta < 0 else "remained stable"
        return (
            f"{case_id} for {market} evolved confidence {direction} to "
            f"{round(evolved_confidence, 2)} with trajectory {trajectory}. "
            "This is read-only historical confidence context for Q Series."
        )

    def _summary(self, packets):
        tier_counts = {}
        trajectory_counts = {}

        for packet in packets:
            tier = packet["confidence_tier"]
            trajectory = packet["confidence_trajectory"]
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            trajectory_counts[trajectory] = trajectory_counts.get(trajectory, 0) + 1

        top = packets[0] if packets else None

        return {
            "evolution_count": len(packets),
            "confidence_tier_counts": tier_counts,
            "trajectory_counts": trajectory_counts,
            "top_case_id": top["case_id"] if top else None,
            "top_market": top["market"] if top else None,
            "top_confidence_tier": top["confidence_tier"] if top else None,
            "top_evolved_confidence": top["evolved_confidence"] if top else None,
            "strengthening_count": (
                trajectory_counts.get("strengthening", 0)
                + trajectory_counts.get("strengthening_high_confidence", 0)
            ),
            "execution_allowed": False,
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
            return default

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
            "has_evolution_report": bool(self.last_evolution_report),
            "evolution_count": self.last_evolution_report.get("evolution_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


historical_confidence_evolution_engine = HistoricalConfidenceEvolutionEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.historical_confidence_evolution_engine import (
    historical_confidence_evolution_engine,
)


def test_oi_142_historical_confidence_evolution_engine():
    comparisons = {
        "comparison_packets": [
            {
                "case_id": "case-crypto-001",
                "market": "CRYPTO",
                "case_type": "digest_snapshot",
                "case_score": 91,
                "best_match_market": "CRYPTO",
                "best_similarity_score": 85.588,
                "top_matches": [
                    {
                        "market": "CRYPTO",
                        "similarity_score": 85.588,
                        "similarity_tier": "near_match",
                        "read_only": True,
                        "execution_allowed": False,
                    }
                ],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "case_id": "case-nasdaq-001",
                "market": "NASDAQ",
                "case_type": "strategic_briefing",
                "case_score": 73,
                "best_match_market": "NASDAQ",
                "best_similarity_score": 72.114,
                "top_matches": [
                    {
                        "market": "NASDAQ",
                        "similarity_score": 72.114,
                        "similarity_tier": "strong_match",
                        "read_only": True,
                        "execution_allowed": False,
                    }
                ],
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
                "pattern_key": "NASDAQ",
                "pattern_type": "market_visibility",
                "pattern_score": 55.2,
                "markets": ["NASDAQ"],
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = historical_confidence_evolution_engine.build_confidence_evolution(
        comparisons,
        memory,
        patterns,
    )

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["evolution_count"] == 2
    assert report["confidence_evolution_packets"][0]["evolution_rank"] == 1
    assert report["confidence_evolution_packets"][0]["market"] == "CRYPTO"
    assert report["confidence_evolution_packets"][0]["evolved_confidence"] >= 80
    assert report["confidence_evolution_packets"][0]["execution_allowed"] is False
    assert report["confidence_evolution_packets"][0]["read_only"] is True
    assert report["evolution_summary"]["execution_allowed"] is False
    assert report["evolution_summary"]["read_only"] is True

    diag = historical_confidence_evolution_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["evolution_count"] == report["evolution_count"]

    print("[PASS] OI-142 Historical Confidence Evolution Engine")
    print({
        "evolution_count": report["evolution_count"],
        "summary": report["evolution_summary"],
        "top": report["confidence_evolution_packets"][0],
    })


if __name__ == "__main__":
    test_oi_142_historical_confidence_evolution_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .historical_confidence_evolution_engine import historical_confidence_evolution_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-142 INSTALLER")
print(" Historical Confidence Evolution Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-142 installed")
print()
print("Run:")
print("py test_oi_142_historical_confidence_evolution_engine.py")