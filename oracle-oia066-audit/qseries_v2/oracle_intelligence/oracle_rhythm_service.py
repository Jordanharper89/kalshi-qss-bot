"""
OI-023 Oracle Rhythm Service Integration

Purpose:
- Expose OI-021 Market Rhythm Analyzer and OI-022 Rhythm Insight Bridge
  as a clean Oracle Intelligence service surface.
- Provide diagnostics, snapshot, insight packet, and context methods.
- Remain read-only.
- No trade execution.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from .market_rhythm_analyzer import oracle_market_rhythm_analyzer
except Exception:
    oracle_market_rhythm_analyzer = None

try:
    from .rhythm_insight_bridge import oracle_rhythm_insight_bridge, RhythmInsightBridge
except Exception:
    oracle_rhythm_insight_bridge = None
    RhythmInsightBridge = None


@dataclass
class OracleRhythmServiceState:
    module: str
    status: str
    generated_at: str
    analyzer_ready: bool
    bridge_ready: bool
    rows_analyzed: int
    rhythm_snapshot_ready: bool
    rhythm_packet_ready: bool
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleRhythmService:
    """
    Service layer for Oracle rhythm intelligence.

    This class intentionally does not place orders, send execution commands,
    or mutate trading state. It only reads historical intelligence.
    """

    def __init__(self, analyzer=None, bridge=None):
        self.analyzer = analyzer or oracle_market_rhythm_analyzer

        if bridge is not None:
            self.bridge = bridge
        elif oracle_rhythm_insight_bridge is not None:
            self.bridge = oracle_rhythm_insight_bridge
        elif RhythmInsightBridge is not None and self.analyzer is not None:
            self.bridge = RhythmInsightBridge(self.analyzer)
        else:
            self.bridge = None

        self.last_state: Optional[Dict[str, Any]] = None

    def diagnostics(self) -> Dict[str, Any]:
        analyzer_diag = {}
        bridge_diag = {}

        if self.analyzer is not None and hasattr(self.analyzer, "diagnostics"):
            analyzer_diag = self.analyzer.diagnostics()

        if self.bridge is not None and hasattr(self.bridge, "diagnostics"):
            bridge_diag = self.bridge.diagnostics()

        return {
            "module": "OI-023 Oracle Rhythm Service Integration",
            "status": self._status(analyzer_diag, bridge_diag),
            "analyzer_ready": self.analyzer is not None,
            "bridge_ready": self.bridge is not None,
            "analyzer_status": analyzer_diag.get("status"),
            "bridge_status": bridge_diag.get("status"),
            "read_only": True,
            "execution_allowed": False,
        }

    def refresh(self) -> Dict[str, Any]:
        """
        Refresh rhythm intelligence and return service state.
        """

        snapshot = self.get_rhythm_snapshot(force=True)
        packet = self.get_rhythm_packet(force=True)

        state = OracleRhythmServiceState(
            module="OI-023 Oracle Rhythm Service Integration",
            status=packet.get("status") or snapshot.get("status") or "unknown",
            generated_at=self._now(),
            analyzer_ready=self.analyzer is not None,
            bridge_ready=self.bridge is not None,
            rows_analyzed=max(
                int(snapshot.get("rows_analyzed", 0) or 0),
                int(packet.get("rows_analyzed", 0) or 0),
            ),
            rhythm_snapshot_ready=bool(snapshot),
            rhythm_packet_ready=bool(packet),
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_state = state
        return state

    def get_state(self) -> Dict[str, Any]:
        if self.last_state is None:
            return self.refresh()
        return self.last_state

    def get_rhythm_snapshot(self, force: bool = False) -> Dict[str, Any]:
        if self.analyzer is None:
            return {
                "module": "OI-021 Market Rhythm Analyzer",
                "status": "missing_analyzer",
                "rows_analyzed": 0,
                "read_only": True,
                "execution_allowed": False,
            }

        if force and hasattr(self.analyzer, "analyze"):
            return self.analyzer.analyze()

        if hasattr(self.analyzer, "get_snapshot"):
            return self.analyzer.get_snapshot()

        if hasattr(self.analyzer, "analyze"):
            return self.analyzer.analyze()

        return {
            "module": "OI-021 Market Rhythm Analyzer",
            "status": "invalid_analyzer",
            "rows_analyzed": 0,
            "read_only": True,
            "execution_allowed": False,
        }

    def get_rhythm_packet(self, force: bool = False) -> Dict[str, Any]:
        if self.bridge is None:
            return {
                "module": "OI-022 Rhythm Insight Bridge",
                "status": "missing_bridge",
                "rows_analyzed": 0,
                "read_only": True,
                "execution_allowed": False,
            }

        if force and hasattr(self.bridge, "build_packet"):
            return self.bridge.build_packet()

        if hasattr(self.bridge, "get_packet"):
            return self.bridge.get_packet()

        if hasattr(self.bridge, "build_packet"):
            return self.bridge.build_packet()

        return {
            "module": "OI-022 Rhythm Insight Bridge",
            "status": "invalid_bridge",
            "rows_analyzed": 0,
            "read_only": True,
            "execution_allowed": False,
        }

    def get_oracle_context(self) -> Dict[str, Any]:
        """
        Main method other Oracle Intelligence modules should call.
        """

        packet = self.get_rhythm_packet()

        if self.bridge is not None and hasattr(self.bridge, "oracle_context"):
            context = self.bridge.oracle_context()
        else:
            context = {
                "context_type": "market_rhythm",
                "status": packet.get("status"),
                "rows_analyzed": packet.get("rows_analyzed", 0),
                "summary": packet.get("oracle_summary", []),
                "market_clock": packet.get("market_clock", {}),
                "category_intelligence": packet.get("category_intelligence", {}),
            }

        context["service_module"] = "OI-023 Oracle Rhythm Service Integration"
        context["read_only"] = True
        context["execution_allowed"] = False

        return context

    def api_payload(self) -> Dict[str, Any]:
        """
        API-safe payload for Oracle API layer or dashboards.
        """

        state = self.get_state()
        context = self.get_oracle_context()

        return {
            "module": "oracle_rhythm_service_payload",
            "status": state.get("status"),
            "state": state,
            "context": context,
            "read_only": True,
            "execution_allowed": False,
        }

    def _status(self, analyzer_diag: Dict[str, Any], bridge_diag: Dict[str, Any]) -> str:
        if self.analyzer is None:
            return "missing_analyzer"
        if self.bridge is None:
            return "missing_bridge"

        analyzer_status = analyzer_diag.get("status")
        bridge_status = bridge_diag.get("status")

        if analyzer_status in {"ok", "waiting_for_history_db"} and bridge_status in {"ok", "waiting_for_history_db"}:
            return "ok"

        if analyzer_status == "waiting_for_history_db":
            return "waiting_for_history_db"

        return "degraded"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_rhythm_service = OracleRhythmService()
