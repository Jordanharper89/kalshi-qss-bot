"""
OLA-035
Oracle Atomic Market Lineage Batch Router

Atomic cohort boundary above OLA-034.

Purpose:
- accept one ordered canonical market_snapshot cohort
- preflight the entire cohort before mutating live lineage state
- reject duplicate observation identities within the batch
- reject duplicate source + market identities within the same cohort
- derive canonical market identity through OLA-031 rather than decoding
  CanonicalObservation payload storage shape
- validate every frame against an isolated clone of current lineage state
- commit the entire cohort only after full preflight succeeds
- preserve deterministic ordered receipts and per-market lineage continuity

This boundary owns no persistence, intelligence interpretation, scoring,
alerting, Q Series handoff, authorization, or execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .oracle_canonical_market_state_fingerprint_contract import (
    MarketStateFingerprintContractError,
    MarketStateFingerprintInvariantError,
    OracleCanonicalMarketStateFingerprintContract,
)
from .oracle_live_market_lineage_pipeline_bridge import (
    LiveMarketLineagePipelineContractError,
    LiveMarketLineagePipelineInvariantError,
    LiveMarketLineagePipelineReceipt,
    OracleLiveMarketLineagePipelineBridge,
)
from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
)


SCHEMA_VERSION = "OLA-035"
ENGINE_ID = "OLA-035"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class AtomicMarketLineageBatchContractError(ValueError):
    """Raised when OLA-035 batch input is malformed."""


class AtomicMarketLineageBatchInvariantError(RuntimeError):
    """Raised when permanent OLA-035 invariants are violated."""


@dataclass(frozen=True, slots=True)
class AtomicMarketLineageBatchFrame:
    observation: CanonicalObservation
    frame_observed_at: datetime


@dataclass(frozen=True, slots=True)
class AtomicMarketLineageBatchReceipt:
    schema_version: str
    engine_id: str
    status: str
    batch_frame_count: int
    batch_market_count: int
    ledger_market_count_before: int
    ledger_record_count_before: int
    ledger_market_count_after: int
    ledger_record_count_after: int
    transition_count: int
    receipts: tuple[LiveMarketLineagePipelineReceipt, ...]
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise AtomicMarketLineageBatchInvariantError(
                "schema version invariant violated"
            )
        if self.engine_id != ENGINE_ID:
            raise AtomicMarketLineageBatchInvariantError(
                "engine identity invariant violated"
            )
        if self.status != "committed":
            raise AtomicMarketLineageBatchInvariantError(
                "successful batch receipt must be committed"
            )
        if self.batch_frame_count <= 0:
            raise AtomicMarketLineageBatchInvariantError(
                "batch frame count must be positive"
            )
        if self.batch_market_count <= 0:
            raise AtomicMarketLineageBatchInvariantError(
                "batch market count must be positive"
            )
        if len(self.receipts) != self.batch_frame_count:
            raise AtomicMarketLineageBatchInvariantError(
                "receipt count must equal batch frame count"
            )
        if (
            self.ledger_record_count_after
            - self.ledger_record_count_before
            != self.batch_frame_count
        ):
            raise AtomicMarketLineageBatchInvariantError(
                "committed record delta must equal batch frame count"
            )
        if self.transition_count != sum(
            1
            for receipt in self.receipts
            if receipt.transition_detected
        ):
            raise AtomicMarketLineageBatchInvariantError(
                "transition count invariant violated"
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
            raise AtomicMarketLineageBatchInvariantError(
                "OLA-035 read-only authority invariants violated"
            )


class OracleAtomicMarketLineageBatchRouter:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        bridge: OracleLiveMarketLineagePipelineBridge | None = None,
    ) -> None:
        self._bridge = (
            bridge
            if bridge is not None
            else OracleLiveMarketLineagePipelineBridge()
        )
        self._fingerprint_contract = (
            OracleCanonicalMarketStateFingerprintContract()
        )

        if not isinstance(
            self._bridge,
            OracleLiveMarketLineagePipelineBridge,
        ):
            raise AtomicMarketLineageBatchContractError(
                "bridge must be an OLA-034 "
                "OracleLiveMarketLineagePipelineBridge"
            )

    @property
    def bridge(self) -> OracleLiveMarketLineagePipelineBridge:
        return self._bridge

    def route(
        self,
        *,
        frames: Iterable[AtomicMarketLineageBatchFrame],
    ) -> AtomicMarketLineageBatchReceipt:
        normalized_frames = tuple(frames)

        if not normalized_frames:
            raise AtomicMarketLineageBatchContractError(
                "batch must contain at least one frame"
            )

        observation_ids: set[str] = set()
        market_keys: set[tuple[str, str]] = set()

        for frame in normalized_frames:
            if not isinstance(
                frame,
                AtomicMarketLineageBatchFrame,
            ):
                raise AtomicMarketLineageBatchContractError(
                    "batch frames must be "
                    "AtomicMarketLineageBatchFrame records"
                )

            observation = frame.observation

            if not isinstance(observation, CanonicalObservation):
                raise AtomicMarketLineageBatchContractError(
                    "batch observation must be canonical"
                )
            if observation.observation_type != "market_snapshot":
                raise AtomicMarketLineageBatchContractError(
                    "batch accepts only market_snapshot observations"
                )

            observation_id = observation.observation_id

            if observation_id in observation_ids:
                raise AtomicMarketLineageBatchContractError(
                    "duplicate observation_id within batch"
                )

            try:
                fingerprint = self._fingerprint_contract.fingerprint(
                    observation=observation
                )
            except MarketStateFingerprintContractError as exc:
                raise AtomicMarketLineageBatchContractError(
                    "OLA-031 fingerprint contract rejected "
                    f"batch observation: {exc}"
                ) from exc
            except MarketStateFingerprintInvariantError as exc:
                raise AtomicMarketLineageBatchInvariantError(
                    "OLA-031 fingerprint invariant failed during "
                    f"batch preflight: {exc}"
                ) from exc

            market_key = (
                fingerprint.source_id,
                fingerprint.source_market_id,
            )

            if market_key in market_keys:
                raise AtomicMarketLineageBatchContractError(
                    "duplicate source + market identity within batch"
                )

            observation_ids.add(observation_id)
            market_keys.add(market_key)

        before_market_count = self._bridge.ledger.market_count
        before_record_count = self._bridge.ledger.record_count

        try:
            preflight_bridge = deepcopy(self._bridge)
        except Exception as exc:
            raise AtomicMarketLineageBatchInvariantError(
                f"unable to clone live lineage state for preflight: {exc}"
            ) from exc

        try:
            for frame in normalized_frames:
                preflight_bridge.process(
                    observation=frame.observation,
                    frame_observed_at=frame.frame_observed_at,
                )
        except LiveMarketLineagePipelineContractError as exc:
            raise AtomicMarketLineageBatchContractError(
                f"batch preflight rejected cohort: {exc}"
            ) from exc
        except LiveMarketLineagePipelineInvariantError as exc:
            raise AtomicMarketLineageBatchInvariantError(
                f"batch preflight invariant failed: {exc}"
            ) from exc

        if self._bridge.ledger.market_count != before_market_count:
            raise AtomicMarketLineageBatchInvariantError(
                "preflight mutated live ledger market count"
            )
        if self._bridge.ledger.record_count != before_record_count:
            raise AtomicMarketLineageBatchInvariantError(
                "preflight mutated live ledger record count"
            )

        receipts: list[LiveMarketLineagePipelineReceipt] = []

        for frame in normalized_frames:
            try:
                receipts.append(
                    self._bridge.process(
                        observation=frame.observation,
                        frame_observed_at=frame.frame_observed_at,
                    )
                )
            except LiveMarketLineagePipelineContractError as exc:
                raise AtomicMarketLineageBatchInvariantError(
                    "commit diverged from successful preflight: "
                    f"{exc}"
                ) from exc
            except LiveMarketLineagePipelineInvariantError as exc:
                raise AtomicMarketLineageBatchInvariantError(
                    "commit invariant diverged from preflight: "
                    f"{exc}"
                ) from exc

        receipt = AtomicMarketLineageBatchReceipt(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            status="committed",
            batch_frame_count=len(normalized_frames),
            batch_market_count=len(market_keys),
            ledger_market_count_before=before_market_count,
            ledger_record_count_before=before_record_count,
            ledger_market_count_after=self._bridge.ledger.market_count,
            ledger_record_count_after=self._bridge.ledger.record_count,
            transition_count=sum(
                1
                for item in receipts
                if item.transition_detected
            ),
            receipts=tuple(receipts),
            read_only=READ_ONLY,
            execution_allowed=EXECUTION_ALLOWED,
            execution_adapter_resolved=EXECUTION_ADAPTER_RESOLVED,
            execution_adapter_invoked=EXECUTION_ADAPTER_INVOKED,
            trade_authorization_allowed=TRADE_AUTHORIZATION_ALLOWED,
            order_placement_allowed=ORDER_PLACEMENT_ALLOWED,
            funds_moved=FUNDS_MOVED,
            portfolio_mutated=PORTFOLIO_MUTATED,
        )

        receipt.assert_invariants()
        return receipt
