from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "market_reaction_timeline_engine.py"
TEST = ROOT / "test_oi_082_market_reaction_timeline_engine.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-082 Market Reaction Timeline Engine

Purpose:
- Learn and model the sequence in which related prediction markets react to catalysts.
- Identify lead/lag relationships, expected reaction windows, delayed markets, and catch-up candidates.
- Support Oracle's Information Edge layer by estimating which markets have not reacted yet.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import math


class MarketReactionTimelineEngine:
    module_name = "oi_082_market_reaction_timeline_engine"

    def __init__(self) -> None:
        self._observations: List[Dict[str, Any]] = []
        self._timeline_memory: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "observations": len(self._observations),
            "timeline_keys": len(self._timeline_memory),
        }

    def record_reaction_sequence(
        self,
        catalyst_id: str,
        catalyst_type: str,
        market_reactions: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cleaned = [self._clean_reaction(r) for r in market_reactions or []]
        cleaned = [r for r in cleaned if r.get("ticker")]
        cleaned.sort(key=lambda r: r["reaction_time_minutes"])

        observation = {
            "catalyst_id": str(catalyst_id),
            "catalyst_type": str(catalyst_type),
            "recorded_at": self._now(),
            "reaction_count": len(cleaned),
            "market_reactions": cleaned,
            "metadata": metadata or {},
        }

        self._observations.append(observation)
        self._timeline_memory[str(catalyst_type)].append(observation)

        return {
            "status": "ok",
            "read_only": True,
            "catalyst_id": str(catalyst_id),
            "catalyst_type": str(catalyst_type),
            "reaction_count": len(cleaned),
            "sequence": cleaned,
        }

    def build_timeline_model(self, catalyst_type: Optional[str] = None) -> Dict[str, Any]:
        observations = self._select_observations(catalyst_type)
        market_stats: Dict[str, Dict[str, Any]] = {}

        for obs in observations:
            for idx, reaction in enumerate(obs.get("market_reactions", [])):
                key = reaction.get("market_type") or reaction.get("category") or reaction.get("ticker")
                bucket = market_stats.setdefault(key, {
                    "market_key": key,
                    "count": 0,
                    "reaction_times": [],
                    "reaction_strengths": [],
                    "lead_positions": [],
                    "directions": defaultdict(int),
                })
                bucket["count"] += 1
                bucket["reaction_times"].append(reaction["reaction_time_minutes"])
                bucket["reaction_strengths"].append(reaction["reaction_strength"])
                bucket["lead_positions"].append(idx + 1)
                bucket["directions"][reaction.get("direction") or "UNKNOWN"] += 1

        modeled = [self._summarize_market_stats(stats) for stats in market_stats.values()]
        modeled.sort(key=lambda x: (x["avg_reaction_time_minutes"], x["avg_lead_position"]))
        lead_lag_edges = self._lead_lag_edges(observations)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "catalyst_type": catalyst_type,
            "observation_count": len(observations),
            "market_timeline": modeled,
            "lead_lag_edges": lead_lag_edges,
            "summary": self._model_summary(modeled, lead_lag_edges),
        }

    def analyze_current_reaction(
        self,
        catalyst_type: str,
        current_markets: List[Dict[str, Any]],
        elapsed_minutes: float,
    ) -> Dict[str, Any]:
        model = self.build_timeline_model(catalyst_type)
        timeline = model.get("market_timeline", [])
        expected_by_key = {row["market_key"]: row for row in timeline}
        results = []

        for market in current_markets or []:
            key = market.get("market_type") or market.get("category") or market.get("ticker")
            expected = expected_by_key.get(key)
            results.append(self._analyze_market_reaction_status(market, expected, elapsed_minutes))

        results.sort(key=lambda r: (r["catch_up_score"], r["reaction_lag_minutes"]), reverse=True)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "catalyst_type": catalyst_type,
            "elapsed_minutes": float(elapsed_minutes),
            "markets_analyzed": len(results),
            "reaction_status": results,
            "catch_up_candidates": [r for r in results if r["catch_up_candidate"]],
            "summary": self._current_summary(results),
            "timeline_model": model,
        }

    def expected_reaction_window(self, catalyst_type: str, market_key: str) -> Dict[str, Any]:
        model = self.build_timeline_model(catalyst_type)
        for row in model.get("market_timeline", []):
            if row["market_key"] == market_key:
                return {
                    "status": "ok",
                    "read_only": True,
                    "catalyst_type": catalyst_type,
                    "market_key": market_key,
                    "expected_start_minute": row["p25_reaction_time_minutes"],
                    "expected_median_minute": row["median_reaction_time_minutes"],
                    "expected_late_minute": row["p75_reaction_time_minutes"],
                    "avg_reaction_strength": row["avg_reaction_strength"],
                    "confidence": row["model_confidence"],
                }

        return {"status": "not_found", "read_only": True, "catalyst_type": catalyst_type, "market_key": market_key}

    def _analyze_market_reaction_status(self, market: Dict[str, Any], expected: Optional[Dict[str, Any]], elapsed_minutes: float) -> Dict[str, Any]:
        key = market.get("market_type") or market.get("category") or market.get("ticker")
        ticker = market.get("ticker") or market.get("market_ticker") or key
        current_reaction_strength = self._num(
            market.get("reaction_strength") or market.get("price_delta_pct") or market.get("move_pct") or market.get("momentum"),
            0.0,
        )

        if not expected:
            return {
                "ticker": ticker,
                "market_key": key,
                "status": "unknown_model",
                "read_only": True,
                "expected_reaction_time_minutes": None,
                "reaction_lag_minutes": 0.0,
                "current_reaction_strength": current_reaction_strength,
                "expected_reaction_strength": None,
                "catch_up_candidate": False,
                "catch_up_score": 0.0,
                "reason_codes": ["no_timeline_model"],
            }

        expected_time = expected.get("median_reaction_time_minutes") or expected.get("avg_reaction_time_minutes") or 0.0
        expected_strength = expected.get("avg_reaction_strength") or 0.0
        late_window = expected.get("p75_reaction_time_minutes") or expected_time
        lag = float(elapsed_minutes) - float(expected_time)
        strength_gap = max(0.0, float(expected_strength) - abs(float(current_reaction_strength)))
        reacted = abs(float(current_reaction_strength)) >= max(1.0, float(expected_strength) * 0.35)
        overdue = float(elapsed_minutes) > float(late_window)

        catch_up_score = 0.0
        reason_codes = []

        if overdue and not reacted:
            catch_up_score += 45.0
            reason_codes.append("reaction_overdue")
        if strength_gap > 0:
            catch_up_score += min(35.0, strength_gap * 4.0)
            reason_codes.append("reaction_strength_gap")
        if expected.get("model_confidence", 0) >= 60:
            catch_up_score += 15.0
            reason_codes.append("high_confidence_timeline_model")
        if expected.get("avg_lead_position", 99) > 1:
            catch_up_score += 5.0
            reason_codes.append("historically_lagging_market")

        catch_up_score = max(0.0, min(100.0, catch_up_score))
        catch_up = catch_up_score >= 55.0

        if not reason_codes:
            reason_codes.append("reaction_in_line")

        status = "catch_up_candidate" if catch_up else "reacted" if reacted else "monitor"

        return {
            "ticker": ticker,
            "market_key": key,
            "status": status,
            "read_only": True,
            "expected_reaction_time_minutes": round(float(expected_time), 2),
            "reaction_lag_minutes": round(lag, 2),
            "current_reaction_strength": round(float(current_reaction_strength), 4),
            "expected_reaction_strength": round(float(expected_strength), 4),
            "catch_up_candidate": catch_up,
            "catch_up_score": round(catch_up_score, 2),
            "reason_codes": reason_codes,
        }

    def _lead_lag_edges(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        edges: Dict[str, Dict[str, Any]] = {}
        for obs in observations:
            reactions = obs.get("market_reactions", [])
            for earlier, later in zip(reactions, reactions[1:]):
                a = earlier.get("market_type") or earlier.get("category") or earlier.get("ticker")
                b = later.get("market_type") or later.get("category") or later.get("ticker")
                key = f"{a}->{b}"
                delay = later["reaction_time_minutes"] - earlier["reaction_time_minutes"]
                bucket = edges.setdefault(key, {"source": a, "target": b, "count": 0, "delays": [], "strengths": []})
                bucket["count"] += 1
                bucket["delays"].append(delay)
                bucket["strengths"].append(later["reaction_strength"])

        rows = []
        for edge in edges.values():
            rows.append({
                "source": edge["source"],
                "target": edge["target"],
                "count": edge["count"],
                "avg_delay_minutes": round(sum(edge["delays"]) / len(edge["delays"]), 2),
                "avg_target_strength": round(sum(edge["strengths"]) / len(edge["strengths"]), 4),
                "confidence": round(min(100.0, 45.0 + edge["count"] * 10.0), 2),
            })
        rows.sort(key=lambda r: (r["confidence"], -r["avg_delay_minutes"]), reverse=True)
        return rows

    def _summarize_market_stats(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        times = sorted(stats["reaction_times"])
        strengths = stats["reaction_strengths"]
        positions = stats["lead_positions"]
        dominant_direction = max(stats["directions"].items(), key=lambda kv: kv[1])[0] if stats["directions"] else "UNKNOWN"
        count = stats["count"]
        return {
            "market_key": stats["market_key"],
            "count": count,
            "avg_reaction_time_minutes": round(sum(times) / len(times), 2),
            "median_reaction_time_minutes": round(self._percentile(times, 50), 2),
            "p25_reaction_time_minutes": round(self._percentile(times, 25), 2),
            "p75_reaction_time_minutes": round(self._percentile(times, 75), 2),
            "avg_reaction_strength": round(sum(strengths) / len(strengths), 4),
            "avg_lead_position": round(sum(positions) / len(positions), 2),
            "dominant_direction": dominant_direction,
            "model_confidence": round(min(100.0, 45.0 + count * 10.0), 2),
        }

    def _model_summary(self, modeled: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not modeled:
            return {"status": "empty", "fastest_market": None, "slowest_market": None, "edge_count": 0}
        return {
            "status": "ok",
            "fastest_market": modeled[0]["market_key"],
            "slowest_market": modeled[-1]["market_key"],
            "edge_count": len(edges),
            "modeled_markets": len(modeled),
        }

    def _current_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        candidates = [r for r in results if r["catch_up_candidate"]]
        return {
            "catch_up_candidate_count": len(candidates),
            "top_candidate": candidates[0]["ticker"] if candidates else None,
            "avg_catch_up_score": round(sum(r["catch_up_score"] for r in results) / len(results), 2) if results else 0.0,
        }

    def _clean_reaction(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ticker": row.get("ticker") or row.get("market_ticker"),
            "market_type": row.get("market_type") or row.get("category"),
            "category": row.get("category"),
            "reaction_time_minutes": self._num(row.get("reaction_time_minutes"), 0.0),
            "reaction_strength": self._num(row.get("reaction_strength") or row.get("move_pct") or row.get("price_delta_pct"), 0.0),
            "direction": str(row.get("direction") or "UNKNOWN").upper(),
            "confidence": self._num(row.get("confidence"), 50.0),
        }

    def _select_observations(self, catalyst_type: Optional[str]) -> List[Dict[str, Any]]:
        if catalyst_type:
            return list(self._timeline_memory.get(str(catalyst_type), []))
        return list(self._observations)

    def _percentile(self, values: List[float], pct: float) -> float:
        if not values:
            return 0.0
        if len(values) == 1:
            return values[0]
        k = (len(values) - 1) * (pct / 100.0)
        lower = int(math.floor(k))
        upper = int(math.ceil(k))
        if lower == upper:
            return values[lower]
        weight = k - lower
        return values[lower] * (1 - weight) + values[upper] * weight

    def _num(self, value: Any, default: float = 0.0) -> float:
        try:
            v = float(value)
            if math.isfinite(v):
                return v
            return default
        except Exception:
            return default

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


market_reaction_timeline_engine = MarketReactionTimelineEngine()
'''

test_code = r'''from qseries_v2.oracle_intelligence.market_reaction_timeline_engine import MarketReactionTimelineEngine


def test_oi_082_market_reaction_timeline_engine():
    engine = MarketReactionTimelineEngine()

    engine.record_reaction_sequence(
        catalyst_id="CPI-1",
        catalyst_type="macro_cpi",
        market_reactions=[
            {"ticker": "BTC", "market_type": "crypto", "reaction_time_minutes": 2, "reaction_strength": 6, "direction": "YES"},
            {"ticker": "NASDAQ", "market_type": "equities", "reaction_time_minutes": 8, "reaction_strength": 4, "direction": "YES"},
            {"ticker": "RATES", "market_type": "rates", "reaction_time_minutes": 14, "reaction_strength": 5, "direction": "NO"},
        ],
    )

    engine.record_reaction_sequence(
        catalyst_id="CPI-2",
        catalyst_type="macro_cpi",
        market_reactions=[
            {"ticker": "BTC2", "market_type": "crypto", "reaction_time_minutes": 3, "reaction_strength": 7, "direction": "YES"},
            {"ticker": "NASDAQ2", "market_type": "equities", "reaction_time_minutes": 9, "reaction_strength": 4.5, "direction": "YES"},
            {"ticker": "RATES2", "market_type": "rates", "reaction_time_minutes": 16, "reaction_strength": 5.5, "direction": "NO"},
        ],
    )

    model = engine.build_timeline_model("macro_cpi")
    assert model["status"] == "ok"
    assert model["read_only"] is True
    assert model["observation_count"] == 2
    assert model["summary"]["fastest_market"] == "crypto"
    assert model["summary"]["slowest_market"] == "rates"
    assert len(model["lead_lag_edges"]) >= 2

    current = engine.analyze_current_reaction(
        catalyst_type="macro_cpi",
        elapsed_minutes=20,
        current_markets=[
            {"ticker": "BTC-LIVE", "market_type": "crypto", "reaction_strength": 6},
            {"ticker": "RATES-LIVE", "market_type": "rates", "reaction_strength": 0.5},
        ],
    )

    assert current["status"] == "ok"
    assert current["markets_analyzed"] == 2
    assert current["catch_up_candidates"][0]["ticker"] == "RATES-LIVE"

    window = engine.expected_reaction_window("macro_cpi", "rates")
    assert window["status"] == "ok"
    assert window["expected_median_minute"] >= 14

    status = engine.status()
    assert status["status"] == "ok"
    assert status["observations"] == 2

    print("[PASS] OI-082 Market Reaction Timeline Engine")
    print({
        "model_summary": model["summary"],
        "top_catch_up": current["summary"]["top_candidate"],
        "window": window,
    })


if __name__ == "__main__":
    test_oi_082_market_reaction_timeline_engine()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .market_reaction_timeline_engine import market_reaction_timeline_engine, MarketReactionTimelineEngine\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-082 INSTALLER")
print(" Market Reaction Timeline Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-082 installed")
print()
print("Run:")
print("python test_oi_082_market_reaction_timeline_engine.py")
