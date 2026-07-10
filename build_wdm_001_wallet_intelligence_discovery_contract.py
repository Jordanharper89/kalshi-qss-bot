from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "wallet_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

CONTRACT_FILE = MODULE_DIR / "wallet_intelligence_discovery_contract.py"
TEST_FILE = ROOT / "test_wdm_001_wallet_intelligence_discovery_contract.py"
INIT_FILE = MODULE_DIR / "__init__.py"
ORACLE_INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

CONTRACT_CODE = r'''"""
WDM-001 Wallet Intelligence Discovery Contract

Canonical read-only contract for Oracle Wallet Intelligence Discovery.

Oracle responsibilities:
- observe wallet activity
- normalize wallet/entity/event intelligence
- discover wallet-driven opportunities
- preserve determinism, replayability, explainability, telemetry

Oracle does NOT:
- sign transactions
- move funds
- execute trades
- place orders
- manage exits
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple


SCHEMA_VERSION = "WDM-001"
CONTRACT_ID = "oracle.discovery.contract.wallet_intelligence"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


class WalletIntelligenceFamily(str, Enum):
    SMART_MONEY = "smart_money"
    WHALE_ACTIVITY = "whale_activity"
    TOKEN_ACCUMULATION = "token_accumulation"
    TOKEN_DISTRIBUTION = "token_distribution"
    NEW_POSITION = "new_position"
    WALLET_CLUSTER = "wallet_cluster"
    SOLANA_WALLET = "solana_wallet"
    EVM_WALLET = "evm_wallet"


@dataclass(frozen=True)
class WalletIntelligenceDiscoveryRequest:
    request_id: str
    family: WalletIntelligenceFamily
    source_name: str
    chains: Tuple[str, ...] = field(default_factory=tuple)
    wallets: Tuple[str, ...] = field(default_factory=tuple)
    symbols: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "chains", tuple(str(c).lower() for c in self.chains))
        object.__setattr__(self, "wallets", tuple(str(w) for w in self.wallets))
        object.__setattr__(self, "symbols", tuple(str(s).upper() for s in self.symbols))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "request_id": self.request_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "chains": list(self.chains),
            "wallets": list(self.wallets),
            "symbols": list(self.symbols),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class WalletIntelligenceDiscoveryTelemetry:
    schema_version: str
    engine_id: str
    request_id: str
    started_at: str
    completed_at: str
    records_seen: int
    wallets_seen: int
    opportunities_emitted: int
    rejected_records: int
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "request_id": self.request_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "records_seen": self.records_seen,
            "wallets_seen": self.wallets_seen,
            "opportunities_emitted": self.opportunities_emitted,
            "rejected_records": self.rejected_records,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class WalletIntelligenceDiscoveryHealth:
    schema_version: str
    engine_id: str
    status: str
    ready: bool
    details: Mapping[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=_utc_now_iso)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "details", _freeze(dict(self.details or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "status": self.status,
            "ready": self.ready,
            "details": dict(self.details),
            "checked_at": self.checked_at,
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class WalletIntelligenceDiscoveryCapability:
    schema_version: str
    engine_id: str
    family: WalletIntelligenceFamily
    source_name: str
    supports_replay: bool = True
    deterministic: bool = True
    telemetry: bool = True
    read_only: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "supports_replay": self.supports_replay,
            "deterministic": self.deterministic,
            "telemetry": self.telemetry,
            "read_only": self.read_only,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class WalletIntelligenceDiscoveryResult:
    schema_version: str
    engine_id: str
    request_id: str
    status: str
    opportunities: Tuple[Any, ...]
    telemetry: WalletIntelligenceDiscoveryTelemetry
    health: WalletIntelligenceDiscoveryHealth
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "opportunities", tuple(self.opportunities or ()))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "request_id": self.request_id,
            "status": self.status,
            "opportunities": [
                o.to_dict() if hasattr(o, "to_dict") else dict(o)
                for o in self.opportunities
            ],
            "telemetry": self.telemetry.to_dict(),
            "health": self.health.to_dict(),
            "read_only": self.read_only,
        }


class WalletIntelligenceDiscoveryEngineContract:
    schema_version = SCHEMA_VERSION
    contract_id = CONTRACT_ID
    read_only = True

    @property
    def engine_id(self) -> str:
        raise NotImplementedError

    def capabilities(self) -> WalletIntelligenceDiscoveryCapability:
        raise NotImplementedError

    def health(self) -> WalletIntelligenceDiscoveryHealth:
        raise NotImplementedError

    def discover(
        self,
        request: WalletIntelligenceDiscoveryRequest,
    ) -> WalletIntelligenceDiscoveryResult:
        raise NotImplementedError


class EmptyWalletIntelligenceDiscoveryEngine(WalletIntelligenceDiscoveryEngineContract):
    engine_id = "oracle.discovery.wallet_intelligence.empty"

    def capabilities(self) -> WalletIntelligenceDiscoveryCapability:
        return WalletIntelligenceDiscoveryCapability(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=WalletIntelligenceFamily.SMART_MONEY,
            source_name="empty",
            metadata={
                "purpose": "contract regression test",
                "execution": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
            },
        )

    def health(self) -> WalletIntelligenceDiscoveryHealth:
        return WalletIntelligenceDiscoveryHealth(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"empty_engine": True, "read_only": True},
        )

    def discover(
        self,
        request: WalletIntelligenceDiscoveryRequest,
    ) -> WalletIntelligenceDiscoveryResult:
        started_at = _utc_now_iso()
        telemetry = WalletIntelligenceDiscoveryTelemetry(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=0,
            wallets_seen=0,
            opportunities_emitted=0,
            rejected_records=0,
            metadata={"empty": True, "read_only": True},
        )
        return WalletIntelligenceDiscoveryResult(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            status="empty",
            opportunities=(),
            telemetry=telemetry,
            health=self.health(),
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "CONTRACT_ID",
    "WalletIntelligenceFamily",
    "WalletIntelligenceDiscoveryRequest",
    "WalletIntelligenceDiscoveryTelemetry",
    "WalletIntelligenceDiscoveryHealth",
    "WalletIntelligenceDiscoveryCapability",
    "WalletIntelligenceDiscoveryResult",
    "WalletIntelligenceDiscoveryEngineContract",
    "EmptyWalletIntelligenceDiscoveryEngine",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.wallet_intelligence_discovery_model.wallet_intelligence_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    WalletIntelligenceFamily,
    WalletIntelligenceDiscoveryRequest,
    EmptyWalletIntelligenceDiscoveryEngine,
)


def test_wdm_001_wallet_intelligence_discovery_contract():
    request = WalletIntelligenceDiscoveryRequest(
        request_id="wallet.discovery.test.request",
        family=WalletIntelligenceFamily.SMART_MONEY,
        source_name="test_source",
        chains=("Solana", "Ethereum"),
        wallets=("wallet_a", "wallet_b"),
        symbols=("sol-usd", "eth-usd"),
        metadata={"records": [{"wallet": "wallet_a", "chain": "solana"}]},
    )

    engine = EmptyWalletIntelligenceDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "WDM-001"
    assert CONTRACT_ID == "oracle.discovery.contract.wallet_intelligence"

    assert request.read_only is True
    assert request.chains == ("solana", "ethereum")
    assert request.wallets == ("wallet_a", "wallet_b")
    assert request.symbols == ("SOL-USD", "ETH-USD")
    assert request.family == WalletIntelligenceFamily.SMART_MONEY

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True
    assert caps.metadata["signing_allowed"] is False
    assert caps.metadata["fund_movement_allowed"] is False

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "WDM-001"
    assert result.engine_id == "oracle.discovery.wallet_intelligence.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.wallets_seen == 0
    assert result.telemetry.opportunities_emitted == 0
    assert result.health.status == "ok"

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "WDM-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] WDM-001 Wallet Intelligence Discovery Contract")
    print(
        {
            "schema_version": d["schema_version"],
            "engine_id": d["engine_id"],
            "status": d["status"],
            "opportunities": len(d["opportunities"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_wdm_001_wallet_intelligence_discovery_contract()
'''

INIT_CODE = '''try:
    from .wallet_intelligence_discovery_contract import (
        SCHEMA_VERSION,
        CONTRACT_ID,
        WalletIntelligenceFamily,
        WalletIntelligenceDiscoveryRequest,
        WalletIntelligenceDiscoveryTelemetry,
        WalletIntelligenceDiscoveryHealth,
        WalletIntelligenceDiscoveryCapability,
        WalletIntelligenceDiscoveryResult,
        WalletIntelligenceDiscoveryEngineContract,
        EmptyWalletIntelligenceDiscoveryEngine,
    )
except Exception:
    pass
'''

CONTRACT_FILE.write_text(CONTRACT_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")
INIT_FILE.write_text(INIT_CODE, encoding="utf-8")

existing_oracle_init = ORACLE_INIT.read_text(encoding="utf-8") if ORACLE_INIT.exists() else ""
ORACLE_EXPORT = '''
try:
    from .wallet_intelligence_discovery_model.wallet_intelligence_discovery_contract import (
        WalletIntelligenceFamily,
        WalletIntelligenceDiscoveryRequest,
        WalletIntelligenceDiscoveryEngineContract,
    )
except Exception:
    pass
'''

if "WalletIntelligenceDiscoveryEngineContract" not in existing_oracle_init:
    ORACLE_INIT.write_text(existing_oracle_init.rstrip() + "\n" + ORACLE_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" WDM-001 INSTALLER")
print(" Wallet Intelligence Discovery Contract")
print("========================================")
print(f"[OK] Wrote {CONTRACT_FILE}")
print(f"[OK] Wrote {INIT_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {ORACLE_INIT}")
print()
print("[DONE] WDM-001 installed")
print()
print("Run:")
print("py test_wdm_001_wallet_intelligence_discovery_contract.py")