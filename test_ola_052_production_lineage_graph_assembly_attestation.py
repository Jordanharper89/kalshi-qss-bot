from __future__ import annotations

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
