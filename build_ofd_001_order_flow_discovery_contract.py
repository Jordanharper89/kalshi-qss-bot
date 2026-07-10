from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "order_flow_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

CONTRACT_FILE = MODULE_DIR / "order_flow_discovery_contract.py"
TEST_FILE = ROOT / "test_ofd_001_order_flow_discovery_contract.py"
INIT_FILE = MODULE_DIR / "__init__.py"
ORACLE_INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

CONTRACT_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Mapping, Tuple

SCHEMA_VERSION = "OFD-001"
CONTRACT_ID = "oracle.discovery.contract.order_flow"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _freeze(v: Any) -> Any:
    if isinstance(v, Mapping):
        return MappingProxyType({str(k): _freeze(x) for k, x in v.items()})
    if isinstance(v, list):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, tuple):
        return tuple(_freeze(x) for x in v)
    return v


class OrderFlowFamily(str, Enum):
    LIQUIDITY_IMBALANCE = "liquidity_imbalance"
    VOLUME_IMBALANCE = "volume_imbalance"
    ORDER_BOOK_PRESSURE = "order_book_pressure"
    TRADE_FLOW_MOMENTUM = "trade_flow_momentum"
    SPREAD_DISLOCATION = "spread_dislocation"
    DEPTH_SHIFT = "depth_shift"
    PREDICTION_MARKET_FLOW = "prediction_market_flow"
    CRYPTO_FLOW = "crypto_flow"


@dataclass(frozen=True)
class OrderFlowDiscoveryRequest:
    request_id: str
    family: OrderFlowFamily
    source_name: str
    market_ids: Tuple[str, ...] = field(default_factory=tuple)
    venues: Tuple[str, ...] = field(default_factory=tuple)
    symbols: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    read_only: bool = True

    def __post_init__(self):
        object.__setattr__(self, "market_ids", tuple(str(x) for x in self.market_ids))
        object.__setattr__(self, "venues", tuple(str(x).lower() for x in self.venues))
        object.__setattr__(self, "symbols", tuple(str(x).upper() for x in self.symbols))
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata or {})))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "request_id": self.request_id,
            "family": self.family.value,
            "source_name": self.source_name,
            "market_ids": list(self.market_ids),
            "venues": list(self.venues),
            "symbols": list(self.symbols),
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class OrderFlowDiscoveryTelemetry:
    schema_version: str
    engine_id: str
    request_id: str
    started_at: str
    completed_at: str
    records_seen: int
    markets_seen: int
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
            "markets_seen": self.markets_seen,
            "opportunities_emitted": self.opportunities_emitted,
            "rejected_records": self.rejected_records,
            "metadata": dict(self.metadata),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class OrderFlowDiscoveryHealth:
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
class OrderFlowDiscoveryCapability:
    schema_version: str
    engine_id: str
    family: OrderFlowFamily
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
class OrderFlowDiscoveryResult:
    schema_version: str
    engine_id: str
    request_id: str
    status: str
    opportunities: Tuple[Any, ...]
    telemetry: OrderFlowDiscoveryTelemetry
    health: OrderFlowDiscoveryHealth
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


class OrderFlowDiscoveryEngineContract:
    schema_version = SCHEMA_VERSION
    contract_id = CONTRACT_ID
    read_only = True

    @property
    def engine_id(self) -> str:
        raise NotImplementedError

    def capabilities(self) -> OrderFlowDiscoveryCapability:
        raise NotImplementedError

    def health(self) -> OrderFlowDiscoveryHealth:
        raise NotImplementedError

    def discover(self, request: OrderFlowDiscoveryRequest) -> OrderFlowDiscoveryResult:
        raise NotImplementedError


class EmptyOrderFlowDiscoveryEngine(OrderFlowDiscoveryEngineContract):
    engine_id = "oracle.discovery.order_flow.empty"

    def capabilities(self) -> OrderFlowDiscoveryCapability:
        return OrderFlowDiscoveryCapability(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            family=OrderFlowFamily.ORDER_BOOK_PRESSURE,
            source_name="empty",
            metadata={
                "purpose": "contract regression test",
                "execution": False,
                "order_allowed": False,
                "position_sizing_allowed": False,
                "broker_connectivity_allowed": False,
                "wallet_signing_allowed": False,
            },
        )

    def health(self) -> OrderFlowDiscoveryHealth:
        return OrderFlowDiscoveryHealth(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            status="ok",
            ready=True,
            details={"empty_engine": True, "read_only": True},
        )

    def discover(self, request: OrderFlowDiscoveryRequest) -> OrderFlowDiscoveryResult:
        started_at = _utc_now_iso()
        telemetry = OrderFlowDiscoveryTelemetry(
            schema_version=SCHEMA_VERSION,
            engine_id=self.engine_id,
            request_id=request.request_id,
            started_at=started_at,
            completed_at=_utc_now_iso(),
            records_seen=0,
            markets_seen=0,
            opportunities_emitted=0,
            rejected_records=0,
            metadata={"empty": True, "read_only": True},
        )
        return OrderFlowDiscoveryResult(
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
    "OrderFlowFamily",
    "OrderFlowDiscoveryRequest",
    "OrderFlowDiscoveryTelemetry",
    "OrderFlowDiscoveryHealth",
    "OrderFlowDiscoveryCapability",
    "OrderFlowDiscoveryResult",
    "OrderFlowDiscoveryEngineContract",
    "EmptyOrderFlowDiscoveryEngine",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_discovery_contract import (
    SCHEMA_VERSION,
    CONTRACT_ID,
    OrderFlowFamily,
    OrderFlowDiscoveryRequest,
    EmptyOrderFlowDiscoveryEngine,
)


def test_ofd_001_order_flow_discovery_contract():
    request = OrderFlowDiscoveryRequest(
        request_id="order.flow.discovery.test.request",
        family=OrderFlowFamily.ORDER_BOOK_PRESSURE,
        source_name="test_source",
        market_ids=("market_a", "market_b"),
        venues=("Kalshi", "Polymarket"),
        symbols=("btc", "eth"),
        metadata={"records": [{"market_id": "market_a", "bid_depth": 100}]},
    )

    engine = EmptyOrderFlowDiscoveryEngine()
    caps = engine.capabilities()
    health = engine.health()
    result = engine.discover(request)

    assert SCHEMA_VERSION == "OFD-001"
    assert CONTRACT_ID == "oracle.discovery.contract.order_flow"

    assert request.read_only is True
    assert request.market_ids == ("market_a", "market_b")
    assert request.venues == ("kalshi", "polymarket")
    assert request.symbols == ("BTC", "ETH")
    assert request.family == OrderFlowFamily.ORDER_BOOK_PRESSURE

    assert engine.read_only is True
    assert caps.read_only is True
    assert caps.deterministic is True
    assert caps.supports_replay is True
    assert caps.telemetry is True
    assert caps.metadata["execution"] is False
    assert caps.metadata["order_allowed"] is False
    assert caps.metadata["position_sizing_allowed"] is False
    assert caps.metadata["broker_connectivity_allowed"] is False
    assert caps.metadata["wallet_signing_allowed"] is False

    assert health.status == "ok"
    assert health.ready is True
    assert health.read_only is True

    assert result.schema_version == "OFD-001"
    assert result.engine_id == "oracle.discovery.order_flow.empty"
    assert result.status == "empty"
    assert result.read_only is True
    assert len(result.opportunities) == 0
    assert result.telemetry.records_seen == 0
    assert result.telemetry.markets_seen == 0
    assert result.telemetry.opportunities_emitted == 0

    try:
        request.metadata["new"] = "mutation"
        raise AssertionError("request metadata should be immutable")
    except TypeError:
        pass

    d = result.to_dict()
    assert d["schema_version"] == "OFD-001"
    assert d["read_only"] is True
    assert d["telemetry"]["read_only"] is True
    assert d["health"]["read_only"] is True

    print("[PASS] OFD-001 Order Flow Discovery Contract")
    print({
        "schema_version": d["schema_version"],
        "engine_id": d["engine_id"],
        "status": d["status"],
        "opportunities": len(d["opportunities"]),
        "read_only": d["read_only"],
    })


if __name__ == "__main__":
    test_ofd_001_order_flow_discovery_contract()
'''

INIT_CODE = '''
try:
    from .order_flow_discovery_contract import (
        SCHEMA_VERSION,
        CONTRACT_ID,
        OrderFlowFamily,
        OrderFlowDiscoveryRequest,
        OrderFlowDiscoveryTelemetry,
        OrderFlowDiscoveryHealth,
        OrderFlowDiscoveryCapability,
        OrderFlowDiscoveryResult,
        OrderFlowDiscoveryEngineContract,
        EmptyOrderFlowDiscoveryEngine,
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
    from .order_flow_discovery_model.order_flow_discovery_contract import (
        OrderFlowFamily,
        OrderFlowDiscoveryRequest,
        OrderFlowDiscoveryEngineContract,
    )
except Exception:
    pass
'''

if "OrderFlowDiscoveryEngineContract" not in existing_oracle_init:
    ORACLE_INIT.write_text(existing_oracle_init.rstrip() + "\n" + ORACLE_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" OFD-001 INSTALLER")
print(" Order Flow Discovery Contract")
print("========================================")
print(f"[OK] Wrote {CONTRACT_FILE}")
print(f"[OK] Wrote {INIT_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {ORACLE_INIT}")
print()
print("[DONE] OFD-001 installed")
print()
print("Run:")
print("py test_ofd_001_order_flow_discovery_contract.py")