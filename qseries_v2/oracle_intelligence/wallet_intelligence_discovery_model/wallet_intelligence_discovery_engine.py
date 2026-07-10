"""
WDM-003 Wallet Intelligence Discovery Engine

Read-only Oracle discovery engine for wallet intelligence opportunities.

Consumes WDM-002 WalletActivitySnapshot records and emits immutable
UniversalOpportunity-shaped wallet intelligence opportunities.

No signing, fund movement, swaps, trading, routing, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .wallet_intelligence_discovery_contract import (
    SCHEMA_VERSION as CONTRACT_SCHEMA_VERSION,
    WalletIntelligenceDiscoveryCapability,
    WalletIntelligenceDiscoveryEngineContract,
    WalletIntelligenceDiscoveryHealth,
    WalletIntelligenceDiscoveryRequest,
    WalletIntelligenceDiscoveryResult,
    WalletIntelligenceDiscoveryTelemetry,
    WalletIntelligenceFamily,
)
from .wallet_intelligence_source_adapter import (
    WalletActivitySnapshot,
    WalletIntelligenceSourceAdapter,
)


SCHEMA_VERSION = "WDM-003"
ENGINE_ID = "oracle.discovery.wallet_intelligence"
ENGINE_NAME = "Wallet Intelligence Discovery Engine"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return "{" + ",".join(
            f"{str(k)}:{_stable_text(v)}"
            for k, v in sorted(value.items(), key=lambda x: str(x[0]))
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_stable_text(v) for v in value) + "]"
    return repr(value)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = sha256(_stable_text(payload).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}.{digest}"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class WalletIntelligenceOpportunity:
    opportunity_id: str
    schema_version: str
    wallet: str
    chain: str
    symbol: str
    opportunity_type: str
    source_engine_id: str
    signal_type: str
    signal_score: float
    confidence: float
    usd_value: float
    wallet_score: float
    universal_market: Mapping[str, Any]
    status: str
    explanation: Mapping[str, Any]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "schema_version": self.schema_version,
            "wallet": self.wallet,
            "chain": self.chain,
            "symbol": self.symbol,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "signal_type": self.signal_type,
            "signal_score": self.signal_score,
            "confidence": self.confidence,
            "usd_value": self.usd_value,
            "wallet_score": self.wallet_score,
            "universal_market": dict(self.universal_market),
            "status": self.status,
            "explanation": dict(self.explanation),
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class WalletIntelligenceDiscoveryEngine(WalletIntelligenceDiscoveryEngineContract):
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    engine_name = ENGINE_NAME
    read_only = True

    def __init__(
        self,
        source_snapshots: Optional[Sequence[WalletActivitySnapshot]] = None,
        min_wallet_score: float = 0.70,
        min_usd_value: float = 1000.0,
        min_signal_score: float = 0.55,
    ) -> None:
        self.source_snapshots = tuple(source_snapshots or ())
        self.min_wallet_score = float(min_wallet_score)
        self.min_usd_value = float(min_usd_value)
        self.min_signal_score = float(min_signal_score)

    def capabilities(self) -> WalletIntelligenceDiscoveryCapability:
        return WalletIntelligenceDiscoveryCapability(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=WalletIntelligenceFamily.SMART_MONEY,
            source_name="wallet_activity_snapshot",
            supports_replay=True,
            deterministic=True,
            telemetry=True,
            read_only=True,
            metadata={
                "engine_schema_version": self.schema_version,
                "engine_name": self.engine_name,
                "produces": "UniversalOpportunity-shaped wallet intelligence opportunities",
                "execution": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
            },
        )

    def health(self) -> WalletIntelligenceDiscoveryHealth:
        return WalletIntelligenceDiscoveryHealth(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={
                "engine_schema_version": self.schema_version,
                "read_only": True,
                "execution": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
            },
        )

    def discover(
        self,
        request: WalletIntelligenceDiscoveryRequest | None = None,
    ) -> WalletIntelligenceDiscoveryResult:
        started_at = _utc_now_iso()
        snapshots = self._resolve_snapshots(request)

        opportunities = []
        rejected = 0

        for snapshot in snapshots:
            opportunity = self._build_opportunity(snapshot)
            if opportunity is None:
                rejected += 1
                continue
            opportunities.append(opportunity)

        opportunities = tuple(
            sorted(
                opportunities,
                key=lambda o: (-o.signal_score, -o.confidence, o.chain, o.wallet, o.symbol, o.opportunity_id),
            )
        )

        request_id = request.request_id if request is not None else "wallet.intelligence.discovery.default"
        wallets_seen = len({s.wallet for s in snapshots})

        telemetry = WalletIntelligenceDiscoveryTelemetry(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=len(snapshots),
            wallets_seen=wallets_seen,
            opportunities_emitted=len(opportunities),
            rejected_records=rejected,
            metadata={
                "engine_schema_version": self.schema_version,
                "min_wallet_score": self.min_wallet_score,
                "min_usd_value": self.min_usd_value,
                "min_signal_score": self.min_signal_score,
                "deterministic_sort": True,
                "read_only": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
            },
            read_only=True,
        )

        return WalletIntelligenceDiscoveryResult(
            schema_version=CONTRACT_SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request_id,
            status="passed" if opportunities else "empty",
            opportunities=opportunities,
            telemetry=telemetry,
            health=self.health(),
            read_only=True,
        )

    def _resolve_snapshots(
        self,
        request: WalletIntelligenceDiscoveryRequest | None,
    ) -> Tuple[WalletActivitySnapshot, ...]:
        if request is None:
            return tuple(self.source_snapshots)

        metadata = request.metadata or {}
        records = None
        for key in ("snapshots", "wallet_snapshots", "wallet_activity", "records", "raw_records"):
            if key in metadata:
                records = metadata[key]
                break

        if records is None:
            return tuple(self.source_snapshots)

        record_tuple = tuple(records)
        if all(isinstance(record, WalletActivitySnapshot) for record in record_tuple):
            return record_tuple

        adapter = WalletIntelligenceSourceAdapter(source_name=request.source_name)
        return adapter.normalize_batch(record_tuple).snapshots

    def _to_universal_market(self, snapshot: WalletActivitySnapshot) -> Mapping[str, Any]:
        payload = {
            "schema_family": "UMM",
            "market_type": "wallet_intelligence",
            "chain": snapshot.chain,
            "wallet": snapshot.wallet,
            "symbol": snapshot.symbol,
            "token_address": snapshot.token_address,
            "action": snapshot.action,
            "usd_value": snapshot.usd_value,
            "price": snapshot.price,
            "tx_hash": snapshot.tx_hash,
            "block_time": snapshot.block_time,
            "wallet_score": snapshot.wallet_score,
            "win_rate": snapshot.win_rate,
            "realized_pnl": snapshot.realized_pnl,
            "read_only": True,
            "execution_allowed": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
        }
        return _freeze(payload)

    def _classify_signal(self, snapshot: WalletActivitySnapshot) -> str:
        action = snapshot.action.lower()
        if action in {"buy", "accumulate", "increase", "new_position"}:
            return "smart_money_accumulation"
        if action in {"sell", "distribute", "decrease"}:
            return "smart_money_distribution"
        return "wallet_activity_observation"

    def _score_signal(self, snapshot: WalletActivitySnapshot) -> float:
        value_score = min(snapshot.usd_value, 100_000.0) / 100_000.0
        pnl_score = max(0.0, min(snapshot.realized_pnl, 100_000.0) / 100_000.0)
        win_score = snapshot.win_rate
        wallet_score = snapshot.wallet_score
        holding_score = min(snapshot.holding_count, 25) / 25.0

        signal_score = (
            wallet_score * 0.40
            + value_score * 0.25
            + win_score * 0.20
            + pnl_score * 0.10
            + holding_score * 0.05
        )
        return round(max(0.0, min(1.0, signal_score)), 6)

    def _build_opportunity(
        self,
        snapshot: WalletActivitySnapshot,
    ) -> Optional[WalletIntelligenceOpportunity]:
        if not snapshot.wallet or not snapshot.chain or not snapshot.symbol:
            return None

        if snapshot.wallet_score < self.min_wallet_score:
            return None

        if snapshot.usd_value < self.min_usd_value:
            return None

        signal_score = self._score_signal(snapshot)
        if signal_score < self.min_signal_score:
            return None

        signal_type = self._classify_signal(snapshot)

        confidence = round(
            max(
                0.0,
                min(
                    1.0,
                    signal_score * 0.70
                    + snapshot.wallet_score * 0.20
                    + snapshot.win_rate * 0.10,
                ),
            ),
            6,
        )

        identity_payload = {
            "wallet": snapshot.wallet,
            "chain": snapshot.chain,
            "symbol": snapshot.symbol,
            "tx_hash": snapshot.tx_hash,
            "signal_type": signal_type,
            "signal_score": signal_score,
        }

        explanation = MappingProxyType(
            {
                "summary": "Wallet activity from a high-scoring wallet produced a read-only intelligence signal.",
                "wallet": snapshot.wallet,
                "chain": snapshot.chain,
                "symbol": snapshot.symbol,
                "action": snapshot.action,
                "signal_type": signal_type,
                "signal_score": signal_score,
                "usd_value": snapshot.usd_value,
                "wallet_score": snapshot.wallet_score,
                "win_rate": snapshot.win_rate,
                "realized_pnl": snapshot.realized_pnl,
                "rules": [
                    "read_only_scan",
                    "minimum_wallet_score_guardrail",
                    "minimum_usd_value_guardrail",
                    "minimum_signal_score_guardrail",
                    "deterministic_opportunity_id",
                    "no_signing_authority",
                    "no_fund_movement_authority",
                    "no_execution_authority",
                ],
            }
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "source_engine_id": self.engine_id,
                "wallet": snapshot.wallet,
                "chain": snapshot.chain,
                "symbol": snapshot.symbol,
                "tx_hash": snapshot.tx_hash,
                "created_at": _utc_now_iso(),
                "read_only": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
            }
        )

        return WalletIntelligenceOpportunity(
            opportunity_id=_stable_id("uop.wallet_intelligence", identity_payload),
            schema_version="UOM-compatible/WDM-003",
            wallet=snapshot.wallet,
            chain=snapshot.chain,
            symbol=snapshot.symbol,
            opportunity_type="wallet_intelligence_signal",
            source_engine_id=self.engine_id,
            signal_type=signal_type,
            signal_score=signal_score,
            confidence=confidence,
            usd_value=snapshot.usd_value,
            wallet_score=snapshot.wallet_score,
            universal_market=self._to_universal_market(snapshot),
            status="discovered",
            explanation=explanation,
            telemetry=telemetry,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ENGINE_NAME",
    "WalletIntelligenceOpportunity",
    "WalletIntelligenceDiscoveryEngine",
]
