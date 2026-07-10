from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "wallet_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

ENGINE_FILE = MODULE_DIR / "wallet_intelligence_discovery_engine.py"
TEST_FILE = ROOT / "test_wdm_003_wallet_intelligence_discovery_engine.py"
INIT_FILE = MODULE_DIR / "__init__.py"

ENGINE_CODE = r'''"""
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
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.wallet_intelligence_discovery_model.wallet_intelligence_discovery_contract import (
    WalletIntelligenceDiscoveryRequest,
    WalletIntelligenceFamily,
)
from qseries_v2.oracle_intelligence.wallet_intelligence_discovery_model.wallet_intelligence_discovery_engine import (
    WalletIntelligenceDiscoveryEngine,
)


def test_wdm_003_wallet_intelligence_discovery_engine():
    raw_records = [
        {
            "address": "wallet_a",
            "network": "solana",
            "token_symbol": "WIF",
            "token_address": "wif_mint",
            "type": "accumulate",
            "token_amount": 25000,
            "value_usd": 10000,
            "token_price": 0.40,
            "tx_hash": "tx_a",
            "block_time": "2026-01-01T00:01:00Z",
            "wallet_score": 0.93,
            "realized_pnl": 25000,
            "win_rate": 0.81,
            "holding_count": 8,
        },
        {
            "wallet": "wallet_b",
            "chain": "Solana",
            "symbol": "BONK",
            "mint": "bonk_mint",
            "action": "buy",
            "amount": 1000000,
            "usd_value": 5000,
            "price": 0.005,
            "signature": "tx_b",
            "timestamp": "2026-01-01T00:02:00Z",
            "smart_money_score": 0.88,
            "pnl": 12000,
            "win_rate": 0.72,
            "positions": 15,
        },
        {
            "wallet": "wallet_c",
            "chain": "solana",
            "symbol": "LOW",
            "mint": "low_mint",
            "action": "buy",
            "amount": 100,
            "usd_value": 100,
            "price": 1.0,
            "signature": "tx_c",
            "timestamp": "2026-01-01T00:03:00Z",
            "smart_money_score": 0.20,
            "pnl": 0,
            "win_rate": 0.20,
            "positions": 1,
        },
    ]

    request = WalletIntelligenceDiscoveryRequest(
        request_id="wdm003.test.request",
        family=WalletIntelligenceFamily.SMART_MONEY,
        source_name="wdm_003_test_feed",
        chains=("solana",),
        wallets=("wallet_a", "wallet_b", "wallet_c"),
        symbols=("WIF", "BONK", "LOW"),
        metadata={"raw_records": raw_records},
    )

    engine = WalletIntelligenceDiscoveryEngine(
        min_wallet_score=0.70,
        min_usd_value=1000,
        min_signal_score=0.55,
    )

    caps = engine.capabilities()
    health = engine.health()
    report_1 = engine.discover(request)
    report_2 = engine.discover(request)

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.telemetry is True
    assert caps.metadata["signing_allowed"] is False
    assert caps.metadata["fund_movement_allowed"] is False
    assert health.status == "ok"
    assert health.read_only is True

    assert report_1.schema_version == "WDM-001"
    assert report_1.engine_id == "oracle.discovery.wallet_intelligence"
    assert report_1.status == "passed"
    assert report_1.read_only is True
    assert len(report_1.opportunities) == 2

    ids_1 = [o.opportunity_id for o in report_1.opportunities]
    ids_2 = [o.opportunity_id for o in report_2.opportunities]
    assert ids_1 == ids_2

    first = report_1.opportunities[0]
    assert first.read_only is True
    assert first.opportunity_type == "wallet_intelligence_signal"
    assert first.source_engine_id == "oracle.discovery.wallet_intelligence"
    assert first.signal_type in {"smart_money_accumulation", "smart_money_distribution", "wallet_activity_observation"}
    assert first.signal_score >= 0.55
    assert 0.0 <= first.confidence <= 1.0
    assert first.usd_value >= 1000
    assert first.wallet_score >= 0.70
    assert first.status == "discovered"
    assert first.universal_market["market_type"] == "wallet_intelligence"
    assert first.universal_market["read_only"] is True
    assert first.universal_market["execution_allowed"] is False
    assert first.universal_market["signing_allowed"] is False
    assert first.universal_market["fund_movement_allowed"] is False
    assert first.explanation["rules"]

    try:
        first.universal_market["execution_allowed"] = True
        raise AssertionError("universal_market should be immutable")
    except TypeError:
        pass

    d = report_1.to_dict()
    assert d["read_only"] is True
    assert d["telemetry"]["records_seen"] == 3
    assert d["telemetry"]["wallets_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["rejected_records"] == 1
    assert d["telemetry"]["read_only"] is True

    print("[PASS] WDM-003 Wallet Intelligence Discovery Engine")
    print(
        {
            "schema_version": "WDM-003",
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_wdm_003_wallet_intelligence_discovery_engine()
'''

INIT_EXPORT = '''
try:
    from .wallet_intelligence_discovery_engine import (
        WalletIntelligenceDiscoveryEngine,
        WalletIntelligenceOpportunity,
    )
except Exception:
    pass
'''

ENGINE_FILE.write_text(ENGINE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "WalletIntelligenceDiscoveryEngine" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" WDM-003 INSTALLER")
print(" Wallet Intelligence Discovery Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] WDM-003 installed")
print()
print("Run:")
print("py test_wdm_003_wallet_intelligence_discovery_engine.py")