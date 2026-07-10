from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "arbitrage_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

CONTRACT_FILE = MODULE_DIR / "arbitrage_discovery_contract.py"
TEST_FILE = ROOT / "test_adm_001_arbitrage_discovery_contract.py"
INIT_FILE = MODULE_DIR / "__init__.py"
ORACLE_INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

CONTRACT_CODE = r'''"""
ADM-001 Arbitrage Discovery Contract

Canonical read-only contract for Oracle Arbitrage Discovery divisions.

Oracle responsibilities:
- discover cross-market / cross-venue pricing gaps
- normalize source records
- emit UniversalOpportunity-compatible records
- preserve determinism, replayability, explainability, telemetry

Oracle does NOT:
- place trades
- route orders
- execute legs
- size positions
- manage exits
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple


SCHEMA_VERSION = "ADM-001"
CONTRACT_ID = "oracle.discovery.contract.arbitrage"


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


class ArbitrageDiscoveryFamily(str, Enum):
    CROSS_EXCHANGE = "cross_exchange"
    CROSS_MARKET = "cross_market"
    PREDICTION_MARKET = "prediction_market_arbitrage"
    CRYPTO_SPOT = "crypto_spot_arbitrage"
    TRIANGULAR = "triangular_arbitrage"
    LATENCY = "latency_arbitrage"
    SPREAD = "spread_arbitrage"


@dataclass(frozen=True)
class ArbitrageDiscoveryRequest:
    request_id: str
    family: ArbitrageDiscoveryFamily
    source_name: str
    symbols: Tuple[str, ...] = field(default_factory=tuple)
    venues: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "symbols", tuple(str(s).upper() for s in self.symbols))
        object.__setattr__(self, "venues", tuple(str(v).lower() for v in self.venues))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "request_id": self.request_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "symbols": list(self.symbols),
            "venues": list(self.venues),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class ArbitrageDiscoveryTelemetry:
    schema_version: str
    engine_id: str
    request_id: str
    started_at: str
    completed_at: str
    records_seen: int
    pairs_evaluated: int
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
            "pairs_evaluated": self.pairs_evaluated,
            "opportunities_emitted": self.opportunities_emitted,
            "rejected_records": self.rejected_records,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class ArbitrageDiscoveryHealth:
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
class ArbitrageDiscoveryCapability:
    schema_version: str
    engine_id: str
    family: ArbitrageDiscoveryFamily
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
class ArbitrageDiscoveryResult:
    schema_version: str
    engine_id: str
    request_id: str
    status: str
    opportunities: Tuple[Any, ...]
    telemetry: ArbitrageDiscoveryTelemetry
    health: ArbitrageDiscoveryHealth
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


class ArbitrageDiscoveryEngineContract:
    schema_version = SCHEMA_VERSION
    contract_id = CONTRACT_ID
    read_only = True

    @property
    def engine_id(self) -> str:
        raise NotImplementedError

    def capabilities(self) -> ArbitrageDiscoveryCapability:
        raise NotImplementedError

    def health(self) -> ArbitrageDiscoveryHealth:
        raise NotImplementedError

    def discover(self, request: ArbitrageDiscoveryRequest) -> ArbitrageDiscoveryResult:
        raise NotImplementedError


class EmptyArbitrageDiscoveryEngine(ArbitrageDiscoveryEngineContract):
    engine_id = "oracle.discovery.arbitrage.empty"

    def capabilities(self) -> ArbitrageDiscoveryCapability:
        return ArbitrageDiscoveryCapability(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=ArbitrageDiscoveryFamily.CROSS_EXCHANGE,
            source_name="empty",
            metadata={"purpose": "contract regression test", "execution": False},
        )

    def health(self) -> ArbitrageDiscoveryHealth:
        return ArbitrageDiscoveryHealth(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"empty_engine": True, "read_only": True},
        )

    def discover(self, request: ArbitrageDiscoveryRequest) -> ArbitrageDiscoveryResult:
        started_at = _utc_now_iso()
        telemetry = ArbitrageDiscoveryTelemetry(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=0,
            pairs_evaluated=0,
            opportunities_emitted=0,
            rejected_records=0,
            metadata={"empty": True, "read_only": True},
        )
        return ArbitrageDiscoveryResult(
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
    "ArbitrageDiscoveryFamily",
    "ArbitrageDiscoveryRequest",
    "ArbitrageDiscoveryTelemetry",
    "ArbitrageDiscoveryHealth",
    "ArbitrageDiscoveryCapability",
    "ArbitrageDiscoveryResult",
    "ArbitrageDiscoveryEngineContract",
    "EmptyArbitrageDiscoveryEngine",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.arbitrage_discovery_model.arbitrage_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    ArbitrageDiscoveryFamily,
    ArbitrageDiscoveryRequest,
    EmptyArbitrageDiscoveryEngine,
)


def test_adm_001_arbitrage_discovery_contract():
    request = ArbitrageDiscoveryRequest(
        request_id="arbitrage.discovery.test.request",
        family=ArbitrageDiscoveryFamily.CROSS_EXCHANGE,
        source_name="test_source",
        symbols=("btc-usd", "eth-usd"),
        venues=("Coinbase", "Kraken"),
        metadata={"records": [{"symbol": "BTC-USD", "venue": "coinbase"}]},
    )

    engine = EmptyArbitrageDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "ADM-001"
    assert CONTRACT_ID == "oracle.discovery.contract.arbitrage"

    assert request.read_only is True
    assert request.symbols == ("BTC-USD", "ETH-USD")
    assert request.venues == ("coinbase", "kraken")
    assert request.family == ArbitrageDiscoveryFamily.CROSS_EXCHANGE

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "ADM-001"
    assert result.engine_id == "oracle.discovery.arbitrage.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.pairs_evaluated == 0
    assert result.telemetry.opportunities_emitted == 0
    assert result.health.status == "ok"

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "ADM-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] ADM-001 Arbitrage Discovery Contract")
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
    test_adm_001_arbitrage_discovery_contract()
'''

INIT_CODE = '''try:
    from .arbitrage_discovery_contract import (
        SCHEMA_VERSION,
        CONTRACT_ID,
        ArbitrageDiscoveryFamily,
        ArbitrageDiscoveryRequest,
        ArbitrageDiscoveryTelemetry,
        ArbitrageDiscoveryHealth,
        ArbitrageDiscoveryCapability,
        ArbitrageDiscoveryResult,
        ArbitrageDiscoveryEngineContract,
        EmptyArbitrageDiscoveryEngine,
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
    from .arbitrage_discovery_model.arbitrage_discovery_contract import (
        ArbitrageDiscoveryFamily,
        ArbitrageDiscoveryRequest,
        ArbitrageDiscoveryEngineContract,
    )
except Exception:
    pass
'''

if "ArbitrageDiscoveryEngineContract" not in existing_oracle_init:
    ORACLE_INIT.write_text(existing_oracle_init.rstrip() + "\n" + ORACLE_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" ADM-001 INSTALLER")
print(" Arbitrage Discovery Contract")
print("========================================")
print(f"[OK] Wrote {CONTRACT_FILE}")
print(f"[OK] Wrote {INIT_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {ORACLE_INIT}")
print()
print("[DONE] ADM-001 installed")
print()
print("Run:")
print("py test_adm_001_arbitrage_discovery_contract.py")