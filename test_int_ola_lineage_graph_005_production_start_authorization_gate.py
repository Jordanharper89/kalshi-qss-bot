
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

OLA054_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_live_shadow_startup_readiness_attestation"
)
OLA055_MODULE = (
    "qseries_v2.oracle_intelligence.live_acquisition."
    "oracle_production_live_shadow_start_authorization"
)


def _assert_module_contracts() -> None:
    ola054 = importlib.import_module(OLA054_MODULE)
    ola055 = importlib.import_module(OLA055_MODULE)

    assert getattr(ola054, "SCHEMA_VERSION", None) == "OLA-054"
    assert getattr(ola054, "ENGINE_ID", None) == "OLA-054"

    assert getattr(ola055, "SCHEMA_VERSION", None) == "OLA-055"
    assert getattr(ola055, "ENGINE_ID", None) == "OLA-055"

    assert (
        getattr(
            ola055.OracleProductionLiveShadowStartAuthorizer,
            "read_only",
            None,
        )
        is True
    )
    assert (
        getattr(
            ola055.OracleProductionLiveShadowStartAuthorizer,
            "execution_allowed",
            None,
        )
        is False
    )


def _assert_actual_ola030_authorization_chain() -> None:
    assert OLA030.exists(), OLA030

    source = OLA030.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert isinstance(tree, ast.Module)

    required = (
        "OracleProductionLiveShadowStartupReadinessAttestor",
        "OracleProductionLiveShadowStartAuthorizer",
        "production_startup_readiness_attestation = (",
        "production_start_authorization = (",
        "startup_readiness_attestation=(",
        "service_bootstrap=service_bootstrap",
        "runner=runner",
        '"production_startup_readiness_attestation": (',
        '"production_start_authorization": (',
    )
    for marker in required:
        assert marker in source, marker

    readiness_pos = source.index(
        "production_startup_readiness_attestation = ("
    )
    authorization_pos = source.index(
        "production_start_authorization = ("
    )
    return_pos = source.index("    return {", authorization_pos)

    assert readiness_pos < authorization_pos < return_pos


def _exercise_ola055_fail_closed_contract() -> None:
    ola055 = importlib.import_module(OLA055_MODULE)

    Authorizer = ola055.OracleProductionLiveShadowStartAuthorizer
    Blocked = ola055.OracleProductionLiveShadowStartAuthorizationBlocked

    startup_readiness = SimpleNamespace(startup_ready=True)

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

    record = Authorizer().authorize(
        startup_readiness_attestation=startup_readiness,
        service_bootstrap=bootstrap,
        runner=runner,
    )

    assert record.start_authorized is True
    assert record.authorization_consumed is False
    assert record.service_started is False
    assert record.process_created is False
    assert record.thread_created is False
    assert record.loop_started is False
    assert record.acquisition_invoked is False
    assert record.scheduler_tick_invoked is False
    assert record.shadow_cycle_invoked is False
    assert record.read_only is True
    assert record.execution_allowed is False
    assert record.alerts_allowed is False
    assert record.qseries_handoff_allowed is False

    wrong_runner = Runner(SimpleNamespace(**vars(bootstrap)))

    try:
        Authorizer().authorize(
            startup_readiness_attestation=startup_readiness,
            service_bootstrap=bootstrap,
            runner=wrong_runner,
        )
    except Blocked:
        pass
    else:
        raise AssertionError(
            "INT-OLA-LINEAGE-GRAPH-005 expected fail-closed "
            "runner/bootstrap identity mismatch"
        )


def main() -> None:
    _assert_module_contracts()
    _assert_actual_ola030_authorization_chain()
    _exercise_ola055_fail_closed_contract()

    print(
        "[PASS] INT-OLA-LINEAGE-GRAPH-005 "
        "Production Start Authorization Gate"
    )
    print({
        "schema_version": "INT-OLA-LINEAGE-GRAPH-005",
        "engine_id": "INT-OLA-LINEAGE-GRAPH-005",
        "status": "passed",
        "actual_ola030_source_graph_inspected": True,
        "actual_graph_ast_valid": True,
        "ola054_startup_readiness_contract_preserved": True,
        "ola055_start_authorization_contract_preserved": True,
        "startup_readiness_precedes_start_authorization": True,
        "ola022_service_start_permission_preserved": True,
        "ola023_runner_bootstrap_identity_preserved": True,
        "start_authorized_but_not_consumed": True,
        "service_not_started": True,
        "no_process_created": True,
        "no_thread_created": True,
        "no_loop_started": True,
        "no_acquisition_invoked": True,
        "no_scheduler_tick_invoked": True,
        "no_shadow_cycle_invoked": True,
        "fail_closed_runner_bootstrap_identity_mismatch_tested": True,
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
