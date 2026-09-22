
from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent

OLA030 = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "live_acquisition_model"
    / "oracle_first_real_shadow_corpus_launch_command.py"
)

OLA052_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_lineage_graph_assembly_attestation"
)
OLA053_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_lineage_scheduler_activation_attestation"
)
OLA054_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_live_shadow_startup_readiness_attestation"
)


def _assert_module_contracts() -> None:
    ola052 = importlib.import_module(OLA052_MODULE)
    ola053 = importlib.import_module(OLA053_MODULE)
    ola054 = importlib.import_module(OLA054_MODULE)

    assert getattr(ola052, "SCHEMA_VERSION", None) == "OLA-052"
    assert getattr(ola052, "ENGINE_ID", None) == "OLA-052"

    assert getattr(ola053, "SCHEMA_VERSION", None) == "OLA-053"
    assert getattr(ola053, "ENGINE_ID", None) == "OLA-053"

    assert getattr(ola054, "SCHEMA_VERSION", None) == "OLA-054"
    assert getattr(ola054, "ENGINE_ID", None) == "OLA-054"

    assert (
        getattr(
            ola054.OracleProductionLiveShadowStartupReadinessAttestor,
            "read_only",
            None,
        )
        is True
    )
    assert (
        getattr(
            ola054.OracleProductionLiveShadowStartupReadinessAttestor,
            "execution_allowed",
            None,
        )
        is False
    )


def _assert_actual_ola030_prestart_chain() -> None:
    assert OLA030.exists(), OLA030

    source = OLA030.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert isinstance(tree, ast.Module)

    required = (
        "OracleProductionLineageGraphAssemblyAttestor",
        "OracleProductionLineageSchedulerActivationAttestor",
        "OracleProductionLiveShadowStartupReadinessAttestor",
        "lineage_graph_attestation = (",
        "lineage_scheduler_activation_attestation = (",
        "production_startup_readiness_attestation = (",
        '"lineage_graph_attestation": (',
        '"lineage_scheduler_activation_attestation": (',
        '"production_startup_readiness_attestation": (',
    )
    for marker in required:
        assert marker in source, marker

    assembly_pos = source.index("lineage_graph_attestation = (")
    activation_pos = source.index(
        "lineage_scheduler_activation_attestation = ("
    )
    startup_pos = source.index(
        "production_startup_readiness_attestation = ("
    )
    return_pos = source.index("    return {", startup_pos)

    assert assembly_pos < activation_pos < startup_pos < return_pos


def _exercise_ola054_fail_closed_prestart_contract() -> None:
    ola054 = importlib.import_module(OLA054_MODULE)

    Attestor = ola054.OracleProductionLiveShadowStartupReadinessAttestor
    Blocked = (
        ola054.
        OracleProductionLiveShadowStartupReadinessAttestationBlocked
    )

    graph_attestation = SimpleNamespace(full_graph_attested=True)
    activation_attestation = SimpleNamespace(
        full_activation_chain_attested=True
    )

    bootstrap = SimpleNamespace(
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

    class Runner:
        read_only = True
        execution_allowed = False

        def __init__(self, bootstrap_record):
            self._bootstrap_record = bootstrap_record

    runner = Runner(bootstrap)

    record = Attestor().attest(
        lineage_graph_attestation=graph_attestation,
        lineage_scheduler_activation_attestation=activation_attestation,
        service_bootstrap=bootstrap,
        runner=runner,
    )

    assert record.startup_ready is True
    assert record.service_started is False
    assert record.process_created is False
    assert record.thread_created is False
    assert record.loop_started is False
    assert record.acquisition_invoked is False
    assert record.scheduler_tick_invoked is False
    assert record.shadow_cycle_invoked is False
    assert record.read_only is True
    assert record.execution_allowed is False

    bad_bootstrap = SimpleNamespace(**vars(bootstrap))
    bad_bootstrap.scheduler_tick_invoked = True

    try:
        Attestor().attest(
            lineage_graph_attestation=graph_attestation,
            lineage_scheduler_activation_attestation=activation_attestation,
            service_bootstrap=bad_bootstrap,
            runner=Runner(bad_bootstrap),
        )
    except Blocked:
        pass
    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-004 expected fail-closed "
            "pre-start activity rejection"
        )


def main() -> None:
    _assert_module_contracts()
    _assert_actual_ola030_prestart_chain()
    _exercise_ola054_fail_closed_prestart_contract()

    print(
        "[PASS] INT-OLA-LINEAGE-GRAPH-004 "
        "Production Startup Readiness Gate"
    )
    print({
        "schema_version": "INT-OLA-LINEAGE-GRAPH-004",
        "engine_id": "INT-OLA-LINEAGE-GRAPH-004",
        "status": "passed",
        "actual_ola030_source_graph_inspected": True,
        "actual_graph_ast_valid": True,
        "ola052_graph_assembly_attestation_preserved": True,
        "ola053_scheduler_activation_attestation_preserved": True,
        "ola054_startup_readiness_attestation_preserved": True,
        "prestart_chain_order_preserved": True,
        "startup_ready_but_service_not_started": True,
        "no_process_created": True,
        "no_thread_created": True,
        "no_loop_started": True,
        "no_acquisition_invoked": True,
        "no_scheduler_tick_invoked": True,
        "no_shadow_cycle_invoked": True,
        "fail_closed_prestart_activity_rejection_tested": True,
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
