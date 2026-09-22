"""
OLA-044
Oracle Persisted Cohort Lineage Production Wiring Contract

Canonical production composition boundary for the existing live persistence
router, OLA-042 staging router, OLA-043 completion promoter, and OLA-039
persisted-cohort lineage bridge.

Purpose:
- wrap the exact production persistence router with OLA-042
- expose the OLA-042 staging router as the single router to be injected into
  both the live acquisition runtime and OLA-017
- preserve the underlying production persistence router unchanged
- promote one completed OLA-017 cycle through OLA-043
- consume the exact OLA-040 captured cohort
- form the OLA-038 persisted-cycle bundle
- advance lineage through OLA-039
- preserve the OLA-017 cycle result unchanged for OLA-021/OLA-030 projection

This contract does not alter scheduler kwargs or scheduler result shape.
It does not perform intelligence interpretation, scoring, alerting,
Q Series handoff, authorization, or execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Mapping

from .oracle_canonical_persisted_cohort_capture_port import (
    CanonicalPersistedCohortCaptureContractError,
    OracleCanonicalPersistedCohortCapturePort,
)
from .oracle_persisted_cohort_lineage_bridge import (
    OraclePersistedCohortLineageBridge,
    PersistedCohortLineageBridgeContractError,
    PersistedCohortLineageBridgeInvariantError,
    PersistedCohortLineageBridgeReceipt,
)
from .oracle_persisted_cohort_staging_router import (
    OraclePersistedCohortStagingRouter,
)
from .oracle_persisted_cycle_canonical_cohort_bundle_contract import (
    OraclePersistedCycleCanonicalCohortBundle,
    PersistedCycleCanonicalCohortBundleContractError,
    PersistedCycleCanonicalCohortBundleInvariantError,
)
from .oracle_post_persistence_cohort_capture_hook import (
    OraclePostPersistenceCohortCaptureHook,
)
from .oracle_staged_persisted_cohort_completion_promoter import (
    OracleStagedPersistedCohortCompletionPromoter,
    StagedPersistedCohortCompletionPromoterContractError,
    StagedPersistedCohortCompletionPromoterInvariantError,
    StagedPersistedCohortCompletionPromotionReceipt,
)


SCHEMA_VERSION = "OLA-044"
ENGINE_ID = "OLA-044"
RECEIPT_TYPE = (
    "oracle_persisted_cohort_lineage_production_wiring_receipt"
)

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class PersistedCohortLineageProductionWiringContractError(ValueError):
    """Raised when OLA-044 production wiring input is malformed."""


class PersistedCohortLineageProductionWiringInvariantError(RuntimeError):
    """Raised when OLA-044 permanent invariants are violated."""


def _require_utc_datetime(
    value: Any,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise PersistedCohortLineageProductionWiringContractError(
            f"{field_name} must be a datetime"
        )

    if value.tzinfo is None or value.utcoffset() is None:
        raise PersistedCohortLineageProductionWiringContractError(
            f"{field_name} must be timezone-aware"
        )

    return value.astimezone(timezone.utc)


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
        raise PersistedCohortLineageProductionWiringContractError(
            "OLA-017 cycle result must expose canonical mapping evidence"
        )

    if not isinstance(payload, Mapping):
        raise PersistedCohortLineageProductionWiringContractError(
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
class PersistedCohortLineageProductionWiringReceipt:
    schema_version: str
    engine_id: str
    receipt_type: str
    upstream_schema_version: str
    upstream_engine_id: str
    acquisition_batch_id: str
    canonical_count: int
    persistence_count: int
    cycle_completed_at: str
    stage_hash: str
    promotion_hash: str
    capture_hash: str
    bundle_hash: str
    lineage_bridge_hash: str
    transition_count: int
    lineage_market_count_after: int
    lineage_record_count_after: int
    cycle_result_preserved: bool
    scheduler_kwargs_unchanged: bool
    scheduler_results_unchanged: bool
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    wiring_hash: str

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "schema version invariant violated"
            )

        if self.engine_id != ENGINE_ID:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "engine identity invariant violated"
            )

        if self.receipt_type != RECEIPT_TYPE:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "receipt type invariant violated"
            )

        if self.upstream_schema_version != "OLA-017":
            raise PersistedCohortLineageProductionWiringInvariantError(
                "upstream schema identity invariant violated"
            )

        if self.upstream_engine_id != "OLA-017":
            raise PersistedCohortLineageProductionWiringInvariantError(
                "upstream engine identity invariant violated"
            )

        if self.canonical_count <= 0:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "canonical count must be positive"
            )

        if self.persistence_count != self.canonical_count:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "persistence equality invariant violated"
            )

        if self.cycle_result_preserved is not True:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "OLA-017 cycle result preservation invariant violated"
            )

        if self.scheduler_kwargs_unchanged is not True:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "scheduler kwargs invariant violated"
            )

        if self.scheduler_results_unchanged is not True:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "scheduler result invariant violated"
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
            raise PersistedCohortLineageProductionWiringInvariantError(
                "OLA-044 read-only authority invariants violated"
            )


class OraclePersistedCohortLineageProductionWiringContract:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        production_persistence_router: Any,
        capture_port: (
            OracleCanonicalPersistedCohortCapturePort | None
        ) = None,
        lineage_bridge: (
            OraclePersistedCohortLineageBridge | None
        ) = None,
    ) -> None:
        route_batch = getattr(
            production_persistence_router,
            "route_batch",
            None,
        )

        if not callable(route_batch):
            raise PersistedCohortLineageProductionWiringContractError(
                "production_persistence_router must expose route_batch"
            )

        self._production_persistence_router = (
            production_persistence_router
        )
        self._capture_port = (
            capture_port
            if capture_port is not None
            else OracleCanonicalPersistedCohortCapturePort()
        )

        if not isinstance(
            self._capture_port,
            OracleCanonicalPersistedCohortCapturePort,
        ):
            raise PersistedCohortLineageProductionWiringContractError(
                "capture_port must be an OLA-040 capture port"
            )

        self._staging_router = OraclePersistedCohortStagingRouter(
            persistence_router=production_persistence_router
        )
        self._capture_hook = OraclePostPersistenceCohortCaptureHook(
            capture_port=self._capture_port
        )
        self._promoter = (
            OracleStagedPersistedCohortCompletionPromoter(
                staging_router=self._staging_router,
                capture_hook=self._capture_hook,
            )
        )
        self._lineage_bridge = (
            lineage_bridge
            if lineage_bridge is not None
            else OraclePersistedCohortLineageBridge()
        )

        if not isinstance(
            self._lineage_bridge,
            OraclePersistedCohortLineageBridge,
        ):
            raise PersistedCohortLineageProductionWiringContractError(
                "lineage_bridge must be an OLA-039 lineage bridge"
            )

    @property
    def production_persistence_router(self) -> Any:
        return self._production_persistence_router

    @property
    def staged_persistence_router(
        self,
    ) -> OraclePersistedCohortStagingRouter:
        return self._staging_router

    @property
    def capture_port(
        self,
    ) -> OracleCanonicalPersistedCohortCapturePort:
        return self._capture_port

    @property
    def promoter(
        self,
    ) -> OracleStagedPersistedCohortCompletionPromoter:
        return self._promoter

    @property
    def lineage_bridge(
        self,
    ) -> OraclePersistedCohortLineageBridge:
        return self._lineage_bridge

    def complete_persisted_cycle(
        self,
        *,
        ola_017_cycle_result: Any,
        acquisition_batch_id: str,
        cycle_completed_at: datetime,
    ) -> tuple[
        Any,
        PersistedCohortLineageProductionWiringReceipt,
    ]:
        cycle_payload_before = _cycle_payload(
            ola_017_cycle_result
        )
        completed_at = _require_utc_datetime(
            cycle_completed_at,
            "cycle_completed_at",
        )

        try:
            promotion = self._promoter.promote_completed_cycle(
                ola_017_cycle_result=ola_017_cycle_result,
                acquisition_batch_id=acquisition_batch_id,
            )
        except StagedPersistedCohortCompletionPromoterContractError as exc:
            raise PersistedCohortLineageProductionWiringContractError(
                f"OLA-043 promoter rejected completed cycle: {exc}"
            ) from exc
        except StagedPersistedCohortCompletionPromoterInvariantError as exc:
            raise PersistedCohortLineageProductionWiringInvariantError(
                f"OLA-043 promoter invariant failed: {exc}"
            ) from exc

        capture = self._consume_promoted_capture(
            promotion=promotion
        )

        try:
            bundle = (
                OraclePersistedCycleCanonicalCohortBundle.create(
                    ola_017_cycle_result=ola_017_cycle_result,
                    canonical_observations=(
                        capture.canonical_observations
                    ),
                    cycle_completed_at=completed_at,
                )
            )
        except PersistedCycleCanonicalCohortBundleContractError as exc:
            raise PersistedCohortLineageProductionWiringContractError(
                f"OLA-038 bundle rejected promoted capture: {exc}"
            ) from exc
        except PersistedCycleCanonicalCohortBundleInvariantError as exc:
            raise PersistedCohortLineageProductionWiringInvariantError(
                f"OLA-038 bundle invariant failed: {exc}"
            ) from exc

        try:
            lineage_receipt = self._lineage_bridge.advance(
                bundle=bundle
            )
        except PersistedCohortLineageBridgeContractError as exc:
            raise PersistedCohortLineageProductionWiringContractError(
                f"OLA-039 lineage bridge rejected bundle: {exc}"
            ) from exc
        except PersistedCohortLineageBridgeInvariantError as exc:
            raise PersistedCohortLineageProductionWiringInvariantError(
                f"OLA-039 lineage bridge invariant failed: {exc}"
            ) from exc

        cycle_payload_after = _cycle_payload(
            ola_017_cycle_result
        )

        if cycle_payload_after != cycle_payload_before:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "OLA-017 cycle result was mutated by lineage wiring"
            )

        self._assert_cross_boundary_binding(
            promotion=promotion,
            bundle=bundle,
            lineage_receipt=lineage_receipt,
        )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "receipt_type": RECEIPT_TYPE,
            "upstream_schema_version": (
                lineage_receipt.upstream_schema_version
            ),
            "upstream_engine_id": (
                lineage_receipt.upstream_engine_id
            ),
            "acquisition_batch_id": (
                lineage_receipt.acquisition_batch_id
            ),
            "canonical_count": lineage_receipt.canonical_count,
            "persistence_count": (
                lineage_receipt.persistence_count
            ),
            "cycle_completed_at": completed_at.isoformat(),
            "stage_hash": promotion.stage_hash,
            "promotion_hash": promotion.promotion_hash,
            "capture_hash": promotion.capture_hash,
            "bundle_hash": bundle.bundle_hash,
            "lineage_bridge_hash": lineage_receipt.bridge_hash,
            "transition_count": lineage_receipt.transition_count,
            "lineage_market_count_after": (
                lineage_receipt.lineage_market_count_after
            ),
            "lineage_record_count_after": (
                lineage_receipt.lineage_record_count_after
            ),
            "cycle_result_preserved": True,
            "scheduler_kwargs_unchanged": True,
            "scheduler_results_unchanged": True,
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "execution_adapter_resolved": EXECUTION_ADAPTER_RESOLVED,
            "execution_adapter_invoked": EXECUTION_ADAPTER_INVOKED,
            "trade_authorization_allowed": TRADE_AUTHORIZATION_ALLOWED,
            "order_placement_allowed": ORDER_PLACEMENT_ALLOWED,
            "funds_moved": FUNDS_MOVED,
            "portfolio_mutated": PORTFOLIO_MUTATED,
        }

        receipt = PersistedCohortLineageProductionWiringReceipt(
            **payload,
            wiring_hash=_stable_hash(payload),
        )

        receipt.assert_invariants()

        return ola_017_cycle_result, receipt

    def _consume_promoted_capture(
        self,
        *,
        promotion: StagedPersistedCohortCompletionPromotionReceipt,
    ):
        try:
            return self._capture_port.consume(
                acquisition_batch_id=(
                    promotion.acquisition_batch_id
                )
            )
        except CanonicalPersistedCohortCaptureContractError as exc:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "OLA-043 promotion succeeded but OLA-040 capture "
                f"could not be consumed: {exc}"
            ) from exc

    @staticmethod
    def _assert_cross_boundary_binding(
        *,
        promotion: StagedPersistedCohortCompletionPromotionReceipt,
        bundle: OraclePersistedCycleCanonicalCohortBundle,
        lineage_receipt: PersistedCohortLineageBridgeReceipt,
    ) -> None:
        identities = {
            promotion.acquisition_batch_id,
            bundle.acquisition_batch_id,
            lineage_receipt.acquisition_batch_id,
        }

        if len(identities) != 1:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "acquisition batch identity diverged across wiring"
            )

        counts = {
            promotion.canonical_count,
            bundle.canonical_count,
            lineage_receipt.canonical_count,
        }

        if len(counts) != 1:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "canonical count diverged across wiring"
            )

        persistence_counts = {
            promotion.persistence_count,
            bundle.persistence_count,
            lineage_receipt.persistence_count,
        }

        if len(persistence_counts) != 1:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "persistence count diverged across wiring"
            )

        if promotion.capture_hash != bundle.bundle_hash:
            # The hashes intentionally represent different canonical records.
            # Their identity is bound through acquisition batch and ordered
            # observation IDs, not hash equality.
            pass

        if promotion.observation_ids != bundle.observation_ids:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "observation ordering diverged across wiring"
            )

        if promotion.source_market_ids != bundle.source_market_ids:
            raise PersistedCohortLineageProductionWiringInvariantError(
                "market ordering diverged across wiring"
            )
