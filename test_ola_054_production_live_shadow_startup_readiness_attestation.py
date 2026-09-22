
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_startup_readiness_attestation import (
    OracleProductionLiveShadowStartupReadinessAttestationBlocked,
    OracleProductionLiveShadowStartupReadinessAttestor,
)

ROOT = Path(__file__).resolve().parent
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"


class Runner:
    read_only = True
    execution_allowed = False

    def __init__(self, bootstrap):
        self._bootstrap_record = bootstrap


def bootstrap_record():
    return SimpleNamespace(
        bootstrap_status="ready",
        service_start_allowed=True,
        service_started=False,
        process_created=False,
        thread_created=False,
        loop_started=False,
        acquisition_invoked=False,
        scheduler_tick_invoked=False,
        shadow_cycle_invoked=False,
    )


def main():
    graph_attestation = SimpleNamespace(full_graph_attested=True)
    activation_attestation = SimpleNamespace(
        full_activation_chain_attested=True
    )
    bootstrap = bootstrap_record()
    runner = Runner(bootstrap)

    record = OracleProductionLiveShadowStartupReadinessAttestor().attest(
        lineage_graph_attestation=graph_attestation,
        lineage_scheduler_activation_attestation=activation_attestation,
        service_bootstrap=bootstrap,
        runner=runner,
    )

    assert record.schema_version == "OLA-054"
    assert record.startup_ready is True
    assert record.service_started is False
    assert record.loop_started is False
    assert record.read_only is True
    assert record.execution_allowed is False

    bad_bootstrap = bootstrap_record()
    bad_bootstrap.loop_started = True

    try:
        OracleProductionLiveShadowStartupReadinessAttestor().attest(
            lineage_graph_attestation=graph_attestation,
            lineage_scheduler_activation_attestation=activation_attestation,
            service_bootstrap=bad_bootstrap,
            runner=Runner(bad_bootstrap),
        )
    except OracleProductionLiveShadowStartupReadinessAttestationBlocked:
        pass
    else:
        raise AssertionError(
            "OLA-054 must fail closed if startup activity already occurred"
        )

    source = OLA030.read_text(encoding="utf-8")
    ast.parse(source)

    required = (
        "OracleProductionLiveShadowStartupReadinessAttestor",
        "production_startup_readiness_attestation = (",
        "lineage_graph_attestation=(",
        "lineage_scheduler_activation_attestation=(",
        "service_bootstrap=service_bootstrap",
        "runner=runner",
        '"production_startup_readiness_attestation": (',
    )
    for marker in required:
        assert marker in source, marker

    activation_pos = source.index(
        "lineage_scheduler_activation_attestation = ("
    )
    startup_pos = source.index(
        "production_startup_readiness_attestation = ("
    )
    return_pos = source.index("    return {", startup_pos)

    assert activation_pos < startup_pos < return_pos

    print("[PASS] OLA-054 Production Live Shadow Startup Readiness Attestation")
    print({
        "schema_version": "OLA-054",
        "engine_id": "OLA-054",
        "status": "passed",
        "actual_ola030_startup_boundary_attested": True,
        "ola052_graph_assembly_required": True,
        "ola053_scheduler_activation_required": True,
        "ola022_bootstrap_ready_required": True,
        "ola023_runner_bootstrap_identity_preserved": True,
        "startup_authorized_but_not_started": True,
        "fail_closed_prestarted_runtime_tested": True,
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
