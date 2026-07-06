from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "information_edge_engine.py"
TEST = ROOT / "test_oi_081_information_edge_engine.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-081 Information Edge Engine

Purpose:
- Detect whether Oracle appears to have an information advantage over market pricing.
- Score freshness, market reaction lag, volume confirmation, source quality,
  cross-market confirmation, and price inefficiency.
- Produce an Information Edge Score for downstream Oracle/Q Series research.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import math


class InformationEdgeEngine:
    module_name = "oi_081_information_edge_engine"

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "purpose": "information_edge_detection",
        }

    def score_information_edge(
        self,
        market: Dict[str, Any],
        information: Optional[Dict[str, Any]] = None,
        research_packet: Optional[Dict[str, Any]] = None,
        related_markets: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        information = information or {}
        research_packet = research_packet or {}
        related_markets = related_markets or []

        dimensions = {
            "freshness": self._freshness_score(information),
            "source_reliability": self._source_reliability_score(information),
            "market_reaction_lag": self._market_reaction_lag_score(market, information),
            "price_inefficiency": self._price_inefficiency_score(market, research_packet),
            "volume_confirmation": self._volume_confirmation_score(market),
            "cross_market_confirmation": self._cross_market_confirmation_score(market, related_markets),
            "research_quality": self._research_quality_score(research_packet),
            "information_completeness": self._information_completeness_score(information, market, research_packet),
        }

        weights = {
            "freshness": 0.16,
            "source_reliability": 0.13,
            "market_reaction_lag": 0.17,
            "price_inefficiency": 0.18,
            "volume_confirmation": 0.10,
            "cross_market_confirmation": 0.12,
            "research_quality": 0.10,
            "information_completeness": 0.04,
        }

        score = sum(dimensions[k] * weights[k] for k in dimensions)
        edge_score = round(max(0.0, min(100.0, score)), 2)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "ticker": market.get("ticker") or market.get("market_ticker"),
            "information_edge_score": edge_score,
            "edge_grade": self._grade(edge_score),
            "edge_level": self._level(edge_score),
            "estimated_market_catchup_minutes": self._catchup_minutes(edge_score, dimensions),
            "dimensions": {k: round(v, 2) for k, v in dimensions.items()},
            "reason_codes": self._reason_codes(dimensions, edge_score),
            "market": market,
            "information": information,
            "execution_enabled": False,
            "execution_owner": "Q Series",
        }

    def score_batch(
        self,
        markets: List[Dict[str, Any]],
        information_by_ticker: Optional[Dict[str, Dict[str, Any]]] = None,
        packets_by_ticker: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        information_by_ticker = information_by_ticker or {}
        packets_by_ticker = packets_by_ticker or {}
        results = []

        for market in markets or []:
            ticker = market.get("ticker") or market.get("market_ticker")
            results.append(self.score_information_edge(
                market=market,
                information=information_by_ticker.get(ticker, {}),
                research_packet=packets_by_ticker.get(ticker, {}),
            ))

        results.sort(key=lambda r: r["information_edge_score"], reverse=True)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "markets_scored": len(results),
            "top_edges": results,
        }

    def _freshness_score(self, information: Dict[str, Any]) -> float:
        age = self._num(information.get("age_seconds"))

        if age is None:
            timestamp = information.get("timestamp") or information.get("published_at")
            dt = self._parse_time(timestamp)
            if dt:
                age = max((datetime.now(timezone.utc) - dt).total_seconds(), 0.0)

        if age is None:
            return 45.0
        if age <= 30:
            return 100.0
        if age <= 120:
            return 90.0
        if age <= 300:
            return 75.0
        if age <= 900:
            return 55.0
        if age <= 3600:
            return 35.0
        return 15.0

    def _source_reliability_score(self, information: Dict[str, Any]) -> float:
        reliability = self._num(information.get("source_reliability") or information.get("reliability"))
        if reliability is not None:
            if reliability <= 1:
                reliability *= 100.0
            return max(0.0, min(100.0, reliability))

        tier = str(information.get("source_tier") or "").lower()
        if tier in {"official", "primary", "exchange", "government"}:
            return 95.0
        if tier in {"trusted", "verified", "major"}:
            return 82.0
        if tier in {"social", "rumor", "unverified"}:
            return 45.0
        return 60.0

    def _market_reaction_lag_score(self, market: Dict[str, Any], information: Dict[str, Any]) -> float:
        expected = self._num(information.get("expected_price_move_pct") or information.get("expected_move_pct"))
        actual = self._num(market.get("price_delta_pct") or market.get("change_pct") or market.get("move_pct"))

        if expected is None:
            return 50.0
        if actual is None:
            actual = 0.0

        lag = max(abs(expected) - abs(actual), 0.0)
        return max(0.0, min(100.0, lag * 12.0))

    def _price_inefficiency_score(self, market: Dict[str, Any], packet: Dict[str, Any]) -> float:
        price = self._num(market.get("price") or market.get("yes_price") or market.get("implied_probability"))
        summary = packet.get("summary", {}) or {}
        signals = packet.get("signals", {}) or {}
        probability = self._num(summary.get("expected_probability") or signals.get("expected_probability"))

        if probability is not None and probability <= 1:
            probability *= 100.0

        if price is None or probability is None:
            return 45.0

        gap = abs(probability - price)
        return max(0.0, min(100.0, gap * 8.0))

    def _volume_confirmation_score(self, market: Dict[str, Any]) -> float:
        volume_delta = self._num(market.get("volume_delta_pct"))
        volume = self._num(market.get("volume"))
        previous = self._num(market.get("previous_volume") or market.get("volume_5m_ago"))

        if volume_delta is None and volume is not None and previous not in {None, 0}:
            volume_delta = ((volume - previous) / max(previous, 1.0)) * 100.0

        if volume_delta is None:
            return 45.0
        if volume_delta <= 0:
            return 25.0
        return max(0.0, min(100.0, volume_delta / 2.0))

    def _cross_market_confirmation_score(self, market: Dict[str, Any], related: List[Dict[str, Any]]) -> float:
        if not related:
            value = self._num(market.get("cross_market_confirmation") or market.get("correlation_signal"))
            if value is None:
                return 45.0
            return max(0.0, min(100.0, abs(value) * 100.0 if abs(value) <= 1 else abs(value)))

        confirmations = 0
        total = 0
        direction = self._num(market.get("price_delta_pct") or market.get("change_pct") or 0.0)

        for item in related:
            delta = self._num(item.get("price_delta_pct") or item.get("change_pct"))
            if delta is None:
                continue
            total += 1
            if direction == 0 or (delta >= 0 and direction >= 0) or (delta <= 0 and direction <= 0):
                confirmations += 1

        if total == 0:
            return 45.0
        return confirmations / total * 100.0

    def _research_quality_score(self, packet: Dict[str, Any]) -> float:
        quality = self._num(packet.get("research_quality_score") or packet.get("summary", {}).get("research_quality_score"))
        if quality is not None:
            return max(0.0, min(100.0, quality))

        grade = str(packet.get("grade") or packet.get("signals", {}).get("final_research_grade") or "").upper()
        return {
            "A+": 97.0,
            "A": 92.0,
            "A-": 87.0,
            "B+": 82.0,
            "B": 75.0,
            "C": 65.0,
            "WATCH": 50.0,
        }.get(grade, 60.0)

    def _information_completeness_score(self, information: Dict[str, Any], market: Dict[str, Any], packet: Dict[str, Any]) -> float:
        fields = [
            information.get("headline") or information.get("summary"),
            information.get("source") or information.get("source_tier"),
            information.get("timestamp") or information.get("age_seconds"),
            information.get("expected_move_pct") or information.get("expected_price_move_pct"),
            market.get("price") or market.get("yes_price") or market.get("implied_probability"),
            market.get("volume"),
            market.get("liquidity") or market.get("open_interest"),
            packet.get("summary") or packet.get("signals"),
        ]
        present = sum(1 for f in fields if f is not None)
        return present / len(fields) * 100.0

    def _reason_codes(self, dimensions: Dict[str, float], score: float) -> List[str]:
        reasons = []
        if dimensions["freshness"] >= 80:
            reasons.append("fresh_information")
        if dimensions["market_reaction_lag"] >= 70:
            reasons.append("market_reaction_lag_detected")
        if dimensions["price_inefficiency"] >= 70:
            reasons.append("large_price_probability_gap")
        if dimensions["source_reliability"] >= 80:
            reasons.append("reliable_source")
        if dimensions["cross_market_confirmation"] >= 70:
            reasons.append("cross_market_confirmation")
        if dimensions["volume_confirmation"] >= 70:
            reasons.append("volume_confirms_information")
        if score < 55:
            reasons.append("weak_information_edge")
        return reasons or ["moderate_information_edge"]

    def _catchup_minutes(self, score: float, dimensions: Dict[str, float]) -> Optional[float]:
        if score < 55:
            return None
        lag = dimensions.get("market_reaction_lag", 50.0)
        freshness = dimensions.get("freshness", 50.0)
        minutes = 60.0 - (score * 0.35) - (lag * 0.15) - (freshness * 0.10)
        return round(max(3.0, min(60.0, minutes)), 2)

    def _grade(self, score: float) -> str:
        if score >= 90:
            return "A+"
        if score >= 85:
            return "A"
        if score >= 80:
            return "A-"
        if score >= 75:
            return "B+"
        if score >= 70:
            return "B"
        if score >= 60:
            return "C"
        return "WATCH"

    def _level(self, score: float) -> str:
        if score >= 85:
            return "very_high"
        if score >= 75:
            return "high"
        if score >= 65:
            return "medium"
        if score >= 55:
            return "low"
        return "weak"

    def _parse_time(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    def _num(self, value: Any) -> Optional[float]:
        try:
            v = float(value)
            if math.isfinite(v):
                return v
            return None
        except Exception:
            return None


information_edge_engine = InformationEdgeEngine()
'''

test_code = r'''from qseries_v2.oracle_intelligence.information_edge_engine import information_edge_engine


def test_oi_081_information_edge_engine():
    market = {
        "ticker": "INFO-EDGE-TEST",
        "price": 52,
        "price_delta_pct": 1,
        "volume": 50000,
        "previous_volume": 10000,
        "liquidity": 30000,
        "spread": 2,
        "cross_market_confirmation": 0.85,
    }

    information = {
        "headline": "Major catalyst released",
        "source": "official_feed",
        "source_tier": "official",
        "age_seconds": 45,
        "expected_price_move_pct": 8,
    }

    packet = {
        "research_quality_score": 90,
        "summary": {
            "expected_probability": 0.72,
            "research_quality_score": 90,
        },
        "signals": {
            "final_research_grade": "A",
        },
    }

    result = information_edge_engine.score_information_edge(market, information, packet)

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["ticker"] == "INFO-EDGE-TEST"
    assert result["information_edge_score"] >= 70
    assert result["edge_grade"] in {"A+", "A", "A-", "B+", "B"}
    assert result["execution_enabled"] is False
    assert "fresh_information" in result["reason_codes"]
    assert "reliable_source" in result["reason_codes"]

    batch = information_edge_engine.score_batch(
        markets=[market, {"ticker": "WEAK", "price": 90}],
        information_by_ticker={"INFO-EDGE-TEST": information},
        packets_by_ticker={"INFO-EDGE-TEST": packet},
    )

    assert batch["status"] == "ok"
    assert batch["markets_scored"] == 2
    assert batch["top_edges"][0]["ticker"] == "INFO-EDGE-TEST"

    status = information_edge_engine.status()
    assert status["status"] == "ok"

    print("[PASS] OI-081 Information Edge Engine")
    print({
        "score": result["information_edge_score"],
        "grade": result["edge_grade"],
        "level": result["edge_level"],
        "reasons": result["reason_codes"],
        "catchup_minutes": result["estimated_market_catchup_minutes"],
    })


if __name__ == "__main__":
    test_oi_081_information_edge_engine()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .information_edge_engine import information_edge_engine, InformationEdgeEngine\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-081 INSTALLER")
print(" Information Edge Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-081 installed")
print()
print("Run:")
print("python test_oi_081_information_edge_engine.py")
