from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class LearningLoopPacket:
    module: str
    status: str
    generated_at: str
    event_type: str
    snapshot_count: int
    historical_update: Dict[str, Any]
    relationship_update: Dict[str, Any]
    forecast_update: Dict[str, Any]
    explanation_update: Dict[str, Any]
    learning_summary: Dict[str, Any]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EventDrivenLearningLoop:
    def __init__(
        self,
        history_pipeline=None,
        relationship_monitor=None,
        forecast_service=None,
        explanation_engine=None,
    ):
        self.history_pipeline = history_pipeline
        self.relationship_monitor = relationship_monitor
        self.forecast_service = forecast_service
        self.explanation_engine = explanation_engine
        self.events_processed = 0
        self.last_packet: Optional[Dict[str, Any]] = None

        if self.relationship_monitor is None:
            try:
                from .live_relationship_monitor import oracle_live_relationship_monitor
                self.relationship_monitor = oracle_live_relationship_monitor
            except Exception:
                pass

        if self.forecast_service is None:
            try:
                from .forecast_intelligence_service import oracle_forecast_intelligence_service
                self.forecast_service = oracle_forecast_intelligence_service
            except Exception:
                pass

        if self.explanation_engine is None:
            try:
                from .regime_aware_explanation_engine import oracle_explanation_engine
                self.explanation_engine = oracle_explanation_engine
            except Exception:
                pass

    def diagnostics(self) -> Dict[str, Any]:
        return {
            "module": "OI-039 Event-Driven Learning Loop",
            "status": "ok",
            "history_pipeline_ready": self.history_pipeline is not None,
            "relationship_monitor_ready": self.relationship_monitor is not None,
            "forecast_service_ready": self.forecast_service is not None,
            "explanation_engine_ready": self.explanation_engine is not None,
            "events_processed": self.events_processed,
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def process_market_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        return self.process_event({
            "type": "market_snapshot",
            "snapshots": [snapshot],
        })

    def process_market_batch(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self.process_event({
            "type": "market_snapshot_batch",
            "snapshots": snapshots,
        })

    def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = event.get("type", "unknown_event")
        snapshots = event.get("snapshots") or []
        if event.get("snapshot"):
            snapshots.append(event["snapshot"])

        historical_update = self._historical_update(event, snapshots)
        relationship_update = self._relationship_update(snapshots)
        forecast_update = self._forecast_update(snapshots)
        explanation_update = self._explanation_update(snapshots)

        self.events_processed += 1

        packet = LearningLoopPacket(
            module="OI-039 Event-Driven Learning Loop",
            status="ok",
            generated_at=self._now(),
            event_type=event_type,
            snapshot_count=len(snapshots),
            historical_update=historical_update,
            relationship_update=relationship_update,
            forecast_update=forecast_update,
            explanation_update=explanation_update,
            learning_summary=self._summary(historical_update, relationship_update, forecast_update, explanation_update),
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_packet = packet
        return packet

    def latest(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return {
                "module": "OI-039 Event-Driven Learning Loop",
                "status": "no_event_processed_yet",
                "read_only": True,
                "execution_allowed": False,
            }
        return self.last_packet

    def _historical_update(self, event: Dict[str, Any], snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.history_pipeline is None:
            return {
                "status": "history_pipeline_not_connected",
                "snapshots_received": len(snapshots),
                "recorded": False,
                "read_only": True,
                "execution_allowed": False,
            }

        try:
            if hasattr(self.history_pipeline, "record_batch"):
                result = self.history_pipeline.record_batch(snapshots)
            elif hasattr(self.history_pipeline, "record_snapshot"):
                result = {
                    "records": [
                        self.history_pipeline.record_snapshot(snapshot)
                        for snapshot in snapshots
                    ]
                }
            else:
                result = {"status": "invalid_history_pipeline"}

            return {
                "status": "ok",
                "snapshots_received": len(snapshots),
                "recorded": True,
                "result": result,
                "read_only": True,
                "execution_allowed": False,
            }

        except Exception as exc:
            return {
                "status": "history_update_error",
                "error": str(exc),
                "snapshots_received": len(snapshots),
                "recorded": False,
                "read_only": True,
                "execution_allowed": False,
            }

    def _relationship_update(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.relationship_monitor is None:
            return {
                "status": "relationship_monitor_not_connected",
                "read_only": True,
                "execution_allowed": False,
            }

        try:
            if hasattr(self.relationship_monitor, "monitor"):
                return self.relationship_monitor.monitor(snapshots)
        except Exception as exc:
            return {
                "status": "relationship_monitor_error",
                "error": str(exc),
                "read_only": True,
                "execution_allowed": False,
            }

        return {
            "status": "invalid_relationship_monitor",
            "read_only": True,
            "execution_allowed": False,
        }

    def _forecast_update(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.forecast_service is None:
            return {
                "status": "forecast_service_not_connected",
                "reports": [],
                "read_only": True,
                "execution_allowed": False,
            }

        reports = []
        for snapshot in snapshots[:10]:
            try:
                if hasattr(self.forecast_service, "api_payload"):
                    reports.append(self.forecast_service.api_payload(snapshot))
                elif hasattr(self.forecast_service, "analyze"):
                    reports.append(self.forecast_service.analyze(snapshot))
            except Exception as exc:
                reports.append({
                    "status": "forecast_error",
                    "error": str(exc),
                    "ticker": snapshot.get("ticker"),
                })

        return {
            "status": "ok",
            "reports_generated": len(reports),
            "reports": reports,
            "read_only": True,
            "execution_allowed": False,
        }

    def _explanation_update(self, snapshots: List[Dict[str, Any]]) -> Dict[str, Any]:
        if self.explanation_engine is None:
            return {
                "status": "explanation_engine_not_connected",
                "explanations": [],
                "read_only": True,
                "execution_allowed": False,
            }

        explanations = []
        for snapshot in snapshots[:10]:
            try:
                if hasattr(self.explanation_engine, "api_payload"):
                    explanations.append(self.explanation_engine.api_payload(snapshot))
                elif hasattr(self.explanation_engine, "explain_market"):
                    explanations.append(self.explanation_engine.explain_market(snapshot))
            except Exception as exc:
                explanations.append({
                    "status": "explanation_error",
                    "error": str(exc),
                    "ticker": snapshot.get("ticker"),
                })

        return {
            "status": "ok",
            "explanations_generated": len(explanations),
            "explanations": explanations,
            "read_only": True,
            "execution_allowed": False,
        }

    def _summary(
        self,
        historical_update: Dict[str, Any],
        relationship_update: Dict[str, Any],
        forecast_update: Dict[str, Any],
        explanation_update: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "historical_status": historical_update.get("status"),
            "relationship_status": relationship_update.get("status"),
            "forecast_reports": forecast_update.get("reports_generated", 0),
            "explanations": explanation_update.get("explanations_generated", 0),
            "events_processed": self.events_processed,
            "read_only": True,
            "execution_allowed": False,
        }

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_event_learning_loop = EventDrivenLearningLoop()
