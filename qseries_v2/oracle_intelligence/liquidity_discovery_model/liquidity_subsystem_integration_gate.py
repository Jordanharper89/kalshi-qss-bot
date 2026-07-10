
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .liquidity_discovery_contract import empty_liquidity_discovery_result
from .liquidity_discovery_engine import discover_liquidity_opportunities
from .liquidity_oos_runtime_gate import validate_liquidity_oos_runtime
from .liquidity_pipeline_bridge import run_liquidity_pipeline
from .liquidity_pipeline_gate import validate_liquidity_discovery_result
from .liquidity_registry_bridge import bridge_liquidity_registry
from .liquidity_replay_ledger import LiquidityReplayLedgerBuilder
from .liquidity_source_adapter import build_liquidity_source_snapshot


READ_ONLY = True
SCHEMA_VERSION = "LQD-009"
ENGINE_ID = "oracle.discovery.liquidity.subsystem_integration_gate"


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _deep_sort(value[k]) for k in sorted(value.keys(), key=str)}
    if isinstance(value, list):
        return [_deep_sort(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(v) for v in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    return sha256(repr(_deep_sort(payload)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LiquiditySubsystemIntegrationResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    reason: str
    contract_hash: str
    source_snapshot_hash: str
    discovery_result_hash: str
    gate_hash: str
    registry_hash: str
    pipeline_hash: str
    oos_hash: str
    replay_ledger_hash: str
    opportunity_count: int
    checks: Dict[str, bool] = field(default_factory=dict)
    audit: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True
    integration_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class LiquiditySubsystemIntegrationGate:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def run(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        source_name: str = "liquidity.integration",
        observed_at: Optional[str] = None,
        runtime_context: Optional[Mapping[str, Any]] = None,
    ) -> LiquiditySubsystemIntegrationResult:
        raw_list = list(raw_records or [])
        context = dict(runtime_context or {"mode": "oos", "fold": "integration"})

        contract = empty_liquidity_discovery_result()

        source_snapshot = build_liquidity_source_snapshot(
            raw_records=raw_list,
            source_name=source_name,
            observed_at=observed_at,
        )

        discovery = discover_liquidity_opportunities(
            raw_records=raw_list,
            source_name=source_name,
            observed_at=observed_at,
            min_spread_bps=250,
            max_total_depth=1000,
            min_depth_imbalance=0.30,
        )

        gate = validate_liquidity_discovery_result(discovery)
        registry = bridge_liquidity_registry(gate)

        pipeline = run_liquidity_pipeline(
            raw_records=raw_list,
            source_name=source_name,
            observed_at=observed_at,
            min_spread_bps=250,
            max_total_depth=1000,
            min_depth_imbalance=0.30,
        )

        oos = validate_liquidity_oos_runtime(
            pipeline_result=pipeline,
            runtime_context=context,
        )

        ledger_builder = LiquidityReplayLedgerBuilder()
        ledger = ledger_builder.build([oos])
        ledger_validation = ledger_builder.validate(ledger)

        checks = {
            "read_only": all([
                contract.read_only,
                source_snapshot.read_only,
                discovery.read_only,
                gate.read_only,
                registry.read_only,
                pipeline.read_only,
                oos.read_only,
                ledger.read_only,
            ]),
            "contract_schema": contract.schema_version == "LQD-001",
            "source_schema": source_snapshot.schema_version == "LQD-002",
            "discovery_schema": discovery.schema_version == "LQD-003",
            "gate_schema": gate.schema_version == "LQD-004",
            "registry_schema": registry.schema_version == "LQD-005",
            "pipeline_schema": pipeline.schema_version == "LQD-006",
            "oos_schema": oos.schema_version == "LQD-007",
            "ledger_schema": ledger.schema_version == "LQD-008",
            "discovery_count_matches_pipeline": discovery.opportunity_count == pipeline.opportunity_count,
            "pipeline_count_matches_oos": pipeline.opportunity_count == oos.opportunity_count,
            "ledger_has_one_entry": ledger.entry_count == 1,
            "ledger_validation_accepted": ledger_validation["accepted"] is True,
            "gate_accepted": gate.accepted is True,
            "registry_accepted": registry.accepted is True,
            "pipeline_accepted": pipeline.accepted is True,
            "oos_accepted": oos.accepted is True,
            "hashes_present": all([
                contract.result_hash,
                source_snapshot.snapshot_hash,
                discovery.result_hash,
                gate.gate_hash,
                registry.registry_hash,
                pipeline.pipeline_hash,
                oos.oos_hash,
                ledger.ledger_hash,
            ]),
        }

        accepted = all(checks.values())
        status = "accepted" if accepted else "rejected"
        failed = [name for name, passed in checks.items() if not passed]
        reason = "liquidity subsystem integration checks passed" if accepted else "failed checks: " + ", ".join(failed)

        audit = {
            "read_only": True,
            "deterministic": True,
            "replayable": True,
            "immutable": True,
            "subsystem": "liquidity_discovery",
            "modules": [
                "LQD-001 contract",
                "LQD-002 source_adapter",
                "LQD-003 discovery_engine",
                "LQD-004 pipeline_gate",
                "LQD-005 registry_bridge",
                "LQD-006 pipeline_bridge",
                "LQD-007 oos_runtime_gate",
                "LQD-008 replay_ledger",
                "LQD-009 subsystem_integration_gate",
            ],
            "ledger_validation": ledger_validation,
        }

        unsigned = LiquiditySubsystemIntegrationResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            reason=reason,
            contract_hash=contract.result_hash,
            source_snapshot_hash=source_snapshot.snapshot_hash,
            discovery_result_hash=discovery.result_hash,
            gate_hash=gate.gate_hash,
            registry_hash=registry.registry_hash,
            pipeline_hash=pipeline.pipeline_hash,
            oos_hash=oos.oos_hash,
            replay_ledger_hash=ledger.ledger_hash,
            opportunity_count=discovery.opportunity_count,
            checks=checks,
            audit=audit,
            read_only=True,
            integration_hash="",
        )

        return LiquiditySubsystemIntegrationResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            reason=unsigned.reason,
            contract_hash=unsigned.contract_hash,
            source_snapshot_hash=unsigned.source_snapshot_hash,
            discovery_result_hash=unsigned.discovery_result_hash,
            gate_hash=unsigned.gate_hash,
            registry_hash=unsigned.registry_hash,
            pipeline_hash=unsigned.pipeline_hash,
            oos_hash=unsigned.oos_hash,
            replay_ledger_hash=unsigned.replay_ledger_hash,
            opportunity_count=unsigned.opportunity_count,
            checks=unsigned.checks,
            audit=unsigned.audit,
            read_only=True,
            integration_hash=_stable_hash(unsigned.canonical()),
        )

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def run_liquidity_subsystem_integration_gate(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "liquidity.integration",
    observed_at: Optional[str] = None,
    runtime_context: Optional[Mapping[str, Any]] = None,
) -> LiquiditySubsystemIntegrationResult:
    return LiquiditySubsystemIntegrationGate().run(
        raw_records=raw_records,
        source_name=source_name,
        observed_at=observed_at,
        runtime_context=runtime_context,
    )
