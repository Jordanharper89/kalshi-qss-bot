"""
OLA-043
Oracle Staged Persisted Cohort Completion Promoter

Canonical completion boundary connecting:
- OLA-042 persisted canonical cohort staging
to:
- OLA-041 post-persistence capture hook
to:
- OLA-040 exact canonical cohort capture port

Purpose:
- require completed OLA-017 cycle evidence
- identify the acquisition batch from the pending OLA-042 stage
- verify staged canonical count against OLA-017 canonical_count
- verify staged routing evidence count against PostgreSQL routing delta
- consume the OLA-042 stage exactly once
- promote the exact CanonicalObservation objects through OLA-041
- return one immutable deterministic promotion receipt

This boundary does not perform acquisition or persistence.
It does not alter scheduler kwargs or scheduler results.
It does not advance lineage itself.

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
from typing import Any, Mapping

from .oracle_persisted_cohort_staging_router import (
    OraclePersistedCohortStagingRouter,
    PersistedCanonicalCohortStage,
    PersistedCohortStagingRouterContractError,
    PersistedCohortStagingRouterInvariantError,
)
from .oracle_post_persistence_cohort_capture_hook import (
    OraclePostPersistenceCohortCaptureHook,
    PostPersistenceCohortCaptureHookContractError,
    PostPersistenceCohortCaptureHookInvariantError,
    PostPersistenceCohortCaptureHookReceipt,
)


SCHEMA_VERSION = "OLA-043"
ENGINE_ID = "OLA-043"
RECEIPT_TYPE = (
    "oracle_staged_persisted_cohort_completion_promotion_receipt"
)

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class StagedPersistedCohortCompletionPromoterContractError(ValueError):
    """Raised when OLA-043 promotion input is malformed."""


class StagedPersistedCohortCompletionPromoterInvariantError(RuntimeError):
    """Raised when permanent OLA-043 invariants are violated."""


def _require_non_empty_string(
    value: Any,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise StagedPersistedCohortCompletionPromoterContractError(
            f"{field_name} must be a string"
        )

    normalized = value.strip()

    if not normalized:
        raise StagedPersistedCohortCompletionPromoterContractError(
            f"{field_name} must not be empty"
        )

    return normalized


def _require_non_negative_int(
    value: Any,
    field_name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise StagedPersistedCohortCompletionPromoterContractError(
            f"{field_name} must be an integer"
        )

    if value < 0:
        raise StagedPersistedCohortCompletionPromoterContractError(
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
        raise StagedPersistedCohortCompletionPromoterContractError(
            "OLA-017 cycle result must expose canonical mapping evidence"
        )

    if not isinstance(payload, Mapping):
        raise StagedPersistedCohortCompletionPromoterContractError(
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
class StagedPersistedCohortCompletionPromotionReceipt:
    schema_version: str
    engine_id: str
    receipt_type: str
    upstream_schema_version: str
    upstream_engine_id: str
    cycle_status: str
    acquisition_batch_id: str
    canonical_count: int
    persistence_count: int
    stage_hash: str
    capture_hook_hash: str
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
    promotion_hash: str

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "schema version invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "engine identity invariant violated"
            )

        if self.receipt_type != RECEIPT_TYPE:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "receipt type invariant violated"
            )

        if self.upstream_schema_version != "OLA-017":
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "upstream schema identity invariant violated"
            )

        if self.upstream_engine_id != "OLA-017":
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "upstream engine identity invariant violated"
            )

        if self.cycle_status != "completed":
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "cycle completion invariant violated"
            )

        if self.canonical_count <= 0:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "canonical count must be positive"
            )

        if self.persistence_count != self.canonical_count:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "persistence equality invariant violated"
            )

        if len(self.observation_ids) != self.canonical_count:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "observation identity count invariant violated"
            )

        if len(self.source_market_ids) != self.canonical_count:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
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
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "OLA-043 read-only authority invariants violated"
            )


class OracleStagedPersistedCohortCompletionPromoter:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        staging_router: OraclePersistedCohortStagingRouter,
        capture_hook: OraclePostPersistenceCohortCaptureHook | None = None,
    ) -> None:
        if not isinstance(
            staging_router,
            OraclePersistedCohortStagingRouter,
        ):
            raise StagedPersistedCohortCompletionPromoterContractError(
                "staging_router must be an OLA-042 "
                "OraclePersistedCohortStagingRouter"
            )

        self._staging_router = staging_router
        self._capture_hook = (
            capture_hook
            if capture_hook is not None
            else OraclePostPersistenceCohortCaptureHook()
        )

        if not isinstance(
            self._capture_hook,
            OraclePostPersistenceCohortCaptureHook,
        ):
            raise StagedPersistedCohortCompletionPromoterContractError(
                "capture_hook must be an OLA-041 "
                "OraclePostPersistenceCohortCaptureHook"
            )

    @property
    def staging_router(
        self,
    ) -> OraclePersistedCohortStagingRouter:
        return self._staging_router

    @property
    def capture_hook(
        self,
    ) -> OraclePostPersistenceCohortCaptureHook:
        return self._capture_hook

    def promote_completed_cycle(
        self,
        *,
        ola_017_cycle_result: Any,
        acquisition_batch_id: str,
    ) -> StagedPersistedCohortCompletionPromotionReceipt:
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
            raise StagedPersistedCohortCompletionPromoterContractError(
                "upstream schema_version must be OLA-017"
            )

        if upstream_engine_id != "OLA-017":
            raise StagedPersistedCohortCompletionPromoterContractError(
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
            raise StagedPersistedCohortCompletionPromoterContractError(
                "only completed OLA-017 cycles can promote staged cohorts"
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
            raise StagedPersistedCohortCompletionPromoterContractError(
                "canonical_count must be positive"
            )

        if persistence_count != canonical_count:
            raise StagedPersistedCohortCompletionPromoterContractError(
                "PostgreSQL persistence count must equal canonical_count"
            )

        if cycle_payload.get("read_only") is not True:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "OLA-017 cycle result lost read-only invariant"
            )

        if cycle_payload.get("execution_allowed") is not False:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "OLA-017 cycle result gained execution capability"
            )

        batch_id = _require_non_empty_string(
            acquisition_batch_id,
            "acquisition_batch_id",
        )

        metadata = self._staging_router.peek_stage_metadata(
            acquisition_batch_id=batch_id
        )

        if metadata is None:
            raise StagedPersistedCohortCompletionPromoterContractError(
                "no pending OLA-042 stage for acquisition batch"
            )

        staged_count = metadata.get(
            "canonical_count"
        )

        if staged_count != canonical_count:
            raise StagedPersistedCohortCompletionPromoterContractError(
                "staged canonical count does not match OLA-017 canonical_count"
            )

        routing_ids = metadata.get(
            "routing_evidence_observation_ids"
        )

        if not isinstance(routing_ids, tuple):
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "OLA-042 routing evidence identity projection malformed"
            )

        if len(routing_ids) != persistence_count:
            raise StagedPersistedCohortCompletionPromoterContractError(
                "staged routing evidence count does not match persistence count"
            )

        try:
            stage = self._staging_router.consume_stage(
                acquisition_batch_id=batch_id
            )
        except PersistedCohortStagingRouterContractError as exc:
            raise StagedPersistedCohortCompletionPromoterContractError(
                f"OLA-042 staging router rejected promotion: {exc}"
            ) from exc
        except PersistedCohortStagingRouterInvariantError as exc:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                f"OLA-042 staging invariant failed: {exc}"
            ) from exc

        self._assert_stage_binding(
            stage=stage,
            batch_id=batch_id,
            canonical_count=canonical_count,
            persistence_count=persistence_count,
        )

        try:
            capture_receipt = (
                self._capture_hook.capture_completed_cycle(
                    ola_017_cycle_result=cycle_payload,
                    canonical_observations=(
                        stage.canonical_observations
                    ),
                )
            )
        except PostPersistenceCohortCaptureHookContractError as exc:
            raise StagedPersistedCohortCompletionPromoterContractError(
                f"OLA-041 capture hook rejected promoted stage: {exc}"
            ) from exc
        except PostPersistenceCohortCaptureHookInvariantError as exc:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                f"OLA-041 capture hook invariant failed: {exc}"
            ) from exc

        self._assert_capture_binding(
            stage=stage,
            capture_receipt=capture_receipt,
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "receipt_type": RECEIPT_TYPE,
            "upstream_schema_version": upstream_schema_version,
            "upstream_engine_id": upstream_engine_id,
            "cycle_status": cycle_status,
            "acquisition_batch_id": batch_id,
            "canonical_count": canonical_count,
            "persistence_count": persistence_count,
            "stage_hash": stage.stage_hash,
            "capture_hook_hash": capture_receipt.hook_hash,
            "capture_hash": capture_receipt.capture_hash,
            "observation_ids": list(stage.observation_ids),
            "source_market_ids": list(stage.source_market_ids),
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "execution_adapter_resolved": EXECUTION_ADAPTER_RESOLVED,
            "execution_adapter_invoked": EXECUTION_ADAPTER_INVOKED,
            "trade_authorization_allowed": TRADE_AUTHORIZATION_ALLOWED,
            "order_placement_allowed": ORDER_PLACEMENT_ALLOWED,
            "funds_moved": FUNDS_MOVED,
            "portfolio_mutated": PORTFOLIO_MUTATED,
        }

        receipt = (
            StagedPersistedCohortCompletionPromotionReceipt(
                schema_version=SCHEMA_VERSION,
                engine_id=ENGINE_ID,
                receipt_type=RECEIPT_TYPE,
                upstream_schema_version=upstream_schema_version,
                upstream_engine_id=upstream_engine_id,
                cycle_status=cycle_status,
                acquisition_batch_id=batch_id,
                canonical_count=canonical_count,
                persistence_count=persistence_count,
                stage_hash=stage.stage_hash,
                capture_hook_hash=capture_receipt.hook_hash,
                capture_hash=capture_receipt.capture_hash,
                observation_ids=stage.observation_ids,
                source_market_ids=stage.source_market_ids,
                read_only=READ_ONLY,
                execution_allowed=EXECUTION_ALLOWED,
                execution_adapter_resolved=(
                    EXECUTION_ADAPTER_RESOLVED
                ),
                execution_adapter_invoked=(
                    EXECUTION_ADAPTER_INVOKED
                ),
                trade_authorization_allowed=(
                    TRADE_AUTHORIZATION_ALLOWED
                ),
                order_placement_allowed=(
                    ORDER_PLACEMENT_ALLOWED
                ),
                funds_moved=FUNDS_MOVED,
                portfolio_mutated=PORTFOLIO_MUTATED,
                promotion_hash=_stable_hash(payload),
            )
        )

        receipt.assert_invariants()
        return receipt

    @staticmethod
    def _assert_stage_binding(
        *,
        stage: PersistedCanonicalCohortStage,
        batch_id: str,
        canonical_count: int,
        persistence_count: int,
    ) -> None:
        if stage.acquisition_batch_id != batch_id:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "stage acquisition batch binding invariant violated"
            )

        if stage.canonical_count != canonical_count:
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "stage canonical count binding invariant violated"
            )

        if (
            len(stage.delegated_routing_evidence)
            != persistence_count
        ):
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "stage persistence evidence binding invariant violated"
            )

    @staticmethod
    def _assert_capture_binding(
        *,
        stage: PersistedCanonicalCohortStage,
        capture_receipt: PostPersistenceCohortCaptureHookReceipt,
    ) -> None:
        if (
            capture_receipt.acquisition_batch_id
            != stage.acquisition_batch_id
        ):
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "capture batch binding invariant violated"
            )

        if (
            capture_receipt.canonical_count
            != stage.canonical_count
        ):
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "capture canonical count binding invariant violated"
            )

        if (
            capture_receipt.observation_ids
            != stage.observation_ids
        ):
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "capture observation ordering invariant violated"
            )

        if (
            capture_receipt.source_market_ids
            != stage.source_market_ids
        ):
            raise StagedPersistedCohortCompletionPromoterInvariantError(
                "capture market ordering invariant violated"
            )
