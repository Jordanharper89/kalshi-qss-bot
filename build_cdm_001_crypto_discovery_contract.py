from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "crypto_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

CONTRACT_FILE = MODULE_DIR / "crypto_discovery_contract.py"
TEST_FILE = ROOT / "test_cdm_001_crypto_discovery_contract.py"
INIT_FILE = MODULE_DIR / "__init__.py"
ORACLE_INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

CONTRACT_CODE = r'''"""
CDM-001 Crypto Discovery Contract

Canonical read-only contract for Oracle Crypto Discovery divisions.

Oracle responsibilities:
- discover crypto market opportunities
- normalize source records
- emit UniversalOpportunity-compatible records
- preserve determinism, replayability, explainability, telemetry

Oracle does NOT:
- place trades
- size positions
- execute swaps/orders
- manage exits
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Tuple


SCHEMA_VERSION = "CDM-001"
CONTRACT_ID = "oracle.discovery.contract.crypto"


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


class CryptoDiscoveryFamily(str, Enum):
    CRYPTO_SPOT = "crypto_spot"
    ARBITRAGE = "crypto_arbitrage"
    SOLANA_LAUNCH = "solana_launch"
    WALLET_INTELLIGENCE = "wallet_intelligence"
    LIQUIDITY = "crypto_liquidity"
    VOLATILITY = "crypto_volatility"


@dataclass(frozen=True)
class CryptoDiscoveryRequest:
    request_id: str
    family: CryptoDiscoveryFamily
    source_name: str
    symbols: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "symbols", tuple(str(s).upper() for s in self.symbols))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "request_id": self.request_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "symbols": list(self.symbols),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class CryptoDiscoveryTelemetry:
    schema_version: str
    engine_id: str
    request_id: str
    started_at: str
    completed_at: str
    records_seen: int
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
            "opportunities_emitted": self.opportunities_emitted,
            "rejected_records": self.rejected_records,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class CryptoDiscoveryHealth:
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
class CryptoDiscoveryCapability:
    schema_version: str
    engine_id: str
    family: CryptoDiscoveryFamily
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
class CryptoDiscoveryResult:
    schema_version: str
    engine_id: str
    request_id: str
    status: str
    opportunities: Tuple[Any, ...]
    telemetry: CryptoDiscoveryTelemetry
    health: CryptoDiscoveryHealth
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


class CryptoDiscoveryEngineContract:
    schema_version = SCHEMA_VERSION
    contract_id = CONTRACT_ID
    read_only = True

    @property
    def engine_id(self) -> str:
        raise NotImplementedError

    def capabilities(self) -> CryptoDiscoveryCapability:
        raise NotImplementedError

    def health(self) -> CryptoDiscoveryHealth:
        raise NotImplementedError

    def discover(self, request: CryptoDiscoveryRequest) -> CryptoDiscoveryResult:
        raise NotImplementedError


class EmptyCryptoDiscoveryEngine(CryptoDiscoveryEngineContract):
    engine_id = "oracle.discovery.crypto.empty"

    def capabilities(self) -> CryptoDiscoveryCapability:
        return CryptoDiscoveryCapability(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=CryptoDiscoveryFamily.CRYPTO_SPOT,
            source_name="empty",
            metadata={"purpose": "contract regression test"},
        )

    def health(self) -> CryptoDiscoveryHealth:
        return CryptoDiscoveryHealth(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"empty_engine": True},
        )

    def discover(self, request: CryptoDiscoveryRequest) -> CryptoDiscoveryResult:
        started_at = _utc_now_iso()
        telemetry = CryptoDiscoveryTelemetry(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=0,
            opportunities_emitted=0,
            rejected_records=0,
            metadata={"empty": True},
        )
        return CryptoDiscoveryResult(
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
    "CryptoDiscoveryFamily",
    "CryptoDiscoveryRequest",
    "CryptoDiscoveryTelemetry",
    "CryptoDiscoveryHealth",
    "CryptoDiscoveryCapability",
    "CryptoDiscoveryResult",
    "CryptoDiscoveryEngineContract",
    "EmptyCryptoDiscoveryEngine",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.crypto_discovery_model.crypto_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    CryptoDiscoveryFamily,
    CryptoDiscoveryRequest,
    EmptyCryptoDiscoveryEngine,
)


def test_cdm_001_crypto_discovery_contract():
    request = CryptoDiscoveryRequest(
        request_id="crypto.discovery.test.request",
        family=CryptoDiscoveryFamily.CRYPTO_SPOT,
        source_name="test_source",
        symbols=("btc-usd", "eth-usd"),
        metadata={"records": [{"symbol": "BTC-USD"}]},
    )

    engine = EmptyCryptoDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "CDM-001"
    assert CONTRACT_ID == "oracle.discovery.contract.crypto"

    assert request.read_only is True
    assert request.symbols == ("BTC-USD", "ETH-USD")
    assert request.family == CryptoDiscoveryFamily.CRYPTO_SPOT

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "CDM-001"
    assert result.engine_id == "oracle.discovery.crypto.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.opportunities_emitted == 0
    assert result.health.status == "ok"

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "CDM-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] CDM-001 Crypto Discovery Contract")
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
    test_cdm_001_crypto_discovery_contract()
'''

INIT_CODE = '''try:
    from .crypto_discovery_contract import (
        SCHEMA_VERSION,
        CONTRACT_ID,
        CryptoDiscoveryFamily,
        CryptoDiscoveryRequest,
        CryptoDiscoveryTelemetry,
        CryptoDiscoveryHealth,
        CryptoDiscoveryCapability,
        CryptoDiscoveryResult,
        CryptoDiscoveryEngineContract,
        EmptyCryptoDiscoveryEngine,
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
    from .crypto_discovery_model.crypto_discovery_contract import (
        CryptoDiscoveryFamily,
        CryptoDiscoveryRequest,
        CryptoDiscoveryEngineContract,
    )
except Exception:
    pass
'''

if "CryptoDiscoveryEngineContract" not in existing_oracle_init:
    ORACLE_INIT.write_text(existing_oracle_init.rstrip() + "\n" + ORACLE_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" CDM-001 INSTALLER")
print(" Crypto Discovery Contract")
print("========================================")
print(f"[OK] Wrote {CONTRACT_FILE}")
print(f"[OK] Wrote {INIT_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {ORACLE_INIT}")
print()
print("[DONE] CDM-001 installed")
print()
print("Run:")
print("py test_cdm_001_crypto_discovery_contract.py")