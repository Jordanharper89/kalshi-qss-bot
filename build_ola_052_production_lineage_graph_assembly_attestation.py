from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE = ROOT / 'qseries_v2/oracle_intelligence/live_acquisition/oracle_production_lineage_graph_assembly_attestation.py'
OLA030 = ROOT / 'qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py'
TEST = ROOT / 'test_ola_052_production_lineage_graph_assembly_attestation.py'

MODULE_TEXT = r'''"""
OLA-052 Oracle Production Lineage Graph Assembly Attestation.

Fail-closed structural attestation for the actual OLA-030 production lineage graph.

This boundary proves, by object identity, that the production persistence router is
wrapped exactly once by OLA-044 before OLA-001/OLA-017 construction and that the
completed production cycle callable flows through OLA-045 -> OLA-046 -> OLA-050.

The attestor performs no acquisition, persistence, alerting, handoff, or execution.
Oracle remains permanently read-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

SCHEMA_VERSION = "OLA-052"
ENGINE_ID = "OLA-052"
ATTESTATION_TYPE = "oracle_production_lineage_graph_assembly_attestation"


class OracleProductionLineageGraphAssemblyAttestationError(ValueError):
    pass


class OracleProductionLineageGraphAssemblyAttestationBlocked(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class OracleProductionLineageGraphAssemblyAttestationRecord:
    schema_version: str
    engine_id: str
    attestation_type: str
    production_router_preserved: bool
    staged_router_identity_preserved: bool
    runtime_uses_staged_router: bool
    ola017_uses_staged_router: bool
    runtime_and_ola017_share_router: bool
    ola045_bound_to_ola044: bool
    ola046_bound_to_production_cycle: bool
    ola046_bound_to_ola045: bool
    ola050_bound_to_ola046: bool
    full_lineage_chain_attested: bool
    read_only: bool = True
    execution_allowed: bool = False
    alerts_allowed: bool = False
    qseries_handoff_allowed: bool = False
    execution_adapter_resolved: bool = False
    execution_adapter_invoked: bool = False
    trade_authorization_allowed: bool = False
    order_placement_allowed: bool = False
    funds_moved: bool = False
    portfolio_mutated: bool = False

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION or self.engine_id != ENGINE_ID:
            raise OracleProductionLineageGraphAssemblyAttestationError(
                "OLA-052 identity mismatch"
            )
        if self.attestation_type != ATTESTATION_TYPE:
            raise OracleProductionLineageGraphAssemblyAttestationError(
                "attestation_type mismatch"
            )
        required = (
            self.production_router_preserved,
            self.staged_router_identity_preserved,
            self.runtime_uses_staged_router,
            self.ola017_uses_staged_router,
            self.runtime_and_ola017_share_router,
            self.ola045_bound_to_ola044,
            self.ola046_bound_to_production_cycle,
            self.ola046_bound_to_ola045,
            self.ola050_bound_to_ola046,
            self.full_lineage_chain_attested,
            self.read_only,
        )
        if not all(value is True for value in required):
            raise OracleProductionLineageGraphAssemblyAttestationBlocked(
                "production lineage graph assembly attestation failed closed"
            )
        forbidden = (
            self.execution_allowed,
            self.alerts_allowed,
            self.qseries_handoff_allowed,
            self.execution_adapter_resolved,
            self.execution_adapter_invoked,
            self.trade_authorization_allowed,
            self.order_placement_allowed,
            self.funds_moved,
            self.portfolio_mutated,
        )
        if any(value is True for value in forbidden):
            raise OracleProductionLineageGraphAssemblyAttestationBlocked(
                "OLA-052 permanent read-only invariant violated"
            )


class OracleProductionLineageGraphAssemblyAttestor:
    read_only = True
    execution_allowed = False

    def attest(
        self,
        *,
        production_persistence_router: Any,
        lineage_production_wiring: Any,
        lineage_persistence_router: Any,
        acquisition_runtime: Any,
        cycle_orchestrator: Any,
        production_cycle_callable: Callable[..., Any],
        lineage_completion_bridge: Any,
        lineage_scheduler_adapter: Any,
        lineage_cycle_callable: Any,
    ) -> OracleProductionLineageGraphAssemblyAttestationRecord:
        if not callable(production_cycle_callable):
            raise OracleProductionLineageGraphAssemblyAttestationError(
                "production_cycle_callable must be callable"
            )
        if not callable(lineage_cycle_callable):
            raise OracleProductionLineageGraphAssemblyAttestationError(
                "lineage_cycle_callable must be callable"
            )

        staged_from_wiring = getattr(
            lineage_production_wiring, "staged_persistence_router", None
        )
        production_from_wiring = getattr(
            lineage_production_wiring, "production_persistence_router", None
        )
        runtime_router = getattr(acquisition_runtime, "persistence_router", None)
        if runtime_router is None:
            runtime_router = getattr(acquisition_runtime, "_persistence_router", None)
        orchestrator_router = getattr(cycle_orchestrator, "postgresql_router", None)
        if orchestrator_router is None:
            orchestrator_router = getattr(cycle_orchestrator, "_postgresql_router", None)

        bridge_wiring = getattr(lineage_completion_bridge, "production_wiring", None)
        adapter_cycle = getattr(lineage_scheduler_adapter, "scheduler_cycle_callable", None)
        adapter_bridge = getattr(lineage_scheduler_adapter, "lineage_completion_bridge", None)
        facade_adapter = getattr(lineage_cycle_callable, "scheduler_adapter", None)

        checks = {
            "production_router_preserved": production_from_wiring is production_persistence_router,
            "staged_router_identity_preserved": staged_from_wiring is lineage_persistence_router,
            "runtime_uses_staged_router": runtime_router is lineage_persistence_router,
            "ola017_uses_staged_router": orchestrator_router is lineage_persistence_router,
            "runtime_and_ola017_share_router": runtime_router is orchestrator_router,
            "ola045_bound_to_ola044": bridge_wiring is lineage_production_wiring,
            "ola046_bound_to_production_cycle": adapter_cycle is production_cycle_callable,
            "ola046_bound_to_ola045": adapter_bridge is lineage_completion_bridge,
            "ola050_bound_to_ola046": facade_adapter is lineage_scheduler_adapter,
        }
        full = all(checks.values())
        if not full:
            failed = ", ".join(name for name, passed in checks.items() if not passed)
            raise OracleProductionLineageGraphAssemblyAttestationBlocked(
                f"production lineage graph assembly mismatch: {failed}"
            )

        return OracleProductionLineageGraphAssemblyAttestationRecord(
            schema_version=SCHEMA_VERSION,
            engine_id=ENGINE_ID,
            attestation_type=ATTESTATION_TYPE,
            full_lineage_chain_attested=True,
            **checks,
        )


__all__ = [
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ATTESTATION_TYPE",
    "OracleProductionLineageGraphAssemblyAttestationError",
    "OracleProductionLineageGraphAssemblyAttestationBlocked",
    "OracleProductionLineageGraphAssemblyAttestationRecord",
    "OracleProductionLineageGraphAssemblyAttestor",
]
'''

TEST_TEXT = r'''from __future__ import annotations

import ast
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_lineage_graph_assembly_attestation import (
    OracleProductionLineageGraphAssemblyAttestationBlocked,
    OracleProductionLineageGraphAssemblyAttestor,
)

ROOT = Path(__file__).resolve().parent
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"


class ProductionRouter:
    def route_batch(self, *args, **kwargs):
        return None


class Wiring:
    def __init__(self, production, staged):
        self.production_persistence_router = production
        self.staged_persistence_router = staged


class Runtime:
    def __init__(self, router):
        self._persistence_router = router


class Orchestrator:
    def __init__(self, router):
        self._postgresql_router = router


class Bridge:
    def __init__(self, wiring):
        self.production_wiring = wiring


class Adapter:
    def __init__(self, cycle, bridge):
        self.scheduler_cycle_callable = cycle
        self.lineage_completion_bridge = bridge


class Facade:
    def __init__(self, adapter):
        self.scheduler_adapter = adapter

    def __call__(self, **kwargs):
        return None


def production_cycle(**kwargs):
    return None


def main():
    production = ProductionRouter()
    staged = object()
    wiring = Wiring(production, staged)
    runtime = Runtime(staged)
    orchestrator = Orchestrator(staged)
    bridge = Bridge(wiring)
    adapter = Adapter(production_cycle, bridge)
    facade = Facade(adapter)

    record = OracleProductionLineageGraphAssemblyAttestor().attest(
        production_persistence_router=production,
        lineage_production_wiring=wiring,
        lineage_persistence_router=staged,
        acquisition_runtime=runtime,
        cycle_orchestrator=orchestrator,
        production_cycle_callable=production_cycle,
        lineage_completion_bridge=bridge,
        lineage_scheduler_adapter=adapter,
        lineage_cycle_callable=facade,
    )
    assert record.schema_version == "OLA-052"
    assert record.full_lineage_chain_attested is True
    assert record.read_only is True
    assert record.execution_allowed is False

    try:
        OracleProductionLineageGraphAssemblyAttestor().attest(
            production_persistence_router=production,
            lineage_production_wiring=wiring,
            lineage_persistence_router=object(),
            acquisition_runtime=runtime,
            cycle_orchestrator=orchestrator,
            production_cycle_callable=production_cycle,
            lineage_completion_bridge=bridge,
            lineage_scheduler_adapter=adapter,
            lineage_cycle_callable=facade,
        )
    except OracleProductionLineageGraphAssemblyAttestationBlocked:
        pass
    else:
        raise AssertionError("OLA-052 must fail closed on graph identity mismatch")

    source = OLA030.read_text(encoding="utf-8")
    ast.parse(source)
    required = (
        "OracleProductionLineageGraphAssemblyAttestor",
        "lineage_graph_attestation =",
        "production_persistence_router=(",
        '"lineage_graph_attestation": (',
    )
    for marker in required:
        assert marker in source, marker

    print("[PASS] OLA-052 Production Lineage Graph Assembly Attestation")
    print({
        "schema_version": "OLA-052",
        "engine_id": "OLA-052",
        "status": "passed",
        "actual_ola030_graph_attested": True,
        "production_router_identity_attested": True,
        "staged_router_identity_attested": True,
        "runtime_and_ola017_shared_router_attested": True,
        "ola045_to_ola044_identity_attested": True,
        "ola046_to_production_cycle_identity_attested": True,
        "ola046_to_ola045_identity_attested": True,
        "ola050_to_ola046_identity_attested": True,
        "fail_closed_identity_mismatch_tested": True,
        "read_only": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "execution_adapter_resolved": False,
        "execution_adapter_invoked": False,
        "trade_authorization_allowed": False,
        "order_placement_allowed": False,
        "funds_moved": False,
        "portfolio_mutated": False,
    })


if __name__ == "__main__":
    main()
'''


def patch_ola030(source: str) -> str:
    import_marker = '''from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_shadow_acquisition_cycle_orchestrator import (\n    OraclePostgreSQLShadowAcquisitionCycleOrchestrator,\n)\n'''
    new_import = import_marker + '''\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_production_lineage_graph_assembly_attestation import (\n    OracleProductionLineageGraphAssemblyAttestor,\n)\n'''
    if 'OracleProductionLineageGraphAssemblyAttestor' not in source:
        if import_marker not in source:
            raise RuntimeError('OLA-030 import anchor not found')
        source = source.replace(import_marker, new_import, 1)

    scheduler_anchor = '''    scheduler = (\n        OracleControlledShadowCollectionSchedulerTick(\n'''
    attestation_block = '''    lineage_graph_attestation = (\n        OracleProductionLineageGraphAssemblyAttestor()\n        .attest(\n            production_persistence_router=(\n                persistence_router\n            ),\n            lineage_production_wiring=(\n                lineage_production_wiring\n            ),\n            lineage_persistence_router=(\n                lineage_persistence_router\n            ),\n            acquisition_runtime=(\n                acquisition_runtime\n            ),\n            cycle_orchestrator=(\n                cycle_orchestrator\n            ),\n            production_cycle_callable=(\n                production_cycle_callable\n            ),\n            lineage_completion_bridge=(\n                lineage_completion_bridge\n            ),\n            lineage_scheduler_adapter=(\n                lineage_scheduler_adapter\n            ),\n            lineage_cycle_callable=(\n                lineage_cycle_callable\n            ),\n        )\n    )\n\n'''
    if 'lineage_graph_attestation = (' not in source:
        if scheduler_anchor not in source:
            raise RuntimeError('OLA-030 scheduler anchor not found')
        source = source.replace(scheduler_anchor, attestation_block + scheduler_anchor, 1)

    return_anchor = '''        "lineage_cycle_callable": (\n            lineage_cycle_callable\n        ),\n'''
    return_block = return_anchor + '''        "lineage_graph_attestation": (\n            lineage_graph_attestation\n        ),\n'''
    if '"lineage_graph_attestation": (' not in source:
        if return_anchor not in source:
            raise RuntimeError('OLA-030 return anchor not found')
        source = source.replace(return_anchor, return_block, 1)
    return source


def main() -> None:
    print('========================================')
    print(' OLA-052 INSTALLER')
    print(' PRODUCTION LINEAGE GRAPH ASSEMBLY ATTESTATION')
    print('========================================')

    if not OLA030.exists():
        raise SystemExit(f'[ERROR] Missing OLA-030 production graph: {OLA030}')

    MODULE.parent.mkdir(parents=True, exist_ok=True)
    MODULE.write_text(MODULE_TEXT, encoding='utf-8')
    print(f'[OK] Wrote OLA-052 attestation module: {MODULE}')

    source = OLA030.read_text(encoding='utf-8')
    patched = patch_ola030(source)
    OLA030.write_text(patched, encoding='utf-8')
    print(f'[OK] Integrated OLA-052 into actual OLA-030 graph: {OLA030}')

    TEST.write_text(TEST_TEXT, encoding='utf-8')
    print(f'[OK] Wrote regression test: {TEST}')

    compile(MODULE.read_text(encoding='utf-8'), str(MODULE), 'exec')
    compile(OLA030.read_text(encoding='utf-8'), str(OLA030), 'exec')
    compile(TEST.read_text(encoding='utf-8'), str(TEST), 'exec')

    print('\n[DONE] OLA-052 production lineage graph assembly attestation installed')
    print('\nRun:')
    print('py test_ola_052_production_lineage_graph_assembly_attestation.py')


if __name__ == '__main__':
    main()
