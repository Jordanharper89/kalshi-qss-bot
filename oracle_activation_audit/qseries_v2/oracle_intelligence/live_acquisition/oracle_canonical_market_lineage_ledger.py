"""
OLA-033
Oracle Canonical Market Lineage Ledger

Deterministic per-market lineage state boundary above OLA-031 and OLA-032.

Owns:
- current lineage head per exact source + market identity
- independent lineage continuity across interleaved markets
- one immutable OLA-032 lineage record per accepted fingerprint frame
- deterministic replay from ordered fingerprint frames
- fail-closed duplicate observation identity
- fail-closed per-market clock regression
- dependency error translation at the OLA-033 contract boundary

Does not own persistence, intelligence interpretation, scoring, alerts,
Q Series handoff, authorization, or execution.

Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Iterable, Mapping

from .oracle_canonical_dwell_change_lineage_contract import (
    CanonicalMarketStateDwellChangeLineage,
    DwellChangeLineageContractError,
    DwellChangeLineageInvariantError,
    OracleCanonicalDwellChangeLineageContract,
)
from .oracle_canonical_market_state_fingerprint_contract import (
    CanonicalMarketStateFingerprint,
)


SCHEMA_VERSION = "OLA-033"
ENGINE_ID = "OLA-033"

READ_ONLY = True
EXECUTION_ALLOWED = False
EXECUTION_ADAPTER_RESOLVED = False
EXECUTION_ADAPTER_INVOKED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False


class MarketLineageLedgerContractError(ValueError):
    """Raised when OLA-033 ledger input is malformed."""


class MarketLineageLedgerInvariantError(RuntimeError):
    """Raised when OLA-033 permanent invariants are violated."""


@dataclass(frozen=True, slots=True)
class MarketLineageLedgerReceipt:
    schema_version: str
    engine_id: str
    source_id: str
    source_market_id: str
    observation_id: str
    previous_lineage_hash: str | None
    current_lineage_hash: str
    current_market_state_hash: str
    transition_detected: bool
    consecutive_frame_count: int
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

    def assert_invariants(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise MarketLineageLedgerInvariantError(
                "schema version invariant violated"
            )
        if self.engine_id != ENGINE_ID:
            raise MarketLineageLedgerInvariantError(
                "engine identity invariant violated"
            )
        if self.ledger_market_count <= 0:
            raise MarketLineageLedgerInvariantError(
                "ledger market count must be positive"
            )
        if self.ledger_record_count <= 0:
            raise MarketLineageLedgerInvariantError(
                "ledger record count must be positive"
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
            raise MarketLineageLedgerInvariantError(
                "OLA-033 read-only authority invariants violated"
            )


@dataclass(frozen=True, slots=True)
class MarketLineageReplayFrame:
    fingerprint: CanonicalMarketStateFingerprint
    frame_observed_at: datetime


class OracleCanonicalMarketLineageLedger:
    read_only = True
    execution_allowed = False

    def __init__(self) -> None:
        self._lineage_contract = (
            OracleCanonicalDwellChangeLineageContract()
        )
        self._heads: dict[
            tuple[str, str],
            CanonicalMarketStateDwellChangeLineage,
        ] = {}
        self._records: list[
            CanonicalMarketStateDwellChangeLineage
        ] = []
        self._seen_observation_ids: set[str] = set()

    @staticmethod
    def _market_key(
        fingerprint: CanonicalMarketStateFingerprint,
    ) -> tuple[str, str]:
        if not isinstance(
            fingerprint,
            CanonicalMarketStateFingerprint,
        ):
            raise MarketLineageLedgerContractError(
                "fingerprint must be an OLA-031 "
                "CanonicalMarketStateFingerprint"
            )

        fingerprint.assert_invariants()

        return (
            fingerprint.source_id,
            fingerprint.source_market_id,
        )

    def append(
        self,
        *,
        fingerprint: CanonicalMarketStateFingerprint,
        frame_observed_at: datetime,
    ) -> MarketLineageLedgerReceipt:
        key = self._market_key(fingerprint)

        if fingerprint.observation_id in self._seen_observation_ids:
            raise MarketLineageLedgerContractError(
                "duplicate observation_id rejected"
            )

        previous = self._heads.get(key)

        try:
            lineage = self._lineage_contract.observe(
                current_fingerprint=fingerprint,
                current_frame_observed_at=frame_observed_at,
                previous_lineage=previous,
            )
        except DwellChangeLineageContractError as exc:
            raise MarketLineageLedgerContractError(
                f"OLA-032 lineage contract rejected append: {exc}"
            ) from exc
        except DwellChangeLineageInvariantError as exc:
            raise MarketLineageLedgerInvariantError(
                f"OLA-032 lineage invariant failed: {exc}"
            ) from exc

        lineage.assert_invariants()

        if previous is None:
            if lineage.previous_lineage_hash is not None:
                raise MarketLineageLedgerInvariantError(
                    "new market lineage cannot reference prior head"
                )
        else:
            if lineage.previous_lineage_hash != previous.lineage_hash:
                raise MarketLineageLedgerInvariantError(
                    "lineage head continuity invariant violated"
                )

        self._heads[key] = lineage
        self._records.append(lineage)
        self._seen_observation_ids.add(fingerprint.observation_id)

        receipt = MarketLineageLedgerReceipt(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            source_id=lineage.source_id,
            source_market_id=lineage.source_market_id,
            observation_id=lineage.observation_id,
            previous_lineage_hash=lineage.previous_lineage_hash,
            current_lineage_hash=lineage.lineage_hash,
            current_market_state_hash=(
                lineage.current_market_state_hash
            ),
            transition_detected=lineage.transition_detected,
            consecutive_frame_count=(
                lineage.consecutive_frame_count
            ),
            dwell_seconds=lineage.dwell_seconds,
            ledger_market_count=len(self._heads),
            ledger_record_count=len(self._records),
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
        )

        receipt.assert_invariants()
        return receipt

    def head(
        self,
        *,
        source_id: str,
        source_market_id: str,
    ) -> CanonicalMarketStateDwellChangeLineage | None:
        return self._heads.get(
            (
                source_id,
                source_market_id,
            )
        )

    def heads(
        self,
    ) -> Mapping[
        tuple[str, str],
        CanonicalMarketStateDwellChangeLineage,
    ]:
        return MappingProxyType(dict(self._heads))

    def records(
        self,
    ) -> tuple[
        CanonicalMarketStateDwellChangeLineage,
        ...,
    ]:
        return tuple(self._records)

    @property
    def market_count(self) -> int:
        return len(self._heads)

    @property
    def record_count(self) -> int:
        return len(self._records)

    @classmethod
    def replay(
        cls,
        frames: Iterable[MarketLineageReplayFrame],
    ) -> "OracleCanonicalMarketLineageLedger":
        ledger = cls()

        for frame in frames:
            if not isinstance(frame, MarketLineageReplayFrame):
                raise MarketLineageLedgerContractError(
                    "replay frames must be "
                    "MarketLineageReplayFrame records"
                )

            ledger.append(
                fingerprint=frame.fingerprint,
                frame_observed_at=frame.frame_observed_at,
            )

        return ledger
