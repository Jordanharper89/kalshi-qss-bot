from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "solana_launch_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_FILE = MODULE_DIR / "solana_launch_discovery_registry_bridge.py"
TEST_FILE = ROOT / "test_sld_005_solana_launch_discovery_registry_bridge.py"
INIT_FILE = MODULE_DIR / "__init__.py"

BRIDGE_CODE = r'''"""
SLD-005 Solana Launch Discovery Registry Bridge

Read-only bridge from SLD-003 Solana launch discovery output to
registry-ready immutable records for the Opportunity Operating System lane.

No signing, fund movement, swaps, sniping, routing, buying, selling, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Dict, Mapping, Sequence, Tuple

from .solana_launch_discovery_contract import (
    SolanaLaunchDiscoveryFamily,
    SolanaLaunchDiscoveryRequest,
)
from .solana_launch_discovery_engine import SolanaLaunchDiscoveryEngine


SCHEMA_VERSION = "SLD-005"
BRIDGE_ID = "oracle.discovery.bridge.solana_launch_registry"
BRIDGE_NAME = "Solana Launch Discovery Registry Bridge"


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
class SolanaLaunchRegistryRecord:
    schema_version: str
    bridge_id: str
    opportunity_id: str
    mint: str
    symbol: str
    opportunity_type: str
    source_engine_id: str
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
            "mint": self.mint,
            "symbol": self.symbol,
            "opportunity_type": self.opportunity_type,
            "source_engine_id": self.source_engine_id,
            "registry_status": self.registry_status,
            "registry_key": self.registry_key,
            "payload": dict(self.payload),
            "audit": dict(self.audit),
            "read_only": self.read_only,
        }


@dataclass(frozen=True)
class SolanaLaunchRegistryBridgeReport:
    schema_version: str
    bridge_id: str
    status: str
    records: Tuple[SolanaLaunchRegistryRecord, ...]
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


class SolanaLaunchDiscoveryRegistryBridge:
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
            "accepts": "SLD-003 SolanaLaunchDiscoveryResult",
            "emits": "registry-ready immutable Solana launch records",
            "compatible_with": ["OOS-001 Registry", "OOS-003 Pipeline"],
            "deterministic": True,
            "telemetry": True,
            "execution": False,
            "signing_allowed": False,
            "fund_movement_allowed": False,
            "swap_allowed": False,
            "snipe_allowed": False,
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

    def bridge_report(self, discovery_report: Any) -> SolanaLaunchRegistryBridgeReport:
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
                "snipe_allowed": False,
            }
        )

        return SolanaLaunchRegistryBridgeReport(
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
        source_name: str = "solana_launch_registry_bridge_source",
        min_liquidity_usd: float = 1000.0,
        max_age_seconds: float = 600.0,
        min_launch_score: float = 0.55,
    ) -> SolanaLaunchRegistryBridgeReport:
        request = SolanaLaunchDiscoveryRequest(
            request_id="sld005.solana.launch.registry.bridge",
            family=SolanaLaunchDiscoveryFamily.NEW_TOKEN_LAUNCH,
            source_name=source_name,
            metadata={"raw_records": tuple(raw_records or ())},
        )

        engine = SolanaLaunchDiscoveryEngine(
            min_liquidity_usd=min_liquidity_usd,
            max_age_seconds=max_age_seconds,
            min_launch_score=min_launch_score,
        )
        discovery_report = engine.discover(request)
        return self.bridge_report(discovery_report)

    def _record_from_opportunity(self, opportunity: Any) -> SolanaLaunchRegistryRecord:
        opportunity_id = str(getattr(opportunity, "opportunity_id"))
        mint = str(getattr(opportunity, "mint"))
        symbol = str(getattr(opportunity, "symbol"))
        opportunity_type = str(getattr(opportunity, "opportunity_type"))
        source_engine_id = str(getattr(opportunity, "source_engine_id"))

        registry_key = f"{source_engine_id}:{opportunity_type}:{symbol}:{mint}:{opportunity_id}"

        payload = MappingProxyType(
            {
                "opportunity_id": opportunity_id,
                "mint": mint,
                "symbol": symbol,
                "opportunity_type": opportunity_type,
                "source_engine_id": source_engine_id,
                "launch_score": getattr(opportunity, "launch_score", None),
                "safety_score": getattr(opportunity, "safety_score", None),
                "liquidity_score": getattr(opportunity, "liquidity_score", None),
                "momentum_score": getattr(opportunity, "momentum_score", None),
                "confidence": getattr(opportunity, "confidence", None),
                "liquidity_usd": getattr(opportunity, "liquidity_usd", None),
                "age_seconds": getattr(opportunity, "age_seconds", None),
                "status": getattr(opportunity, "status", None),
                "universal_market": _freeze(getattr(opportunity, "universal_market", {})),
                "explanation": _freeze(getattr(opportunity, "explanation", {})),
                "telemetry": _freeze(getattr(opportunity, "telemetry", {})),
                "read_only": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "snipe_allowed": False,
            }
        )

        audit = MappingProxyType(
            {
                "bridge_schema_version": self.schema_version,
                "bridge_id": self.bridge_id,
                "registered_from": "SLD Solana launch discovery",
                "created_at": _utc_now_iso(),
                "oracle_read_only": True,
                "execution_fields_present": False,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "snipe_allowed": False,
            }
        )

        return SolanaLaunchRegistryRecord(
            schema_version=self.schema_version,
            bridge_id=self.bridge_id,
            opportunity_id=opportunity_id,
            mint=mint,
            symbol=symbol,
            opportunity_type=opportunity_type,
            source_engine_id=source_engine_id,
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
    "SolanaLaunchRegistryRecord",
    "SolanaLaunchRegistryBridgeReport",
    "SolanaLaunchDiscoveryRegistryBridge",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.solana_launch_discovery_model.solana_launch_discovery_registry_bridge import (
    SolanaLaunchDiscoveryRegistryBridge,
)


def test_sld_005_solana_launch_discovery_registry_bridge():
    raw_records = [
        {
            "token_mint": "mint_a",
            "ticker": "ALPHA",
            "name": "Alpha Token",
            "pool_address": "pool_a",
            "dex": "raydium",
            "quote_asset": "SOL",
            "liquidity_usd": 50000,
            "market_cap_usd": 200000,
            "volume_5m_usd": 15000,
            "holder_count": 250,
            "age_seconds": 30,
            "mint_authority_disabled": True,
            "freeze_authority_disabled": True,
            "lp_burned": True,
            "pool_status": "active",
            "deployer_wallet": "wallet_a",
            "tx_signature": "tx_a",
            "detected_at": "2026-01-01T00:01:00Z",
        },
        {
            "mint": "mint_b",
            "symbol": "BETA",
            "name": "Beta Token",
            "pool": "pool_b",
            "dex": "Raydium",
            "quote": "SOL",
            "liquidity": 25000,
            "market_cap": 120000,
            "volume_5m": 8000,
            "holders": 120,
            "age": 90,
            "mint_disabled": True,
            "freeze_disabled": True,
            "liquidity_burned": True,
            "status": "active",
            "creator": "wallet_b",
            "signature": "tx_b",
            "timestamp": "2026-01-01T00:02:00Z",
        },
        {
            "mint": "mint_bad",
            "symbol": "BAD",
            "pool": "pool_bad",
            "liquidity": 100,
            "age": 900,
            "mint_disabled": False,
            "freeze_disabled": False,
            "liquidity_burned": False,
            "status": "active",
        },
    ]

    bridge = SolanaLaunchDiscoveryRegistryBridge()
    caps = bridge.capabilities()
    health = bridge.health()

    report_a = bridge.discover_and_bridge(
        raw_records,
        source_name="sld_005_test_source",
        min_liquidity_usd=1000,
        max_age_seconds=600,
        min_launch_score=0.55,
    )
    report_b = bridge.discover_and_bridge(
        list(reversed(raw_records)),
        source_name="sld_005_test_source",
        min_liquidity_usd=1000,
        max_age_seconds=600,
        min_launch_score=0.55,
    )

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["signing_allowed"] is False
    assert caps["fund_movement_allowed"] is False
    assert caps["swap_allowed"] is False
    assert caps["snipe_allowed"] is False
    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report_a.schema_version == "SLD-005"
    assert report_a.bridge_id == "oracle.discovery.bridge.solana_launch_registry"
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
    assert first.payload["snipe_allowed"] is False
    assert first.audit["oracle_read_only"] is True
    assert first.audit["execution_fields_present"] is False
    assert first.audit["execution_allowed"] is False
    assert first.payload["universal_market"]["market_type"] == "solana_launch"

    try:
        first.payload["execution_allowed"] = True
        raise AssertionError("registry payload should be immutable")
    except TypeError:
        pass

    d = report_a.to_dict()
    assert d["schema_version"] == "SLD-005"
    assert d["read_only"] is True
    assert d["telemetry"]["opportunities_seen"] == 2
    assert d["telemetry"]["records_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["signing_allowed"] is False
    assert d["telemetry"]["fund_movement_allowed"] is False
    assert d["telemetry"]["swap_allowed"] is False
    assert d["telemetry"]["snipe_allowed"] is False

    print("[PASS] SLD-005 Solana Launch Discovery Registry Bridge")
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
    test_sld_005_solana_launch_discovery_registry_bridge()
'''

INIT_EXPORT = '''
try:
    from .solana_launch_discovery_registry_bridge import (
        SolanaLaunchDiscoveryRegistryBridge,
        SolanaLaunchRegistryBridgeReport,
        SolanaLaunchRegistryRecord,
    )
except Exception:
    pass
'''

BRIDGE_FILE.write_text(BRIDGE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "SolanaLaunchDiscoveryRegistryBridge" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" SLD-005 INSTALLER")
print(" Solana Launch Discovery Registry Bridge")
print("========================================")
print(f"[OK] Wrote {BRIDGE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] SLD-005 installed")
print()
print("Run:")
print("py test_sld_005_solana_launch_discovery_registry_bridge.py")