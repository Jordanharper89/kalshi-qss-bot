from pathlib import Path

ROOT = Path.cwd()

MODULE_DIR = ROOT / "qseries_v2" / "oracle_intelligence" / "wallet_intelligence_discovery_model"
MODULE_DIR.mkdir(parents=True, exist_ok=True)

GATE_FILE = MODULE_DIR / "wallet_intelligence_discovery_pipeline_gate.py"
TEST_FILE = ROOT / "test_wdm_004_wallet_intelligence_discovery_pipeline_gate.py"
INIT_FILE = MODULE_DIR / "__init__.py"

GATE_CODE = r'''"""
WDM-004 Wallet Intelligence Discovery Pipeline Gate

Read-only integration gate for:
WDM-002 Wallet Intelligence Source Adapter
    -> WDM-003 Wallet Intelligence Discovery Engine
    -> UniversalOpportunity-shaped wallet intelligence output

No signing, fund movement, swaps, routing, trading, or execution.
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
from .wallet_intelligence_source_adapter import WalletIntelligenceSourceAdapter
from .wallet_intelligence_discovery_engine import WalletIntelligenceDiscoveryEngine


SCHEMA_VERSION = "WDM-004"
GATE_ID = "oracle.discovery.gate.wallet_intelligence_pipeline"
GATE_NAME = "Wallet Intelligence Discovery Pipeline Gate"


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
class WalletIntelligenceDiscoveryGateReport:
    schema_version: str
    gate_id: str
    status: str
    passed_checks: int
    failed_checks: int
    warning_count: int
    checks: Mapping[str, bool]
    telemetry: Mapping[str, Any]
    read_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "status": self.status,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warning_count": self.warning_count,
            "checks": dict(self.checks),
            "telemetry": dict(self.telemetry),
            "read_only": self.read_only,
        }


class WalletIntelligenceDiscoveryPipelineGate:
    schema_version = SCHEMA_VERSION
    gate_id = GATE_ID
    gate_name = GATE_NAME
    read_only = True

    def __init__(
        self,
        source_name: str = "wallet_intelligence_gate_source",
        min_wallet_score: float = 0.70,
        min_usd_value: float = 1000.0,
        min_signal_score: float = 0.55,
    ) -> None:
        self.source_name = str(source_name)
        self.min_wallet_score = float(min_wallet_score)
        self.min_usd_value = float(min_usd_value)
        self.min_signal_score = float(min_signal_score)

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "read_only": True,
            "validates": [
                "WDM-002 source adapter",
                "WDM-003 discovery engine",
                "wallet intelligence UniversalMarket shape",
                "wallet intelligence UniversalOpportunity shape",
                "deterministic replay",
                "immutable output",
                "no signing authority",
                "no fund movement authority",
                "no execution authority",
            ],
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
            "gate_id": self.gate_id,
            "status": "ok",
            "ready": True,
            "read_only": True,
            "checked_at": _utc_now_iso(),
        }

    def run(self, raw_records: Sequence[Any] | None = None) -> WalletIntelligenceDiscoveryGateReport:
        started_at = _utc_now_iso()
        raw = tuple(raw_records or self._fixture_records())

        adapter = WalletIntelligenceSourceAdapter(source_name=self.source_name)
        batch_a = adapter.normalize_batch(raw)
        batch_b = adapter.normalize_batch(tuple(reversed(raw)))

        request_a = WalletIntelligenceDiscoveryRequest(
            request_id="wdm004.wallet.pipeline.gate.a",
            family=WalletIntelligenceFamily.SMART_MONEY,
            source_name=self.source_name,
            chains=tuple(sorted({s.chain for s in batch_a.snapshots})),
            wallets=tuple(sorted({s.wallet for s in batch_a.snapshots})),
            symbols=tuple(sorted({s.symbol for s in batch_a.snapshots})),
            metadata={"snapshots": batch_a.snapshots},
        )
        request_b = WalletIntelligenceDiscoveryRequest(
            request_id="wdm004.wallet.pipeline.gate.b",
            family=WalletIntelligenceFamily.SMART_MONEY,
            source_name=self.source_name,
            chains=tuple(sorted({s.chain for s in batch_b.snapshots})),
            wallets=tuple(sorted({s.wallet for s in batch_b.snapshots})),
            symbols=tuple(sorted({s.symbol for s in batch_b.snapshots})),
            metadata={"snapshots": batch_b.snapshots},
        )

        engine = WalletIntelligenceDiscoveryEngine(
            min_wallet_score=self.min_wallet_score,
            min_usd_value=self.min_usd_value,
            min_signal_score=self.min_signal_score,
        )

        report_a = engine.discover(request_a)
        report_b = engine.discover(request_b)

        opportunity_ids_a = tuple(o.opportunity_id for o in report_a.opportunities)
        opportunity_ids_b = tuple(o.opportunity_id for o in report_b.opportunities)

        checks = {
            "gate_is_read_only": self.read_only is True,
            "adapter_is_read_only": adapter.read_only is True,
            "batch_is_read_only": batch_a.read_only is True,
            "engine_is_read_only": engine.read_only is True,
            "discovery_report_is_read_only": report_a.read_only is True,
            "adapter_schema_ok": batch_a.schema_version == "WDM-002",
            "engine_contract_schema_ok": report_a.schema_version == "WDM-001",
            "raw_records_seen": batch_a.telemetry.get("raw_records_seen") == len(raw),
            "snapshots_emitted": len(batch_a.snapshots) == len(raw),
            "wallets_seen": batch_a.telemetry.get("wallets_seen") == 3,
            "adapter_deterministic_order": tuple((s.chain, s.wallet, s.symbol, s.tx_hash) for s in batch_a.snapshots)
            == tuple((s.chain, s.wallet, s.symbol, s.tx_hash) for s in batch_b.snapshots),
            "engine_emits_opportunities": len(report_a.opportunities) == 2,
            "engine_replay_deterministic": opportunity_ids_a == opportunity_ids_b,
            "all_opportunities_read_only": all(o.read_only is True for o in report_a.opportunities),
            "all_opportunities_have_ids": all(bool(o.opportunity_id) for o in report_a.opportunities),
            "all_opportunities_have_wallet": all(bool(o.wallet) for o in report_a.opportunities),
            "all_opportunities_have_chain": all(bool(o.chain) for o in report_a.opportunities),
            "all_opportunities_have_symbol": all(bool(o.symbol) for o in report_a.opportunities),
            "all_opportunities_have_signal": all(bool(o.signal_type) for o in report_a.opportunities),
            "all_opportunities_have_signal_score": all(
                o.signal_score >= self.min_signal_score for o in report_a.opportunities
            ),
            "all_opportunities_have_confidence": all(
                0.0 <= o.confidence <= 1.0 for o in report_a.opportunities
            ),
            "all_opportunities_have_explanation": all(
                bool(o.explanation) for o in report_a.opportunities
            ),
            "all_opportunities_have_telemetry": all(
                bool(o.telemetry) for o in report_a.opportunities
            ),
            "universal_market_shape": all(
                o.universal_market.get("market_type") == "wallet_intelligence"
                and o.universal_market.get("read_only") is True
                and o.universal_market.get("execution_allowed") is False
                and o.universal_market.get("signing_allowed") is False
                and o.universal_market.get("fund_movement_allowed") is False
                for o in report_a.opportunities
            ),
            "source_engine_id_present": all(
                o.source_engine_id == "oracle.discovery.wallet_intelligence"
                for o in report_a.opportunities
            ),
            "telemetry_present": bool(batch_a.telemetry) and bool(report_a.telemetry),
            "no_execution_fields": all(
                not hasattr(o, "order_id")
                and not hasattr(o, "position_size")
                and not hasattr(o, "execution_id")
                and not hasattr(o, "signature")
                and not hasattr(o, "private_key")
                for o in report_a.opportunities
            ),
            "immutable_universal_market": self._check_immutable_market(report_a),
        }

        passed = sum(1 for ok in checks.values() if ok)
        failed = sum(1 for ok in checks.values() if not ok)

        telemetry = MappingProxyType(
            {
                "schema_version": self.schema_version,
                "gate_id": self.gate_id,
                "started_at": started_at,
                "completed_at": _utc_now_iso(),
                "raw_records_seen": len(raw),
                "snapshots_emitted": len(batch_a.snapshots),
                "wallets_seen": batch_a.telemetry.get("wallets_seen"),
                "opportunities_emitted": len(report_a.opportunities),
                "adapter_schema_version": batch_a.schema_version,
                "engine_contract_schema_version": report_a.schema_version,
                "passed_checks": passed,
                "failed_checks": failed,
                "warning_count": 0,
                "read_only": True,
                "execution_allowed": False,
                "signing_allowed": False,
                "fund_movement_allowed": False,
                "swap_allowed": False,
                "deterministic_replay": opportunity_ids_a == opportunity_ids_b,
            }
        )

        return WalletIntelligenceDiscoveryGateReport(
            schema_version=self.schema_version,
            gate_id=self.gate_id,
            status="passed" if failed == 0 else "failed",
            passed_checks=passed,
            failed_checks=failed,
            warning_count=0,
            checks=_freeze(checks),
            telemetry=telemetry,
            read_only=True,
        )

    def _check_immutable_market(self, report: Any) -> bool:
        if not report.opportunities:
            return False
        try:
            report.opportunities[0].universal_market["execution_allowed"] = True
            return False
        except TypeError:
            return True

    def _fixture_records(self) -> Tuple[Mapping[str, Any], ...]:
        return (
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
        )


__all__ = [
    "SCHEMA_VERSION",
    "GATE_ID",
    "GATE_NAME",
    "WalletIntelligenceDiscoveryGateReport",
    "WalletIntelligenceDiscoveryPipelineGate",
]
'''

TEST_CODE = r'''from qseries_v2.oracle_intelligence.wallet_intelligence_discovery_model.wallet_intelligence_discovery_pipeline_gate import (
    WalletIntelligenceDiscoveryPipelineGate,
)


def test_wdm_004_wallet_intelligence_discovery_pipeline_gate():
    gate = WalletIntelligenceDiscoveryPipelineGate(
        source_name="wdm_004_test_source",
        min_wallet_score=0.70,
        min_usd_value=1000,
        min_signal_score=0.55,
    )

    caps = gate.capabilities()
    health = gate.health()
    report = gate.run()

    assert caps["read_only"] is True
    assert caps["execution"] is False
    assert caps["signing_allowed"] is False
    assert caps["fund_movement_allowed"] is False
    assert caps["swap_allowed"] is False
    assert caps["deterministic"] is True

    assert health["status"] == "ok"
    assert health["read_only"] is True

    assert report.schema_version == "WDM-004"
    assert report.gate_id == "oracle.discovery.gate.wallet_intelligence_pipeline"
    assert report.status == "passed"
    assert report.failed_checks == 0
    assert report.warning_count == 0
    assert report.read_only is True

    assert report.passed_checks >= 25
    assert report.checks["gate_is_read_only"] is True
    assert report.checks["adapter_is_read_only"] is True
    assert report.checks["engine_is_read_only"] is True
    assert report.checks["adapter_schema_ok"] is True
    assert report.checks["engine_contract_schema_ok"] is True
    assert report.checks["adapter_deterministic_order"] is True
    assert report.checks["engine_replay_deterministic"] is True
    assert report.checks["universal_market_shape"] is True
    assert report.checks["source_engine_id_present"] is True
    assert report.checks["no_execution_fields"] is True
    assert report.checks["immutable_universal_market"] is True

    d = report.to_dict()
    assert d["schema_version"] == "WDM-004"
    assert d["status"] == "passed"
    assert d["telemetry"]["raw_records_seen"] == 3
    assert d["telemetry"]["snapshots_emitted"] == 3
    assert d["telemetry"]["wallets_seen"] == 3
    assert d["telemetry"]["opportunities_emitted"] == 2
    assert d["telemetry"]["read_only"] is True
    assert d["telemetry"]["execution_allowed"] is False
    assert d["telemetry"]["signing_allowed"] is False
    assert d["telemetry"]["fund_movement_allowed"] is False
    assert d["telemetry"]["deterministic_replay"] is True

    print("[PASS] WDM-004 Wallet Intelligence Discovery Pipeline Gate")
    print(
        {
            "schema_version": d["schema_version"],
            "gate_id": d["gate_id"],
            "status": d["status"],
            "passed_checks": d["passed_checks"],
            "failed_checks": d["failed_checks"],
            "opportunities": d["telemetry"]["opportunities_emitted"],
            "read_only": d["read_only"],
        }
    )


if __name__ == "__main__":
    test_wdm_004_wallet_intelligence_discovery_pipeline_gate()
'''

INIT_EXPORT = '''
try:
    from .wallet_intelligence_discovery_pipeline_gate import (
        WalletIntelligenceDiscoveryPipelineGate,
        WalletIntelligenceDiscoveryGateReport,
    )
except Exception:
    pass
'''

GATE_FILE.write_text(GATE_CODE, encoding="utf-8")
TEST_FILE.write_text(TEST_CODE, encoding="utf-8")

existing_init = INIT_FILE.read_text(encoding="utf-8") if INIT_FILE.exists() else ""
if "WalletIntelligenceDiscoveryPipelineGate" not in existing_init:
    INIT_FILE.write_text(existing_init.rstrip() + "\n" + INIT_EXPORT.lstrip(), encoding="utf-8")

print("========================================")
print(" WDM-004 INSTALLER")
print(" Wallet Intelligence Discovery Pipeline Gate")
print("========================================")
print(f"[OK] Wrote {GATE_FILE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT_FILE}")
print()
print("[DONE] WDM-004 installed")
print()
print("Run:")
print("py test_wdm_004_wallet_intelligence_discovery_pipeline_gate.py")