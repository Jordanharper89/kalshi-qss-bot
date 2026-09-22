"""
OLA-041
Oracle Post-Persistence Cohort Capture Hook

Canonical production-wiring hook between successful OLA-017 persistence
reconciliation and the OLA-040 exact canonical cohort capture port.

Purpose:
- accept one completed OLA-017 cycle result
- require canonical_count > 0
- require PostgreSQL routing delta == canonical_count
- require the exact canonical observation cohort
- require one acquisition_batch_id across the cohort
- capture the exact CanonicalObservation objects through OLA-040
- return one immutable deterministic hook receipt

The hook does not alter OLA-017 result projection.
It does not alter OLA-021 scheduler canonicalization.
It performs no lineage advancement itself.

No intelligence interpretation.
No signal scoring.
No alerts.
No Q Series handoff.
No execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from .oracle_canonical_persisted_cohort_capture_port import (
    CanonicalPersistedCohortCapture,
    CanonicalPersistedCohortCaptureContractError,
    CanonicalPersistedCohortCaptureInvariantError,
    OracleCanonicalPersistedCohortCapturePort,
    canonical_persisted_cohort_capture_port,
)
from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
)


SCHEMA_VERSION = "OLA-041"
ENGINE_ID = "OLA-041"
RECEIPT_TYPE = "oracle_post_persistence_cohort_capture_hook_receipt"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class PostPersistenceCohortCaptureHookContractError(ValueError):
    """Raised when OLA-041 hook input is malformed."""


class PostPersistenceCohortCaptureHookInvariantError(RuntimeError):
    """Raised when permanent OLA-041 invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PostPersistenceCohortCaptureHookContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise PostPersistenceCohortCaptureHookContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PostPersistenceCohortCaptureHookContractError(
            f"{field_name} must be an integer"
        )

    if value < 0:
        raise PostPersistenceCohortCaptureHookContractError(
            f"{field_name} must not be negative"
        )

    return value


def _cycle_payload(
    cycle_result: Any,
) -> dict[str, Any]:
    if hasattr(
        cycle_result,
        "to_canonical_dict",
    ):
        payload = cycle_result.to_canonical_dict()
    elif isinstance(cycle_result, Mapping):
        payload = cycle_result
    else:
        raise PostPersistenceCohortCaptureHookContractError(
            "OLA-017 cycle result must expose canonical mapping evidence"
        )

    if not isinstance(payload, Mapping):
        raise PostPersistenceCohortCaptureHookContractError(
            "OLA-017 canonical cycle evidence must be a mapping"
        )

    return dict(payload)


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class PostPersistenceCohortCaptureHookReceipt:
    schema_version: str
    engine_id: str
    receipt_type: str
    upstream_schema_version: str
    upstream_engine_id: str
    cycle_status: str
    acquisition_batch_id: str
    canonical_count: int
    persistence_count: int
    capture_hash: str
    observation_ids: tuple[str, ...]
    source_market_ids: tuple[str, ...]
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    hook_hash: str

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise PostPersistenceCohortCaptureHookInvariantError(
                "schema version invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise PostPersistenceCohortCaptureHookInvariantError(
                "engine identity invariant violated"
            )

        if self.receipt_type != RECEIPT_TYPE:
            raise PostPersistenceCohortCaptureHookInvariantError(
                "receipt type invariant violated"
            )

        if self.upstream_schema_version != "OLA-017":
            raise PostPersistenceCohortCaptureHookInvariantError(
                "upstream schema identity invariant violated"
            )

        if self.upstream_engine_id != "OLA-017":
            raise PostPersistenceCohortCaptureHookInvariantError(
                "upstream engine identity invariant violated"
            )

        if self.cycle_status != "completed":
            raise PostPersistenceCohortCaptureHookInvariantError(
                "cycle completion invariant violated"
            )

        if self.canonical_count <= 0:
            raise PostPersistenceCohortCaptureHookInvariantError(
                "canonical count must be positive"
            )

        if self.persistence_count != self.canonical_count:
            raise PostPersistenceCohortCaptureHookInvariantError(
                "persistence equality invariant violated"
            )

        if len(self.observation_ids) != self.canonical_count:
            raise PostPersistenceCohortCaptureHookInvariantError(
                "observation identity count invariant violated"
            )

        if len(self.source_market_ids) != self.canonical_count:
            raise PostPersistenceCohortCaptureHookInvariantError(
                "market identity count invariant violated"
            )

        authority = (
            self.read_only,
            self.execution_allowed,
            self.execution_adapter_resolved,
            self.execution_adapter_invoked,
            self.trade_authorization_allowed,
            self.order_placement_allowed,
            self.funds_moved,
            self.portfolio_mutated,
        )

        if authority != (
            True,
            False,
            False,
            False,
            False,
            False,
            False,
            False,
        ):
            raise PostPersistenceCohortCaptureHookInvariantError(
                "OLA-041 read-only authority invariants violated"
            )


class OraclePostPersistenceCohortCaptureHook:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        capture_port: (
            OracleCanonicalPersistedCohortCapturePort | None
        ) = None,
    ) -> None:
        self._capture_port = (
            capture_port
            if capture_port is not None
            else canonical_persisted_cohort_capture_port()
        )

        if not isinstance(
            self._capture_port,
            OracleCanonicalPersistedCohortCapturePort,
        ):
            raise PostPersistenceCohortCaptureHookContractError(
                "capture_port must be an OLA-040 "
                "OracleCanonicalPersistedCohortCapturePort"
            )

    @property
    def capture_port(
        self,
    ) -> OracleCanonicalPersistedCohortCapturePort:
        return self._capture_port

    def capture_completed_cycle(
        self,
        *,
        ola_017_cycle_result: Any,
        canonical_observations: Sequence[CanonicalObservation],
    ) -> PostPersistenceCohortCaptureHookReceipt:
        cycle_payload = _cycle_payload(
            ola_017_cycle_result
        )

        upstream_schema_version = _require_non_empty_string(
            cycle_payload.get("schema_version"),
            "ola_017_cycle_result.schema_version",
        )
        upstream_engine_id = _require_non_empty_string(
            cycle_payload.get("engine_id"),
            "ola_017_cycle_result.engine_id",
        )

        if upstream_schema_version != "OLA-017":
            raise PostPersistenceCohortCaptureHookContractError(
                "upstream schema_version must be OLA-017"
            )

        if upstream_engine_id != "OLA-017":
            raise PostPersistenceCohortCaptureHookContractError(
                "upstream engine_id must be OLA-017"
            )

        cycle_status = _require_non_empty_string(
            cycle_payload.get(
                "cycle_status",
                cycle_payload.get("status"),
            ),
            "ola_017_cycle_result.cycle_status",
        )

        if cycle_status != "completed":
            raise PostPersistenceCohortCaptureHookContractError(
                "only completed OLA-017 cycles can be captured"
            )

        canonical_count = _require_non_negative_int(
            cycle_payload.get("canonical_count"),
            "ola_017_cycle_result.canonical_count",
        )

        persistence_count = _require_non_negative_int(
            cycle_payload.get(
                "postgresql_routing_record_delta",
                cycle_payload.get(
                    "postgresql_persistence_count"
                ),
            ),
            "ola_017_cycle_result.postgresql_routing_record_delta",
        )

        if canonical_count <= 0:
            raise PostPersistenceCohortCaptureHookContractError(
                "canonical_count must be positive"
            )

        if persistence_count != canonical_count:
            raise PostPersistenceCohortCaptureHookContractError(
                "PostgreSQL persistence count must equal canonical_count"
            )

        if cycle_payload.get("read_only") is not True:
            raise PostPersistenceCohortCaptureHookInvariantError(
                "OLA-017 cycle result lost read-only invariant"
            )

        if cycle_payload.get("execution_allowed") is not False:
            raise PostPersistenceCohortCaptureHookInvariantError(
                "OLA-017 cycle result gained execution capability"
            )

        observations = tuple(canonical_observations)

        if len(observations) != canonical_count:
            raise PostPersistenceCohortCaptureHookContractError(
                "exact canonical cohort count must equal canonical_count"
            )

        try:
            capture = self._capture_port.capture(
                canonical_observations=observations
            )
        except CanonicalPersistedCohortCaptureContractError as exc:
            raise PostPersistenceCohortCaptureHookContractError(
                f"OLA-040 capture port rejected cohort: {exc}"
            ) from exc
        except CanonicalPersistedCohortCaptureInvariantError as exc:
            raise PostPersistenceCohortCaptureHookInvariantError(
                f"OLA-040 capture invariant failed: {exc}"
            ) from exc

        self._assert_capture_binding(
            capture=capture,
            observations=observations,
            canonical_count=canonical_count,
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "receipt_type": RECEIPT_TYPE,
            "upstream_schema_version": upstream_schema_version,
            "upstream_engine_id": upstream_engine_id,
            "cycle_status": cycle_status,
            "acquisition_batch_id": capture.acquisition_batch_id,
            "canonical_count": canonical_count,
            "persistence_count": persistence_count,
            "capture_hash": capture.capture_hash,
            "observation_ids": list(capture.observation_ids),
            "source_market_ids": list(capture.source_market_ids),
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "execution_adapter_resolved": EXECUTION_ADAPTER_RESOLVED,
            "execution_adapter_invoked": EXECUTION_ADAPTER_INVOKED,
            "trade_authorization_allowed": TRADE_AUTHORIZATION_ALLOWED,
            "order_placement_allowed": ORDER_PLACEMENT_ALLOWED,
            "funds_moved": FUNDS_MOVED,
            "portfolio_mutated": PORTFOLIO_MUTATED,
        }

        receipt = PostPersistenceCohortCaptureHookReceipt(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            receipt_type=RECEIPT_TYPE,
            upstream_schema_version=upstream_schema_version,
            upstream_engine_id=upstream_engine_id,
            cycle_status=cycle_status,
            acquisition_batch_id=capture.acquisition_batch_id,
            canonical_count=canonical_count,
            persistence_count=persistence_count,
            capture_hash=capture.capture_hash,
            observation_ids=capture.observation_ids,
            source_market_ids=capture.source_market_ids,
            read_only=READ_ONLY,
            execution_allowed=EXECUTION_ALLOWED,
            execution_adapter_resolved=EXECUTION_ADAPTER_RESOLVED,
            execution_adapter_invoked=EXECUTION_ADAPTER_INVOKED,
            trade_authorization_allowed=TRADE_AUTHORIZATION_ALLOWED,
            order_placement_allowed=ORDER_PLACEMENT_ALLOWED,
            funds_moved=FUNDS_MOVED,
            portfolio_mutated=PORTFOLIO_MUTATED,
            hook_hash=_stable_hash(payload),
        )

        receipt.assert_invariants()
        return receipt

    @staticmethod
    def _assert_capture_binding(
        *,
        capture: CanonicalPersistedCohortCapture,
        observations: tuple[CanonicalObservation, ...],
        canonical_count: int,
    ) -> None:
        if capture.canonical_count != canonical_count:
            raise PostPersistenceCohortCaptureHookInvariantError(
                "capture count binding invariant violated"
            )

        if capture.canonical_observations != observations:
            raise PostPersistenceCohortCaptureHookInvariantError(
                "exact canonical cohort binding invariant violated"
            )

        if not all(
            captured is original
            for captured, original in zip(
                capture.canonical_observations,
                observations,
            )
        ):
            raise PostPersistenceCohortCaptureHookInvariantError(
                "canonical observation object identity was not preserved"
            )
