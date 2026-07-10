from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "macro_event_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

CONTRACT_FILE = MODULE_DIR / "macro_event_discovery_contract.py"
TEST_FILE = ROOT / "test_med_001_macro_event_discovery_contract.py"
INIT_FILE = MODULE_DIR / "__init__.py"
ORACLE_INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

CONTRACT_CODE = r'''"""
MED-001 Macro Event Discovery Contract

Canonical read-only contract for Oracle Macro Event Discovery.

Oracle discovers, normalizes, explains, and ranks macro event intelligence.
Oracle does not execute trades, size positions, route orders, or manage exits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple


SCHEMA_VERSION = "MED-001"
CONTRACT_ID = "oracle.discovery.contract.macro_event"


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


class MacroEventDiscoveryFamily(str, Enum):
    ECONOMIC_RELEASE = "economic_release"
    FED_EVENT = "fed_event"
    INFLATION_EVENT = "inflation_event"
    JOBS_EVENT = "jobs_event"
    GEOPOLITICAL_EVENT = "geopolitical_event"
    ELECTION_EVENT = "election_event"
    WEATHER_EVENT = "weather_event"
    NEWS_SHOCK = "news_shock"
    CROSS_MARKET_EVENT = "cross_market_event"


@dataclass(frozen=True)
class MacroEventDiscoveryRequest:
    request_id: str
    family: MacroEventDiscoveryFamily
    source_name: str
    event_ids: Tuple[str, ...] = field(default_factory=tuple)
    regions: Tuple[str, ...] = field(default_factory=tuple)
    markets: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "event_ids", tuple(str(e) for e in self.event_ids))
        object.__setattr__(self, "regions", tuple(str(r).upper() for r in self.regions))
        object.__setattr__(self, "markets", tuple(str(m).upper() for m in self.markets))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "request_id": self.request_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "event_ids": list(self.event_ids),
            "regions": list(self.regions),
            "markets": list(self.markets),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class MacroEventDiscoveryTelemetry:
    schema_version: str
    engine_id: str
    request_id: str
    started_at: str
    completed_at: str
    records_seen: int
    events_seen: int
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
            "events_seen": self.events_seen,
            "opportunities_emitted": self.opportunities_emitted,
            "rejected_records": self.rejected_records,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class MacroEventDiscoveryHealth:
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
class MacroEventDiscoveryCapability:
    schema_version: str
    engine_id: str
    family: MacroEventDiscoveryFamily
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
class MacroEventDiscoveryResult:
    schema_version: str
    engine_id: str
    request_id: str
    status: str
    opportunities: Tuple[Any, ...]
    telemetry: MacroEventDiscoveryTelemetry
    health: MacroEventDiscoveryHealth
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


class MacroEventDiscoveryEngineContract:
    schema_version = SCHEMA_VERSION
    contract_id = CONTRACT_ID
    read_only = True

    @property
    def engine_id(self) -> str:
        raise NotImplementedError

    def capabilities(self) -> MacroEventDiscoveryCapability:
        raise NotImplementedError

    def health(self) -> MacroEventDiscoveryHealth:
        raise NotImplementedError

    def discover(self, request: MacroEventDiscoveryRequest) -> MacroEventDiscoveryResult:
        raise NotImplementedError


class EmptyMacroEventDiscoveryEngine(MacroEventDiscoveryEngineContract):
    engine_id = "oracle.discovery.macro_event.empty"

    def capabilities(self) -> MacroEventDiscoveryCapability:
        return MacroEventDiscoveryCapability(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=MacroEventDiscoveryFamily.ECONOMIC_RELEASE,
            source_name="empty",
            metadata={
                "purpose": "contract regression test",
                "execution": False,
                "order_allowed": False,
                "position_sizing_allowed": False,
            },
        )

    def health(self) -> MacroEventDiscoveryHealth:
        return MacroEventDiscoveryHealth(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"empty_engine": True, "read_only": True},
        )

    def discover(self, request: MacroEventDiscoveryRequest) -> MacroEventDiscoveryResult:
        started_at = _utc_now_iso()
        telemetry = MacroEventDiscoveryTelemetry(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=0,
            events_seen=0,
            opportunities_emitted=0,
            rejected_records=0,
            metadata={"empty": True, "read_only": True},
        )
        return MacroEventDiscoveryResult(
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
    "MacroEventDiscoveryFamily",
    "MacroEventDiscoveryRequest",
    "MacroEventDiscoveryTelemetry",
    "MacroEventDiscoveryHealth",
    "MacroEventDiscoveryCapability",
    "MacroEventDiscoveryResult",
    "MacroEventDiscoveryEngineContract",
    "EmptyMacroEventDiscoveryEngine",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.macro_event_discovery_model.macro_event_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    MacroEventDiscoveryFamily,
    MacroEventDiscoveryRequest,
    EmptyMacroEventDiscoveryEngine,
)


def test_med_001_macro_event_discovery_contract():
    request = MacroEventDiscoveryRequest(
        request_id="macro.event.discovery.test.request",
        family=MacroEventDiscoveryFamily.ECONOMIC_RELEASE,
        source_name="test_source",
        event_ids=("cpi_2026_01", "fomc_2026_01"),
        regions=("us", "global"),
        markets=("rates", "prediction_markets"),
        metadata={"records": [{"event_id": "cpi_2026_01", "region": "US"}]},
    )

    engine = EmptyMacroEventDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "MED-001"
    assert CONTRACT_ID == "oracle.discovery.contract.macro_event"

    assert request.read_only is True
    assert request.event_ids == ("cpi_2026_01", "fomc_2026_01")
    assert request.regions == ("US", "GLOBAL")
    assert request.markets == ("RATES", "PREDICTION_MARKETS")
    assert request.family == MacroEventDiscoveryFamily.ECONOMIC_RELEASE

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True
    assert caps.metadata["execution"] is False
    assert caps.metadata["order_allowed"] is False
    assert caps.metadata["position_sizing_allowed"] is False

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "MED-001"
    assert result.engine_id == "oracle.discovery.macro_event.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.events_seen == 0
    assert result.telemetry.opportunities_emitted == 0
    assert result.health.status == "ok"

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "MED-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] MED-001 Macro Event Discovery Contract")
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
    test_med_001_macro_event_discovery_contract()
'''

INIT_CODE = '''try:
    from .macro_event_discovery_contract import (
        SCHEMA_VERSION,
        CONTRACT_ID,
        MacroEventDiscoveryFamily,
        MacroEventDiscoveryRequest,
        MacroEventDiscoveryTelemetry,
        MacroEventDiscoveryHealth,
        MacroEventDiscoveryCapability,
        MacroEventDiscoveryResult,
        MacroEventDiscoveryEngineContract,
        EmptyMacroEventDiscoveryEngine,
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
    from .macro_event_discovery_model.macro_event_discovery_contract import (
        MacroEventDiscoveryFamily,
        MacroEventDiscoveryRequest,
        MacroEventDiscoveryEngineContract,
    )
except Exception:
    pass
'''

if "MacroEventDiscoveryEngineContract" not in existing_oracle_init:
    ORACLE_INIT.write_text(existing_oracle_init.rstrip() + "\n" + ORACLE_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" MED-001 INSTALLER")
print(" Macro Event Discovery Contract")
print("========================================")
print(f"[OK] Wrote {CONTRACT_FILE}")
print(f"[OK] Wrote {INIT_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {ORACLE_INIT}")
print()
print("[DONE] MED-001 installed")
print()
print("Run:")
print("py test_med_001_macro_event_discovery_contract.py")