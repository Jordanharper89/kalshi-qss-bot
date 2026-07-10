from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "wallet_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "wallet_intelligence_discovery_registry_bridge.py"
TEST_FILE = ROOT / "test_wdm_005_wallet_intelligence_discovery_registry_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''"""
WDM-005 Wallet Intelligence Discovery Registry Bridge

Read-only bridge from WDM-003 wallet intelligence discovery output to
registry-ready immutable records for the Opportunity Operating System lane.

No signing, fund movement, swaps, trading, routing, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .wallet_intelligence_discovery_contract import (
    WalletIntelligenceDiscoveryRequest,
    WalletIntelligenceFamily,
)
from .wallet_intelligence_discovery_engine import WalletIntelligenceDiscoveryEngine


SCHEMA_VERSION = "WDM-005"
BRIDGE_ID = "oracle.discovery.bridge.wallet_intelligence_registry"
BRIDGE_NAME = "Wallet Intelligence Discovery Registry Bridge"


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


@dataclass(frozen=True)
class WalletIntelligenceRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    wallet: str
    chain: str
    symbol: str
    opportunity_type: str
    source_engine_id: str
    signal_type: str
    registry_status: str
    registry_key: str
    payload: Mapping[str, Any]
    audit: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "opportunity_id": self.opportunity_id,
            "wallet": self.wallet,
            "chain": self.chain,
            "symbol": self.symbol,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "signal_type": self.signal_type,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class WalletIntelligenceRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[WalletIntelligenceRegistryRecord, ...]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "status": self.status,
            "records": [r.to_dict() for r in self.records],
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class WalletIntelligenceDiscoveryRegistryBridge:
    schema_version = SCHEMA_VERSION
    bridge_id = BRIDGE_ID
    bridge_name = BRIDGE_NAME
    read_only = True

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "bridge_name": self.bridge_name,
            "read_only": True,
            "accepts": "WDM-003 WalletIntelligenceDiscoveryResult",
            "emits": "registry-ready immutable wallet intelligence records",
            "compatible_with": ["OOS-001 Registry", "OOS-003 Pipeline"],
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
        }

    def health(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bridge_id": self.bridge_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def bridge_report(self, discovery_report: Any) -> WalletIntelligenceRegistryBridgeReport:
        started_at = _utc_now_iso()
        opportunities = tuple(getattr(discovery_report, "opportunities", ()) or ())

        records = tuple(
            sorted(
                (self._record_from_opportunity(o) for o in opportunities),
                key=lambda r: (r.registry_key, r.opportunity_id),
            )
        )

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "opportunities_seen": len(opportunities),
                "records_emitted": len(records),
                "read_only": True,
                "deterministic_sort": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
            }
        )

        return WalletIntelligenceRegistryBridgeReport(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            status="passed" if records else "empty",
            records=records,
            telemetry=telemetry,
            read_only=True,
        )

    def discover_and_bridge(
        self,
        raw_records: Sequence[Any],
        source_name: str = "wallet_intelligence_registry_bridge_source",
        min_wallet_score: float = 0.70,
        min_usd_value: float = 1000.0,
        min_signal_score: float = 0.55,
    ) -> WalletIntelligenceRegistryBridgeReport:
        request = WalletIntelligenceDiscoveryRequest(
            request_id="wdm005.wallet.intelligence.registry.bridge",
            family=WalletIntelligenceFamily.SMART_MONEY,
            source_name=source_name,
            metadata={"raw_records": tuple(raw_records or ())},
        )

        engine = WalletIntelligenceDiscoveryEngine(
            min_wallet_score=min_wallet_score,
            min_usd_value=min_usd_value,
            min_signal_score=min_signal_score,
        )
        discovery_report = engine.discover(request)
        return self.bridge_report(discovery_report)

    def _record_from_opportunity(self, opportunity: Any) -> WalletIntelligenceRegistryRecord:
        opportunity_id = str(getattr(opportunity, "opportunity_id"))
        wallet = str(getattr(opportunity, "wallet"))
        chain = str(getattr(opportunity, "chain"))
        symbol = str(getattr(opportunity, "symbol"))
        opportunity_type = str(getattr(opportunity, "opportunity_type"))
        source_engine_id = str(getattr(opportunity, "source_engine_id"))
        signal_type = str(getattr(opportunity, "signal_type"))

        registry_key = (
            f"{source_engine_id}:{opportunity_type}:{chain}:"
            f"{wallet}:{symbol}:{signal_type}:{opportunity_id}"
        )

        payload = MappingProxyType(
            {
                "opportunity_id": opportunity_id,
                "wallet": wallet,
                "chain": chain,
                "symbol": symbol,
                "opportunity_type": opportunity_type,
                "source_engine_id": source_engine_id,
                "signal_type": signal_type,
                "signal_score": getattr(opportunity, "signal_score", None),
                "confidence": getattr(opportunity, "confidence", None),
                "usd_value": getattr(opportunity, "usd_value", None),
                "wallet_score": getattr(opportunity, "wallet_score", None),
                "status": getattr(opportunity, "status", None),
                "universal_market": _freeze(getattr(opportunity, "universal_market", {})),
                "explanation": _freeze(getattr(opportunity, "explanation", {})),
                "telemetry": _freeze(getattr(opportunity, "telemetry", {})),
                "read_only": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
            }
        )

        audit = MappingProxyType(
            {
                "bridge_schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "registered_from": "WDM wallet intelligence discovery",
                "created_at": _utc_now_iso(),
                "oracle_read_only": True,
                "execution_fields_present": False,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
            }
        )

        return WalletIntelligenceRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            wallet=wallet,
            chain=chain,
            symbol=symbol,
            opportunity_type=opportunity_type,
            source_engine_id=source_engine_id,
            signal_type=signal_type,
            registry_status="registry_ready",
            registry_key=registry_key,
            payload=payload,
            audit=audit,
            read_only=True,
        )


__all__ = [
    "SCHEMA_VERSION",
    "BRIDGE_ID",
    "BRIDGE_NAME",
    "WalletIntelligenceRegistryRecord",
    "WalletIntelligenceRegistryBridgeReport",
    "WalletIntelligenceDiscoveryRegistryBridge",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.wallet_intelligence_discovery_model.wallet_intelligence_discovery_registry_bridge import (
    WalletIntelligenceDiscoveryRegistryBridge,
)


def test_wdm_005_wallet_intelligence_discovery_registry_bridge():
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

    bridge = WalletIntelligenceDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_and_bridge(
        raw_records,
        source_name="wdm_005_test_source",
        min_wallet_score=0.70,
        min_usd_value=1000,
        min_signal_score=0.55,
    )
    report_b = bridge.discover_and_bridge(
        list(reversed(raw_records)),
        source_name="wdm_005_test_source",
        min_wallet_score=0.70,
        min_usd_value=1000,
        min_signal_score=0.55,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["signing_allowed"] is False
    assert caps["fund_movement_allowed"] is False
    assert caps["swap_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "WDM-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.wallet_intelligence_registry"
    assert report_a.status == "passed"
    assert report_a.read_only is True
    assert len(report_a.records) == 2

    keys_a = [r.registry_key for r in report_a.records]
    keys_b = [r.registry_key for r in report_b.records]
    assert keys_a == keys_b

    first = report_a.records[0]
    assert first.read_only is True
    assert first.registry_status == "registry_ready"
    assert first.payload["read_only"] is True
    assert first.payload["execution_allowed"] is False
    assert first.payload["signing_allowed"] is False
    assert first.payload["fund_movement_allowed"] is False
    assert first.payload["swap_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["execution_allowed"] is False
    assert first.payload["universal_market"]["market_type"] == "wallet_intelligence"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("registry payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "WDM-005"
    assert d["read_only"] is True
    assert d["telemetry"]["opportunities_seen"] == 2
    assert d["telemetry"]["records_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["signing_allowed"] is False
    assert d["telemetry"]["fund_movement_allowed"] is False

    print("[PASS] WDM-005 Wallet Intelligence Discovery Registry Bridge")
    print(
        {
            "schema_version": d["schema_version"],
            "bridge_id": d["bridge_id"],
            "status": d["status"],
            "records": len(d["records"]),
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_wdm_005_wallet_intelligence_discovery_registry_bridge()
'''

INIT_EXPORT = '''
try:
    from .wallet_intelligence_discovery_registry_bridge import (
        WalletIntelligenceDiscoveryRegistryBridge,
        WalletIntelligenceRegistryBridgeReport,
        WalletIntelligenceRegistryRecord,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "WalletIntelligenceDiscoveryRegistryBridge" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" WDM-005 INSTALLER")
print(" Wallet Intelligence Discovery Registry Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] WDM-005 installed")
print()
print("Run:")
print("py test_wdm_005_wallet_intelligence_discovery_registry_bridge.py")