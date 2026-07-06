
"""
OI-093 Adaptive Influence Decay Engine

Read-only Oracle Intelligence module.

Purpose:
- Model how influence weakens across time and path distance.
- Replace fixed shock-path decay with adaptive decay curves.
- Account for volatility, fragility, resilience, and systemic importance.
- Oracle remains strictly read-only.
- Q Series remains solely responsible for execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import math
import time


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(value)))


@dataclass
class AdaptiveDecayProfile:
    market: str
    decay_rate: float
    half_life_steps: float
    persistence_score: float
    decay_class: str
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdaptiveInfluenceDecayEngine:
    module = "oi_093_adaptive_influence_decay_engine"

    def __init__(self) -> None:
        self.last_profiles: Dict[str, Any] = {}

    def build_decay_profiles(
        self,
        influence_graph: Optional[Dict[str, Any]] = None,
        fragility_report: Optional[Dict[str, Any]] = None,
        resilience_report: Optional[Dict[str, Any]] = None,
        transition_graph: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        influence_graph = influence_graph or {}
        fragility_report = fragility_report or {}
        resilience_report = resilience_report or {}
        transition_graph = transition_graph or {}

        influence = self._index(influence_graph.get("nodes", []), "market")
        fragility = self._index(fragility_report.get("scores", []), "market")
        resilience = self._index(resilience_report.get("scores", []), "market")
        transition = self._index(transition_graph.get("nodes", []), "market")

        markets = set(influence.keys()) | set(fragility.keys()) | set(resilience.keys()) | set(transition.keys())

        profiles: List[AdaptiveDecayProfile] = []
        for market in markets:
            i = influence.get(market, {})
            f = fragility.get(market, {})
            r = resilience.get(market, {})
            t = transition.get(market, {})

            bridge = _safe_float(i.get("bridge_score"))
            outgoing = _safe_float(i.get("outgoing_influence"))
            incoming = _safe_float(i.get("incoming_influence"))
            fragility_score = _safe_float(f.get("fragility_score"))
            resilience_score = _safe_float(r.get("resilience_score"))
            transition_pressure = _safe_float(t.get("transition_pressure"))
            instability = _safe_float(t.get("instability_score"))

            persistence = _clamp(
                bridge * 0.18
                + outgoing * 0.18
                + incoming * 0.10
                + fragility_score * 0.20
                + transition_pressure * 0.17
                + instability * 0.12
                + max(0.0, 100 - resilience_score) * 0.05
            )

            # Higher persistence means slower decay.
            decay_rate = _clamp(0.18 + (100 - persistence) / 100.0 * 0.62, 0.12, 0.85)
            half_life = math.log(0.5) / math.log(max(0.01, 1.0 - decay_rate))

            profiles.append(
                AdaptiveDecayProfile(
                    market=market,
                    decay_rate=round(decay_rate, 4),
                    half_life_steps=round(half_life, 4),
                    persistence_score=round(persistence, 4),
                    decay_class=self._decay_class(decay_rate),
                    reasons=self._reasons(persistence, decay_rate, bridge, fragility_score, resilience_score),
                )
            )

        profiles.sort(key=lambda x: x.persistence_score, reverse=True)

        report = {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "market_count": len(profiles),
            "profiles": [p.to_dict() for p in profiles],
            "slowest_decay_markets": [p.to_dict() for p in profiles[:10]],
            "fastest_decay_markets": [p.to_dict() for p in sorted(profiles, key=lambda x: x.decay_rate, reverse=True)[:10]],
            "decay_class_counts": self._counts(profiles),
        }

        self.last_profiles = report
        return report

    def apply_decay_to_paths(
        self,
        shock_trace: Optional[Dict[str, Any]] = None,
        decay_profiles: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        shock_trace = shock_trace or {}
        decay_profiles = decay_profiles or {}

        profile_lookup = self._index(decay_profiles.get("profiles", []), "market")
        adjusted = []

        for path in shock_trace.get("paths", []):
            if not isinstance(path, dict):
                continue

            markets = path.get("path", [])
            if not isinstance(markets, list):
                markets = []

            score = _safe_float(path.get("shock_score"))
            multiplier = 1.0
            for market in markets[1:]:
                profile = profile_lookup.get(_safe_str(market), {})
                decay_rate = _safe_float(profile.get("decay_rate"), 0.45)
                multiplier *= max(0.0, 1.0 - decay_rate)

            adjusted_score = _clamp(score * multiplier)

            row = dict(path)
            row["adaptive_decay_multiplier"] = round(multiplier, 6)
            row["adaptive_decay_score"] = round(adjusted_score, 4)
            adjusted.append(row)

        adjusted.sort(key=lambda x: x["adaptive_decay_score"], reverse=True)

        return {
            "module": self.module,
            "status": "ok",
            "timestamp": time.time(),
            "read_only": True,
            "source_market": shock_trace.get("source_market"),
            "path_count": len(adjusted),
            "adjusted_paths": adjusted,
            "top_adjusted_paths": adjusted[:10],
        }

    def _index(self, rows: List[Dict[str, Any]], key: str) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            if isinstance(row, dict):
                value = _safe_str(row.get(key)).strip()
                if value:
                    out[value] = row
        return out

    def _decay_class(self, decay_rate: float) -> str:
        if decay_rate <= 0.25:
            return "persistent"
        if decay_rate <= 0.45:
            return "slow_decay"
        if decay_rate <= 0.65:
            return "normal_decay"
        return "fast_decay"

    def _counts(self, profiles: List[AdaptiveDecayProfile]) -> Dict[str, int]:
        counts = {"persistent": 0, "slow_decay": 0, "normal_decay": 0, "fast_decay": 0}
        for profile in profiles:
            counts[profile.decay_class] = counts.get(profile.decay_class, 0) + 1
        return counts

    def _reasons(self, persistence: float, decay_rate: float, bridge: float, fragility: float, resilience: float) -> List[str]:
        reasons = [f"Persistence score is {round(persistence, 2)} and decay rate is {round(decay_rate, 3)}."]
        if bridge >= 55:
            reasons.append("Bridge behavior can keep influence alive across markets.")
        if fragility >= 65:
            reasons.append("High fragility can increase persistence of shock effects.")
        if resilience >= 65:
            reasons.append("Strong resilience helps influence decay faster.")
        if decay_rate <= 0.35:
            reasons.append("Influence is expected to decay slowly.")
        elif decay_rate >= 0.65:
            reasons.append("Influence is expected to decay quickly.")
        return reasons[:8]

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "status": "ok",
            "has_profiles": bool(self.last_profiles),
            "market_count": self.last_profiles.get("market_count", 0),
            "read_only": True,
        }


adaptive_influence_decay_engine = AdaptiveInfluenceDecayEngine()
