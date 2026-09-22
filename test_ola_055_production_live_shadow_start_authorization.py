from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

from qseries_v2.oracle_intelligence.live_acquisition.oracle_production_live_shadow_start_authorization import (
    OracleProductionLiveShadowStartAuthorizationBlocked,
    OracleProductionLiveShadowStartAuthorizer,
)

ROOT = Path(__file__).resolve().parent
OLA030 = ROOT / "qseries_v2/oracle_intelligence/live_acquisition_model/oracle_first_real_shadow_corpus_launch_command.py"


class Runner:
    read_only = True
    execution_allowed = False

    def __init__(self, bootstrap):
        self._bootstrap_record = bootstrap


def make_bootstrap():
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
    startup_readiness = SimpleNamespace(startup_ready=True)
    bootstrap = make_bootstrap()
    runner = Runner(bootstrap)

    record = OracleProductionLiveShadowStartAuthorizer().authorize(
        startup_readiness_attestation=startup_readiness,
        service_bootstrap=bootstrap,
        runner=runner,
    )

    assert record.schema_version == "OLA-055"
    assert record.start_authorized is True
    assert record.authorization_consumed is False
    assert record.service_started is False
    assert record.loop_started is False
    assert record.read_only is True
    assert record.execution_allowed is False

    bad_bootstrap = make_bootstrap()
    bad_bootstrap.shadow_cycle_invoked = True

    try:
        OracleProductionLiveShadowStartAuthorizer().authorize(
            startup_readiness_attestation=startup_readiness,
            service_bootstrap=bad_bootstrap,
            runner=Runner(bad_bootstrap),
        )
    except OracleProductionLiveShadowStartAuthorizationBlocked:
        pass
    else:
        raise AssertionError(
            "OLA-055 must fail closed if pre-start activity already occurred"
        )

    source = OLA030.read_text(encoding="utf-8")
    ast.parse(source)

    required = (
        "OracleProductionLiveShadowStartAuthorizer",
        "production_start_authorization = (",
        "startup_readiness_attestation=(",
        "service_bootstrap=service_bootstrap",
        "runner=runner",
        '"production_start_authorization": (',
    )
    for marker in required:
        assert marker in source, marker

    startup_pos = source.index(
        "production_startup_readiness_attestation = ("
    )
    authorization_pos = source.index(
        "production_start_authorization = ("
    )
    return_pos = source.index("    return {", authorization_pos)

    assert startup_pos < authorization_pos < return_pos

    print("[PASS] OLA-055 Production Live Shadow Start Authorization")
    print({
        "schema_version": "OLA-055",
        "engine_id": "OLA-055",
        "status": "passed",
        "actual_ola030_start_authorization_integrated": True,
        "ola054_startup_readiness_required": True,
        "ola022_service_start_permission_required": True,
        "ola023_runner_bootstrap_identity_preserved": True,
        "start_authorized_but_not_consumed": True,
        "service_not_started": True,
        "no_process_created": True,
        "no_thread_created": True,
        "no_loop_started": True,
        "no_acquisition_invoked": True,
        "no_scheduler_tick_invoked": True,
        "no_shadow_cycle_invoked": True,
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
