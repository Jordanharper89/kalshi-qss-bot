"""
OLA-034
Oracle Live Market Lineage Pipeline Bridge

Canonical integration boundary connecting live canonical market observations to:
- OLA-031 exact live market-state fingerprinting
- OLA-033 per-market canonical lineage ledger

Purpose:
- accept canonical market_snapshot observations from the live acquisition path
- derive exact OLA-031 market-state identity
- append one deterministic frame into the OLA-033 lineage ledger
- return one immutable bridge receipt binding observation, fingerprint,
  lineage head, dwell, and transition identity

This bridge owns no persistence and performs no intelligence interpretation,
signal scoring, alerting, Q Series handoff, authorization, or execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Any

from .oracle_canonical_market_lineage_ledger import (
    MarketLineageLedgerContractError,
    MarketLineageLedgerInvariantError,
    OracleCanonicalMarketLineageLedger,
)
from .oracle_canonical_market_state_fingerprint_contract import (
    CanonicalMarketStateFingerprint,
    MarketStateFingerprintContractError,
    MarketStateFingerprintInvariantError,
    OracleCanonicalMarketStateFingerprintContract,
)
from .oracle_live_read_only_acquisition_runtime import (
    CanonicalObservation,
)


SCHEMA_VERSION = "OLA-034"
ENGINE_ID = "OLA-034"
BRIDGE_RECEIPT_TYPE = "oracle_live_market_lineage_pipeline_receipt"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class LiveMarketLineagePipelineContractError(ValueError):
    """Raised when OLA-034 pipeline input is malformed."""


class LiveMarketLineagePipelineInvariantError(RuntimeError):
    """Raised when permanent OLA-034 invariants are violated."""


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
class LiveMarketLineagePipelineReceipt:
    schema_version: str
    engine_id: str
    receipt_type: str
    source_id: str
    source_market_id: str
    observation_id: str
    fingerprint_id: str
    market_state_hash: str
    previous_market_state_hash: str | None
    lineage_hash: str
    previous_lineage_hash: str | None
    transition_detected: bool
    transition_id: str | None
    consecutive_frame_count: int
    state_first_observed_at: str
    state_last_observed_at: str
    state_changed_at: str | None
    dwell_seconds: str
    ledger_market_count: int
    ledger_record_count: int
    read_only: bool
    execution_allowed: bool
    execution_adapter_resolved: bool
    execution_adapter_invoked: bool
    trade_authorization_allowed: bool
    order_placement_allowed: bool
    funds_moved: bool
    portfolio_mutated: bool
    receipt_hash: str

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise LiveMarketLineagePipelineInvariantError(
                "schema version invariant violated"
            )
        if self.engine_id != ENGINE_ID:
            raise LiveMarketLineagePipelineInvariantError(
                "engine identity invariant violated"
            )
        if self.receipt_type != BRIDGE_RECEIPT_TYPE:
            raise LiveMarketLineagePipelineInvariantError(
                "receipt type invariant violated"
            )
        if self.consecutive_frame_count <= 0:
            raise LiveMarketLineagePipelineInvariantError(
                "consecutive frame count must be positive"
            )
        if self.ledger_market_count <= 0:
            raise LiveMarketLineagePipelineInvariantError(
                "ledger market count must be positive"
            )
        if self.ledger_record_count <= 0:
            raise LiveMarketLineagePipelineInvariantError(
                "ledger record count must be positive"
            )

        if self.transition_detected:
            if self.previous_market_state_hash is None:
                raise LiveMarketLineagePipelineInvariantError(
                    "transition requires previous market state hash"
                )
            if self.transition_id is None:
                raise LiveMarketLineagePipelineInvariantError(
                    "transition requires transition identity"
                )
            if self.state_changed_at is None:
                raise LiveMarketLineagePipelineInvariantError(
                    "transition requires state_changed_at"
                )
        else:
            if self.transition_id is not None:
                raise LiveMarketLineagePipelineInvariantError(
                    "non-transition cannot carry transition identity"
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
            raise LiveMarketLineagePipelineInvariantError(
                "OLA-034 read-only authority invariants violated"
            )


class OracleLiveMarketLineagePipelineBridge:
    read_only = True
    execution_allowed = False

    def __init__(
        self,
        *,
        ledger: OracleCanonicalMarketLineageLedger | None = None,
    ) -> None:
        self._fingerprint_contract = (
            OracleCanonicalMarketStateFingerprintContract()
        )
        self._ledger = (
            ledger
            if ledger is not None
            else OracleCanonicalMarketLineageLedger()
        )

        if not isinstance(
            self._ledger,
            OracleCanonicalMarketLineageLedger,
        ):
            raise LiveMarketLineagePipelineContractError(
                "ledger must be an OLA-033 "
                "OracleCanonicalMarketLineageLedger"
            )

    @property
    def ledger(self) -> OracleCanonicalMarketLineageLedger:
        return self._ledger

    def process(
        self,
        *,
        observation: CanonicalObservation,
        frame_observed_at: datetime,
    ) -> LiveMarketLineagePipelineReceipt:
        if not isinstance(observation, CanonicalObservation):
            raise LiveMarketLineagePipelineContractError(
                "observation must be a canonical live acquisition observation"
            )

        if observation.observation_type != "market_snapshot":
            raise LiveMarketLineagePipelineContractError(
                "OLA-034 accepts only market_snapshot observations"
            )

        try:
            fingerprint = self._fingerprint_contract.fingerprint(
                observation=observation
            )
        except MarketStateFingerprintContractError as exc:
            raise LiveMarketLineagePipelineContractError(
                f"OLA-031 fingerprint contract rejected observation: {exc}"
            ) from exc
        except MarketStateFingerprintInvariantError as exc:
            raise LiveMarketLineagePipelineInvariantError(
                f"OLA-031 fingerprint invariant failed: {exc}"
            ) from exc

        self._assert_fingerprint_binding(
            observation=observation,
            fingerprint=fingerprint,
        )

        try:
            ledger_receipt = self._ledger.append(
                fingerprint=fingerprint,
                frame_observed_at=frame_observed_at,
            )
        except MarketLineageLedgerContractError as exc:
            raise LiveMarketLineagePipelineContractError(
                f"OLA-033 lineage ledger rejected frame: {exc}"
            ) from exc
        except MarketLineageLedgerInvariantError as exc:
            raise LiveMarketLineagePipelineInvariantError(
                f"OLA-033 lineage ledger invariant failed: {exc}"
            ) from exc

        lineage = self._ledger.head(
            source_id=fingerprint.source_id,
            source_market_id=fingerprint.source_market_id,
        )

        if lineage is None:
            raise LiveMarketLineagePipelineInvariantError(
                "OLA-033 accepted frame but lineage head is missing"
            )

        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "receipt_type": BRIDGE_RECEIPT_TYPE,
            "source_id": lineage.source_id,
            "source_market_id": lineage.source_market_id,
            "observation_id": lineage.observation_id,
            "fingerprint_id": lineage.fingerprint_id,
            "market_state_hash": lineage.current_market_state_hash,
            "previous_market_state_hash": (
                lineage.previous_market_state_hash
            ),
            "lineage_hash": lineage.lineage_hash,
            "previous_lineage_hash": lineage.previous_lineage_hash,
            "transition_detected": lineage.transition_detected,
            "transition_id": lineage.transition_id,
            "consecutive_frame_count": lineage.consecutive_frame_count,
            "state_first_observed_at": (
                lineage.state_first_observed_at.isoformat()
            ),
            "state_last_observed_at": (
                lineage.state_last_observed_at.isoformat()
            ),
            "state_changed_at": (
                None
                if lineage.state_changed_at is None
                else lineage.state_changed_at.isoformat()
            ),
            "dwell_seconds": lineage.dwell_seconds,
            "ledger_market_count": ledger_receipt.ledger_market_count,
            "ledger_record_count": ledger_receipt.ledger_record_count,
            "read_only": READ_ONLY,
            "execution_allowed": EXECUTION_ALLOWED,
            "execution_adapter_resolved": EXECUTION_ADAPTER_RESOLVED,
            "execution_adapter_invoked": EXECUTION_ADAPTER_INVOKED,
            "trade_authorization_allowed": TRADE_AUTHORIZATION_ALLOWED,
            "order_placement_allowed": ORDER_PLACEMENT_ALLOWED,
            "funds_moved": FUNDS_MOVED,
            "portfolio_mutated": PORTFOLIO_MUTATED,
        }

        receipt = LiveMarketLineagePipelineReceipt(
            **payload,
            receipt_hash=_stable_hash(payload),
        )
        receipt.assert_invariants()
        return receipt

    @staticmethod
    def _assert_fingerprint_binding(
        *,
        observation: CanonicalObservation,
        fingerprint: CanonicalMarketStateFingerprint,
    ) -> None:
        if fingerprint.observation_id != observation.observation_id:
            raise LiveMarketLineagePipelineInvariantError(
                "fingerprint observation identity binding violated"
            )
        if fingerprint.source_id != observation.source_id:
            raise LiveMarketLineagePipelineInvariantError(
                "fingerprint source identity binding violated"
            )
