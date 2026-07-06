from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class RuntimePacket:
    module: str
    status: str
    generated_at: str
    runtime_status: str
    snapshots_processed: int
    batches_processed: int
    last_event: Dict[str, Any]
    learning_loop_status: Dict[str, Any]
    intelligence_packet: Dict[str, Any]
    diagnostics: Dict[str, Any]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleIntelligenceRuntimeOrchestrator:
    def __init__(self, learning_loop=None):
        self.learning_loop = learning_loop
        self.started = False
        self.started_at: Optional[str] = None
        self.snapshots_processed = 0
        self.batches_processed = 0
        self.last_packet: Optional[Dict[str, Any]] = None

        if self.learning_loop is None:
            try:
                from .event_driven_learning_loop import oracle_event_learning_loop
                self.learning_loop = oracle_event_learning_loop
            except Exception:
                pass

    def start(self) -> Dict[str, Any]:
        self.started = True
        self.started_at = self.started_at or self._now()
        return self.diagnostics()

    def stop(self) -> Dict[str, Any]:
        self.started = False
        return self.diagnostics()

    def diagnostics(self) -> Dict[str, Any]:
        loop_diag = {}
        if self.learning_loop is not None and hasattr(self.learning_loop, "diagnostics"):
            loop_diag = self.learning_loop.diagnostics()

        return {
            "module": "OI-040 Oracle Intelligence Runtime Orchestrator",
            "status": "ok" if self.learning_loop is not None else "missing_learning_loop",
            "runtime_status": "running" if self.started else "stopped",
            "started": self.started,
            "started_at": self.started_at,
            "learning_loop_ready": self.learning_loop is not None,
            "learning_loop_diagnostics": loop_diag,
            "snapshots_processed": self.snapshots_processed,
            "batches_processed": self.batches_processed,
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def process_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        if not self.started:
            self.start()

        self.snapshots_processed += 1

        loop_packet = self._process_snapshot(snapshot)
        packet = self._runtime_packet(
            event_type="single_snapshot",
            snapshots=[snapshot],
            loop_packet=loop_packet,
        )

        self.last_packet = packet
        return packet

    def process_batch(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.started:
            self.start()

        self.batches_processed += 1
        self.snapshots_processed += len(snapshots)

        loop_packet = self._process_batch(snapshots)
        packet = self._runtime_packet(
            event_type="snapshot_batch",
            snapshots=snapshots,
            loop_packet=loop_packet,
        )

        self.last_packet = packet
        return packet

    def intelligence_packet(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return {
                "module": "OI-040 Oracle Intelligence Runtime Orchestrator",
                "status": "no_runtime_packet_yet",
                "read_only": True,
                "execution_allowed": False,
            }
        return self.last_packet

    def api_payload(self) -> Dict[str, Any]:
        packet = self.intelligence_packet()
        return {
            "module": "oracle_intelligence_runtime_payload",
            "status": packet.get("status"),
            "runtime_status": packet.get("runtime_status"),
            "snapshots_processed": packet.get("snapshots_processed"),
            "batches_processed": packet.get("batches_processed"),
            "intelligence_packet": packet.get("intelligence_packet"),
            "read_only": True,
            "execution_allowed": False,
        }

    def _process_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        if self.learning_loop is None:
            return {
                "status": "missing_learning_loop",
                "read_only": True,
                "execution_allowed": False,
            }

        if hasattr(self.learning_loop, "process_market_snapshot"):
            return self.learning_loop.process_market_snapshot(snapshot)

        if hasattr(self.learning_loop, "process_event"):
            return self.learning_loop.process_event({
                "type": "market_snapshot",
                "snapshot": snapshot,
            })

        return {
            "status": "invalid_learning_loop",
            "read_only": True,
            "execution_allowed": False,
        }

    def _process_batch(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.learning_loop is None:
            return {
                "status": "missing_learning_loop",
                "read_only": True,
                "execution_allowed": False,
            }

        if hasattr(self.learning_loop, "process_market_batch"):
            return self.learning_loop.process_market_batch(snapshots)

        if hasattr(self.learning_loop, "process_event"):
            return self.learning_loop.process_event({
                "type": "market_snapshot_batch",
                "snapshots": snapshots,
            })

        return {
            "status": "invalid_learning_loop",
            "read_only": True,
            "execution_allowed": False,
        }

    def _runtime_packet(self, event_type: str, snapshots: List[Dict[str, Any]], loop_packet: Dict[str, Any]) -> Dict[str, Any]:
        intelligence = self._extract_intelligence(loop_packet)

        packet = RuntimePacket(
            module="OI-040 Oracle Intelligence Runtime Orchestrator",
            status=loop_packet.get("status", "unknown"),
            generated_at=self._now(),
            runtime_status="running" if self.started else "stopped",
            snapshots_processed=self.snapshots_processed,
            batches_processed=self.batches_processed,
            last_event={
                "event_type": event_type,
                "snapshot_count": len(snapshots),
                "tickers": [
                    s.get("ticker") or s.get("market_ticker") or s.get("symbol")
                    for s in snapshots
                ],
            },
            learning_loop_status={
                "status": loop_packet.get("status"),
                "summary": loop_packet.get("learning_summary", {}),
            },
            intelligence_packet=intelligence,
            diagnostics=self.diagnostics(),
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        return packet

    def _extract_intelligence(self, loop_packet: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "historical_update": loop_packet.get("historical_update", {}),
            "relationship_update": {
                "status": (loop_packet.get("relationship_update") or {}).get("status"),
                "summary": (loop_packet.get("relationship_update") or {}).get("monitor_summary", {}),
            },
            "forecast_update": {
                "status": (loop_packet.get("forecast_update") or {}).get("status"),
                "reports_generated": (loop_packet.get("forecast_update") or {}).get("reports_generated", 0),
                "reports": (loop_packet.get("forecast_update") or {}).get("reports", []),
            },
            "explanation_update": {
                "status": (loop_packet.get("explanation_update") or {}).get("status"),
                "explanations_generated": (loop_packet.get("explanation_update") or {}).get("explanations_generated", 0),
                "explanations": (loop_packet.get("explanation_update") or {}).get("explanations", []),
            },
            "read_only": True,
            "execution_allowed": False,
        }

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_intelligence_runtime = OracleIntelligenceRuntimeOrchestrator()
