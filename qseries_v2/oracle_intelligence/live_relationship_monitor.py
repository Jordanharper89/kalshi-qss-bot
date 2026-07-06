from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List, Optional


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


@dataclass
class LiveRelationshipPacket:
    module: str
    status: str
    generated_at: str
    live_markets_analyzed: int
    historical_relationships_found: int
    drift_alerts: List[Dict[str, Any]]
    delayed_followers: List[Dict[str, Any]]
    relationship_anomalies: List[Dict[str, Any]]
    monitor_summary: Dict[str, Any]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LiveRelationshipMonitor:
    def __init__(self, relationship_engine=None):
        self.relationship_engine = relationship_engine
        self.last_packet: Optional[Dict[str, Any]] = None

        if self.relationship_engine is None:
            try:
                from .market_relationship_engine import oracle_relationship_engine
                self.relationship_engine = oracle_relationship_engine
            except Exception:
                pass

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "OI-038 Live Relationship Monitor",
            "status": "ok" if self.relationship_engine is not None else "missing_relationship_engine",
            "relationship_engine_ready": self.relationship_engine is not None,
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def monitor(self, live_markets: List[Dict[str, Any]]) -> Dict[str, Any]:
        snapshot = self._relationship_snapshot(live_markets)

        drift = self._detect_correlation_drift(live_markets, snapshot)
        delayed = self._detect_delayed_followers(live_markets, snapshot)
        anomalies = self._detect_anomalies(live_markets, snapshot, drift, delayed)

        packet = LiveRelationshipPacket(
            module="OI-038 Live Relationship Monitor",
            status=snapshot.get("status", "unknown"),
            generated_at=self._now(),
            live_markets_analyzed=len(live_markets),
            historical_relationships_found=(snapshot.get("market_correlations") or {}).get("pair_count", 0),
            drift_alerts=drift,
            delayed_followers=delayed,
            relationship_anomalies=anomalies,
            monitor_summary=self._summary(drift, delayed, anomalies),
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_packet = packet
        return packet

    def relationship_alerts(self, live_markets: List[Dict[str, Any]]) -> Dict[str, Any]:
        packet = self.monitor(live_markets)
        return {
            "module": "OI-038 Live Relationship Monitor",
            "status": packet.get("status"),
            "alerts": {
                "drift": packet.get("drift_alerts", []),
                "delayed_followers": packet.get("delayed_followers", []),
                "anomalies": packet.get("relationship_anomalies", []),
            },
            "read_only": True,
            "execution_allowed": False,
        }

    def latest(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return {
                "module": "OI-038 Live Relationship Monitor",
                "status": "no_monitor_run_yet",
                "read_only": True,
                "execution_allowed": False,
            }
        return self.last_packet

    def _relationship_snapshot(self, live_markets: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.relationship_engine is None:
            return {
                "status": "missing_relationship_engine",
                "market_correlations": {"pairs": [], "pair_count": 0},
                "lead_lag": {"relationships": []},
                "influence_scores": {},
                "live_context": {},
                "read_only": True,
                "execution_allowed": False,
            }

        if hasattr(self.relationship_engine, "correlation_snapshot"):
            return self.relationship_engine.correlation_snapshot(live_markets=live_markets)

        return {
            "status": "invalid_relationship_engine",
            "market_correlations": {"pairs": [], "pair_count": 0},
            "lead_lag": {"relationships": []},
            "influence_scores": {},
            "live_context": {},
            "read_only": True,
            "execution_allowed": False,
        }

    def _detect_correlation_drift(self, live_markets: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        live_map = self._live_map(live_markets)
        pairs = (snapshot.get("market_correlations") or {}).get("pairs", [])
        alerts = []

        for pair in pairs:
            a = pair.get("market_a")
            b = pair.get("market_b")

            if a not in live_map or b not in live_map:
                continue

            live_a = live_map[a]
            live_b = live_map[b]

            move_a = _safe_float(live_a.get("price_change") or live_a.get("yes_change") or live_a.get("change"))
            move_b = _safe_float(live_b.get("price_change") or live_b.get("yes_change") or live_b.get("change"))
            historical_corr = _safe_float(pair.get("correlation"))

            if historical_corr >= 0.4 and move_a * move_b < 0:
                alerts.append({
                    "type": "positive_relationship_break",
                    "market_a": a,
                    "market_b": b,
                    "historical_correlation": historical_corr,
                    "live_move_a": move_a,
                    "live_move_b": move_b,
                    "severity": self._severity(abs(historical_corr) * 100),
                })

            if historical_corr <= -0.4 and move_a * move_b > 0:
                alerts.append({
                    "type": "negative_relationship_break",
                    "market_a": a,
                    "market_b": b,
                    "historical_correlation": historical_corr,
                    "live_move_a": move_a,
                    "live_move_b": move_b,
                    "severity": self._severity(abs(historical_corr) * 100),
                })

        return alerts[:50]

    def _detect_delayed_followers(self, live_markets: List[Dict[str, Any]], snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        live_map = self._live_map(live_markets)
        relationships = (snapshot.get("lead_lag") or {}).get("relationships", [])
        alerts = []

        for rel in relationships:
            leader = rel.get("leader")
            follower = rel.get("follower")

            if leader not in live_map or follower not in live_map:
                continue

            leader_move = abs(_safe_float(live_map[leader].get("price_change") or live_map[leader].get("yes_change") or live_map[leader].get("change")))
            follower_move = abs(_safe_float(live_map[follower].get("price_change") or live_map[follower].get("yes_change") or live_map[follower].get("change")))

            if leader_move >= 3.0 and follower_move <= 1.0:
                alerts.append({
                    "type": "possible_delayed_follower",
                    "leader": leader,
                    "follower": follower,
                    "leader_move": leader_move,
                    "follower_move": follower_move,
                    "historical_lag_buckets": rel.get("lag_buckets"),
                    "historical_correlation": rel.get("correlation"),
                    "severity": self._severity(leader_move * 12),
                })

        return alerts[:50]

    def _detect_anomalies(
        self,
        live_markets: List[Dict[str, Any]],
        snapshot: Dict[str, Any],
        drift: List[Dict[str, Any]],
        delayed: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        anomalies = []

        influence = snapshot.get("influence_scores", {}) or {}
        live_map = self._live_map(live_markets)

        for ticker, live in live_map.items():
            score = _safe_float((influence.get(ticker) or {}).get("score"))
            move = abs(_safe_float(live.get("price_change") or live.get("yes_change") or live.get("change")))
            volume_change = abs(_safe_float(live.get("volume_change")))

            if score >= 50 and move >= 4:
                anomalies.append({
                    "type": "high_influence_market_moving",
                    "ticker": ticker,
                    "influence_score": score,
                    "live_move": move,
                    "volume_change": volume_change,
                    "severity": self._severity(score),
                })

        if len(drift) >= 3:
            anomalies.append({
                "type": "broad_relationship_drift",
                "count": len(drift),
                "severity": "high",
            })

        if len(delayed) >= 3:
            anomalies.append({
                "type": "multi_market_delayed_reaction",
                "count": len(delayed),
                "severity": "high",
            })

        return anomalies[:50]

    def _summary(self, drift: List[Dict[str, Any]], delayed: List[Dict[str, Any]], anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(drift) + len(delayed) + len(anomalies)

        if total >= 10:
            label = "high_activity"
        elif total >= 4:
            label = "moderate_activity"
        elif total >= 1:
            label = "light_activity"
        else:
            label = "normal"

        return {
            "status": label,
            "drift_alerts": len(drift),
            "delayed_followers": len(delayed),
            "relationship_anomalies": len(anomalies),
            "total_alerts": total,
            "read_only": True,
            "execution_allowed": False,
        }

    def _live_map(self, live_markets: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        out = {}
        for market in live_markets:
            ticker = market.get("ticker") or market.get("market_ticker") or market.get("symbol")
            if ticker:
                out[str(ticker)] = market
        return out

    def _severity(self, score: float) -> str:
        score = _safe_float(score)
        if score >= 85:
            return "critical"
        if score >= 70:
            return "high"
        if score >= 40:
            return "medium"
        return "low"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_live_relationship_monitor = LiveRelationshipMonitor()
