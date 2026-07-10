from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"
ORACLE = BASE / "oracle_intelligence"
OOS = ORACLE / "opportunity_operating_system"

MODULE_PATH = OOS / "opportunity_operating_system.py"
INIT_PATH = OOS / "__init__.py"
ORACLE_INIT_PATH = ORACLE / "__init__.py"
TEST_PATH = ROOT / "test_oos_001_opportunity_operating_system.py"

MODULE_CODE = r'''"""
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
'''

INIT_CODE = r'''from .opportunity_operating_system import (
    OOS_VERSION,
    VALID_TRANSITIONS,
    OpportunityLifecycleEvent,
    OpportunityRecord,
    OpportunityIntakeResult,
    OpportunityOperatingTelemetry,
    OpportunityOperatingSystem,
    build_oos,
)

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
'''

TEST_CODE = r'''from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.opportunity_operating_system import (
    OOS_VERSION,
    OpportunityOperatingSystem,
    build_oos,
)
from qseries_v2.oracle_intelligence.universal_market_model import UniversalMarketFactory
from qseries_v2.oracle_intelligence.universal_opportunity_model import (
    UniversalOpportunityFactory,
)


def _market():
    return UniversalMarketFactory.from_prediction_market(
        venue_id="kalshi",
        venue_name="Kalshi",
        market_id="KXBTC-YES",
        title="Will BTC close above 100k?",
        bid=0.52,
        ask=0.55,
        liquidity=30000,
    )


def _opportunity():
    return UniversalOpportunityFactory.prediction_market_scalp(
        market=_market(),
        fair_value=0.67,
        market_price=0.55,
        confidence=0.84,
        explanation="Oracle fair value is above market ask.",
        liquidity_score=0.76,
        risk_score=0.31,
    )


def test_oos_001_intake_registers_opportunity():
    oos = build_oos()
    opportunity = _opportunity()

    result = oos.intake(opportunity, source="test")

    assert result.status == "registered"
    assert result.duplicate is False
    assert result.fingerprint == opportunity.fingerprint()
    assert len(oos.all_records()) == 1

    record = oos.get(result.fingerprint)
    assert record is not None
    assert record.opportunity == opportunity
    assert record.status == "new"
    assert record.read_only is True


def test_oos_001_duplicate_detection():
    oos = build_oos()
    opportunity = _opportunity()

    first = oos.intake(opportunity, source="engine_a")
    second = oos.intake(opportunity, source="engine_b")

    assert first.status == "registered"
    assert second.status == "duplicate"
    assert second.duplicate is True
    assert second.duplicate_count == 1
    assert len(oos.all_records()) == 1

    record = oos.get(first.fingerprint)
    assert record.duplicate_count == 1
    assert record.metadata["last_duplicate_source"] == "engine_b"


def test_oos_001_lifecycle_transitions():
    oos = build_oos()
    opportunity = _opportunity()
    result = oos.intake(opportunity)

    verified = oos.transition(result.fingerprint, "verified", reason="evidence_confirmed")
    ranked = oos.transition(result.fingerprint, "ranked", reason="quality_scored")
    assigned = oos.transition(result.fingerprint, "assigned", reason="decision_layer_candidate")
    executed = oos.transition(result.fingerprint, "executed", reason="q_series_ack")
    archived = oos.transition(result.fingerprint, "archived", reason="settled_reviewed")

    assert verified.status == "verified"
    assert ranked.status == "ranked"
    assert assigned.status == "assigned"
    assert executed.status == "executed"
    assert archived.status == "archived"
    assert len(archived.lifecycle) == 5
    assert archived.lifecycle[0].from_status == "new"
    assert archived.lifecycle[-1].to_status == "archived"


def test_oos_001_invalid_transition_is_blocked():
    oos = build_oos()
    opportunity = _opportunity()
    result = oos.intake(opportunity)

    try:
        oos.transition(result.fingerprint, "executed", reason="skip_attempt")
        raise AssertionError("Invalid lifecycle transition should fail.")
    except ValueError:
        pass


def test_oos_001_lookup_remove_and_active_archived_records():
    oos = build_oos()
    opportunity = _opportunity()
    result = oos.intake(opportunity)

    by_id = oos.get_by_opportunity_id(opportunity.opportunity_id)
    assert by_id is not None
    assert by_id.fingerprint == result.fingerprint

    assert len(oos.active_records()) == 1

    oos.transition(result.fingerprint, "verified")
    oos.transition(result.fingerprint, "ranked")
    oos.transition(result.fingerprint, "assigned")
    oos.transition(result.fingerprint, "executed")
    oos.transition(result.fingerprint, "archived")

    assert len(oos.active_records()) == 0
    assert len(oos.archived_records()) == 1

    removed = oos.remove(result.fingerprint)
    assert removed is not None
    assert len(oos.all_records()) == 0


def test_oos_001_telemetry_and_serialization():
    oos = build_oos()
    opportunity = _opportunity()

    result = oos.intake(opportunity)
    oos.intake(opportunity)
    oos.transition(result.fingerprint, "verified", reason="verified_for_test")

    telemetry = oos.telemetry()
    data = oos.to_dict()

    assert telemetry.total_registered == 1
    assert telemetry.active_count == 1
    assert telemetry.duplicate_count == 1
    assert telemetry.lifecycle_event_count == 1
    assert telemetry.average_quality > 0
    assert telemetry.schema_version == OOS_VERSION
    assert telemetry.read_only is True

    assert data["schema_version"] == OOS_VERSION
    assert data["read_only"] is True
    assert len(data["records"]) == 1
    assert data["records"][0]["opportunity"]["read_only"] is True


def test_oos_001_record_immutability():
    oos = OpportunityOperatingSystem()
    result = oos.intake(_opportunity())
    record = oos.get(result.fingerprint)

    try:
        record.status = "executed"
        raise AssertionError("OpportunityRecord should be immutable.")
    except FrozenInstanceError:
        pass


def test_oos_001_rejects_non_read_only_objects():
    class BadOpportunity:
        read_only = False

        def fingerprint(self):
            return "bad"

        def to_dict(self):
            return {}

    oos = build_oos()

    try:
        oos.intake(BadOpportunity())
        raise AssertionError("Non-read-only opportunity should be rejected.")
    except ValueError:
        pass


if __name__ == "__main__":
    test_oos_001_intake_registers_opportunity()
    test_oos_001_duplicate_detection()
    test_oos_001_lifecycle_transitions()
    test_oos_001_invalid_transition_is_blocked()
    test_oos_001_lookup_remove_and_active_archived_records()
    test_oos_001_telemetry_and_serialization()
    test_oos_001_record_immutability()
    test_oos_001_rejects_non_read_only_objects()

    oos = build_oos()
    opportunity = _opportunity()
    intake = oos.intake(opportunity)
    oos.intake(opportunity)
    oos.transition(intake.fingerprint, "verified", reason="test_verified")
    telemetry = oos.telemetry()

    print("[PASS] OOS-001 Opportunity Operating System")
    print(
        {
            "schema_version": telemetry.schema_version,
            "total_registered": telemetry.total_registered,
            "active_count": telemetry.active_count,
            "duplicate_count": telemetry.duplicate_count,
            "lifecycle_event_count": telemetry.lifecycle_event_count,
            "read_only": telemetry.read_only,
        }
    )
'''

def ensure_dirs():
    OOS.mkdir(parents=True, exist_ok=True)


def update_oracle_init():
    ORACLE_INIT_PATH.touch(exist_ok=True)
    text = ORACLE_INIT_PATH.read_text(encoding="utf-8")

    line = "from .opportunity_operating_system import OpportunityOperatingSystem, build_oos"

    if line not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += line + "\n"

    ORACLE_INIT_PATH.write_text(text, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OOS-001 INSTALLER")
    print(" Opportunity Operating System")
    print("=" * 40)

    ensure_dirs()

    MODULE_PATH.write_text(MODULE_CODE, encoding="utf-8")
    print(f"[OK] Wrote {MODULE_PATH}")

    INIT_PATH.write_text(INIT_CODE, encoding="utf-8")
    print(f"[OK] Wrote {INIT_PATH}")

    TEST_PATH.write_text(TEST_CODE, encoding="utf-8")
    print(f"[OK] Wrote {TEST_PATH}")

    update_oracle_init()
    print(f"[OK] Updated {ORACLE_INIT_PATH}")

    print("\n[DONE] OOS-001 installed")
    print("\nRun:")
    print("py test_oos_001_opportunity_operating_system.py")


if __name__ == "__main__":
    main()