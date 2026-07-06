from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

ENGINE = PKG / "historical_case_comparison_engine.py"
TEST = ROOT / "test_oi_141_historical_case_comparison_engine.py"
INIT = PKG / "__init__.py"

ENGINE.write_text(r'''
"""
OI-141 Historical Case Comparison Engine
Read-only Oracle Intelligence module.

Purpose:
- Compare current Oracle intelligence cases against historical market memory.
- Identify similar historical cases by market, archive type, tier, memory signature,
  pattern strength, and visibility priority.
- Produce read-only comparison packets for downstream confidence evolution.
- Does not execute trades.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from typing import Dict, Any, List
import time


class HistoricalCaseComparisonEngine:
    module = "oi_141_historical_case_comparison_engine"

    def __init__(self):
        self.last_comparison_report = {}

    def compare_cases(self, current_case_report=None, market_memory_report=None, pattern_report=None):
        current_case_report = current_case_report or {}
        market_memory_report = market_memory_report or {}
        pattern_report = pattern_report or {}

        current_cases = self._cases(current_case_report)
        memory_profiles = [
            x for x in market_memory_report.get("market_memory_profiles", [])
            if isinstance(x, dict)
        ]
        patterns = [
            x for x in pattern_report.get("patterns", [])
            if isinstance(x, dict)
        ]

        comparisons = []
        for case in current_cases:
            case_comparisons = []

            for memory in memory_profiles:
                related_patterns = self._patterns_for_market(patterns, memory.get("market"))
                comparison = self._compare_case_to_memory(case, memory, related_patterns)
                case_comparisons.append(comparison)

            case_comparisons.sort(
                key=lambda x: (
                    x["similarity_score"],
                    x["memory_strength"],
                    x["market"],
                ),
                reverse=True,
            )

            for idx, item in enumerate(case_comparisons, start=1):
                item["comparison_rank"] = idx

            comparisons.append({
                "case_id": case["case_id"],
                "market": case["market"],
                "case_type": case["case_type"],
                "case_score": case["case_score"],
                "best_match_market": case_comparisons[0]["market"] if case_comparisons else None,
                "best_similarity_score": case_comparisons[0]["similarity_score"] if case_comparisons else 0.0,
                "comparison_count": len(case_comparisons),
                "matches": case_comparisons,
                "top_matches": case_comparisons[:5],
                "case_comparison_note": self._case_note(case, case_comparisons),
                "read_only": True,
                "execution_allowed": False,
            })

        comparisons.sort(
            key=lambda x: (
                x["best_similarity_score"],
                x["case_score"],
                x["case_id"],
            ),
            reverse=True,
        )

        for idx, item in enumerate(comparisons, start=1):
            item["case_rank"] = idx

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "execution_allowed": False,
            "input_modules": [
                "oi_140_oracle_market_memory_engine",
                "oi_139_historical_visibility_pattern_engine",
            ],
            "case_count": len(current_cases),
            "comparison_packet_count": len(comparisons),
            "comparison_packets": comparisons,
            "top_comparison_packets": comparisons[:10],
            "comparison_summary": self._summary(comparisons),
            "qseries_handoff": {
                "execution_owner": "Q Series",
                "oracle_permission": "read_only",
                "execution_allowed": False,
                "handoff_type": "historical_case_comparison_context_only",
            },
        }

        self.last_comparison_report = report
        return report

    def _cases(self, current_case_report):
        raw_cases = []

        if isinstance(current_case_report, list):
            raw_cases = [x for x in current_case_report if isinstance(x, dict)]
        elif isinstance(current_case_report, dict):
            for key in [
                "cases",
                "current_cases",
                "intelligence_cases",
                "digest_items",
                "handoff_items",
                "market_memory_profiles",
                "records",
                "items",
            ]:
                value = current_case_report.get(key)
                if isinstance(value, list):
                    raw_cases = [x for x in value if isinstance(x, dict)]
                    break

            if not raw_cases and current_case_report:
                raw_cases = [current_case_report]

        cases = []
        for idx, row in enumerate(raw_cases, start=1):
            market = str(row.get("market") or row.get("symbol") or row.get("ticker") or "UNKNOWN")
            case_type = str(
                row.get("case_type")
                or row.get("archive_type")
                or row.get("digest_tier")
                or row.get("handoff_tier")
                or row.get("memory_tier")
                or "oracle_case"
            )
            case_score = self._float(
                row.get("case_score")
                or row.get("digest_score")
                or row.get("handoff_score")
                or row.get("memory_strength")
                or row.get("catalog_priority")
                or row.get("score")
                or 50
            )
            case_id = str(
                row.get("case_id")
                or row.get("catalog_key")
                or row.get("archive_id")
                or row.get("id")
                or f"{market}:{case_type}:{idx}"
            )

            cases.append({
                "case_id": case_id,
                "market": market,
                "case_type": case_type,
                "case_score": round(case_score, 4),
                "source": row,
            })

        return cases

    def _compare_case_to_memory(self, case, memory, related_patterns):
        market_match = 1.0 if case["market"] == str(memory.get("market") or "UNKNOWN") else 0.0

        case_type = case["case_type"].lower()
        signature = memory.get("historical_signature", {}) or {}
        archive_signature = [
            str(x).lower()
            for x in signature.get("archive_type_signature", []) or []
        ]
        pattern_signature = [
            str(x).lower()
            for x in signature.get("pattern_type_signature", []) or []
        ]
        tier_signature = [
            str(x).lower()
            for x in signature.get("tier_signature", []) or []
        ]

        archive_match = 1.0 if case_type in archive_signature else 0.0
        tier_match = 1.0 if case_type in tier_signature else 0.0
        pattern_match = self._pattern_match(case, related_patterns)

        score_distance = abs(case["case_score"] - self._float(memory.get("memory_strength"), 0))
        score_similarity = max(0.0, 1.0 - (score_distance / 100.0))

        memory_strength = self._float(memory.get("memory_strength"), 0)
        avg_pattern_score = self._float(memory.get("avg_pattern_score"), 0)

        similarity = (
            market_match * 28
            + archive_match * 18
            + tier_match * 10
            + pattern_match * 16
            + score_similarity * 16
            + min(memory_strength, 100) * 0.08
            + min(avg_pattern_score, 100) * 0.04
        )

        similarity = max(0.0, min(100.0, similarity))

        return {
            "market": memory.get("market"),
            "similarity_score": round(similarity, 4),
            "similarity_tier": self._tier(similarity),
            "memory_strength": round(memory_strength, 4),
            "memory_tier": memory.get("memory_tier"),
            "avg_pattern_score": round(avg_pattern_score, 4),
            "market_match": bool(market_match),
            "archive_signature_match": bool(archive_match),
            "tier_signature_match": bool(tier_match),
            "pattern_match_score": round(pattern_match * 100, 4),
            "score_distance": round(score_distance, 4),
            "historical_signature": signature,
            "comparison_note": self._comparison_note(case, memory, similarity),
            "read_only": True,
            "execution_allowed": False,
        }

    def _pattern_match(self, case, patterns):
        if not patterns:
            return 0.0

        case_market = case["market"]
        case_type = case["case_type"].lower()

        hits = 0.0
        possible = 0.0

        for pattern in patterns:
            possible += 1.0
            key = str(pattern.get("pattern_key") or "").lower()
            ptype = str(pattern.get("pattern_type") or "").lower()
            markets = [str(x) for x in pattern.get("markets", []) or []]
            archive_types = [str(x).lower() for x in pattern.get("archive_types", []) or []]
            tiers = [str(x).lower() for x in pattern.get("catalog_tiers", []) or []]

            if case_market in markets:
                hits += 0.35
            if case_type == key:
                hits += 0.25
            if case_type in archive_types:
                hits += 0.25
            if case_type in tiers:
                hits += 0.15
            if ptype == "market_visibility" and key == case_market.lower():
                hits += 0.20

        if possible <= 0:
            return 0.0

        return max(0.0, min(1.0, hits / possible))

    def _tier(self, score):
        if score >= 85:
            return "near_match"
        if score >= 70:
            return "strong_match"
        if score >= 50:
            return "partial_match"
        if score >= 30:
            return "weak_match"
        return "no_clear_match"

    def _case_note(self, case, comparisons):
        if not comparisons:
            return (
                f"{case['case_id']} has no historical market memory comparison. "
                "Oracle remains read-only and provides no execution permission."
            )

        top = comparisons[0]
        return (
            f"{case['case_id']} best historical comparison is {top['market']} "
            f"with similarity score {top['similarity_score']} ({top['similarity_tier']}). "
            "This is read-only historical context for Q Series."
        )

    def _comparison_note(self, case, memory, similarity):
        return (
            f"Current case {case['case_id']} compared with {memory.get('market')} "
            f"market memory at similarity {round(similarity, 2)}. Oracle provides "
            "comparison context only; Q Series owns execution decisions."
        )

    def _patterns_for_market(self, patterns, market):
        market = str(market or "UNKNOWN")
        out = []

        for pattern in patterns:
            markets = [str(x) for x in pattern.get("markets", []) or []]
            key = str(pattern.get("pattern_key") or "")

            if market in markets or key == market:
                out.append(pattern)

        return out

    def _summary(self, comparisons):
        tier_counts = {}
        for packet in comparisons:
            best = packet.get("top_matches", [{}])[0] if packet.get("top_matches") else {}
            tier = best.get("similarity_tier", "no_clear_match")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        top = comparisons[0] if comparisons else None

        return {
            "comparison_packet_count": len(comparisons),
            "similarity_tier_counts": tier_counts,
            "top_case_id": top["case_id"] if top else None,
            "top_case_market": top["market"] if top else None,
            "top_best_match_market": top["best_match_market"] if top else None,
            "top_best_similarity_score": top["best_similarity_score"] if top else None,
            "execution_allowed": False,
            "read_only": True,
        }

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
            "has_comparison_report": bool(self.last_comparison_report),
            "comparison_packet_count": self.last_comparison_report.get("comparison_packet_count", 0),
            "execution_allowed": False,
            "read_only": True,
        }


historical_case_comparison_engine = HistoricalCaseComparisonEngine()
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.historical_case_comparison_engine import (
    historical_case_comparison_engine,
)


def test_oi_141_historical_case_comparison_engine():
    current_cases = {
        "cases": [
            {
                "case_id": "case-crypto-001",
                "market": "CRYPTO",
                "case_type": "digest_snapshot",
                "case_score": 91,
            },
            {
                "case_id": "case-nasdaq-001",
                "market": "NASDAQ",
                "case_type": "strategic_briefing",
                "case_score": 73,
            },
        ]
    }

    memory = {
        "market_memory_profiles": [
            {
                "market": "CRYPTO",
                "memory_strength": 92,
                "memory_tier": "institutional_memory",
                "avg_pattern_score": 89.7,
                "historical_signature": {
                    "market": "CRYPTO",
                    "archive_type_signature": ["digest_snapshot"],
                    "pattern_type_signature": ["market_visibility"],
                    "tier_signature": ["institutional_priority"],
                    "execution_allowed": False,
                    "read_only": True,
                },
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "market": "NASDAQ",
                "memory_strength": 71,
                "memory_tier": "strong_memory",
                "avg_pattern_score": 55.2,
                "historical_signature": {
                    "market": "NASDAQ",
                    "archive_type_signature": ["strategic_briefing"],
                    "pattern_type_signature": ["market_visibility"],
                    "tier_signature": ["high_value"],
                    "execution_allowed": False,
                    "read_only": True,
                },
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
                "archive_types": ["digest_snapshot"],
                "catalog_tiers": ["institutional_priority"],
                "read_only": True,
                "execution_allowed": False,
            },
            {
                "pattern_key": "NASDAQ",
                "pattern_type": "market_visibility",
                "pattern_score": 55.2,
                "markets": ["NASDAQ"],
                "archive_types": ["strategic_briefing"],
                "catalog_tiers": ["high_value"],
                "read_only": True,
                "execution_allowed": False,
            },
        ]
    }

    report = historical_case_comparison_engine.compare_cases(current_cases, memory, patterns)

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["execution_allowed"] is False
    assert report["qseries_handoff"]["execution_owner"] == "Q Series"
    assert report["qseries_handoff"]["execution_allowed"] is False
    assert report["case_count"] == 2
    assert report["comparison_packet_count"] == 2
    assert report["comparison_packets"][0]["case_rank"] == 1
    assert report["comparison_packets"][0]["top_matches"][0]["execution_allowed"] is False
    assert report["comparison_packets"][0]["top_matches"][0]["read_only"] is True
    assert report["comparison_summary"]["execution_allowed"] is False
    assert report["comparison_summary"]["read_only"] is True
    assert report["comparison_packets"][0]["best_similarity_score"] > 50

    diag = historical_case_comparison_engine.diagnostics()
    assert diag["status"] == "ok"
    assert diag["read_only"] is True
    assert diag["execution_allowed"] is False
    assert diag["comparison_packet_count"] == report["comparison_packet_count"]

    print("[PASS] OI-141 Historical Case Comparison Engine")
    print({
        "case_count": report["case_count"],
        "comparison_packet_count": report["comparison_packet_count"],
        "summary": report["comparison_summary"],
        "top": report["comparison_packets"][0],
    })


if __name__ == "__main__":
    test_oi_141_historical_case_comparison_engine()
''', encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

line = "from .historical_case_comparison_engine import historical_case_comparison_engine\n"
if line not in init_text:
    INIT.write_text(init_text.rstrip() + "\n" + line, encoding="utf-8")

print("========================================")
print(" OI-141 INSTALLER")
print(" Historical Case Comparison Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-141 installed")
print()
print("Run:")
print("py test_oi_141_historical_case_comparison_engine.py")