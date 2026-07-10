"""
OOS-001 Opportunity Operating System

Central read-only opportunity manager for Oracle Intelligence V3.

Responsibilities:
- Intake UniversalOpportunity objects
- Register opportunities by deterministic fingerprint
- Detect duplicates
- Track lifecycle transitions
- Preserve immutable opportunity objects
- Emit registry telemetry
- Prepare opportunity flow for future Decision Layer and Q Series execution

Oracle discovers and manages intelligence.
Decision Layer selects.
Q Series executes.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict, replace
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


OOS_VERSION = "OOS-001"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


VALID_TRANSITIONS = {
    "new": {"verified", "rejected", "expired", "archived"},
    "verified": {"ranked", "rejected", "expired", "archived"},
    "ranked": {"assigned", "rejected", "expired", "archived"},
    "assigned": {"executed", "rejected", "expired", "archived"},
    "executed": {"archived"},
    "rejected": {"archived"},
    "expired": {"archived"},
    "archived": set(),
}


@dataclass(frozen=True)
class OpportunityLifecycleEvent:
    opportunity_id: str
    fingerprint: str
    from_status: str
    to_status: str
    reason: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OpportunityRecord:
    fingerprint: str
    opportunity: Any
    status: str
    duplicate_count: int = 0
    first_seen_at: str = field(default_factory=utc_now)
    last_seen_at: str = field(default_factory=utc_now)
    lifecycle: Tuple[OpportunityLifecycleEvent, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        opp_to_dict = getattr(self.opportunity, "to_dict", None)
        opportunity_data = opp_to_dict() if callable(opp_to_dict) else self.opportunity

        return {
            "fingerprint": self.fingerprint,
            "opportunity": opportunity_data,
            "status": self.status,
            "duplicate_count": self.duplicate_count,
            "first_seen_at": self.first_seen_at,
            "last_seen_at": self.last_seen_at,
            "lifecycle": [event.to_dict() for event in self.lifecycle],
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class OpportunityIntakeResult:
    status: str
    fingerprint: str
    opportunity_id: str
    duplicate: bool
    duplicate_count: int
    message: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OpportunityOperatingTelemetry:
    total_registered: int
    active_count: int
    archived_count: int
    duplicate_count: int
    average_quality: float
    lifecycle_event_count: int
    schema_version: str = OOS_VERSION
    read_only: bool = True
    generated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OpportunityOperatingSystem:
    """
    In-memory OOS registry.

    This manager stores immutable opportunity records. It does not execute,
    decide, place orders, or mutate markets.
    """

    schema_version = OOS_VERSION
    read_only = True

    def __init__(self):
        self._records: Dict[str, OpportunityRecord] = {}

    def intake(self, opportunity: Any, source: str = "oracle", metadata: Optional[Dict[str, Any]] = None) -> OpportunityIntakeResult:
        self._validate_opportunity(opportunity)

        fingerprint = self._fingerprint(opportunity)
        opportunity_id = str(getattr(opportunity, "opportunity_id", "unknown_opportunity"))

        if fingerprint in self._records:
            existing = self._records[fingerprint]
            updated = replace(
                existing,
                duplicate_count=existing.duplicate_count + 1,
                last_seen_at=utc_now(),
                metadata={
                    **dict(existing.metadata),
                    "last_duplicate_source": source,
                    "last_duplicate_at": utc_now(),
                },
            )
            self._records[fingerprint] = updated

            return OpportunityIntakeResult(
                status="duplicate",
                fingerprint=fingerprint,
                opportunity_id=opportunity_id,
                duplicate=True,
                duplicate_count=updated.duplicate_count,
                message="Duplicate opportunity detected and merged by fingerprint.",
            )

        status = self._status_value(getattr(opportunity, "status", "new"))

        record = OpportunityRecord(
            fingerprint=fingerprint,
            opportunity=opportunity,
            status=status,
            duplicate_count=0,
            metadata={
                "source": source,
                **(metadata or {}),
            },
        )
        self._records[fingerprint] = record

        return OpportunityIntakeResult(
            status="registered",
            fingerprint=fingerprint,
            opportunity_id=opportunity_id,
            duplicate=False,
            duplicate_count=0,
            message="Opportunity registered.",
        )

    def get(self, fingerprint: str) -> Optional[OpportunityRecord]:
        return self._records.get(fingerprint)

    def get_by_opportunity_id(self, opportunity_id: str) -> Optional[OpportunityRecord]:
        for record in self._records.values():
            if str(getattr(record.opportunity, "opportunity_id", "")) == str(opportunity_id):
                return record
        return None

    def all_records(self) -> List[OpportunityRecord]:
        return list(self._records.values())

    def active_records(self) -> List[OpportunityRecord]:
        return [
            record for record in self._records.values()
            if record.status not in {"archived", "expired", "rejected"}
        ]

    def archived_records(self) -> List[OpportunityRecord]:
        return [record for record in self._records.values() if record.status == "archived"]

    def transition(
        self,
        fingerprint: str,
        to_status: str,
        reason: str = "manual_transition",
    ) -> OpportunityRecord:
        if fingerprint not in self._records:
            raise KeyError(f"Unknown opportunity fingerprint: {fingerprint}")

        record = self._records[fingerprint]
        from_status = self._status_value(record.status)
        to_status = self._status_value(to_status)

        allowed = VALID_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise ValueError(f"Invalid opportunity transition: {from_status} -> {to_status}")

        event = OpportunityLifecycleEvent(
            opportunity_id=str(getattr(record.opportunity, "opportunity_id", "unknown_opportunity")),
            fingerprint=fingerprint,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
        )

        updated = replace(
            record,
            status=to_status,
            lifecycle=tuple(list(record.lifecycle) + [event]),
            last_seen_at=utc_now(),
        )

        self._records[fingerprint] = updated
        return updated

    def remove(self, fingerprint: str) -> Optional[OpportunityRecord]:
        return self._records.pop(fingerprint, None)

    def clear(self) -> None:
        self._records.clear()

    def telemetry(self) -> OpportunityOperatingTelemetry:
        records = list(self._records.values())
        total = len(records)
        active = len(self.active_records())
        archived = len(self.archived_records())
        duplicates = sum(record.duplicate_count for record in records)
        lifecycle_events = sum(len(record.lifecycle) for record in records)

        quality_scores = []
        for record in records:
            quality = getattr(record.opportunity, "quality_score", None)
            if callable(quality):
                try:
                    quality_scores.append(float(quality()))
                except Exception:
                    pass

        average_quality = round(sum(quality_scores) / len(quality_scores), 6) if quality_scores else 0.0

        return OpportunityOperatingTelemetry(
            total_registered=total,
            active_count=active,
            archived_count=archived,
            duplicate_count=duplicates,
            average_quality=average_quality,
            lifecycle_event_count=lifecycle_events,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "read_only": self.read_only,
            "records": [record.to_dict() for record in self._records.values()],
            "telemetry": self.telemetry().to_dict(),
        }

    def _validate_opportunity(self, opportunity: Any) -> None:
        if opportunity is None:
            raise ValueError("Opportunity cannot be None.")

        if not bool(getattr(opportunity, "read_only", False)):
            raise ValueError("Opportunity must be read_only.")

        fingerprint = getattr(opportunity, "fingerprint", None)
        if not callable(fingerprint):
            raise ValueError("Opportunity must expose fingerprint().")

        to_dict = getattr(opportunity, "to_dict", None)
        if not callable(to_dict):
            raise ValueError("Opportunity must expose to_dict().")

    def _fingerprint(self, opportunity: Any) -> str:
        value = opportunity.fingerprint()
        if not value:
            raise ValueError("Opportunity fingerprint cannot be empty.")
        return str(value)

    def _status_value(self, status: Any) -> str:
        if hasattr(status, "value"):
            return str(status.value)
        return str(status).lower()


def build_oos() -> OpportunityOperatingSystem:
    return OpportunityOperatingSystem()


__all__ = [
    "OOS_VERSION",
    "VALID_TRANSITIONS",
    "OpportunityLifecycleEvent",
    "OpportunityRecord",
    "OpportunityIntakeResult",
    "OpportunityOperatingTelemetry",
    "OpportunityOperatingSystem",
    "build_oos",
]
