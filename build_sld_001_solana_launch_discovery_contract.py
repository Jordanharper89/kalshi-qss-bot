from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "solana_launch_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

CONTRACT_FILE = MODULE_DIR / "solana_launch_discovery_contract.py"
TEST_FILE = ROOT / "test_sld_001_solana_launch_discovery_contract.py"
INIT_FILE = MODULE_DIR / "__init__.py"
ORACLE_INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

CONTRACT_CODE = r'''"""
SLD-001 Solana Launch Discovery Contract

Canonical read-only contract for Oracle Solana Launch Discovery.

Oracle discovers and explains launch opportunities.
Oracle does not buy, sell, swap, sign, route, or execute.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple


SCHEMA_VERSION = "SLD-001"
CONTRACT_ID = "oracle.discovery.contract.solana_launch"


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


class SolanaLaunchDiscoveryFamily(str, Enum):
    NEW_TOKEN_LAUNCH = "new_token_launch"
    LIQUIDITY_ADDED = "liquidity_added"
    RAYDIUM_POOL = "raydium_pool"
    WALLET_LAUNCH_SIGNAL = "wallet_launch_signal"
    TOKEN_SAFETY_SIGNAL = "token_safety_signal"


@dataclass(frozen=True)
class SolanaLaunchDiscoveryRequest:
    request_id: str
    family: SolanaLaunchDiscoveryFamily
    source_name: str
    mints: Tuple[str, ...] = field(default_factory=tuple)
    pools: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "mints", tuple(str(m) for m in self.mints))
        object.__setattr__(self, "pools", tuple(str(p) for p in self.pools))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "request_id": self.request_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "mints": list(self.mints),
            "pools": list(self.pools),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SolanaLaunchDiscoveryTelemetry:
    schema_version: str
    engine_id: str
    request_id: str
    started_at: str
    completed_at: str
    records_seen: int
    launches_seen: int
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
            "launches_seen": self.launches_seen,
            "opportunities_emitted": self.opportunities_emitted,
            "rejected_records": self.rejected_records,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SolanaLaunchDiscoveryHealth:
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
class SolanaLaunchDiscoveryCapability:
    schema_version: str
    engine_id: str
    family: SolanaLaunchDiscoveryFamily
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
class SolanaLaunchDiscoveryResult:
    schema_version: str
    engine_id: str
    request_id: str
    status: str
    opportunities: Tuple[Any, ...]
    telemetry: SolanaLaunchDiscoveryTelemetry
    health: SolanaLaunchDiscoveryHealth
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


class SolanaLaunchDiscoveryEngineContract:
    schema_version = SCHEMA_VERSION
    contract_id = CONTRACT_ID
    read_only = True

    @property
    def engine_id(self) -> str:
        raise NotImplementedError

    def capabilities(self) -> SolanaLaunchDiscoveryCapability:
        raise NotImplementedError

    def health(self) -> SolanaLaunchDiscoveryHealth:
        raise NotImplementedError

    def discover(self, request: SolanaLaunchDiscoveryRequest) -> SolanaLaunchDiscoveryResult:
        raise NotImplementedError


class EmptySolanaLaunchDiscoveryEngine(SolanaLaunchDiscoveryEngineContract):
    engine_id = "oracle.discovery.solana_launch.empty"

    def capabilities(self) -> SolanaLaunchDiscoveryCapability:
        return SolanaLaunchDiscoveryCapability(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH,
            source_name="empty",
            metadata={
                "purpose": "contract regression test",
                "execution": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
            },
        )

    def health(self) -> SolanaLaunchDiscoveryHealth:
        return SolanaLaunchDiscoveryHealth(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"empty_engine": True, "read_only": True},
        )

    def discover(self, request: SolanaLaunchDiscoveryRequest) -> SolanaLaunchDiscoveryResult:
        started_at = _utc_now_iso()
        telemetry = SolanaLaunchDiscoveryTelemetry(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=0,
            launches_seen=0,
            opportunities_emitted=0,
            rejected_records=0,
            metadata={"empty": True, "read_only": True},
        )
        return SolanaLaunchDiscoveryResult(
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
    "SolanaLaunchDiscoveryFamily",
    "SolanaLaunchDiscoveryRequest",
    "SolanaLaunchDiscoveryTelemetry",
    "SolanaLaunchDiscoveryHealth",
    "SolanaLaunchDiscoveryCapability",
    "SolanaLaunchDiscoveryResult",
    "SolanaLaunchDiscoveryEngineContract",
    "EmptySolanaLaunchDiscoveryEngine",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.solana_launch_discovery_model.solana_launch_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    SolanaLaunchDiscoveryFamily,
    SolanaLaunchDiscoveryRequest,
    EmptySolanaLaunchDiscoveryEngine,
)


def test_sld_001_solana_launch_discovery_contract():
    request = SolanaLaunchDiscoveryRequest(
        request_id="solana.launch.discovery.test.request",
        family=SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH,
        source_name="test_source",
        mints=("mint_a", "mint_b"),
        pools=("pool_a",),
        metadata={"records": [{"mint": "mint_a", "pool": "pool_a"}]},
    )

    engine = EmptySolanaLaunchDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "SLD-001"
    assert CONTRACT_ID == "oracle.discovery.contract.solana_launch"

    assert request.read_only is True
    assert request.mints == ("mint_a", "mint_b")
    assert request.pools == ("pool_a",)
    assert request.family == SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True
    assert caps.metadata["signing_allowed"] is False
    assert caps.metadata["fund_movement_allowed"] is False
    assert caps.metadata["swap_allowed"] is False

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "SLD-001"
    assert result.engine_id == "oracle.discovery.solana_launch.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.launches_seen == 0
    assert result.telemetry.opportunities_emitted == 0
    assert result.health.status == "ok"

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "SLD-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] SLD-001 Solana Launch Discovery Contract")
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
    test_sld_001_solana_launch_discovery_contract()
'''

INIT_CODE = '''try:
    from .solana_launch_discovery_contract import (
        SCHEMA_VERSION,
        CONTRACT_ID,
        SolanaLaunchDiscoveryFamily,
        SolanaLaunchDiscoveryRequest,
        SolanaLaunchDiscoveryTelemetry,
        SolanaLaunchDiscoveryHealth,
        SolanaLaunchDiscoveryCapability,
        SolanaLaunchDiscoveryResult,
        SolanaLaunchDiscoveryEngineContract,
        EmptySolanaLaunchDiscoveryEngine,
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
    from .solana_launch_discovery_model.solana_launch_discovery_contract import (
        SolanaLaunchDiscoveryFamily,
        SolanaLaunchDiscoveryRequest,
        SolanaLaunchDiscoveryEngineContract,
    )
except Exception:
    pass
'''

if "SolanaLaunchDiscoveryEngineContract" not in existing_oracle_init:
    ORACLE_INIT.write_text(existing_oracle_init.rstrip() + "\n" + ORACLE_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" SLD-001 INSTALLER")
print(" Solana Launch Discovery Contract")
print("========================================")
print(f"[OK] Wrote {CONTRACT_FILE}")
print(f"[OK] Wrote {INIT_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {ORACLE_INIT}")
print()
print("[DONE] SLD-001 installed")
print()
print("Run:")
print("py test_sld_001_solana_launch_discovery_contract.py")